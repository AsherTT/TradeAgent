# Equity Research Workbench

This context defines the market-history language used to prevent identity ambiguity and future-data leakage.

## Language

**Instrument**:
A permanently identified traded security whose ticker may change over time.
_Avoid_: Ticker, symbol

**Symbol History**:
A half-open record of the symbol and exchange that identified an Instrument during a period.

**Corporate Action**:
An issuer or exchange event with separate effective and information-availability timestamps.

**Analysis Timestamp**:
The information cutoff for a research or backtest decision; later-available records are unknowable.
_Avoid_: Current time, as-of date

**Price Adjustment Mode**:
An explicit declaration of whether bars are raw, split-adjusted, total-return-adjusted, or reconstructed using only point-in-time-visible actions.
_Avoid_: Adjusted close

**Provider Qualification**:
A versioned golden-case assessment that determines whether a data provider is eligible for strict backtesting.
