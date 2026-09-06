"""Chaplain disposition census adapters (FR-1012 Step 0, R-2/R-3 both rounds).

Slot contract per FR-892: state-dict in; ``chaplain_discover`` returns the
frozen, sorted, de-duplicated item list; ``chaplain_extract`` returns one
item's payload (file text + its collector-owned facts row).

Everything the model must NOT be trusted with is computed here in code
(invariant 5): per-REQ fan-in from the pytest marker AST
(``scripts/req_coverage.py``'s extractor, never text regex), CAP module
presence, current status, SHA-256, byte counts. ``reconcile`` joins the
shared graph's generic ``LedgerRow`` output to those facts and emits the
frozen test/CAP rows, rejecting everything the judgement lists.

Only tests and CAPs are census items (PR #617 review P2).
"""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[4]

# Frozen discovery rule (FR-1012 § Step 0). Text regexes select CANDIDATES only;
# the model decides the semantics, code decides the arithmetic.
TEST_NEEDLE = re.compile(r"\.chaplain|inquisitor|watcher2?|philosopher|inbox|triage|distill|chaplain")
CAP_NEEDLE = re.compile(r"chaplain|watcher|inquisitor|philosopher|inbox|triage|distill")
LEGACY_ID_TESTS = (
    "tests/unit/test_id_registry.py",
    "tests/unit/test_fr754_id_registry_package_boundary.py",
)
# Non-census deletion set (judgement D-6): enumerated, never sent to the model.
NON_CENSUS_DELETION_SET = (
    "scripts/id_registry.py",
    "scripts/validate_id_registry.py",
    ".github/skills/chaplain-ops/",
    "scripts/chaplain-prompts/",
)
RUNTIME_ROOT = ".chaplain/"
MANIFEST_ENV = "CHAPLAIN_CENSUS_MANIFEST"
DEFAULT_MANIFEST = "docs/census/chaplain-disposition-input.jsonl"
PAYLOAD_SEPARATOR = "----- FILE TEXT -----"
LABELS = ("keep", "delete", "retire", "manual_review")


# --- git helpers -----------------------------------------------------------


def _git(root: Path, *argv: str) -> str:
    return subprocess.run(  # noqa: S603 — fixed git argv, no shell (CONF-462)
        ["git", *argv], cwd=root, capture_output=True, text=True, check=True
    ).stdout


def _ls_files(root: Path, *pathspecs: str) -> list[str]:
    return [p for p in _git(root, "ls-files", "--", *pathspecs).split("\n") if p]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8", errors="replace")


# --- discovery -------------------------------------------------------------


def discover_paths(root: Path) -> list[str]:
    """The frozen rule: candidate tests ∪ candidate CAPs ∪ legacy ID tests; sorted, unique."""
    tests = [p for p in _ls_files(root, "tests/**/*.py") if TEST_NEEDLE.search(_read(root, p))]
    caps = [p for p in _ls_files(root, "capabilities/CAP-*.yaml") if CAP_NEEDLE.search(_read(root, p))]
    legacy = [p for p in LEGACY_ID_TESTS if (root / p).is_file()]
    return sorted(set(tests) | set(caps) | set(legacy))


