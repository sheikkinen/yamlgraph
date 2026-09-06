"""FR-1012 Step 2 — the Chaplain runtime is gone from main; FR-1016 — its one-shot tooling too (REQ-YG-666, CAP-264).

RED on the pre-removal tree, GREEN after the atomic removal commit. Every
assertion names a state the census (docs/census/chaplain-test-disposition.jsonl)
or the frozen non-census deletion set authorises; nothing here decides what
to delete — it only witnesses that exactly that was done.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
CENSUS = REPO / "docs/census/chaplain-test-disposition.jsonl"
ARCHIVE_NOTE = REPO / "docs/archive/chaplain.md"
JOURNAL = REPO / "docs/census/chaplain-archive.run.json"

# process: reads docs/, capabilities/, scripts/ and runs now.py (FR-756)
pytestmark = pytest.mark.process

NON_CENSUS_DELETIONS = [
    ".chaplain",
    ".github/skills/chaplain-ops",
    "scripts/chaplain-prompts",
    "scripts/id_registry.py",
    "scripts/validate_id_registry.py",
]


def _census_rows() -> list[dict]:
    return [
        json.loads(line)
        for line in CENSUS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _tracked(path: str) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "--", path],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [p for p in out.splitlines() if p]


@pytest.mark.req("REQ-YG-666")
@pytest.mark.parametrize("path", NON_CENSUS_DELETIONS)
def test_non_census_deletion_set_is_gone(path):
    assert not _tracked(path), f"{path} still tracked"
    assert not (REPO / path).exists() or path == ".chaplain", f"{path} still present"


@pytest.mark.req("REQ-YG-666")
def test_validate_id_registry_hook_removed():
    config = (REPO / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "validate-id-registry" not in config
    assert "validate_id_registry" not in config


@pytest.mark.req("REQ-YG-666")
def test_gitignore_has_no_chaplain_entries():
    lines = (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert [ln for ln in lines if ".chaplain" in ln] == []


@pytest.mark.req("REQ-YG-666")
def test_every_census_delete_row_is_gone():
    deletes = [
        r["path"]
        for r in _census_rows()
        if r["kind"] == "test" and r["verdict"] == "delete"
    ]
    assert len(deletes) == 41
    present = [p for p in deletes if (REPO / p).exists() or _tracked(p)]
    assert present == [], f"census delete rows still present: {present}"


@pytest.mark.req("REQ-YG-666")
def test_every_census_keep_row_is_still_there():
    # The census kept its own test file (correct at census time); FR-1016 retired the
    # tooling afterwards by a separate judgement, so that set is excluded here while the
    # census record itself stays byte-identical (FR-1016 AC-07).
    keeps = [
        r["path"]
        for r in _census_rows()
        if r["verdict"] == "keep" and r["path"] not in FR1016_TOOLING_DELETIONS
    ]
    missing = [p for p in keeps if not (REPO / p).exists()]
    assert missing == [], f"census keep rows missing: {missing}"


@pytest.mark.req("REQ-YG-666")
def test_every_census_retire_cap_is_retired_by_fr1012():
    retire = [
        r for r in _census_rows() if r["kind"] == "cap" and r["verdict"] == "retire"
    ]
    assert len(retire) == 24
    wrong = []
    for r in retire:
        cap = yaml.safe_load((REPO / r["path"]).read_text(encoding="utf-8"))
        if cap.get("status") != "retired" or cap.get("retired_by") != "FR-1012":
            wrong.append(
                f"{r['cap_id']}: status={cap.get('status')} retired_by={cap.get('retired_by')}"
            )
    assert wrong == [], "\n".join(wrong)


@pytest.mark.req("REQ-YG-666")
def test_no_kept_cap_lists_a_chaplain_module():
    keeps = [
        r["path"]
        for r in _census_rows()
        if r["kind"] == "cap" and r["verdict"] == "keep"
    ]
    offenders = []
    for p in keeps:
        cap = yaml.safe_load((REPO / p).read_text(encoding="utf-8"))
        modules = set(cap.get("modules") or []) | {
            m for req in cap.get("requirements", []) for m in req.get("modules") or []
        }
        bad = [
            m
            for m in modules
            if m.startswith(
                (
                    ".chaplain",
                    "examples/philosopher",
                    ".github/skills/chaplain-ops",
                    "scripts/chaplain-prompts",
                    "scripts/id_registry",
                    "scripts/validate_id_registry",
                )
            )
        ]
        if bad:
            offenders.append(f"{p}: {bad}")
    assert offenders == [], "\n".join(offenders)


@pytest.mark.req("REQ-YG-666")
def test_archive_note_records_the_three_identities():
    assert ARCHIVE_NOTE.is_file(), "docs/archive/chaplain.md missing"
    note = ARCHIVE_NOTE.read_text(encoding="utf-8")
    journal = json.loads(JOURNAL.read_text(encoding="utf-8"))
    for key in ("pre", "split", "archive_head"):
        assert journal[key] in note, f"archive note lacks {key} {journal[key]}"
    assert "chaplain-archive" in note and "sheikkinen/yamlgraph-chaplain" in note
    assert "not a runnable distribution" in note


@pytest.mark.req("REQ-YG-666")
def test_now_py_prints_no_chaplain():
    proc = subprocess.run(
        [sys.executable, "scripts/vscode/now.py"],
        cwd=REPO,
        capture_output=True,
        text=True,
        env={
            "PYTHONUTF8": "1",
            "PATH": __import__("os").environ.get("PATH", ""),
            "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", ""),
        },
    )
    assert ".chaplain" not in proc.stdout, [
        ln for ln in proc.stdout.splitlines() if ".chaplain" in ln
    ]


@pytest.mark.req("REQ-YG-666")
def test_cap_264_now_claims_the_end_state():
    cap = (REPO / "capabilities/CAP-264-chaplain-runtime-retired.yaml").read_text(
        encoding="utf-8"
    )
    assert re.search(r"absent from main", cap), (
        "CAP-264 must claim the runtime is absent from main once it is"
    )


# --- FR-1016: the one-shot tooling that executed FR-1012 is gone too -------

FR1016_TOOLING_DELETIONS = [
    "scripts/chaplain_census.py",
    "scripts/chaplain_archive.sh",
    "scripts/chaplain_postmerge_witness.sh",
    "examples/demos/corpus_census/adapters/chaplain_adapters.py",
    "examples/demos/corpus_census/adapters/chaplain-discover.tool.yaml",
    "examples/demos/corpus_census/adapters/chaplain-extract.tool.yaml",
    "examples/demos/corpus_census/adapters/chaplain_rubric.md",
    "tests/unit/test_fr1012_chaplain_census.py",
    "tests/unit/test_fr1012_chaplain_archive.py",
    "tests/unit/test_fr1012_chaplain_postmerge_witness.py",
]

WITNESS = "tests/unit/test_fr1012_chaplain_removed.py"


@pytest.mark.req("REQ-YG-666")
@pytest.mark.parametrize("path", FR1016_TOOLING_DELETIONS)
def test_fr1016_one_shot_tooling_is_gone(path):
    assert not _tracked(path), f"{path} still tracked"
    assert not (REPO / path).exists(), f"{path} still present"


@pytest.mark.req("REQ-YG-666")
def test_fr1016_cap_264_claims_only_the_end_state():
    path = REPO / "capabilities/CAP-264-chaplain-runtime-retired.yaml"
    text = path.read_text(encoding="utf-8")
    cap = yaml.safe_load(text)
    assert cap["fr"] == "FR-1012, FR-1016"
    assert cap["modules"] == [WITNESS]
    assert [r["modules"] for r in cap["requirements"]] == [[WITNESS]]
    for name in (
        "chaplain_census",
        "chaplain_archive",
        "chaplain_postmerge",
        "chaplain_adapters",
        "chaplain_rubric",
    ):
        assert name not in text, f"CAP-264 still names deleted tooling: {name}"
    for identity in ("0184a73d", "b31f5849", "cf30d87f", "absent from main"):
        assert identity in text, f"CAP-264 lost the end-state claim: {identity}"
