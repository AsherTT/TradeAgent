# Finnhub company news integration

The open-source [TradeAgent aggregator](https://github.com/enving/TradeAgent/blob/main/src/news/aggregator.py)
queries Yahoo Finance news without a key, and Finnhub company news and NewsAPI when their keys
are configured. Yahoo was the source of the earlier KLAC market-price timeout; that attempt never
reached news. Finnhub's [company-news endpoint](https://finnhub.io/docs/api/company-news) lists
recent updates in the free tier for North American companies, including KLAC. A free account and
API key are still required. [NewsAPI's free Developer plan](https://newsapi.org/pricing) delays
articles by 24 hours and is restricted to development/testing, so it is unsuitable for current
production research.

Set `MARKET_DATA_ENABLED=true`, `NEWS_ENABLED=true`, and `FINNHUB_API_KEY=<free key>` in the
worker environment. Keep the key out of source control. Submit a `current_research` run. The
worker requests seven days of ticker-specific company news, capped at the research document
budget; article headline and summary are scanned and cited, while full text is not available from
this response. The feed does not accept a free-form search objective, so its current snapshot is
not retried through the graph's News Replan node. The request uses a 15-second timeout and sends
the key in a header. Provider HTTP or network failure leaves an explicit evidence gap.

The current run fetches news before freezing the market cutoff so the true observation time can
be represented without lookahead. Fixed-cutoff historical research never acquires fresh news as
historical evidence. This adapter and the cutoff sequence are tested with offline HTTP fixtures.
A narrow live KLAC request with a locally configured free key succeeded on 2026-09-30; the combined
current-news and Yahoo acquisition admitted 19 scanned news records but stopped at the market
quality gate. See `docs/KLAC_CURRENT_QUALIFICATION.md`. News relevance and complete model synthesis
are still unqualified.
