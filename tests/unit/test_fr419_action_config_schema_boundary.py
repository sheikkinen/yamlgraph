"""RED tests for FR-419: ActionConfig schema-boundary validation.

Condemns five bug classes before the fix:
1. Unknown YAML key is silently dropped instead of rejected at parse time.
2. Alias keys (vars/error) from flat YAML syntax are not accepted.
3. Engine envelope metadata key `type` causes false ValidationError.
4. FR-319 variable interpolation is broken when shim is removed.
5. event_map normalization (lowercase/strip) is lost when shim helpers are deleted.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# ActionConfig import — RED until Step 1 of FR-419 is implemented
# ---------------------------------------------------------------------------
try:
    from yamlgraph.utils.fsm.action import ActionConfig

    _ACTION_CONFIG_AVAILABLE = True
except ImportError:
    _ACTION_CONFIG_AVAILABLE = False

# ---------------------------------------------------------------------------
# Chaplain adapter import helpers (same pattern as test_fr319)
# ---------------------------------------------------------------------------
WORKTREE = Path(__file__).resolve().parents[2]
ACTION_PATH = WORKTREE / ".chaplain" / "actions" / "yamlgraph_async_action.py"


class _StubBaseAction:
    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    def get_machine_name(self, context: dict) -> str:
        return context.get("machine_name", "test-machine")


def _load_chaplain_action(monkeypatch):
    sm_pkg = types.ModuleType("statemachine_engine")
    sm_actions_pkg = types.ModuleType("statemachine_engine.actions")
    sm_base_mod = types.ModuleType("statemachine_engine.actions.base")
    sm_base_mod.BaseAction = _StubBaseAction
    monkeypatch.setitem(sys.modules, "statemachine_engine", sm_pkg)
    monkeypatch.setitem(sys.modules, "statemachine_engine.actions", sm_actions_pkg)
    monkeypatch.setitem(sys.modules, "statemachine_engine.actions.base", sm_base_mod)
    spec = importlib.util.spec_from_file_location("_chaplain_action", ACTION_PATH)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.YamlgraphAsyncAction


# ---------------------------------------------------------------------------
# 1. Unknown key rejection
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-319")
class TestActionConfigUnknownKeyRejection:
    """FR-419: unknown keys must be rejected at parse time, not silently dropped."""

    def test_unknown_key_raises_validation_error(self) -> None:
        """event_ky (typo) must raise ValidationError, not be silently dropped."""
        pytest.importorskip("pydantic")
        from pydantic import ValidationError

        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined in yamlgraph.utils.fsm.action")

        with pytest.raises(ValidationError, match="event_ky"):
            ActionConfig.model_validate(
                {"graph": "foo.yaml", "event_ky": "judge_result"}
            )

    def test_known_key_does_not_raise(self) -> None:
        """event_key (correct spelling) must parse cleanly."""
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined in yamlgraph.utils.fsm.action")

        cfg = ActionConfig.model_validate(
            {"graph": "foo.yaml", "event_key": "judge_result"}
        )
        assert cfg.event_key == "judge_result"


# ---------------------------------------------------------------------------
# 2. Alias acceptance for flat YAML keys
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-319")
class TestActionConfigAliasAcceptance:
    """Flat YAML syntax (vars, error) must parse via AliasChoices without a shim."""

    def test_vars_alias_maps_to_variables(self) -> None:
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")

        cfg = ActionConfig.model_validate(
            {"graph": "foo.yaml", "vars": {"topic": "AI"}}
        )
        assert cfg.variables == {"topic": "AI"}

    def test_error_alias_maps_to_failure(self) -> None:
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")

        cfg = ActionConfig.model_validate({"graph": "foo.yaml", "error": "my_error"})
        assert cfg.failure == "my_error"

    def test_canonical_names_also_accepted(self) -> None:
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")

        cfg = ActionConfig.model_validate(
            {"graph": "foo.yaml", "variables": {"k": "v"}, "failure": "fail_ev"}
        )
        assert cfg.variables == {"k": "v"}
        assert cfg.failure == "fail_ev"


# ---------------------------------------------------------------------------
# 3. Engine envelope does not cause false ValidationError
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-319")
class TestActionConfigEnvelopeIsolation:
    """type: yamlgraph_async in engine config must not trigger extra=forbid failure."""

    def test_type_key_stripped_before_validation(self) -> None:
        """Parsing the raw engine config (with 'type' key) must not raise."""
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")

        # Simulate what the bridge execute() must do: strip envelope before parsing
        raw_engine_config = {
            "type": "yamlgraph_async",
            "graph": ".chaplain/graphs/step-judge-v2.yaml",
            "event_key": "judge_result",
            "event_map": {"APPROVE": "approve"},
            "success": "done",
            "error": "error",
            "timeout": 600,
        }
        _ENVELOPE_KEYS = {"type", "params"}
        payload = {
            k: v for k, v in raw_engine_config.items() if k not in _ENVELOPE_KEYS
        }

        # Must parse cleanly — no ValidationError for 'type'
        cfg = ActionConfig.model_validate(payload)
        assert cfg.event_key == "judge_result"
        assert cfg.timeout == 600


# ---------------------------------------------------------------------------
# 4. FR-319 interpolation behavior survives shim removal
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-319")
class TestFR319InterpolationPreservation:
    """pre_snapshot interpolation must survive after _translate_legacy_config is gone."""

    def test_variable_placeholder_resolved_from_context(self, monkeypatch) -> None:
        """vars with {context_key} placeholders must resolve via pre_snapshot."""
        from yamlgraph.utils.fsm.action import ActionConfig

        action_cls = _load_chaplain_action(monkeypatch)
        action = action_cls(
            {
                "graph": "some.yaml",
                "vars": {"fr_path": "{topic_file}"},
                "success": "done",
                "error": "error",
            }
        )
        context = {"topic_file": "/data/topics/gh-420.md", "main_dir": "/repo"}
        # Simulate what bridge execute() does: validate config, produce params dict
        raw = {k: v for k, v in action.config.items() if k not in {"type", "params"}}
        cfg = ActionConfig.model_validate(raw)
        params = cfg.model_dump(by_alias=False)
        action.pre_snapshot(params, context)
        assert params["variables"]["fr_path"] == "/data/topics/gh-420.md"

    def test_unresolved_normalize_empty_semantics_preserved(self, monkeypatch) -> None:
        """Keys in _NORMALIZE_EMPTY_ON_UNRESOLVED with unresolved placeholders become ''."""
        from yamlgraph.utils.fsm.action import ActionConfig

        action_cls = _load_chaplain_action(monkeypatch)
        action = action_cls(
            {
                "graph": "some.yaml",
                "vars": {"precommit_output": "{precommit_output}"},
                "success": "done",
                "error": "error",
            }
        )
        context = {"main_dir": "/repo"}  # precommit_output NOT in context
        raw = {k: v for k, v in action.config.items() if k not in {"type", "params"}}
        cfg = ActionConfig.model_validate(raw)
        params = cfg.model_dump(by_alias=False)
        action.pre_snapshot(params, context)
        assert params["variables"]["precommit_output"] == ""


# ---------------------------------------------------------------------------
# 5. event_map normalization is case-insensitive after shim removal
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-319")
class TestEventMapNormalizationPreservation:
    """event_map normalization now lives in ActionConfig._normalize_event_map validator."""

    def test_uppercase_event_map_key_normalized(self) -> None:
        """APPROVE in event_map must be lowercased so extract_event() can match 'approve'."""
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")

        cfg = ActionConfig.model_validate(
            {
                "graph": "judge.yaml",
                "event_map": {"APPROVE": "approve_event", "REJECT": "reject_event"},
            }
        )
        assert (
            "approve" in cfg.event_map
        ), "APPROVE must be normalized to lowercase in ActionConfig.event_map"
        assert "reject" in cfg.event_map

    def test_mixed_case_and_whitespace_key_normalized(self) -> None:
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")

        cfg = ActionConfig.model_validate(
            {"graph": "judge.yaml", "event_map": {" Amend ": "revise"}}
        )
        assert (
            "amend" in cfg.event_map
        ), "event_map keys must be stripped and lowercased by ActionConfig validator"


# ---------------------------------------------------------------------------
# 6. Author-annotation key `description` is stripped, not rejected
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-319")
class TestActionConfigDescriptionStrip:
    """Condemns the description-field regression introduced by FR-419.

    Every action block in watcher-pipeline-v2.yaml carries a `description:` field
    as a human-readable label.  FR-419's ActionConfig(extra='forbid') had no
    `description` field and did not strip it before validation, so *every* plan,
    judge, and enforce step emitted event=error immediately — before the graph
    was ever launched.

    Fix contract:
    - `description` is an author annotation (not an execution field).
    - It must be stripped alongside engine-envelope keys (`type`, `params`) in
      ``_STRIP_BEFORE_VALIDATE`` before ``ActionConfig.model_validate()`` is called.
    - ``ActionConfig`` itself must NOT have a ``description`` field.
    - Genuine execution-field typos must still be caught.
    """

    # Verbatim from watcher-pipeline-v2.yaml judge action (lines ~273-283)
    _REAL_JUDGE_ACTION = {
        "type": "yamlgraph_async",
        "description": "⚖️ Judging feature request (model B — fresh eyes)",
        "graph": ".chaplain/graphs/watcher-plan/step-judge-v2.yaml",
        "vars": {"topic_file": "{topic_file}", "fr_path": "{fr_path}"},
        "event_key": "judge_result",
        "event_map": {"APPROVE": "approve", "AMEND": "revise", "REJECT": "reject"},
        "success": "error",
        "error": "error",
        "timeout": 600,
    }

    def test_description_without_stripping_raises(self) -> None:
        """Condemns the bug: raw payload with description= raises ValidationError.

        This is what every pipeline run did before the fix — strip only
        {type, params} (old _ENVELOPE_KEYS), leaving description= in the payload.
        """
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")

        from pydantic import ValidationError

        old_envelope_keys = {"type", "params"}
        raw_with_description = {
            k: v
            for k, v in self._REAL_JUDGE_ACTION.items()
            if k not in old_envelope_keys
        }
        assert "description" in raw_with_description  # confirm the bug scenario

        with pytest.raises(ValidationError, match="description"):
            ActionConfig.model_validate(raw_with_description)

    def test_description_stripped_before_validate_succeeds(self) -> None:
        """Fix contract: _STRIP_BEFORE_VALIDATE removes description before parse."""
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")

        from yamlgraph.utils.fsm.action import _STRIP_BEFORE_VALIDATE

        assert (
            "description" in _STRIP_BEFORE_VALIDATE
        ), "_STRIP_BEFORE_VALIDATE must include 'description'"

        stripped = {
            k: v
            for k, v in self._REAL_JUDGE_ACTION.items()
            if k not in _STRIP_BEFORE_VALIDATE
        }
        cfg = ActionConfig.model_validate(stripped)
        assert cfg.graph == ".chaplain/graphs/watcher-plan/step-judge-v2.yaml"
        assert cfg.event_key == "judge_result"
        assert "approve" in cfg.event_map  # also exercises _normalize_event_map

    def test_description_not_a_model_field(self) -> None:
        """ActionConfig must NOT have a description field — it is not execution state."""
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")

        assert (
            "description" not in ActionConfig.model_fields
        ), "description belongs in _STRIP_BEFORE_VALIDATE, not in ActionConfig"

    def test_typo_still_rejected_after_fix(self) -> None:
        """Regression guard: stripping description must not weaken typo detection."""
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")

        from pydantic import ValidationError

        from yamlgraph.utils.fsm.action import _STRIP_BEFORE_VALIDATE

        payload = {"graph": "x.yaml", "evnt_key": "result"}  # deliberate typo
        stripped = {k: v for k, v in payload.items() if k not in _STRIP_BEFORE_VALIDATE}
        with pytest.raises(ValidationError, match="evnt_key"):
            ActionConfig.model_validate(stripped)
