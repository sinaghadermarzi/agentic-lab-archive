"""Framework metadata used by the comparison notebook."""

from importlib.util import find_spec

FRAMEWORKS = {
    "LangGraph": {
        "package": "langgraph",
        "extra": "langgraph",
        "fit": "stateful graph orchestration, checkpoints, routing, and human gates",
        "source": "https://docs.langchain.com/oss/python/langgraph/install",
    },
    "OpenAI Agents SDK": {
        "package": "agents",
        "extra": "openai-agents",
        "fit": "small agent/tool/handoff/guardrail primitives with tracing",
        "source": "https://openai.github.io/openai-agents-python/",
    },
    "PydanticAI": {
        "package": "pydantic_ai",
        "extra": "pydanticai",
        "fit": "typed Python services, dependencies, tools, and structured outputs",
        "source": "https://ai.pydantic.dev/",
    },
    "Google ADK": {
        "package": "google.adk",
        "extra": "google-adk",
        "fit": "Gemini/Google Cloud agents and explicit workflow orchestration",
        "source": "https://google.github.io/adk-docs/",
    },
    "Microsoft Agent Framework": {
        "package": "agent_framework",
        "extra": "microsoft-agent-framework",
        "fit": "Python/.NET enterprise agents, workflows, orchestration, and HITL",
        "source": "https://learn.microsoft.com/en-us/agent-framework/",
    },
    "CrewAI": {
        "package": "crewai",
        "extra": "crewai",
        "fit": "role-based crews and event-driven Flows",
        "source": "https://docs.crewai.com/",
    },
    "AWS Strands Agents": {
        "package": "strands",
        "extra": "strands",
        "fit": "model-driven agents with AWS/Bedrock integrations",
        "source": "https://strandsagents.com/docs/user-guide/quickstart/overview/",
    },
    "LlamaIndex Workflows": {
        "package": "llama_index.core.workflow",
        "extra": "llamaindex",
        "fit": "event-driven document, retrieval, and knowledge workflows",
        "source": "https://docs.llamaindex.ai/en/stable/module_guides/workflow/",
    },
    "Mastra": {
        "package": "(TypeScript)",
        "extra": "see docs",
        "fit": "TypeScript agents, workflows, memory, evals, and observability",
        "source": "https://mastra.ai/docs",
    },
    "Vercel AI SDK": {
        "package": "(TypeScript)",
        "extra": "see docs",
        "fit": "TypeScript/Next.js tool loops, streaming UI, and workflow agents",
        "source": "https://ai-sdk.dev/docs/agents",
    },
    "Claude tooling": {
        "package": "anthropic (Python SDK)",
        "extra": "see docs",
        "fit": "tool loops and long-running coding/computer-work agents",
        "source": "https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner",
    },
}


def availability() -> dict[str, bool]:
    """Return import availability without importing or initializing providers."""

    result: dict[str, bool] = {}
    for name, info in FRAMEWORKS.items():
        package = info["package"]
        if package.startswith("("):
            continue
        try:
            result[name] = find_spec(package) is not None
        except ModuleNotFoundError:
            result[name] = False
    return result
