"""FR-933: bounded, diagnostic-only feedback for a rejected structured output.

Built from Pydantic's structured error data (`loc`, `msg`, `type`, `ctx`)
rather than `str(ValidationError)`, whose rendering embeds `input_value`
and would carry the rejected content straight back into the next prompt.

The framework reports the constraint; the model repairs its own output.
Nothing here edits, coerces, truncates or replaces a value — those are the
mechanisms FR-408 was rejected for.
"""

from pydantic import ValidationError

_REDACTED = "<omitted>"

# Constraint keys pydantic reports in ctx; the limit is safe to echo, the
# value is not.
_LIMIT_KEYS = (
    "max_length",
    "min_length",
    "le",
    "ge",
    "lt",
    "gt",
    "multiple_of",
    "max_digits",
    "decimal_places",
    "pattern",
)


def _sized(value: object) -> int | None:
    if isinstance(value, str | list | tuple | dict | set):
        return len(value)
    return None


def _sanitize(message: str, value: object) -> str:
    """Drop the rejected value from a message that quoted it."""
    if not isinstance(value, str) or len(value) < 8:
        return message
    return message.replace(value, _REDACTED)


def _describe(err: dict) -> str:
    location = ".".join(str(part) for part in err.get("loc", ())) or "<root>"
    detail = _sanitize(str(err.get("msg", "")), err.get("input"))
    facts = [
        f"{key}={err['ctx'][key]}"
        for key in _LIMIT_KEYS
        if key in (err.get("ctx") or {})
    ]
    if (actual := _sized(err.get("input"))) is not None:
        facts.append(f"you sent {actual}")
    suffix = f" ({', '.join(facts)})" if facts else ""
    return f"- field '{location}': {detail}{suffix}"


def build_validation_feedback(error: Exception) -> str | None:
    """Describe a schema rejection, or None when there is nothing to report.

    Returning None for every non-validation exception is what keeps
    transient faults (timeouts, resets, 429s) retrying identically, which
    is the behaviour retry was built for.
    """
    if not isinstance(error, ValidationError):
        return None

    violations = [_describe(err) for err in error.errors()]
    if not violations:
        return None

    return (
        "CORRECTION: your previous response was rejected by schema "
        "validation and was not used. It failed on:\n"
        + "\n".join(violations)
        + "\nResend the complete object with every field satisfying its "
        "constraints. Do not quote or restate your rejected answer — write "
        "a new, shorter value for each field listed above."
    )
