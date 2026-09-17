"""FastAPI entry point for the workbench."""

from fastapi import FastAPI

from backend.app.api.research import router as research_router

app = FastAPI(
    title="Agentic Equity Research Workbench",
    version="0.1.0",
    description="Phase 0-3 foundation, model runtime, persistence, and job queue",
)
app.include_router(research_router)


@app.get("/health", tags=["operations"])
async def health() -> dict[str, str]:
    return {"status": "ok", "milestone": "phase-0-3"}
