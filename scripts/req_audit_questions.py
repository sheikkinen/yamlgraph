#!/usr/bin/env python3
"""Construct requirement-witness audit question files (FR-851, no LLM).

Deterministic constructor: walks the requirements-test-code mapping
(shared coverage_contexts boundary + req_coverage marker walker) and
emits one frozen-schema JSON question per registry requirement plus
token-budgeted batches for the audit graph
(examples/demos/req_witness_audit/).

Usage:
    python scripts/req_audit_questions.py --out tmp/req-audit/
    python scripts/req_audit_questions.py --out tmp/req-audit/ \
        --max-tokens 8000
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coverage_contexts import (  # noqa: E402  # CONF-413
    RESOLUTION_CLASSES,
    derive_resolution,
    load_coverage_contexts,
)
from req_coverage import (  # noqa: E402  # CONF-410
    CAPABILITIES_DIR,
    FRAMEWORK_TEST_DIRS,
    _load_req_descriptions,
    extract_req_markers,
)

__all__ = ["RESOLUTION_CLASSES", "derive_resolution"]  # shared-truth re-exports

REPO_ROOT = Path(__file__).resolve().parent.parent

FIXED_QUESTION = (
    "Are requirement, test, and code properly covered — what would improve the witness?"
)
# chars/4: documented approximation, deterministic by construction (R-4)
TOKEN_DIVISOR = 4
DEFAULT_MAX_TOKENS = 8000
SOURCE_EXCERPT_LINES = 40


def estimate_tokens(text: str) -> int:
    """Deterministic token estimate: character count / 4."""
    return len(text) // TOKEN_DIVISOR


def _req_sort_key(req_id: str) -> int:
    match = re.search(r"(\d+)$", req_id)
    return int(match.group(1)) if match else 0


def build_question(
    req_id: str,
    req_text: str,
    cap_id: str,
    cap_name: str,
    declared_modules: list[str],
    tests: list[dict],
    resolved_files: list[str],
    evidence_depth: str = "names",
) -> dict:
    """Assemble one frozen-schema question payload (R-3)."""
    return {
        "req_id": req_id,
        "req_text": req_text,
        "cap_id": cap_id,
        "cap_name": cap_name,
        "declared_modules": declared_modules,
        "tests": tests,
        "resolved_files": resolved_files,
        "evidence_depth": evidence_depth,
        "question": FIXED_QUESTION,
    }


def build_batches(
    questions: list[dict], max_tokens: int = DEFAULT_MAX_TOKENS
) -> list[list[dict]]:
    """Greedy-pack questions ordered by req_id under the token budget.

    An oversized single question gets its own batch — isolated, never
    truncated (R-4).
    """
    ordered = sorted(questions, key=lambda q: _req_sort_key(q["req_id"]))
    batches: list[list[dict]] = []
    current: list[dict] = []
    current_tokens = 0
    for q in ordered:
        cost = estimate_tokens(json.dumps(q))
        if cost > max_tokens:
            if current:
                batches.append(current)
                current, current_tokens = [], 0
            batches.append([q])
            continue
        if current and current_tokens + cost > max_tokens:
            batches.append(current)
            current, current_tokens = [], 0
        current.append(q)
        current_tokens += cost
    if current:
        batches.append(current)
    return batches


def write_questions(
    questions: list[dict],
    out_dir: Path,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict[str, list[str]]:
    """Write per-REQ question files, batch files, and the manifest.

    Deterministic: sorted keys, stable ordering — byte-identical for the
    same tree (AC-03). Returns the manifest (batch id → req ids).
    """
    questions_dir = out_dir / "questions"
    batches_dir = out_dir / "batches"
    questions_dir.mkdir(parents=True, exist_ok=True)
    batches_dir.mkdir(parents=True, exist_ok=True)

    for q in questions:
        path = questions_dir / f"{q['req_id']}.json"
        path.write_text(json.dumps(q, indent=2, sort_keys=True) + "\n")

    manifest: dict[str, list[str]] = {}
    for i, batch in enumerate(build_batches(questions, max_tokens)):
        batch_id = f"batch-{i:03d}"
        manifest[batch_id] = [q["req_id"] for q in batch]
        path = batches_dir / f"{batch_id}.json"
        path.write_text(json.dumps(batch, indent=2, sort_keys=True) + "\n")

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return manifest


def _extract_test_body(test_file: Path, test_key: str) -> str:
    """Source of the test function named by *test_key* (stage 2)."""
    try:
        source = test_file.read_text()
        tree = ast.parse(source, filename=str(test_file))
    except (OSError, SyntaxError):
        return ""
    parts = test_key.split("::")
    class_name = parts[1] if len(parts) == 3 else None
    func_name = parts[-1]
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.name == func_name
            and (
                class_name is None
                or any(
                    isinstance(p, ast.ClassDef) and p.name == class_name
                    for p in ast.walk(tree)
                )
            )
        ):
            return ast.get_source_segment(source, node) or ""
    return ""


def build_stage2_question(
    question: dict, test_files: dict[str, Path], repo_root: Path
) -> dict:
    """Escalate a flagged question to bodies depth (R-3 stage 2).

    Adds test function sources and a head excerpt of each resolved file
    (first SOURCE_EXCERPT_LINES lines — module docstring, imports, and
    leading definitions).
    """
    q2 = dict(question)
    q2["evidence_depth"] = "bodies"
    bodies: dict[str, str] = {}
    for t in question["tests"]:
        test_id = t["test_id"]
        f = test_files.get(test_id)
        if f is not None:
            bodies[test_id] = _extract_test_body(f, test_id)
    q2["test_bodies"] = bodies
    excerpts: dict[str, str] = {}
    for rel in question["resolved_files"]:
        src = repo_root / rel
        if src.exists():
            lines = src.read_text().splitlines()[:SOURCE_EXCERPT_LINES]
            excerpts[rel] = "\n".join(lines)
    q2["source_excerpts"] = excerpts
    return q2


def _load_req_registry() -> dict[str, tuple[str, str, list[str]]]:
    """req_id → (cap_id, cap_name, declared modules) from capabilities/."""
    registry: dict[str, tuple[str, str, list[str]]] = {}
    for filepath in sorted(CAPABILITIES_DIR.glob("CAP-*.yaml")):
        data = yaml.safe_load(filepath.read_text())
        if data.get("status") == "retired":
            continue
        cap_modules = data.get("modules") or []
        for req in data.get("requirements", []):
            modules = req.get("modules") or cap_modules
            registry[req["id"]] = (data["id"], data["name"], list(modules))
    return registry


def collect_questions(root: Path = REPO_ROOT) -> list[dict]:
    """Build all question payloads from the current tree (no LLM).

    Raises CoverageContextError when the .coverage instrument is missing,
    context-free, or poisoned (FR-850 AC-03 — hard refusal, never a
    silent substitute).
    """
    registry = _load_req_registry()
    descriptions = _load_req_descriptions(root)

    all_markers: dict[str, list[str]] = {}
    test_key_to_file: dict[str, Path] = {}
    for rel in FRAMEWORK_TEST_DIRS:
        test_dir = root / rel
        if not test_dir.exists():
            continue
        for filepath in sorted(test_dir.rglob("test_*.py")):
            for req, tests in extract_req_markers(filepath).items():
                all_markers.setdefault(req, []).extend(tests)
                for t in tests:
                    test_key_to_file[t] = filepath

    tagged = {t for tests in all_markers.values() for t in tests}
    coverage_map, recorded = load_coverage_contexts(root, tagged or None)

    questions: list[dict] = []
    for req_id in sorted(registry, key=_req_sort_key):
        cap_id, cap_name, modules = registry[req_id]
        tests: list[dict] = []
        resolved: set[str] = set()
        for test_key in sorted(set(all_markers.get(req_id, []))):
            cls, files = derive_resolution(
                test_key, coverage_map, recorded, test_key_to_file.get(test_key)
            )
            tests.append({"test_id": test_key, "resolution": cls})
            resolved.update(files)
        questions.append(
            build_question(
                req_id=req_id,
                req_text=descriptions.get(req_id, ""),
                cap_id=cap_id,
                cap_name=cap_name,
                declared_modules=modules,
                tests=tests,
                resolved_files=sorted(resolved),
            )
        )
    return questions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("tmp/req-audit"))
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    args = parser.parse_args()

    questions = collect_questions()
    manifest = write_questions(questions, args.out, args.max_tokens)
    print(f"✓ {len(questions)} questions, {len(manifest)} batches → {args.out}")


if __name__ == "__main__":
    main()
