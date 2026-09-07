"""FR-1027 preflight — bound as the `preflight` slot, first node in every mode.

Loaded by PATH from a slot manifest (no package context), so this module is
self-contained: stdlib + inline ceilings mirrored from models.py (asserted
equal by tests). Fails BEFORE any GitHub/Jira fetch or LLM call.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

# Mirrors of models.py ceilings (path-loaded module cannot import the package).
MAX_REPOS = 400
MAX_PROJECTS = 150
MAX_TOP_PERSONS = 60
MAX_SYNTHESIS_CALLS = 2
N_CANARIES = 5
MAX_LLM_CALLS = (
    MAX_REPOS + MAX_PROJECTS + MAX_TOP_PERSONS + MAX_SYNTHESIS_CALLS + N_CANARIES
)

AZURE_VARS = ("AZURE_AI_ENDPOINT", "AZURE_AI_API_KEY", "AZURE_MODEL")
JIRA_VARS = ("JIRA_URL", "JIRA_USERNAME", "JIRA_API_TOKEN")
VALID_VISIBILITY = frozenset({"public", "private", "internal"})
REPO_ROOT = Path(__file__).resolve().parents[3]
LIVE_ROOT = REPO_ROOT / "research" / "org-ai-dossier"
SMOKE_ROOT = REPO_ROOT / "tmp" / "org-ai-dossier-smoke"
PUBLIC_DEMO_OWNER = "sheikkinen"


def _gh_auth_ok() -> None:
    try:
        subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["gh", "auth", "status"],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise RuntimeError(f"gh auth status failed: {exc}") from exc


def _git_ignored(path: Path) -> bool:
    rel = os.path.relpath(path, REPO_ROOT)
    result = subprocess.run(  # noqa: S603 — fixed argv, no shell
        ["git", "check-ignore", "-q", rel],  # noqa: S607
        cwd=REPO_ROOT,
        capture_output=True,
        timeout=10,
    )
    return result.returncode == 0


def estimate_llm_calls(n_repos: int, n_projects: int, top_persons: int) -> int:
    if (
        n_repos > MAX_REPOS
        or n_projects > MAX_PROJECTS
        or top_persons > MAX_TOP_PERSONS
    ):
        raise ValueError(
            f"estimate exceeds MAX_LLM_CALLS ceilings ({n_repos}, {n_projects}, {top_persons})"
        )
    estimate = n_repos + n_projects + top_persons + MAX_SYNTHESIS_CALLS + N_CANARIES
    if estimate > MAX_LLM_CALLS:
        raise ValueError(f"estimate {estimate} exceeds MAX_LLM_CALLS={MAX_LLM_CALLS}")
    return estimate


def _require_env(names: tuple[str, ...]) -> None:
    missing = [v for v in names if not os.environ.get(v, "").strip()]
    if missing:
        raise OSError(f"preflight: missing env {', '.join(missing)}")


def _visibility(state: dict[str, Any], allowed: frozenset[str]) -> list[str]:
    raw = str(state.get("visibility", "")).strip()
    values = [v.strip().lower() for v in raw.split(",") if v.strip()]
    if not values or not set(values) <= allowed:
        raise ValueError(
            f"preflight: visibility must be a non-empty subset of {sorted(allowed)}, got {raw!r}"
        )
    return values


def _int(state: dict[str, Any], key: str, lo: int, hi: int) -> int:
    raw = str(state.get(key, "")).strip()
    if not raw.isdigit() or not lo <= int(raw) <= hi:
        raise ValueError(
            f"preflight: {key} must be an integer in [{lo}, {hi}], got {raw!r}"
        )
    return int(raw)


def _persons_policy(state: dict[str, Any], *, allow_true: bool) -> bool:
    raw = str(state.get("persons_llm", "")).strip().lower()
    if raw not in ("true", "false"):
        raise ValueError(
            f"preflight: persons_llm is required and must be 'true' or 'false', got {raw!r}"
        )
    if raw == "true":
        if not allow_true:
            raise ValueError(
                "preflight: persons_llm=true is not permitted in smoke mode"
            )
        if not str(state.get("persons_llm_ack", "")).strip():
            raise ValueError(
                "preflight: persons_llm=true requires a non-empty persons_llm_ack"
            )
    return raw == "true"


def _out_dir(state: dict[str, Any], root: Path, *, require_ignored: bool) -> Path:
    raw = str(state.get("out_dir", "")).strip()
    if not raw:
        raise ValueError("preflight: out_dir is required")
    out = Path(raw)
    if not out.is_absolute():
        out = REPO_ROOT / out
    resolved = out.resolve(strict=False)
    root_resolved = root.resolve(strict=False)
    if resolved == root_resolved or root_resolved not in resolved.parents:
        raise ValueError(
            f"preflight: out_dir must be strictly beneath {root} (resolved {resolved})"
        )
    if resolved.exists():
        raise ValueError(f"preflight: out_dir already exists: {resolved}")
    if require_ignored:
        root.mkdir(parents=True, exist_ok=True)
        if not _git_ignored(root):
            raise ValueError(f"preflight: {root} is not covered by .gitignore")
    return resolved


def _common(state: dict[str, Any]) -> None:
    _require_env(AZURE_VARS)
    _gh_auth_ok()
    _int(state, "window_days", 1, 3650)
    estimate_llm_calls(
        MAX_REPOS, MAX_PROJECTS, _int(state, "top_persons", 1, MAX_TOP_PERSONS)
    )


def preflight(state: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Live preflight — every check, before any fetch."""
    state = state or kwargs
    _common(state)
    _visibility(state, VALID_VISIBILITY)
    _require_env(JIRA_VARS)
    _persons_policy(state, allow_true=True)
    _out_dir(state, LIVE_ROOT, require_ignored=True)
    return {"preflight_ok": True}


def preflight_smoke(
    state: dict[str, Any] | None = None, **kwargs: Any
) -> dict[str, Any]:
    """Smoke preflight — public visibility, no Jira env, persons_llm=false, tmp root."""
    state = state or kwargs
    _common(state)
    if _visibility(state, VALID_VISIBILITY) != ["public"]:
        raise ValueError("preflight(smoke): visibility must be exactly 'public'")
    _persons_policy(state, allow_true=False)
    _out_dir(state, SMOKE_ROOT, require_ignored=False)
    return {"preflight_ok": True}
