"""FR-1027 graph-facing tools: preflight, GitHub coverage, re-exports.

`preflight` (live) and `preflight_smoke` are bound as the `preflight` slot and
run as the first node in every mode. They fail BEFORE any GitHub/Jira fetch
or LLM call: Azure env, `gh auth status`, visibility policy, Jira env (live),
`persons_llm` policy (+ack), `out_dir` root/locality, ceilings estimate.
"""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime, timedelta
from typing import Any

from examples.demos.corpus_census.adapters import gh_ai_adapters
from examples.demos.org_ai_dossier.canaries import (
    canary_expected_findings,
    inject_jira_canaries,
    inject_repo_canaries,
)
from examples.demos.org_ai_dossier.models import (
    MAX_API_CALLS_GITHUB,
    MAX_API_CALLS_JIRA,
    MAX_PROJECTS,
    MAX_TOP_PERSONS,
)
from examples.demos.org_ai_dossier.preflight import (
    VALID_VISIBILITY,
    _int,
    _visibility,
    estimate_llm_calls,
    preflight,
    preflight_smoke,
)
from examples.demos.org_ai_dossier.reduce import reduce
from examples.demos.org_ai_dossier.render import (
    prepare_findings_input,
    prepare_person_input,
    render_artifacts,
)

__all__ = [
    "canary_expected_findings",
    "coverage_gh",
    "estimate_llm_calls",
    "inject_jira_canaries",
    "inject_repo_canaries",
    "preflight",
    "preflight_smoke",
    "prepare_findings_input",
    "prepare_person_input",
    "reduce",
    "render_artifacts",
]


def coverage_gh(state: dict[str, Any]) -> dict[str, Any]:
    """Org-API total (or None) plus listing counts; the same fixed argv as discover."""
    org = str(state.get("org", "")).strip()
    if not org:
        raise ValueError("coverage_gh: org is required")
    window = _int(state, "window_days", 1, 3650)
    allowed = set(_visibility(state, VALID_VISIBILITY))
    api_total: int | None = None
    try:
        meta = gh_ai_adapters._gh_json("api", f"orgs/{org}")
        if isinstance(meta, dict) and "public_repos" in meta:
            api_total = int(meta.get("public_repos", 0)) + int(
                meta.get("total_private_repos", 0) or 0
            )
    except (subprocess.CalledProcessError, ValueError):
        api_total = None
    listing = gh_ai_adapters._gh_json(
        "repo",
        "list",
        org,
        "--limit",
        str(gh_ai_adapters.MAX_LISTED + 1),
        "--json",
        "name,pushedAt,isArchived,visibility",
    )
    cutoff = datetime.now(UTC) - timedelta(days=window)
    counts = {
        "listed": len(listing),
        "archived": 0,
        "out_of_window": 0,
        "visibility_rejected": 0,
        "active": 0,
    }
    for entry in listing:
        if str(entry.get("visibility", "")).lower() not in allowed:
            counts["visibility_rejected"] += 1
        elif entry.get("isArchived"):
            counts["archived"] += 1
        elif gh_ai_adapters._parse_iso(entry.get("pushedAt"), "pushedAt") < cutoff:
            counts["out_of_window"] += 1
        else:
            counts["active"] += 1
    return {
        "coverage_gh": {"api_total": api_total, **counts},
        "api_calls_estimated": min(MAX_API_CALLS_GITHUB, 2 + counts["active"] * 12)
        + MAX_API_CALLS_JIRA,
        "llm_calls_estimated": estimate_llm_calls(
            counts["active"],
            MAX_PROJECTS,
            _int(state, "top_persons", 1, MAX_TOP_PERSONS),
        ),
        "run_started": datetime.now(UTC).isoformat(),
    }
