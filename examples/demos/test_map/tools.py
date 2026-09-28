"""Graph tools for the FR-1137 test corpus map: freeze and publish.

The LLM stage only *claims* a description, target and type per test.
Deterministic code owns everything else: the frozen corpus, AST identity,
partitions, ceilings, reconciliation, the withheld canary, hashes, and
rendering (extract.py, reconcile.py).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import uuid
from pathlib import Path
from types import ModuleType
from typing import Any

from yamlgraph.config import DEFAULT_MODELS
from yamlgraph.utils.schema_walk import resolve_static_provider

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[2]
DEFAULT_SCOPE = "tests/unit,tests/integration"
DEFAULT_JSON = "tmp/test-map/test-map.json"
DEFAULT_MD = "tmp/test-map/test-map.md"
REJECTED_NAME = "test-map-rejected.json"
RAW_NAME = "raw-responses.jsonl"
TEMPERATURE = 0.0

# Frozen ceilings (FR-1137 § Frozen ceilings). Checked before any LLM call.
MAX_FILES = 700
MAX_SOURCE_BYTES = 6_000_000
MAX_PAYLOAD_TOKENS = 8_000
MAX_PARTITIONS = 900
MAX_CONCURRENCY = 8
CALL_TIMEOUT_S = 180
GRAPH_TIMEOUT_S = 3600


def _sibling(name: str) -> ModuleType:
    """Load a demo-local module by path; the CLI loads this file by path too."""
    spec = importlib.util.spec_from_file_location(
        f"_fr1137_{name}", DEMO_DIR / f"{name}.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"{name}.py is not loadable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_extract = _sibling("extract")
_reconcile = _sibling("reconcile")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout


def _ceiling(value: int, limit: int, what: str) -> None:
    if value > limit:
        raise ValueError(f"scope has {value} {what}, over the {limit} {what} ceiling")


def _ceilings() -> dict[str, int]:
    return {
        "files": MAX_FILES,
        "source_bytes": MAX_SOURCE_BYTES,
        "payload_tokens": MAX_PAYLOAD_TOKENS,
        "partitions": MAX_PARTITIONS,
        "concurrency": MAX_CONCURRENCY,
        "call_timeout_s": CALL_TIMEOUT_S,
        "graph_timeout_s": GRAPH_TIMEOUT_S,
    }


def freeze_corpus(state: dict[str, Any] | None = None, **kwargs: Any) -> dict:
    """Freeze a clean committed scope into rows, partitions and provenance."""
    state = state if isinstance(state, dict) else kwargs
    root = Path(state.get("root") or REPO_ROOT)
    scope = [s.strip() for s in (state.get("scope") or DEFAULT_SCOPE).split(",")]
    scope = [s for s in scope if s]
    dirty = _git(root, "status", "--porcelain", "--untracked-files=all", "--", *scope)
    if dirty.strip():
        raise ValueError(f"test scope is dirty; commit or stash first:\n{dirty}")
    commit_sha = _git(root, "rev-parse", "HEAD").strip()
    files = sorted(
        rel
        for rel in _git(root, "ls-files", "--", *scope).splitlines()
        if Path(rel).name.startswith("test_") and rel.endswith(".py")
    )
    _ceiling(len(files), MAX_FILES, "files")
    total = sum((root / rel).stat().st_size for rel in files)
    _ceiling(total, MAX_SOURCE_BYTES, "bytes")

    entries: list[dict[str, Any]] = []
    rows: list[Any] = []
    payloads: list[Any] = []
    for rel in files:
        raw = (root / rel).read_bytes()
        file_rows = _extract.extract_tests(root / rel, rel)
        payloads.extend(
            _extract.build_payloads(
                rel, raw.decode("utf-8"), file_rows, MAX_PAYLOAD_TOKENS
            )
        )
        rows.extend(file_rows)
        entries.append(
            {
                "path": rel,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
                "tests": len(file_rows),
            }
        )
    _ceiling(len(payloads), MAX_PARTITIONS, "partitions")

    listing = "".join(f"{e['path']}\t{e['sha256']}\n" for e in entries)
    provider = resolve_static_provider(None, None)
    provenance = {
        "commit_sha": commit_sha,
        "scope": scope,
        "ceilings": _ceilings(),
        "files": entries,
        "corpus_hash": hashlib.sha256(listing.encode()).hexdigest(),
        "provider": provider,
        "model": DEFAULT_MODELS.get(provider, ""),
        "temperature": TEMPERATURE,
        "counts": {
            "files": len(files),
            "tests": len(rows),
            "partitions": len(payloads),
        },
    }
    # Dict-returning python nodes merge into state; key the update explicitly.
    return {
        "corpus": {
            "provenance": provenance,
            "rows": [row.model_dump() for row in rows],
            "partitions": [payload.model_dump() for payload in payloads],
        }
    }


def _reject(path: Path, run_id: str, corpus: dict, defects: list, **raw: Any) -> None:
    report = {
        "run_id": run_id,
        "commit_sha": corpus["provenance"]["commit_sha"],
        "counts": corpus["provenance"]["counts"],
        "defects": defects,
        **raw,
    }
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    raise RuntimeError(f"test map rejected: {len(defects)} defects; see {path}")


def publish_map(state: dict[str, Any] | None = None, **kwargs: Any) -> dict:
    """Reconcile, run the canary, then write canonical artifacts or reject."""
    state = state if isinstance(state, dict) else kwargs
    corpus = state["corpus"]
    findings = list(state.get("findings") or [])
    failures = list(state.get("findings_failures") or [])
    json_path = Path(state.get("json_path") or DEFAULT_JSON)
    md_path = Path(state.get("md_path") or DEFAULT_MD)
    rejected = json_path.parent / REJECTED_NAME
    raw_path = json_path.parent / RAW_NAME
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    for stale in (json_path, md_path, rejected, raw_path):
        stale.unlink(missing_ok=True)

    run_id = state.get("run_id") or uuid.uuid4().hex
    rows, defects = _reconcile.reconcile(corpus, findings, failures)
    canary_summary: dict[str, int] = {}
    if not defects:
        canary_path = Path(state.get("canary_path") or DEMO_DIR / "canary.json")
        canary = json.loads(canary_path.read_text(encoding="utf-8"))
        canary_defects, canary_summary = _reconcile.check_canary(rows, canary)
        defects.extend(canary_defects)
    if defects:
        _reject(
            rejected, run_id, corpus, defects, raw_findings=findings, failures=failures
        )

    parts = corpus["partitions"]
    with raw_path.open("w", encoding="utf-8") as handle:
        for finding in sorted(findings, key=lambda f: f["_map_index"]):
            partition = parts[finding["_map_index"]]["partition_id"]
            handle.write(json.dumps({"partition_id": partition, **finding}) + "\n")
    blob = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    provenance = {
        **corpus["provenance"],
        "run_id": run_id,
        "artifact_hash": hashlib.sha256(blob.encode()).hexdigest(),
        "calls": {"estimated": len(parts), "actual": len(findings) + len(failures)},
        "reconciliation": {"rows": len(rows), "failed_rows": 0, "defects": 0},
        "canary": canary_summary,
    }
    doc = {"provenance": provenance, "rows": rows}
    json_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    md_path.write_text(_reconcile.render_markdown(doc), encoding="utf-8")
    return {
        "result": {
            "accepted": True,
            "json_path": str(json_path),
            "md_path": str(md_path),
            "rows": len(rows),
            "artifact_hash": provenance["artifact_hash"],
        }
    }
