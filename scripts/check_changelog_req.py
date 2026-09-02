#!/usr/bin/env python3
"""Validate changelog fragment `req:` front-matter against capabilities registry.

FR-247: Changelog REQ Cross-Validation Gate.

Phase 1 — Mechanical pre-filter (fast, free):
  - Parse YAML front-matter → extract req:
  - Skip fragments with no req: field
  - Verify req: ID exists in capabilities/CAP-*.yaml
  - Single-REQ CAP → mechanical match (always passes if ID found)
  - Multi-REQ CAP → deferred to Phase 2 (LLM)

Phase 2 — LLM semantic cross-check (Haiku):
  - Invoked only for multi-REQ CAPs
  - Uses yamlgraph graph run graphs/enforcement/changelog-req-check.yaml
  - Skipped with --skip-llm flag

Usage:
    python scripts/check_changelog_req.py                  # report only
    python scripts/check_changelog_req.py --strict         # exit 1 on failure
    python scripts/check_changelog_req.py --skip-llm       # mechanical only
    python scripts/check_changelog_req.py --verbose        # show reasoning
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CAPABILITIES_DIR = REPO_ROOT / "capabilities"
CHANGELOG_DIR = REPO_ROOT / "changelog" / "unreleased"


@dataclass
class FragmentReq:
    """Parsed req field from a changelog fragment."""

    req_ids: set[str]
    body: str


@dataclass
class ValidationResult:
    """Result of validating a single changelog fragment."""

    filepath: Path
    status: str  # "pass", "fail", "skipped", "deferred"
    reason: str


def parse_fragment_req(filepath: Path) -> FragmentReq | None:
    """Extract req IDs and body from a changelog fragment's YAML front-matter.

    Returns None if the fragment has no req: field or no valid front-matter.
    """
    content = filepath.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return None

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    try:
        front_matter = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None

    if not front_matter or not isinstance(front_matter, dict):
        return None

    raw_req = front_matter.get("req")
    if not raw_req:
        return None

    req_ids = {r.strip() for r in str(raw_req).split(",") if r.strip()}
    body = parts[2].strip()
    return FragmentReq(req_ids=req_ids, body=body)


def load_req_to_cap_index(capabilities_dir: Path) -> dict[str, str]:
    """Build REQ-ID → CAP-ID mapping from capability YAML files.

    Uses direct id: field lookup in requirements arrays.
    Does NOT use the lossy fr: field (FR-247 design decision).
    """
    index: dict[str, str] = {}

    if not capabilities_dir.exists():
        return index

    for filepath in sorted(capabilities_dir.glob("CAP-*.yaml")):
        with open(filepath, encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError:
                continue

        if not data or not isinstance(data, dict):
            continue

        cap_id = data.get("id", "")
        for req in data.get("requirements", []):
            req_id = req.get("id", "")
            if req_id:
                index[req_id] = cap_id

    return index


def find_owning_cap(
    req_id: str,
    index: dict[str, str],
    capabilities_dir: Path,
) -> tuple[str, list[str]] | None:
    """Find the CAP that owns a requirement and return all its REQ IDs.

    Returns (cap_id, [all_req_ids_in_cap]) or None if not found.
    """
    cap_id = index.get(req_id)
    if not cap_id:
        return None

    # Load the full CAP to get all its REQ IDs
    for filepath in capabilities_dir.glob("CAP-*.yaml"):
        with open(filepath, encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError:
                continue
        if data and data.get("id") == cap_id:
            all_reqs = [r["id"] for r in data.get("requirements", []) if r.get("id")]
            return cap_id, all_reqs

    return None


def _load_req_descriptions(capabilities_dir: Path, cap_id: str) -> dict[str, str]:
    """Load requirement descriptions from a specific CAP file."""
    for filepath in capabilities_dir.glob("CAP-*.yaml"):
        with open(filepath, encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError:
                continue
        if data and data.get("id") == cap_id:
            return {
                r["id"]: r.get("description", "")
                for r in data.get("requirements", [])
                if r.get("id")
            }
    return {}


def _run_llm_check(
    fragment_body: str,
    claimed_req_id: str,
    claimed_req_description: str,
    candidate_reqs: str,
    cap_id: str,
    *,
    verbose: bool = False,
) -> ValidationResult | None:
    """Run the LLM semantic cross-check via yamlgraph graph.

    Returns ValidationResult or None if the graph cannot be executed.
    """
    graph_path = REPO_ROOT / "graphs" / "enforcement" / "changelog-req-check.yaml"
    if not graph_path.exists():
        return None

    try:
        cmd = [
            sys.executable,
            "-m",
            "yamlgraph",
            "graph",
            "run",
            str(graph_path),
            "--var",
            f"changelog_body={fragment_body}",
            "--var",
            f"claimed_req_id={claimed_req_id}",
            "--var",
            f"claimed_req_description={claimed_req_description}",
            "--var",
            f"candidate_reqs={candidate_reqs}",
            "--var",
            f"cap_id={cap_id}",
            "--full",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None
        # Parse the verdict from stdout (structured output)
        output = result.stdout.strip()
        if verbose:
            print(f"  LLM output: {output}")
        # The graph returns structured output with match/correct_req/reasoning
        if "match" in output.lower() and "true" in output.lower():
            return ValidationResult(
                filepath=Path("llm"),
                status="pass",
                reason="LLM confirmed match",
            )
        return ValidationResult(
            filepath=Path("llm"),
            status="fail",
            reason=f"LLM rejected match: {output[:200]}",
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def validate_fragment(
    filepath: Path,
    index: dict[str, str],
    capabilities_dir: Path,
    *,
    skip_llm: bool = False,
    verbose: bool = False,
) -> ValidationResult:
    """Validate a single changelog fragment's req: field.

    Returns a ValidationResult with status:
    - "pass": req is valid and mechanically verified
    - "fail": req is invalid (phantom, unparseable, etc.)
    - "skipped": fragment has no req field
    - "deferred": multi-REQ CAP, needs LLM (skipped with --skip-llm)
    """
    # Try to parse front-matter
    content = filepath.read_text(encoding="utf-8")
    if not content.startswith("---"):
        # No front-matter at all — skip (not a properly formatted fragment)
        return ValidationResult(
            filepath=filepath, status="skipped", reason="no front-matter"
        )

    parts = content.split("---", 2)
    if len(parts) < 3:
        return ValidationResult(
            filepath=filepath, status="skipped", reason="no front-matter"
        )

    try:
        front_matter = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return ValidationResult(
            filepath=filepath,
            status="fail",
            reason=f"YAML parse error in front-matter: {e}",
        )

    if not front_matter or not isinstance(front_matter, dict):
        return ValidationResult(
            filepath=filepath, status="skipped", reason="empty front-matter"
        )

    raw_req = front_matter.get("req")
    if not raw_req:
        return ValidationResult(
            filepath=filepath, status="skipped", reason="no req field"
        )

    # Parse req IDs
    req_ids = {r.strip() for r in str(raw_req).split(",") if r.strip()}
    body = parts[2].strip()

    # Validate each req ID
    errors: list[str] = []
    deferred: list[str] = []

    for req_id in sorted(req_ids):
        cap_info = find_owning_cap(req_id, index, capabilities_dir)
        if cap_info is None:
            errors.append(f"{req_id}: phantom REQ — not found in any capability")
            continue

        cap_id, all_reqs = cap_info

        if len(all_reqs) == 1:
            # Single-REQ CAP — mechanical match (tautological: found via index)
            if verbose:
                print(f"  ✅ {req_id} → {cap_id} (single-REQ, mechanical pass)")
            continue

        # Multi-REQ CAP — need LLM to verify content match
        if skip_llm:
            deferred.append(f"{req_id} in {cap_id} ({len(all_reqs)} REQs)")
            if verbose:
                print(f"  ⏭️  {req_id} → {cap_id} ({len(all_reqs)} REQs, LLM skipped)")
            continue

        # Run LLM check
        req_descriptions = _load_req_descriptions(capabilities_dir, cap_id)
        claimed_desc = req_descriptions.get(req_id, "")
        candidates = "\n".join(
            f"- {rid}: {req_descriptions.get(rid, '')}" for rid in all_reqs
        )
        llm_result = _run_llm_check(
            fragment_body=body,
            claimed_req_id=req_id,
            claimed_req_description=claimed_desc,
            candidate_reqs=candidates,
            cap_id=cap_id,
            verbose=verbose,
        )
        if llm_result is None:
            deferred.append(f"{req_id} in {cap_id} (LLM unavailable)")
        elif llm_result.status == "fail":
            errors.append(f"{req_id}: {llm_result.reason}")
        elif verbose:
            print(f"  ✅ {req_id} → {cap_id} (LLM confirmed)")

    if errors:
        return ValidationResult(
            filepath=filepath,
            status="fail",
            reason="; ".join(errors),
        )

    if deferred:
        return ValidationResult(
            filepath=filepath,
            status="deferred",
            reason="; ".join(deferred),
        )

    return ValidationResult(
        filepath=filepath, status="pass", reason="all REQs verified"
    )


def main() -> int:
    """Run the changelog REQ cross-validation gate."""
    parser = argparse.ArgumentParser(
        description="Validate changelog fragment req: values against capabilities registry"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Exit non-zero on any failure"
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Run mechanical checks only, skip LLM semantic check",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print detailed reasoning"
    )
    args = parser.parse_args()

    # Build REQ → CAP index
    index = load_req_to_cap_index(CAPABILITIES_DIR)
    if not index:
        print("⚠️  No capabilities found — skipping validation")
        return 0

    # Scan changelog fragments
    if not CHANGELOG_DIR.exists():
        print("⚠️  No changelog/unreleased/ directory — skipping")
        return 0

    fragments = sorted(CHANGELOG_DIR.glob("*.md"))
    if not fragments:
        print("⏭️  No changelog fragments to validate")
        return 0

    passed = 0
    failed = 0
    skipped = 0
    deferred_count = 0
    failures: list[str] = []

    for frag_path in fragments:
        result = validate_fragment(
            frag_path,
            index,
            CAPABILITIES_DIR,
            skip_llm=args.skip_llm,
            verbose=args.verbose,
        )

        if result.status == "pass":
            passed += 1
            if args.verbose:
                print(f"✅ {frag_path.name}: {result.reason}")
        elif result.status == "fail":
            failed += 1
            failures.append(f"❌ {frag_path.name}: {result.reason}")
            print(f"❌ {frag_path.name}: {result.reason}")
        elif result.status == "deferred":
            deferred_count += 1
            if args.verbose:
                print(f"⏭️  {frag_path.name}: {result.reason}")
        else:
            skipped += 1

    # Summary
    total = passed + failed + skipped + deferred_count
    print(
        f"\nChangelog REQ validation: {passed} passed, {failed} failed, "
        f"{skipped} skipped, {deferred_count} deferred (of {total} fragments)"
    )

    if failures and args.strict:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
