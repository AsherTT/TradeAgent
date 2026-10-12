"""Public directory acquisition at the external HTTP boundary."""

import httpx
import pytest

from backend.app.company_directory import (
    MAX_BYTES,
    MAX_STALE_SECONDS,
    RETRY_SECONDS,
    TTL_SECONDS,
    DirectoryUnavailable,
    SecCompanyDirectory,
)


@pytest.mark.asyncio
async def test_directory_retains_multiple_codes_per_issuer_and_reuses_snapshot() -> None:
    payload = {"fields": ["cik", "name", "ticker", "exchange"], "data": [
        [1067983, "Berkshire Hathaway Inc", "BRK-A", "NYSE"],
        [1067983, "Berkshire Hathaway Inc", "BRK-B", "NYSE"],
        [320193, "Apple Inc.", "AAPL", "Nasdaq"],
    ]}
    requests: list[httpx.Request] = []

    def source(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=payload)

    directory = SecCompanyDirectory(
        "Test contact@example.test", transport=httpx.MockTransport(source),
    )
    first = await directory.snapshot()
    second = await directory.snapshot()
    assert [(row.cik, row.symbol, row.exchange) for row in first.items] == [
        ("0001067983", "BRK-A", "NYSE"), ("0001067983", "BRK-B", "NYSE"),
        ("0000320193", "AAPL", "NASDAQ"),
    ]
    assert second.fetched_at == first.fetched_at and second.stale is False
    assert len(requests) == 1 and requests[0].url.path == "/files/company_tickers_exchange.json"


@pytest.mark.asyncio
async def test_failed_refresh_uses_bounded_stale_cache_and_backoff_then_recovers() -> None:
    now = [0.0]
    healthy = [True]
    requests: list[httpx.Request] = []

    def source(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={
            "fields": ["cik", "name", "ticker", "exchange"],
            "data": [[320193, "Apple Inc.", "AAPL", "Nasdaq"]],
        }) if healthy[0] else httpx.Response(403, text="private upstream detail")

    directory = SecCompanyDirectory(
        "Test contact@example.test", transport=httpx.MockTransport(source), clock=lambda: now[0],
    )
    first = await directory.snapshot()
    healthy[0] = False
    now[0] = TTL_SECONDS + 1.0
    stale = await directory.snapshot()
    assert stale.stale is True and stale.fetched_at == first.fetched_at
    assert (await directory.snapshot()).stale is True and len(requests) == 2
    now[0] = MAX_STALE_SECONDS + 1.0
    with pytest.raises(DirectoryUnavailable, match=r"^directory_unavailable$"):
        await directory.snapshot()
    healthy[0] = True
    now[0] += RETRY_SECONDS + 1
    assert (await directory.snapshot()).stale is False


@pytest.mark.asyncio
@pytest.mark.parametrize("response", [
    httpx.Response(200, json={"fields": ["ticker"], "data": [["AAPL"]]}),
    httpx.Response(200, json={"fields": ["cik", "name", "ticker", "exchange"],
                             "data": [[True, "Wrong CIK", "TEST", "NASDAQ"]]}),
    httpx.Response(302, headers={"Location": "https://untrusted.example"}),
    httpx.Response(200, content=b"x" * (MAX_BYTES + 1)),
])
async def test_unsafe_or_invalid_source_never_becomes_empty_success(
    response: httpx.Response,
) -> None:
    directory = SecCompanyDirectory("Test contact@example.test", transport=httpx.MockTransport(
        lambda _: response,
    ))
    with pytest.raises(DirectoryUnavailable, match=r"^directory_unavailable$"):
        await directory.snapshot()


@pytest.mark.asyncio
async def test_missing_contact_is_explicit_and_does_not_contact_source() -> None:
    def forbidden(_: httpx.Request) -> httpx.Response:
        pytest.fail("unconfigured directory should not request SEC")
    directory = SecCompanyDirectory(None, transport=httpx.MockTransport(forbidden))
    with pytest.raises(DirectoryUnavailable, match=r"^directory_not_configured$"):
        await directory.snapshot()
