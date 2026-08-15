# Agentic Frameworks & Patterns Lab

An executable, framework-aware lab for learning how modern agentic systems are actually assembled.

The lab keeps the durable ideas separate from fast-moving SDK syntax:

> deterministic workflow spine + bounded agentic decisions + objective verification + human authority at consequential boundaries

## What is inside

- A progressive curriculum from a local tool loop to multi-agent orchestration, protocols, deep agents, observability, and live LLM policies.
- Runnable Python notebooks: every pattern ships with a deterministic reference implementation you can step through, and live cells activate as soon as the matching extra and credentials are in place.
- Framework lessons for LangGraph, OpenAI Agents SDK, PydanticAI, Google ADK, Microsoft Agent Framework, CrewAI, AWS Strands Agents, LlamaIndex Workflows, Hugging Face smolagents, and Agno — with AutoGen and Semantic Kernel covered as lineage of Microsoft Agent Framework.
- A framework comparison notebook with primary-source links, trade-offs, and an extensible adapter map for TypeScript ecosystems such as Mastra and Vercel AI SDK.
- Protocol modules for MCP and A2A: teaching doubles of each protocol with every wire message visible, hands-on notebooks with the official SDKs (stdio / localhost, no API keys required), and a sourced survey of the wider landscape (AG-UI, AP2, AGNTCY, ANP, and the two unrelated "ACP"s).
- A deep-agents track: the four context disciplines for long-horizon work (plan artifacts, filesystem offloading, isolated sub-agents, skills) with measurable context windows, an end-to-end run, interrupt/resume/compaction, and the `deepagents` package.
- Observability: a ~100-line span tracer (`lab_core.trace`) that turns any tool loop or deep agent into a rendered span tree, plus `notebooks/obs.py` (ported from the dspy-lab course) bridging the same spans into MLflow and Arize Phoenix — local UIs found-or-started from a cell, no accounts, no API keys.
- One `.env` for live LLM use across the whole lab (LiteLLM provider strings, OpenRouter default — the same conventions as dspy-lab).
- Tests for the pattern implementations and notebook integrity.
- No API keys, private data, or generated credentials committed to the repository.

