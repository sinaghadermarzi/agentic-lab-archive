"""Metadata for the agent-protocol landscape notebook.

Each entry answers: which boundary does the protocol standardize, who
governs it, and how real is adoption. Status strings were checked against
the linked primary sources in August 2026; re-verify before citing them,
because this space moves quickly.
"""

from importlib.util import find_spec

PROTOCOLS = {
    "MCP": {
        "layer": "agent <-> tools and context",
        "standardizes": "discovery and invocation of tools, resources, and prompts",
        "governance": "open standard started by Anthropic; Linux Foundation ecosystem",
        "status": "de facto standard for tool access; SDKs and servers everywhere",
        "source": "https://modelcontextprotocol.io/",
    },
    "A2A": {
        "layer": "agent <-> agent",
        "standardizes": "Agent Card discovery, task lifecycle, message/artifact exchange",
        "governance": "A2A project, Linux Foundation (donated by Google, 2025)",
        "status": "v1.0; 150+ member orgs; shipped in major cloud agent platforms",
        "source": "https://a2a-protocol.org/",
    },
    "AG-UI": {
        "layer": "agent <-> user-facing app",
        "standardizes": "event stream between agent backends and frontends (~16 event types)",
        "governance": "open project initiated by CopilotKit (ag-ui-protocol org)",
        "status": "first-party integrations across most Track B frameworks; TypeScript-centric",
        "source": "https://github.com/ag-ui-protocol/ag-ui",
    },
    "AP2": {
        "layer": "agent <-> payments",
        "standardizes": "mandates and flows for authorized agent-initiated payments",
        "governance": "Google-led open project with payments-industry partners",
        "status": "emerging; specification and samples, pre-production",
        "source": "https://github.com/google-agentic-commerce/AP2",
    },
    "AGNTCY": {
        "layer": "identity, discovery, and messaging infrastructure",
        "standardizes": "agent schemas (OASF), directory, identity, SLIM messaging",
        "governance": "Linux Foundation collective (Cisco, Dell, Red Hat, Google Cloud, ...)",
        "status": "component projects with early adoption; infrastructure layer",
        "source": "https://github.com/agntcy",
    },
    "ANP": {
        "layer": "agent <-> agent (decentralized)",
        "standardizes": "DID-based identity (did:wba) and open-network agent discovery",
        "governance": "open community",
        "status": "spec v1.1; emerging, limited production adoption",
        "source": "https://github.com/agent-network-protocol/AgentNetworkProtocol",
    },
    "ACP (IBM/BeeAI)": {
        "layer": "agent <-> agent (REST)",
        "standardizes": "historical: REST-first agent communication",
        "governance": "was Linux Foundation via BeeAI",
        "status": "merged into A2A (August 2025); do not target for new work",
        "source": "https://lfaidata.foundation/communityblog/2025/08/29/acp-joins-forces-with-a2a-under-the-linux-foundations-lf-ai-data/",
    },
    "Agent Client Protocol": {
        "layer": "code editor <-> coding agent",
        "standardizes": "editor/agent sessions for AI coding tools (unrelated to the ACP above)",
        "governance": "Zed Industries, open source",
        "status": "v1 stable; adopted by editors and coding agents; SDKs in 5 languages",
        "source": "https://github.com/zed-industries/agent-client-protocol",
    },
}


def landscape_table() -> str:
    """Render the landscape as a fixed-width text table for notebook output."""

    headers = ("Protocol", "Boundary", "Status")
    rows = [(name, info["layer"], info["status"]) for name, info in PROTOCOLS.items()]
    widths = [max(len(r[i]) for r in [headers, *rows]) for i in range(3)]
    lines = [
        "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)),
        "  ".join("-" * widths[i] for i in range(3)),
    ]
    lines += ["  ".join(r[i].ljust(widths[i]) for i in range(3)) for r in rows]
    return "\n".join(lines)


def sdk_availability() -> dict[str, bool]:
    """Which protocol SDKs covered hands-on in this lab are importable."""

    return {"mcp": find_spec("mcp") is not None, "a2a": find_spec("a2a") is not None}
