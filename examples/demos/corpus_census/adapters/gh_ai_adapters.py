"""FR-1029 GitHub AI-signal adapters (FR-892 slot contract).

- `gh_org_active_discover`: visibility-policy + archived + window filter,
  sorted unique ids, `OverflowError` at MAX_REPOS+1 (before any LLM spend).
- `gh_repo_ai_extract`: typed bounded evidence bundle with deterministic
  AI-signal probes (instruction files, manifest/workflow hits, PR authors).
- `gh_org_code_search`: org-wide code search per frozen keyword, rate-budgeted,
  cap-flagged; the reducer reconciles hits against frozen active ids.

Every `gh` invocation is fixed argv via subprocess, no shell.
"""

from __future__ import annotations

import base64
import fnmatch
import json
import subprocess
import time
from datetime import UTC, datetime, timedelta
from typing import Any

GH_TIMEOUT = 60
MAX_LISTED = 1000  # one cheap listing call; overflow at MAX_LISTED+1 aborts
MAX_REPOS = 400  # ACTIVE repos after filtering — the LLM-spend ceiling
MAX_README_CHARS = 3000
MAX_CONTRIBUTORS = 10
MAX_MANIFESTS = 6
MAX_WORKFLOWS = 5
MAX_PRS = 30
MAX_HIT_LINE_CHARS = 160
MAX_MANIFEST_HITS = 60
MAX_WORKFLOW_HITS = 30
MAX_BUNDLE_CHARS = 6000
MAX_SEARCH_TERMS = 12
MAX_SEARCH_RESULTS = 100
SEARCH_MIN_INTERVAL_S = 7.0  # ≤10 code-search calls per minute, with margin

VALID_VISIBILITY = frozenset({"public", "private", "internal"})
INSTRUCTION_PATHS = (
    ".github/copilot-instructions.md",
    "CLAUDE.md",
    "AGENTS.md",
    ".cursorrules",
    ".cursor/",
    ".claude/",
    ".github/skills/",
    ".github/agents/",
)
MANIFEST_PATTERNS = (
    "package.json",
    "requirements*.txt",
    "pyproject.toml",
    "*.csproj",
    "Directory.Packages.props",
    "go.mod",
    "composer.json",
)
AI_PACKAGE_TERMS = (
    "openai",
    "@azure/openai",
    "Azure.AI.",
    "anthropic",
    "@anthropic-ai/",
    "langchain",
    "langgraph",
    "llama-index",
    "llama_index",
    "semantic-kernel",
    "Microsoft.SemanticKernel",
    '"ai"',
    "transformers",
    "ollama",
    "mistralai",
    "google-generativeai",
    "cohere",
)
WORKFLOW_TERMS = ("copilot", "openai", "claude", "ai-inference")
BOT_MARKERS = (
    "[bot]",
    "copilot",
    "dependabot",
    "renovate",
    "actions-user",
    "github-actions",
)
SEARCH_TERMS = (
    "openai",
    "anthropic",
    "langchain",
    "Azure.AI",
    "semantic-kernel",
    "copilot-instructions",
    "CLAUDE.md",
    "AGENTS.md",
    "tekoäly",
    "kielimalli",
    "tekoälyavustaja",
)
assert len(SEARCH_TERMS) <= MAX_SEARCH_TERMS


# Seams for tests (clock + sleep); never patched in production.
def _now() -> datetime:
    return datetime.now(UTC)


_monotonic = time.monotonic
_sleep = time.sleep


def _gh(*argv: str) -> str:
    result = subprocess.run(  # noqa: S603 — fixed gh argv, no shell
        ["gh", *argv],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=GH_TIMEOUT,
        check=True,
    )
    return result.stdout


def _gh_json(*argv: str) -> Any:
    raw = _gh(*argv)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"gh returned non-JSON for {argv[-1]!r}: {exc.msg}") from exc


def _require(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value.strip()


def _parse_iso(raw: Any, field: str) -> datetime:
    if not isinstance(raw, str):
        raise ValueError(f"{field}: expected ISO timestamp, got {raw!r}")
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field}: malformed timestamp {raw!r}") from exc


def _parse_window(raw: str, label: str) -> int:
    if not raw.isdigit() or int(raw) < 1:
        raise ValueError(
            f"{label}: window_days must be a positive integer, got {raw!r}"
        )
    return int(raw)


def _parse_source(source: str) -> tuple[str, int]:
    org, sep, raw_days = source.strip().partition(":")
    if not org or not sep:
        raise ValueError(
            f"gh_org_active_discover: source must be <org>:<window_days>: {source!r}"
        )
    return org, _parse_window(raw_days, "gh_org_active_discover")


def _org_and_window(state: dict[str, Any]) -> tuple[str, int]:
    """`source` = '<org>:<days>', or the separate `org` + `window_days` keys
    (yamlgraph templates resolve one placeholder per string)."""
    source = state.get("source")
    if isinstance(source, str) and source.strip():
        return _parse_source(source)
    if state.get("org") is None and source is not None:
        raise ValueError("source is required")
    return _require(state, "org"), _parse_window(
        str(state.get("window_days", "")), "gh_org_active_discover"
    )


