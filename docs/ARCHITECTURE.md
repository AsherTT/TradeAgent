# Architecture Baseline

The source-of-truth architecture is **Agentic Equity Research Workbench v1.1.1 — Quant Integrity + Operational Reliability Hardened** dated 2026-09-16.

This repository currently implements only its first milestone (Phases 0-2). Later packages remain intentionally absent or skeletal until their architecture gate is reached.

## Current boundaries

- FastAPI application skeleton
- strict Pydantic data contracts
- deterministic budget guard
- provider-neutral model gateway
- Codex subscription, Qwen, DeepSeek, OpenAI API, and mock executor boundaries
- bounded retry/fallback and execution metadata
- unit and adapter tests

No current component produces investment advice, strategy signals, broker orders, or claims of historical alpha.
