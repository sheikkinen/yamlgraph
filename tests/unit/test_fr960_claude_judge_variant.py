"""FR-960 RED: Claude judge variant inside the sole-route judge adapter.

Judgement: feature-requests/FR-960-claude-judge-variant.judgement.md (R-5).
Two surfaces, no real judge launched anywhere (C-6):

* wrapper — ``scripts/judge.sh`` with a stubbed ``YAMLGRAPH_BIN`` that records
  its argv and writes the artifact the wrapper asked for;
* graph routing — the adapter graph compiled with ``subprocess.run`` mocked,
  proving ``backend=copilot`` visits only ``judge`` and ``backend=claude`` only
  ``judge_claude``, with the frozen four-tool argv.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
JUDGE = REPO_ROOT / "scripts" / "judge.sh"
ADAPTER = REPO_ROOT / ".github" / "skills" / "judge-fr" / "adapters" / "graph.yaml"
PROMPT = (
    REPO_ROOT
    / ".github"
    / "skills"
    / "judge-fr"
    / "adapters"
    / "prompts"
    / "judge.yaml"
)
FOUR_TOOLS = "Read,Glob,Grep,Write"

# --- wrapper ------------------------------------------------------------------

# Records argv, then writes a verdict to the path passed as --var artifact_path=.
STUB_BODY = r"""
mkdir -p "$JUDGE_WORKDIR/tmp"
printf '%s\n' "$@" > "$JUDGE_WORKDIR/tmp/argv.txt"
for a in "$@"; do
  case "$a" in artifact_path=*) ART="${a#artifact_path=}";; esac
