"""A deterministic teaching double of the deep-agent architecture.

Deep agents are the notebook-01 tool loop wearing four context disciplines
for long-horizon work: a plan kept as a persistent artifact, a filesystem
for offloading context, sub-agents that think in isolated windows and
return only compact conclusions, and detailed prompts with progressively
disclosed skills. The scarce resource all four protect is the context
window, so this module models it as a first-class, printable object.

Two distinctions keep the demos honest. The *trace* (from
``patterns.run_tool_loop``) is the flight recorder: complete, for the
loop. The *Context* is the window: curated, what a model would see.
Token counts use the standard chars/4 estimate; no LLM or network is
involved anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from lab_core.patterns import Budget, CheckpointStore, ToolLoopResult, run_tool_loop


def estimate_tokens(text: str) -> int:
    """Deterministic stand-in for a tokenizer: roughly four characters per token."""

    return max(1, len(text) // 4)


@dataclass
class ContextEntry:
    label: str
    text: str

    @property
    def tokens(self) -> int:
        return estimate_tokens(self.text)


@dataclass
class Context:
    """What would be sent to the model this turn — the resource every pillar protects."""

    owner: str
    entries: list[ContextEntry] = field(default_factory=list)

    def add(self, label: str, text: str) -> None:
        self.entries.append(ContextEntry(label, str(text)))

    def pin(self, label: str, text: str) -> None:
        """Add-or-replace by label: slots like system/goal/todos update in place."""

        for entry in self.entries:
            if entry.label == label:
                entry.text = str(text)
                return
        self.add(label, text)

    def tokens(self) -> int:
        return sum(entry.tokens for entry in self.entries)

    def render(self) -> str:
        return "\n\n".join(f"## {e.label}\n{e.text}" for e in self.entries)

    def compact(
        self, *, keep_last: int = 2, keep_labels: tuple[str, ...] = ("system", "goal", "todos")
    ) -> str:
        """Fold old unpinned entries into one summary entry; lossy by design."""

        keep_tail = [e for e in self.entries if e.label not in keep_labels][-keep_last:]
        folded = [e for e in self.entries if e.label not in keep_labels and e not in keep_tail]
        if not folded:
            return "nothing to compact"
        summary = f"[compacted] {len(folded)} entries: " + ", ".join(e.label for e in folded)
        rebuilt = [e for e in self.entries if e.label in keep_labels]
        rebuilt.append(ContextEntry("compacted", summary))
        rebuilt.extend(keep_tail)
        self.entries = rebuilt
        return summary


@dataclass
class TodoItem:
    text: str
    status: str = "pending"
    note: str = ""


class TodoList:
    """The plan as a persistent artifact the agent re-reads and updates each step."""

    def __init__(self) -> None:
        self.items: list[TodoItem] = []

    def add(self, *texts: str) -> None:
        self.items.extend(TodoItem(text) for text in texts)

    def complete(self, index: int, note: str = "") -> None:
        self.items[index].status = "done"
        self.items[index].note = note

    def next_pending(self) -> TodoItem | None:
        return next((item for item in self.items if item.status == "pending"), None)

    def render(self) -> str:
        if not self.items:
            return "(no plan yet)"
        marks = {"pending": " ", "done": "x"}
        lines = []
        for item in self.items:
            suffix = f" ({item.note})" if item.note else ""
            lines.append(f"- [{marks[item.status]}] {item.text}{suffix}")
        return "\n".join(lines)

    def to_dict(self) -> list[dict[str, str]]:
        return [vars(item).copy() for item in self.items]

    @classmethod
    def from_dict(cls, data: Sequence[Mapping[str, str]]) -> TodoList:
        todos = cls()
        todos.items = [TodoItem(**dict(item)) for item in data]
        return todos


class VirtualFS:
    """Context offloading target: payloads live here, receipts live in context."""

    def __init__(self) -> None:
        self.files: dict[str, str] = {}

    def write(self, path: str, text: str) -> str:
        self.files[path] = str(text)
        return f"wrote {path} ({len(self.files[path])} chars)"

    def read(self, path: str) -> str:
        if path not in self.files:
            raise KeyError(
                f"no such file: {path} (have: {', '.join(sorted(self.files)) or 'none'})"
            )
        return self.files[path]

    def ls(self, prefix: str = "") -> list[str]:
        return sorted(path for path in self.files if path.startswith(prefix))


@dataclass
class Skill:
    """Progressive disclosure: the catalog line is cheap, instructions load on demand."""

    name: str
    description: str
    instructions: str


def compose_system_prompt(role: str, skills: Sequence[Skill] = ()) -> str:
    lines = [role]
    if skills:
        lines.append("\nSkills available via load_skill (name: description):")
        lines.extend(f"- {s.name}: {s.description}" for s in skills)
    return "\n".join(lines)


@dataclass
class SubAgentReport:
    agent: str
    task: str
    summary: str
    detail_path: str
    context: Context


class SubAgent:
    """Isolated context in, compact conclusion out. Shares the fs, never the history."""

    def __init__(
        self,
        name: str,
        instructions: str,
        worker: Callable[[str, Context, VirtualFS], Mapping[str, str]],
        fs: VirtualFS,
        *,
        max_summary_chars: int = 280,
    ) -> None:
        self.name = name
        self.instructions = instructions
        self.worker = worker
        self.fs = fs
        self.max_summary_chars = max_summary_chars
        self.runs: list[SubAgentReport] = []

    def run(self, task: str) -> SubAgentReport:
        context = Context(owner=self.name)
        context.pin("instructions", self.instructions)
        context.add("task", task)
        outcome = self.worker(task, context, self.fs)
        detail_path = f"/subagents/{self.name}-{len(self.runs) + 1}.md"
        self.fs.write(detail_path, str(outcome.get("detail", "")))
        summary = str(outcome["summary"])
        if len(summary) > self.max_summary_chars:
            summary = summary[: self.max_summary_chars] + " …[truncated]"
        report = SubAgentReport(self.name, task, summary, detail_path, context)
        self.runs.append(report)
        return report


class DeepAgent:
    """The notebook-01 loop wearing the four disciplines; ``run`` returns its result."""

    def __init__(
        self,
        name: str,
        *,
        system_prompt: str,
        policy: Callable[[str, TodoList, list[dict[str, Any]]], Mapping[str, Any]],
        tools: Mapping[str, Callable[[Any], Any]] | None = None,
        subagents: Sequence[SubAgent] = (),
        skills: Sequence[Skill] = (),
        fs: VirtualFS | None = None,
        budget: Budget | None = None,
        checkpoints: CheckpointStore | None = None,
        context_limit: int = 2000,
        max_observation_chars: int = 200,
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.policy = policy
        self.extra_tools = dict(tools or {})
        self.subagents = {agent.name: agent for agent in subagents}
        self.skills = {skill.name: skill for skill in skills}
        self.fs = fs if fs is not None else VirtualFS()
        self.budget = budget
        self.checkpoints = checkpoints
        self.context_limit = context_limit
        self.max_observation_chars = max_observation_chars
        self.todos = TodoList()
        self.context = Context(owner=name)
        self.goal = ""

    def run(self, goal: str, *, run_id: str = "run-1", max_steps: int = 12) -> ToolLoopResult:
        self.goal = goal
        self.todos = TodoList()
        return self._loop(run_id, max_steps)

    def resume(self, run_id: str = "run-1", *, max_steps: int = 12) -> ToolLoopResult:
        """Restart from artifacts — plan, files, checkpoint — never the dead transcript."""

        if self.checkpoints is None:
            raise RuntimeError("resume requires a checkpoint store")
        state = self.checkpoints.load(run_id)
        self.goal = state["goal"]
        self.todos = TodoList.from_dict(state["todos"])
        self.fs.files = dict(state["files"])
        return self._loop(run_id, max_steps)

    def _loop(self, run_id: str, max_steps: int) -> ToolLoopResult:
        self._fresh_context()

        def adapter(goal: str, trace: list[dict[str, Any]]) -> Mapping[str, Any]:
            self.context.pin("todos", self.todos.render())  # the agent re-reads its plan
            return self.policy(goal, self.todos, trace)

        return run_tool_loop(self.goal, adapter, self._wired_tools(run_id), max_steps=max_steps)

    def _fresh_context(self) -> None:
        self.context = Context(owner=self.name)
        self.context.pin("system", self.system_prompt)
        self.context.pin("goal", self.goal)
        self.context.pin("todos", self.todos.render())
        self.context.pin("files", "\n".join(self.fs.ls()) or "(empty)")

    def _wired_tools(self, run_id: str) -> dict[str, Callable[[Any], Any]]:
        tools: dict[str, Callable[[Any], Any]] = {
            "write_todos": self._tool_write_todos,
            "write_file": lambda a: self.fs.write(a["path"], a["text"]),
            "read_file": lambda a: self.fs.read(a["path"]),
            "ls": lambda a: "\n".join(self.fs.ls((a or {}).get("prefix", ""))) or "(empty)",
            "task": self._tool_task,
            "load_skill": self._tool_load_skill,
        }
        tools.update(self.extra_tools)
        return {name: self._observe(name, fn, run_id) for name, fn in tools.items()}

    def _tool_write_todos(self, args: Mapping[str, Any]) -> str:
        if "add" in args:
            self.todos.add(*args["add"])
        if "done" in args:
            self.todos.complete(args["done"], args.get("note", ""))
        return self.todos.render()

    def _tool_task(self, args: Mapping[str, Any]) -> str:
        report = self.subagents[args["agent"]].run(args["task"])
        return f"{report.summary} (detail: {report.detail_path})"

    def _tool_load_skill(self, args: Mapping[str, Any]) -> str:
        skill = self.skills[args["name"]]
        self.context.add(f"skill:{skill.name}", skill.instructions)
        return f"loaded skill {skill.name} ({estimate_tokens(skill.instructions)} tokens)"

    def _observe(self, name: str, fn: Callable[[Any], Any], run_id: str) -> Callable[[Any], Any]:
        def wrapped(args: Any) -> Any:
            if self.budget is not None:
                self.budget.charge()
            observation = fn(args)
            capped = str(observation)
            if len(capped) > self.max_observation_chars:
                capped = (
                    capped[: self.max_observation_chars]
                    + f" …[+{len(capped) - self.max_observation_chars} chars]"
                )
            self.context.add(f"tool:{name}", capped)
            if self.context.tokens() > self.context_limit:
                self.context.compact()
            if self.checkpoints is not None:
                self.checkpoints.save(
                    run_id,
                    {
                        "goal": self.goal,
                        "todos": self.todos.to_dict(),
                        "files": dict(self.fs.files),
                    },
                )
            return observation

        return wrapped
