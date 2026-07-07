"""Pydantic models for novel_fandom derived story artifacts (FR-691).

Threads (decomposition by conflict) and throughlines (decomposition by
character) are *derived* from canon — they regenerate, canon grows. They live
in a separate module from `canon.py` so the two truths stay distinct and
`canon.py` stays under the module-size limit.

- `Thread`: a plot tension with carriers, sources, opposition, and a
  raise/release event ledger.
- `Throughline`: a per-character emotional walk over events in `sequence`
  order.

The mechanical gates that validate sets of these live in
`examples/novel_fandom/nodes/thread_gates.py` (one implementation, two callers:
graph nodes and tests).
"""

from typing import Literal

from pydantic import BaseModel, Field

ThreadKind = Literal["feud", "bond", "belief", "survival", "succession"]
ThreadStatus = Literal["open", "escalating", "released", "latent"]
EntryDelta = Literal["gain", "loss", "none"]


class Thread(BaseModel):
    """A plot thread: a tension that opens and (maybe) closes across events."""

    type: Literal["thread"] = "thread"
    id: str
    kind: ThreadKind
    carriers: list[str] = Field(
        default_factory=list,
        description="Character ids that carry the tension; must resolve to canon.",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Canon ids (rules, factions, backstory) this thread derives from.",
    )
    opposition: str = Field(
        description="What stands against resolution. Required, non-empty — a "
        "tension nobody opposes is a theme, not a thread.",
    )
    stakes: str = Field(
        default="",
        description="What is lost if the thread is never resolved.",
    )
    raises: list[str] = Field(
        default_factory=list,
        description="Event ids that open/escalate the thread.",
    )
    releases: list[str] = Field(
        default_factory=list,
        description="Event ids that resolve the thread; empty => status != released.",
    )
    status: ThreadStatus = "latent"
    justification: str = Field(
        default="",
        description="For latent threads mined in reconcile: the canon field it "
        "was drawn from (admission rationale under the cap).",
    )


class ThroughlineEntry(BaseModel):
    """One character's emotional state at one event on their throughline."""

    event: str = Field(
        description="Event id; must resolve to canon and carry a sequence."
    )
    emotion: str = Field(description="Emotional state at this event.")
    delta: EntryDelta = Field(
        default="none",
        description="Emotional change from the prior entry: gain, loss, or none.",
    )
    slack: bool = Field(
        default=False,
        description="A breathing point — the reader gets air here.",
    )


class Throughline(BaseModel):
    """A character's emotional walk over the events they appear in."""

    type: Literal["throughline"] = "throughline"
    character: str = Field(description="Character id; must resolve to canon.")
    entries: list[ThroughlineEntry] = Field(default_factory=list)
    arc_taut: bool = Field(
        default=False,
        description="Explicit claim that the arc has no slack by design — the "
        "only way to pass the slack-point acceptance without a slack point.",
    )


STORY_MODELS: dict[str, type[BaseModel]] = {
    "thread": Thread,
    "throughline": Throughline,
}
