"""Framework-neutral implementations of recurring agentic patterns.

These are deliberately deterministic teaching doubles. They make the control
flow visible without hiding it behind an SDK or requiring an API key.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping


@dataclass
class ToolLoopResult:
    answer: Any | None
    trace: list[dict[str, Any]] = field(default_factory=list)
    completed: bool = False
    error: str | None = None


def run_tool_loop(
    goal: str,
    choose_action: Callable[[str, list[dict[str, Any]]], Mapping[str, Any]],
    tools: Mapping[str, Callable[[Any], Any]],
    *,
    max_steps: int = 8,
) -> ToolLoopResult:
    """Run an explicit observe → decide → act loop with a hard step budget.

    ``choose_action`` is the model-shaped boundary. In a live system it can
    call an LLM; in the notebooks it is a deterministic policy.
    """

    trace: list[dict[str, Any]] = []
    for step in range(1, max_steps + 1):
        action = dict(choose_action(goal, trace))
        if "final" in action:
            trace.append({"step": step, "decision": "final", "output": action["final"]})
            return ToolLoopResult(action["final"], trace, completed=True)
        tool_name = action.get("tool")
        if tool_name not in tools:
            return ToolLoopResult(None, trace, error=f"unknown tool: {tool_name!r}")
        try:
            observation = tools[tool_name](action.get("input"))
        except Exception as exc:  # pragma: no cover - included to show tool boundaries
            trace.append({"step": step, "tool": tool_name, "error": str(exc)})
            return ToolLoopResult(None, trace, error=f"tool failed: {tool_name}: {exc}")
        trace.append(
            {
                "step": step,
                "decision": "tool",
                "tool": tool_name,
                "input": action.get("input"),
                "observation": observation,
            }
        )
    return ToolLoopResult(None, trace, error=f"step budget exceeded ({max_steps})")


def route(value: Any, classifier: Callable[[Any], str], branches: Mapping[str, Callable[[Any], Any]]) -> Any:
    """Classify input, then invoke one narrowly scoped branch."""

    key = classifier(value)
    if key not in branches:
        raise KeyError(f"no branch registered for route {key!r}")
    return branches[key](value)


def fan_out_fan_in(
    items: Iterable[Any], worker: Callable[[Any], Any], reducer: Callable[[list[Any]], Any], *, workers: int = 4
) -> Any:
    """Run independent work concurrently, then reduce the complete result set."""

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(worker, items))
    return reducer(results)


def evaluate_optimize(
    initial: Any,
    evaluate: Callable[[Any], Mapping[str, Any]],
    revise: Callable[[Any, Mapping[str, Any]], Any],
    *,
    max_rounds: int = 3,
) -> tuple[Any, list[Mapping[str, Any]]]:
    """Generate → evaluate → revise until an objective rubric passes."""

    candidate = initial
    reports: list[Mapping[str, Any]] = []
    for _ in range(max_rounds + 1):
        report = dict(evaluate(candidate))
        reports.append(report)
        if report.get("pass") is True:
            return candidate, reports
        if len(reports) > max_rounds:
            break
        candidate = revise(candidate, report)
    return candidate, reports


@dataclass
class Budget:
    """Simple run envelope for steps, retries, and estimated spend."""

    max_steps: int = 10
    max_retries: int = 2
    max_spend: float = 1.0
    steps: int = 0
    retries: int = 0
    spend: float = 0.0

    def charge(self, *, spend: float = 0.0, retry: bool = False) -> None:
        self.steps += 1
        self.spend += spend
        if retry:
            self.retries += 1
        if self.steps > self.max_steps:
            raise RuntimeError("step budget exceeded")
        if self.retries > self.max_retries:
            raise RuntimeError("retry budget exceeded")
        if self.spend > self.max_spend:
            raise RuntimeError("spend budget exceeded")


class CheckpointStore:
    """In-memory checkpoint store used to demonstrate resumable state."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def save(self, run_id: str, state: Any) -> None:
        self._data[run_id] = state

    def load(self, run_id: str) -> Any:
        return self._data[run_id]


class ApprovalGate:
    """Pause a proposed consequential action until an explicit decision arrives."""

    def __init__(self, approver: Callable[[Any], bool]) -> None:
        self.approver = approver

    def require(self, proposal: Any) -> Any:
        if not self.approver(proposal):
            raise PermissionError("human approval denied")
        return proposal
