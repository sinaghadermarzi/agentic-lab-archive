# Agentic Frameworks & Patterns Lab

An executable, framework-aware lab for learning how modern agentic systems are actually assembled.

The lab keeps the durable ideas separate from fast-moving SDK syntax:

> deterministic workflow spine + bounded agentic decisions + objective verification + human authority at consequential boundaries

## What is inside

- A progressive curriculum from a local tool loop to multi-agent orchestration.
- Runnable Python notebooks that default to deterministic, offline demonstrations.
- Optional, clearly gated framework cells for LangGraph, OpenAI Agents SDK, PydanticAI, Google ADK, Microsoft Agent Framework, CrewAI, AWS Strands Agents, LlamaIndex Workflows, Hugging Face smolagents, and Agno — with AutoGen and Semantic Kernel covered as lineage of Microsoft Agent Framework.
- A framework comparison notebook with primary-source links, trade-offs, and an extensible adapter map for TypeScript ecosystems such as Mastra and Vercel AI SDK.
- Protocol modules for MCP and A2A: offline teaching doubles of each protocol, hands-on notebooks with the official SDKs (stdio / localhost, no API keys required), and a sourced survey of the wider landscape (AG-UI, AP2, AGNTCY, ANP, and the two unrelated "ACP"s).
- A deep-agents track: the four context disciplines for long-horizon work (plan artifacts, filesystem offloading, isolated sub-agents, skills) built offline with measurable context windows, an end-to-end run, interrupt/resume/compaction, and the `deepagents` package.
- Observability: a ~100-line span tracer (`lab_core.trace`) that turns any tool loop or deep agent into a rendered span tree, plus `notebooks/obs.py` (ported from the dspy-lab course) bridging the same spans into MLflow and Arize Phoenix — local UIs found-or-started from a cell, no accounts, no API keys.
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
| `18_a2a_concepts.ipynb` | Agent2Agent cards, task lifecycle, delegation | Offline |
| `19_a2a_python_sdk.ipynb` | Build and consume an A2A agent over localhost | Optional live (no API key) |
| `20_protocol_landscape.ipynb` | AG-UI, AP2, AGNTCY, ANP, ACP history | Offline |
| `21_smolagents.ipynb` | Code-as-action agents, sandboxed execution | Optional live |
| `22_agno.ipynb` | Agents, teams, and the AgentOS runtime | Optional live |
| `23_deep_agents_concepts.ipynb` | Plan artifacts, context offload, isolation, skills | Offline |
| `24_deep_agent_run.ipynb` | A deep agent end to end, with context economics | Offline |
| `25_deep_agent_survival.ipynb` | Interrupt, resume from artifacts, compaction | Offline |
| `26_deepagents.ipynb` | LangChain deepagents harness | Optional live |
| `27_observability.ipynb` | Span trees, MLflow and Phoenix tracing | Offline core + optional local UIs (no API key) |

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
pip install -e '.[smolagents]'
pip install -e '.[agno]'
pip install -e '.[mcp]'
pip install -e '.[a2a]'
pip install -e '.[deepagents]'
pip install -e '.[obs]'
```

**Observability (optional).** Notebook 27 teaches tracing. Any notebook's run can be traced by attaching a `lab_core.trace.Tracer` (deep agents take a `tracer=` argument; plain tool loops use `tracer.wrap_tools(...)`) — `tracer.render()` prints the span tree with no installs at all. With the `obs` extra, `import obs` then `obs.enable_mlflow()` + `obs.mlflow_ui()` or `obs.enable_phoenix()` mirror the same spans into a local UI; the cell ends by printing the localhost link where the traces appear. The `obs.py` helper (ported from dspy-lab) makes this safe to leave and return to: sessions are dated (`agentic-lab-YYYY-MM-DD`) so days never collide, the MLflow store is pinned inside the repo (gitignored) and falls back cleanly if a remnant file is unusable, and the UIs are found-or-started from a cell — reusing a healthy server, skipping ports held by strangers. No terminal, no accounts, no extra API keys. Phoenix keeps its data in `~/.phoenix`.

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
