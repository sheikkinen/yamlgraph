"""FR-782 — payload egress boundary, rendering, and deterministic diff.

The consent gate is only worth something if the previewed bytes ARE the
sent bytes (`substance_over_presence`). `build_payload` serializes the
outbound JSON exactly once, writes it to disk, and hashes it;
`verify_payload_identity` re-reads that file after the interrupt and
refuses to continue on any difference.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from .models import (
    SCHEMA_VERSION,
    ConsentEnvelope,
    ConsentPayloadMismatchError,
    Extraction,
    SynthesisPayload,
)

logger = logging.getLogger(__name__)

PAYLOAD_FILENAME = "synthesis-payload.json"
SNAPSHOT_FILENAME = "payload-snapshot.json"
JSON_FILENAME = "self-portrait.json"
MARKDOWN_FILENAME = "self-portrait.md"
DIFF_FILENAME = "portrait-diff.md"

#: Frozen agent contract (R-1) — agents may depend on these keys.
PORTRAIT_FIELDS = (
    "identity",
    "social_graph",
    "expertise",
    "geography",
    "rhythms",
    "evolution",
    "agent_briefing",
)


def confined_path(output_dir: Path | str, name: str) -> Path:
    """Resolve `name` inside `output_dir`, refusing any escape (C-2)."""
    root = Path(output_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = (root / name).resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"{name!r} resolves outside the output directory {root}")
    return target


def sha256_hex(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def payload_bytes(payload: SynthesisPayload) -> bytes:
    """Canonical, stable serialization — the exact outbound bytes."""
    return json.dumps(
        payload.model_dump(), indent=2, sort_keys=True, ensure_ascii=False
    ).encode("utf-8")


def build_payload(
    extraction: Extraction,
    output_dir: Path | str,
    portrait_date: str,
) -> tuple[SynthesisPayload, ConsentEnvelope]:
    """Build the exact synthesis payload and its consent envelope (R-2)."""
    people = [e for e in extraction.entities if e.category == "person"]
    organizations = [e for e in extraction.entities if e.category == "organization"]
    other = [
        e for e in extraction.entities if e.category not in {"person", "organization"}
    ]
    payload = SynthesisPayload(
        schema_version=SCHEMA_VERSION,
        portrait_date=portrait_date,
        people=people,
        organizations=organizations,
        other_entities=other,
        topics=extraction.topics,
        locations=extraction.locations,
        contacts=extraction.contacts,
        source_summary=extraction.source_summary,
    )
    blob = payload_bytes(payload)
    path = confined_path(output_dir, PAYLOAD_FILENAME)
    path.write_bytes(blob)
    envelope = ConsentEnvelope(
        payload_path=str(path),
        byte_count=len(blob),
        sha256=sha256_hex(blob),
        payload_json=blob.decode("utf-8"),
    )
    logger.info(
        "synthesis payload: %d bytes, sha256=%s, written to %s",
        envelope.byte_count,
        envelope.sha256,
        path,
    )
    return payload, envelope


def verify_payload_identity(envelope: dict) -> str:
    """Re-read the previewed payload and prove byte-for-byte identity."""
    path = Path(envelope["payload_path"])
    blob = path.read_bytes()
    if len(blob) != envelope["byte_count"] or sha256_hex(blob) != envelope["sha256"]:
        raise ConsentPayloadMismatchError(
            "the synthesis payload changed after consent was given "
            f"({path}): previewed {envelope['byte_count']} bytes "
            f"sha256={envelope['sha256']}, found {len(blob)} bytes "
            f"sha256={sha256_hex(blob)}"
        )
    text = blob.decode("utf-8")
    if text != envelope["payload_json"]:
        raise ConsentPayloadMismatchError(
            "the previewed payload text differs from the file about to be sent"
        )
    return text


def consent_summary(envelope: ConsentEnvelope, payload: SynthesisPayload) -> str:
    """Human-readable preview that points at the full outbound payload."""
    supplementary = ", ".join(
        f"{s.name}: {s.status}" for s in payload.source_summary.supplementary
    )
    top_people = ", ".join(p.name for p in payload.people[:5]) or "(none)"
    top_topics = (
        ", ".join(t.label or t.topic_id for t in payload.topics[:5]) or "(none)"
    )
    top_places = ", ".join(loc.locality for loc in payload.locations[:5]) or "(none)"
    return (
        "About to send your personal portrait data to the configured LLM provider.\n"
        f"  person entities  : {len(payload.people)} (top: {top_people})\n"
        f"  organizations    : {len(payload.organizations)}\n"
        f"  other entities   : {len(payload.other_entities)}\n"
        f"  topics           : {len(payload.topics)} (top: {top_topics})\n"
        f"  locality clusters: {len(payload.locations)} (top: {top_places})\n"
        f"  contacts         : {len(payload.contacts)}\n"
        f"  supplementary    : {supplementary or '(none probed)'}\n"
        f"  payload file     : {envelope.payload_path}\n"
        f"  bytes            : {envelope.byte_count}\n"
        f"  sha256           : {envelope.sha256}\n"
        "Read the payload file to see exactly what will be sent — synthesis "
        "verifies this hash before any provider call.\n"
        "Send it? [yes/no]"
    )


def _as_lines(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


def _narrative(portrait: dict, payload: SynthesisPayload, generated_at: str) -> str:
    headings = {
        "identity": "Identity",
        "social_graph": "Social Graph",
        "expertise": "Expertise",
        "geography": "Geography",
        "rhythms": "Rhythms",
        "evolution": "Evolution",
        "agent_briefing": "Agent Briefing",
    }
    parts = [
        f"# Self-Portrait — {payload.portrait_date}",
        "",
        f"_Generated {generated_at} from {payload.source_summary.db_path}_",
        "",
    ]
    for field, heading in headings.items():
        parts.append(f"## {heading}")
        parts.append("")
        lines = _as_lines(portrait.get(field))
        parts.extend([f"- {line}" for line in lines] if len(lines) > 1 else lines)
        parts.append("")
    parts += ["## Evidence", ""]
    parts += [
        "- Locality clusters: "
        + ", ".join(f"{loc.locality} ({loc.visits})" for loc in payload.locations[:10]),
        "- Topics: " + ", ".join(t.label or t.topic_id for t in payload.topics[:10]),
        "- Significant contacts: " + ", ".join(c.name for c in payload.contacts[:10]),
        "",
    ]
    for source in payload.source_summary.supplementary:
        parts.append(f"- Supplementary {source.name}: {source.status}")
    parts.append("")
    return "\n".join(parts)


def _diff_markdown(current: SynthesisPayload, previous: dict | None) -> str:
    if previous is None:
        return (
            f"# Portrait Diff — {current.portrait_date}\n\n"
            "No previous portrait snapshot found; this is the baseline run.\n"
        )

    prev_people = {p["name"] for p in previous.get("people", [])}
    now_people = {p.name for p in current.people}
    prev_places = {loc["locality"] for loc in previous.get("locations", [])}
    now_places = {loc.locality for loc in current.locations}
    prev_topics = {
        t["topic_id"]: t.get("score", 0.0) for t in previous.get("topics", [])
    }
    now_topics = {t.topic_id: t.score for t in current.topics}

    shifted = [
        f"- {qid}: {prev_topics[qid]:.2f} → {score:.2f}"
        for qid, score in sorted(now_topics.items())
        if qid in prev_topics and abs(prev_topics[qid] - score) >= 0.05
    ]
    dropped_topics = [
        f"- {qid} (dropped)" for qid in sorted(prev_topics - now_topics.keys())
    ]

    def section(title: str, items: list[str]) -> list[str]:
        return [f"## {title}", "", *(items or ["- (none)"]), ""]

    lines = [
        f"# Portrait Diff — {current.portrait_date}",
        "",
        f"Compared against snapshot dated {previous.get('portrait_date', 'unknown')}.",
        "",
    ]
    lines += section("New people", [f"- {n}" for n in sorted(now_people - prev_people)])
    lines += section(
        "Departed people", [f"- {n}" for n in sorted(prev_people - now_people)]
    )
    lines += section("Shifted topic scores", shifted + dropped_topics)
    lines += section(
        "New locations", [f"- {p}" for p in sorted(now_places - prev_places)]
    )
    lines += section(
        "Dropped locations", [f"- {p}" for p in sorted(prev_places - now_places)]
    )
    return "\n".join(lines)


def render_outputs(
    portrait: dict,
    payload: SynthesisPayload,
    output_dir: Path | str,
) -> dict[str, str]:
    """Write the frozen JSON contract, the narrative, and the diff."""
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")

    snapshot_path = confined_path(output_dir, SNAPSHOT_FILENAME)
    previous = (
        json.loads(snapshot_path.read_text(encoding="utf-8"))
        if snapshot_path.exists()
        else None
    )

    document = {
        "schema_version": SCHEMA_VERSION,
        "portrait_date": payload.portrait_date,
        "generated_at": generated_at,
        "source_summary": payload.source_summary.model_dump(),
        "provenance": [p.model_dump() for p in payload.source_summary.provenance],
    }
    for field in PORTRAIT_FIELDS:
        document[field] = portrait.get(field)

    json_path = confined_path(output_dir, JSON_FILENAME)
    json_path.write_text(
        json.dumps(document, indent=2, sort_keys=False, ensure_ascii=False),
        encoding="utf-8",
    )

    markdown_path = confined_path(output_dir, MARKDOWN_FILENAME)
    markdown_path.write_text(
        _narrative(portrait, payload, generated_at), encoding="utf-8"
    )

    diff_path = confined_path(output_dir, DIFF_FILENAME)
    diff_path.write_text(_diff_markdown(payload, previous), encoding="utf-8")

    snapshot_path.write_bytes(payload_bytes(payload))

    return {
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
        "diff_path": str(diff_path),
        "snapshot_path": str(snapshot_path),
    }


def render_extraction_summary(
    payload: SynthesisPayload, output_dir: Path | str
) -> dict[str, str]:
    """Consent denied: local extraction summary only, nothing was sent."""
    markdown_path = confined_path(output_dir, "extraction-summary.md")
    lines = [
        f"# Extraction Summary — {payload.portrait_date}",
        "",
        "Consent was declined, so this portrait was **not synthesized** — "
        "no personal data left this machine.",
        "",
        f"- Source database: {payload.source_summary.db_path}",
        f"- People: {len(payload.people)}",
        f"- Organizations: {len(payload.organizations)}",
        f"- Other entities: {len(payload.other_entities)}",
        f"- Topics: {len(payload.topics)}",
        f"- Locality clusters: {len(payload.locations)}",
        f"- Significant contacts: {len(payload.contacts)}",
        "",
        "The extracted payload remains local at "
        f"`{confined_path(output_dir, PAYLOAD_FILENAME)}`.",
        "",
    ]
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"markdown_path": str(markdown_path)}
