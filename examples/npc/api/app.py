"""NPC Encounter Web UI - FastAPI Application.

HTMX-powered web interface for running NPC encounters.
Uses YAMLGraph for encounter logic with session persistence.

Usage:
    uvicorn examples.npc.api.app:app --reload

    # Or with custom port
    uvicorn examples.npc.api.app:app --reload --port 8080
"""

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from examples.npc.api.routes.encounter import router as encounter_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle handler."""
    logger.info("🚀 Starting NPC Encounter Web UI...")
    logger.info("📍 Templates: examples/npc/api/templates")
    logger.info("📦 Static files: examples/npc/api/static")
    yield
    logger.info("👋 Shutting down NPC Encounter Web UI...")


# Create FastAPI app
app = FastAPI(
    title="NPC Encounter Web UI",
    description="HTMX-powered web interface for running NPC encounters",
    version="0.1.0",
    lifespan=lifespan,
)

# Templates
templates = Jinja2Templates(directory="examples/npc/api/templates")

# Include routers
app.include_router(encounter_router)

# Mount static files (create directory if needed)
try:
    app.mount(
        "/static", StaticFiles(directory="examples/npc/api/static"), name="static"
    )
except RuntimeError:
    # Static directory doesn't exist, that's fine
    logger.warning("⚠️ Static directory not found, skipping static mount")

# Mount outputs directory for generated images
try:
    app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
    logger.info("📁 Mounted outputs directory for generated images")
except RuntimeError:
    logger.warning("⚠️ Outputs directory not found, skipping outputs mount")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main encounter page."""
    # Generate a unique session ID for this encounter
    session_id = str(uuid.uuid4())[:8]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"session_id": session_id},
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "npc-encounter-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "examples.npc.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
