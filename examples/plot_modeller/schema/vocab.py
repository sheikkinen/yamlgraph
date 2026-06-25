"""FR-593 — Story-level vocabulary for the L5 perspective stage.

``StoryVocab`` is the validated structured binding for the ``extract_vocab`` output.
It exists to make the FR-592 regression impossible to reintroduce: there, the vocab
arrived as a markdown *string* on the consumed path and was inert. A bare string fails
``model_validate`` here, so the canonicalization stage can only receive a real object.

Scope (code-verified): *characters* are not modelled — at Mode 8 the agent list is
ground-truth supplied (``_load_gt_agents``). The novel, non-oracle vocabulary is
**locations + objects** plus an ``aliases`` map (loose mention -> canonical token).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StoryVocab(BaseModel):
    model_config = ConfigDict(extra="ignore")

    locations: list[str] = Field(
        default_factory=list, description="Canonical location names"
    )
    objects: list[str] = Field(
        default_factory=list, description="Canonical object names"
    )
    aliases: dict[str, str] = Field(
        default_factory=dict,
        description="Loose mention -> canonical token (e.g. 'the lab' -> 'Vantari Labs')",
    )
