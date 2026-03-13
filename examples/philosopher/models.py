"""FR-185/FR-195: Philosopher Pydantic models and JSON extraction utility.

Provides validated models for copilot node output and a JSON extraction
helper that handles markdown fences and preamble text.
"""

import json
import re

from pydantic import BaseModel, Field


class Proposal(BaseModel):
    """A single graduation proposal."""

    type: str = Field(description="Category: trap, heuristic, or seed")
    name: str = Field(description="Pattern name (snake_case)")
    count: int = Field(description="Occurrence count across diary entries")
    files: list[str] = Field(description="Diary files where pattern appears")


class ProposalList(BaseModel):
    """Validated list of graduation proposals from analyze node."""

    proposals: list[Proposal] = Field(
        default_factory=list,
        description="List of graduation proposals",
    )


class ChallengeVerdict(BaseModel):
    """Devil's advocate verdict on a graduation candidate (FR-195)."""

    verdict: str = Field(description="'approve' or 'reject'")
    confidence: float = Field(
        description="Confidence in verdict (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    objections: list[str] = Field(
        description="Devil's advocate concerns raised",
    )
    surviving_arguments: list[str] = Field(
        description="Arguments that withstood challenge",
    )


class DiaryEntry(BaseModel):
    """Validated diary entry from reflect node."""

    theme: str = Field(description="Short title for the diary entry (2-4 words)")
    body: str = Field(description="Main reflection content in markdown format")
    seed: str = Field(description="A forward-looking question for future exploration")


def extract_json(text: str, node_name: str) -> str:
    """Extract JSON from copilot output, stripping markdown fences and preamble.

    Strategy:
    1. Strip markdown code fences (```json ... ```)
    2. Find first [ or { to last ] or }
    3. Raise ValueError on failure (no silent fallbacks per Commandment 6)
    """
    # Strip markdown fences
    stripped = re.sub(r"```(?:json)?\s*\n?", "", text).strip()
    if stripped.endswith("```"):
        stripped = stripped[:-3].strip()

    # Find JSON boundaries
    for start_char, end_char in [("[", "]"), ("{", "}")]:
        start = stripped.find(start_char)
        end = stripped.rfind(end_char)
        if start != -1 and end > start:
            candidate = stripped[start : end + 1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                continue

    raise ValueError(
        f"No valid JSON found in copilot output for node '{node_name}'. "
        f"Preview: {text[:200]}"
    )
