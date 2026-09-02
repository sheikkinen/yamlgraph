"""FR-951 witnesses: the CLI's own output streams must declare UTF-8.

The installed console entry is invoked with the host codec restored
(``PYTHONUTF8=0``) and forced onto the streams (``PYTHONIOENCODING=cp1252``),
with stdout and stderr captured as byte pipes. An undeclared stream cannot emit
the status glyphs the CLI already prints, so the diagnostic destroys itself.
"""

import os
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GRAPH = REPO_ROOT / "tests" / "fixtures" / "fr951" / "unicode_graph.yaml"
MISSING_GRAPH = REPO_ROOT / "tests" / "fixtures" / "fr951" / "no_such_graph.yaml"

CHECK_MARK = "\u2705"
CROSS_MARK = "\u274c"
UNICODE_EXCEPTIONS = ("UnicodeDecodeError", "UnicodeEncodeError")

pytestmark = [
    pytest.mark.req("REQ-YG-638"),
    pytest.mark.skipif(
        sys.platform != "win32",
        reason="FR-951: the inherited-codec boundary only exists on Windows",
    ),
]


def _console_entry() -> Path:
    """Locate the installed ``yamlgraph`` console script."""
    name = "yamlgraph.exe" if os.name == "nt" else "yamlgraph"
    candidate = Path(sysconfig.get_path("scripts")) / name
    assert candidate.exists(), (
        f"FR-951 witness requires the installed console entry at {candidate}; "
        "run `pip install -e .`"
    )
    return candidate


def _run(*args: str) -> subprocess.CompletedProcess[bytes]:
    env = dict(os.environ)
    env["PYTHONUTF8"] = "0"
    env["PYTHONIOENCODING"] = "cp1252"
    return subprocess.run(
        [str(_console_entry()), *args],
        capture_output=True,
        cwd=REPO_ROOT,
        env=env,
        check=False,
    )


def _decoded(proc: subprocess.CompletedProcess[bytes]) -> tuple[str, str]:
    stdout = proc.stdout.decode("utf-8")
    stderr = proc.stderr.decode("utf-8")
    for stream_name, text in (("stdout", stdout), ("stderr", stderr)):
        for exception_name in UNICODE_EXCEPTIONS:
            assert exception_name not in text, (
                f"{exception_name} surfaced on {stream_name}:\n{text}"
            )
    return stdout, stderr


def test_cli_lints_unicode_graph_through_piped_streams() -> None:
    proc = _run("graph", "lint", str(GRAPH))
    stdout, stderr = _decoded(proc)
    assert proc.returncode == 0, f"stdout:\n{stdout}\nstderr:\n{stderr}"


def test_cli_stdout_carries_non_ascii_glyph() -> None:
    proc = _run("graph", "lint", str(GRAPH))
    stdout, _ = _decoded(proc)
    assert CHECK_MARK in stdout


def test_cli_stderr_carries_non_ascii_glyph() -> None:
    proc = _run("graph", "lint", "--json", str(MISSING_GRAPH))
    _, stderr = _decoded(proc)
    assert CROSS_MARK in stderr
