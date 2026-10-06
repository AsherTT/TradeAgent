"""FastAPI entry point for the workbench."""

from fastapi import FastAPI
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.app.api.accounts import router as accounts_router
from backend.app.api.evaluation import router as evaluation_router
from backend.app.api.rag import router as rag_router
from backend.app.api.research import router as research_router
from backend.app.api.thesis import router as thesis_router
from backend.app.api.workspace import router as workspace_router

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


@app.exception_handler(RequestValidationError)
async def safe_validation_error(request: Request, exc: RequestValidationError) -> Response:
    if request.url.path.startswith("/auth/"):
        return JSONResponse(status_code=422, content={"detail": "invalid_auth_input"})
    return await request_validation_exception_handler(request, exc)


@app.get("/health", tags=["operations"])
async def health() -> dict[str, str]:
    return {"status": "ok", "version": app.version}
