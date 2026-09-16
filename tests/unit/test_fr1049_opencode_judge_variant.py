"""FR-1049 RED: opencode judge variant inside the sole-route judge adapter.

Judgement: feature-requests/FR-1049-opencode-judge-variant.judgement.md.
Two surfaces, no real judge launched anywhere (C-6):

* wrapper — ``scripts/judge.sh`` with a stubbed ``YAMLGRAPH_BIN`` that records
  its argv and writes the artifact the wrapper asked for;
* graph routing — the adapter graph compiled with ``subprocess.run`` mocked,
  proving ``backend=opencode`` visits only ``judge_opencode`` with a bare
  ``--model`` argv (no tool/permission/`--auto`/`--agent`/resume flag).
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
OPENCODE_MODEL = "deepseek/deepseek-v4-pro"

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


@pytest.mark.req("REQ-YG-682")
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

    def test_opencode_selects_opencode_branch(self, tmp_path, fr_file, stub):
        r = _run([str(fr_file)], tmp_path, stub, {"JUDGE_BACKEND": "opencode"})
        assert r.returncode == 0, r.stderr
        argv = _argv(tmp_path)
        assert "backend=opencode" in argv
        assert (
            f"artifact_path={tmp_path}/tmp/draft-judgement-opencode-FR-000-fixture.md"
            in argv
        )
        assert (
            tmp_path / "tmp" / "draft-judgement-opencode-FR-000-fixture.md"
        ).is_file()
        assert (
            "backend=opencode" in r.stdout
            and "draft-judgement-opencode-FR-000-fixture.md" in r.stdout
        )

    def test_unknown_backend_exits_64_before_lock(self, tmp_path, fr_file, stub):
        r = _run([str(fr_file)], tmp_path, stub, {"JUDGE_BACKEND": "opncode"})
        assert r.returncode == 64
        assert "opncode" in r.stderr
        assert not (tmp_path / "tmp" / ".judge.lock").exists()
        assert not (tmp_path / "tmp" / "argv.txt").exists()  # no graph launch

    def test_var_arguments_are_exact(self, tmp_path, fr_file, stub):
        _run([str(fr_file)], tmp_path, stub, {"JUDGE_BACKEND": "opencode"})
        argv = _argv(tmp_path)
        assert argv[:3] == [
            "graph",
            "run",
            ".github/skills/judge-fr/adapters/graph.yaml",
        ]
        assert argv.count("--var") == 3
        assert f"fr_path={fr_file}" in argv


@pytest.mark.req("REQ-YG-682")
class TestWrapperArtifactIsolation:
    def test_opencode_run_preserves_other_backends_and_frs(
        self, tmp_path, fr_file, stub
    ):
        tmpdir = tmp_path / "tmp"
        tmpdir.mkdir()
        copilot = tmpdir / "draft-judgement-copilot-FR-000-fixture.md"
        claude = tmpdir / "draft-judgement-claude-FR-000-fixture.md"
        other_fr = tmpdir / "draft-judgement-opencode-other.md"
        for f in (copilot, claude, other_fr):
            f.write_text("keep\n", encoding="utf-8")
        r = _run([str(fr_file)], tmp_path, stub, {"JUDGE_BACKEND": "opencode"})
        assert r.returncode == 0, r.stderr
        for f in (copilot, claude, other_fr):
            assert f.read_text(encoding="utf-8") == "keep\n", f.name

    def test_same_backend_same_fr_rerun_replaces_its_own_artifact(
        self, tmp_path, fr_file, stub
    ):
        art = tmp_path / "tmp" / "draft-judgement-opencode-FR-000-fixture.md"
        assert (
            _run(
                [str(fr_file)], tmp_path, stub, {"JUDGE_BACKEND": "opencode"}
            ).returncode
            == 0
        )
        first = art.read_text(encoding="utf-8")
        assert (
            _run(
                [str(fr_file)], tmp_path, stub, {"JUDGE_BACKEND": "opencode"}
            ).returncode
            == 0
        )
        second = art.read_text(encoding="utf-8")
        assert first != second  # replaced, not appended or preserved


# --- graph routing -------------------------------------------------------------

VERSION_OK = "1.18.31\n"


def _opencode_stream(text: str = "**Verdict:** stub", sid: str = "ses_x") -> str:
    return "\n".join(
        [
            json.dumps(
                {"type": "step_start", "sessionID": sid, "part": {"type": "step-start"}}
            ),
            json.dumps(
                {
                    "type": "text",
                    "sessionID": sid,
                    "part": {"type": "text", "text": text},
                }
            ),
            json.dumps(
                {
                    "type": "step_finish",
                    "sessionID": sid,
                    "part": {"type": "step-finish", "reason": "stop"},
                }
            ),
        ]
    )


def _proc(stdout: str, rc: int = 0) -> MagicMock:
    m = MagicMock()
    m.stdout, m.returncode, m.stderr = stdout, rc, ""
    return m


def _opencode_cli(responses: list[MagicMock]):
    """subprocess.run stand-in: hand `responses` to `opencode` calls in order.

    Anything else gets an empty bytes success so the scripted responses are
    never consumed.
    """
    queue = list(responses)

    def run(argv, *args, **kwargs):
        if argv and argv[0] == "opencode":
            return queue.pop(0)
        m = MagicMock()
        m.stdout, m.returncode, m.stderr = b"", 0, b""
        return m

    return run


CLAUDE_VERSION_OK = "2.1.255 (Claude Code)\n"
CLAUDE_AUTH_OK = json.dumps(
    {"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty"}
)
CLAUDE_ENVELOPE_OK = json.dumps(
    {"is_error": False, "result": "**Verdict:** stub", "session_id": "s-1"}
)


def _claude_cli(responses: list[MagicMock]):
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
    """Only copilot/claude/opencode argvs — yamlgraph's own `git describe` is not a judge."""
    return [
        list(c[0][0])
        for c in mock_run.call_args_list
        if c[0][0] and c[0][0][0] in ("copilot", "claude", "opencode")
    ]


