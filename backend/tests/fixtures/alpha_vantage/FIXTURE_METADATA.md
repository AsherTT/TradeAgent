# Alpha Vantage fixture provenance

These payloads are saved offline golden cases derived from the response fields documented at
<https://www.alphavantage.co/documentation/>. They were not captured by making a live request and
contain no credential, account, or quota information.

- `daily_raw_success.json`: `TIME_SERIES_DAILY` JSON shape, compact raw daily bars
- `dividends_success.json`: `DIVIDENDS` JSON shape with date-only declaration metadata
- `splits_success.json`: `SPLITS` JSON shape without a historical publication timestamp

Before production use, an explicitly authorized live trial must capture actual response bytes,
observation timestamps, HTTP metadata, entitlement, and symbol coverage for comparison with these
golden cases.
