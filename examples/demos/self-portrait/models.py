"""FR-782 self-portrait — typed boundary models (R-6).

Every row that leaves the SQLite boundary is validated here. Schema drift
across macOS versions is asserted at this boundary, never patched
downstream (`the_one_law`): unknown entity categories, missing required
tables, and unreadable databases raise named errors instead of degrading
into empty sections.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

SCHEMA_VERSION = "1.0"

#: `ne_records.category` -> stable portrait category name.
#: Source inventory: control-plane `docs/plan-self-portrait.md`.
ENTITY_CATEGORIES: dict[int, str] = {
    1: "person",
    2: "organization",
    5: "place",
    8: "product",
    9: "event",
    10: "creative_work",
    11: "technology",
    12: "concept",
}

EntityCategory = Literal[
    "person",
    "organization",
    "place",
    "product",
    "event",
    "creative_work",
    "technology",
    "concept",
]


class SchemaDriftError(RuntimeError):
    """The database schema differs from the asserted contract.

    Raised at the extraction boundary — a missing required table or an
    unknown category id is drift, and drift is reported, never absorbed.
    """


class DatabaseUnreadableError(RuntimeError):
    """The primary database is missing or unreadable (usually TCC/FDA)."""


class ConsentPayloadMismatchError(RuntimeError):
    """The payload about to be sent differs from the previewed payload."""


class EntityRow(BaseModel):
    """A named entity (`ne_records`)."""

    name: str
    category: EntityCategory
    score: float = 0.0
    language: str | None = None


class TopicRow(BaseModel):
    """A Wikidata-identified topic (`tp_records`)."""

    topic_id: str
    score: float = 0.0
    label: str | None = None

    @field_validator("topic_id")
    @classmethod
    def _q_id(cls, value: str) -> str:
        if not value.startswith("Q") or not value[1:].isdigit():
            raise ValueError(f"topic_id is not a Wikidata Q-ID: {value!r}")
        return value


class LocationRow(BaseModel):
    """A visited locality cluster (`loc_records`)."""

    locality: str
    country: str | None = None
    visits: int = 1


class ContactRow(BaseModel):
    """A significant contact (`significant_contacts`)."""

    name: str
    score: float = 0.0
    first_seen: str | None = None
    last_seen: str | None = None


class ProvenanceRow(BaseModel):
    """Where the device learned things (`sources`)."""

    source: str
    record_count: int = 0


class SupplementarySource(BaseModel):
    """Availability probe for a supplementary database (R-3).

    FR-782 probes only: `available` never implies a parser exists. `path`
    is home-relative — the absolute path carries the account name and this
    model is part of the outbound consent payload.
    """

    name: str
    path: str
    available: bool = False
    status: Literal["absent", "not configured", "present (not parsed)"] = "absent"


class SourceSummary(BaseModel):
    """Counts and provenance for the whole extraction."""

    db_path: str
    entity_count: int = 0
    topic_count: int = 0
    location_count: int = 0
    contact_count: int = 0
    provenance: list[ProvenanceRow] = Field(default_factory=list)
    supplementary: list[SupplementarySource] = Field(default_factory=list)


class Extraction(BaseModel):
    """Everything read from the primary database, typed."""

    entities: list[EntityRow] = Field(default_factory=list)
    topics: list[TopicRow] = Field(default_factory=list)
    locations: list[LocationRow] = Field(default_factory=list)
    contacts: list[ContactRow] = Field(default_factory=list)
    source_summary: SourceSummary


class SynthesisPayload(BaseModel):
    """The exact data that will be sent to the LLM (R-2, C-8).

    This model IS the egress boundary: the consent preview serializes it,
    and synthesis consumes the same serialization byte-for-byte.
    """

    schema_version: str = SCHEMA_VERSION
    portrait_date: str
    people: list[EntityRow] = Field(default_factory=list)
    organizations: list[EntityRow] = Field(default_factory=list)
    other_entities: list[EntityRow] = Field(default_factory=list)
    topics: list[TopicRow] = Field(default_factory=list)
    locations: list[LocationRow] = Field(default_factory=list)
    contacts: list[ContactRow] = Field(default_factory=list)
    source_summary: SourceSummary


class ConsentEnvelope(BaseModel):
    """Preview metadata proving payload identity across the interrupt."""

    payload_path: str
    byte_count: int
    sha256: str
    payload_json: str
