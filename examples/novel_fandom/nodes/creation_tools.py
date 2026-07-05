"""Creation pipeline nodes for agent-first genesis/worldgen (FR-686).

Three node functions for the create_*.yaml graph-tool pipelines:
1. persist_entity(state)  — Pydantic-validate + atomic write (hard gate)
2. build_check_context(state) — canon digest + ref prefetch for LLM check
3. final_gate(state) — deterministic terminal gate (AC-10)

Plus standalone python tools (no pipeline logic needed):
- list_thin_entities, deepen_entity, persist_synopsis
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_CANON_DIR = Path(__file__).parent.parent / "canon"

_VALID_ROLES = frozenset({"protagonist", "antagonist", "supporting", "minor"})
_VALID_SCOPES = frozenset({"world", "regional", "local"})
_VALID_RULE_DOMAINS = frozenset(
    {
        "magic_system",
        "character_state",
        "physical_constraint",
        "social_rule",
        "temporal_rule",
    }
)

_nodes_dir = str(Path(__file__).parent)
if _nodes_dir not in sys.path:
    sys.path.insert(0, _nodes_dir)


def _canon_path() -> Path:
    return _CANON_DIR


def _load_page_models() -> dict:
    """Load PAGE_MODELS from canon.py."""
    schema_path = Path(__file__).parent.parent / "schema" / "canon.py"
    spec = importlib.util.spec_from_file_location("nf_canon_creation", schema_path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    page_models = mod.PAGE_MODELS
    for m in page_models.values():
        m.model_rebuild()
    return page_models


def _write_page(page: dict, canon_dir: Path) -> str:
    """Validate with Pydantic and write atomically. Returns path or error."""
    page_type = page.get("type", "misc")
    page_id = page.get("id", "unknown")

    page_models = _load_page_models()
    model_cls = page_models.get(page_type)
    if model_cls:
        try:
            model_cls(**page)
        except Exception as e:  # noqa: BLE001
            return f"Error: validation failed for '{page_id}': {e}"

    type_dir = canon_dir / page_type
    type_dir.mkdir(parents=True, exist_ok=True)
    target = type_dir / f"{page_id}.yaml"

    fd, tmp_path = tempfile.mkstemp(dir=type_dir, suffix=".tmp", prefix=".create_")
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


def _parse_id_role_pairs(text: str) -> list[dict[str, str]]:
    """Parse 'id:role, id2:role2' into list of {to, kind} dicts."""
    if not text or not text.strip():
        return []
    pairs = []
    for part in text.split(","):
        part = part.strip()
        if ":" in part:
            ref_id, role = part.split(":", 1)
            pairs.append({"to": ref_id.strip(), "kind": role.strip(), "valence": ""})
        elif part:
            pairs.append({"to": part.strip(), "kind": "related", "valence": ""})
    return pairs


def _parse_csv(text: str) -> list[str]:
    """Parse comma-separated string into list of stripped strings."""
    if not text or not text.strip():
        return []
    return [s.strip() for s in text.split(",") if s.strip()]


def _extract_ref_ids(page: dict) -> set[str]:
    """Extract all entity IDs referenced by a page's fields."""
    refs: set[str] = set()
    for rel in page.get("relationships", []):
        if isinstance(rel, dict) and rel.get("to"):
            refs.add(rel["to"])
    for field in ("participants", "members", "affected_locations", "references"):
        for item in page.get(field, []):
            if isinstance(item, str) and item:
                refs.add(item)
    faction = page.get("faction", "")
    if faction:
        refs.add(faction)
    return refs


# ============================================================
# Node 1: persist_entity — Pydantic-gated atomic write
# Used inside each create_*.yaml graph-tool pipeline
# ============================================================

_ENTITY_BUILDERS: dict[str, Any] = {}


def _build_character(state: dict) -> dict:
    role = state.get("role", "supporting")
    if role not in _VALID_ROLES:
        raise ValueError(
            f"invalid role '{role}'. Must be: {', '.join(sorted(_VALID_ROLES))}"
        )
    return {
        "type": "character",
        "id": state["id"],
        "lane": "dynamic",
        "depth": 0,
        "name": state.get("name", ""),
        "role": role,
        "faction": state.get("faction", ""),
        "personality": state.get("summary", ""),
        "relationships": _parse_id_role_pairs(state.get("related_to", "")),
    }


def _build_event(state: dict) -> dict:
    scope = state.get("scope", "world")
    if scope not in _VALID_SCOPES:
        raise ValueError(
            f"invalid scope '{scope}'. Must be: {', '.join(sorted(_VALID_SCOPES))}"
        )
    return {
        "type": "event",
        "id": state["id"],
        "lane": "dynamic",
        "depth": 0,
        "year": int(state.get("year", 0)),
        "scope": scope,
        "participants": _parse_csv(state.get("participants", "")),
        "consequences": _parse_csv(state.get("consequences", "")),
        "affected_locations": _parse_csv(state.get("affected_locations", "")),
        "window": state.get("summary", ""),
    }


