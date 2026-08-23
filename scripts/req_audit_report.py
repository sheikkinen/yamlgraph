#!/usr/bin/env python3
"""Reconcile witness-audit verdicts and render the ranked report (FR-851).

Boundary reconciliation per two_strike_split: model output is a CLAIM —
returned req_ids are verified against the batch's input ids. Hallucinated
ids reject the batch result, duplicates keep first, missing ids re-queue
once then surface as unaudited. No input requirement disappears silently.

Usage:
    python scripts/req_audit_report.py --audit-dir tmp/req-audit \
        --model claude-haiku --provider anthropic --tree-sha <sha>
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

VERDICT_RANK = {"no": 0, "partial": 1}


@dataclass
class BatchResult:
    audited: dict[str, dict]
    requeue: list[str]
    duplicates: list[str]
    rejected: bool


@dataclass
class ReconcileResult:
    audited: dict[str, dict]
    unaudited: list[str]
    rejected_batches: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)


def reconcile_batch(input_ids: list[str], verdicts: list[dict]) -> BatchResult:
    """Verify one batch's verdicts against its input ids."""
    input_set = set(input_ids)
    hallucinated = [v["req_id"] for v in verdicts if v["req_id"] not in input_set]
    if hallucinated:
        return BatchResult(
            audited={}, requeue=list(input_ids), duplicates=[], rejected=True
        )
    audited: dict[str, dict] = {}
    duplicates: list[str] = []
    for v in verdicts:
        req_id = v["req_id"]
        if req_id in audited:
            duplicates.append(req_id)
            continue
        audited[req_id] = v
    requeue = [r for r in input_ids if r not in audited]
    return BatchResult(
        audited=audited, requeue=requeue, duplicates=duplicates, rejected=False
    )


def reconcile(
    batch_inputs: dict[str, list[str]],
    responses: dict[str, list[dict]],
    retry_responses: dict[str, list[dict]] | None = None,
) -> ReconcileResult:
    """Two-pass reconciliation: first responses, one retry, then unaudited."""
    audited: dict[str, dict] = {}
    requeue_by_batch: dict[str, list[str]] = {}
    rejected: list[str] = []
    duplicates: list[str] = []

    for batch_id in sorted(batch_inputs):
        result = reconcile_batch(batch_inputs[batch_id], responses.get(batch_id, []))
        if result.rejected:
            rejected.append(batch_id)
        audited.update(result.audited)
        duplicates.extend(result.duplicates)
        if result.requeue:
            requeue_by_batch[batch_id] = result.requeue

    unaudited: list[str] = []
    retry_responses = retry_responses or {}
    for batch_id, requeued_ids in sorted(requeue_by_batch.items()):
        retry = reconcile_batch(requeued_ids, retry_responses.get(batch_id, []))
        if retry.rejected:
            rejected.append(f"{batch_id}(retry)")
            unaudited.extend(requeued_ids)
            continue
        audited.update(retry.audited)
        duplicates.extend(retry.duplicates)
        unaudited.extend(retry.requeue)

    return ReconcileResult(
        audited=audited,
        unaudited=sorted(set(unaudited)),
        rejected_batches=rejected,
        duplicates=duplicates,
    )


def render_report(result: ReconcileResult, metadata: dict) -> str:
    """Ranked markdown report: no/partial/unaudited first, yes collapsed."""
    flagged = sorted(
        (v for v in result.audited.values() if v["witnessed"] in VERDICT_RANK),
        key=lambda v: (VERDICT_RANK[v["witnessed"]], v["req_id"]),
    )
    yes_count = sum(1 for v in result.audited.values() if v["witnessed"] == "yes")

    lines = [
        "# Requirement Witness Audit",
        "",
        f"- Stage: {metadata.get('stage', '1')}",
        f"- Model: {metadata.get('model', '?')} ({metadata.get('provider', '?')})",
        f"- Tree: {metadata.get('tree_sha', '?')}",
        f"- Batches: {metadata.get('batch_count', '?')}",
        f"- Reconciliation: {len(result.audited)} audited, "
        f"{len(result.unaudited)} unaudited, "
        f"{len(result.rejected_batches)} rejected batches, "
        f"{len(result.duplicates)} duplicates",
    ]
    run_manifest = metadata.get("run_manifest") or {}
    if run_manifest:  # FR-860: provenance header from run-manifest.json
        dirty = "DIRTY TREE" if run_manifest.get("git_dirty") else "clean"
        lines += [
            f"- Provenance: git {run_manifest.get('git_sha', '?')} ({dirty})",
            "- Instrument: "
            f"{run_manifest.get('recorded_context_count', '?')} recorded "
            f"contexts / {run_manifest.get('tagged_test_count', '?')} "
            "tagged tests",
            f"- Run model: {run_manifest.get('model', '?')} "
            f"({run_manifest.get('provider', '?')})",
        ]
    lines += [
        "",
        "## Flagged (no, then partial)",
        "",
    ]
    for v in flagged:
        lines.append(
            f"- **{v['req_id']}** [{v['witnessed']}] {v['gap']} → {v['suggestion']}"
        )
    if not flagged:
        lines.append("(none)")
    lines += ["", "## Unaudited", ""]
    lines += [f"- {req_id}" for req_id in result.unaudited] or ["(none)"]
    lines += [
        "",
        "## Yes (collapsed)",
        "",
        f"{yes_count} requirements graded yes.",
        "",
    ]
    return "\n".join(lines)


def _load_responses(raw_dir: Path) -> dict[str, list[dict]]:
    """batch id → verdict list from raw response files."""
    responses: dict[str, list[dict]] = {}
    if not raw_dir.is_dir():
        return responses
    for path in sorted(raw_dir.glob("batch-*.json")):
        data = json.loads(path.read_text())
        verdicts = data["verdicts"] if isinstance(data, dict) else data
        responses[path.stem] = verdicts
    return responses


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=Path("tmp/req-audit"))
    parser.add_argument("--model", default="?")
    parser.add_argument("--provider", default="?")
    parser.add_argument(
        "--stage", default="1 (witness plausibility from names and declared links)"
    )
    parser.add_argument("--tree-sha", default="")
    parser.add_argument(
        "--run-manifest",
        type=Path,
        default=None,
        help="FR-860 run-manifest.json to embed as report provenance",
    )
    args = parser.parse_args()

    manifest = json.loads((args.audit_dir / "manifest.json").read_text())
    responses = _load_responses(args.audit_dir / "raw")
    retry_responses = _load_responses(args.audit_dir / "raw-retry")

    tree_sha = (
        args.tree_sha
        or subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    )

    result = reconcile(manifest, responses, retry_responses)
    run_manifest = (
        json.loads(args.run_manifest.read_text()) if args.run_manifest else {}
    )
    report = render_report(
        result,
        metadata={
            "model": args.model,
            "provider": args.provider,
            "stage": args.stage,
            "tree_sha": tree_sha,
            "batch_count": len(manifest),
            "run_manifest": run_manifest,
        },
    )
    out_path = args.audit_dir / "report.md"
    out_path.write_text(report)
    print(f"✓ report → {out_path}")
    if result.unaudited:
        print(f"⚠️  {len(result.unaudited)} unaudited: {result.unaudited}")


if __name__ == "__main__":
    main()
