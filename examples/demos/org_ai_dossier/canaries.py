"""FR-1027 hidden semantic canaries (judgement R-3).

Two frozen families with known answers, injected as extra map items AFTER
extraction and BEFORE classification (the reducer cannot make LLM calls), then
stripped by the reducer before any ledger is accepted. A miss on any canary
aborts the run. Ids carry a reserved prefix so no real unit can collide.
"""

from __future__ import annotations

import json
from typing import Any

from examples.demos.org_ai_dossier.models import CANARY_PREFIX

REPO_CANARIES: list[dict[str, Any]] = [
    {
        "id": f"{CANARY_PREFIX}a-openai-copilot",
        "description": "Customer chat assistant",
        "pushed_at": "2026-09-01T00:00:00Z",
        "archived": False,
        "visibility": "private",
        "language": "TypeScript",
        "readme_head": "# Assistant\nA chat assistant service built on the OpenAI API.",
        "contributors": ["c1"],
        "tree_truncated": False,
        "instruction_files": [".github/copilot-instructions.md"],
        "manifest_hits": [{"path": "package.json", "line": '"openai": "^4.0.0",'}],
        "workflow_hits": [],
        "pr_authors": [{"login": "c1", "bot": False, "n": 2}],
        "absent": [],
    },
    {
        "id": f"{CANARY_PREFIX}b-marketing-only",
        "description": "AI-powered analytics dashboard",
        "pushed_at": "2026-09-01T00:00:00Z",
        "archived": False,
        "visibility": "private",
        "language": "TypeScript",
        "readme_head": "# Dashboard\nOur AI-powered dashboard shows sales KPIs.",
        "contributors": ["c2"],
        "tree_truncated": False,
        "instruction_files": [],
        "manifest_hits": [],
        "workflow_hits": [],
        "pr_authors": [{"login": "c2", "bot": False, "n": 1}],
        "absent": [],
    },
    {
        "id": f"{CANARY_PREFIX}c-plain-library",
        "description": "Date formatting helpers",
        "pushed_at": "2026-09-01T00:00:00Z",
        "archived": False,
        "visibility": "private",
        "language": "TypeScript",
        "readme_head": "# dates\nZero-dependency date formatting helpers.",
        "contributors": ["c3"],
        "tree_truncated": False,
        "instruction_files": [],
        "manifest_hits": [],
        "workflow_hits": [],
        "pr_authors": [],
        "absent": [],
    },
]

JIRA_CANARIES: list[dict[str, Any]] = [
    {
        "key": "CANARYA",
        "name": "Copilot rollout",
        "project_type": "software",
        "lead": None,
        "updated_in_window": 6,
        "created_in_window": 2,
        "ai_term_count": 4,
        "issues": [
            {
                "key": "CANARYA-1",
                "summary": "Roll out GitHub Copilot to all developers",
                "issuetype": "Story",
                "status": "In Progress",
                "assignee_id": "k1",
                "reporter_id": "k2",
                "description_head": "Enable Copilot seats and write usage guidelines.",
            },
            {
                "key": "CANARYA-2",
                "summary": "Measure Copilot acceptance rate",
                "issuetype": "Task",
                "status": "To Do",
                "assignee_id": "k1",
                "reporter_id": "k2",
                "description_head": "",
            },
        ],
        "assignees": [{"account_id": "k1", "display_name": "K One", "n": 2}],
        "reporters": [{"account_id": "k2", "display_name": "K Two", "n": 2}],
    },
    {
        "key": "CANARYB",
        "name": "Office move",
        "project_type": "business",
        "lead": None,
        "updated_in_window": 3,
        "created_in_window": 1,
        "ai_term_count": 0,
        "issues": [
            {
                "key": "CANARYB-1",
                "summary": "Order new desks",
                "issuetype": "Task",
                "status": "Done",
                "assignee_id": "k3",
                "reporter_id": "k3",
                "description_head": "Twelve standing desks.",
            },
        ],
        "assignees": [{"account_id": "k3", "display_name": "K Three", "n": 1}],
        "reporters": [{"account_id": "k3", "display_name": "K Three", "n": 1}],
    },
]

# Expected answers: (ai_usage, required tool names ⊆ surviving tools)
REPO_EXPECTED: list[tuple[str, set[str]]] = [
    ("both", {"openai", "copilot"}),
    ("unclear", set()),
    ("none", set()),
]
JIRA_EXPECTED: list[tuple[str, set[str]]] = [
    ("dev_tooling", {"copilot"}),
    ("none", set()),
]


def _entries(bundles: list[dict[str, Any]], start: int) -> list[dict[str, Any]]:
    return [
        {"value": json.dumps(b), "_map_index": start + i} for i, b in enumerate(bundles)
    ]


def inject_repo_canaries(state: dict[str, Any]) -> dict[str, Any]:
    """Append the repo canary bundles after the real extracted items."""
    start = len(state.get("repo_bundles") or [])
    return {"repo_bundles": _entries(REPO_CANARIES, start)}


def inject_jira_canaries(state: dict[str, Any]) -> dict[str, Any]:
    start = len(state.get("jira_bundles") or [])
    return {"jira_bundles": _entries(JIRA_CANARIES, start)}


def canary_expected_findings(kind: str, start: int) -> list[dict[str, Any]]:
    """Correct classifier outputs for the family — test/documentation helper."""
    if kind == "repo":
        out = []
        for i, (usage, tools) in enumerate(REPO_EXPECTED):
            bundle = REPO_CANARIES[i]
            ai_tools = []
            if "openai" in tools:
                ai_tools.append(
                    {
                        "name": "openai",
                        "kind": "provider",
                        "evidence_path": "package.json",
                    }
                )
            if "copilot" in tools:
                ai_tools.append(
                    {
                        "name": "copilot",
                        "kind": "coding_agent",
                        "evidence_path": ".github/copilot-instructions.md",
                    }
                )
            out.append(
                {
                    "_map_index": start + i,
                    "purpose": bundle["description"],
                    "ai_usage": usage,
                    "ai_tools": ai_tools,
                    "rationale": "canary",
                }
            )
        return out
    out = []
    for i, (usage, tools) in enumerate(JIRA_EXPECTED):
        bundle = JIRA_CANARIES[i]
        ai_tools = (
            [
                {
                    "name": "copilot",
                    "kind": "coding_agent",
                    "evidence_issue": bundle["issues"][0]["key"],
                }
            ]
            if "copilot" in tools
            else []
        )
        out.append(
            {
                "_map_index": start + i,
                "purpose": bundle["name"],
                "ai_usage": usage,
                "ai_tools": ai_tools,
                "rationale": "canary",
            }
        )
    return out


def check_canaries(kind: str, rows: list[dict[str, Any]]) -> None:
    """`rows` are the reduced canary rows in family order; raise on any miss."""
    expected = REPO_EXPECTED if kind == "repo" else JIRA_EXPECTED
    if len(rows) != len(expected):
        raise ValueError(
            f"canary {kind}: expected {len(expected)} rows, got {len(rows)}"
        )
    for row, (usage, tools) in zip(rows, expected, strict=True):
        got = {t["name"].lower() for t in row.get("ai_tools", [])}
        if (
            row.get("status") != "classified"
            or row.get("ai_usage") != usage
            or not tools <= got
        ):
            ident = row.get("id") or row.get("key")
            raise ValueError(
                f"canary {kind} miss on {ident}: expected {usage}/{sorted(tools)}, "
                f"got {row.get('ai_usage')}/{sorted(got)} ({row.get('status')})"
            )