def _require(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


def chaplain_discover(state: dict[str, Any]) -> list[str]:
    """Slot ``discover``. source = repository root path (the frozen tree is HEAD there)."""
    root = Path(_require(state, "source")).resolve()
    if not (root / ".git").exists():
        raise NotADirectoryError(f"chaplain_discover: not a git checkout: {root}")
    items = discover_paths(root)
    if not items:
        raise ValueError("chaplain_discover: the frozen rule matched nothing")
    return items


# --- facts (collector-owned) ----------------------------------------------


def _req_extractor():
    spec = importlib.util.spec_from_file_location("req_coverage", REPO_ROOT / "scripts" / "req_coverage.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.extract_req_markers


def marker_reqs(root: Path, test_paths: list[str]) -> dict[str, list[str]]:
    """path -> sorted REQ ids, from the pytest marker AST (never text regex)."""
    extract = _req_extractor()
    return {p: sorted(extract(root / p).keys()) for p in test_paths}


def kind_of(path: str) -> Literal["test", "cap"]:
    return "cap" if path.startswith("capabilities/") else "test"


def build_manifest(root: Path, source_sha: str, items: list[str] | None = None) -> list[dict[str, Any]]:
    """Frozen input manifest rows. Fan-in counts tests OUTSIDE the candidate set (FR-1012 R-1)."""
    items = items if items is not None else discover_paths(root)
    candidate = set(items)
    all_tests = _ls_files(root, "tests/**/*.py")
    reqs_by_test = marker_reqs(root, all_tests)
    outside_by_req: dict[str, set[str]] = {}
    for test, reqs in reqs_by_test.items():
        if test in candidate:
            continue
        for req in reqs:
            outside_by_req.setdefault(req, set()).add(test)

    rows: list[dict[str, Any]] = []
    for path in items:
        data = (root / path).read_bytes()
        row: dict[str, Any] = {
            "source_sha": source_sha,
            "path": path,
            "kind": kind_of(path),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        if row["kind"] == "test":
            reqs = reqs_by_test.get(path, [])
            row["reqs"] = reqs
            row["fan_in_by_req"] = {r: len(outside_by_req.get(r, ())) for r in reqs}
        else:
            cap = yaml.safe_load(data.decode("utf-8")) or {}
            reqs = sorted({r["id"] for r in cap.get("requirements", []) if isinstance(r, dict) and "id" in r})
            modules = sorted(
                set(cap.get("modules") or [])
                | {m for r in cap.get("requirements", []) if isinstance(r, dict) for m in r.get("modules") or []}
            )
            row.update(
                cap_id=str(cap.get("id", "")),
                current_status=str(cap.get("status", "active")),
                reqs=reqs,
                modules=modules,
                modules_present={m: (root / m).exists() for m in modules},
                surviving_witnesses_by_req={r: sorted(outside_by_req.get(r, ())) for r in reqs},
            )
        rows.append(row)
    return rows


def write_manifest(rows: list[dict[str, Any]], path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
    path.write_text(text, encoding="utf-8", newline="\n")  # LF on every host: the sha is over the bytes on disk
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(path: Path) -> dict[str, dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {r["path"]: r for r in rows}


# --- extraction ------------------------------------------------------------


def payload_for(root: Path, facts: dict[str, Any]) -> str:
    """Deterministic payload: facts header + file text. The reconciler rebuilds it to check spans."""
    header = {k: v for k, v in facts.items() if k not in {"source_sha", "sha256"}}
    return (
        "Facts (computed by code; treat as ground truth):\n"
        + json.dumps(header, sort_keys=True, indent=1)
        + "\n"
        + PAYLOAD_SEPARATOR
        + "\n"
        + _read(root, facts["path"])
    )


def chaplain_extract(state: dict[str, Any]) -> str:
    """Slot ``extract``. item = repo-relative path; facts come from the frozen manifest."""
    item = _require(state, "item")
    manifest = Path(os.environ.get(MANIFEST_ENV, str(REPO_ROOT / DEFAULT_MANIFEST)))
    rows = load_manifest(manifest)
    if item not in rows:
        raise KeyError(f"chaplain_extract: {item} is not in the frozen manifest {manifest}")
    root = manifest.resolve().parents[2] if manifest.is_absolute() else REPO_ROOT
    return payload_for(root, rows[item])


# --- reconciliation ----------------------------------------------------------


class TestRow(BaseModel):
    path: str
    kind: Literal["test"] = "test"
    verdict: Literal["keep", "delete"]
    reason: str
    reqs: list[str]
    fan_in_by_req: dict[str, int]
    cites: list[str]
    manual_review: bool
    confidence: float = Field(ge=0, le=1)


class CapRow(BaseModel):
    path: str
    cap_id: str
    kind: Literal["cap"] = "cap"
    current_status: str
    verdict: Literal["keep", "retire"]
    reason: str
    reqs: list[str]
    modules: list[str]
    modules_present: dict[str, bool]
    surviving_witnesses_by_req: dict[str, list[str]]
    cites: list[str]
    manual_review: bool
    confidence: float = Field(ge=0, le=1)


class ReconcileError(ValueError):
    """A fail-closed reconciliation failure (invariants 2, 4, 7; illegal cells)."""


def _norm(text: str) -> str:
    return " ".join(text.split())


def _runtime_owned(module: str) -> bool:
    return module.startswith(RUNTIME_ROOT) or any(
        module == m.rstrip("/") or module.startswith(m) for m in NON_CENSUS_DELETION_SET
    )


def _check_generic(generic: list[dict[str, Any]], manifest: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_ref: dict[str, dict[str, Any]] = {}
    for g in generic:
        ref = g.get("item_ref")
        if ref not in manifest:
            raise ReconcileError(f"unknown item_ref in generic ledger: {ref!r}")
        if ref in by_ref:
            raise ReconcileError(f"duplicate item_ref in generic ledger: {ref}")
        by_ref[ref] = g
    missing = sorted(set(manifest) - set(by_ref))
    if missing:
        raise ReconcileError(f"manifest rows without a generic row: {missing}")
    return by_ref


def _label(g: dict[str, Any], facts: dict[str, Any], root: Path, resolutions: dict[str, Any]) -> tuple[str, str, bool, float]:
    """Return (verdict, reason, manual_review, confidence) for one row, or raise.

    A resolution counts as human only when ``confirmed`` is true; an unconfirmed
    (proposed) resolution keeps the row ``manual_review`` and carries the proposal
    in the reason so the operator sees what to confirm.
    """
    path = facts["path"]
    resolved = resolutions.get(path)
    if resolved and resolved.get("confirmed") is True:
        return resolved["verdict"], f"human resolution ({resolved.get('resolved_by', '?')}, {resolved.get('date', '?')}): {resolved['reason']}", False, 1.0
    proposal = f"; PROPOSED {resolved['verdict']}: {resolved['reason']} (unconfirmed)" if resolved else ""
    if g.get("abstained") or g.get("judgement") == "abstain" or (g.get("repaired") and g.get("judgement") == "abstain"):
        if resolved:
            return "keep", f"model abstained ({g.get('abstain_reason', '')!r}){proposal}", True, 0.0
        raise ReconcileError(f"{path}: abstained/demoted/failed row without human resolution ({g.get('abstain_reason', '')!r})")
    label = str(g.get("judgement", "")).strip()
    legal = {"test": {"keep", "delete", "manual_review"}, "cap": {"keep", "retire", "manual_review"}}[facts["kind"]]
    if label not in legal:
        raise ReconcileError(f"{path}: illegal verdict {label!r} for kind {facts['kind']}")
    span = str(g.get("evidence_span", ""))
    if not span or _norm(span) not in _norm(payload_for(root, facts)):
        if resolved:
            return "keep", f"model {label} with an inexact evidence span{proposal}", True, float(g.get("confidence", 0))
        raise ReconcileError(f"{path}: evidence_span is not an exact span of the item payload")
    if label == "manual_review" or resolved:
        return "keep", f"model {label}; span: {span}{proposal}", True, float(g.get("confidence", 0))
    return label, f"model: {span}", False, float(g.get("confidence", 0))


def reconcile(
    generic: list[dict[str, Any]],
    manifest: dict[str, dict[str, Any]],
    root: Path,
    resolutions: dict[str, Any] | None = None,
) -> list[TestRow | CapRow]:
    """Deterministic join + the two rubric rules code can check (FR-1012 § Step 0)."""
    resolutions = resolutions or {}
    by_ref = _check_generic(generic, manifest)
    labels = {p: _label(by_ref[p], facts, root, resolutions) for p, facts in manifest.items()}
    caps = [p for p, f in manifest.items() if f["kind"] == "cap"]
    tests = [p for p, f in manifest.items() if f["kind"] == "test"]

    confirmed = {p for p, r in resolutions.items() if r.get("confirmed") is True}
    for _ in range(3):  # fixpoint over the two cross-row rules
        retire_reqs = {r for p in caps if labels[p][0] == "retire" for r in manifest[p]["reqs"]}
        for p in tests:
            verdict, reason, manual, conf = labels[p]
            if verdict != "delete" or p in confirmed:
                continue
            orphaned = [r for r in manifest[p]["reqs"] if manifest[p]["fan_in_by_req"].get(r, 0) == 0 and r not in retire_reqs]
            if orphaned:
                labels[p] = ("keep", f"delete would orphan {orphaned} (fan-in 0, no retiring CAP); {reason}", True, conf)
        kept_test_reqs = {r for p in tests if labels[p][0] == "keep" for r in manifest[p]["reqs"]}
        deleted_tests = {p for p in tests if labels[p][0] == "delete"}
        for p in caps:
            verdict, reason, manual, conf = labels[p]
            if verdict != "retire" or p in confirmed:
                continue
            f = manifest[p]
            live = [r for r in f["reqs"] if f["surviving_witnesses_by_req"].get(r) or r in kept_test_reqs]
            # a CAP's own witness test that this census deletes is not a foreign module
            foreign = [m for m, present in f["modules_present"].items() if present and not _runtime_owned(m) and m not in deleted_tests]
            if live or foreign:
                labels[p] = ("keep", f"mixed CAP: live REQs {live}, non-runtime modules {foreign}; {reason}", True, conf)

    rows: list[TestRow | CapRow] = []
    for p, f in manifest.items():
        verdict, reason, manual, conf = labels[p]
        cites = [p] + (["FR-1012 human resolution"] if p in resolutions else [])
        if f["kind"] == "test":
            rows.append(TestRow(path=p, verdict=verdict, reason=reason, reqs=f["reqs"], fan_in_by_req=f["fan_in_by_req"], cites=cites, manual_review=manual, confidence=conf))
        else:
            rows.append(CapRow(path=p, cap_id=f["cap_id"], current_status=f["current_status"], verdict=verdict, reason=reason, reqs=f["reqs"], modules=f["modules"], modules_present=f["modules_present"], surviving_witnesses_by_req=f["surviving_witnesses_by_req"], cites=cites, manual_review=manual, confidence=conf))
    return rows


def unresolved(rows: list[TestRow | CapRow]) -> list[str]:
    return [r.path for r in rows if r.manual_review]
