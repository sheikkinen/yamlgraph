#!/usr/bin/env python3
"""FR-1012 Step 0 — the sole, fail-closed invocation surface for the Chaplain
disposition census (round-2 judgement R-3; REQ-YG-666, CAP-264).

Usage:
    python scripts/chaplain_census.py --preflight            # manifest + refusals only, no provider call
    python scripts/chaplain_census.py                        # full run: preflight → shared graph → reconcile
    python scripts/chaplain_census.py --resolutions docs/census/chaplain-manual-resolutions.json

Every refusal happens BEFORE the shared graph (and therefore the provider) is
invoked. The graph is `examples/demos/corpus_census/graph.yaml`, byte-for-byte
unchanged; Chaplain-specific behaviour lives only in the adapters and here.

Exit codes: 0 ok · 64 usage · 65 preflight/contract refusal · 69 executor
missing · 70 graph failure · 75 unresolved manual-review rows (artifacts
written; enforcement stops until FR-1012 records the human resolutions).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GRAPH = "examples/demos/corpus_census/graph.yaml"
ADAPTERS = REPO_ROOT / "examples/demos/corpus_census/adapters"
OUT_DIR = REPO_ROOT / "docs/census"
STEM = "chaplain-test-disposition"

# Frozen ceilings (FR-1012 § Step 0; AC-05).
MAX_ITEMS = 120
MAX_TOTAL_BYTES = 1_500_000
MAX_ITEM_BYTES = 64 * 1024  # operator amendment 2026-09-06: 48 KB refused test_philosopher.py (52 409 B); FR-1012 § Step 0 records it
MAX_CALLS = 130  # items (one judge call each) + one synthesis call
TIMEOUT_S = 20 * 60
PROVIDER = "anthropic"
MODEL = "claude-haiku-4-5"
# Prerequisite merges (FR-1012 § Prerequisite gate) — the source SHA must descend from all three.
PREREQUISITES = {"FR-1014": "fec26941", "FR-1011": "84baceb7", "FR-1015": "32fd6e9f"}
# Withheld canaries (invariant 8): matched by verdict FAMILY, never shown to the rubric.
CANARIES = {
    "tests/unit/test_fr305_watcher_pipeline_v2.py": "delete",
    "tests/unit/test_fr_triage.py": "keep",
}
CREDENTIAL_RE = re.compile(r"(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
VISIBILITY = "operator-owned source and tests of a private repository; no personal data; provider anthropic/claude-haiku-4-5 approved for this class (FR-1012 R-7 record)"

EX_USAGE, EX_CONTRACT, EX_UNAVAILABLE, EX_GRAPH, EX_UNRESOLVED = 64, 65, 69, 70, 75


class Refusal(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


def _adapters():
    spec = importlib.util.spec_from_file_location("chaplain_adapters", ADAPTERS / "chaplain_adapters.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _git(*argv: str) -> str:
    return subprocess.run(["git", *argv], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()  # noqa: S603 — fixed git argv (CONF-463)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- preflight ---------------------------------------------------------------


def preflight(ad, out_dir: Path) -> dict:
    """Freeze the manifest and refuse every breach BEFORE any provider call (AC-05)."""
    head = _git("rev-parse", "HEAD")
    if _git("status", "--porcelain", "--", ".chaplain", "tests", "capabilities"):
        raise Refusal(EX_CONTRACT, "census tree is dirty under .chaplain/, tests/ or capabilities/ — commit or stash first")
    for fr, sha in PREREQUISITES.items():
        ok = subprocess.run(["git", "merge-base", "--is-ancestor", sha, head], cwd=REPO_ROOT, check=False).returncode == 0  # noqa: S603 — fixed git argv (CONF-463)
        if not ok:
            raise Refusal(EX_CONTRACT, f"source {head[:8]} does not descend from {fr} merge {sha}")
    items = ad.discover_paths(REPO_ROOT)
    rows = ad.build_manifest(REPO_ROOT, head, items)
    total = sum(r["bytes"] for r in rows)
    oversize = [(r["path"], r["bytes"]) for r in rows if r["bytes"] > MAX_ITEM_BYTES]
    calls = len(rows) + 1
    problems = []
    if len(rows) > MAX_ITEMS:
        problems.append(f"{len(rows)} items > {MAX_ITEMS}")
    if total > MAX_TOTAL_BYTES:
        problems.append(f"{total} bytes total > {MAX_TOTAL_BYTES}")
    if oversize:
        problems.append(f"items over {MAX_ITEM_BYTES // 1024} KB: " + ", ".join(f"{p} ({b} B)" for p, b in oversize))
    if calls > MAX_CALLS:
        problems.append(f"{calls} model calls > {MAX_CALLS}")
    for r in rows:
        if CREDENTIAL_RE.search((REPO_ROOT / r["path"]).read_text(encoding="utf-8", errors="replace")):
            problems.append(f"credential-shaped content in {r['path']}")
    manifest_path = out_dir / "chaplain-disposition-input.jsonl"
    manifest_sha = ad.write_manifest(rows, manifest_path)
    record = {
        "run_id": str(uuid.uuid4()),
        "started_at": datetime.now(UTC).isoformat(),
        "source_sha": head,
        "chaplain_tree_sha": _git("rev-parse", "HEAD:.chaplain"),
        "prerequisites": PREREQUISITES,
        "provider": PROVIDER,
        "model": MODEL,
        "visibility_data_classification": VISIBILITY,
        "ceilings": {"max_items": MAX_ITEMS, "max_total_bytes": MAX_TOTAL_BYTES, "max_item_bytes": MAX_ITEM_BYTES, "max_calls": MAX_CALLS, "timeout_s": TIMEOUT_S},
        "counts": {"items": len(rows), "tests": sum(r["kind"] == "test" for r in rows), "caps": sum(r["kind"] == "cap" for r in rows), "bytes": total, "planned_calls": calls},
        "manifest_path": str(manifest_path.relative_to(REPO_ROOT) if manifest_path.is_relative_to(REPO_ROOT) else manifest_path),
        "manifest_sha256": manifest_sha,
        "preflight_problems": problems,
    }
    (out_dir / f"{STEM}.run.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    if problems:
        raise Refusal(EX_CONTRACT, "preflight refused: " + "; ".join(problems))
    return record


# --- graph run ---------------------------------------------------------------


def run_graph(record: dict, out_dir: Path, yamlgraph_bin: str) -> Path:
    raw_dir = out_dir / f"{STEM}.raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    generic_md = out_dir / f"{STEM}.generic.md"
    cmd = [
        yamlgraph_bin, "graph", "run", GRAPH,
        "--tool", f"discover={ADAPTERS / 'chaplain-discover.tool.yaml'}",
        "--tool", f"extract={ADAPTERS / 'chaplain-extract.tool.yaml'}",
        "--var", f"source={REPO_ROOT}",
        "--var", f"rubric=@{ADAPTERS / 'chaplain_rubric.md'}",
        "--var", 'labels=["keep","delete","retire","manual_review"]',
        "--var", f"provider={PROVIDER}", "--var", f"model={MODEL}",
        "--var", f"output_path={generic_md}",
        "--var", f"brief_path={out_dir / (STEM + '.brief.md')}",
        "--var", "brief_rubric=Which chaplain-coupled tests and capability records witness the retired runtime, and what blocks removing the rest?",
        "--full",
    ]
    env = {**os.environ, "CHAPLAIN_CENSUS_MANIFEST": str(REPO_ROOT / record["manifest_path"]), "PYTHONUTF8": "1"}
    (raw_dir / "command.txt").write_text(" ".join(cmd) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(cmd, cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=TIMEOUT_S, check=False)  # noqa: S603 — argv built above (CONF-463)
    except subprocess.TimeoutExpired as exc:
        (raw_dir / "run.stdout.log").write_text((exc.stdout or "") + f"\n[TIMEOUT after {TIMEOUT_S}s]\n", encoding="utf-8")
        raise Refusal(EX_GRAPH, f"graph exceeded the {TIMEOUT_S}s deadline") from exc
    (raw_dir / "run.stdout.log").write_text(proc.stdout, encoding="utf-8")
    (raw_dir / "run.stderr.log").write_text(proc.stderr, encoding="utf-8")
    generic_jsonl = generic_md.with_suffix(".jsonl")
    if proc.returncode != 0 or not generic_jsonl.is_file():
        raise Refusal(EX_GRAPH, f"shared graph failed (rc={proc.returncode}); see {raw_dir}")
    shutil.copyfile(generic_jsonl, raw_dir / "generic-ledger.jsonl")  # raw primary output, preserved
    return generic_jsonl


# --- reconcile + invariants ------------------------------------------------------


def reconcile_and_record(ad, record: dict, generic_jsonl: Path, out_dir: Path, resolutions_path: Path | None) -> int:
    manifest = ad.load_manifest(REPO_ROOT / record["manifest_path"])
    generic = [json.loads(line) for line in generic_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    raw_res = json.loads(resolutions_path.read_text(encoding="utf-8")) if resolutions_path else {}
    resolutions = {k: v for k, v in raw_res.items() if isinstance(v, dict)}  # "_about" and other notes are not rows
    rows = ad.reconcile(generic, manifest, REPO_ROOT, resolutions)
    by_path = {r.path: r for r in rows}
    canary = {p: {"expected": fam, "got": by_path[p].verdict if p in by_path else None} for p, fam in CANARIES.items()}
    canary_ok = all(c["got"] == c["expected"] for c in canary.values())
    unresolved = ad.unresolved(rows)

    jsonl = out_dir / f"{STEM}.jsonl"
    jsonl.write_text("".join(r.model_dump_json() + "\n" for r in rows), encoding="utf-8")
    md = ["# Chaplain disposition census (FR-1012 Step 0)", "", f"Source `{record['source_sha'][:8]}` · {len(rows)} rows · unresolved {len(unresolved)} · canaries {'pass' if canary_ok else 'FAIL'}", "",
          "| path | kind | verdict | manual_review | reqs | reason |", "|---|---|---|---|---|---|"]
    md += [f"| `{r.path}` | {r.kind} | {r.verdict} | {'yes' if r.manual_review else ''} | {', '.join(r.reqs)} | {r.reason.replace('|', '/')} |" for r in rows]
    (out_dir / f"{STEM}.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    record.update(
        finished_at=datetime.now(UTC).isoformat(),
        generic_ledger_sha256=_sha256_file(generic_jsonl),
        disposition_sha256=_sha256_file(jsonl),
        counts_out={"delete": sum(r.verdict == "delete" for r in rows), "retire": sum(r.verdict == "retire" for r in rows), "keep": sum(r.verdict == "keep" for r in rows), "unresolved": len(unresolved)},
        unresolved=unresolved,
        resolutions_file=str(resolutions_path) if resolutions_path else None,
        resolutions_confirmed=sorted(p for p, r in resolutions.items() if r.get("confirmed") is True),
        resolutions_pending_confirmation=sorted(p for p, r in resolutions.items() if r.get("confirmed") is not True),
        canaries=canary,
        invariants={
            "1_each_item_one_payload": len(manifest) == record["counts"]["items"],
            "2_each_payload_one_result": len(generic) == len(manifest),
            # one reduction batch: every generic row came from the single preserved ledger of this run
            "3_one_reduction_batch": len({g.get("model") for g in generic}) == 1 and len({g.get("prompt_version") for g in generic}) == 1,
            "4_model_ids_reconciled": {g["item_ref"] for g in generic} == set(manifest),
            # counts in code: the reconciled verdict counts sum to the manifest size (nothing counted by the model)
            "5_counts_in_code": sum(1 for r in rows) == len(manifest),
            "6_provenance_recorded": all(record.get(k) for k in ("provider", "model", "source_sha", "chaplain_tree_sha", "run_id", "manifest_sha256")),
            # no silent drop: every abstained / failed / manual-labelled generic row ended as a confirmed human resolution
            "7_no_silent_drop": all(
                resolutions.get(g["item_ref"], {}).get("confirmed") is True
                for g in generic
                if g.get("abstained") or g.get("judgement") in ("abstain", "manual_review")
            ),
            "8_withheld_canaries_match": canary_ok,
        },
        human_raw_read="PENDING — a named human must read docs/census/chaplain-test-disposition.raw/ and record name+date here before the rows are trusted",
    )
    (out_dir / f"{STEM}.run.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    if not canary_ok:
        raise Refusal(EX_CONTRACT, f"withheld canary mismatch: {canary}")
    if unresolved:
        print(f"chaplain_census: {len(unresolved)} manual_review row(s) — enforcement stops until FR-1012 records resolutions:", *unresolved, sep="\n  ")
        return EX_UNRESOLVED
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preflight", action="store_true", help="freeze the manifest and run every refusal; make no provider call")
    ap.add_argument("--reconcile-only", action="store_true", help="re-reconcile the preserved raw generic ledger of the recorded run; no provider call")
    ap.add_argument("--resolutions", type=Path, help="JSON {path: {verdict, reason, resolved_by, date, confirmed}} — only confirmed:true counts as human")
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--yamlgraph-bin", default=os.environ.get("YAMLGRAPH_BIN") or shutil.which("yamlgraph"))
    args = ap.parse_args(argv)
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    ad = _adapters()
    try:
        if args.reconcile_only:
            record = json.loads((out_dir / f"{STEM}.run.json").read_text(encoding="utf-8"))
            manifest_path = REPO_ROOT / record["manifest_path"]
            if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != record["manifest_sha256"]:
                raise Refusal(EX_CONTRACT, "manifest on disk differs from the recorded run's manifest_sha256 — re-run the census")
            raw = out_dir / f"{STEM}.raw" / "generic-ledger.jsonl"
            if not raw.is_file():
                raise Refusal(EX_CONTRACT, f"no preserved raw ledger at {raw}")
            record["reconcile_only_at"] = datetime.now(UTC).isoformat()
            return reconcile_and_record(ad, record, raw, out_dir, args.resolutions)
        record = preflight(ad, out_dir)
        print(f"chaplain_census: preflight ok — {record['counts']} manifest {record['manifest_sha256'][:12]}")
        if args.preflight:
            return 0
        if not args.yamlgraph_bin:
            raise Refusal(EX_UNAVAILABLE, "no yamlgraph executor: set YAMLGRAPH_BIN or put yamlgraph on PATH")
        generic = run_graph(record, out_dir, args.yamlgraph_bin)
        return reconcile_and_record(ad, record, generic, out_dir, args.resolutions)
    except Refusal as exc:
        print(f"chaplain_census: {exc}", file=sys.stderr)
        return exc.code
    except ad.ReconcileError as exc:
        print(f"chaplain_census: reconciliation refused: {exc}", file=sys.stderr)
        return EX_CONTRACT


if __name__ == "__main__":
    sys.exit(main())
