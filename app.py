"""
EquiLearn FastAPI application entry point.
AI/ML logic lives in orchestrator.py, integration_adapter.py, package_builder.py.
This file only wires routes and configures the app.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.routes.health import router as health_router
from api.routes.jobs import router as jobs_router
from db.init_db import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup (idempotent)."""
    create_tables()
    yield
    # shutdown: nothing to teardown yet


app = FastAPI(
    title="EquiLearn API",
    description="Accessibility-first learning content transformation service.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)

# Mount all v1 routes under /api/v1/
app.include_router(health_router, prefix="/api/v1")
app.include_router(jobs_router,   prefix="/api/v1")

# ----- root redirect for convenience -----
from fastapi.responses import RedirectResponse

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/api/v1/health")
