# yfinance Qualification

## Windows system proxy diagnosis (2026-09-29)

A live KLAC history call initially timed out in `curl_cffi` while the same Yahoo chart endpoint
was reachable through the Windows system HTTPS proxy. `curl_cffi` did not automatically inherit
that proxy. The library adapter now supplies a request-scoped `curl_cffi` session with the system
HTTPS proxy (also honoring standard proxy environment variables through Python's proxy lookup).
On this workstation, a subsequent real KLAC 60-day current acquisition returned 41 bars ending
2026-09-28; two successive history calls also succeeded. This verifies connectivity and parsing
here, not the unverified Yahoo corporate-action provenance or complete synthesis quality.

The yfinance adapter is an offline-qualified, whole-request fallback for the user's personal
research workflow. It is not affiliated with Yahoo, and the library license does not grant rights
to redistribute downloaded Yahoo market data.

## Enforced behavior

- Daily OHLCV is requested with `auto_adjust=False`, `back_adjust=False`, and `repair=False`.
- A permanent instrument resolves to one symbol epoch covering the complete requested window.
- Bars retain source, observation/availability timestamps, and provider quality version.
- Empty, malformed, stale, partial, or timezone-naive history fails closed.
- Dividends and splits use observation time as their availability time and remain `UNVERIFIED`.
- Fixed-cutoff bars and actions share one request-scoped history response; the current-research
  adapter also derives its complete result from one acquired snapshot.
- Current acquisition records its decision cutoff only after the response is obtained, validates
  the full daily lookback coverage, and propagates the worst bar/action quality to normalized bars.
- Excluding yfinance from configured providers disables the current route rather than bypassing
  configuration.
- Known rate-limit and transport exceptions are typed operational failures. Unknown library,
  parser, and integrity failures remain terminal and cannot trigger provider fallback.
- Ordinary tests use saved synthetic fixtures and never call Yahoo endpoints.

## Eligibility

The route is allowed for qualified non-strict research. It is not eligible for strict
point-in-time backtests until independent golden cases, historical action publication times, and
a versioned quality report support that claim. The provider quality report remains fixture-only;
the live KLAC connectivity check above does not promote that report's quality status.
