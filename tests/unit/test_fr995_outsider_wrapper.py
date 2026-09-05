"""FR-995 outsider wrapper — behavioural contracts (REQ-YG-663), FR-1004 observation (REQ-YG-662).

No real model calls: `yamlgraph` and `gh` are replaced by fakes on PATH.
FR-1004: there is no ledger. The posted PR comment is the only durable
measurement record; the fake `gh pr comment` keeps the `--body-file` bytes so
the posted body can be asserted byte-for-byte. `OUTSIDER_LEDGER` is set in
every run to prove it has no effect.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / ".github/skills/outsider-view"
TOOLS = SKILL / "adapters/outsider_tools.py"
WRAPPER = REPO / "scripts/outsider.sh"
PY = Path(sys.executable)  # CI has no .venv; use the interpreter running the tests
FAKE_HEAD = "a" * 40
FAKE_PR_TEXT = "# T\n\nB body\n"  # what the wrapper writes from the fake `gh pr view`

pytestmark = pytest.mark.process  # runs scripts/outsider.sh with fakes on PATH (FR-756)

VALID_REPORT = """## 1. In my own words

This change adds a checker.

## 2. Could I decide whether to merge this from the description alone?

YES

It says what changed.

## 3. Words and references I could not understand

nothing

## 4. What a merge decision would still need

