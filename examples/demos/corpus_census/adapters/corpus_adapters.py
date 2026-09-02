"""Corpus adapters for the FR-892 proof configurations.

PDF library census (AC-08) and git history timeline census (AC-09).
Slot contract, matching the pipeline's python-node convention: functions
take the resolved state dict; discover returns a list of item refs,
extract returns one item's text content.
"""

from __future__ import annotations

import base64
import json
import re
import subprocess
from pathlib import Path
from typing import Any

MAX_ITEMS = 50
MAX_PAGES = 5
MAX_CHARS = 4000


def _require(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


# --- PDF library (AC-08) -------------------------------------------------


def pdf_discover(state: dict[str, Any]) -> list[str]:
    """Enumerate PDF files in the source folder (bounded, sorted)."""
    folder = Path(_require(state, "source"))
    if not folder.is_dir():
        raise NotADirectoryError(f"pdf_discover: not a directory: {folder}")
    pdfs = [str(p) for p in sorted(folder.glob("*.pdf"))][:MAX_ITEMS]
    if not pdfs:
        raise ValueError(f"pdf_discover: no PDFs in {folder}")
    return pdfs


def pdf_extract(state: dict[str, Any]) -> str:
    """Extract text from the first MAX_PAGES pages of one PDF."""
    from pypdf import PdfReader

    item = _require(state, "item")
    reader = PdfReader(item)
    text = "\n".join(
        (page.extract_text() or "") for page in reader.pages[:MAX_PAGES]
    ).strip()[:MAX_CHARS]
    if not text:
        raise ValueError(f"pdf_extract: no extractable text in {item}")
    return text


# --- Git history timeline (AC-09) ----------------------------------------


def _git(repo: str, *argv: str) -> str:
    result = subprocess.run(  # noqa: S603 — fixed git argv, no shell
        ["git", "-C", repo, *argv],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return result.stdout


def git_discover(state: dict[str, Any]) -> list[str]:
    """Enumerate a bounded commit window. source format: '<repo>:<n>'."""
    source = _require(state, "source")
    repo, _, n = source.partition(":")
    window = min(int(n or "10"), MAX_ITEMS)
    shas = _git(repo, "log", f"-{window}", "--format=%H").split()
    if not shas:
        raise ValueError(f"git_discover: no commits in {repo}")
    # Item ref carries the repo so extract stays stateless: '<repo>@<sha>'
    return [f"{repo}@{sha}" for sha in shas]


def git_extract(state: dict[str, Any]) -> str:
    """One commit's subject, body, and diffstat."""
    item = _require(state, "item")
    repo, _, sha = item.partition("@")
    text = _git(repo, "show", "-s", "--format=%s%n%n%b", sha)
    stat = _git(repo, "show", "--stat", "--format=", sha)
    return (text + "\n" + stat).strip()[:MAX_CHARS]


# --- GitHub org repo census (FR-899) --------------------------------------

MAX_REPOS = 100
MAX_README_CHARS = 3000
MAX_PERSONS = 5
GH_TIMEOUT = 60


def _gh(*argv: str) -> str:
    result = subprocess.run(  # noqa: S603 — fixed gh argv, no shell
        ["gh", *argv],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=GH_TIMEOUT,
        check=True,
    )
    return result.stdout


def _parse_org_source(source: str) -> tuple[str, int]:
    org, sep, raw_limit = source.strip().partition(":")
    if not org:
        raise ValueError(f"gh_org_discover: malformed source: {source!r}")
    limit = MAX_REPOS
    if sep:
        if not raw_limit.isdigit() or int(raw_limit) < 1:
            raise ValueError(f"gh_org_discover: malformed limit: {source!r}")
        limit = min(int(raw_limit), MAX_REPOS)
    return org, limit


def gh_org_discover(state: dict[str, Any]) -> list[str]:
    """Enumerate an organization's repositories. source: '<org>[:<n>]'."""
    org, limit = _parse_org_source(_require(state, "source"))
    listing = json.loads(
        _gh("repo", "list", org, "--limit", str(limit), "--json", "name")
    )
    if not listing:
        raise ValueError(f"gh_org_discover: no repositories for org {org}")
    return [f"{org}/{entry['name']}" for entry in listing]


def gh_repo_extract(state: dict[str, Any]) -> str:
    """Bounded per-repo evidence bundle for one '<org>/<name>' item ref."""
    item = _require(state, "item")
    if item.count("/") != 1 or not all(item.split("/")):
        raise ValueError(f"gh_repo_extract: malformed item ref: {item!r}")

    meta = json.loads(_gh("api", f"repos/{item}"))
    try:
        readme_payload = json.loads(_gh("api", f"repos/{item}/readme"))
        readme_head = base64.b64decode(readme_payload.get("content", "")).decode(
            "utf-8", errors="replace"
        )[:MAX_README_CHARS]
    except subprocess.CalledProcessError:
        readme_head = "readme: none"
    contributors = json.loads(
        _gh("api", f"repos/{item}/contributors?per_page={MAX_PERSONS}")
    )

    bundle = {
        "name": item,
        "description": meta.get("description"),
        "pushed_at": meta.get("pushed_at"),
        "archived": meta.get("archived"),
        "language": meta.get("language"),
        "readme_head": readme_head,
        "contributors": [c["login"] for c in contributors[:MAX_PERSONS]],
    }
    blob = json.dumps(bundle)
    if len(blob) > MAX_CHARS:
        overshoot = len(blob) - MAX_CHARS
        bundle["readme_head"] = readme_head[: max(0, len(readme_head) - overshoot)]
        blob = json.dumps(bundle)
    return blob


# --- Authored-PR person profile (FR-962) ---------------------------------

MAX_PRS = 500
MAX_BODY_CHARS = 3000
MAX_LABELS = 10
_VALID_VISIBILITY = {"public", "private", "internal"}
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SHA40 = re.compile(r"^[0-9a-f]{40}$")


def _parse_pr_source(source: str) -> tuple[str, str, str]:
    """Parse '<author>@<owner>:<since>' with ISO YYYY-MM-DD `since` (R-2)."""
    author, sep_at, rest = source.strip().partition("@")
    if not sep_at or not author:
        raise ValueError(
            f"gh_authored_prs_discover: malformed source: {source!r} "
            "(expected '<author>@<owner>:<since>')"
        )
    owner, sep_colon, since = rest.partition(":")
    if not sep_colon or not owner or not since:
        raise ValueError(
            f"gh_authored_prs_discover: malformed source: {source!r} "
            "(expected '<author>@<owner>:<since>')"
        )
    if not _ISO_DATE.match(since):
        raise ValueError(
            f"gh_authored_prs_discover: `since` must be ISO YYYY-MM-DD, "
            f"got {since!r}"
        )
    return author, owner, since


def _parse_visibility(state: dict[str, Any]) -> list[str]:
    """Parse required `visibility` state var (R-5): JSON list from the enum."""
    raw = state.get("visibility")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"gh_authored_prs_discover: `visibility` must be JSON list, "
                f"got {raw!r}"
            ) from exc
    if not isinstance(raw, list) or not raw:
        raise ValueError(
            "gh_authored_prs_discover: `visibility` must be a non-empty list "
            f"from {sorted(_VALID_VISIBILITY)}"
        )
    seen: set[str] = set()
    canonical: list[str] = []
    for entry in raw:
        if not isinstance(entry, str):
            raise ValueError(
                f"gh_authored_prs_discover: visibility entry must be str, "
                f"got {entry!r}"
            )
        key = entry.casefold()
        if key not in _VALID_VISIBILITY:
            raise ValueError(
                f"gh_authored_prs_discover: unknown visibility {entry!r}; "
                f"allowed: {sorted(_VALID_VISIBILITY)}"
            )
        if key in seen:
            raise ValueError(
                f"gh_authored_prs_discover: duplicate visibility {entry!r}"
            )
        seen.add(key)
        canonical.append(key)
    return canonical


def gh_authored_prs_discover(state: dict[str, Any]) -> list[str]:
    """Enumerate PRs authored by <author> in <owner> since <since>.

    source: '<author>@<owner>:<since>' — e.g. 'sheikkinen@sheikkinen:2026-06-01'
    visibility: JSON list from {"public","private","internal"} (required, R-5)
    Overflow-detecting (R-1): queries MAX_PRS+1 and rejects on 501.
    Returns sorted, deduplicated list of item refs '<owner>/<repo>#<number>'.
    """
    author, owner, since = _parse_pr_source(_require(state, "source"))
    visibility = _parse_visibility(state)
    argv: list[str] = [
        "search",
        "prs",
        "--author",
        author,
        "--owner",
        owner,
        "--created",
        f">={since}",
        "--limit",
        str(MAX_PRS + 1),
        "--json",
        "repository,number",
    ]
    for vis in visibility:
        argv.extend(["--visibility", vis])
    listing = json.loads(_gh(*argv))
    if not listing:
        raise ValueError(
            f"gh_authored_prs_discover: no PRs for "
            f"author={author!r} owner={owner!r} since={since!r} "
            f"visibility={visibility}"
        )
    if len(listing) > MAX_PRS:
        raise ValueError(
            f"gh_authored_prs_discover: population exceeded MAX_PRS={MAX_PRS} "
            f"(got {len(listing)}); narrow `since` or split the query"
        )
    refs_set: set[str] = set()
    for entry in listing:
        ref = f"{entry['repository']['nameWithOwner']}#{entry['number']}"
        if ref in refs_set:
            raise ValueError(f"gh_authored_prs_discover: duplicate item ref {ref!r}")
        refs_set.add(ref)
    return sorted(refs_set)


def _parse_pr_item(item: str) -> tuple[str, str, int]:
    """Parse '<owner>/<repo>#<positive-number>' into (owner, repo, number)."""
    nwo, sep, raw_number = item.partition("#")
    if not sep or not raw_number.isdigit():
        raise ValueError(f"gh_pr_extract: malformed item ref: {item!r}")
    number = int(raw_number)
    if number <= 0:
        raise ValueError(f"gh_pr_extract: non-positive PR number: {item!r}")
    owner, sep2, repo = nwo.partition("/")
    if not sep2 or not owner or not repo:
        raise ValueError(f"gh_pr_extract: malformed item ref: {item!r}")
    return owner, repo, number


def gh_pr_extract(state: dict[str, Any]) -> str:
    """Bounded per-PR evidence bundle for one '<owner>/<repo>#<number>' ref."""
    item = _require(state, "item")
    owner, repo, number = _parse_pr_item(item)

    meta = json.loads(_gh("api", f"repos/{owner}/{repo}/pulls/{number}"))
    body_head = (meta.get("body") or "")[:MAX_BODY_CHARS]
    merged_at = meta.get("merged_at")
    api_state = (meta.get("state") or "").lower()
    if merged_at:
        state_value = "merged"
    elif api_state in {"open", "closed"}:
        state_value = api_state
    else:
        raise ValueError(
            f"gh_pr_extract: unexpected API state for {item!r}: "
            f"{meta.get('state')!r}"
        )
    labels = [lbl["name"] for lbl in (meta.get("labels") or [])[:MAX_LABELS]]
    base_sha = (meta.get("base") or {}).get("sha") or ""
    head_sha = (meta.get("head") or {}).get("sha") or ""
    if not _SHA40.match(base_sha) or not _SHA40.match(head_sha):
        raise ValueError(f"gh_pr_extract: malformed base/head SHA for {item!r}")
    additions = meta.get("additions") or 0
    deletions = meta.get("deletions") or 0
    changed_files = meta.get("changed_files") or 0
    for name, value in (
        ("additions", additions),
        ("deletions", deletions),
        ("changed_files", changed_files),
    ):
        if not isinstance(value, int) or value < 0:
            raise ValueError(
                f"gh_pr_extract: {name} must be non-negative int for "
                f"{item!r}, got {value!r}"
            )

    bundle = {
        "repo": f"{owner}/{repo}",
        "number": number,
        "url": f"https://github.com/{owner}/{repo}/pull/{number}",
        "title": meta.get("title") or "",
        "state": state_value,
        "created_at": meta.get("created_at"),
        "merged_at": merged_at,
        "labels": labels,
        "body_head": body_head,
        "additions": additions,
        "deletions": deletions,
        "changed_files": changed_files,
        "base_sha": base_sha,
        "head_sha": head_sha,
    }
    blob = json.dumps(bundle)
    if len(blob) > MAX_CHARS:
        overshoot = len(blob) - MAX_CHARS
        truncated = body_head[: max(0, len(body_head) - overshoot)]
        bundle["body_head"] = truncated
        blob = json.dumps(bundle)
    return blob
