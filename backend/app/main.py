"""FastAPI entry point for the workbench."""

from fastapi import FastAPI

from backend.app.api.rag import router as rag_router
from backend.app.api.research import router as research_router
from backend.app.api.thesis import router as thesis_router

app = FastAPI(
    title="Agentic Equity Research Workbench",
    version="0.1.0",
    description="Research workflow with secure RAG, evidence, Thesis, and frozen forecasts",
)
app.include_router(research_router)
app.include_router(thesis_router)
app.include_router(rag_router)


@app.get("/health", tags=["operations"])
async def health() -> dict[str, str]:
    return {"status": "ok", "milestone": "phase-7"}
