"""FastAPI entry point for the workbench."""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.app.api.accounts import router as accounts_router
from backend.app.api.company_discovery import router as company_discovery_router
from backend.app.api.evaluation import router as evaluation_router
from backend.app.api.rag import router as rag_router
from backend.app.api.research import router as research_router
from backend.app.api.thesis import router as thesis_router
from backend.app.api.workspace import router as workspace_router
from backend.app.api.workspace_portal import router as workspace_portal_router
from backend.app.api.workspace_research import router as workspace_research_router

app = FastAPI(
    title="Agentic Equity Research Workbench",
    version="0.1.0",
    description="Research workflow with secure RAG, evidence, Thesis, and frozen forecasts",
)
app.include_router(research_router)
app.include_router(thesis_router)
app.include_router(rag_router)
app.include_router(evaluation_router)
app.include_router(accounts_router)
app.include_router(workspace_router)
app.include_router(company_discovery_router)
app.include_router(workspace_portal_router)
app.include_router(workspace_research_router)


@app.middleware("http")
async def account_research_cache_control(
    request: Request, call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    response = await call_next(request)
    if request.url.path.startswith("/workspace/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(RequestValidationError)
async def safe_validation_error(request: Request, exc: RequestValidationError) -> Response:
    if request.url.path.startswith("/auth/"):
        return JSONResponse(status_code=422, content={"detail": "invalid_auth_input"})
    if request.url.path.startswith("/workspace/research"):
        return JSONResponse(status_code=422, content={"detail": "invalid_research_input"})
    return await request_validation_exception_handler(request, exc)


@app.get("/health", tags=["operations"])
async def health() -> dict[str, str]:
    return {"status": "ok", "version": app.version}
