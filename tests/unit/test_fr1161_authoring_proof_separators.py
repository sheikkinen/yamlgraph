"""FR-1161 deviation: authoring reports written on Windows list `\\` paths.

Both sole-route checks must accept them: the FR-767 commit backstop
(`scripts/check_authoring_proof.py`) and `scripts/author.sh`'s
artifact-existence check (REQ-YG-423).
"""

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PROOF_SCRIPT = REPO / "scripts" / "check_authoring_proof.py"
AUTHOR_SH = REPO / "scripts" / "author.sh"

REPORT = """# Artifacts

- `examples\\demos\\cached_map\\graph.yaml` - the graph.
- `examples\\demos\\cached_map\\prompts\\review.yaml` - the prompt.

# Precedent
"""

pytestmark = pytest.mark.process


def _load_proof_module():
    spec = importlib.util.spec_from_file_location("check_authoring_proof", PROOF_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.req("REQ-YG-423")
def test_proof_accepts_backslash_report_paths(tmp_path, monkeypatch):
    mod = _load_proof_module()
    report = tmp_path / "report.md"
    report.write_text(REPORT, encoding="utf-8")
    monkeypatch.setattr(mod, "REPORT", report)
    monkeypatch.setattr(
        mod,
        "staged_new_files",
        lambda: [
            "examples/demos/cached_map/graph.yaml",
            "examples/demos/cached_map/prompts/review.yaml",
        ],
    )
    assert mod.main() == 0


def _bash() -> str | None:
    # Windows' bash.exe on PATH may be the WSL relay; use Git Bash or skip.
    if sys.platform == "win32":
        git_bash = Path(os.environ.get("PROGRAMFILES", "")) / "Git/bin/bash.exe"
        return str(git_bash) if git_bash.exists() else None
    return shutil.which("bash")


@pytest.mark.req("REQ-YG-423")
def test_author_sh_extracts_backslash_artifact_paths(tmp_path):
    bash = _bash()
    if bash is None:
        pytest.skip("no usable bash")
    report = tmp_path / "report.md"
    report.write_text(REPORT, encoding="utf-8")
    script = (
        f'source <(sed -n "/^artifact_candidates()/,/^}}/p" "{AUTHOR_SH.as_posix()}"); '
        f'artifact_candidates "{report.as_posix()}"'
    )
    out = subprocess.run(
        [bash, "-c", script], capture_output=True, text=True, check=True
    ).stdout.split()
    assert "examples/demos/cached_map/graph.yaml" in out
    assert "examples/demos/cached_map/prompts/review.yaml" in out
