"""Provider-neutral instrument identity at one point in time."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class ProviderInstrument:
    symbol: str
    currency: str
    valid_from: datetime
    valid_to: datetime | None = None


class InstrumentMetadataResolver(Protocol):
    """Resolve permanent identity to provider metadata at a point in time."""

    async def resolve_instrument(
        self, instrument_id: UUID, *, at: datetime
    ) -> ProviderInstrument: ...
