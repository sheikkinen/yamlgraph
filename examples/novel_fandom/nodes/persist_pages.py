"""Persist deepened + skeleton pages to canon/ with Pydantic validation.

Validates each page against canon.py models before writing.
Uses atomic writes (tempfile + os.replace). Skeletons don't overwrite.
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

    try:
        model_cls(**page)
    except Exception as e:  # noqa: BLE001
        logger.warning("Validation failed for '%s': %s", page.get("id"), e)
        return None

    target = canon_dir / f"{page['id']}.yaml"
    if not overwrite and target.exists():
        return None

    fd, tmp_path = tempfile.mkstemp(dir=canon_dir, suffix=".tmp", prefix=".persist_")
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
        target = canon_dir / f"{page['id']}.yaml"
        if target.exists():
            continue
        fd, tmp_path = tempfile.mkstemp(
            dir=canon_dir, suffix=".tmp", prefix=".persist_"
        )
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
