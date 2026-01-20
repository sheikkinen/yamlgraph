"""Encounter API routes.

HTMX-powered endpoints for NPC encounter management.
Returns HTML fragments for dynamic page updates.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from examples.npc.api.session import (
    EncounterSession,
    TurnResult,
    create_npcs_from_concepts,
    get_encounter_graph,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/encounter", tags=["encounter"])

# Templates - configured at app startup
templates = Jinja2Templates(directory="examples/npc/api/templates")


async def _get_session(session_id: str) -> EncounterSession:
    """Create session wrapper for given session_id."""
    graph = await get_encounter_graph()
    return EncounterSession(graph, session_id)


def _render_turn_result(
    request: Request,
    result: TurnResult,
    session_id: str,
) -> HTMLResponse:
    """Render turn result as HTML fragment."""
    if result.error:
        return templates.TemplateResponse(
            request=request,
            name="components/error.html",
            context={
                "error": result.error,
                "session_id": session_id,
            },
            status_code=400,
            headers={"HX-Trigger": "encounter-error"},
        )

    return templates.TemplateResponse(
        request=request,
        name="components/turn_result.html",
        context={
            "turn_number": result.turn_number,
            "narrations": result.narrations,
            "scene_image": result.scene_image,
            "turn_summary": result.turn_summary,
            "is_complete": result.is_complete,
            "session_id": session_id,
        },
        headers={"HX-Trigger": "encounter-updated"},
    )


@router.post("/start", response_class=HTMLResponse)
async def start_encounter(
    request: Request,
    session_id: Annotated[str, Form()],
    location: Annotated[str, Form()] = "tavern",
):
    """Start a new encounter session.

    Args:
        session_id: Unique identifier for this encounter session
        location: Where the encounter takes place

    Returns:
        HTML fragment with initial encounter state
    """
    logger.info(f"📝 Starting encounter {session_id} at {location}")

    # Get concepts from form data - always use getlist for multiple values
    form_data = await request.form()
    concepts = form_data.getlist("npc_concepts")
    logger.info(f"📋 NPC concepts received: {concepts}")

    # Create NPCs from concepts
    if concepts:
        concept_dicts = [{"concept": c} for c in concepts if c.strip()]
        logger.info(f"🎭 Creating {len(concept_dicts)} NPCs from concepts")
        npcs = await create_npcs_from_concepts(concept_dicts)
    else:
        # Default NPC
        logger.info("🎭 No concepts provided, using default NPC")
        npcs = [{"name": "Innkeeper", "race": "human", "character_class": "Commoner"}]

    logger.info(f"✅ Created {len(npcs)} NPCs")

    # Start encounter
    session = await _get_session(session_id)
    result = await session.start(npcs=npcs, location=location)

    return _render_turn_result(request, result, session_id)


@router.post("/turn", response_class=HTMLResponse)
async def process_turn(
    request: Request,
    session_id: Annotated[str, Form()],
    dm_input: Annotated[str, Form()],
):
    """Process a DM input turn.

    Args:
        session_id: The encounter session to resume
        dm_input: DM's input/narration for the turn

    Returns:
        HTML fragment with NPC responses
    """
    logger.info(f"🎲 Processing turn for {session_id}")

    session = await _get_session(session_id)

    # Check if session exists
    if not await session._is_resume():
        return templates.TemplateResponse(
            request=request,
            name="components/error.html",
            context={
                "error": "Session not found. Please start a new encounter.",
                "session_id": session_id,
            },
            status_code=400,
            headers={"HX-Trigger": "encounter-error"},
        )

    result = await session.turn(dm_input)

    return _render_turn_result(request, result, session_id)


@router.get("/{session_id}", response_class=HTMLResponse)
async def get_encounter_state(
    request: Request,
    session_id: str,
):
    """Get current encounter state.

    Args:
        session_id: The encounter session to retrieve

    Returns:
        HTML fragment with current encounter state
    """
    session = await _get_session(session_id)

    # Check if session exists
    if not await session._is_resume():
        raise HTTPException(status_code=404, detail="Session not found")

    # Get state from graph
    graph = await get_encounter_graph()
    config = {"configurable": {"thread_id": session_id}}
    state = await graph.aget_state(config)

    return templates.TemplateResponse(
        request=request,
        name="components/encounter_state.html",
        context={
            "session_id": session_id,
            "turn_number": state.values.get("turn_number", 0),
            "narrations": state.values.get("narrations", []),
            "npcs": state.values.get("npcs", []),
            "location": state.values.get("location", "Unknown"),
        },
    )
