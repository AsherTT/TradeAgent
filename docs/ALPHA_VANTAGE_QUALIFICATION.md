# Alpha Vantage offline adapter qualification

Qualified artifact version: `alpha-vantage-daily-raw-v1`

Machine-readable reports:

- `docs/provider_quality/alpha_vantage_daily_raw_v1.json`
- `docs/provider_quality/alpha_vantage_actions_observed_v1.json`

This qualification covers the adapter contract and saved HTTP response shapes only. It does not
claim that a live Alpha Vantage account, entitlement, or historical dataset has been qualified.
No live provider request or API credential was used.

## Qualified scope

- `TIME_SERIES_DAILY` raw daily OHLCV parsing into strict `MarketBar` contracts
- permanent `instrument_id` preservation through an injected point-in-time instrument resolver
- exchange-time-zone daily close timestamps, conservative observation-time availability, and
  analysis-window filtering
- explicit `alpha_vantage` source and qualification-version provenance
- provider error, throttling, malformed payload, invalid OHLCV, and symbol-mismatch rejection
- provider-neutral integration through `MarketDataService.load_bars()`

The saved golden fixture represents the documented Alpha Vantage daily JSON schema. A later,
explicitly authorized live trial must record and compare an actual response before production use.

## Corporate-action limitation

Dividend and split endpoints do not document a historical publication timestamp precise enough for
the project's point-in-time contract. Their rows conservatively use the later of the documented
event date and response observation time as `available_at`. The constructor enforces an
`UNVERIFIED` corporate-action quality report, so this adapter is not eligible for strict
point-in-time backtests.

## Deferred

- credentials and live calls
- premium `outputsize=full` qualification
- production worker configuration
- live entitlement, quota, and coverage verification
- exchange-holiday-aware calendars; boundary checks currently understand weekends and otherwise
  fail closed when a missing weekday could be a holiday
- commercial-use and redistribution review
