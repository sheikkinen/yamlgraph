"""FR-1048 RED: ``backend: opencode`` for the copilot node.

Closed backend enum, typed opencode flags, fail-closed model resolution,
frozen argv, per-invocation version preflight, typed fail-closed JSONL state
machine, provider-credential-preserving environment.

Judgement: feature-requests/FR-1048-opencode-cli-backend.md (R-1..R-4 folded)
Evidence:  feature-requests/evidence/FR-1048-opencode-cli-probe.md (every
fixture string below is a capture from that file, not a guess).

Every ``subprocess.run`` is mocked: no binary, no network, no billing.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from yamlgraph.models.schemas import CopilotResult, OpenCodeCliFlags

# --- evidence fixtures (FR-1048-opencode-cli-probe.md) ----------------------

VERSION_OK = "1.18.31\n"
VERSION_DRIFT = "1.17.9\n"

SID = "ses_f5a05a0faffe3TbMvYHe3wGo2f"
SID_OTHER = "ses_f59f4c2d5ffeLWm4Iqk9TBRR6k"


def _ev(etype: str, sid: str, **extra) -> str:
    return json.dumps({"type": etype, "sessionID": sid, **extra})


def _step_start(sid: str = SID) -> str:
    return _ev("step_start", sid, part={"type": "step-start"})


def _text(sid: str = SID, text: str = "\n\nok") -> str:
    return _ev("text", sid, part={"type": "text", "text": text})


def _tool_use(sid: str = SID) -> str:
    return _ev(
        "tool_use",
        sid,
        part={
            "type": "tool",
            "tool": "read",
            "callID": "call_1",
            "state": {"status": "completed"},
        },
    )


def _step_finish(sid: str = SID, reason: str = "stop") -> str:
    return _ev("step_finish", sid, part={"type": "step-finish", "reason": reason})


def _error(sid: str = SID, name: str = "UnknownError", message: str = "boom") -> str:
    return _ev("error", sid, error={"name": name, "data": {"message": message}})


SIMPLE_OK = "\n".join([_step_start(), _text(), _step_finish(reason="stop")]) + "\n"
TOOL_OK = (
    "\n".join(
        [
            _step_start(),
            _tool_use(),
            _step_finish(reason="tool-calls"),
            _step_start(),
            _text(text="\n\nhello tool world"),
            _step_finish(reason="stop"),
        ]
    )
    + "\n"
)

RENDERED_PROMPT = "System: Test\n\nUser: Hello"


def _proc(stdout: str = "", returncode: int = 0, stderr: str = "") -> MagicMock:
    m = MagicMock()
    m.stdout = stdout
    m.returncode = returncode
    m.stderr = stderr
    return m


def _happy_procs(stream: str = SIMPLE_OK) -> list:
    return [_proc(VERSION_OK), _proc(stream)]


def _prompt_file(tmp_path: Path) -> str:
    f = tmp_path / "prompts" / "test.yaml"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("system: Test\nuser: Hello", encoding="utf-8")
    return str(f)


def _config(tmp_path: Path, backend="opencode", cli_flags=None, **extra) -> dict:
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


def _run(
    tmp_path: Path, cli_flags=None, state=None, procs=None, defaults=None, **extra
):
    """Build an opencode node, run it once with mocked subprocess."""
    from yamlgraph.node_factory.copilot_node import create_copilot_node

    side_effect = procs if procs is not None else _happy_procs()
    with patch("subprocess.run", side_effect=side_effect) as mock_run:
        node_fn = create_copilot_node(
            "t",
            _config(tmp_path, cli_flags=cli_flags, **extra),
            defaults=defaults or {},
        )
        out = node_fn(state or {})
    return out, mock_run


def _agent_argv(mock_run) -> list:
    return mock_run.call_args_list[1][0][0]


# --- REQ-YG-680: closed enum -------------------------------------------------


@pytest.mark.req("REQ-YG-680")
class TestClosedBackendEnum:
    @pytest.mark.parametrize("bad", ["opnecode", 3, "", "OPENCODE", "Opencode"])
    def test_unknown_backend_fails_at_compile_before_any_subprocess(
        self, tmp_path: Path, bad
    ) -> None:
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        with (
            patch("subprocess.run") as mock_run,
            pytest.raises(ValueError, match=r"cli.*api.*sampling.*claude.*opencode"),
        ):
            create_copilot_node("t", _config(tmp_path, backend=bad))
        mock_run.assert_not_called()

    @pytest.mark.parametrize("bad", ["opnecode", 3, "", "OPENCODE"])
    def test_schema_rejects_unknown_backend(self, bad) -> None:
        from yamlgraph.models.node_schema import NodeConfig

        with pytest.raises(ValidationError):
            NodeConfig(type="copilot", prompt="p", state_key="r", backend=bad)

    def test_none_backend_still_defaults_to_copilot_cli(self, tmp_path: Path) -> None:
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        # backend=None normalizes to "cli", which does not require a model.
        create_copilot_node("t", _config(tmp_path, backend=None))


# --- REQ-YG-680: typed flags -------------------------------------------------


@pytest.mark.req("REQ-YG-680")
class TestOpenCodeFlags:
    @pytest.mark.parametrize(
        "bad",
        [
            {"model": 3},
            {"resume": 3},
            {"model": ""},
            {"resume": "   "},
            {"agent": "judge"},
            {"dir": "/tmp"},
            {"variant": "high"},
            {"thinking": True},
            {"auto": True},
            {"continue_session": True},
        ],
    )
    def test_invalid_shapes_rejected(self, bad) -> None:
        with pytest.raises(ValidationError):
            OpenCodeCliFlags.model_validate(bad)

    def test_omitted_and_none_accepted(self) -> None:
        assert OpenCodeCliFlags.model_validate({}).model is None
        assert (
            OpenCodeCliFlags.model_validate({"model": None, "resume": None}).resume
            is None
        )

    def test_valid_strings_accepted(self) -> None:
        f = OpenCodeCliFlags.model_validate(
            {"model": "inception/mercury-2.5", "resume": "{state.prev.session_id}"}
        )
        assert f.model == "inception/mercury-2.5"
        assert f.resume == "{state.prev.session_id}"


# --- REQ-YG-681: fail-closed model resolution --------------------------------


@pytest.mark.req("REQ-YG-681")
class TestModelResolution:
    @pytest.mark.parametrize("bad", ["model-only", "/model", "provider/", "no slash"])
    def test_malformed_model_fails_at_compile(self, tmp_path: Path, bad) -> None:
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        with (
            patch("subprocess.run") as mock_run,
            pytest.raises(ValueError, match="provider/model"),
        ):
            create_copilot_node("t", _config(tmp_path, cli_flags={"model": bad}))
        mock_run.assert_not_called()

    def test_blank_model_fails_at_flag_validation(self, tmp_path: Path) -> None:
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        with (
            patch("subprocess.run") as mock_run,
            pytest.raises(ValueError, match="cli_flags"),
        ):
            create_copilot_node("t", _config(tmp_path, cli_flags={"model": ""}))
        mock_run.assert_not_called()

    def test_missing_model_fails_at_compile(self, tmp_path: Path) -> None:
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        with (
            patch("subprocess.run") as mock_run,
            pytest.raises(ValueError, match="provider/model"),
        ):
            create_copilot_node("t", _config(tmp_path))
        mock_run.assert_not_called()

    def test_invalid_higher_priority_does_not_fall_through(
        self, tmp_path: Path
    ) -> None:
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        # cli_flags.model is grammar-invalid but non-blank; node.model is valid.
        # Must fail (no fallthrough to the valid lower-priority value).
        with (
            patch("subprocess.run") as mock_run,
            pytest.raises(ValueError, match="provider/model"),
        ):
            create_copilot_node(
                "t",
                _config(
                    tmp_path,
                    cli_flags={"model": "model-only"},
                    model="inception/mercury-2.5",
                ),
            )
        mock_run.assert_not_called()

    def test_precedence_cli_flags_over_node_over_defaults(self, tmp_path: Path) -> None:
        out, mock_run = _run(
            tmp_path,
            cli_flags={"model": "inception/mercury-2"},
            model="deepseek/deepseek-v4-pro",
            defaults={"model": "inception/mercury-2.5"},
        )
        argv = _agent_argv(mock_run)
        assert argv[argv.index("--model") + 1] == "inception/mercury-2"

    def test_defaults_model_used_when_only_source(self, tmp_path: Path) -> None:
        out, mock_run = _run(tmp_path, defaults={"model": "inception/mercury-2.5"})
        argv = _agent_argv(mock_run)
        assert argv[argv.index("--model") + 1] == "inception/mercury-2.5"


# --- REQ-YG-679: argv + version preflight ------------------------------------


@pytest.mark.req("REQ-YG-679")
class TestArgvAndPreflight:
    def test_frozen_argv_order_prompt_first(self, tmp_path: Path) -> None:
        out, mock_run = _run(tmp_path, cli_flags={"model": "inception/mercury-2.5"})
        argv = _agent_argv(mock_run)
        assert argv == [
            "opencode",
            "run",
            RENDERED_PROMPT,
            "--format",
            "json",
            "--model",
            "inception/mercury-2.5",
        ]

    def test_resume_maps_to_session_trailing(self, tmp_path: Path) -> None:
        out, mock_run = _run(
            tmp_path,
            cli_flags={"model": "inception/mercury-2.5", "resume": "ses_abc"},
        )
        argv = _agent_argv(mock_run)
        assert argv[-2:] == ["--session", "ses_abc"]

    def test_version_probe_then_agent_call(self, tmp_path: Path) -> None:
        out, mock_run = _run(tmp_path, cli_flags={"model": "inception/mercury-2.5"})
        assert mock_run.call_count == 2
        assert mock_run.call_args_list[0][0][0] == ["opencode", "--version"]

    def test_version_drift_fails_before_agent(self, tmp_path: Path) -> None:
        procs = [_proc(VERSION_DRIFT), _proc(SIMPLE_OK)]
        with patch("subprocess.run", side_effect=procs) as mock_run:
            from yamlgraph.node_factory.copilot_node import create_copilot_node

            node_fn = create_copilot_node(
                "t", _config(tmp_path, cli_flags={"model": "inception/mercury-2.5"})
            )
            with pytest.raises(RuntimeError, match="unsupported opencode version"):
                node_fn({})
        assert mock_run.call_count == 1  # only the probe ran

    def test_resume_state_expression_resolves(self, tmp_path: Path) -> None:
        out, mock_run = _run(
            tmp_path,
            cli_flags={
                "model": "inception/mercury-2.5",
                "resume": "{state.prev.session_id}",
            },
            state={"prev": {"session_id": "ses_resolved"}},
        )
        argv = _agent_argv(mock_run)
        assert argv[-2:] == ["--session", "ses_resolved"]

    def test_resume_invalid_expression_raises(self, tmp_path: Path) -> None:
        with patch("subprocess.run", side_effect=_happy_procs()) as mock_run:
            from yamlgraph.node_factory.copilot_node import create_copilot_node

            node_fn = create_copilot_node(
                "t",
                _config(
                    tmp_path,
                    cli_flags={
                        "model": "inception/mercury-2.5",
                        "resume": "{state.missing}",
                    },
                ),
            )
            with pytest.raises(RuntimeError):
                node_fn({})
        assert mock_run.call_count == 1  # only the version probe


# --- REQ-YG-679: state machine ----------------------------------------------


@pytest.mark.req("REQ-YG-679")
class TestStreamStateMachine:
    def test_simple_success_maps_result(self, tmp_path: Path) -> None:
        out, _ = _run(tmp_path, cli_flags={"model": "inception/mercury-2.5"})
        result = out["result"]
        assert isinstance(result, CopilotResult)
        assert result.backend == "opencode"
        assert result.output == "\n\nok"
        assert result.session_id == SID
        assert result.exit_code == 0

    def test_multi_step_tool_sequence_success(self, tmp_path: Path) -> None:
        out, _ = _run(
            tmp_path,
            cli_flags={"model": "inception/mercury-2.5"},
            procs=_happy_procs(TOOL_OK),
        )
        assert out["result"].output == "\n\nhello tool world"

    def test_error_event_fails(self, tmp_path: Path) -> None:
        stream = "\n".join([_step_start(), _error()]) + "\n"
        with patch("subprocess.run", side_effect=_happy_procs(stream)):
            from yamlgraph.node_factory.copilot_node import create_copilot_node

            node_fn = create_copilot_node(
                "t", _config(tmp_path, cli_flags={"model": "inception/mercury-2.5"})
            )
            with pytest.raises(RuntimeError, match="UnknownError"):
                node_fn({})

    @pytest.mark.parametrize(
        "stream,match",
        [
            ("\n".join([_step_start(), _step_start()]) + "\n", "nested step_start"),
            (
                "\n".join([_text(), _step_finish(reason="stop")]) + "\n",
                "text outside an open step",
            ),
            ("\n".join([_step_start()]) + "\n", "unclosed step"),
            (
                "\n".join([_step_start(), _step_finish(reason="tool-calls")]) + "\n",
                "ended without a terminal",
            ),
            (
                "\n".join(
                    [_step_start(), _text(), _step_finish(reason="stop"), _text()]
                )
                + "\n",
                "event after terminal",
            ),
            ("\n".join([_step_start(), _step_finish(reason="stop")]) + "\n", "no text"),
            (
                "\n".join([_step_start(), _step_finish(reason="weird")]) + "\n",
                "unknown step_finish reason",
            ),
            (
                "\n".join(
                    [_step_start(), _text(SID_OTHER), _step_finish(reason="stop")]
                )
                + "\n",
                "conflicting sessionID",
            ),
        ],
    )
    def test_invalid_transitions_fail(self, tmp_path: Path, stream, match) -> None:
        with patch("subprocess.run", side_effect=_happy_procs(stream)):
            from yamlgraph.node_factory.copilot_node import create_copilot_node

            node_fn = create_copilot_node(
                "t", _config(tmp_path, cli_flags={"model": "inception/mercury-2.5"})
            )
            with pytest.raises(RuntimeError, match=match):
                node_fn({})

    def test_non_json_line_fails(self, tmp_path: Path) -> None:
        stream = (
            "\n".join([_step_start(), "not json", _step_finish(reason="stop")]) + "\n"
        )
        with patch("subprocess.run", side_effect=_happy_procs(stream)):
            from yamlgraph.node_factory.copilot_node import create_copilot_node

            node_fn = create_copilot_node(
                "t", _config(tmp_path, cli_flags={"model": "inception/mercury-2.5"})
            )
            with pytest.raises(RuntimeError, match="non-JSON"):
                node_fn({})

    def test_unknown_event_type_fails(self, tmp_path: Path) -> None:
        stream = (
            "\n".join(
                [_step_start(), _ev("reasoning", SID, part={"type": "reasoning"})]
            )
            + "\n"
        )
        with patch("subprocess.run", side_effect=_happy_procs(stream)):
            from yamlgraph.node_factory.copilot_node import create_copilot_node

            node_fn = create_copilot_node(
                "t", _config(tmp_path, cli_flags={"model": "inception/mercury-2.5"})
            )
            with pytest.raises(RuntimeError, match="malformed or unknown event"):
                node_fn({})

    def test_nonzero_exit_fails_without_state_update(self, tmp_path: Path) -> None:
        procs = [
            _proc(VERSION_OK),
            _proc(SIMPLE_OK, returncode=1, stderr="Session not found"),
        ]
        with patch("subprocess.run", side_effect=procs):
            from yamlgraph.node_factory.copilot_node import create_copilot_node

            node_fn = create_copilot_node(
                "t", _config(tmp_path, cli_flags={"model": "inception/mercury-2.5"})
            )
            with pytest.raises(RuntimeError, match="exit 1"):
                node_fn({})


# --- REQ-YG-681: environment preserves provider credentials ------------------


@pytest.mark.req("REQ-YG-681")
class TestEnvironment:
    def test_provider_credentials_retained(self, tmp_path: Path) -> None:
        with (
            patch.dict(
                "os.environ",
                {
                    "ANTHROPIC_API_KEY": "sk-x",
                    "OPENAI_API_KEY": "sk-y",
                    "PATH": "/usr/bin",
                },
            ),
            patch("subprocess.run", side_effect=_happy_procs()) as mock_run,
        ):
            from yamlgraph.node_factory.copilot_node import create_copilot_node

            node_fn = create_copilot_node(
                "t", _config(tmp_path, cli_flags={"model": "inception/mercury-2.5"})
            )
            node_fn({})
        env = mock_run.call_args_list[1].kwargs["env"]
        assert env["ANTHROPIC_API_KEY"] == "sk-x"
        assert env["OPENAI_API_KEY"] == "sk-y"
        assert env["PATH"] == "/usr/bin"

    def test_otel_scoping_retained(self, tmp_path: Path) -> None:
        with (
            patch.dict("os.environ", {"YAMLGRAPH_OTEL_DIR": "/tmp/otel"}),
            patch("subprocess.run", side_effect=_happy_procs()) as mock_run,
        ):
            from yamlgraph.node_factory.copilot_node import create_copilot_node

            node_fn = create_copilot_node(
                "t", _config(tmp_path, cli_flags={"model": "inception/mercury-2.5"})
            )
            node_fn({})
        env = mock_run.call_args_list[1].kwargs["env"]
        assert env["COPILOT_OTEL_FILE_EXPORTER_PATH"] == "/tmp/otel/t.otel.jsonl"