done
[ -n "${ART:-}" ] && printf '%s\n' "**Verdict:** APPROVED (stub $(date +%s%N))" > "$ART"
exit 0
"""


def _write_stub(path: Path, body: str = STUB_BODY) -> Path:
    path.write_text(f"#!/usr/bin/env bash\n{body}\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def _run(
    args: list[str], workdir: Path, stub: Path | None, env_extra: dict | None = None
):
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("JUDGE_EXECUTION", "YAMLGRAPH_BIN", "JUDGE_BACKEND")
    }
    env["JUDGE_WORKDIR"] = str(workdir)
    if stub is not None:
        env["YAMLGRAPH_BIN"] = str(stub)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(JUDGE), *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _argv(workdir: Path) -> list[str]:
    return (workdir / "tmp" / "argv.txt").read_text(encoding="utf-8").splitlines()


@pytest.fixture()
def fr_file(tmp_path: Path) -> Path:
    fr = tmp_path / "FR-000-fixture.md"
    fr.write_text("# FR-000 fixture\n", encoding="utf-8")
    return fr


@pytest.fixture()
def stub(tmp_path: Path) -> Path:
    return _write_stub(tmp_path / "yg-stub")


@pytest.mark.req("REQ-YG-642")
class TestWrapperBackendSelection:
    def test_unset_backend_selects_copilot_and_derives_artifact(
        self, tmp_path, fr_file, stub
    ):
        r = _run([str(fr_file)], tmp_path, stub)
        assert r.returncode == 0, r.stderr
        argv = _argv(tmp_path)
        assert "backend=copilot" in argv
        assert (
            f"artifact_path={tmp_path}/tmp/draft-judgement-copilot-FR-000-fixture.md"
            in argv
        )
        assert (
            tmp_path / "tmp" / "draft-judgement-copilot-FR-000-fixture.md"
        ).is_file()
        assert (
            "backend=copilot" in r.stdout
            and "draft-judgement-copilot-FR-000-fixture.md" in r.stdout
        )

    def test_copilot_explicit(self, tmp_path, fr_file, stub):
        r = _run([str(fr_file)], tmp_path, stub, {"JUDGE_BACKEND": "copilot"})
        assert r.returncode == 0, r.stderr
        assert "backend=copilot" in _argv(tmp_path)

    def test_claude_selects_claude_branch(self, tmp_path, fr_file, stub):
        r = _run([str(fr_file)], tmp_path, stub, {"JUDGE_BACKEND": "claude"})
        assert r.returncode == 0, r.stderr
        argv = _argv(tmp_path)
        assert "backend=claude" in argv
        assert (
            f"artifact_path={tmp_path}/tmp/draft-judgement-claude-FR-000-fixture.md"
            in argv
        )
        assert (tmp_path / "tmp" / "draft-judgement-claude-FR-000-fixture.md").is_file()

    def test_unknown_backend_exits_64_before_lock(self, tmp_path, fr_file, stub):
        r = _run([str(fr_file)], tmp_path, stub, {"JUDGE_BACKEND": "cluade"})
        assert r.returncode == 64
        assert "cluade" in r.stderr
        assert not (tmp_path / "tmp" / ".judge.lock").exists()
        assert not (tmp_path / "tmp" / "argv.txt").exists()  # no graph launch

    def test_var_arguments_are_exact(self, tmp_path, fr_file, stub):
        _run([str(fr_file)], tmp_path, stub, {"JUDGE_BACKEND": "claude"})
        argv = _argv(tmp_path)
        assert argv[:3] == [
            "graph",
            "run",
            ".github/skills/judge-fr/adapters/graph.yaml",
        ]
        assert argv.count("--var") == 3
        assert f"fr_path={fr_file}" in argv


@pytest.mark.req("REQ-YG-642")
class TestWrapperArtifactIsolation:
    def test_other_backend_and_other_fr_artifacts_survive(
        self, tmp_path, fr_file, stub
    ):
        tmpdir = tmp_path / "tmp"
        tmpdir.mkdir()
        other_fr = tmpdir / "draft-judgement-copilot-other.md"
        same_fr_copilot = tmpdir / "draft-judgement-copilot-FR-000-fixture.md"
        legacy = tmpdir / "draft-judgement.md"
        for f in (other_fr, same_fr_copilot, legacy):
            f.write_text("keep\n", encoding="utf-8")
        r = _run([str(fr_file)], tmp_path, stub, {"JUDGE_BACKEND": "claude"})
        assert r.returncode == 0, r.stderr
        for f in (other_fr, same_fr_copilot, legacy):
            assert f.read_text(encoding="utf-8") == "keep\n", f.name

    def test_same_backend_same_fr_rerun_replaces_its_own_artifact(
        self, tmp_path, fr_file, stub
    ):
        art = tmp_path / "tmp" / "draft-judgement-copilot-FR-000-fixture.md"
        assert _run([str(fr_file)], tmp_path, stub).returncode == 0
        first = art.read_text(encoding="utf-8")
        assert _run([str(fr_file)], tmp_path, stub).returncode == 0
        second = art.read_text(encoding="utf-8")
        assert first != second  # replaced, not appended or preserved

    def test_missing_verdict_line_still_exits_65(self, tmp_path, fr_file):
        stub = _write_stub(
            tmp_path / "yg-noverdict",
            STUB_BODY.replace("**Verdict:** APPROVED", "no verdict here"),
        )
        r = _run([str(fr_file)], tmp_path, stub)
        assert r.returncode == 65
        assert "draft-judgement-copilot-FR-000-fixture.md" in r.stderr


# --- graph routing -------------------------------------------------------------

VERSION_OK = "2.1.255 (Claude Code)\n"
AUTH_OK = json.dumps(
    {"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty"}
)
ENVELOPE_OK = json.dumps(
    {"is_error": False, "result": "**Verdict:** stub", "session_id": "s-1"}
)


def _proc(stdout: str, rc: int = 0) -> MagicMock:
    m = MagicMock()
    m.stdout, m.returncode, m.stderr = stdout, rc, ""
    return m


def _claude_cli(responses: list[MagicMock]):
    """subprocess.run stand-in: hand `responses` to `claude` calls in order.

    Anything else (platform probes shelled out by other layers, FR-982) gets
    an empty bytes success so the scripted responses are never consumed.
    """
    queue = list(responses)

    def run(argv, *args, **kwargs):
        if argv and argv[0] == "claude":
            return queue.pop(0)
        m = MagicMock()
        m.stdout, m.returncode, m.stderr = b"", 0, b""
        return m

    return run


def _compile():
    from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

    return compile_graph(load_graph_config(ADAPTER)).compile()


def _agent_calls(mock_run) -> list[list[str]]:
    """Only copilot/claude argvs — yamlgraph's own `git describe` is not a judge."""
    return [
        list(c[0][0])
        for c in mock_run.call_args_list
        if c[0][0] and c[0][0][0] in ("copilot", "claude")
    ]


