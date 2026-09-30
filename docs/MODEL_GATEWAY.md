# Model Gateway PoC

`ModelGateway` is the only application entry point for model execution.

## Request flow

1. Accept a provider-neutral `ModelRequest` and Pydantic output schema.
2. Select an ordered provider route through `TaskPolicy`.
3. Reject executors that do not meet required capabilities.
4. Retry each eligible provider a bounded number of times. An explicit request timeout skips
   another attempt at the same provider and proceeds to the next configured provider.
5. Fall back to the next configured provider.
6. Validate the result with Pydantic; invalid JSON or schema mismatch is a failed execution.
7. Record every attempted, failed, skipped, and successful provider decision in tracing.
8. Aggregate successful token and cost metadata through `UsageMeter`.
9. Return typed output and immutable `ExecutorMetadata`.

## Provider boundaries

- Codex subscription uses the official `openai-codex` Python SDK and local app-server. It is personal/experimental runtime only.
- Qwen and DeepSeek use separate OpenAI-compatible HTTP adapters.
- OpenAI API is an optional cloud/fallback executor and is not enabled without an explicit model.
- `MockExecutor` is the default test seam. Ordinary tests never call a live model.

Local Codex network configuration can explicitly set `CODEX_PROXY_URL` for the SDK child.
The option defaults empty, does not alter global proxy variables, and rejects embedded
credentials. Only completed SDK turns with text are admitted. Local transport and real
intent/plan qualification are recorded in `docs/CODEX_TRANSPORT_QUALIFICATION.md`; this
does not qualify full synthesis, API-provider access or cloud deployment.

Live provider qualification is opt-in: set `RUN_LIVE_MODEL=1` and run the
`live_model` test explicitly. Ordinary tests never consume model-provider quota.
