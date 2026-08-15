import sys
import unittest
from importlib.util import find_spec
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "notebooks"))

import llm  # noqa: E402
from lab_core.patterns import run_tool_loop  # noqa: E402

llm._LOADED = True  # tests control the environment directly; never read a local .env

ENV_KEYS = ("MODEL", "STRONG_MODEL", "OPENROUTER_API_KEY", "OPENAI_API_KEY")
CLEAN = {key: "" for key in ENV_KEYS}


class LlmHelperTests(unittest.TestCase):
    def test_parse_action_handles_fences_and_garbage(self):
        self.assertEqual(
            llm.parse_action('{"tool": "lookup", "input": "x"}'), {"tool": "lookup", "input": "x"}
        )
        fenced = 'Sure!\n```json\n{"final": "done"}\n```'
        self.assertEqual(llm.parse_action(fenced), {"final": "done"})
        self.assertIsNone(llm.parse_action("no json here"))
        self.assertIsNone(llm.parse_action("[1, 2, 3]"))

    def test_model_defaults_and_env_overrides(self):
        with patch.dict("os.environ", CLEAN):
            self.assertEqual(llm.model(), llm.DEFAULT_MODEL)
            self.assertEqual(llm.model(strong=True), llm.DEFAULT_STRONG_MODEL)
            self.assertFalse(llm.ready())
        with patch.dict(
            "os.environ", {**CLEAN, "MODEL": "openai/gpt-4o-mini", "OPENAI_API_KEY": "k"}
        ):
            self.assertEqual(llm.model(), "openai/gpt-4o-mini")
            self.assertTrue(llm.ready())
        with patch.dict("os.environ", {**CLEAN, "OPENROUTER_API_KEY": "k"}):
            self.assertTrue(llm.ready())  # default model routes through OpenRouter

    def test_ready_matches_the_configured_provider(self):
        # An OpenRouter key must NOT satisfy a direct provider's credential check.
        with patch.dict(
            "os.environ", {**CLEAN, "MODEL": "openai/gpt-4o-mini", "OPENROUTER_API_KEY": "k"}
        ):
            self.assertFalse(llm.ready())
        with patch.dict("os.environ", {**CLEAN, "MODEL": "anthropic/claude-sonnet-5"}):
            self.assertFalse(llm.ready())
        with patch.dict(
            "os.environ", {**CLEAN, "MODEL": "anthropic/claude-sonnet-5", "ANTHROPIC_API_KEY": "k"}
        ):
            self.assertTrue(llm.ready())
        with patch.dict("os.environ", {**CLEAN, "MODEL": "ollama_chat/llama3"}):
            self.assertTrue(llm.ready())  # local providers need no key

    @unittest.skipUnless(find_spec("litellm"), "litellm not installed")
    def test_complete_mock_runs_full_path_without_key(self):
        with patch.dict("os.environ", CLEAN):
            self.assertEqual(
                llm.complete("say hi", mock="hello from the mock"), "hello from the mock"
            )

    @unittest.skipUnless(find_spec("litellm"), "litellm not installed")
    def test_llm_policy_drives_tool_loop_via_mocks(self):
        policy = llm.llm_policy(
            {"lookup": "Look up a fact."},
            mocks=[
                '{"tool": "lookup", "input": "react"}',
                '{"final": "ReAct interleaves reasoning and acting."}',
            ],
        )
        with patch.dict("os.environ", CLEAN):
            result = run_tool_loop("explain", policy, {"lookup": lambda _: "evidence"}, max_steps=3)
        self.assertTrue(result.completed)
        self.assertEqual(result.answer, "ReAct interleaves reasoning and acting.")
        self.assertEqual(result.trace[0]["tool"], "lookup")

    @unittest.skipUnless(find_spec("litellm"), "litellm not installed")
    def test_llm_policy_survives_unparseable_reply(self):
        policy = llm.llm_policy(
            {"lookup": "Look up a fact."}, mocks=["I would love to help but no JSON"]
        )
        with patch.dict("os.environ", CLEAN):
            result = run_tool_loop("explain", policy, {"lookup": lambda _: "evidence"}, max_steps=3)
        self.assertTrue(result.completed)
        self.assertIn("not a valid action", result.answer)


if __name__ == "__main__":
    unittest.main()
