"""DM v2 story-stage routes (FR-474, Phases 1–2).

One generation mode per stage, all swapping ``#app-body`` so the breadcrumb stays
live: weave (generate/iterate), edit (autosave), accept (advance to next stage).
The endpoints always operate on the session's *current* stage, so the URL paths
are stage-agnostic; the card re-renders whichever stage is now active.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from examples.dungeon_master.api.session import DMSession, StageView

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/story", tags=["story"])

templates = Jinja2Templates(directory="examples/dungeon_master/api/templates")


def _crumbs(view: StageView) -> list[dict]:
    """Story · <accepted stages…> · <current stage> for the breadcrumb."""
    crumbs: list[dict] = [{"label": "Story"}]
    crumbs.extend({"label": label} for _, label in view.trail)
    crumbs.append({"label": view.label})
    return crumbs


def render_stage(request: Request, view: StageView, session_id: str) -> HTMLResponse:
    """Render the current stage's card (or an error card) as an #app-body fragment."""
    if view.error:
        return templates.TemplateResponse(
            request=request,
            name="components/error.html",
            context={"error": view.error, "session_id": session_id},
            status_code=400,
        )
    return templates.TemplateResponse(
        request=request,
        name="components/app_body.html",
        context={
            "mode": "stage",
            "crumbs": _crumbs(view),
            "stage": view,
            "session_id": session_id,
        },
    )


@router.post("/synopsis/weave", response_class=HTMLResponse)
async def weave_stage(
    request: Request,
    session_id: Annotated[str, Form()],
    text: Annotated[str, Form()] = "",
    prompt: Annotated[str, Form()] = "",
):
    """The single generation mode: apply the prompt to the current stage's draft."""
    logger.info("📜 Weaving stage for session %s", session_id)
    view = await DMSession(session_id).weave(text, prompt)
    return render_stage(request, view, session_id)


@router.post("/synopsis/edit", response_class=HTMLResponse)
async def edit_stage(
    request: Request,
    session_id: Annotated[str, Form()],
    text: Annotated[str, Form()] = "",
):
    """Persist the edited prose for the current stage (autosave) and re-render."""
    view = DMSession(session_id).edit(text)
    return render_stage(request, view, session_id)


@router.post("/synopsis/accept", response_class=HTMLResponse)
async def accept_stage(
    request: Request,
    session_id: Annotated[str, Form()],
    text: Annotated[str, Form()] = "",
):
    """Freeze the current stage, advance to the next, and re-render."""
    logger.info("✓ Stage accepted for session %s", session_id)
    view = await DMSession(session_id).accept(text)
    return render_stage(request, view, session_id)
