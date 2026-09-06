"""RED tests for FR-419: ActionConfig schema-boundary validation.

Condemns five bug classes before the fix:
1. Unknown YAML key is silently dropped instead of rejected at parse time.
2. Alias keys (vars/error) from flat YAML syntax are not accepted.
3. Engine envelope metadata key `type` causes false ValidationError.
4. FR-319 variable interpolation is broken when shim is removed.
5. event_map normalization (lowercase/strip) is lost when shim helpers are deleted.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# ActionConfig import — RED until Step 1 of FR-419 is implemented
# ---------------------------------------------------------------------------
import pytest

pytestmark = pytest.mark.process

try:
    from yamlgraph.utils.fsm.action import ActionConfig

    _ACTION_CONFIG_AVAILABLE = True
except ImportError:
    _ACTION_CONFIG_AVAILABLE = False

# ---------------------------------------------------------------------------
# Chaplain adapter import helpers (same pattern as test_fr319)
# ---------------------------------------------------------------------------
WORKTREE = Path(__file__).resolve().parents[2]
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


# ---------------------------------------------------------------------------
# Bug: statemachine_engine passes context dict as vars value (single-expression
# template substitution passes through raw dict instead of stringifying)
# ---------------------------------------------------------------------------


class TestActionConfigVariablesCoercion:
    """AC: variables values that are non-string must be coerced to JSON strings.

    Condemns the failure seen in validate_fix when validate_gate_output (a dict
    from the custom_action_validate_gate) is passed as-is via single-expression
    template substitution by statemachine_engine.
    """

    # Real shape of validate_gate_output from watcher-pipeline-v2 validate_gate
    _GATE_OUTPUT_DICT = {
        "attempt": 1,
        "max_attempts": 5,
        "check": "branch_freshness",
        "reason": "branch is behind origin/main (rebase or merge required)",
    }

    @pytest.mark.req("REQ-YG-319")
    def test_dict_variable_value_coerced_to_json_string(self) -> None:
        """Fix contract: dict value in vars must be JSON-serialised to string."""
        import json

        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")

        payload = {
            "graph": ".chaplain/graphs/watcher-enforce/validate-session.yaml",
            "vars": {
                "fr_path": "feature-requests/FR-xxx/FR-xxx.md",
                "validate_gate_output": self._GATE_OUTPUT_DICT,
            },
            "success": "validate_done",
        }

        cfg = ActionConfig.model_validate(payload)
        coerced = cfg.variables["validate_gate_output"]
        assert isinstance(coerced, str), f"Expected str, got {type(coerced)}"
        # Must round-trip as valid JSON
        parsed = json.loads(coerced)
        assert parsed["check"] == "branch_freshness"

    @pytest.mark.req("REQ-YG-319")
    def test_int_variable_value_coerced_to_string(self) -> None:
        """int variable values (e.g. attempt count) must also coerce."""
        payload = {
            "graph": "x.yaml",
            "vars": {"attempt": 3},
        }
        cfg = ActionConfig.model_validate(payload)
        assert cfg.variables["attempt"] == "3"

    @pytest.mark.req("REQ-YG-319")
    def test_string_variable_unchanged(self) -> None:
        """Normal string values must pass through untouched."""
        payload = {
            "graph": "x.yaml",
            "vars": {"fr_path": "feature-requests/FR-999/FR-999.md"},
        }
        cfg = ActionConfig.model_validate(payload)
        assert cfg.variables["fr_path"] == "feature-requests/FR-999/FR-999.md"


# ---------------------------------------------------------------------------
# FR-422: event_map strict typing and nested params strip consistency
# ---------------------------------------------------------------------------


class TestEventMapStrictTyping:
    """FR-422 AC-01/02/03: event_map must reject non-null non-dict values.

    Defensive hardening: not a live failure, but silently wrong —
    event_map: "APPROVE" currently normalizes to {} and routing falls
    through to success event without matching any keyword.
    """

    @pytest.mark.req("REQ-YG-319")
    def test_string_event_map_raises(self) -> None:
        """event_map as string must raise ValidationError, not silently become {}."""
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="event_map"):
            ActionConfig.model_validate({"graph": "x.yaml", "event_map": "APPROVE"})

    @pytest.mark.req("REQ-YG-319")
    def test_list_event_map_raises(self) -> None:
        """event_map as list must raise ValidationError."""
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="event_map"):
            ActionConfig.model_validate(
                {"graph": "x.yaml", "event_map": ["APPROVE", "REJECT"]}
            )

    @pytest.mark.req("REQ-YG-319")
    def test_null_event_map_normalizes_to_empty_dict(self) -> None:
        """event_map: null (None) must normalize to {} — not raise."""
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")

        cfg = ActionConfig.model_validate({"graph": "x.yaml", "event_map": None})
        assert cfg.event_map == {}

    @pytest.mark.req("REQ-YG-319")
    def test_dict_event_map_still_normalizes(self) -> None:
        """Existing dict event_map normalization must not regress."""
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")

        cfg = ActionConfig.model_validate(
            {
                "graph": "x.yaml",
                "event_map": {"APPROVE": "approve", " AMEND ": "revise"},
            }
        )
        assert cfg.event_map == {"approve": "approve", "amend": "revise"}


class TestNestedParamsStripConsistency:
    """FR-422 AC-04/05: _STRIP_BEFORE_VALIDATE applied consistently to params branch.

    Defensive hardening: nested params style not in watcher-pipeline-v2.yaml
    currently, but the execute() path exists and the strip gap is real.
    """

    @pytest.mark.req("REQ-YG-319")
    def test_nested_params_with_description_raises_without_strip(self) -> None:
        """Condemning test: description in params dict fails validation (proves gap)."""
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")
        from pydantic import ValidationError

        from yamlgraph.utils.fsm.action import _STRIP_BEFORE_VALIDATE

        # Simulate the execute() params branch WITHOUT stripping
        params = {
            "graph": "graphs/classifier.yaml",
            "description": "nested style description",
            "success": "ok",
            "error": "err",
        }
        raw_unstripped = dict(params)  # no strip applied

        assert "description" in raw_unstripped
        with pytest.raises(ValidationError, match="description"):
            ActionConfig.model_validate(raw_unstripped)

        # Fix path: strip before validate
        raw_stripped = {
            k: v for k, v in params.items() if k not in _STRIP_BEFORE_VALIDATE
        }
        cfg = ActionConfig.model_validate(raw_stripped)
        assert cfg.graph == "graphs/classifier.yaml"

    @pytest.mark.req("REQ-YG-319")
    def test_nested_params_typo_still_rejected_after_fix(self) -> None:
        """Regression guard: stripping description must not weaken typo detection."""
        if not _ACTION_CONFIG_AVAILABLE:
            pytest.fail("ActionConfig not yet defined")
        from pydantic import ValidationError

        from yamlgraph.utils.fsm.action import _STRIP_BEFORE_VALIDATE

        params = {
            "graph": "x.yaml",
            "description": "label",
            "evnt_key": "result",  # deliberate typo
        }
        raw_stripped = {
            k: v for k, v in params.items() if k not in _STRIP_BEFORE_VALIDATE
        }
        with pytest.raises(ValidationError, match="evnt_key"):
            ActionConfig.model_validate(raw_stripped)
