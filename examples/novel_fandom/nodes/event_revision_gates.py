"""FR-693: Event-revision closure, waiver, and byte-identity gates (REQ-YG-537/538).

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
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_STORY_DIR = Path(__file__).parent.parent / "story"


def check_latent_closure(
    threads: list[dict[str, Any]],
    waivers: list[dict[str, Any]],
) -> dict[str, Any]:
    """Every latent thread must be closed by events or by a waiver.

    A ``status == "latent"`` thread is closed when it carries both a non-empty
    ``raises`` and a non-empty ``releases`` list, or when its id appears in the
    waiver set. Non-latent threads are ignored.
    """
    waived = {str(w.get("thread", "")) for w in waivers}
    violations: list[str] = []
    for thread in threads:
        if thread.get("status") != "latent":
            continue
        tid = str(thread.get("id", ""))
        if tid in waived:
            continue
        raises = thread.get("raises") or []
        releases = thread.get("releases") or []
        if raises and releases:
            continue
        violations.append(f"latent thread '{tid}' has no raise+release and no waiver")
    return {"valid": not violations, "violations": violations}


def check_waiver_integrity(
    waivers: list[dict[str, Any]],
    thread_ids: set[str],
) -> dict[str, Any]:
    """Every waiver must name a live thread and carry a reason and a decider."""
    violations: list[str] = []
    for waiver in waivers:
        thread = str(waiver.get("thread", ""))
        if thread not in thread_ids:
            violations.append(f"waiver names dangling thread '{thread}'")
            continue
        if not str(waiver.get("reason", "")).strip():
            violations.append(f"waiver for '{thread}' has no reason")
        if not str(waiver.get("decided_by", "")).strip():
            violations.append(f"waiver for '{thread}' has no decider")
    return {"valid": not violations, "violations": violations}


def check_byte_identity(
    before: dict[str, bytes],
    after: dict[str, bytes],
) -> dict[str, Any]:
    """Pre-existing event files are never mutated; only new files may appear.

    Every id in ``before`` must be present in ``after`` with identical bytes.
    New ids in ``after`` are allowed (additive).
    """
    violations: list[str] = []
    for page_id, original in before.items():
        if page_id not in after:
            violations.append(f"pre-existing page '{page_id}' was deleted")
        elif after[page_id] != original:
            violations.append(f"pre-existing page '{page_id}' was mutated")
    return {"valid": not violations, "violations": violations}


# ------------------------------------------------------------------
# Graph adapters — one implementation, two callers (tests + graph nodes)
# ------------------------------------------------------------------


def _load_threads() -> list[dict[str, Any]]:
    """Read the full persisted thread dicts (with raises/releases/status)."""
    thread_dir = _STORY_DIR / "thread"
    out: list[dict[str, Any]] = []
    if thread_dir.is_dir():
        for f in sorted(thread_dir.glob("*.yaml")):
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "id" in data:
                out.append(data)
    return out


def _load_waivers() -> list[dict[str, Any]]:
    """Read the deliberate-omission waivers from story/thread_waivers.yaml."""
    f = _STORY_DIR / "thread_waivers.yaml"
    if not f.is_file():
        return []
    data = yaml.safe_load(f.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("waivers") or []
    return []


def load_revision_context(state: dict[str, Any]) -> dict[str, Any]:
    """Graph node: load threads + waivers so the gate has its post-condition.

    Also builds a digest of the *latent* threads (the deficit list) that the
    event-revision agent cites when deciding what to close.
    """
    threads = _load_threads()
    waivers = _load_waivers()
    waived = {str(w.get("thread", "")) for w in waivers}
    digest_lines: list[str] = []
    for t in threads:
        if t.get("status") != "latent":
            continue
        note = " (waived)" if t.get("id") in waived else ""
        carriers = ", ".join(t.get("carriers") or [])
        digest_lines.append(
            f"- {t['id']} ({t.get('kind', '?')}): carriers=[{carriers}] "
            f"opposition={t.get('opposition', '')}{note}"
        )
    return {
        "revision_threads": threads,
        "revision_waivers": waivers,
        "thread_ids": [t["id"] for t in threads],
        "thread_digest": "\n".join(digest_lines) or "(no latent threads)",
    }


def gate_event_revision(state: dict[str, Any]) -> dict[str, Any]:
    """Graph node: run latent-closure and waiver-integrity over loaded context.

    Reads ``revision_threads`` / ``revision_waivers`` from state (falling back
    to disk), then aggregates both verdicts under ``gate_result``. Exit gate =
    zero unwaived latents and zero dangling/incomplete waivers.
    """
    threads = state.get("revision_threads") or _load_threads()
    waivers = state.get("revision_waivers") or _load_waivers()
    thread_ids = {t["id"] for t in threads}
    closure = check_latent_closure(threads, waivers)
    integrity = check_waiver_integrity(waivers, thread_ids)
    violations = closure["violations"] + integrity["violations"]
    return {
        "gate_result": {
            "valid": not violations,
            "violations": violations,
            "closure": closure,
            "waiver_integrity": integrity,
        }
    }
