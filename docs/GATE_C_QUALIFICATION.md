# Gate C Qualification

Offline qualification recorded: 2026-09-25 (Asia/Shanghai).

## Scope and result

The Phase 5 research graph has an offline qualification for complete, insufficient-evidence,
budget-exhausted, interrupted, and cancelled outcomes. This is **not yet the final Gate C pass**:
the complete path has not been rerun through a rebuilt Docker API, broker, worker, and PostgreSQL
stack. The offline complete path uses a qualified market fixture and mock model; no external
model, market-data, or news request is made.

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

## Remaining final qualification

Rebuild the affected API and worker images and exercise a complete mock-provider run through the
real broker and PostgreSQL stack. Verify the stored Synthesis citations, worker redelivery, and
terminal API response. Keep external providers disabled. Record the container evidence here before
marking Gate C passed or advancing the real Research API frontend integration and Phase 6.
