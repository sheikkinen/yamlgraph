"""FR-1027 LLM-free aggregates: source-local person rankings and AI-tool inventory.

Persons are source-qualified (`github:<login>`, `jira:<accountId>`); the two
rankings are never joined (judgement R-5). Bots are excluded on the GitHub side.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from examples.demos.org_ai_dossier.models import (
    AIToolRow,
    GitHubBundle,
    JiraAIRow,
    JiraBundle,
    PersonRow,
    RepoAIRow,
)


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