def _parse_visibility(state: dict[str, Any]) -> frozenset[str]:
    raw = _require(state, "visibility")
    values = frozenset(v.strip().lower() for v in raw.split(",") if v.strip())
    if not values or not values <= VALID_VISIBILITY:
        raise ValueError(
            f"visibility policy must be a subset of {sorted(VALID_VISIBILITY)}: {raw!r}"
        )
    return values


# --- discover (AC-05) -------------------------------------------------------


def gh_org_active_discover(state: dict[str, Any]) -> list[str]:
    """Active, policy-visible, non-archived repos of <org> within the window."""
    org, window_days = _org_and_window(state)
    allowed = _parse_visibility(state)
    listing = _gh_json(
        "repo",
        "list",
        org,
        "--limit",
        str(MAX_LISTED + 1),
        "--json",
        "name,pushedAt,isArchived,visibility",
    )
    if not isinstance(listing, list):
        raise ValueError("gh_org_active_discover: listing is not a list")
    if len(listing) > MAX_LISTED:
        raise OverflowError(
            f"gh_org_active_discover: org {org} lists more than MAX_LISTED={MAX_LISTED} repos"
        )
    cutoff = _now() - timedelta(days=window_days)
    seen: set[str] = set()
    active: list[str] = []
    for entry in listing:
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError(f"gh_org_active_discover: entry without name: {entry!r}")
        if name in seen:
            raise ValueError(f"gh_org_active_discover: duplicate repo {name!r}")
        seen.add(name)
        if str(entry.get("visibility", "")).lower() not in allowed:
            continue
        if entry.get("isArchived"):
            continue
        if _parse_iso(entry.get("pushedAt"), f"{name}.pushedAt") < cutoff:
            continue
        active.append(f"{org}/{name}")
    if len(active) > MAX_REPOS:
        raise OverflowError(
            f"gh_org_active_discover: {len(active)} active repos exceed MAX_REPOS={MAX_REPOS}"
        )
    return sorted(active)


# --- extract (AC-06) --------------------------------------------------------


def _optional(bundle: dict[str, Any], label: str, *argv: str) -> Any | None:
    try:
        return _gh_json(*argv)
    except subprocess.CalledProcessError:
        bundle["absent"].append(label)
        return None


def _decode_content(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    return base64.b64decode(payload.get("content", "")).decode(
        "utf-8", errors="replace"
    )


def _grep_hits(path: str, text: str, terms: tuple[str, ...]) -> list[dict[str, str]]:
    hits = []
    for line in text.splitlines():
        if any(term.lower() in line.lower() for term in terms):
            hits.append({"path": path, "line": line.strip()[:MAX_HIT_LINE_CHARS]})
    return hits


def _tree_paths(tree: Any) -> tuple[list[str], bool]:
    if not isinstance(tree, dict):
        return [], False
    paths = [e.get("path", "") for e in tree.get("tree", []) if isinstance(e, dict)]
    return [p for p in paths if p], bool(tree.get("truncated"))


def _instruction_files(paths: list[str]) -> list[str]:
    found = []
    for marker in INSTRUCTION_PATHS:
        if marker.endswith("/"):
            if any(p.startswith(marker) for p in paths):
                found.append(marker)
        elif marker in paths:
            found.append(marker)
    return found


def _select(paths: list[str], predicate, cap: int) -> list[str]:
    return [p for p in paths if predicate(p)][:cap]


def _is_manifest(path: str) -> bool:
    base = path.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatch(base, pat) for pat in MANIFEST_PATTERNS)


def _is_workflow(path: str) -> bool:
    return path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml"))


def _pr_authors(pulls: Any, cutoff: datetime) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for pr in pulls if isinstance(pulls, list) else []:
        login = (pr.get("user") or {}).get("login")
        if not login or _parse_iso(pr.get("updated_at"), "pull.updated_at") < cutoff:
            continue
        counts[login] = counts.get(login, 0) + 1
    return [
        {"login": login, "bot": any(m in login.lower() for m in BOT_MARKERS), "n": n}
        for login, n in sorted(counts.items())
    ]


def _trim_to_cap(bundle: dict[str, Any]) -> str:
    blob = json.dumps(bundle, ensure_ascii=False)
    while len(blob) > MAX_BUNDLE_CHARS:
        if bundle["readme_head"]:
            bundle["readme_head"] = bundle["readme_head"][
                : len(bundle["readme_head"]) // 2
            ]
        elif bundle["manifest_hits"]:
            bundle["manifest_hits"].pop()
        elif bundle["workflow_hits"]:
            bundle["workflow_hits"].pop()
        else:
            raise ValueError("gh_repo_ai_extract: bundle cannot be trimmed under cap")
        blob = json.dumps(bundle, ensure_ascii=False)
    return blob


