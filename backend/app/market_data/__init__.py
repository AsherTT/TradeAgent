"""Provider-neutral, point-in-time-safe market-data boundary."""

from backend.app.market_data.alpha_vantage import (
    AlphaVantageCorporateActionProvider,
    AlphaVantageMarketDataProvider,
    AlphaVantageProviderError,
    InstrumentMetadataResolver,
    ProviderInstrument,
)
from backend.app.market_data.normalization import PriceNormalizationError, normalize_prices
from backend.app.market_data.providers import CorporateActionProvider, MarketDataProvider
from backend.app.market_data.quality import (
    ProviderQualityError,
    require_report_matches_actions,
    require_report_matches_bars,
    require_strict_backtest_eligible,
    require_strict_bars_eligible,
    worse_quality,
)
from backend.app.market_data.service import MarketDataRequest, MarketDataService

__all__ = [
    "AlphaVantageCorporateActionProvider",
    "AlphaVantageMarketDataProvider",
    "AlphaVantageProviderError",
    "CorporateActionProvider",
    "InstrumentMetadataResolver",
    "MarketDataProvider",
    "MarketDataRequest",
    "MarketDataService",
    "PriceNormalizationError",
    "ProviderInstrument",
    "ProviderQualityError",
    "normalize_prices",
    "require_report_matches_actions",
    "require_report_matches_bars",
    "require_strict_backtest_eligible",
    "require_strict_bars_eligible",
    "worse_quality",
]
