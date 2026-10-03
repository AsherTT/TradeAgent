"""LangGraph research orchestration."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from backend.app.graph.workflow import (
        EvidenceCollection,
        MarketResearchEvidence,
        ResearchEvidence,
        ResearchWorkflow,
        failed_research_state,
    )

__all__ = [
    "EvidenceCollection",
    "MarketResearchEvidence",
    "ResearchEvidence",
    "ResearchWorkflow",
    "failed_research_state",
]


def __getattr__(name: str) -> Any:
    """Keep existing exports without loading orchestration for a leaf-module import."""
    if name not in __all__:
        raise AttributeError(name)
    from backend.app.graph import workflow

    return getattr(workflow, name)