@pytest.mark.req("REQ-YG-642")
class TestGraphRouting:
    def test_graph_has_two_copilot_nodes_sharing_the_judge_prompt(self):
        import yaml

        cfg = yaml.safe_load(ADAPTER.read_text(encoding="utf-8"))
        copilot_nodes = {
            k: v for k, v in cfg["nodes"].items() if v.get("type") == "copilot"
        }
        assert set(copilot_nodes) == {"judge", "judge_claude"}
        assert all(v["prompt"] == "judge" for v in copilot_nodes.values())
        judge = copilot_nodes["judge"]
        assert judge["backend"] == "cli"
        assert judge["cli_flags"]["model"] == "gpt-5.6-sol"
        assert judge["cli_flags"]["allow_all_paths"] is True
        assert judge["cli_flags"]["allow_all_tools"] is True
        claude = copilot_nodes["judge_claude"]
        assert claude["backend"] == "claude"
        # PR #577 review P3: an exact id, never an alias (REQ-YG-632 spirit).
        assert claude["cli_flags"]["model"] == "claude-opus-5"
        assert claude["cli_flags"]["tools"] == FOUR_TOOLS.split(",")
        assert claude["cli_flags"]["allowed_tools"] == FOUR_TOOLS.split(",")
        assert claude["cli_flags"]["max_turns"] == 40
        assert "allow_all_tools" not in claude["cli_flags"]
        assert set(cfg["state"]) >= {
            "fr_path",
            "backend",
            "artifact_path",
            "judge_result",
        }

    def test_prompt_uses_artifact_path_variable(self):
        text = PROMPT.read_text(encoding="utf-8")
        assert "{{ artifact_path }}" in text
        assert "tmp/draft-judgement.md" not in text

    def test_copilot_backend_visits_only_judge(self):
        app = _compile()
        with patch("subprocess.run", return_value=_proc("**Verdict:** ok")) as m:
            final = app.invoke(
                {
                    "fr_path": "feature-requests/X.md",
                    "backend": "copilot",
                    "artifact_path": "tmp/a.md",
                }
            )
        calls = _agent_calls(m)
        assert len(calls) == 1
        argv = calls[0]
        assert argv[0] == "copilot"
        assert "--model" in argv and argv[argv.index("--model") + 1] == "gpt-5.6-sol"
        prompt = argv[argv.index("-p") + 1]
        assert "feature-requests/X.md" in prompt and "tmp/a.md" in prompt
        assert final["judge_result"].backend == "cli"

    def test_claude_backend_visits_only_judge_claude_with_four_tools(self):
        app = _compile()
        with patch(
            "subprocess.run",
            side_effect=_claude_cli(
                [_proc(VERSION_OK), _proc(AUTH_OK), _proc(ENVELOPE_OK)]
            ),
        ) as m:
            final = app.invoke(
                {
                    "fr_path": "feature-requests/X.md",
                    "backend": "claude",
                    "artifact_path": "tmp/b.md",
                }
            )
        calls = _agent_calls(m)
        assert [c[:2] for c in calls] == [
            ["claude", "--version"],
            ["claude", "auth", "status"][:2],
            ["claude", "-p"],
        ]
        agent = calls[2]
        assert agent[:2] == ["claude", "-p"]
        assert "feature-requests/X.md" in agent[2] and "tmp/b.md" in agent[2]
        assert agent[agent.index("--tools") + 1] == FOUR_TOOLS
        assert agent[agent.index("--allowedTools") + 1] == FOUR_TOOLS
        assert agent[agent.index("--max-turns") + 1] == "40"
        assert "--dangerously-skip-permissions" not in agent
        assert not any(
            tok == "Bash" or tok == "Edit" or tok.startswith("mcp__") for tok in agent
        )
        assert not any(c[0] == "copilot" for c in calls)
        assert final["judge_result"].backend == "claude"
