"""FR-1027 deterministic markdown/ledger renderers (code-owned, LLM-free).

Every share is rendered as `n of <denominator>=<value>`; `unclear` and
`map_failed` are shown beside every AI-use share; an unavailable org API total
prints `unavailable` and no ratio (judgement R-4).
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from examples.demos.org_ai_dossier.models import MAX_ONEPAGER_WORDS, ONEPAGER_FINDINGS


def _share(n: int, denom_name: str, denom: int) -> str:
    return f"{n} of {denom_name}={denom}"


def _coverage_block(cov: dict[str, Any]) -> list[str]:
    g, j = cov["github"], cov["jira"]
    total = "unavailable" if g["api_total"] is None else str(g["api_total"])
    lines = [
        "## Coverage",
        "",
        f"- GitHub org API total: {total}; listed (token-visible)={g['listed']}; archived={g['archived']}; "
        f"out_of_window={g['out_of_window']}; visibility_rejected={g['visibility_rejected']}",
        f"- GitHub active={g['active']}; extracted={g['extracted']}; classified={g['classified']}; "
        f"unclear={g['unclear']}; map_failed={g['map_failed']}; tree_truncated={g['tree_truncated']}",
        f"- Jira visible={j['visible']}; active={j['active']}; dormant={j['dormant']}; classified={j['classified']}; "
        f"unclear={j['unclear']}; map_failed={j['map_failed']}; page_cap_hit={j['page_cap_hit']}",
    ]
    lines += [f"- caveat: {c}" for c in g["search_caveats"][:10]]
    return lines + [""]


def _ai_share_lines(reduced: dict[str, Any]) -> list[str]:
    g = reduced["coverage"]["github"]
    j = reduced["coverage"]["jira"]
    repos, jira = reduced["repos"], reduced["jira"]
    lines = ["## AI use (denominator = active units)", ""]
    for usage in ("product", "dev_tooling", "both", "none", "unclear"):
        n_r = sum(r["ai_usage"] == usage for r in repos)
        n_j = sum(x["ai_usage"] == usage for x in jira)
        lines.append(
            f"- {usage}: repos {_share(n_r, 'active', g['active'])}; jira {_share(n_j, 'active', j['active'])}"
        )
    lines.append(f"- map_failed: repos {g['map_failed']}; jira {j['map_failed']}")
    return lines + [""]


def _tools_lines(reduced: dict[str, Any], limit: int) -> list[str]:
    lines = [
        "## AI tools",
        "",
        "| tool | kind | repos | jira projects |",
        "| --- | --- | --- | --- |",
    ]
    for t in reduced["ai_tools"][:limit]:
        lines.append(
            f"| {t['name']} | {t['kind']} | {t['n_repos']} | {t['n_projects']} |"
        )
    return lines + [""]


def _persons_lines(reduced: dict[str, Any], limit: int, summaries: bool) -> list[str]:
    lines = ["## Persons (two source-local rankings; no cross-system join)", ""]
    for source in ("github", "jira"):
        lines.append(f"### {source}")
        for p in reduced[f"persons_{source}"][:limit]:
            units = ", ".join(p["repos"] or p["projects"])
            line = (
                f"- #{p['rank']} {p['id']} ({p['label']}) score={p['score']}: {units}"
            )
            if summaries and p.get("summary"):
                line += f" — {p['summary']}"
            lines.append(line)
        lines.append("")
    return lines


CITATION_TOKEN_RE = re.compile(r"\s*\b(?:row|label):[^\s\]\),]+")


def _claims_lines(title: str, claims: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    for c in claims:
        # the model tends to echo citation ids inside the prose; citations live in brackets
        text = CITATION_TOKEN_RE.sub("", str(c["text"])).strip()
        lines.append(f"- {text} [{', '.join(str(x) for x in c.get('citations', []))}]")
    return lines + [""]


def _onepager(
    state: dict[str, Any],
    reduced: dict[str, Any],
    claims: list[dict[str, Any]],
    run_id: str,
) -> str:
    if len(claims) != ONEPAGER_FINDINGS:
        raise ValueError(
            f"onepager must carry exactly three findings, got {len(claims)}"
        )
    lines = [
        f"# Org AI dossier — onepager ({state['org']}, window {state['window_days']}d)",
        "",
    ]
    lines += _coverage_block(reduced["coverage"])
    lines += _ai_share_lines(reduced)
    lines += _tools_lines(reduced, 8)
    lines += _persons_lines(reduced, 5, summaries=False)
    lines += _claims_lines("Findings", claims)
    lines += [
        "## Method",
        "",
        f"- run {run_id}; provider azure; every unit one judgement; reducers code-owned; "
        "canaries repo/jira passed; see run.json",
        "",
        "## Caveats",
        "",
        "- token-visible subset of the org; code-search hits are default-branch only; "
        "persons are source-local rankings, never joined",
        "",
    ]
    text = "\n".join(lines)
    words = len(text.split())
    if words > MAX_ONEPAGER_WORDS:
        raise ValueError(
            f"onepager is {words} words; bound is {MAX_ONEPAGER_WORDS} (800)"
        )
    return text


def _dossier(state, reduced, claims, summaries: bool) -> str:
    lines = [f"# Org AI dossier — {state['org']} (window {state['window_days']}d)", ""]
    lines += _coverage_block(reduced["coverage"]) + _ai_share_lines(reduced)
    lines += _claims_lines("Findings", claims) + _tools_lines(reduced, 100)
    lines += _persons_lines(reduced, 100, summaries=summaries)
    return "\n".join(lines)


def _repos_md(state, reduced) -> str:
    lines = (
        [f"# Repositories — {state['org']}", ""]
        + _coverage_block(reduced["coverage"])
        + _ai_share_lines(reduced)
    )
    for r in reduced["repos"]:
        tools = (
            ", ".join(f"{t['name']}({t['evidence_path']})" for t in r["ai_tools"])
            or "-"
        )
        lines += [
            f"## {r['id']}",
            "",
            f"- status: {r['status']}; ai_usage: {r['ai_usage']}; purpose: {r['purpose']}",
            f"- tools: {tools}",
            f"- search keywords: {', '.join(r['search_keywords']) or '-'}",
            f"- contributors: {', '.join(r['contributors']) or '-'}",
            "",
        ]
    return "\n".join(lines)


def _jira_md(state, reduced) -> str:
    lines = (
        [f"# Jira projects — {state['org']}", ""]
        + _coverage_block(reduced["coverage"])
        + _ai_share_lines(reduced)
    )
    for j in reduced["jira"]:
        tools = (
            ", ".join(f"{t['name']}({t['evidence_issue']})" for t in j["ai_tools"])
            or "-"
        )
        lines += [
            f"## {j['key']}",
            "",
            f"- status: {j['status']}; ai_usage: {j['ai_usage']}; purpose: {j['purpose']}",
            f"- updated in window: {j['updated_in_window']}; AI-term issues: {j['ai_term_count']}",
            f"- tools: {tools}",
            "",
        ]
    return "\n".join(lines)


def _write_ledgers(
    root: Path, reduced: dict[str, Any], raw: dict[str, list] | None = None
) -> dict[str, Path]:
    led = root / "ledgers"
    led.mkdir()
    paths = {}
    for name, rows in (
        ("repos", reduced["repos"]),
        ("jira", reduced["jira"]),
        ("persons", reduced["persons_github"] + reduced["persons_jira"]),
        *((f"raw_{k}", v) for k, v in (raw or {}).items()),
    ):
        p = led / f"{name}.jsonl"
        p.write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
            encoding="utf-8",
        )
        paths[f"ledgers/{name}.jsonl"] = p
    p = led / "ai_tools.csv"
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["name", "kind", "n_repos", "n_projects", "evidence"])
        for t in reduced["ai_tools"]:
            w.writerow(
                [
                    t["name"],
                    t["kind"],
                    t["n_repos"],
                    t["n_projects"],
                    ";".join(t["evidence"]),
                ]
            )
    paths["ledgers/ai_tools.csv"] = p
    return paths
