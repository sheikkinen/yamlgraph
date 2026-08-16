"""FR-678: Narrow bare exception catch in agent structured-output fallback.

The cheap JSON-parse-and-validate path in ``_try_structured_output`` must
catch only ``pydantic.ValidationError`` (schema mismatch is a legitimate
"content not parseable for this schema" signal). Programming defects —
``TypeError`` from a bad model, ``AttributeError`` from a normalization bug,
``ValueError`` from a broken ``extract_json`` — must propagate instead of
being silently converted into an expensive LLM re-invoke (Commandment 6,
``downstream_fix`` trap).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.schema_loader import load_schema_from_yaml
from yamlgraph.tools.agent import _try_structured_output

PROMPT_YAML_WITH_SCHEMA = """\
schema:
  name: SimpleVerdict
  fields:
    verdict:
      type: str
      description: "APPROVE or REJECT"
    reasoning:
      type: str
      description: "Why"
system: You are a judge.
user: "Judge: {input}"
"""


def _output_model():
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        f.write(PROMPT_YAML_WITH_SCHEMA)
        f.flush()
        return load_schema_from_yaml(Path(f.name))


class TestNarrowedStructuredOutputCatch:
    """FR-678: only ValidationError triggers fallback; defects propagate."""

    @pytest.mark.req("REQ-YG-422")
    def test_type_error_from_model_validate_propagates(self):
        """A TypeError from model_validate is a defect — it must propagate,
        not be swallowed into an LLM re-invoke."""
        content = '{"verdict": "APPROVE", "reasoning": "Solid"}'

        bad_model = MagicMock()
        bad_model.model_validate.side_effect = TypeError("bad model definition")

        llm_base = MagicMock()

        with pytest.raises(TypeError, match="bad model definition"):
            _try_structured_output(
                content, msgs=[], output_model=bad_model, llm_base=llm_base
            )
        # The LLM fallback must NOT have been reached.
        llm_base.with_structured_output.assert_not_called()

    @pytest.mark.req("REQ-YG-422")
    def test_value_error_from_extract_json_propagates(self):
        """A ValueError raised by extract_json is not a normal parse miss —
        it must propagate, not trigger the LLM fallback."""
        content = "anything"
        llm_base = MagicMock()

        with (
            patch(
                "yamlgraph.tools.agent.extract_json",
                side_effect=ValueError("extract_json blew up"),
            ),
            pytest.raises(ValueError, match="extract_json blew up"),
        ):
            _try_structured_output(
                content, msgs=[], output_model=_output_model(), llm_base=llm_base
            )
        llm_base.with_structured_output.assert_not_called()

    @pytest.mark.req("REQ-YG-422")
    def test_validation_error_falls_back_to_llm(self):
        """A ValidationError (schema mismatch in extracted JSON) is a
        legitimate fallback trigger — re-invoke the LLM."""
        output_model = _output_model()
        # Valid JSON dict but wrong schema (missing required fields) →
        # model_validate raises ValidationError.
        content = '{"unexpected_field": 123}'

        mock_structured = MagicMock()
        mock_structured.invoke.return_value = output_model(
            verdict="APPROVE", reasoning="recovered"
        )
        llm_base = MagicMock()
        llm_base.with_structured_output.return_value = mock_structured

        result = _try_structured_output(
            content, msgs=[], output_model=output_model, llm_base=llm_base
        )

        assert isinstance(result, dict)
        assert result["verdict"] == "APPROVE"
        llm_base.with_structured_output.assert_called_once()

    @pytest.mark.req("REQ-YG-422")
    def test_prose_content_falls_back_without_exception(self):
        """Non-JSON prose makes extract_json return a non-dict; fallback
        triggers via the isinstance check, not exception swallowing."""
        output_model = _output_model()
        content = "This is prose with no JSON at all."

        mock_structured = MagicMock()
        mock_structured.invoke.return_value = output_model(
            verdict="REJECT", reasoning="prose"
        )
        llm_base = MagicMock()
        llm_base.with_structured_output.return_value = mock_structured

        result = _try_structured_output(
            content, msgs=[], output_model=output_model, llm_base=llm_base
        )

        assert isinstance(result, dict)
        assert result["verdict"] == "REJECT"

    @pytest.mark.req("REQ-YG-422")
    def test_response_format_unavailable_falls_back_to_function_calling(self):
        """FR-809 field defect: DeepSeek rejects response_format with a 400
        ('This response_format type is unavailable now'); the structured
        re-invoke must fall back to method=function_calling like the FR-458
        invalid_json_schema class, not surface the provider 400."""
        output_model = _output_model()
        content = "This is prose with no JSON at all."

        deepseek_400 = Exception(
            "Error code: 400 - {'error': {'message': 'This response_format "
            "type is unavailable now', 'type': 'invalid_request_error', "
            "'param': None, 'code': 'invalid_request_error'}}"
        )
        strict_llm = MagicMock()
        strict_llm.invoke.side_effect = deepseek_400
        fc_llm = MagicMock()
        fc_llm.invoke.return_value = output_model(
            verdict="APPROVE", reasoning="recovered via function_calling"
        )
        llm_base = MagicMock()
        llm_base.with_structured_output.side_effect = [strict_llm, fc_llm]

        result = _try_structured_output(
            content, msgs=[], output_model=output_model, llm_base=llm_base
        )

        assert isinstance(result, dict)
        assert result["verdict"] == "APPROVE"
        assert llm_base.with_structured_output.call_args_list[1].kwargs == {
            "method": "function_calling"
        }

    @pytest.mark.req("REQ-YG-422")
    def test_tool_choice_rejected_falls_back_to_plain_reinvoke(self):
        """FR-809 field defect: DeepSeek thinking mode rejects BOTH
        response_format and tool_choice; with no partial dict available the
        agent must fall back to a plain re-invoke and parse the JSON from
        raw content, not surface the provider 400."""
        output_model = _output_model()
        content = "This is prose with no JSON at all."

        strict_llm = MagicMock()
        strict_llm.invoke.side_effect = Exception(
            "Error code: 400 - {'error': {'message': 'This response_format "
            "type is unavailable now'}}"
        )
        fc_llm = MagicMock()
        fc_llm.invoke.side_effect = Exception(
            "Error code: 400 - {'error': {'message': 'Thinking mode does not "
            "support this tool_choice'}}"
        )
        llm_base = MagicMock()
        llm_base.with_structured_output.side_effect = [strict_llm, fc_llm]
        plain_response = MagicMock()
        plain_response.content = '{"verdict": "APPROVE", "reasoning": "plain"}'
        llm_base.invoke.return_value = plain_response

        result = _try_structured_output(
            content, msgs=[], output_model=output_model, llm_base=llm_base
        )

        assert isinstance(result, dict)
        assert result["verdict"] == "APPROVE"
        llm_base.invoke.assert_called_once()

    @pytest.mark.req("REQ-YG-422")
    def test_plain_reinvoke_unparseable_raises(self):
        """The plain re-invoke tier must not hedge: unparseable content
        raises rather than returning a fabricated result (Commandment 6)."""
        output_model = _output_model()

        strict_llm = MagicMock()
        strict_llm.invoke.side_effect = Exception("response_format unavailable")
        fc_llm = MagicMock()
        fc_llm.invoke.side_effect = Exception("does not support this tool_choice")
        llm_base = MagicMock()
        llm_base.with_structured_output.side_effect = [strict_llm, fc_llm]
        plain_response = MagicMock()
        plain_response.content = "still prose, no JSON"
        llm_base.invoke.return_value = plain_response

        with pytest.raises(Exception, match="tool_choice"):
            _try_structured_output(
                "prose", msgs=[], output_model=output_model, llm_base=llm_base
            )

    @pytest.mark.req("REQ-YG-422")
    def test_validation_fallback_logs_at_warning(self, caplog):
        """The fallback trigger must be observable at WARNING with the
        exception class name (Commandment 9 — the re-invoke costs money)."""
        import logging

        output_model = _output_model()
        content = '{"unexpected_field": 123}'

        mock_structured = MagicMock()
        mock_structured.invoke.return_value = output_model(
            verdict="APPROVE", reasoning="ok"
        )
        llm_base = MagicMock()
        llm_base.with_structured_output.return_value = mock_structured

        agent_logger = logging.getLogger("yamlgraph")
        prev_propagate = agent_logger.propagate
        agent_logger.propagate = True
        try:
            with caplog.at_level(logging.WARNING, logger="yamlgraph.tools.agent"):
                _try_structured_output(
                    content, msgs=[], output_model=output_model, llm_base=llm_base
                )
        finally:
            agent_logger.propagate = prev_propagate

        warnings = [
            rec
            for rec in caplog.records
            if rec.levelno == logging.WARNING and "ValidationError" in rec.getMessage()
        ]
        assert (
            warnings
        ), f"Expected WARNING log naming ValidationError, got {caplog.records}"
