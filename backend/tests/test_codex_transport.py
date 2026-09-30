"""The actual SDK shape: child-only proxy options and Enum completion status."""

import os
import sys
from enum import Enum
from types import SimpleNamespace
from typing import Any

import pytest

from backend.app.ai.errors import ProviderUnavailableError
from backend.app.ai.executors.codex_subscription import CodexSubscriptionExecutor
from backend.app.config import Settings


class Status(Enum):
    completed = "completed"
    interrupted = "interrupted"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [Status.completed, Status.interrupted])
async def test_child_proxy_and_completion_status(
    monkeypatch: pytest.MonkeyPatch, status: Status
) -> None:
    observed: dict[str, Any] = {}
    original_env = dict(os.environ)

    class Config:
        def __init__(self, *, env: dict[str, str]) -> None:
            observed["env"] = env

    class Thread:
        async def run(self, prompt: str) -> Any:
            return SimpleNamespace(status=status, final_response="OK")

    class Codex:
        def __init__(self, *, config: Config) -> None:
            observed["config"] = config

        async def __aenter__(self) -> "Codex":
            return self

        async def __aexit__(self, *args: object) -> None:
            observed["closed"] = True

        async def thread_start(self, **kwargs: Any) -> Thread:
            assert kwargs["sandbox"] == "read_only"
            return Thread()

    monkeypatch.setitem(
        sys.modules,
        "openai_codex",
        SimpleNamespace(
            AsyncCodex=Codex, CodexConfig=Config, Sandbox=SimpleNamespace(read_only="read_only")
        ),
    )
    if status is Status.completed:
        assert (
            await CodexSubscriptionExecutor._run_with_sdk(
                "prompt", None, 1, "low", proxy_url="http://127.0.0.1:9999"
            )
            == "OK"
        )
    else:
        with pytest.raises(ProviderUnavailableError):
            await CodexSubscriptionExecutor._run_with_sdk(
                "prompt", None, 1, "low", proxy_url="http://127.0.0.1:9999"
            )
    assert observed["env"]["HTTPS_PROXY"] == "http://127.0.0.1:9999"
    assert observed["env"]["HTTP_PROXY"] == "http://127.0.0.1:9999"
    assert dict(os.environ) == original_env
    assert observed["closed"]


@pytest.mark.parametrize(
    "url",
    [
        "socks5://localhost:99",
        "http://user:secret@localhost:99",
        "https://localhost",
        "http://localhost:99/?token=private",
    ],
)
def test_proxy_configuration_rejects_unsupported_or_credential_urls(url: str) -> None:
    with pytest.raises(ValueError, match="without credentials"):
        Settings(_env_file=None, codex_proxy_url=url)
