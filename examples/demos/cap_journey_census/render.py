"""CAP journey census — markdown rendering of the reduced ledger (LLM-free)."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

PROMPT_VERSION = "judge_cap.v1"


def _mermaid(rows: list[Any]) -> str:
    lines = ["```mermaid", "graph LR"]
    for r in rows:
        for m in r.mechanical.get("consumers_by_module", [])[:5]:
            lines.append(
                f'  {r.cap_id}["{r.cap_id} {r.name[:28]}"] --> m{abs(hash(m)) % 10**6}["{m}"]'
            )
    lines.append("```")
    return "\n".join(lines) if len(lines) > 3 else "_no module consumers recorded_"


def _markdown(
    rows: list[Any], catalog: list[str], misses: list[str], meta: dict[str, Any]
) -> str:
    judged = [r for r in rows if r.classification_status == "judged"]
    out = [
        "# CAP Journey Census Ledger\n",
        f"- rows: {len(rows)}  judged: {len(judged)}  row_failed: {sum(r.classification_status == 'row_failed' for r in rows)}  abstained: {sum(r.classification_status == 'abstained' for r in rows)}",
        f"- model: {meta['model']}  git_sha: {meta['git_sha']}  prompt: {PROMPT_VERSION}",
        f"- canary misses: {len(misses)}"
        + (" — " + "; ".join(misses) if misses else ""),
        "",
    ]
    out.append(
        "## Journey × CAP matrix\n\n| journey | CAPs | keep | wedge | retire | contested |\n|---|---:|---:|---|---:|---:|"
    )
    for j in catalog:
        js = [r for r in judged if j in r.journeys]
        d = Counter(r.disposition_effective for r in js)
        wedge = next((r.extend_to for r in js if r.extend_to), "-")
        out.append(
            f"| {j} | {len(js)} | {d['keep']} | {wedge} | {d['retire']} | {d['contested']} |"
        )
    off = Counter(o for r in judged for o in r.off_catalog)
    out.append(f"\noff-catalog labels: {dict(off) or 'none'}\n")
    out.append(
        "## Disposition table\n\n| CAP | name | disposition | effective | extend_to | consumer_cited | anchor violations |\n|---|---|---|---|---|---|---|"
    )
    for r in sorted(judged, key=lambda r: (r.disposition_effective or "", r.cap_id)):
        out.append(
            f"| {r.cap_id} | {r.name[:40]} | {r.disposition} | {r.disposition_effective} | {r.extend_to or '-'} | {r.consumer_cited or '-'} | {'; '.join(r.anchor_violations) or '-'} |"
        )
    out.append("\n## Value\n")
    vs = Counter(r.value_status for r in judged)
    out.append(
        f"stated: {vs['stated']}  value_generic: {vs['value_generic']}  value_unstated: {vs['value_unstated']}  / {len(judged)}\n"
    )
    out.append("| CAP | for whom | pain | versus |\n|---|---|---|---|")
    for r in judged:
        out.append(
            f"| {r.cap_id} | {r.value_for_whom or '-'} | {(r.value_pain or '-')[:90]} | {(r.value_versus or '-')[:60]} |"
        )
    out.append("\n## Blast by journey\n")
    by_j: dict[str, list[Any]] = defaultdict(list)
    for r in judged:
        for j in r.journeys:
            by_j[j].append(r)
    for j in catalog:
        if by_j.get(j):
            out.append(f"### {j}\n\n{_mermaid(by_j[j])}\n")
    out.append("## Failed / abstained rows\n\n| CAP | status | reason |\n|---|---|---|")
    for r in rows:
        if r.classification_status != "judged":
            out.append(
                f"| {r.cap_id} | {r.classification_status} | {(r.failure_reason or '-')[:160]} |"
            )
    return "\n".join(out) + "\n"
