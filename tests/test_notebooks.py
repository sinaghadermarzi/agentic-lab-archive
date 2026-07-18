import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class NotebookTests(unittest.TestCase):
    def test_expected_notebooks_are_valid_json(self):
        expected = [
            "00_setup_and_safety.ipynb",
            "01_tool_loop_react.ipynb",
            "02_workflow_spine.ipynb",
            "03_verification_and_adversarial.ipynb",
            "04_delegation_and_handoffs.ipynb",
            "05_state_human_gates_and_budgets.ipynb",
            "06_framework_comparison.ipynb",
            "07_langgraph.ipynb",
            "08_openai_agents_sdk.ipynb",
            "09_pydanticai.ipynb",
            "10_google_adk.ipynb",
            "11_microsoft_agent_framework.ipynb",
            "12_crewai.ipynb",
            "13_strands_agents.ipynb",
            "14_llamaindex_workflows.ipynb",
            "15_capstone_research_review.ipynb",
        ]
        for name in expected:
            path = ROOT / "notebooks" / name
            self.assertTrue(path.exists(), name)
            notebook = json.loads(path.read_text())
            self.assertEqual(notebook["nbformat"], 4)
            self.assertGreaterEqual(len(notebook["cells"]), 2)

    def test_no_secret_like_files_are_tracked_in_tree(self):
        self.assertFalse(list(ROOT.rglob(".env")))
        self.assertFalse(list(ROOT.rglob("*.pem")))
        self.assertFalse(list(ROOT.rglob("*.key")))


if __name__ == "__main__":
    unittest.main()
