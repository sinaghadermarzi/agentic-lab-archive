"""Optional LLM helpers for the agentic-lab notebooks (taught in notebook 28).

Same conventions as the dspy-lab course, so one ``.env`` serves both repos:
``OPENROUTER_API_KEY`` is the single required key (the default models route
through OpenRouter), and ``MODEL`` / ``STRONG_MODEL`` accept any LiteLLM
provider string (``openrouter/...``, ``openai/...``, ``anthropic/...``,
``ollama_chat/...``). Unset variables fall back to the same defaults as
dspy-lab. Where dspy-lab hands these to ``dspy.LM``, this lab has no DSPy —
``complete()`` calls LiteLLM directly, and ``llm_policy()`` adapts a model
into the lab's ``choose_action`` contract so the deterministic policies of
notebooks 01–25 can be swapped for a live decision boundary.

Every entry point takes a ``mock`` argument that routes through LiteLLM's
``mock_response`` — the full code path without a key or network — which is
how the tests exercise this module and how notebook 28's offline cell works.
"""

import getpass
import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_MODEL = "openrouter/deepseek/deepseek-v3.2"
DEFAULT_STRONG_MODEL = "openrouter/deepseek/deepseek-v4-flash"

_LOADED = False


def _load_env() -> None:
    """Read ``.env`` at the repo root once; missing file or package is fine."""
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass  # plain environment variables still work


def model(strong: bool = False) -> str:
    _load_env()
    if strong:  # blank .env lines count as unset
        return os.environ.get("STRONG_MODEL") or DEFAULT_STRONG_MODEL
    return os.environ.get("MODEL") or DEFAULT_MODEL


def ready() -> bool:
    """True when a key for the configured model's provider is present."""
    _load_env()
    needed = "OPENROUTER_API_KEY" if model().startswith("openrouter/") else "OPENAI_API_KEY"
    return bool(os.environ.get(needed) or os.environ.get("OPENROUTER_API_KEY"))


def configure() -> None:
    """Interactive fallback, dspy-lab style: prompt for the key if .env lacks one."""
    _load_env()
    if not ready():
        os.environ["OPENROUTER_API_KEY"] = getpass.getpass("OpenRouter API key: ")
    print(f"llm: model={model()!r} strong={model(strong=True)!r} ready={ready()}")


def complete(
    prompt: str,
    *,
    system: str | None = None,
    strong: bool = False,
    max_tokens: int = 1000,
    mock: str | None = None,
) -> str:
    """One LiteLLM completion; ``mock`` exercises the full path with no key/network."""
    import litellm

    _load_env()
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
    response = litellm.completion(
        model=model(strong=strong),
        messages=messages,
        max_tokens=max_tokens,
        **({"mock_response": mock} if mock is not None else {}),
    )
    return response.choices[0].message.content or ""


def parse_action(text: str) -> dict[str, Any] | None:
    """Extract the first JSON object from a model reply (code fences tolerated)."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match is None:
        return None
    try:
        action = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return action if isinstance(action, dict) else None


def llm_policy(
    tools: Mapping[str, str],
    *,
    system: str | None = None,
    strong: bool = False,
    mocks: list[str] | None = None,
) -> Callable[[str, list[dict[str, Any]]], dict[str, Any]]:
    """Adapt a model into the lab's ``choose_action`` contract (notebook 01).

    ``tools`` maps tool name -> one-line description (the catalog the model
    sees). The returned policy asks for exactly one JSON action per step —
    ``{"tool": ..., "input": ...}`` or ``{"final": ...}`` — and turns an
    unparseable reply into a final answer that says so, so the loop always
    terminates inside its step budget. ``mocks`` scripts the replies for
    keyless runs and tests.
    """
    catalog = "\n".join(f"- {name}: {desc}" for name, desc in tools.items())
    script = list(mocks or [])

    def policy(goal: str, trace: list[dict[str, Any]]) -> dict[str, Any]:
        recent = "\n".join(
            f"step {t['step']}: {t.get('tool', 'final')} -> {str(t.get('observation', ''))[:200]}"
            for t in trace[-5:]
        )
        prompt = (
            f"Goal: {goal}\n\nTools:\n{catalog}\n\nTrace so far:\n{recent or '(none)'}\n\n"
            'Reply with ONE JSON object only: {"tool": "<name>", "input": <value>} '
            'to act, or {"final": "<answer>"} when the goal is met.'
        )
        mock = script.pop(0) if script else None
        reply = complete(prompt, system=system, strong=strong, mock=mock)
        action = parse_action(reply)
        if action is None or not ({"tool", "final"} & action.keys()):
            return {"final": f"model reply was not a valid action: {reply[:120]!r}"}
        return action

    return policy
