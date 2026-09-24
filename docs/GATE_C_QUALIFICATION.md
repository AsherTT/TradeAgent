# Gate C Qualification

Qualified: 2026-09-25 (Asia/Shanghai).

## Scope and result

Gate C passes for the Phase 5 research loop: complete, insufficient-evidence,
budget-exhausted, interrupted, and cancelled outcomes are covered offline, and the complete path
has passed through a rebuilt Docker API, Redis broker, Celery worker, and PostgreSQL. The
container qualification uses a mock model and fixed-cutoff market fixture. It does not qualify
live model, market-data, or news providers.

## Offline evidence

| Outcome or bound | Qualification evidence |
| --- | --- |
| Complete | `test_offline_graph_persists_each_transition_and_completes` and the qualified-market case of `test_http_to_registered_celery_task_to_get_terminal_state` retain Synthesis citations through API submission, registered Celery task, SQLite persistence, and API retrieval. |
| Insufficient evidence | The no-market case of the same API/task test and `test_graph_without_qualified_evidence_finishes_insufficient` stop without Synthesis. |
| Replan, iteration, tool, and model budgets | `test_gate_c_replan_loop_respects_each_budget` forces News to remain absent and checks four independent ceilings, terminal status, and inspectable missing News. |
| Time and context safety | `test_news_retry_stops_if_replan_exhausts_wall_time`, existing workflow budget tests, and Synthesis evidence selection tests cover wall time, bounded context, and citation requirements. |
| Interrupted or unknown external outcome | Intent, evidence, News, Replan, and Synthesis interruption tests verify durable pre-call markers and no repeated external attempt on redelivery. |
| Cancellation and idempotency | Persistence tests verify cancellation before execution, late-result rejection, and terminal redelivery as a no-op. |

The ordinary suite reports 188 passed and one opt-in live-model test skipped, with 94.35%
combined statement/branch coverage. Ruff and strict mypy pass.

## Docker evidence

API, worker, and Beat images were rebuilt from the Phase 5 code. PostgreSQL migration completed,
and the API and Redis were healthy. A qualification-only Celery worker mounted
`backend/tests/gate_c_container_worker.py`; it substituted the model and market-data boundaries
before accepting tasks. The normal API process accepted the submission and dispatched the
registered `research.run` task through Redis. The independent
`backend/tests/gate_c_container_qualify.py` script checked the HTTP terminal response against
PostgreSQL and redelivered the task.

- Research run: `148af5f8-8d69-4fdd-9e1d-c8c16a1519f3`.
- Result: `complete`; transitions included Intent, Plan, market Evidence, Gap Judge, Synthesis,
  and Finish.
- Synthesis cited evidence `6515d6a6-253a-463e-a8a0-013330f47313`; the same citation was
  stored in PostgreSQL.
- Redelivery returned the unchanged complete state and transition history.
- No external model, market-data, or news call occurred. The mock executor uses the
  `codex_subscription` provider identifier only to exercise the normal routing policy.

This qualifies Gate C loop safety and durable research completion with controlled fixtures.
Recorded live provider qualification and News event extraction remain separate Phase 5 work.