def _build_faction(state: dict) -> dict:
    return {
        "type": "faction",
        "id": state["id"],
        "lane": "dynamic",
        "depth": 0,
        "name": state.get("name", ""),
        "description": state.get("description", ""),
        "members": _parse_csv(state.get("members", "")),
    }


def _build_location(state: dict) -> dict:
    return {
        "type": "location",
        "id": state["id"],
        "lane": "dynamic",
        "depth": 0,
        "name": state.get("name", ""),
        "description": state.get("description", ""),
        "location_type": state.get("location_type", ""),
    }


def _build_rule(state: dict) -> dict:
    domain = state.get("domain", "social_rule")
    if domain not in _VALID_RULE_DOMAINS:
        raise ValueError(
            f"invalid domain '{domain}'. Must be: {', '.join(sorted(_VALID_RULE_DOMAINS))}"
        )
    return {
        "type": "rule",
        "id": state["id"],
        "lane": "dynamic",
        "depth": 0,
        "domain": domain,
        "title": state.get("title", ""),
        "description": state.get("description", ""),
    }


def _build_premise(state: dict) -> dict:
    return {
        "type": "premise",
        "id": state.get("id", "premise"),
        "lane": "static",
        "depth": 0,
        "text": state.get("text", ""),
        "genre_tags": _parse_csv(state.get("genre_tags", "")),
        "era": state.get("era", ""),
        "themes": _parse_csv(state.get("themes", "")),
        "calendar_note": state.get("calendar_note", ""),
    }


_ENTITY_BUILDERS = {
    "character": _build_character,
    "event": _build_event,
    "faction": _build_faction,
    "location": _build_location,
    "rule": _build_rule,
    "premise": _build_premise,
}


_ENTITY_USAGE: dict[str, str] = {
    "character": "Required: id, name. Optional: role (protagonist/antagonist/supporting/minor), faction, summary, related_to (comma-sep id:role pairs).",
    "event": "Required: id. Optional: year (int, negative=before flood), scope (world/regional/local), participants, consequences, summary.",
    "faction": "Required: id. Optional: name, description, members (comma-sep IDs).",
    "location": "Required: id. Optional: name, description, location_type.",
    "rule": "Required: id. Optional: domain (magic_system/character_state/physical_constraint/social_rule/temporal_rule), title, description.",
    "premise": "Optional: id (default='premise'), text, genre_tags (comma-sep), era, themes (comma-sep), calendar_note.",
}


def persist_entity(state: dict[str, Any]) -> dict[str, Any]:
    """Graph-tool node 1: build page from state, Pydantic-validate, write.

    Reads entity_type from state (set by graph variables).
    On Pydantic failure: returns error in result with usage, nothing written.
    On success: writes to canon, stores page dict for prefetch.
    """
    entity_type = state.get("entity_type", "")
    builder = _ENTITY_BUILDERS.get(entity_type)
    if not builder:
        valid = ", ".join(sorted(_ENTITY_BUILDERS.keys()))
        return {
            "result": f"Error: unknown entity_type '{entity_type}'. Valid types: {valid}",
            "persisted_page": {},
        }

    try:
        page = builder(state)
    except (ValueError, KeyError) as e:
        usage = _ENTITY_USAGE.get(entity_type, "")
        return {
            "result": f"Error building {entity_type}: {e}. Usage: {usage}",
            "persisted_page": {},
        }

    path = _write_page(page, _canon_path())
    if path.startswith("Error:"):
        return {"result": path, "persisted_page": {}}

    return {
        "result": f"Created {entity_type} {page['id']}",
        "persisted_page": page,
    }


# ============================================================
# Node 2: build_check_context — digest + ref prefetch
# Used inside each create_*.yaml graph-tool pipeline
# ============================================================


