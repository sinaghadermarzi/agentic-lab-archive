# Agentic Frameworks & Patterns Lab

An executable, framework-aware lab for learning how modern agentic systems are assembled.

> deterministic workflow spine + bounded agentic decisions + objective verification + human authority at consequential boundaries

## What is inside

- A progressive curriculum from a local tool loop to multi-agent orchestration.
- Runnable Python notebooks that default to deterministic, offline demonstrations.
- Optional framework cells for LangGraph, OpenAI Agents SDK, PydanticAI, Google ADK, Microsoft Agent Framework, CrewAI, AWS Strands Agents, and LlamaIndex Workflows.
- A framework comparison notebook with primary-source links and an extensible adapter map for TypeScript ecosystems such as Mastra and Vercel AI SDK.
- Tests for the local pattern implementations and notebook integrity.
- No API keys, private data, or generated credentials committed to the repository.

## Start here

1. Read docs/CURRICULUM.md.
2. Create an environment with python -m venv .venv and pip install -e '.[dev]'.
3. Run python -m unittest discover -s tests -v.
4. Launch Jupyter with jupyter lab and open notebooks in order.

The notebooks are usable without an LLM provider. Live framework cells are skipped unless the optional package and its environment variables are present.

## Notebook map

- 00–05: core patterns and operational boundaries.
- 06: framework comparison.
- 07–14: framework-specific examples.
- 15: end-to-end hybrid capstone.

Framework-specific references are collected in docs/SOURCES.md. See .env.example for credential names and .gitignore for secret exclusions.

## Design principles

- Evidence over folklore.
- Offline first.
- Bounded autonomy.
- Objective feedback.
- Small composable pieces.

MIT licensed.