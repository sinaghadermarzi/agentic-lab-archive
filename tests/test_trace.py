import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "notebooks"))

from lab_core.deep import DeepAgent, VirtualFS, compose_system_prompt  # noqa: E402
from lab_core.patterns import run_tool_loop  # noqa: E402
from lab_core.trace import Span, Tracer  # noqa: E402


class RecordingSink:
    def __init__(self):
        self.events = []

    def on_start(self, span: Span) -> None:
        self.events.append(("start", span.name))

    def on_end(self, span: Span) -> None:
        self.events.append(("end", span.name))


class TracerTests(unittest.TestCase):
    def test_spans_nest_and_roots_collect(self):
        tracer = Tracer()
        with tracer.span("outer"):
            with tracer.span("inner-1"):
                pass
            with tracer.span("inner-2"):
                pass
        with tracer.span("second-root"):
            pass
        self.assertEqual([r.name for r in tracer.roots], ["outer", "second-root"])
        self.assertEqual([c.name for c in tracer.roots[0].children], ["inner-1", "inner-2"])
        self.assertEqual(tracer.roots[0].children[0].parent.name, "outer")

    def test_render_shows_tree_latency_and_errors(self):
        tracer = Tracer()
        with self.assertRaises(ValueError):
            with tracer.span("outer"):
                with tracer.span("boom"):
                    raise ValueError("bad input")
        rendered = tracer.render()
        self.assertIn("outer", rendered)
        self.assertIn("  boom", rendered)
        self.assertIn("ms]", rendered)
        self.assertIn("!! ValueError: bad input", rendered)
        self.assertGreaterEqual(tracer.roots[0].duration_ms, 0.0)

    def test_sinks_see_lifo_start_end_order(self):
        sink = RecordingSink()
        tracer = Tracer(sinks=[sink])
        with tracer.span("outer"):
            with tracer.span("inner"):
                pass
        self.assertEqual(
            sink.events,
            [("start", "outer"), ("start", "inner"), ("end", "inner"), ("end", "outer")],
        )

    def test_wrap_tools_traces_a_tool_loop_without_changing_it(self):
        tracer = Tracer()
        tools = tracer.wrap_tools({"lookup": lambda _: "evidence"})

        def policy(goal, trace):
            if not trace:
                return {"tool": "lookup", "input": "q"}
            return {"final": trace[-1]["observation"]}

        with tracer.span("loop"):
            result = run_tool_loop("goal", policy, tools, max_steps=2)
        self.assertTrue(result.completed)
        self.assertEqual(result.answer, "evidence")
        loop_span = tracer.roots[0]
        self.assertEqual([c.name for c in loop_span.children], ["tool:lookup"])
        self.assertEqual(loop_span.children[0].attributes["observation_chars"], len("evidence"))

    def test_deep_agent_emits_root_and_tool_spans_when_traced(self):
        tracer = Tracer(sinks=[RecordingSink()])

        def policy(goal, todos, trace):
            if not todos.items:
                return {"tool": "write_todos", "input": {"add": ["note"]}}
            if todos.next_pending() is None:
                return {"final": "done"}
            if trace and trace[-1].get("tool") == "write_file":
                return {"tool": "write_todos", "input": {"done": 0}}
            return {"tool": "write_file", "input": {"path": "/n.md", "text": "x"}}

        agent = DeepAgent(
            "traced",
            system_prompt=compose_system_prompt("role"),
            policy=policy,
            fs=VirtualFS(),
            tracer=tracer,
        )
        result = agent.run("goal", run_id="t1")
        self.assertTrue(result.completed)
        root = tracer.roots[0]
        self.assertEqual(root.name, "agent:traced")
        self.assertEqual(root.attributes["run_id"], "t1")
        self.assertEqual(
            [c.name for c in root.children],
            ["tool:write_todos", "tool:write_file", "tool:write_todos"],
        )
        self.assertIn("observation_chars", root.children[1].attributes)

    def test_deep_agent_without_tracer_is_unchanged(self):
        agent = DeepAgent(
            "plain",
            system_prompt="role",
            policy=lambda goal, todos, trace: {"final": "ok"},
        )
        self.assertTrue(agent.run("goal").completed)
        self.assertIsNone(agent.tracer)


if __name__ == "__main__":
    unittest.main()