def gh_repo_ai_extract(state: dict[str, Any]) -> str:
    """Typed, bounded evidence bundle for one '<org>/<name>' repository."""
    item = _require(state, "item")
    if item.count("/") != 1 or not all(item.split("/")):
        raise ValueError(f"gh_repo_ai_extract: malformed item ref: {item!r}")
    window_days = _parse_window(str(state.get("window_days", "")), "gh_repo_ai_extract")
    cutoff = _now() - timedelta(days=window_days)

    meta = _gh_json("api", f"repos/{item}")
    if not isinstance(meta, dict):
        raise ValueError(f"gh_repo_ai_extract: metadata is not an object for {item}")
    bundle: dict[str, Any] = {
        "id": item,
        "description": meta.get("description"),
        "pushed_at": meta.get("pushed_at"),
        "archived": bool(meta.get("archived")),
        "visibility": str(meta.get("visibility", "")).lower(),
        "language": meta.get("language"),
        "readme_head": "",
        "contributors": [],
        "tree_truncated": False,
        "instruction_files": [],
        "manifest_hits": [],
        "workflow_hits": [],
        "pr_authors": [],
        "absent": [],
    }
    readme = _optional(bundle, "readme", "api", f"repos/{item}/readme")
    bundle["readme_head"] = _decode_content(readme)[:MAX_README_CHARS]
    contributors = _optional(
        bundle,
        "contributors",
        "api",
        f"repos/{item}/contributors?per_page={MAX_CONTRIBUTORS}",
    )
    bundle["contributors"] = [
        c["login"]
        for c in (contributors or [])
        if isinstance(c, dict) and c.get("login")
    ][:MAX_CONTRIBUTORS]
    tree = _optional(bundle, "tree", "api", f"repos/{item}/git/trees/HEAD?recursive=1")
    paths, truncated = _tree_paths(tree)
    bundle["tree_truncated"] = truncated
    bundle["instruction_files"] = _instruction_files(paths)
    for path in _select(paths, _is_manifest, MAX_MANIFESTS):
        content = _optional(
            bundle, f"contents:{path}", "api", f"repos/{item}/contents/{path}"
        )
        bundle["manifest_hits"].extend(
            _grep_hits(path, _decode_content(content), AI_PACKAGE_TERMS)
        )
    bundle["manifest_hits"] = bundle["manifest_hits"][:MAX_MANIFEST_HITS]
    for path in _select(paths, _is_workflow, MAX_WORKFLOWS):
        content = _optional(
            bundle, f"contents:{path}", "api", f"repos/{item}/contents/{path}"
        )
        bundle["workflow_hits"].extend(
            _grep_hits(path, _decode_content(content), WORKFLOW_TERMS)
        )
    bundle["workflow_hits"] = bundle["workflow_hits"][:MAX_WORKFLOW_HITS]
    pulls = _optional(
        bundle,
        "pulls",
        "api",
        f"repos/{item}/pulls?state=all&per_page={MAX_PRS}&sort=updated&direction=desc",
    )
    bundle["pr_authors"] = _pr_authors(pulls, cutoff)
    return _trim_to_cap(bundle)


# --- org code search (AC-07) -------------------------------------------------


def gh_org_code_search(state: dict[str, Any]) -> dict[str, Any]:
    """One `gh search code` per frozen keyword; ≤10 calls/min; cap flagged.

    Returns ``{"search_hits": {keyword: {repos, capped}}}`` — a python-node dict
    result merges into graph state, so the state key is explicit.
    """
    org = _require(state, "org")
    allowed = _parse_visibility(state)
    hits: dict[str, dict[str, Any]] = {}
    last_call: float | None = None
    for keyword in SEARCH_TERMS:
        if last_call is not None:
            elapsed = _monotonic() - last_call
            if elapsed < SEARCH_MIN_INTERVAL_S:
                _sleep(SEARCH_MIN_INTERVAL_S - elapsed)
        last_call = _monotonic()
        results = _gh_json(
            "search",
            "code",
            keyword,
            "--owner",
            org,
            "--limit",
            str(MAX_SEARCH_RESULTS),
            "--json",
            "repository",
        )
        # search results expose only isPrivate; private/internal both count as non-public
        repos = sorted(
            {
                r["repository"]["nameWithOwner"]
                for r in (results if isinstance(results, list) else [])
                if isinstance(r, dict)
                and r.get("repository", {}).get("nameWithOwner")
                and (
                    ("public" in allowed and not r["repository"].get("isPrivate"))
                    or (
                        ({"private", "internal"} & allowed)
                        and r["repository"].get("isPrivate")
                    )
                )
            }
        )
        n_results = len(results) if isinstance(results, list) else 0
        hits[keyword] = {"repos": repos, "capped": n_results >= MAX_SEARCH_RESULTS}
    return {"search_hits": hits}
