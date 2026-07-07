"""Pydantic models for novel_fandom canon pages.

Typed schemas for fiction entities: Character, Event, Faction, Location, Rule.
Each page has a lane (static|dynamic) for immutability control.
"""

from typing import Literal

from pydantic import BaseModel, Field


class Relationship(BaseModel):
    """A typed, directed relationship between two canon entities."""

    to: str = Field(description="Target entity id")
    kind: str = Field(description="Relationship type (e.g. mentor, rival, ally)")
    valence: str = Field(description="Emotional valence (e.g. trust, enmity, fear)")


class Character(BaseModel):
    """A fiction character with goals, personality, and relationships."""

    type: Literal["character"] = "character"
    id: str
    lane: Literal["static", "dynamic"]
    name: str
    depth: int = 0
    goals: list[str] = Field(default_factory=list)
    personality: str = ""
    faction: str = ""
    relationships: list[Relationship] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    timeline_entry: str = ""
    role: Literal["protagonist", "antagonist", "supporting", "minor"] = "supporting"
    driving_force: str = ""
    wants: str = ""
    needs: str = ""
    fears: list[str] = Field(default_factory=list)
    arc_summary: str = ""
    triggers: list[str] = Field(default_factory=list)
    backstory: str = ""
    birth_year: int | None = None


class Event(BaseModel):
    """A timeline event with participants and bi-temporal validity."""

    type: Literal["event"] = "event"
    id: str
    lane: Literal["static", "dynamic"]
    depth: int = 0
    window: str = ""
    participants: list[str] = Field(default_factory=list)
    consequences: list[str] = Field(default_factory=list)
    valid_from: str | None = None
    valid_to: str | None = None
    year: int | None = None
    sequence: int | None = Field(
        default=None,
        description=(
            "Global total order across all events (FR-690). Optional at the "
            "schema layer so genesis/create_event keep validating; the story "
            "pipeline's mechanical check makes it mandatory for the canon. "
            "Gaps allowed (10, 20, 30 …) for insertion without renumbering."
        ),
    )
    scope: Literal["world", "regional", "local"] = "world"
    affected_locations: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)


class Faction(BaseModel):
    """A named faction or organization."""

    type: Literal["faction"] = "faction"
    id: str
    lane: Literal["static", "dynamic"]
    name: str
    depth: int = 0
    description: str = ""
    members: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)


class Location(BaseModel):
    """A named location in the fiction world."""

    type: Literal["location"] = "location"
    id: str
    lane: Literal["static", "dynamic"]
    name: str
    depth: int = 0
    description: str = ""
    references: list[str] = Field(default_factory=list)
    location_type: str = ""
    atmosphere: list[str] = Field(default_factory=list)
    sensory: list[str] = Field(default_factory=list)
    significance: str = ""


class Rule(BaseModel):
    """A world constraint that the story must obey."""

    type: Literal["rule"] = "rule"
    id: str
    lane: Literal["static", "dynamic"]
    depth: int = 0
    domain: Literal[
        "magic_system",
        "character_state",
        "physical_constraint",
        "social_rule",
        "temporal_rule",
    ]
    title: str
    description: str = ""
    references: list[str] = Field(default_factory=list)


class Premise(BaseModel):
    """The thematic seed of the fiction world."""

    type: Literal["premise"] = "premise"
    id: str
    lane: Literal["static", "dynamic"]
    depth: int = 0
    text: str
    genre_tags: list[str] = Field(default_factory=list)
    era: str = ""
    themes: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    calendar_note: str = ""


class Synopsis(BaseModel):
    """Full-disclosure reveal-all prose expanding the premise."""

    type: Literal["synopsis"] = "synopsis"
    id: str
    lane: Literal["static", "dynamic"]
    depth: int = 0
    text: str
    references: list[str] = Field(default_factory=list)


PAGE_MODELS: dict[str, type[BaseModel]] = {
    "character": Character,
    "event": Event,
    "faction": Faction,
    "location": Location,
    "premise": Premise,
    "rule": Rule,
    "synopsis": Synopsis,
}


def validate_page(data: dict) -> BaseModel:
    """Validate a canon page dict against its type's Pydantic model.

    Raises:
        KeyError: if 'type' field is missing
        ValueError: if type is not recognized
        pydantic.ValidationError: if data doesn't match the schema
    """
    page_type = data["type"]
    model_cls = PAGE_MODELS.get(page_type)
    if model_cls is None:
        msg = f"Unknown page type: {page_type!r}"
        raise ValueError(msg)
    return model_cls.model_validate(data)
