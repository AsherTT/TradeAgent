"""Provider-neutral, point-in-time-safe market-data boundary."""

from backend.app.market_data.alpha_vantage import (
    AlphaVantageCorporateActionProvider,
    AlphaVantageMarketDataProvider,
    AlphaVantageOperationalError,
    AlphaVantageProviderError,
)
from backend.app.market_data.cache import (
    CachedMarketDataLoader,
    InMemoryQualifiedMarketDataCache,
    ProviderQualificationVersions,
)
from backend.app.market_data.errors import (
    MarketDataIntegrityError,
    MarketDataOperationalError,
    OperationalFailureReason,
)
from backend.app.market_data.instrument import InstrumentMetadataResolver, ProviderInstrument
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
from backend.app.market_data.service import (
    AllMarketDataProvidersUnavailable,
    CurrentMarketDataLoader,
    CurrentMarketDataRequest,
    CurrentMarketDataResult,
    FallbackMarketDataService,
    MarketDataAttemptSource,
    MarketDataCandidate,
    MarketDataFallbackPolicy,
    MarketDataLoader,
    MarketDataRequest,
    MarketDataService,
    ProviderAttempt,
    ProviderAttemptOutcome,
)
from backend.app.market_data.yfinance import (
    YFinanceCorporateActionProvider,
    YFinanceLibraryClient,
    YFinanceMarketDataProvider,
    YFinanceProviderError,
)

__all__ = [
    "AllMarketDataProvidersUnavailable",
    "AlphaVantageCorporateActionProvider",
    "AlphaVantageMarketDataProvider",
    "AlphaVantageOperationalError",
    "AlphaVantageProviderError",
    "CachedMarketDataLoader",
    "CorporateActionProvider",
    "CurrentMarketDataLoader",
    "CurrentMarketDataRequest",
    "CurrentMarketDataResult",
    "FallbackMarketDataService",
    "InMemoryQualifiedMarketDataCache",
    "InstrumentMetadataResolver",
    "MarketDataAttemptSource",
    "MarketDataCandidate",
    "MarketDataFallbackPolicy",
    "MarketDataIntegrityError",
    "MarketDataLoader",
    "MarketDataOperationalError",
    "MarketDataProvider",
    "MarketDataRequest",
    "MarketDataService",
    "OperationalFailureReason",
    "PriceNormalizationError",
    "ProviderAttempt",
    "ProviderAttemptOutcome",
    "ProviderInstrument",
    "ProviderQualificationVersions",
    "ProviderQualityError",
    "YFinanceCorporateActionProvider",
    "YFinanceLibraryClient",
    "YFinanceMarketDataProvider",
    "YFinanceProviderError",
    "normalize_prices",
    "require_report_matches_actions",
    "require_report_matches_bars",
    "require_strict_backtest_eligible",
    "require_strict_bars_eligible",
    "worse_quality",
]
