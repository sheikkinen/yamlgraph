"""Persist deepened + skeleton pages to canon/ with Pydantic validation.

Validates each page against canon.py models before writing.
Uses atomic writes (tempfile + os.replace). Skeletons don't overwrite.
Normalizes LLM-varied shapes to schema shapes at the boundary (FR-649).
"""

from __future__ import annotations

import importlib.util
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_VALID_RULE_DOMAINS = frozenset(
    {
        "magic_system",
        "character_state",
        "physical_constraint",
        "social_rule",
        "temporal_rule",
    }
)

_LIST_STR_FIELDS = frozenset(
    {
        "atmosphere",
        "sensory",
        "goals",
        "fears",
        "triggers",
        "genre_tags",
        "themes",
        "members",
        "affected_locations",
    }
)


def normalize_page(page: dict) -> dict:
    """Coerce LLM-varied shapes to schema-expected shapes (FR-649).

    Runs at the persist boundary before Pydantic validation.
    Mutates and returns the same dict.
    """
    # Strip map-node metadata
    page.pop("_map_index", None)

    # --- Relationships ---
    rels = page.get("relationships")
    if isinstance(rels, dict) and not isinstance(rels, list):
        # dict-of-strings: {target: description, ...}
        page["relationships"] = [
            {"to": target, "kind": desc, "valence": ""} for target, desc in rels.items()
        ]
    elif isinstance(rels, list):
        normalized_rels = []
        for rel in rels:
            if not isinstance(rel, dict):
                continue
            if "to" in rel and "kind" in rel:
                # Already correct format
                rel.setdefault("valence", "")
                normalized_rels.append(rel)
            else:
                to = rel.get(
                    "to", rel.get("target", rel.get("target_id", rel.get("id", "?")))
                )
                kind = rel.get(
                    "kind", rel.get("type", rel.get("description", "related"))
                )
                valence = rel.get("valence", "")
                normalized_rels.append({"to": to, "kind": kind, "valence": valence})
        page["relationships"] = normalized_rels

    # --- Participants (Event) ---
    participants = page.get("participants")
    if isinstance(participants, list):
        normalized = []
        for p in participants:
            if isinstance(p, dict):
                normalized.append(p.get("entity", p.get("name", str(p))))
            else:
                normalized.append(str(p))
        page["participants"] = normalized

    # --- Consequences (Event) ---
    consequences = page.get("consequences")
    if isinstance(consequences, dict):
        page["consequences"] = [f"{key}: {val}" for key, val in consequences.items()]

    # --- References ---
    refs = page.get("references")
    if isinstance(refs, list):
        normalized_refs = []
        for ref in refs:
            if isinstance(ref, dict):
                normalized_refs.append(ref.get("pageId", ref.get("id", str(ref))))
            else:
                normalized_refs.append(str(ref))
        page["references"] = normalized_refs

    # --- Scalar → list coercion for list[str] fields ---
    for field in _LIST_STR_FIELDS:
        val = page.get(field)
        if isinstance(val, str):
            page[field] = [val]

    # --- Rule.domain default ---
    if page.get("type") == "rule":
        domain = page.get("domain", "")
        if domain not in _VALID_RULE_DOMAINS:
            page["domain"] = "social_rule"

    return page


def _load_page_models() -> dict:
    """Load PAGE_MODELS from canon.py via importlib to avoid import issues."""
    schema_path = Path(__file__).parent.parent / "schema" / "canon.py"
    spec = importlib.util.spec_from_file_location(
        "novel_fandom_schema_canon", schema_path
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    page_models = mod.PAGE_MODELS  # type: ignore[attr-defined]
    # Rebuild models to resolve deferred annotations (from __future__ import annotations)
    for model_cls in page_models.values():
        model_cls.model_rebuild()
    return page_models


def _validate_and_write(
    page: dict,
    canon_dir: Path,
    page_models: dict,
    *,
    overwrite: bool = True,
) -> str | None:
    """Validate a page and write it atomically. Returns path or None."""
    if not page or "id" not in page or "type" not in page:
        return None

    model_cls = page_models.get(page["type"])
    if not model_cls:
        logger.warning(
            "Unknown page type '%s' for '%s'", page.get("type"), page.get("id")
        )
        return None

    # FR-649: Normalize LLM-varied shapes before validation
    normalize_page(page)

    try:
        model_cls(**page)
    except Exception as e:  # noqa: BLE001
        # FR-649 fallback: persist anyway with warning — work product > schema purity
        logger.warning(
            "Validation failed for '%s' (persisting anyway): %s",
            page.get("id"),
            e,
        )

    page_type = page.get("type", "misc")
    type_dir = canon_dir / page_type
    type_dir.mkdir(parents=True, exist_ok=True)
    target = type_dir / f"{page['id']}.yaml"
    if not overwrite and target.exists():
        return None

    fd, tmp_path = tempfile.mkstemp(dir=type_dir, suffix=".tmp", prefix=".persist_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                page, f, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
        os.replace(tmp_path, target)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    return str(target)


def persist_pages(state: dict[str, Any]) -> dict[str, Any]:
    """Write deepened + skeleton pages to canon/."""
    canon_dir = Path(__file__).parent.parent / "canon"
    return _persist_impl(state, canon_dir)


def _persist_impl(
    state: dict[str, Any],
    canon_dir: Path,
    page_models: dict | None = None,
) -> dict[str, Any]:
    """Implementation with injectable canon_dir and page_models for testing."""
    if page_models is None:
        page_models = _load_page_models()
    written: list[str] = []

    for result in state.get("deepened", []):
        if not isinstance(result, dict):
            continue
        page = result.get("updated_page", {})
        path = _validate_and_write(page, canon_dir, page_models, overwrite=True)
        if path:
            written.append(path)

    for skeleton in state.get("skeletons", []):
        if not isinstance(skeleton, dict):
            continue
        # Extract page from schema wrapper (schema returns {page: dict})
        page = skeleton.get("page", skeleton)
        if not isinstance(page, dict):
            continue
        # Skeletons bypass Pydantic validation — they are deliberately minimal
        # and will be deepened (with full validation) on the next loop iteration.
        if "id" not in page or "type" not in page:
            continue
        page.setdefault("lane", "dynamic")
        page_type = page.get("type", "misc")
        type_dir = canon_dir / page_type
        type_dir.mkdir(parents=True, exist_ok=True)
        target = type_dir / f"{page['id']}.yaml"
        if any(canon_dir.rglob(f"{page['id']}.yaml")):
            continue
        fd, tmp_path = tempfile.mkstemp(dir=type_dir, suffix=".tmp", prefix=".persist_")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    page,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
            os.replace(tmp_path, target)
            written.append(str(target))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    return {"written_paths": written, "written_count": len(written)}
