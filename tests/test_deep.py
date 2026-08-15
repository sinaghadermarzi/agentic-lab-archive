import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "notebooks"))

from lab_core.deep import (  # noqa: E402
    Context,
    DeepAgent,
    SubAgent,
    TodoList,
    VirtualFS,
    compose_system_prompt,
)
from lab_core.patterns import Budget, CheckpointStore, ToolLoopResult  # noqa: E402


seen_contexts: list = []


def build_agent(**overrides):
    fs = VirtualFS()
    fs.write("/sources/doc.md", "CLAIM: water is wet\nfiller " * 40)

    def reader(task, context, files):
        text = files.read("/sources/doc.md")
        context.add("tool:read_file", text[:80])
        claims = [line for line in text.splitlines() if line.startswith("CLAIM:")]
        return {"summary": "; ".join(claims), "detail": text}

    def policy(goal, todos, trace, context):
        seen_contexts.append(context)
        if not todos.items:
            return {"tool": "write_todos", "input": {"add": ["digest doc", "write answer"]}}
        pending = todos.next_pending()
        if pending is None:
            return {"final": "done: /notes/answer.md"}
        index = todos.items.index(pending)
        if pending.text == "digest doc":
            if trace and trace[-1].get("tool") == "task":
                return {"tool": "write_todos", "input": {"done": index, "note": "via reader"}}
            return {"tool": "task", "input": {"agent": "reader", "task": "extract claims"}}
        if trace and trace[-1].get("tool") == "write_file":
            return {"tool": "write_todos", "input": {"done": index}}
        # Resume-safe: evidence comes from the trace when fresh, from artifacts otherwise.
        evidence = [t["observation"] for t in trace if t.get("tool") in ("task", "read_file")]
        if not evidence:
            return {"tool": "read_file", "input": {"path": "/subagents/reader-1.md"}}
        claims = [ln for obs in evidence for ln in str(obs).splitlines() if ln.startswith("CLAIM:")]
        return {
            "tool": "write_file",
            "input": {"path": "/notes/answer.md", "text": "\n".join(claims)},
        }

    config = {
        "system_prompt": compose_system_prompt("You review sources."),
        "policy": policy,
        "fs": fs,
        "checkpoints": CheckpointStore(),
    }
    config.update(overrides)
    agent = DeepAgent("reviewer", **config)
    agent.subagents = {"reader": SubAgent("reader", "Extract CLAIM lines.", reader, fs)}
    return agent


class DeepAgentTests(unittest.TestCase):
    def test_todo_list_renders_and_round_trips(self):
        todos = TodoList()
        todos.add("first", "second")
        todos.complete(0, "ok")
        self.assertIn("- [x] first (ok)", todos.render())
        self.assertEqual(todos.next_pending().text, "second")
        restored = TodoList.from_dict(todos.to_dict())
        self.assertEqual(restored.render(), todos.render())

    def test_context_pins_replace_and_adds_append(self):
        context = Context(owner="t")
        context.pin("todos", "v1")
        context.pin("todos", "v2")
        context.add("obs", "one")
        context.add("obs", "two")
        self.assertEqual([e.label for e in context.entries], ["todos", "obs", "obs"])
        self.assertIn("## todos\nv2", context.render())

    def test_compaction_shrinks_but_keeps_pinned_and_recent(self):
        context = Context(owner="t")
        context.pin("system", "stay")
        for i in range(10):
            context.add("obs", f"observation number {i} with some padding text")
        before = context.tokens()
        summary = context.compact(keep_last=2)
        self.assertLess(context.tokens(), before)
        self.assertIn("[compacted] 8 entries", summary)
        rendered = context.render()
        self.assertIn("stay", rendered)
        self.assertIn("observation number 9", rendered)
        self.assertNotIn("observation number 3", rendered)

    def test_fs_write_returns_receipt_not_content(self):
        fs = VirtualFS()
        receipt = fs.write("/notes/a.md", "x" * 500)
        self.assertEqual(receipt, "wrote /notes/a.md (500 chars)")
        self.assertEqual(fs.read("/notes/a.md"), "x" * 500)
        fs.write("/other/b.md", "y")
        self.assertEqual(fs.ls("/notes"), ["/notes/a.md"])
        with self.assertRaises(KeyError) as ctx:
            fs.read("/missing.md")
        self.assertIn("/missing.md", str(ctx.exception))

    def test_subagent_context_is_isolated(self):
        fs = VirtualFS()
        parent = Context(owner="parent")
        parent.pin("goal", "PARENT-ONLY secret goal")

        def worker(task, context, files):
            context.add("scratch", "sub thinking")
            return {"summary": "short conclusion", "detail": "long detail " * 100}

        report = SubAgent("helper", "Help out.", worker, fs).run("do a thing")
        self.assertNotIn("PARENT-ONLY", report.context.render())
        self.assertEqual(
            [e.label for e in report.context.entries], ["instructions", "task", "scratch"]
        )
        self.assertIn("long detail", fs.read(report.detail_path))
        self.assertNotIn("long detail", parent.render())

    def test_subagent_summary_is_capped(self):
        fs = VirtualFS()
        agent = SubAgent(
            "wordy", "Be brief.", lambda t, c, f: {"summary": "s" * 2000, "detail": ""}, fs
        )
        report = agent.run("task")
        self.assertLessEqual(len(report.summary), agent.max_summary_chars + len(" …[truncated]"))
        self.assertTrue(report.summary.endswith("…[truncated]"))

    def test_deep_agent_completes_and_returns_patterns_result(self):
        seen_contexts.clear()
        agent = build_agent()
        result = agent.run("review the doc", run_id="r1")
        self.assertIsInstance(result, ToolLoopResult)
        # The policy receives the agent's live curated window (the Codex-reviewed seam):
        self.assertIs(seen_contexts[0], agent.context)
        self.assertIn("system", [e.label for e in seen_contexts[0].entries])
        self.assertTrue(result.completed)
        self.assertIsNone(agent.todos.next_pending())
        self.assertIn("CLAIM: water is wet", agent.fs.read("/notes/answer.md"))
        self.assertTrue(any(e.label.startswith("tool:") for e in agent.context.entries))

    def test_interrupt_then_resume_finishes_from_artifacts(self):
        agent = build_agent()
        first = agent.run("review the doc", run_id="r1", max_steps=3)
        self.assertFalse(first.completed)
        self.assertIn("step budget", first.error)
        first_leg_observation = agent.context.entries[-1].text
        resumed = agent.resume("r1")
        self.assertTrue(resumed.completed)
        self.assertNotIn(first_leg_observation, agent.context.render())
        self.assertIn("CLAIM: water is wet", agent.fs.read("/notes/answer.md"))

    def test_observation_cap_and_budget_stop(self):
        agent = build_agent(max_observation_chars=50)
        agent.run("review the doc", run_id="r1")
        capped = [
            e for e in agent.context.entries if e.label == "tool:read_file" or "chars]" in e.text
        ]
        self.assertTrue(any("…[+" in e.text for e in agent.context.entries))
        for entry in capped:
            self.assertLessEqual(len(entry.text), 50 + len(" …[+00000 chars]") + 4)

        strict = build_agent(budget=Budget(max_steps=1))
        result = strict.run("review the doc", run_id="r2")
        self.assertFalse(result.completed)
        self.assertIn("budget", result.error)
        self.assertIn("todos", strict.checkpoints.load("r2"))


if __name__ == "__main__":
    unittest.main()
