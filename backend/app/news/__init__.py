"""Provider-neutral news research boundary."""

from backend.app.news.finnhub import FinnhubNewsLoader
from backend.app.news.research import (
    NewsDocument,
    NewsLoader,
    NewsResearchEvidence,
    NewsSearchRequest,
)

__all__ = [
    "FinnhubNewsLoader",
    "NewsDocument",
    "NewsLoader",
    "NewsResearchEvidence",
    "NewsSearchRequest",
]
