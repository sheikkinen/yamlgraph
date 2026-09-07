"""FR-1027 typed LLM-free reducer (judgement R-2/R-3/R-5).

Order is frozen (FR § Frozen topology): repo identities → jira identities →
evidence reconciliation → search merge → persons → AI-tool inventory →
coverage → canaries. Any structural failure raises; nothing is silently
dropped; the caller's `on_error: fail` guarantees no artifact is written.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import Any

from pydantic import ValidationError

from examples.demos.org_ai_dossier import canaries
from examples.demos.org_ai_dossier.models import (
    CANARY_PREFIX,
    MAX_MAP_FAILED,
    MAX_TOP_PERSONS,
    AIToolRow,
    CoverageGitHub,
    CoverageJira,
    GitHubBundle,
    JiraAIRow,
    JiraBundle,
    JiraClassification,
    PersonRow,
    RepoAIRow,
    RepoClassification,
)


def _int(state: dict[str, Any], key: str, lo: int, hi: int) -> int:
    raw = str(state.get(key, "")).strip()
    if not raw.isdigit() or not lo <= int(raw) <= hi:
        raise ValueError(f"{key} must be an integer in [{lo}, {hi}], got {raw!r}")
    return int(raw)


def _bundles_by_index(entries: list[Any], model: type, label: str) -> dict[int, Any]:
    out: dict[int, Any] = {}
    for position, entry in enumerate(entries):
        if isinstance(entry, dict) and "value" in entry:
            index, raw = int(entry.get("_map_index", position)), entry["value"]
        else:
            index, raw = position, entry
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            bundle = model.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError, TypeError) as exc:
            raise ValueError(
                f"{label} bundle at index {index} is not a valid {model.__name__}: {exc}"
            ) from exc
        if index in out:
            raise ValueError(f"{label}: duplicate bundle index {index}")
        out[index] = bundle
    return out


def _findings_by_index(findings: list[Any], model: type, label: str) -> dict[int, Any]:
    out: dict[int, Any] = {}
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError(f"{label} finding is not a dict: {finding!r}")
        index = finding.get("source_index", finding.get("_map_index"))
        if not isinstance(index, int):
            raise ValueError(f"{label} finding missing source index")
        if index in out:
            raise ValueError(f"{label}: duplicate finding index {index}")
        if "_error" in finding:
            # on_error: skip emits an error-shaped finding — a CONTAINED model
            # failure; the row becomes map_failed and is counted against MAX_MAP_FAILED
            continue
        payload = {
            k: v for k, v in finding.items() if k not in ("_map_index", "source_index")
        }
        try:
            out[index] = model.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(
                f"{label} finding {index} invalid: {exc.errors()[0]['msg']}: {payload!r}"
            ) from exc
    return out


def _reconcile_ids(discovered: list[str], bundle_ids: list[str], label: str) -> None:
    if len(set(discovered)) != len(discovered):
        raise ValueError(f"{label}: duplicate discovered id")
    if len(set(bundle_ids)) != len(bundle_ids):
        raise ValueError(f"{label}: duplicate bundle id")
    missing = sorted(set(discovered) - set(bundle_ids))
    extra = sorted(set(bundle_ids) - set(discovered))
    if missing or extra:
        raise ValueError(
            f"{label}: identity mismatch; missing bundles {missing}, unexpected bundles {extra}"
        )


def _split(bundles: dict[int, Any], is_canary) -> tuple[dict[int, Any], dict[int, Any]]:
    real = {i: b for i, b in bundles.items() if not is_canary(b)}
    canary = {i: b for i, b in bundles.items() if is_canary(b)}
    return real, canary


# Model-named tools are CLAIMS; canonicalize at the boundary (first match wins).
TOOL_CANON: tuple[tuple[str, str], ...] = (
    ("azure openai", "azure-openai"),
    ("azure-openai", "azure-openai"),
    ("azure.ai", "azure-ai"),
    ("@azure/openai", "azure-openai"),
    ("copilot", "copilot"),
    ("claude.md", "claude"),
    ("agents.md", "agents-md"),
    (".github/skills", "agent-skills"),
    ("cursor", "cursor"),
    ("yamlgraph", "yamlgraph"),
    ("replicate", "replicate"),
    ("openai", "openai"),
    ("anthropic", "anthropic"),
    ("claude", "claude"),
    ("langgraph", "langgraph"),
    ("langchain", "langchain"),
    ("llama-index", "llama-index"),
    ("llama_index", "llama-index"),
    ("llamaindex", "llama-index"),
    ("semantic-kernel", "semantic-kernel"),
    ("semantickernel", "semantic-kernel"),
    ("semantic kernel", "semantic-kernel"),
    ("mistral", "mistral"),
    ("ollama", "ollama"),
    ("cohere", "cohere"),
    ("gemini", "gemini"),
    ("google-generativeai", "gemini"),
    ("transformers", "transformers"),
    ("dependabot", "dependabot"),
)


def canonical_tool_name(name: str) -> str:
    low = name.strip().lower()
    for needle, canon in TOOL_CANON:
        if needle in low:
            return canon
    return low


def _canon_tools(tools: list[Any]) -> list[Any]:
    seen: set[tuple[str, str]] = set()
    out = []
    for t in tools:
        canon = t.model_copy(update={"name": canonical_tool_name(t.name)})
        key = (canon.name, canon.kind)
        if key not in seen:
            seen.add(key)
            out.append(canon)
    return out


def _repo_row(bundle: GitHubBundle, cls: RepoClassification | None) -> RepoAIRow:
    if cls is None:
        return RepoAIRow(
            id=bundle.id,
            pushed_at=bundle.pushed_at,
            purpose="",
            ai_usage="unclear",
            ai_tools=[],
            search_keywords=[],
            contributors=bundle.contributors,
            status="map_failed",
        )
    allowed = bundle.evidence_paths()
    tools = _canon_tools([t for t in cls.ai_tools if t.evidence_path in allowed])
    usage = cls.ai_usage
    if usage != "none" and not tools:
        usage = "unclear"
    return RepoAIRow(
        id=bundle.id,
        pushed_at=bundle.pushed_at,
        purpose=cls.purpose,
        ai_usage=usage,
        ai_tools=tools,
        search_keywords=[],
        contributors=bundle.contributors,
        status="classified",
    )


def _jira_row(bundle: JiraBundle, cls: JiraClassification | None) -> JiraAIRow:
    if cls is None:
        return JiraAIRow(
            key=bundle.key,
            purpose="",
            ai_usage="unclear",
            ai_tools=[],
            updated_in_window=bundle.updated_in_window,
            ai_term_count=bundle.ai_term_count,
            status="map_failed",
        )
    allowed = bundle.issue_keys()
    tools = _canon_tools([t for t in cls.ai_tools if t.evidence_issue in allowed])
    usage = cls.ai_usage
    if usage != "none" and not tools:
        usage = "unclear"
    return JiraAIRow(
        key=bundle.key,
        purpose=cls.purpose,
        ai_usage=usage,
        ai_tools=tools,
        updated_in_window=bundle.updated_in_window,
        ai_term_count=bundle.ai_term_count,
        status="classified",
    )


def _rows(
    bundles: dict[int, Any], findings: dict[int, Any], build, label: str
) -> list[Any]:
    rows = [build(bundles[i], findings.get(i)) for i in sorted(bundles)]
    unknown = sorted(set(findings) - set(bundles))
    if unknown:
        raise ValueError(f"{label}: findings for unknown indices {unknown}")
    failed = sum(1 for r in rows if r.status == "map_failed")
    if failed > MAX_MAP_FAILED:
        raise ValueError(
            f"{label}: map_failed={failed} exceeds MAX_MAP_FAILED={MAX_MAP_FAILED}"
        )
    return rows


def _merge_search(rows: list[RepoAIRow], hits: dict[str, Any]) -> list[str]:
    active = {r.id: r for r in rows}
    caveats: list[str] = []
    for keyword, entry in sorted((hits or {}).items()):
        repos = entry.get("repos", []) if isinstance(entry, dict) else []
        if isinstance(entry, dict) and entry.get("capped"):
            caveats.append(
                f"search '{keyword}' capped at result limit; hits are a sample"
            )
        outside = 0
        for repo in repos:
            if repo in active:
                active[repo].search_keywords.append(keyword)
            else:
                outside += 1
        if outside:
            # counted, not named: out-of-set repos may be private/archived org data
            caveats.append(
                f"search '{keyword}': {outside} hit(s) outside the active set "
                "(inactive/archived/unlisted) not merged"
            )
    return caveats


def _persons_github(
    bundles: list[GitHubBundle], purposes: dict[str, str], top: int
) -> list[PersonRow]:
    score: Counter[str] = Counter()
    repos: dict[str, set[str]] = defaultdict(set)
    for b in bundles:
        for author in b.pr_authors:
            if author.bot:
                continue
            score[author.login] += author.n
            repos[author.login].add(b.id)
        for login in b.contributors:
            if any(m in login.lower() for m in ("[bot]", "dependabot", "renovate")):
                continue
            score[login] += 1
            repos[login].add(b.id)
    ranked = sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
    return [
        PersonRow(
            id=f"github:{login}",
            label=login,
            source="github",
            repos=sorted(repos[login]),
            projects=[],
            score=n,
            rank=i + 1,
        )
        for i, (login, n) in enumerate(ranked)
    ]


def _persons_jira(bundles: list[JiraBundle], top: int) -> list[PersonRow]:
    score: Counter[str] = Counter()
    projects: dict[str, set[str]] = defaultdict(set)
    labels: dict[str, str] = {}
    for b in bundles:
        for person in [*b.assignees, *b.reporters]:
            score[person.account_id] += person.n
            projects[person.account_id].add(b.key)
            labels.setdefault(person.account_id, person.display_name)
    ranked = sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
    return [
        PersonRow(
            id=f"jira:{acc}",
            label=labels[acc],
            source="jira",
            repos=[],
            projects=sorted(projects[acc]),
            score=n,
            rank=i + 1,
        )
        for i, (acc, n) in enumerate(ranked)
    ]


def _ai_tools(repos: list[RepoAIRow], jira: list[JiraAIRow]) -> list[AIToolRow]:
    acc: dict[tuple[str, str], dict[str, Any]] = {}
    for r in repos:
        for t in r.ai_tools:
            slot = acc.setdefault(
                (t.name.lower(), t.kind),
                {"repos": set(), "projects": set(), "evidence": []},
            )
            slot["repos"].add(r.id)
            slot["evidence"].append(f"{r.id}:{t.evidence_path}")
    for j in jira:
        for t in j.ai_tools:
            slot = acc.setdefault(
                (t.name.lower(), t.kind),
                {"repos": set(), "projects": set(), "evidence": []},
            )
            slot["projects"].add(j.key)
            slot["evidence"].append(f"{j.key}:{t.evidence_issue}")
    rows = [
        AIToolRow(
            name=name,
            kind=kind,
            n_repos=len(v["repos"]),
            n_projects=len(v["projects"]),
            evidence=sorted(v["evidence"]),
        )
        for (name, kind), v in acc.items()
    ]
    return sorted(rows, key=lambda r: (-(r.n_repos + r.n_projects), r.name))


_SOURCES = {
    "repo": (
        GitHubBundle,
        RepoClassification,
        _repo_row,
        lambda b: b.id,
        CANARY_PREFIX,
    ),
    "jira": (JiraBundle, JiraClassification, _jira_row, lambda b: b.key, "CANARY"),
}


def _source(state: dict[str, Any], kind: str) -> tuple[dict, dict, dict, list]:
    """Parse + reconcile one source → (real_bundles, canary_bundles, findings, rows).

    Canaries are classified through the same prompts and checked HERE, before
    any downstream step — a miss aborts the run.
    """
    model, cls_model, build, ident, canary_prefix = _SOURCES[kind]
    bundles = _bundles_by_index(state.get(f"{kind}_bundles") or [], model, kind)
    real, canary = _split(bundles, lambda b: ident(b).startswith(canary_prefix))
    _reconcile_ids(
        list(state.get(f"{kind}_items") or []), [ident(b) for b in real.values()], kind
    )
    findings = _findings_by_index(state.get(f"{kind}_findings") or [], cls_model, kind)
    rows = _rows(real, {i: f for i, f in findings.items() if i in real}, build, kind)
    canary_rows = [
        build(canary[i], findings.get(i)).model_dump() for i in sorted(canary)
    ]
    canaries.check_canaries(kind, canary_rows)
    return real, canary, findings, rows


def _status_counts(rows: list[Any]) -> dict[str, int]:
    return {
        "classified": sum(r.status == "classified" for r in rows),
        "unclear": sum(r.ai_usage == "unclear" for r in rows),
        "map_failed": sum(r.status == "map_failed" for r in rows),
    }


def _coverage_github(
    cov: dict[str, Any], real: dict[int, GitHubBundle], rows, caveats
) -> CoverageGitHub:
    return CoverageGitHub(
        api_total=cov.get("api_total"),
        listed=int(cov.get("listed", 0)),
        archived=int(cov.get("archived", 0)),
        out_of_window=int(cov.get("out_of_window", 0)),
        visibility_rejected=int(cov.get("visibility_rejected", 0)),
        active=len(real),
        extracted=len(real),
        tree_truncated=sum(b.tree_truncated for b in real.values()),
        search_caveats=caveats,
        **_status_counts(rows),
    )


def _coverage_jira(
    cov: dict[str, Any], real: dict[int, JiraBundle], rows
) -> CoverageJira:
    return CoverageJira(
        visible=int(cov.get("visible", 0)),
        active=len(real),
        dormant=int(cov.get("dormant", 0)),
        extracted=len(real),
        page_cap_hit=bool(cov.get("page_cap_hit")),
        **_status_counts(rows),
    )


def reduce(state: dict[str, Any]) -> dict[str, Any]:
    """Typed reduce of both sources; returns {"reduced": {...}} or raises.

    Frozen order: repo ids → jira ids → evidence reconciliation (inside
    `_source`, with canaries checked per source) → search merge → persons →
    AI tools → coverage → return. Any failure raises; nothing is written here.
    """
    top = _int(state, "top_persons", 1, MAX_TOP_PERSONS)
    repo_real, _, repo_findings, repo_rows = _source(state, "repo")
    jira_real, _, jira_findings, jira_rows = _source(state, "jira")
    caveats = _merge_search(repo_rows, state.get("search_hits") or {})
    purposes = {r.id: r.purpose for r in repo_rows}
    persons_gh = _persons_github(list(repo_real.values()), purposes, top)
    persons_ji = _persons_jira(list(jira_real.values()), top)
    tools = _ai_tools(repo_rows, jira_rows)
    github = _coverage_github(
        dict(state.get("coverage_gh") or {}), repo_real, repo_rows, caveats
    )
    jira = _coverage_jira(dict(state.get("coverage_jira") or {}), jira_real, jira_rows)
    return {
        "reduced": {
            "repos": [r.model_dump(mode="json") for r in repo_rows],
            "jira": [r.model_dump(mode="json") for r in jira_rows],
            "persons_github": [p.model_dump() for p in persons_gh],
            "persons_jira": [p.model_dump() for p in persons_ji],
            "ai_tools": [t.model_dump() for t in tools],
            "coverage": {"github": github.model_dump(), "jira": jira.model_dump()},
            "canaries": {"repo": "pass", "jira": "pass"},
            "purposes": {**purposes, **{r.key: r.purpose for r in jira_rows}},
            "llm_calls_actual": len(repo_findings) + len(jira_findings),
        }
    }
