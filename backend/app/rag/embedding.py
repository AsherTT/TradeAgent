"""Provider-neutral embedding boundary; model choice is intentionally configured outside RAG."""

from __future__ import annotations

from math import isfinite
from typing import Protocol

import httpx

from backend.app.config import Settings

EMBEDDING_DIMENSIONS = 384


class EmbeddingProvider(Protocol):
    model_id: str

    async def embed(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]: ...


class RagEmbeddingError(RuntimeError):
    """The configured embedding service failed or returned an invalid vector batch."""


class HTTPEmbeddingProvider:
    """OpenAI-compatible embeddings with a fixed schema dimension."""

    def __init__(self, *, base_url: str, api_key: str, model_id: str) -> None:
        if not base_url or not api_key or not model_id:
            raise ValueError("embedding endpoint, credential, and model are required")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.model_id = model_id

    async def embed(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        if not texts:
            return ()
        if len(texts) > 64 or any(not text or len(text) > 1200 for text in texts):
            raise RagEmbeddingError("embedding batch exceeds RAG limits")
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self._base_url}/embeddings",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={
                        "model": self.model_id,
                        "input": list(texts),
                        "dimensions": EMBEDDING_DIMENSIONS,
                    },
                )
                response.raise_for_status()
                payload = response.json()
            items = payload["data"]
            if not isinstance(items, list) or len(items) != len(texts):
                raise RagEmbeddingError("embedding service returned an incomplete batch")
            indexed: dict[int, tuple[float, ...]] = {}
            for item in items:
                index = item["index"]
                vector = tuple(float(value) for value in item["embedding"])
                if (
                    not isinstance(index, int)
                    or index < 0
                    or index >= len(texts)
                    or index in indexed
                    or len(vector) != EMBEDDING_DIMENSIONS
                    or any(not isfinite(value) for value in vector)
                    or not any(value != 0 for value in vector)
                ):
                    raise RagEmbeddingError("embedding service returned invalid vectors")
                indexed[index] = vector
            return tuple(indexed[index] for index in range(len(texts)))
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise RagEmbeddingError("embedding service request or response failed") from exc


def build_rag_embedding_provider(settings: Settings) -> EmbeddingProvider | None:
    if settings.rag_retrieval_mode == "lexical_only":
        return None
    if not all(
        (
            settings.rag_embedding_base_url,
            settings.rag_embedding_api_key,
            settings.rag_embedding_model,
        )
    ):
        return None
    assert settings.rag_embedding_base_url is not None
    assert settings.rag_embedding_api_key is not None
    assert settings.rag_embedding_model is not None
    return HTTPEmbeddingProvider(
        base_url=settings.rag_embedding_base_url,
        api_key=settings.rag_embedding_api_key,
        model_id=settings.rag_embedding_model,
    )
