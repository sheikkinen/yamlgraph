"""FR-1155 decision node schemas (REQ-YG-726).

Typed question configs and answer models for the ``decision`` node type.
The contract mirrors the public System One wire shapes (see
feature-requests/FR-1155-decision-node-calibration-audit.md, R-2 table):

- ``noul``   — 0–1 truth; the ``noul`` value *is* the probability, there
  is no separate confidence field.
- ``choice`` — pick one label from a mapping of up to 255 labels;
  answers carry ``choice``, ``confidence``, and per-label probabilities.
- ``score``  — ordered rubric levels from zero; answers carry the
  expected ``score`` (may fall between levels), ``confidence``, a
  ``legend``, and per-level probabilities.

All provider output is normalized here, at the boundary where external
data enters (the_one_law); raw provider dictionaries never reach graph
state.
"""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

MAX_CHOICE_CARDINALITY = 255


# ---------------------------------------------------------------------------
# Question configs (graph YAML side)
# ---------------------------------------------------------------------------


class NoulQuestion(BaseModel):
    """A yes/no question; the answer is the probability of 'yes'."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["noul"]
    instructions: str = Field(min_length=1)


class ChoiceQuestion(BaseModel):
    """Choose one label from a described set (native cap: 255 labels)."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["choice"]
    instructions: str | None = None
    options: dict[str, str | None] = Field(
        min_length=1, max_length=MAX_CHOICE_CARDINALITY
    )


class ScoreQuestion(BaseModel):
    """Score against an ordered rubric; one description per level from zero."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["score"]
    instructions: str | None = None
    levels: list[str] = Field(min_length=1)


DecisionQuestion = Annotated[
    NoulQuestion | ChoiceQuestion | ScoreQuestion,
    Field(discriminator="kind"),
]

_QUESTION_ADAPTER: TypeAdapter[Any] = TypeAdapter(DecisionQuestion)


def parse_question_config(
    raw: dict[str, Any],
) -> NoulQuestion | ChoiceQuestion | ScoreQuestion:
    """Parse one question config dict; raises pydantic.ValidationError (a ValueError)."""
    return _QUESTION_ADAPTER.validate_python(raw)


# ---------------------------------------------------------------------------
# Answer models (provider boundary)
# ---------------------------------------------------------------------------


class NoulDecision(BaseModel):
    """A yes/no answer: P(true). No separate confidence field exists."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["noul"] = "noul"
    noul: float = Field(ge=0.0, le=1.0)


class ChoiceDecision(BaseModel):
    """A selected label with confidence and per-label probabilities."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["choice"] = "choice"
    choice: str
    confidence: float = Field(ge=0.0, le=1.0)
    probabilities: dict[str, float]


class ScoreDecision(BaseModel):
    """An expected score with confidence, legend, and level probabilities."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["score"] = "score"
    score: float
    confidence: float = Field(ge=0.0, le=1.0)
    legend: dict[int, str] = Field(default_factory=dict)
    probabilities: dict[int, float]


DecisionAnswer = Annotated[
    NoulDecision | ChoiceDecision | ScoreDecision,
    Field(discriminator="kind"),
]

_ANSWER_ADAPTER: TypeAdapter[Any] = TypeAdapter(DecisionAnswer)


def normalize_answers(
    questions: dict[str, NoulQuestion | ChoiceQuestion | ScoreQuestion],
    raw_answers: dict[str, Any],
) -> dict[str, NoulDecision | ChoiceDecision | ScoreDecision]:
    """Normalize raw provider answers against the asked questions.

    One boundary for every provider (mock and real): every question must
    be answered, answer kinds must match question kinds, choice labels
    must be members of the declared options, and score probabilities must
    stay within the declared levels. Raises ValueError on any violation —
    no silent substitution (Commandment 6).
    """
    unknown = set(raw_answers) - set(questions)
    if unknown:
        raise ValueError(f"Answers for unknown questions: {sorted(unknown)}")

    normalized: dict[str, NoulDecision | ChoiceDecision | ScoreDecision] = {}
    for name, question in questions.items():
        if name not in raw_answers:
            raise ValueError(f"Missing answer for question '{name}'")
        raw = raw_answers[name]
        answer = raw if _is_answer_model(raw) else _ANSWER_ADAPTER.validate_python(raw)
        if answer.kind != question.kind:
            raise ValueError(
                f"Answer kind '{answer.kind}' does not match question kind "
                f"'{question.kind}' for '{name}'"
            )
        if isinstance(answer, ChoiceDecision):
            _validate_choice(name, question, answer)
        if isinstance(answer, ScoreDecision):
            answer = _validate_score(name, question, answer)
        normalized[name] = answer
    return normalized


def _is_answer_model(value: Any) -> bool:
    return isinstance(value, (NoulDecision, ChoiceDecision, ScoreDecision))


def _validate_choice(
    name: str, question: ChoiceQuestion, answer: ChoiceDecision
) -> None:
    if answer.choice not in question.options:
        raise ValueError(
            f"Choice '{answer.choice}' for '{name}' is not a declared option "
            f"(options: {sorted(question.options)})"
        )
    stray = set(answer.probabilities) - set(question.options)
    if stray:
        raise ValueError(
            f"Probabilities for '{name}' name undeclared options: {sorted(stray)}"
        )


def _validate_score(
    name: str, question: ScoreQuestion, answer: ScoreDecision
) -> ScoreDecision:
    levels = range(len(question.levels))
    stray = set(answer.probabilities) - set(levels)
    if stray:
        raise ValueError(
            f"Probabilities for '{name}' name undeclared levels: {sorted(stray)}"
        )
    if not answer.legend:
        legend = dict(enumerate(question.levels))
        return answer.model_copy(update={"legend": legend})
    return answer
