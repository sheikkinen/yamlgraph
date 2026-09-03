"""FR-959 RED: ``backend: claude`` for the copilot node.

Closed backend enum, typed Claude flags, frozen argv, per-invocation
version + auth preflight, typed JSON envelope, stripped payer environment.

Judgement: feature-requests/FR-959-claude-cli-backend-primitive.judgement.md
Evidence:  feature-requests/evidence/FR-959-claude-auth-probe.md (every
fixture string below is a capture from that file, not a guess).

Every ``subprocess.run`` is mocked: no binary, no network, no billing.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from yamlgraph.models.schemas import CopilotResult

# --- evidence fixtures (FR-959-claude-auth-probe.md) -------------------------

VERSION_OK = "2.1.255 (Claude Code)\n"
VERSION_DRIFT = "2.1.254 (Claude Code)\n"

AUTH_OAUTH_TOKEN = json.dumps(
    {
        "loggedIn": True,
        "authMethod": "oauth_token",
        "apiProvider": "firstParty",
        "analyticsDisabled": False,
        "projectsDirectory": "C:\\Users\\u\\.claude\\projects",
    }
)
# Evidence §2.3: browser login; extra personal keys are present and ignored.
AUTH_CLAUDE_AI = json.dumps(
    {
        "loggedIn": True,
        "authMethod": "claude.ai",
        "apiProvider": "firstParty",
        "analyticsDisabled": False,
        "projectsDirectory": "C:\\Users\\u\\.claude\\projects",
        "email": "<redacted>",
        "orgId": "<redacted>",
        "orgName": "<org>",
        "subscriptionType": "team",
    }
)
AUTH_NONE = json.dumps(
    {
        "loggedIn": False,
        "authMethod": "none",
        "apiProvider": "firstParty",
        "analyticsDisabled": False,
        "projectsDirectory": "C:\\Users\\u\\.claude\\projects",
    }
)
AUTH_API_KEY = json.dumps(
    {
        "loggedIn": True,
        "authMethod": "api_key",
        "apiProvider": "firstParty",
        "analyticsDisabled": False,
        "projectsDirectory": "C:\\Users\\u\\.claude\\projects",
        "apiKeySource": "ANTHROPIC_API_KEY",
    }
)
AUTH_BEDROCK = json.dumps(
    {
        "loggedIn": True,
        "authMethod": "third_party",
        "apiProvider": "bedrock",
        "analyticsDisabled": True,
        "projectsDirectory": "C:\\Users\\u\\.claude\\projects",
    }
)

SESSION_A = "d60ac511-386f-4efd-b760-a4be4bdf1beb"
ENVELOPE_OK = json.dumps(
    {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "result": "pong",
        "session_id": SESSION_A,
        "total_cost_usd": 0,
        "num_turns": 1,
    }
)
# Evidence §5: a failed run still says subtype "success"; only is_error signals.
ENVELOPE_LOGGED_OUT = json.dumps(
    {
        "type": "result",
        "subtype": "success",
        "is_error": True,
        "result": "Not logged in · Please run /login",
        "session_id": SESSION_A,
        "terminal_reason": "api_error",
        "total_cost_usd": 0,
    }
)

RENDERED_PROMPT = "System: Test\n\nUser: Hello"
KEEP_MARKER = "keep"  # sentinel for a variable that must survive env stripping
STRIPPED = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY",
)


def _proc(stdout: str = "", returncode: int = 0, stderr: str = "") -> MagicMock:
    m = MagicMock()
    m.stdout = stdout
    m.returncode = returncode
    m.stderr = stderr
    return m


def _happy_procs() -> list:
    return [_proc(VERSION_OK), _proc(AUTH_OAUTH_TOKEN), _proc(ENVELOPE_OK)]


def _prompt_file(tmp_path: Path) -> str:
    f = tmp_path / "prompts" / "test.yaml"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("system: Test\nuser: Hello", encoding="utf-8")
    return str(f)


def _config(tmp_path: Path, backend="claude", cli_flags=None, **extra) -> dict:
    cfg = {
        "type": "copilot",
        "prompt": _prompt_file(tmp_path),
        "state_key": "result",
        "backend": backend,
    }
    if cli_flags is not None:
        cfg["cli_flags"] = cli_flags
    cfg.update(extra)
    return cfg


def _run(tmp_path: Path, cli_flags=None, state=None, procs=None, calls: int = 1):
    """Build a claude node, run it ``calls`` times with mocked subprocess."""
    from yamlgraph.node_factory.copilot_node import create_copilot_node

    side_effect = procs if procs is not None else _happy_procs() * calls
    with patch("subprocess.run", side_effect=side_effect) as mock_run:
        node_fn = create_copilot_node("t", _config(tmp_path, cli_flags=cli_flags))
        out = None
        for _ in range(calls):
            out = node_fn(state or {})
    return out, mock_run


def _agent_argv(mock_run) -> list:
    return mock_run.call_args_list[2][0][0]


def _base(prompt: str = RENDERED_PROMPT) -> list:
    return ["claude", "-p", prompt, "--output-format", "json"]


# --- REQ-YG-640: closed enum -------------------------------------------------


@pytest.mark.req("REQ-YG-640")
class TestClosedBackendEnum:
    @pytest.mark.parametrize("bad", ["cluade", 3, "", "CLAUDE", "Cli"])
    def test_unknown_backend_fails_at_compile_before_any_subprocess(
        self, tmp_path: Path, bad
    ) -> None:
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        with (
            patch("subprocess.run") as mock_run,
            pytest.raises(ValueError, match=r"cli.*api.*sampling.*claude"),
        ):
            create_copilot_node("t", _config(tmp_path, backend=bad))
        mock_run.assert_not_called()

    @pytest.mark.parametrize("bad", ["cluade", 3, "", "CLAUDE", "Cli"])
    def test_schema_rejects_unknown_backend(self, bad) -> None:
        from yamlgraph.models.node_schema import NodeConfig

        with pytest.raises(ValidationError):
            NodeConfig(type="copilot", prompt="p", state_key="r", backend=bad)

    def test_none_backend_still_defaults_to_copilot_cli(self, tmp_path: Path) -> None:
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        cfg = _config(tmp_path)
        del cfg["backend"]
        with patch("subprocess.run", return_value=_proc("ok")) as mock_run:
            create_copilot_node("t", cfg)({})
        assert mock_run.call_args_list[0][0][0][0] == "copilot"

    def test_sampling_still_not_implemented(self, tmp_path: Path) -> None:
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        with (
            patch("subprocess.run") as mock_run,
            pytest.raises(NotImplementedError),
        ):
            create_copilot_node("t", _config(tmp_path, backend="sampling"))({})
        mock_run.assert_not_called()


# --- REQ-YG-640: typed Claude flags -----------------------------------------

BAD_FLAGS = [
    {"tools": "Read"},
    {"tools": ["Read", 3]},
    {"allowed_tools": "Read,Write"},
    {"max_turns": 0},
    {"max_turns": -1},
    {"max_turns": True},
    {"max_turns": "40"},
    {"allow_all_tools": "yes"},
    {"continue_session": 1},
    {"resume": 42},
    {"bogus_flag": 1},
]


@pytest.mark.req("REQ-YG-640")
class TestClaudeFlagShapes:
    @pytest.mark.parametrize("flags", BAD_FLAGS, ids=lambda f: json.dumps(f))
    def test_malformed_flag_fails_at_compile_before_any_probe(
        self, tmp_path: Path, flags
    ) -> None:
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        with patch("subprocess.run") as mock_run, pytest.raises(ValueError):
            create_copilot_node("t", _config(tmp_path, cli_flags=flags))
        mock_run.assert_not_called()

    @pytest.mark.parametrize("flags", BAD_FLAGS, ids=lambda f: json.dumps(f))
    def test_malformed_flag_fails_at_schema(self, flags) -> None:
        from yamlgraph.models.node_schema import NodeConfig

        with pytest.raises(ValidationError):
            NodeConfig(
                type="copilot",
                prompt="p",
                state_key="r",
                backend="claude",
                cli_flags=flags,
            )

    def test_copilot_cli_backend_flags_stay_untyped(self) -> None:
        """AC-13: the typed model applies to backend=claude only."""
        from yamlgraph.models.node_schema import NodeConfig

        NodeConfig(
            type="copilot",
            prompt="p",
            state_key="r",
            backend="cli",
            cli_flags={"allow_all_tools": "yes", "anything": 1},
        )


# --- REQ-YG-639: frozen argv -------------------------------------------------


@pytest.mark.req("REQ-YG-639")
class TestClaudeArgv:
    def test_prompt_and_model(self, tmp_path: Path) -> None:
        _, m = _run(tmp_path, {"model": "opus"})
        assert _agent_argv(m) == _base() + ["--model", "opus"]

    def test_resume_via_state_expression(self, tmp_path: Path) -> None:
        prev = CopilotResult(
            output="x", exit_code=0, backend="claude", session_id="sess-1"
        )
        _, m = _run(
            tmp_path, {"resume": "{state.prev.session_id}"}, state={"prev": prev}
        )
        assert _agent_argv(m) == _base() + ["--resume", "sess-1"]

    def test_continue_session(self, tmp_path: Path) -> None:
        _, m = _run(tmp_path, {"continue_session": True})
        assert _agent_argv(m) == _base() + ["--continue"]

    def test_tools_list_comma_joined(self, tmp_path: Path) -> None:
        _, m = _run(tmp_path, {"tools": ["Read", "Grep"]})
        assert _agent_argv(m) == _base() + ["--tools", "Read,Grep"]

    def test_empty_tools_means_no_tools(self, tmp_path: Path) -> None:
        _, m = _run(tmp_path, {"tools": []})
        assert _agent_argv(m) == _base() + ["--tools", ""]

    def test_allowed_tools_is_approval_flag(self, tmp_path: Path) -> None:
        _, m = _run(tmp_path, {"allowed_tools": ["Read", "Write"]})
        assert _agent_argv(m) == _base() + ["--allowedTools", "Read,Write"]

    def test_allow_all_tools_wins_over_allowed_tools(self, tmp_path: Path) -> None:
        _, m = _run(tmp_path, {"allow_all_tools": True, "allowed_tools": ["Read"]})
        argv = _agent_argv(m)
        assert argv == _base() + ["--dangerously-skip-permissions"]
        assert "--allowedTools" not in argv

    def test_allow_all_paths_adds_cwd(self, tmp_path: Path) -> None:
        _, m = _run(tmp_path, {"allow_all_paths": True})
        assert _agent_argv(m) == _base() + ["--add-dir", str(Path.cwd())]

    def test_max_turns(self, tmp_path: Path) -> None:
        _, m = _run(tmp_path, {"max_turns": 40})
        assert _agent_argv(m) == _base() + ["--max-turns", "40"]

    def test_full_frozen_order(self, tmp_path: Path) -> None:
        _, m = _run(
            tmp_path,
            {
                "model": "opus",
                "continue_session": True,
                "tools": ["Read", "Glob", "Grep", "Write"],
                "allowed_tools": ["Read", "Glob", "Grep", "Write"],
                "allow_all_paths": True,
                "max_turns": 40,
            },
        )
        assert _agent_argv(m) == _base() + [
            "--model",
            "opus",
            "--continue",
            "--tools",
            "Read,Glob,Grep,Write",
            "--allowedTools",
            "Read,Glob,Grep,Write",
            "--add-dir",
            str(Path.cwd()),
            "--max-turns",
            "40",
        ]

    def test_allowed_tools_never_the_only_tool_flag_when_tools_set(
        self, tmp_path: Path
    ) -> None:
        """AC-04: availability (--tools) and approval (--allowedTools) are distinct."""
        _, m = _run(tmp_path, {"tools": ["Read"], "allowed_tools": ["Read"]})
        argv = _agent_argv(m)
        assert "--tools" in argv and "--allowedTools" in argv
        assert argv.index("--tools") < argv.index("--allowedTools")

    def test_argv_is_a_list_and_prompt_is_one_element(self, tmp_path: Path) -> None:
        _, m = _run(tmp_path, {})
        argv = _agent_argv(m)
        assert isinstance(argv, list)
        assert argv[2] == RENDERED_PROMPT
        assert m.call_args_list[2][1].get("shell") is not True


# --- REQ-YG-641: per-invocation preflight and payer environment -------------


@pytest.mark.req("REQ-YG-641")
class TestPreflight:
    def test_version_then_auth_then_agent_on_every_invocation(
        self, tmp_path: Path
    ) -> None:
        """AC-06: two executions -> two version probes, two auth probes, two agents."""
        _, m = _run(tmp_path, {}, calls=2)
        heads = [c[0][0][:3] for c in m.call_args_list]
        assert (
            heads
            == [
                ["claude", "--version"],
                ["claude", "auth", "status"],
                ["claude", "-p", RENDERED_PROMPT],
            ]
            * 2
        )

    @pytest.mark.parametrize("auth", [AUTH_CLAUDE_AI, AUTH_OAUTH_TOKEN])
    def test_subscription_methods_are_accepted(self, tmp_path: Path, auth) -> None:
        """AC-09: browser login (claude.ai) and setup token (oauth_token) proceed."""
        out, m = _run(
            tmp_path, {}, procs=[_proc(VERSION_OK), _proc(auth), _proc(ENVELOPE_OK)]
        )
        assert m.call_count == 3
        assert out["result"].session_id == SESSION_A

    def test_version_drift_fails_before_auth_probe(self, tmp_path: Path) -> None:
        with pytest.raises(RuntimeError, match=r"2\.1\.254.*2\.1\.255"):
            _run(tmp_path, {}, procs=[_proc(VERSION_DRIFT)])

    def test_matching_version_on_foreign_banner_is_drift(self, tmp_path: Path) -> None:
        """PR #563 review P3: the whole banner is the contract, not its prefix."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        with (
            patch(
                "subprocess.run", side_effect=[_proc("2.1.255 (Untrusted Wrapper)\n")]
            ) as m,
            pytest.raises(RuntimeError, match=r"Untrusted Wrapper.*Claude Code"),
        ):
            create_copilot_node("t", _config(tmp_path, cli_flags={}))({})
        assert m.call_count == 1

    def test_version_drift_makes_exactly_one_call(self, tmp_path: Path) -> None:
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        with (
            patch("subprocess.run", side_effect=[_proc(VERSION_DRIFT)]) as m,
            pytest.raises(RuntimeError),
        ):
            create_copilot_node("t", _config(tmp_path, cli_flags={}))({})
        assert m.call_count == 1

    @pytest.mark.parametrize(
        ("auth", "rc", "names"),
        [
            (AUTH_NONE, 1, "none"),
            (AUTH_API_KEY, 0, "api_key"),
            (AUTH_BEDROCK, 0, "third_party"),
            ("not json at all", 0, "auth status"),
            (AUTH_OAUTH_TOKEN, 2, "exit 2"),
        ],
    )
    def test_auth_refusals_fail_before_agent_prompt(
        self, tmp_path: Path, auth, rc, names
    ) -> None:
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        with (
            patch(
                "subprocess.run", side_effect=[_proc(VERSION_OK), _proc(auth, rc)]
            ) as m,
            pytest.raises(RuntimeError, match=names),
        ):
            create_copilot_node("t", _config(tmp_path, cli_flags={}))({})
        assert m.call_count == 2
        assert all(c[0][0][1] != "-p" for c in m.call_args_list)

    def test_missing_binary_is_named(self, tmp_path: Path) -> None:
        with pytest.raises(RuntimeError, match=r"claude.*PATH"):
            _run(tmp_path, {}, procs=[FileNotFoundError("claude")])

    def test_env_stripped_for_all_three_calls(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC-07: preflight and agent share one sanitized environment."""
        for var in STRIPPED:
            monkeypatch.setenv(var, "leak")
        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", KEEP_MARKER)
        monkeypatch.setenv("YAMLGRAPH_OTEL_DIR", str(tmp_path / "otel"))
        _, m = _run(tmp_path, {})
        assert m.call_count == 3
        for call in m.call_args_list:
            env = call[1]["env"]
            assert env is not None
            for var in STRIPPED:
                assert var not in env, var
            assert env["PATH"] == os.environ["PATH"]
            assert env["CLAUDE_CODE_OAUTH_TOKEN"] == KEEP_MARKER
            assert env["COPILOT_OTEL_FILE_EXPORTER_PATH"].startswith(
                str(tmp_path / "otel")
            )

    def test_no_module_level_auth_cache(self) -> None:
        import yamlgraph.node_factory.copilot_runtime_claude as mod

        cached = [
            n for n in vars(mod) if "cache" in n.lower() and not n.startswith("__")
        ]
        assert cached == []


# --- REQ-YG-639: typed envelope ---------------------------------------------


@pytest.mark.req("REQ-YG-639")
class TestEnvelope:
    def test_success_maps_into_copilot_result(self, tmp_path: Path) -> None:
        out, _ = _run(tmp_path, {"model": "opus"})
        r = out["result"]
        assert isinstance(r, CopilotResult)
        assert r.output == "pong"
        assert r.session_id == SESSION_A
        assert r.exit_code == 0
        assert r.backend == "claude"
        assert r.model == "opus"
        assert out["current_step"] == "t"

    @pytest.mark.parametrize(
        "stdout",
        [
            "[]",
            json.dumps({"session_id": "s"}),
            json.dumps({"result": 1, "session_id": "s"}),
            json.dumps({"result": "x"}),
            json.dumps({"result": "x", "session_id": 5}),
            json.dumps({"result": "x", "session_id": "s", "is_error": "no"}),
            "not json",
            "",
            ENVELOPE_LOGGED_OUT,
        ],
        ids=[
            "array",
            "missing-result",
            "non-string-result",
            "missing-session",
            "non-string-session",
            "non-bool-is_error",
            "not-json",
            "empty",
            "is_error-true-with-subtype-success",
        ],
    )
    def test_malformed_or_error_envelope_raises_without_state_update(
        self, tmp_path: Path, stdout
    ) -> None:
        with pytest.raises(RuntimeError):
            _run(
                tmp_path,
                {},
                procs=[_proc(VERSION_OK), _proc(AUTH_OAUTH_TOKEN), _proc(stdout, 0)],
            )

    @pytest.mark.parametrize("code", [1, 7])
    def test_nonzero_exit_is_generic_and_names_code_and_head(
        self, tmp_path: Path, code
    ) -> None:
        body = json.dumps({"result": "boom " * 10, "session_id": "s", "is_error": True})
        with pytest.raises(RuntimeError, match=rf"exit {code}.*boom"):
            _run(
                tmp_path,
                {},
                procs=[_proc(VERSION_OK), _proc(AUTH_OAUTH_TOKEN), _proc(body, code)],
            )

    def test_nonzero_exit_without_json_uses_stderr_head(self, tmp_path: Path) -> None:
        with pytest.raises(RuntimeError, match=r"exit 1.*stderr-head"):
            _run(
                tmp_path,
                {},
                procs=[
                    _proc(VERSION_OK),
                    _proc(AUTH_OAUTH_TOKEN),
                    _proc("", 1, "stderr-head"),
                ],
            )

    def test_timeout_is_mapped(self, tmp_path: Path) -> None:
        with pytest.raises(RuntimeError, match=r"timed out"):
            _run(
                tmp_path,
                {},
                procs=[
                    _proc(VERSION_OK),
                    _proc(AUTH_OAUTH_TOKEN),
                    subprocess.TimeoutExpired(cmd="claude", timeout=1),
                ],
            )

    def test_no_usage_limit_classifier_in_package(self) -> None:
        """AC-11 (FR-958 R-4): v1 ships no usage-limit taxonomy."""
        pkg = Path(__file__).resolve().parents[2] / "yamlgraph"
        hits = [
            p
            for p in pkg.rglob("*.py")
            if any(
                s in p.read_text(encoding="utf-8")
                for s in ("ClaudeUsageLimitError", "resets_at")
            )
        ]
        assert hits == []
