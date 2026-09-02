"""FR-959 RED: backend-aware lint for ``backend: claude`` (judgement §7, AC-12).

One direct test per lint code. Judgement:
feature-requests/FR-959-claude-cli-backend-primitive.judgement.md
"""

from __future__ import annotations

import json

import pytest

from yamlgraph.linter.patterns.copilot import check_copilot_node_structure


def _node(backend="claude", cli_flags=None, **extra) -> dict:
    cfg = {"type": "copilot", "prompt": "judge", "state_key": "r", "backend": backend}
    if cli_flags is not None:
        cfg["cli_flags"] = cli_flags
    cfg.update(extra)
    return cfg


def _codes(issues) -> list[str]:
    return [i.code for i in issues]


@pytest.mark.req("REQ-YG-640")
class TestClaudeBackendLint:
    def test_valid_claude_node_is_clean(self) -> None:
        issues = check_copilot_node_structure(
            "j",
            _node(
                cli_flags={
                    "model": "opus",
                    "tools": ["Read", "Glob", "Grep", "Write"],
                    "allowed_tools": ["Read", "Glob", "Grep", "Write"],
                    "max_turns": 40,
                }
            ),
        )
        assert issues == []

    @pytest.mark.parametrize("bad", ["cluade", 3, "", "CLAUDE", "Cli"])
    def test_e_backend_unknown(self, bad) -> None:
        issues = check_copilot_node_structure("j", _node(backend=bad))
        assert "E-COPILOT-BACKEND-UNKNOWN" in _codes(issues)
        assert all(i.severity == "error" for i in issues if "UNKNOWN" in i.code)

    def test_none_backend_is_not_unknown(self) -> None:
        cfg = _node()
        del cfg["backend"]
        assert "E-COPILOT-BACKEND-UNKNOWN" not in _codes(
            check_copilot_node_structure("j", cfg)
        )

    @pytest.mark.parametrize(
        "flags",
        [
            {"tools": "Read"},
            {"tools": ["Read", 3]},
            {"allowed_tools": "Read"},
            {"max_turns": 0},
            {"max_turns": -1},
            {"max_turns": True},
            {"max_turns": "40"},
            {"allow_all_tools": "yes"},
            {"continue_session": 1},
            {"resume": 42},
            {"bogus_flag": 1},
        ],
        ids=lambda f: json.dumps(f),
    )
    def test_e_claude_flag_shape(self, flags) -> None:
        issues = check_copilot_node_structure("j", _node(cli_flags=flags))
        assert "E-COPILOT-CLAUDE-FLAG-SHAPE" in _codes(issues)

    @pytest.mark.parametrize("key", ["tools", "allowed_tools", "max_turns"])
    def test_e_cli_flags_for_claude_only_keys_on_cli_backend(self, key) -> None:
        value = 40 if key == "max_turns" else ["Read"]
        issues = check_copilot_node_structure(
            "j", _node(backend="cli", cli_flags={key: value})
        )
        assert "E-COPILOT-CLI-FLAGS" in _codes(issues)

    @pytest.mark.parametrize("key", ["tools", "allowed_tools", "max_turns"])
    def test_e_api_flags_for_claude_only_keys_on_api_backend(self, key) -> None:
        value = 40 if key == "max_turns" else ["Read"]
        issues = check_copilot_node_structure(
            "j", _node(backend="api", cli_flags={key: value}, model="claude-sonnet-4.6")
        )
        assert "E-COPILOT-API-FLAGS" in _codes(issues)

    def test_e_claude_provider(self) -> None:
        issues = check_copilot_node_structure("j", _node(provider="anthropic"))
        assert "E-COPILOT-CLAUDE-PROVIDER" in _codes(issues)

    def test_w_claude_tools_broad_and_narrow(self) -> None:
        issues = check_copilot_node_structure(
            "j",
            _node(
                cli_flags={
                    "tools": ["Read"],
                    "allow_all_tools": True,
                    "allowed_tools": ["Read"],
                }
            ),
        )
        assert "W-COPILOT-CLAUDE-TOOLS" in _codes(issues)
        assert all(i.severity == "warning" for i in issues)

    def test_w_claude_approve_without_restrict(self) -> None:
        issues = check_copilot_node_structure(
            "j", _node(cli_flags={"allowed_tools": ["Read"]})
        )
        assert "W-COPILOT-CLAUDE-APPROVE-WITHOUT-RESTRICT" in _codes(issues)

    def test_w_claude_approve_with_restrict_is_quiet(self) -> None:
        issues = check_copilot_node_structure(
            "j", _node(cli_flags={"tools": ["Read"], "allowed_tools": ["Read"]})
        )
        assert "W-COPILOT-CLAUDE-APPROVE-WITHOUT-RESTRICT" not in _codes(issues)

    @pytest.mark.parametrize("model", ["gpt-5.6-sol", "gpt-4.1", "claude-sonnet-4-sol"])
    def test_w_claude_model_copilot_only_pattern(self, model) -> None:
        issues = check_copilot_node_structure("j", _node(cli_flags={"model": model}))
        assert "W-COPILOT-CLAUDE-MODEL" in _codes(issues)

    def test_w_claude_model_from_graph_defaults(self) -> None:
        """PR #563 review note: the effective default model is linted too."""
        issues = check_copilot_node_structure(
            "j", _node(cli_flags={}), graph_defaults={"model": "gpt-5.6-sol"}
        )
        assert "W-COPILOT-CLAUDE-MODEL" in _codes(issues)

    def test_w_claude_model_alias_is_quiet(self) -> None:
        issues = check_copilot_node_structure("j", _node(cli_flags={"model": "opus"}))
        assert "W-COPILOT-CLAUDE-MODEL" not in _codes(issues)

    def test_resume_and_continue_still_exclusive_on_claude(self) -> None:
        issues = check_copilot_node_structure(
            "j", _node(cli_flags={"resume": "abc", "continue_session": True})
        )
        assert "E-COPILOT-RESUME" in _codes(issues)
