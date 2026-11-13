"""
app/main.py — FastAPI application factory.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Endpoints:
    POST   /api/migration/start                 → kick off migration
    GET    /api/migration/{id}/status           → poll state
    GET    /api/migration/{id}/stream           → SSE live updates
    POST   /api/migration/{id}/decision         → HITL approve/reject
    GET    /api/migration/{id}/iac              → download .tf file
    GET    /health                              → liveness probe
    GET    /docs                                → Swagger UI
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.migration import router as migration_router

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Startup: pre-warm the LangGraph compiled graph so the first request
    isn't slow. Also validates that AWS MCP servers can be reached.
    Shutdown: nothing to tear down (InMemorySaver is in-process).
    """
    logger.info("⚙️  Starting AWS Migration Agent API...")

    # Import here to trigger builder.py module-level graph compilation
    from app.graph.builder import migration_graph as _migration_graph  # noqa: F401
    logger.info("✅ LangGraph compiled and ready")

    # Pre-warm MCP client (spawns uvx subprocesses)
    try:
        from app.tools.aws_mcp_client import get_aws_tools
        tools = await get_aws_tools()
        logger.info("✅ AWS MCP tools loaded (%d tools)", len(tools))
    except Exception as exc:
        logger.warning("⚠️  AWS MCP pre-warm failed: %s — tools will load on first request", exc)

    yield

    logger.info("🛑 Shutting down AWS Migration Agent API")


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="AWS Cloud Migration Agent",
        description=(
            "LangGraph-powered agent that discovers tagged AWS resources, "
            "generates Terraform / CloudFormation IaC, and migrates them "
            "to a target region with human-in-the-loop approval."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS — allow React dev server ────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",   # Vite default
            "http://localhost:3000",   # CRA / other
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──────────────────────────────────────────────────────────────
    app.include_router(health_router)
    app.include_router(migration_router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],
    )