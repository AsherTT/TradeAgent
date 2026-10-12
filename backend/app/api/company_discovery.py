"""Authenticated directory discovery without admitting securities into research."""

from functools import lru_cache
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.accounts import AuthenticatedUser, BrowserSession
from backend.app.company_directory import (
    SEC_DIRECTORY_URL,
    DirectoryIdentity,
    DirectorySnapshot,
    DirectoryUnavailable,
    SecCompanyDirectory,
)
from backend.app.config import get_settings
from backend.app.financials.limiter import RedisSecRequestLimiter
from backend.app.persistence.models import InstrumentRow


class DiscoveredCompany(BaseModel):
    cik: str
    symbol: str
    name: str
    exchange: str | None
    instrument_id: UUID | None


class DirectoryMetadata(BaseModel):
    source: Literal["sec_company_tickers_exchange"] = "sec_company_tickers_exchange"
    source_url: str = SEC_DIRECTORY_URL
    fetched_at: str
    stale: bool
    directory_total: int


class DiscoveryPage(DirectoryMetadata):
    items: list[DiscoveredCompany]
    total: int
    limit: int
    offset: int


class DiscoveryDetail(DirectoryMetadata):
    company: DiscoveredCompany


@lru_cache
def get_company_directory() -> SecCompanyDirectory:
    settings = get_settings()
    return SecCompanyDirectory(
        settings.sec_user_agent, admission=RedisSecRequestLimiter(settings.redis_broker_url),
    )


async def snapshot(directory: SecCompanyDirectory) -> DirectorySnapshot:
    try:
        return await directory.snapshot()
    except DirectoryUnavailable as error:
        raise HTTPException(503, detail=str(error)) from None


def metadata(value: DirectorySnapshot) -> DirectoryMetadata:
    return DirectoryMetadata(
        fetched_at=value.fetched_at.isoformat(), stale=value.stale,
        directory_total=len(value.items),
    )


async def resolve_local(
    items: list[DirectoryIdentity], session: AsyncSession,
) -> list[DiscoveredCompany]:
    pairs = {(item.symbol, item.exchange) for item in items if item.exchange}
    records = list(await session.scalars(select(InstrumentRow).where(
        InstrumentRow.delisted_at.is_(None), InstrumentRow.status == "active",
        or_(*(and_(func.upper(InstrumentRow.current_symbol) == symbol,
                   func.upper(InstrumentRow.exchange) == exchange) for symbol, exchange in pairs)),
    ))) if pairs else []
    matches: dict[tuple[str, str], list[UUID]] = {}
    for record in records:
        matches.setdefault((record.current_symbol.upper(), record.exchange.upper()), []).append(
            record.instrument_id,
        )
    result = []
    for item in items:
        ids = matches.get((item.symbol, item.exchange or ""), [])
        result.append(DiscoveredCompany(
            cik=item.cik, symbol=item.symbol, name=item.name, exchange=item.exchange,
            instrument_id=ids[0] if len(ids) == 1 else None,
        ))
    return result


router = APIRouter(prefix="/workspace/company-discovery", tags=["workspace"])
Directory = Annotated[SecCompanyDirectory, Depends(get_company_directory)]


@router.get("", response_model=DiscoveryPage)
async def search_companies(
    user: AuthenticatedUser, session: BrowserSession, directory: Directory,
    query: Annotated[str, Query(max_length=64)] = "",
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0, le=100_000)] = 0,
) -> DiscoveryPage:
    del user
    value = await snapshot(directory)
    term = query.strip().casefold()
    matches = [item for item in value.items if not term or term in item.symbol.casefold()
               or term in item.name.casefold()]
    matches.sort(key=lambda item: (
        0 if term and item.symbol.casefold() == term
        else 1 if term and item.symbol.casefold().startswith(term) else 2,
        item.symbol, item.exchange or "", item.cik,
    ))
    return DiscoveryPage(
        **metadata(value).model_dump(), total=len(matches), limit=limit, offset=offset,
        items=await resolve_local(matches[offset:offset + limit], session),
    )


@router.get("/{cik}", response_model=DiscoveryDetail)
async def discovered_company(
    cik: Annotated[str, Path(pattern=r"^[0-9]{1,10}$")],
    user: AuthenticatedUser, session: BrowserSession, directory: Directory,
    symbol: Annotated[str, Query(min_length=1, max_length=32)],
    exchange: Annotated[str, Query(max_length=32)] = "",
) -> DiscoveryDetail:
    del user
    value = await snapshot(directory)
    matches = [item for item in value.items if item.cik == cik.zfill(10)
               and item.symbol == symbol.upper() and (item.exchange or "") == exchange.upper()]
    if len(matches) != 1:
        raise HTTPException(404, detail="directory_company_not_found")
    company = (await resolve_local(matches, session))[0]
    return DiscoveryDetail(**metadata(value).model_dump(), company=company)