## First-time setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'                  # core install: every lesson's reference path + tests
python -m unittest discover -s tests     # should be all green
cp .env.example .env                     # then add your OPENROUTER_API_KEY for live LLM cells
jupyter lab
```

That is a complete setup: read [`docs/CURRICULUM.md`](docs/CURRICULUM.md) and open the notebooks in order. Cells that use an optional SDK tell you exactly what to install — each notebook that needs an extra names it in its first cell — or grab everything up front:

```bash
pip install -e '.[all]'                  # every optional integration at once
```

The extras are mutually compatible (the `all` set resolves cleanly), with one caveat: satisfying every framework at once can pin some of them below their newest release (CrewAI in particular resolves older under `[all]`). Install a framework's own extra in a dedicated environment when you want its latest version.

## Notebook map

| Notebook | Focus | Setup beyond `[dev]` |
| --- | --- | --- |
| `00_setup_and_safety.ipynb` | Environment, secret hygiene, permissions, budgets | — |
| `01_tool_loop_react.ipynb` | Observe → decide → act → observe | — |
| `02_workflow_spine.ipynb` | Staged workflow, routing, parallel fan-out/fan-in | — |
| `03_verification_and_adversarial.ipynb` | Evaluator–optimizer, independent verifier, red-team panel | — |
| `04_delegation_and_handoffs.ipynb` | Agent-as-tool, supervisor–worker, handoff semantics | — |
| `05_state_human_gates_and_budgets.ipynb` | Checkpoints, approval gates, blackboard state, termination | — |
| `06_framework_comparison.ipynb` | Framework roles, sources, capability matrix | — |
| `07_langgraph.ipynb` | Stateful graph workflow | `[langgraph]` + key |
| `08_openai_agents_sdk.ipynb` | Tools, agents-as-tools, handoffs, guardrails | `[openai-agents]` + key |
| `09_pydanticai.ipynb` | Typed dependencies and structured outputs | `[pydanticai]` + key |
| `10_google_adk.ipynb` | Agents and workflow orchestration | `[google-adk]` + credentials |
| `11_microsoft_agent_framework.ipynb` | Functional workflows and orchestration; AutoGen/SK lineage | `[microsoft-agent-framework]` + credentials |
| `12_crewai.ipynb` | Crews and Flows | `[crewai]` + key |
| `13_strands_agents.ipynb` | Model-driven agents and state | `[strands]` + credentials |
| `14_llamaindex_workflows.ipynb` | Retrieval-oriented event workflows | `[llamaindex]` + key |
| `15_capstone_research_review.ipynb` | End-to-end hybrid architecture | — |
| `16_mcp_concepts.ipynb` | Model Context Protocol roles, primitives, wire format | — |
| `17_mcp_python_sdk.ipynb` | Build and consume an MCP server over stdio | `[mcp]` (no key) |
| `18_a2a_concepts.ipynb` | Agent2Agent cards, task lifecycle, delegation | — |
| `19_a2a_python_sdk.ipynb` | Build and consume an A2A agent over localhost | `[a2a]` (no key) |
| `20_protocol_landscape.ipynb` | AG-UI, AP2, AGNTCY, ANP, ACP history | — |
| `21_smolagents.ipynb` | Code-as-action agents, sandboxed execution | `[smolagents]` + key |
| `22_agno.ipynb` | Agents, teams, and the AgentOS runtime | `[agno]` + key |
| `23_deep_agents_concepts.ipynb` | Plan artifacts, context offload, isolation, skills | — |
| `24_deep_agent_run.ipynb` | A deep agent end to end, with context economics | — |
| `25_deep_agent_survival.ipynb` | Interrupt, resume from artifacts, compaction | — |
| `26_deepagents.ipynb` | LangChain deepagents harness | `[deepagents]` + key |
| `27_observability.ipynb` | Span trees, MLflow and Phoenix tracing | `[obs]` for the UIs (no key) |
| `28_live_llm_policy.ipynb` | LiteLLM/OpenRouter config, LLM as the decision boundary | `[llm]` + key for the live cell |

**Observability.** Notebook 27 teaches tracing. Any notebook's run can be traced by attaching a `lab_core.trace.Tracer` (deep agents take a `tracer=` argument; plain tool loops use `tracer.wrap_tools(...)`) — `tracer.render()` prints the span tree with no installs at all. With the `obs` extra, `import obs` then `obs.enable_mlflow()` + `obs.mlflow_ui()` or `obs.enable_phoenix()` mirror the same spans into a local UI; the cell ends by printing the localhost link where the traces appear. The `obs.py` helper (ported from dspy-lab) makes this safe to leave and return to: sessions are dated (`agentic-lab-YYYY-MM-DD`) so days never collide, the MLflow store is pinned inside the repo (gitignored) and falls back cleanly if a remnant file is unusable, and the UIs are found-or-started from a cell — reusing a healthy server, skipping ports held by strangers. No terminal, no accounts, no extra API keys. Phoenix keeps its data in `~/.phoenix`.

**Keys & models — one `.env` for live LLM use.** `cp .env.example .env`, set `OPENROUTER_API_KEY`, and every live cell follows the shared `MODEL` / `STRONG_MODEL` choice — the same conventions as the dspy-lab course, so one `.env` serves both repositories. The defaults route through [OpenRouter](https://openrouter.ai) (one key, every major model); any [LiteLLM provider](https://docs.litellm.ai/docs/providers) string works instead (`openai/...`, `anthropic/...`, `ollama_chat/...`). The `notebooks/llm.py` helper (taught in notebook 28) reads `.env`, falls back to the defaults, and can prompt for the key via `llm.configure()`; framework notebooks 07–14 additionally need their own provider credentials as noted in each.

## Design principles

- **Evidence over folklore.** Framework notebooks link to official documentation or original papers and keep claims narrow.
- **Testable by default.** Every pattern has a deterministic reference implementation, so tests and CI never need credentials — and going live is configuration, not a rewrite.
- **Bounded autonomy.** Every loop has explicit step, retry, cost, and permission boundaries.
- **Objective feedback.** Prefer tests, schemas, policy rules, and authoritative retrieval over self-approval.
- **Small composable pieces.** Add a new framework adapter or pattern without rewriting the curriculum.

## Sources

Framework references are collected in [`docs/SOURCES.md`](docs/SOURCES.md). The pattern examples draw from the original [ReAct paper](https://arxiv.org/abs/2210.03629) and [Anthropic's Building Effective AI Agents](https://resources.anthropic.com/building-effective-ai-agents), with implementation links kept next to each notebook.

## Contributing

Add new material as a small notebook plus a deterministic test or fixture where practical. Keep secrets out of notebooks, avoid committing notebook outputs containing sensitive data, and record the source URL for framework-specific claims.

## License

MIT. See [`LICENSE`](LICENSE).
