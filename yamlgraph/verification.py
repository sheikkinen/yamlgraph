"""FR-164/FR-166: Verification gate evaluator.

Deterministic pattern matching for verification questions.
Extracts testable claims from natural-language predictions and
checks them against actual node output.

Supported patterns:
- count_range: "Will return N-M items/documents/..."
- non_empty: "Will return non-empty"
- contains: "Will contain {keyword}"
- annotation: (no pattern match) — logged, no failure
"""

import logging
import re
from typing import Any

from pydantic import BaseModel, Field, model_validator

from yamlgraph.models.schemas import ErrorType, VerificationViolation

logger = logging.getLogger(__name__)

# Pattern: "Will return N-M items/documents/results/..."
COUNT_RANGE_RE = re.compile(r"(\d+)\s*-\s*(\d+)\s+\w+", re.IGNORECASE)

# Pattern: "Will return non-empty"
NON_EMPTY_RE = re.compile(r"non[_-]?empty", re.IGNORECASE)

# Pattern: "Will contain {keyword}" — extract keyword after "contain"
CONTAINS_RE = re.compile(r"(?:will\s+)?contain\s+(.+)", re.IGNORECASE)

# Variable interpolation: {var_name}
VAR_RE = re.compile(r"\{(\w+)\}")


class CountRangeClaim(BaseModel):
    """Parsed count range from verification question (FR-166).

    Validates at the boundary where regex-extracted data enters,
    ensuring min_count ≤ max_count. An inverted range is a config
    bug that must be surfaced immediately.
    """

    min_count: int = Field(ge=0, description="Minimum expected count")
    max_count: int = Field(ge=0, description="Maximum expected count")

    @model_validator(mode="after")
    def validate_range(self) -> "CountRangeClaim":
        """Ensure min ≤ max — inverted ranges are config bugs."""
        if self.min_count > self.max_count:
            raise ValueError(
                f"Inverted count range: min ({self.min_count}) > max ({self.max_count}). "
                f"Write 'N-M items' where N ≤ M."
            )
        return self


class VerificationError(Exception):
    """Raised when on_fail: halt and verification fails."""

    def __init__(self, node_name: str, violation: VerificationViolation):
        self.node_name = node_name
        self.violation = violation
        super().__init__(
            f"Verification failed for node '{node_name}': "
            f"{violation.prediction} (check: {violation.check_type}, "
            f"actual: {violation.actual})"
        )


def _interpolate_question(question: str, state: dict[str, Any]) -> str:
    """Interpolate {var} placeholders in question from state."""

    def replace(match: re.Match) -> str:
        key = match.group(1)
        return str(state.get(key, match.group(0)))

    return VAR_RE.sub(replace, question)


def evaluate_verification(
    question: str,
    actual: Any,
    state: dict[str, Any],
) -> VerificationViolation | None:
    """Evaluate a verification question against actual output.

    Args:
        question: The falsifiable prediction (may contain {var} placeholders)
        actual: The actual output from node execution
        state: Current graph state for variable interpolation

    Returns:
        VerificationViolation if prediction is violated, None if satisfied
    """
    interpolated = _interpolate_question(question, state)

    # Try count_range: "Will return N-M items/documents/..."
    count_match = COUNT_RANGE_RE.search(interpolated)
    if count_match:
        claim = CountRangeClaim(
            min_count=int(count_match.group(1)),
            max_count=int(count_match.group(2)),
        )
        try:
            length = len(actual)
        except TypeError:
            length = 0

        if claim.min_count <= length <= claim.max_count:
            return None
        return VerificationViolation(
            type=ErrorType.VERIFICATION_ERROR,
            message=(
                f"Count range check failed: expected {claim.min_count}-{claim.max_count} items, "
                f"got {length}"
            ),
            node="",  # Filled by caller
            prediction=question,
            actual=repr(actual),
            check_type="count_range",
            details={
                "expected_min": claim.min_count,
                "expected_max": claim.max_count,
                "actual_count": length,
            },
        )

    # Try non_empty: "Will return non-empty"
    if NON_EMPTY_RE.search(interpolated):
        if actual:
            return None
        return VerificationViolation(
            type=ErrorType.VERIFICATION_ERROR,
            message=f"Non-empty check failed: got {repr(actual)}",
            node="",
            prediction=question,
            actual=repr(actual),
            check_type="non_empty",
        )

    # Try contains: "Will contain {keyword}"
    contains_match = CONTAINS_RE.search(interpolated)
    if contains_match:
        keyword = contains_match.group(1).strip()
        if keyword in str(actual):
            return None
        return VerificationViolation(
            type=ErrorType.VERIFICATION_ERROR,
            message=f"Contains check failed: '{keyword}' not found in output",
            node="",
            prediction=question,
            actual=repr(actual),
            check_type="contains",
        )

    # No pattern matched — annotation only
    logger.info(f"Verification annotation (no deterministic check): {interpolated}")
    return None