def build_check_context(state: dict[str, Any]) -> dict[str, Any]:
    """Graph-tool node 2: build canon digest + ref prefetch for LLM check.

    If persist_entity failed (result starts with Error), skip — no check.
    Otherwise: build a 1-line-per-entity digest of the full canon,
    plus full YAML of exactly the entities the new page references.
    """
    result = state.get("result", "")
    if result.startswith("Error:"):
        return {"digest": "", "ref_context": "", "check_skip": True}

    page = state.get("persisted_page", {})
    if not page:
        return {"digest": "", "ref_context": "", "check_skip": True}

    from canon_tools import _load_canon

    canon = _load_canon()

    # Digest: 1 line per entity
    digest_lines = []
    for pid, p in sorted(canon.items()):
        ptype = p.get("type", "?")
        pname = p.get("name", p.get("title", p.get("id", "?")))
        summary = p.get(
            "personality", p.get("description", p.get("window", p.get("text", "")))
        )
        short = (summary[:80] + "...") if len(str(summary)) > 80 else summary
        digest_lines.append(f"- {pid} ({ptype}): {pname} — {short}")

    # Ref prefetch: full YAML of referenced entities
    ref_ids = _extract_ref_ids(page)
    ref_yamls = []
    for rid in sorted(ref_ids):
        if rid in canon:
            ref_yamls.append(
                yaml.dump(canon[rid], default_flow_style=False, allow_unicode=True)
            )

    return {
        "digest": "\n".join(digest_lines),
        "ref_context": "\n---\n".join(ref_yamls)
        if ref_yamls
        else "No referenced entities found in canon.",
        "check_skip": False,
    }


# ============================================================
# persist_synopsis — deterministic python node, not agent tool
# ============================================================


def persist_synopsis(state: dict[str, Any]) -> dict[str, Any]:
    """Persist synopsis to canon as a static page. Called between LLM and agent."""
    synopsis_text = state.get("synopsis", "")
    if not synopsis_text:
        return {}
    page = {
        "type": "synopsis",
        "id": "synopsis",
        "lane": "static",
        "depth": 0,
        "text": synopsis_text,
    }
    _write_page(page, _canon_path())
    return {}


# ============================================================
# final_gate — deterministic terminal gate (AC-10)
# ============================================================


def final_gate(state: dict[str, Any]) -> dict[str, Any]:
    """Deterministic terminal gate: mechanical ref_check on full canon."""
    from canon_tools import _load_canon
    from ref_integrity import validate_referential_integrity

    pages = _load_canon()
    all_pages = list(pages.values())

    if not all_pages:
        return {"gate_result": {"valid": True, "orphan_ids": [], "violations": []}}

    result = validate_referential_integrity(all_pages)
    if not result["valid"]:
        logger.warning(
            "Final gate: %d orphan IDs: %s",
            len(result["orphan_ids"]),
            ", ".join(result["orphan_ids"]),
        )
    else:
        logger.info("Final gate: PASS — canon integrity verified")

    return {"gate_result": result}


def build_audit_digest(state: dict[str, Any]) -> dict[str, Any]:
    """Build full canon digest for ref_check audit LLM node."""
    from canon_tools import _load_canon

    canon = _load_canon()
    digest_lines = []
    for pid, p in sorted(canon.items()):
        ptype = p.get("type", "?")
        pname = p.get("name", p.get("title", p.get("id", "?")))
        summary = p.get(
            "personality", p.get("description", p.get("window", p.get("text", "")))
        )
        short = (str(summary)[:80] + "...") if len(str(summary)) > 80 else summary
        # Include refs for the audit
        refs = []
        for rel in p.get("relationships", []):
            if isinstance(rel, dict) and rel.get("to"):
                refs.append(rel["to"])
        for field in ("participants", "members", "affected_locations", "references"):
            refs.extend(r for r in p.get(field, []) if isinstance(r, str))
        faction = p.get("faction", "")
        if faction:
            refs.append(faction)
        ref_str = f" refs:[{','.join(refs)}]" if refs else ""
        digest_lines.append(f"- {pid} ({ptype}): {pname} — {short}{ref_str}")

    return {"digest": "\n".join(digest_lines)}


# ============================================================
# Standalone python tools (simple lookups, no pipeline)
# ============================================================


def list_thin_entities(canon_dir: str = "") -> str:
    """List entities with depth: 0 that need enrichment."""
    from canon_tools import _load_canon

    pages = _load_canon(canon_dir or None)
    thin = []
    for pid, page in sorted(pages.items()):
        if page.get("depth", 0) == 0 and page.get("type") not in (
            "premise",
            "synopsis",
        ):
            thin.append(f"- {pid} ({page.get('type', '?')})")
    if not thin:
        return "No thin entities found."
    return "\n".join(thin)


def deepen_entity(
    id: str,
    updated_yaml: str,
) -> str:
    """Replace an entity with an enriched version. Increments depth."""
    try:
        page = yaml.safe_load(updated_yaml)
    except yaml.YAMLError as exc:
        return f"Error: invalid YAML: {exc}"

    if not isinstance(page, dict):
        return "Error: updated_yaml must be a YAML mapping"

    page["id"] = id
    page["depth"] = page.get("depth", 0) + 1

    result = _write_page(page, _canon_path())
    if result.startswith("Error:"):
        return result
    return f"Deepened {id} to depth {page['depth']}"
