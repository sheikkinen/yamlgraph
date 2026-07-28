"""Fail-fast gate between the map and the sink (FR-764 R-3 / C-4).

The ``convert_styles`` map returns exactly one collected entry per input
prompt. A branch that raises is collected as an ``_error`` marker dict rather
than a converted ``prompt_text``. Left unchecked, the reused ``save_prompts``
sink stringifies that marker into the output file — a partial, misleading
result that violates the judged "N in == N out or nothing written" contract.

This node enforces that contract at the output boundary (no core map change):
if any collected entry failed, or the collected count does not match the
source count, it raises so the run aborts *before* ``save_prompts`` writes.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def validate_conversions_node(state: dict) -> dict:
    """Raise unless every source prompt produced a converted ``prompt_text``.

    Args:
        state: Graph state with ``source_prompts`` (loader output) and
            ``prompts`` (map collect target).

    Returns:
        Empty dict — validation is side-effect free on success.

    Raises:
        ValueError: If any branch failed or the collected count is wrong. The
            run aborts here, so no partial prompt file is ever written.
    """
    source = state.get("source_prompts") or []
    prompts = state.get("prompts") or []

    failed = [
        entry for entry in prompts if isinstance(entry, dict) and "_error" in entry
    ]
    if failed:
        indices = [entry.get("_map_index", "?") for entry in failed]
        raise ValueError(
            f"{len(failed)} of {len(source)} style conversions failed "
            f"(branch indices {indices}); aborting before save so no partial "
            f"prompt file is written. First error: {failed[0].get('_error')!r}"
        )

    if len(prompts) != len(source):
        raise ValueError(
            f"Converted prompt count {len(prompts)} does not match source "
            f"count {len(source)}; refusing to write a mismatched output file."
        )

    logger.info("✓ All %d style conversions succeeded", len(prompts))
    return {}
