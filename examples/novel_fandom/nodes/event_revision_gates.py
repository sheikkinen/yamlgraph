"""FR-693: Event-revision closure, waiver, and byte-identity gates (REQ-YG-534/535).

The event-revision pass closes latent threads by adding events (additive only)
or documents a deliberate omission in a waiver file. Three pure mechanical
gates enforce it:

  * **latent closure** — every ``status == "latent"`` thread must gain both a
    raise and a release event, or appear in the waiver set
    (``check_latent_closure``).
  * **waiver integrity** — every waiver names a live thread and carries a reason
    and a decider (``check_waiver_integrity``).
  * **byte identity** — pre-existing event files are never mutated; only new
    files may appear (``check_byte_identity``).

One implementation, two callers (tests + the ``event_revision.yaml`` graph).

RED contract: this module ships as always-valid stubs; every invalid-fixture
test fails until the real logic lands (GREEN).
"""

from __future__ import annotations

from typing import Any


def check_latent_closure(
    threads: list[dict[str, Any]],
    waivers: list[dict[str, Any]],
) -> dict[str, Any]:
    """STUB (RED): declare every latent thread closed.

    GREEN contract: each ``status == "latent"`` thread must carry non-empty
    ``raises`` AND ``releases``, or its id must appear in a waiver.
    """
    return {"valid": True, "violations": []}


def check_waiver_integrity(
    waivers: list[dict[str, Any]],
    thread_ids: set[str],
) -> dict[str, Any]:
    """STUB (RED): accept every waiver.

    GREEN contract: each waiver's ``thread`` must be in ``thread_ids`` and it
    must carry a non-empty ``reason`` and ``decided_by``.
    """
    return {"valid": True, "violations": []}


def check_byte_identity(
    before: dict[str, bytes],
    after: dict[str, bytes],
) -> dict[str, Any]:
    """STUB (RED): declare all pre-existing files unchanged.

    GREEN contract: every id in ``before`` must be present in ``after`` with
    identical bytes. New ids in ``after`` are allowed (additive).
    """
    return {"valid": True, "violations": []}
