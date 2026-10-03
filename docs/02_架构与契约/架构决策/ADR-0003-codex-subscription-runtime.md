# ADR-0003: Codex subscription runtime

Status: experimental for cloud; accepted for personal PoC

The Codex executor uses the official local app-server SDK behind a narrow adapter. It starts inference threads with the structural `read_only` sandbox rather than relying on prompt instructions to prevent file changes. Authentication, threads, and SDK types do not cross into business code. Cloud credential persistence, refresh, concurrency, quota, timeout, restart behavior, and session isolation remain unqualified; API executors are required fallbacks.
