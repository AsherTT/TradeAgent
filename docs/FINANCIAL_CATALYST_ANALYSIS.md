# Derived financial metrics and source-reported catalyst interpretations

This increment adds useful source-bound analysis without qualifying a complete report.

- Derive annual net margin (NetIncomeLoss / Revenue) and cash/assets share from
  the shared admitted, fresh, consistent four-concept SEC group. Use Decimal with
  explicit precision 28; no percent rounding in the typed result. Keep two exact
  source UUIDs, formula, period and filing dates. Nonpositive denominator suppresses
  that metric; negative net income is valid. Negative cash suppresses cash/assets.
  No growth, valuation, liquidity sufficiency or investment judgment is inferred.
- Recompute metrics in the read-only report from qualified persisted evidence.
  They add no model/tool calls and never satisfy market or quant capability.
- Add a default-off `CATALYSTS_ENABLED` graph node after RAG and before Gap Judge.
  It may run even when market is unqualified; it extracts at most five optional
  source-reported interpretations from five recent qualified news/public or official
  RAG sources. USER_CONTENT and unknown sources are excluded. Each interpretation
  uses the existing catalyst SynthesisClaim type with an exact bounded quote and UUID.
  No verified dates, price impact, corporate actions or corroboration are inferred.
- Keep the normal commit-before-call marker, bounded model budget and completed
  output/model-history checkpoint. Interrupted calls remain unknown outcome and
  must not repeat; a completed assessment must not reacquire. No sources or disabled
  mode cause no model call. Zero remaining budget causes no extra model call.
  If deterministic coverage is sufficient, reserve the last model call for the
  primary synthesis instead of spending it on optional extraction. Current scanner
  version, zero injection risk and exact content hash are required for source selection.
- Report revalidates catalyst quotes and source eligibility at the frozen cutoff;
  any invalid interpretation suppresses the assessment and adds a gap. Valid ones
  have individual citations but remain explicitly model interpretations, not verified
  catalyst analysis. Existing verified-analysis gaps and complete_analysis=false remain.
  An empty valid assessment preserves model-reported limitations without fabricating events.
- Legacy states without the optional assessment remain readable. Existing mock/default
  workflows stay unchanged. True mode uses at most one additional gateway node; retries
  remain subject to the existing gateway request accounting and unknown-outcome policies.

Offline cases cover ratio arithmetic, period/source conflicts, zero/negative denominators,
freshness, catalyst quote/type/cutoff rejection, opt-in gating, budgets, checkpoints and
redelivery. Real partial-analysis qualification is separate from full synthesis qualification.