- [ ] Test results.
"""

_VAR_KEYS = (
    "report_path",
    "input_path",
    "model",
    "repo",
    "pr",
    "head_sha",
    "prompt_digest",
    "tool_sha",
)


@pytest.fixture(scope="module")
def script() -> str:
    return WRAPPER.read_text(encoding="utf-8")


def _fake_bin(tmp: Path, *, graph_ok: bool, comment_ok: bool, report_text: str) -> Path:
    """Fake `yamlgraph` (runs the real finalize tool on canned model text) and fake `gh`."""
    b = tmp / "bin"
    b.mkdir(parents=True)
    model_out = tmp / "model_output.md"
    model_out.write_text(report_text, encoding="utf-8")
    vars_file = tmp / "graph_vars.txt"
    # The fake consumes every --var the wrapper passes and hands them to the real tool.
    case_arms = " ".join(f'{k}=*) echo "$a" >> "{vars_file}";;' for k in _VAR_KEYS)
    yg = b / "yamlgraph"
    yg.write_text(
        "#!/usr/bin/env bash\n"
        + ("exit 1\n" if not graph_ok else "")
        + f'for a in "$@"; do case "$a" in {case_arms} esac; done\n'
        + f'"{PY}" - "{vars_file}" <<\'EOF\'\n'
        "import importlib.util, sys\n"
        f'spec = importlib.util.spec_from_file_location("ot", "{TOOLS}"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n'
        "state = dict(line.rstrip(chr(10)).split('=', 1) for line in open(sys.argv[1], encoding='utf-8') if '=' in line)\n"
        f'state["outsider_result"] = {{"output": open("{model_out}", encoding="utf-8").read()}}\n'
        "m.finalize_report(state)\n"
        "EOF\n",
        encoding="utf-8",
    )
    gh = b / "gh"
    gh.write_text(
        "#!/usr/bin/env bash\n"
        f'if [ "$1" = pr ] && [ "$2" = view ]; then echo \'{{"title":"T","body":"B body","headRefOid":"{FAKE_HEAD}"}}\'; exit 0; fi\n'
        'if [ "$1" = pr ] && [ "$2" = comment ]; then\n'
        '  for a in "$@"; do if [ -n "${BODY_NEXT:-}" ]; then cp "$a" '
        f'"{tmp}/comment-body.md"; BODY_NEXT=; fi; [ "$a" = --body-file ] && BODY_NEXT=1; done\n'
        f"  exit {0 if comment_ok else 1}\n"
        "fi\n"
        "exit 2\n",
        encoding="utf-8",
    )
    for f in (yg, gh):
        f.chmod(f.stat().st_mode | stat.S_IXUSR)
    return b


def _docs_status() -> str:
    return subprocess.run(
        ["git", "status", "--porcelain", "--", "docs"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _run(
    tmp: Path,
    *args: str,
    graph_ok: bool = True,
    comment_ok: bool = True,
    report_text: str = VALID_REPORT,
):
    b = _fake_bin(
        tmp, graph_ok=graph_ok, comment_ok=comment_ok, report_text=report_text
    )
    work = tmp / "work"
    work.mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k != "OUTSIDER_EXECUTION"}
    env["PATH"] = f"{b}:{env['PATH']}"
    env["OUTSIDER_WORKDIR"] = str(work)
    env["OUTSIDER_LEDGER"] = str(tmp / "ledger.jsonl")  # must have no effect (FR-1004)
    before = _docs_status()
    proc = subprocess.run(
        ["bash", str(WRAPPER), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    # FR-1004 AC-04: no mode touches docs/ or any tracked file; no ledger anywhere.
    assert _docs_status() == before
    assert not (work / "docs").exists()
    assert not (tmp / "ledger.jsonl").exists()
    assert not (REPO / "docs/census/outsider-ledger.jsonl").exists()
    return proc, work


def _tools():
    import importlib.util

    spec = importlib.util.spec_from_file_location("outsider_tools_w", TOOLS)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.req("REQ-YG-663")
def test_adapter_pins_model_and_grants_no_access():
    text = (SKILL / "adapters/graph.yaml").read_text(encoding="utf-8")
    node = yaml.safe_load(text)["nodes"]["outsider"]
    assert node["type"] == "copilot" and node["cli_flags"]["model"] == "gpt-5.6-sol"
    assert "allow_all" not in text


@pytest.mark.req("REQ-YG-662")
def test_adapter_state_carries_base_observation_fields():
    state = yaml.safe_load((SKILL / "adapters/graph.yaml").read_text(encoding="utf-8"))[
        "state"
    ]
    for key in ("repo", "pr", "head_sha", "prompt_digest", "tool_sha"):
        assert state.get(key) == "str", key


@pytest.mark.req("REQ-YG-663")
def test_doctrine_within_sixty_lines():
    assert len((SKILL / "doctrine.md").read_text(encoding="utf-8").splitlines()) <= 60


@pytest.mark.req("REQ-YG-662")
def test_no_ledger_in_active_code(script: str):
    assert "ledger" not in script.casefold()
    assert "OUTSIDER_LEDGER" not in script
    assert "ledger" not in TOOLS.read_text(encoding="utf-8").casefold()
    assert "docs/" not in script


@pytest.mark.req("REQ-YG-663")
def test_wrapper_is_executable_in_the_index():
    # FR-889 lock strips disk perms on main; the committed mode is the contract
    mode = subprocess.run(
        ["git", "ls-files", "-s", "scripts/outsider.sh"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()[0]
    assert mode == "100755", (
        f"scripts/outsider.sh committed as {mode}; ./scripts/outsider.sh would fail"
    )


@pytest.mark.req("REQ-YG-663")
def test_child_cwd_is_a_fresh_temp_dir_outside_repo(script: str):
    assert re.search(
        r'CHILD_CWD="\$\(mktemp -d "\$\{TMPDIR:-/tmp\}/outsider-XXXXXX"\)"', script
    )
    assert not str(Path(tempfile.gettempdir()).resolve()).startswith(
        str(REPO.resolve())
    )
    assert re.search(
        r'\( cd "\$CHILD_CWD" && OUTSIDER_EXECUTION=1 "\$\{YG\[@\]\}" graph run "\$GRAPH"',
        script,
    )


@pytest.mark.req("REQ-YG-663")
def test_losing_process_leaves_the_lock_intact(tmp_path: Path):
    work = tmp_path / "work"
    (work / "tmp/.outsider.lock").mkdir(parents=True)
    (work / "tmp/.outsider.lock/holder").write_text("pid=1 started=now")
    env = {k: v for k, v in os.environ.items() if k != "OUTSIDER_EXECUTION"}
    env["OUTSIDER_WORKDIR"] = str(work)
    proc = subprocess.run(
        ["bash", str(WRAPPER), "--selftest"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 73
    assert (work / "tmp/.outsider.lock/holder").read_text() == "pid=1 started=now"


@pytest.mark.req("REQ-YG-662")
def test_input_mode_writes_placeholder_report_and_no_observation(tmp_path: Path):
    src = tmp_path / "in.md"
    src.write_text("# t\n\nbody", encoding="utf-8")
    proc, work = _run(tmp_path, "--input", str(src), "--label", "t")
    assert proc.returncode == 0, proc.stderr
    reports = list((work / "tmp").glob("outsider-t-*.md"))
    assert len(reports) == 1
    text = reports[0].read_text(encoding="utf-8")
    assert text.startswith("**Derived verdict:** YES")
    obs = _tools().parse_observation(text)
    assert (obs.repo, obs.pr, obs.head_sha) == ("-", "-", "-")
    assert obs.input_sha256 == hashlib.sha256(src.read_bytes()).hexdigest()
    assert not (tmp_path / "comment-body.md").exists()
    assert "no observation" in proc.stdout
    assert not list(Path(tempfile.gettempdir()).glob("outsider-*/input.md"))


@pytest.mark.req("REQ-YG-662")
def test_pr_comment_posts_the_enriched_report_byte_for_byte(tmp_path: Path):
    proc, work = _run(tmp_path, "4242", "--comment")
    assert proc.returncode == 0, proc.stderr
    reports = list((work / "tmp").glob("outsider-pr-4242-*.md"))
    assert len(reports) == 1
    posted = tmp_path / "comment-body.md"
    assert posted.read_bytes() == reports[0].read_bytes()
    obs = _tools().parse_observation(posted.read_text(encoding="utf-8"))
    assert obs.pr == 4242 and obs.head_sha == FAKE_HEAD
    assert obs.input_sha256 == hashlib.sha256(FAKE_PR_TEXT.encode()).hexdigest()
    assert obs.derived_verdict == "YES" and obs.s3 == 0 and obs.s4 == 1
    assert obs.model == "gpt-5.6-sol" and obs.repo == "sheikkinen/yamlgraph"
    assert len(obs.prompt_digest) == 16 and obs.tool_sha not in ("", "-")
    assert "comment posted on #4242" in proc.stdout
    # fetched PR text lived only in the child directory, which is gone
    assert not list(Path(tempfile.gettempdir()).glob("outsider-*/pr-4242.md"))
    assert not list((work / "tmp").glob("*input*"))


@pytest.mark.req("REQ-YG-662")
def test_pr_without_comment_writes_report_only(tmp_path: Path):
    proc, work = _run(tmp_path, "4242")
    assert proc.returncode == 0, proc.stderr
    assert len(list((work / "tmp").glob("outsider-pr-4242-*.md"))) == 1
    assert not (tmp_path / "comment-body.md").exists()
    assert "not posted" in proc.stdout


@pytest.mark.req("REQ-YG-663")
def test_graph_failure_and_parse_failure_fail_closed(tmp_path: Path):
    src = tmp_path / "in.md"
    src.write_text("# t\n\nbody", encoding="utf-8")
    p1, _ = _run(tmp_path / "a", "--input", str(src), graph_ok=False)
    assert p1.returncode == 1 and "NO VALID REPORT" in p1.stderr
    p2, _ = _run(
        tmp_path / "b",
        "4242",
        "--comment",
        report_text="## 1. In my own words\n\nonly one section\n",
    )
    assert p2.returncode == 1 and "NO VALID REPORT" in p2.stderr
    assert not (tmp_path / "b" / "comment-body.md").exists()


@pytest.mark.req("REQ-YG-662")
def test_comment_failure_exits_nonzero_and_records_nothing(tmp_path: Path):
    proc, _ = _run(tmp_path, "4242", "--comment", comment_ok=False)
    assert proc.returncode == 1 and "no observation" in proc.stderr


@pytest.mark.req("REQ-YG-663")
def test_comment_is_opt_in_and_only_path_to_gh_pr_comment(script: str):
    assert "COMMENT=0" in script
    calls = [m.start() for m in re.finditer(r"gh pr comment", script)]
    assert len(calls) == 1
    guard = script[: calls[0]].rstrip().splitlines()[-1]
    assert 'if [ "$COMMENT" -eq 1 ]' in guard
    assert "dry-run" not in script


@pytest.mark.req("REQ-YG-663")
def test_recursion_sentinel_rejected_before_any_run():
    proc = subprocess.run(
        ["bash", str(WRAPPER), "--selftest"],
        capture_output=True,
        text=True,
        env={**os.environ, "OUTSIDER_EXECUTION": "1"},
        check=False,
    )
    assert proc.returncode == 70 and "inside an outsider execution" in proc.stderr
