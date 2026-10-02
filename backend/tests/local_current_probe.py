"""Opt-in owned local API/worker harness; never collected by ordinary pytest.

Run python -m backend.tests.local_current_probe --financials after starting the
local Compose PostgreSQL/Redis services. Existing API/worker instances must be stopped.
"""

import argparse
import asyncio
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx


async def main(*, financials: bool, rag_lexical: bool = False, catalysts: bool = False) -> None:
    env = os.environ.copy()
    env.update(
        DATABASE_URL="postgresql+asyncpg://tradeagent:tradeagent-local-only@127.0.0.1:5432/tradeagent",
        REDIS_BROKER_URL="redis://127.0.0.1:6379/0",
        REDIS_RESULT_URL="redis://127.0.0.1:6379/1",
        MARKET_DATA_ENABLED="true",
        NEWS_ENABLED="true",
        FINANCIALS_ENABLED=str(financials).lower(),
        RAG_ENABLED=str(rag_lexical).lower(),
        RAG_RETRIEVAL_MODE="lexical_only" if rag_lexical else "hybrid",
        KLAC_PROBE_RAG_LEXICAL=str(rag_lexical).lower(),
        CATALYSTS_ENABLED=str(catalysts).lower(),
        KLAC_PROBE_CATALYSTS=str(catalysts).lower(),
        KLAC_PROBE_API_URL="http://127.0.0.1:8002",
    )
    commands = (
        ["-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8002"],
        ["-m", "celery", "-A", "backend.app.jobs.celery_app:celery_app", "worker",
         "--pool=solo", "--loglevel=WARNING", "--without-gossip", "--without-mingle"],
    )
    processes: list[asyncio.subprocess.Process] = []
    logs = []
    try:
        async with httpx.AsyncClient(timeout=1, trust_env=False) as client:
            try:
                await client.get(env["KLAC_PROBE_API_URL"] + "/health")
            except httpx.RequestError:
                pass
            else:
                raise RuntimeError("Probe port is already in use; no process was started")
        for index, command in enumerate(commands):
            log_path = Path(tempfile.gettempdir()) / f"tradeagent-current-service-{index}.log"
            log = log_path.open("wb")
            logs.append(log)
            processes.append(await asyncio.create_subprocess_exec(
                sys.executable, *command, env=env, stdout=log, stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            ))
        async with httpx.AsyncClient(timeout=1, trust_env=False) as client:
            for _ in range(30):
                if any(process.returncode is not None for process in processes):
                    raise RuntimeError("An owned probe service exited during startup")
                try:
                    response = await client.get(env["KLAC_PROBE_API_URL"] + "/health")
                    response.raise_for_status()
                    break
                except httpx.HTTPError:
                    await asyncio.sleep(1)
            else:
                raise TimeoutError("Owned probe API did not become ready")
        probe = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "backend.tests.current_model_durable_probe", env=env,
        )
        try:
            async with asyncio.timeout(150):
                if await probe.wait() != 0:
                    raise RuntimeError("Current research probe failed")
        finally:
            if probe.returncode is None:
                probe.terminate()
                await probe.wait()
    finally:
        for process in processes:
            if process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5)
                except TimeoutError:
                    process.kill()
                    await asyncio.wait_for(process.wait(), timeout=5)
        for log in logs:
            log.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--financials", action="store_true")
    parser.add_argument("--rag-lexical", action="store_true")
    parser.add_argument("--catalysts", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(
        financials=args.financials, rag_lexical=args.rag_lexical, catalysts=args.catalysts,
    ))
