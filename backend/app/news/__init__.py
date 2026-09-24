"""Provider-neutral news research boundary."""

from backend.app.news.research import (
    NewsDocument,
    NewsLoader,
    NewsResearchEvidence,
    NewsSearchRequest,
)

__all__ = ["NewsDocument", "NewsLoader", "NewsResearchEvidence", "NewsSearchRequest"]
