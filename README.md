# Agentic Frameworks & Patterns Lab

An executable, framework-aware lab for learning how modern agentic systems are actually assembled.

The lab keeps the durable ideas separate from fast-moving SDK syntax:

> deterministic workflow spine + bounded agentic decisions + objective verification + human authority at consequential boundaries

## What is inside

- A progressive curriculum from a local tool loop to multi-agent orchestration.
- Runnable Python notebooks that default to deterministic, offline demonstrations.
- Optional, clearly gated framework cells for LangGraph, OpenAI Agents SDK, PydanticAI, Google ADK, Microsoft Agent Framework, CrewAI, AWS Strands Agents, and LlamaIndex Workflows.
- A framework comparison notebook with primary-source links, trade-offs, and an extensible adapter map for TypeScript ecosystems such as Mastra and Vercel AI SDK.
- A Model Context Protocol (MCP) module: an offline teaching double of the protocol, plus a hands-on notebook that builds and consumes a real MCP server with the official SDK over stdio — no API key required.
- Tests for the local pattern implementations and notebook integrity.
- No API keys, private data, or generated credentials committed to the repository.

## Start here

1. Read [`docs/CURRICULUM.md`](docs/CURRICULUM.md).
2. Create an environment with `python -m venv .venv` and `pip install -e '.[dev]'`.
3. Run `python -m unittest discover -s tests -v`.
4. Launch Jupyter and open notebooks in order:

```bash
jupyter lab
```

The notebooks are usable without an LLM provider. Live framework cells are skipped unless the optional package and its environment variables are present.

## Notebook map

| Notebook | Focus | Default mode |
| --- | --- | --- |
| `00_setup_and_safety.ipynb` | Environment, secret hygiene, permissions, budgets | Offline |
| `01_tool_loop_react.ipynb` | Observe → decide → act → observe | Offline |
| `02_workflow_spine.ipynb` | Staged workflow, routing, parallel fan-out/fan-in | Offline |
| `03_verification_and_adversarial.ipynb` | Evaluator–optimizer, independent verifier, red-team panel | Offline |
| `04_delegation_and_handoffs.ipynb` | Agent-as-tool, supervisor–worker, handoff semantics | Offline |
| `05_state_human_gates_and_budgets.ipynb` | Checkpoints, approval gates, blackboard state, termination | Offline |
| `06_framework_comparison.ipynb` | Framework roles, sources, capability matrix | Offline |
| `07_langgraph.ipynb` | Stateful graph workflow | Optional live |
| `08_openai_agents_sdk.ipynb` | Tools, agents-as-tools, handoffs, guardrails | Optional live |
| `09_pydanticai.ipynb` | Typed dependencies and structured outputs | Optional live |
| `10_google_adk.ipynb` | Agents and workflow orchestration | Optional live |
| `11_microsoft_agent_framework.ipynb` | Functional workflows and orchestration | Optional live |
| `12_crewai.ipynb` | Crews and Flows | Optional live |
| `13_strands_agents.ipynb` | Model-driven agents and state | Optional live |
| `14_llamaindex_workflows.ipynb` | Retrieval-oriented event workflows | Optional live |
| `15_capstone_research_review.ipynb` | End-to-end hybrid architecture | Offline |
| `16_mcp_concepts.ipynb` | Model Context Protocol roles, primitives, wire format | Offline |
| `17_mcp_python_sdk.ipynb` | Build and consume an MCP server over stdio | Optional live (no API key) |

## Optional framework installs

The base install intentionally stays small. Install only what you want to explore:

```bash
pip install -e '.[langgraph]'
pip install -e '.[openai-agents]'
pip install -e '.[pydanticai]'
pip install -e '.[google-adk]'
pip install -e '.[microsoft-agent-framework]'
pip install -e '.[crewai]'
pip install -e '.[strands]'
pip install -e '.[llamaindex]'
pip install -e '.[mcp]'
```

For live calls, set provider credentials in your shell or a local `.env` file that is not committed. See `.env.example`.

## Design principles

- **Evidence over folklore.** Framework notebooks link to official documentation or original papers and keep claims narrow.
- **Offline first.** The learning path and tests do not require network access or paid APIs.
- **Bounded autonomy.** Every loop has explicit step, retry, cost, and permission boundaries.
- **Objective feedback.** Prefer tests, schemas, policy rules, and authoritative retrieval over self-approval.
- **Small composable pieces.** Add a new framework adapter or pattern without rewriting the curriculum.

## Sources

Framework references are collected in [`docs/SOURCES.md`](docs/SOURCES.md). The pattern examples draw from the original [ReAct paper](https://arxiv.org/abs/2210.03629) and [Anthropic's Building Effective AI Agents](https://resources.anthropic.com/building-effective-ai-agents), with implementation links kept next to each notebook.

## Contributing

Add new material as a small notebook plus a deterministic test or fixture where practical. Keep secrets out of notebooks, avoid committing notebook outputs containing sensitive data, and record the source URL for framework-specific claims.

## License

MIT. See [`LICENSE`](LICENSE).
