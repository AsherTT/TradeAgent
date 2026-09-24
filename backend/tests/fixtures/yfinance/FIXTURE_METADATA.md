# yfinance offline fixtures

These synthetic fixtures model the public shapes returned by yfinance without redistributing
Yahoo market data or making a network request. Values are used only to qualify parsing,
point-in-time filtering, conservative window checks, error classification, and symbol-epoch
handling.

- `daily_raw_success.json`: timezone-aware daily OHLCV plus observed action columns.
- `empty.json`, `stale.json`, `partial.json`, `malformed.json`: fail-closed cases.
- `renamed_symbol_epoch.json`: a request crossing an unresolved symbol epoch.
- `throttled.json`, `upstream_error.json`: typed operational failures.

The yfinance Apache license covers the library, not redistribution rights for downloaded Yahoo
market data. This route is restricted to the user's personal research workflow.
