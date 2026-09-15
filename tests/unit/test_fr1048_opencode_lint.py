"""FR-1048 lint: backend='opencode' rules (REQ-YG-680/681).

E-COPILOT-OPENCODE-FLAG-SHAPE and E-COPILOT-OPENCODE-MODEL, plus the
reconciled ownership of the opencode flag set (model/resume are shared with
the cli backend; the five dropped flags and continue_session are forbidden
extras).
"""

from __future__ import annotations

import pytest

from yamlgraph.linter.patterns.copilot import check_copilot_node_structure


def _issues(node_config: dict, defaults: dict | None = None) -> list:
    return check_copilot_node_structure(
        "t", {"type": "copilot", **node_config}, graph_defaults=defaults or {}
    )


def _codes(issues: list) -> set:
    return {i.code for i in issues}


@pytest.mark.req("REQ-YG-680")
class TestOpenCodeFlagShape:
    def test_valid_flags_clean(self) -> None:
        issues = _issues(
            {"backend": "opencode", "cli_flags": {"model": "inception/mercury-2.5"}}
        )
        assert _codes(issues) == set()

    @pytest.mark.parametrize(
        "cli_flags",
        [
            {"model": 3},
            {"resume": ""},
            {"agent": "judge"},
            {"dir": "/tmp"},
            {"variant": "high"},
            {"thinking": True},
            {"auto": True},
            {"continue_session": True},
        ],
    )
    def test_malformed_or_dropped_flags_error(self, cli_flags) -> None:
        issues = _issues({"backend": "opencode", "cli_flags": cli_flags})
        assert "E-COPILOT-OPENCODE-FLAG-SHAPE" in _codes(issues)


@pytest.mark.req("REQ-YG-681")
class TestOpenCodeModel:
    @pytest.mark.parametrize("bad", ["model-only", "/model", "provider/"])
    def test_malformed_model_error(self, bad) -> None:
        issues = _issues({"backend": "opencode", "cli_flags": {"model": bad}})
        assert "E-COPILOT-OPENCODE-MODEL" in _codes(issues)

    def test_blank_model_is_flag_shape_error(self) -> None:
        issues = _issues({"backend": "opencode", "cli_flags": {"model": ""}})
        assert "E-COPILOT-OPENCODE-FLAG-SHAPE" in _codes(issues)

    def test_missing_model_error(self) -> None:
        issues = _issues({"backend": "opencode"})
        assert "E-COPILOT-OPENCODE-MODEL" in _codes(issues)

    def test_node_model_satisfies(self) -> None:
        issues = _issues({"backend": "opencode", "model": "inception/mercury-2.5"})
        assert _codes(issues) == set()

    def test_defaults_model_satisfies(self) -> None:
        issues = _issues(
            {"backend": "opencode"}, defaults={"model": "inception/mercury-2.5"}
        )
        assert _codes(issues) == set()

    def test_invalid_higher_priority_fails(self) -> None:
        # cli_flags.model grammar-invalid + valid node.model: no fallthrough.
        issues = _issues(
            {
                "backend": "opencode",
                "cli_flags": {"model": "model-only"},
                "model": "inception/mercury-2.5",
            }
        )
        assert "E-COPILOT-OPENCODE-MODEL" in _codes(issues)


@pytest.mark.req("REQ-YG-680")
class TestUnknownBackend:
    def test_unknown_backend_error(self) -> None:
        issues = _issues({"backend": "opnecode"})
        assert "E-COPILOT-BACKEND-UNKNOWN" in _codes(issues)

    def test_none_backend_defaults_to_cli(self) -> None:
        issues = _issues({"backend": None, "cli_flags": {}})
        assert "E-COPILOT-BACKEND-UNKNOWN" not in _codes(issues)
