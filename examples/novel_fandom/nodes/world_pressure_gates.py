"""FR-692: World-pressure admission + kinship reciprocity gates (REQ-YG-531/532).

The world-pressure pass grows canon *additively* under two mechanical rules:

  * **Admission** — a newly created entity is admitted only if it cites the plot
    thread(s) it pressurizes and every cited id resolves to a live thread. No
    thread citation, no admission (`check_pressure_admission`).
  * **Reciprocity** — a kinship edge `A --kind--> B` (for a bounded set of
    reciprocal kinds) must be acknowledged by some reverse edge `B --*--> A`
    (`check_reciprocity`).

One implementation, two callers (tests + the `world_pressure.yaml` graph nodes).

RED contract: this module ships as always-valid stubs; every invalid-fixture
test fails until the real logic lands (GREEN).
"""

from __future__ import annotations

from typing import Any


def check_pressure_admission(
    entities: list[dict[str, Any]],
    thread_ids: set[str],
) -> dict[str, Any]:
    """STUB (RED): admit every candidate entity.

    GREEN contract: each entity must carry a non-empty ``pressurizes`` list and
    every cited id must be a member of ``thread_ids``.
    """
    return {"valid": True, "violations": []}


def check_reciprocity(
    characters: list[dict[str, Any]],
    reciprocal_kinds: set[str],
) -> dict[str, Any]:
    """STUB (RED): declare every kinship edge reciprocated.

    GREEN contract: for every ``A --kind--> B`` whose ``kind`` is in
    ``reciprocal_kinds``, some reverse edge ``B --*--> A`` must exist.
    """
    return {"valid": True, "violations": []}
