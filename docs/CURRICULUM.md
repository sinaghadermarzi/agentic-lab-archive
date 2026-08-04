# Curriculum

The lab is organized by transferable control-flow ideas, then maps each idea to framework APIs. Each notebook is designed to be read, changed, and re-run.

## Track A — Core patterns

| Lesson | Question | Pattern |
| --- | --- | --- |
| 00 | How do I run safely? | environment, secrets, permissions, budgets |
| 01 | How does an agent use the world? | tool-use loop / ReAct |
| 02 | What should code own? | deterministic workflow with agentic nodes, routing, prompt chaining, fan-out/fan-in |
| 03 | How does a system earn trust? | evaluator–optimizer, independent verifier, red-team panel |
| 04 | How do components collaborate? | agent-as-tool, supervisor–worker, handoff |
| 05 | How does a long run survive? | checkpoints, blackboard state, human authority gates, explicit termination |

## Track B — Frameworks

Each framework notebook has three layers:

1. **Concept mapping:** the framework's primitives and where they fit in the core model.
2. **Minimal live example:** official API shape, guarded by an import and credential check.
3. **Design translation:** what the same example would look like in the framework-neutral core.

| Lesson | Framework | Primary fit |
| --- | --- | --- |
| 06 | Comparison | choose by control-flow needs, provider, language, and operations |
| 07 | LangGraph | durable, stateful graph orchestration |
| 08 | OpenAI Agents SDK | small agent/tool/handoff/guardrail primitives |
| 09 | PydanticAI | typed Python services and structured outputs |
| 10 | Google ADK | Gemini/Google Cloud and multi-language workflow orchestration |
| 11 | Microsoft Agent Framework | Python/.NET enterprise workflows and orchestration |
| 12 | CrewAI | role-based crews plus event-driven flows |
| 13 | AWS Strands Agents | model-driven AWS/Bedrock-centered agents |
| 14 | LlamaIndex Workflows | document, retrieval, and knowledge-intensive workflows |
| 21 | smolagents | minimal code-as-action agents with sandboxed execution |
| 22 | Agno | agents, teams, and the AgentOS operational runtime |

AutoGen and Semantic Kernel are covered as lineage inside lesson 11: both are in maintenance
mode and officially succeeded by Microsoft Agent Framework, so they get a concept mapping and
migration links rather than their own lessons. Mastra, Vercel AI SDK, and the Claude Agent
SDK are included in the comparison notebook as TypeScript/agent-harness extensions; this
repository remains Python-first by design.

## Track C — Capstone

`15_capstone_research_review.ipynb` combines intake validation, routing, parallel research, evidence-backed synthesis, objective review, repair, checkpointing, and an approval gate. It is intentionally deterministic so that students can inspect every transition.

## Track D — Interoperability protocols

Protocols, not frameworks: they standardize the boundaries that every notebook in Track B
wires up its own way — MCP for the tool boundary, A2A for the agent-to-agent boundary.
Concept lessons need only the core install and can be read any time after lesson 01 (16) or
lesson 04 (18). The SDK lessons follow the Track B three-layer structure but their live
examples run locally (stdio / localhost), so they need an extra and no API key.

| Lesson | Focus | Requirement |
| --- | --- | --- |
| 16 | MCP roles, tools/resources/prompts, JSON-RPC lifecycle, trust boundary | none (offline toy) |
| 17 | FastMCP server, stdio client session, framework reuse | `pip install -e '.[mcp]'` |
| 18 | A2A Agent Cards, task lifecycle, artifacts, cross-wire delegation | none (offline toy) |
| 19 | A2A AgentExecutor server, `create_client`, localhost JSON-RPC | `pip install -e '.[a2a]'` |
| 20 | landscape survey: AG-UI, AP2, AGNTCY, ANP, ACP history | none (offline) |

## Suggested pace

- **One afternoon:** 00–05.
- **One day:** 06–09.
- **One day:** 10–14 and 21–22, choosing only the frameworks relevant to your stack.
- **One day:** 16–20 for protocols — MCP any time after 01, A2A after 04.
- **One project:** adapt the capstone to a real domain with synthetic data first.

## Extension rule

When adding a pattern, include its failure mode, a bounded implementation, and an objective test. When adding a framework, include its official source link, install extra, minimum example, and what the framework does not solve for you.
