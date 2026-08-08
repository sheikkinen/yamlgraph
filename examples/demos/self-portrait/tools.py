"""FR-782 — graph-facing tools for the self-portrait example.

Thin state adapters over `extract`, `wikidata`, and `portrait_io`. All
domain logic lives in those modules; these functions only translate graph
state in and partial state updates out.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from pathlib import Path

from . import portrait_io, wikidata
from .extract import DEFAULT_DB_PATH, extract_portrait
from .models import Extraction, SynthesisPayload

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = "~/.yamlgraph/self-portrait"

_TRUTHY = {"true", "1", "yes", "y", "on"}


def _db_path(state: dict) -> str:
    return str(state.get("db_path") or DEFAULT_DB_PATH)


def _probe_home(state: dict) -> str | None:
    """Home directory the supplementary availability probes consult (C-9).

    Fixture, demo, and test runs point this at a synthetic home so the
    committed witness never discloses which databases exist on the real
    machine — availability is itself personal data. `SELF_PORTRAIT_PROBE_HOME`
    overrides; unset means the real home, which is correct for a real run.
    """
    override = state.get("probe_home") or os.environ.get("SELF_PORTRAIT_PROBE_HOME")
    return str(override) if override else None


def _output_dir(state: dict) -> Path:
    return Path(str(state.get("output_dir") or DEFAULT_OUTPUT_DIR)).expanduser()


def _portrait_date(state: dict) -> str:
    return str(state.get("portrait_date") or datetime.now(UTC).date().isoformat())


def _extraction(state: dict) -> Extraction:
    data = state.get("enriched") or state.get("extraction")
    if not data:
        raise ValueError("no extraction in state — run the extract node first")
    return Extraction.model_validate(data)


def prepare_run(state: dict) -> dict:
    """Normalize run inputs at the graph boundary (paths, date, consent mode)."""
    raw_auto = state.get("auto_approve")
    auto_approve = (
        raw_auto
        if isinstance(raw_auto, bool)
        else str(raw_auto or "").lower() in _TRUTHY
    )
    output_dir = _output_dir(state)
    output_dir.mkdir(parents=True, exist_ok=True)
    return {
        "db_path": _db_path(state),
        "output_dir": str(output_dir),
        "portrait_date": _portrait_date(state),
        "auto_approve": auto_approve,
    }


def extract_sources(state: dict) -> dict:
    """Read the primary database into validated rows (fails loud on drift)."""
    extraction = extract_portrait(_db_path(state), home=_probe_home(state))
    return {"extraction": extraction.model_dump()}


def enrich_topics(state: dict) -> dict:
    """Resolve Wikidata topic labels; unresolved topics keep their Q-ID."""
    extraction = Extraction.model_validate(state["extraction"])
    cache_dir = _output_dir(state) / "cache"
    labels = wikidata.resolve_labels(
        [topic.topic_id for topic in extraction.topics], cache_dir=cache_dir
    )
    enriched = extraction.model_copy(
        update={"topics": wikidata.apply_labels(extraction.topics, labels)}
    )
    logger.info("resolved %d/%d topic labels", len(labels), len(extraction.topics))
    return {"enriched": enriched.model_dump()}


def build_synthesis_payload(state: dict) -> dict:
    """Serialize the exact outbound payload and its consent envelope (R-2)."""
    payload, envelope = portrait_io.build_payload(
        _extraction(state), _output_dir(state), portrait_date=_portrait_date(state)
    )
    return {
        "payload": payload.model_dump(),
        "consent": envelope.model_dump(),
        "consent_summary": portrait_io.consent_summary(envelope, payload),
    }


def verify_consent(state: dict) -> dict:
    """Prove the payload about to be sent is the previewed payload (C-8)."""
    payload_json = portrait_io.verify_payload_identity(state["consent"])
    logger.info(
        "consent verified: sending %d bytes (sha256=%s)",
        state["consent"]["byte_count"],
        state["consent"]["sha256"],
    )
    return {"payload_json": payload_json}


def render_portrait(state: dict) -> dict:
    """Write the frozen JSON contract, the narrative, and the diff."""
    portrait = state.get("portrait")
    if not portrait:
        raise ValueError("no synthesized portrait in state — synthesis did not run")
    if hasattr(portrait, "model_dump"):
        portrait = portrait.model_dump()
    outputs = portrait_io.render_outputs(
        portrait, SynthesisPayload.model_validate(state["payload"]), _output_dir(state)
    )
    print(f"📝 self-portrait.json → {outputs['json_path']}")
    print(f"📝 self-portrait.md   → {outputs['markdown_path']}")
    print(f"📝 portrait-diff.md   → {outputs['diff_path']}")
    return {"outputs": outputs}


def render_extraction_only(state: dict) -> dict:
    """Consent declined: local extraction summary only, nothing was sent."""
    outputs = portrait_io.render_extraction_summary(
        SynthesisPayload.model_validate(state["payload"]), _output_dir(state)
    )
    print(f"🚫 consent declined — extraction summary → {outputs['markdown_path']}")
    return {"outputs": outputs}
