"""Dungeon Master v2 — FastAPI app (FR-474 synopsis prototype).

The landing page *is* the synopsis card, seeded with a default tagline — there is
no separate setup/splash screen. Every action swaps ``#app-body`` so the
breadcrumb stays live.

Usage:
    uvicorn examples.dungeon_master.api.app:app --reload
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from examples.dungeon_master.api.routes.synopsis import router as synopsis_router
from examples.dungeon_master.api.session import DEFAULT_TAGLINE, FIRST_STAGE, StageView

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🎲 Starting Dungeon Master v2 (synopsis prototype)...")
    yield
    logger.info("👋 Shutting down Dungeon Master v2...")


app = FastAPI(
    title="Dungeon Master v2",
    description="Synopsis prototype — interactive generation of one artifact",
    version="0.2.0",
    lifespan=lifespan,
)

templates = Jinja2Templates(directory="examples/dungeon_master/api/templates")

app.include_router(synopsis_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Land directly on the first stage's card, seeded with the default tagline."""
    session_id = str(uuid.uuid4())[:8]
    response = templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "mode": "stage",
            "crumbs": [{"label": "Story"}, {"label": FIRST_STAGE.label}],
            "stage": StageView(
                stage=FIRST_STAGE.name,
                label=FIRST_STAGE.label,
                tagline=DEFAULT_TAGLINE,
            ),
            "session_id": session_id,
        },
    )
    response.headers["x-session-id"] = session_id
    return response


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "dungeon-master-v2"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "examples.dungeon_master.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
