import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "notebooks"))

from lab_core.patterns import (  # noqa: E402
    ApprovalGate,
    Budget,
    CheckpointStore,
    evaluate_optimize,
    fan_out_fan_in,
    route,
    run_tool_loop,
)


class PatternTests(unittest.TestCase):
    def test_tool_loop_completes_and_records_observation(self):
        def policy(goal, trace):
            return {"tool": "lookup", "input": "react"} if not trace else {"final": trace[-1]["observation"]}

        result = run_tool_loop("learn", policy, {"lookup": lambda _: "evidence"}, max_steps=2)
        self.assertTrue(result.completed)
        self.assertEqual(result.answer, "evidence")
        self.assertEqual(result.trace[0]["observation"], "evidence")

    def test_tool_loop_has_hard_budget(self):
        result = run_tool_loop("never finish", lambda *_: {"tool": "noop"}, {"noop": lambda _: "ok"}, max_steps=1)
        self.assertFalse(result.completed)
        self.assertIn("budget", result.error)

    def test_route_and_fan_out_fan_in(self):
        self.assertEqual(route("a", lambda _: "x", {"x": lambda value: value.upper()}), "A")
        self.assertEqual(fan_out_fan_in([1, 2, 3], lambda x: x * 2, sum), 12)

    def test_evaluator_optimizer_uses_feedback(self):
        def evaluate(value):
            return {"pass": value == "good", "issues": ["not good"]}

        value, reports = evaluate_optimize("bad", evaluate, lambda _, __: "good", max_rounds=2)
        self.assertEqual(value, "good")
        self.assertEqual(len(reports), 2)

    def test_state_approval_and_budget(self):
        store = CheckpointStore()
        store.save("run", {"step": 1})
        self.assertEqual(store.load("run"), {"step": 1})
        self.assertEqual(ApprovalGate(lambda item: item["risk"] == "low").require({"risk": "low"})["risk"], "low")
        budget = Budget(max_steps=1)
        budget.charge()
        with self.assertRaises(RuntimeError):
            budget.charge()


if __name__ == "__main__":
    unittest.main()
