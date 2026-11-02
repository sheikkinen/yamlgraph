"""FR-1155 decision provider factory (REQ-YG-726).

One factory seam for decision-model backends (the ``create_llm``
precedent, CAP-03): node code never imports a provider directly, and
provider-specific imports stay lazy inside their backend branch so the
module imports clean without optional dependencies installed.

Backends:

- ``mock`` — deterministic planted responses for network-free tests and
  keyless demos.
- ``system_one_adapter`` — the vendor's public LLM-backed implementation
  of the System One contract (optional extra ``decision``).
"""

import logging
from typing import Any, Protocol

from yamlgraph.models.decision_schema import (
    ChoiceDecision,
    ChoiceQuestion,
    NoulDecision,
    NoulQuestion,
    ScoreDecision,
    ScoreQuestion,
    normalize_answers,
    parse_question_config,
)

logger = logging.getLogger(__name__)

DecisionQuestionModel = NoulQuestion | ChoiceQuestion | ScoreQuestion
DecisionAnswerModel = NoulDecision | ChoiceDecision | ScoreDecision


class DecisionProvider(Protocol):
    """A provider that answers typed decision questions about a state blob."""

    def decide(
        self, state: str, questions: dict[str, Any]
    ) -> dict[str, DecisionAnswerModel]: ...


def _parse_questions(
    questions: dict[str, Any],
) -> dict[str, DecisionQuestionModel]:
    return {
        name: raw
        if isinstance(raw, (NoulQuestion, ChoiceQuestion, ScoreQuestion))
        else parse_question_config(raw)
        for name, raw in questions.items()
    }


class MockDecisionProvider:
    """Planted deterministic answers keyed by substring match on the state.

    ``mock_responses`` is an ordered list of ``{match, answers}`` rules;
    the first rule whose ``match`` is a substring of the rendered state
    wins. An unmatched state raises — never a substituted default
    (Commandment 6).
    """

    def __init__(self, mock_responses: list[dict[str, Any]] | None) -> None:
        if not mock_responses:
            raise ValueError(
                "mock decision provider requires mock_responses (list of "
                "{match, answers} rules)"
            )
        for rule in mock_responses:
            if "match" not in rule or "answers" not in rule:
                raise ValueError(
                    "each mock_responses rule requires 'match' and 'answers'"
                )
        self._rules = mock_responses

    def decide(
        self, state: str, questions: dict[str, Any]
    ) -> dict[str, DecisionAnswerModel]:
        parsed = _parse_questions(questions)
        for rule in self._rules:
            if rule["match"] in state:
                return normalize_answers(parsed, rule["answers"])
        raise ValueError(
            f"No mock response rule matches state (first 80 chars): {state[:80]!r}"
        )


class SystemOneAdapterProvider:
    """The vendor's LLM-backed System One client behind the factory seam.

    ``model_spec`` is ``"<llm_provider>:<model>"`` (for example
    ``"openai:gpt-4o-mini"``). The ``system_one_adapter`` import is lazy:
    it runs on first use, never at module import.
    """

    def __init__(self, model_spec: str) -> None:
        if not model_spec or ":" not in model_spec:
            raise ValueError(
                "system_one_adapter requires model in '<provider>:<model>' "
                f"form (got {model_spec!r})"
            )
        self._llm_provider, self._llm_model = model_spec.split(":", 1)
        self._client: Any = None

    def _ensure_client(self) -> Any:
        if self._client is None:
            try:
                from system_one_adapter import SystemOneAdapterClient
            except ImportError as e:  # pragma: no cover - environment-dependent
                raise ImportError(
                    "system-one-adapter is not installed; install the "
                    "'decision' extra: pip install 'yamlgraph[decision]'"
                ) from e
            self._client = SystemOneAdapterClient(
                structured_outputs=True,
                llm_answer_mode="probabilities",
                normalize_probabilities=True,
                provider=self._llm_provider,
                model=self._llm_model,
            )
        return self._client

    def decide(
        self, state: str, questions: dict[str, Any]
    ) -> dict[str, DecisionAnswerModel]:
        from system_one_adapter import Choice, Noul, Score

        parsed = _parse_questions(questions)
        sdk_questions: dict[str, Any] = {}
        for name, q in parsed.items():
            if isinstance(q, NoulQuestion):
                sdk_questions[name] = Noul(instructions=q.instructions)
            elif isinstance(q, ChoiceQuestion):
                sdk_questions[name] = Choice(
                    instructions=q.instructions, criteria=dict(q.options)
                )
            else:
                sdk_questions[name] = Score(
                    instructions=q.instructions, criteria=list(q.levels)
                )

        response = self._ensure_client().system_one(
            state=state, questions=sdk_questions
        )
        raw: dict[str, dict[str, Any]] = {}
        for name, answer in response.answers.items():
            payload = answer.model_dump()
            payload["kind"] = payload.pop("type")
            raw[name] = payload
        return normalize_answers(parsed, raw)


def create_decision_client(provider: str, **kwargs: Any) -> DecisionProvider:
    """Create a decision provider client.

    Args:
        provider: ``"mock"`` or ``"system_one_adapter"``.
        **kwargs: ``mock_responses`` for the mock backend; ``model``
            (``"<llm_provider>:<model>"``) for the adapter backend.

    Raises:
        ValueError: Unknown provider name or invalid backend configuration.
    """
    if provider == "mock":
        return MockDecisionProvider(kwargs.get("mock_responses"))
    if provider == "system_one_adapter":
        return SystemOneAdapterProvider(kwargs.get("model") or "")
    raise ValueError(
        f"Unknown decision provider: {provider!r} "
        "(expected 'mock' or 'system_one_adapter')"
    )
