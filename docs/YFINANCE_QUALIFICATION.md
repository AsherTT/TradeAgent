# yfinance Qualification

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
a versioned quality report support that claim. Qualification remains fixture-only: no live Yahoo
request was made.