@pytest.mark.req("REQ-YG-682")
class TestGraphRouting:
    def test_graph_has_three_copilot_nodes_sharing_the_judge_prompt(self):
        import yaml

        cfg = yaml.safe_load(ADAPTER.read_text(encoding="utf-8"))
        copilot_nodes = {
            k: v for k, v in cfg["nodes"].items() if v.get("type") == "copilot"
        }
        assert set(copilot_nodes) == {"judge", "judge_claude", "judge_opencode"}
        assert all(v["prompt"] == "judge" for v in copilot_nodes.values())
        judge = copilot_nodes["judge"]
        assert judge["backend"] == "cli"
        assert judge["cli_flags"]["model"] == "gpt-5.6-sol"
        claude = copilot_nodes["judge_claude"]
        assert claude["backend"] == "claude"
        assert claude["cli_flags"]["model"] == "claude-opus-5"
        opencode = copilot_nodes["judge_opencode"]
        assert opencode["backend"] == "opencode"
        assert opencode["cli_flags"] == {"model": OPENCODE_MODEL}
        assert set(cfg["state"]) >= {
            "fr_path",
            "backend",
            "artifact_path",
            "judge_result",
        }

    def test_edges_are_mutually_exclusive(self):
        import yaml

        cfg = yaml.safe_load(ADAPTER.read_text(encoding="utf-8"))
        from_select = [
            (e["condition"], e["to"]) for e in cfg["edges"] if e["from"] == "select"
        ]
        assert from_select == [
            ('backend == "copilot"', "judge"),
            ('backend == "claude"', "judge_claude"),
            ('backend == "opencode"', "judge_opencode"),
        ]

    def test_opencode_backend_visits_only_judge_opencode(self):
        app = _compile()
        with patch(
            "subprocess.run",
            side_effect=_opencode_cli(
                [_proc(VERSION_OK), _proc(_opencode_stream("**Verdict:** ok"))]
            ),
        ) as m:
            final = app.invoke(
                {
                    "fr_path": "feature-requests/X.md",
                    "backend": "opencode",
                    "artifact_path": "tmp/c.md",
                }
            )
        calls = _agent_calls(m)
        assert [c[:2] for c in calls] == [
            ["opencode", "--version"],
            ["opencode", "run"],
        ]
        agent = calls[1]
        assert agent == [
            "opencode",
            "run",
            agent[2],
            "--format",
            "json",
            "--model",
            OPENCODE_MODEL,
        ]
        assert "feature-requests/X.md" in agent[2] and "tmp/c.md" in agent[2]
        assert "--tools" not in agent
        assert "--allowedTools" not in agent
        assert "--auto" not in agent
        assert "--agent" not in agent
        assert "--session" not in agent
        assert not any(c[0] == "copilot" or c[0] == "claude" for c in calls)
        assert final["judge_result"].backend == "opencode"
        assert final["judge_result"].model == OPENCODE_MODEL

    def test_copilot_backend_still_visits_only_judge(self):
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
        assert calls[0][0] == "copilot"
        assert final["judge_result"].backend == "cli"

    def test_claude_backend_visits_only_judge_claude(self):
        app = _compile()
        with patch(
            "subprocess.run",
            side_effect=_claude_cli(
                [
                    _proc(CLAUDE_VERSION_OK),
                    _proc(CLAUDE_AUTH_OK),
                    _proc(CLAUDE_ENVELOPE_OK),
                ]
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
        assert "feature-requests/X.md" in agent[2] and "tmp/b.md" in agent[2]
        assert agent[agent.index("--tools") + 1] == FOUR_TOOLS
        assert not any(c[0] == "copilot" or c[0] == "opencode" for c in calls)
        assert final["judge_result"].backend == "claude"
