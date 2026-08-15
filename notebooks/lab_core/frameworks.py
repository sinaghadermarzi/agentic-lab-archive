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
    "smolagents": {
        "package": "smolagents",
        "extra": "smolagents",
        "fit": "minimal code-first agents whose actions are Python snippets (CodeAgent)",
        "source": "https://huggingface.co/docs/smolagents",
    },
    "Agno": {
        "package": "agno",
        "extra": "agno",
        "fit": "agents and teams plus the AgentOS runtime/control plane for operating them",
        "source": "https://docs.agno.com/",
    },
    "LlamaIndex Workflows": {
        "package": "llama_index.core.workflow",
        "extra": "llamaindex",
        "fit": "event-driven document, retrieval, and knowledge workflows",
        "source": "https://docs.llamaindex.ai/en/stable/module_guides/workflow/",
    },
    "LangChain Deep Agents": {
        "package": "deepagents",
        "extra": "deepagents",
        "fit": "planning, filesystem offload, and sub-agent defaults for long-horizon agents on LangGraph",
        "source": "https://docs.langchain.com/oss/python/deepagents/overview",
    },
    "MCP Python SDK": {
        "package": "mcp",
        "extra": "mcp",
        "fit": "open protocol for portable tool/resource/prompt servers across hosts",
        "source": "https://modelcontextprotocol.io/",
    },
    "A2A Python SDK": {
        "package": "a2a",
        "extra": "a2a",
        "fit": "open protocol + SDK for agent-to-agent interop across vendors",
        "source": "https://a2a-protocol.org/",
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
    "Claude Agent SDK": {
        "package": "claude_agent_sdk",
        "extra": "see docs",
        "fit": "harness-grade agent loop (Claude Code) as a library, with hooks and in-process MCP tools",
        "source": "https://platform.claude.com/docs/en/agent-sdk/python",
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
