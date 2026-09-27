"""Provider-neutral embedding boundary; model choice is intentionally configured outside RAG."""

from __future__ import annotations

from typing import Protocol

EMBEDDING_DIMENSIONS = 384


class EmbeddingProvider(Protocol):
    model_id: str

    async def embed(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]: ...
