"""GitHub issue creation tool node for incaller intake mode (FR-360)."""

from __future__ import annotations

import re
import subprocess
from typing import Any

_TRUTHY = frozenset(
    {
        "1",
        "true",
        "yes",
        "y",
        "on",
        "opt-in",
        "opt in",
    }
)
_FALSEY = frozenset(
    {
        "",
        "0",
        "false",
        "no",
        "n",
        "off",
        "none",
        "null",
        "opt-out",
        "opt out",
    }
)
_ISSUE_NUMBER_PATTERN = re.compile(r"/issues/(\d+)(?:/)?$")


def _required_text(extracted: dict[str, Any], key: str) -> str:
    value = extracted.get(key)
    if value is None:
        raise ValueError(f"Missing required extracted field: {key}")
    text = str(value).strip()
    if not text:
        raise ValueError(f"Extracted field is empty: {key}")
    return text


def _normalize_chaplain_opt_in(raw_value: Any) -> bool:
    if raw_value is None:
        return False
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, int):
        if raw_value in (0, 1):
            return bool(raw_value)
        raise ValueError(f"Invalid chaplain_opt_in integer value: {raw_value}")
    if isinstance(raw_value, str):
        normalized = raw_value.strip().lower()
        if normalized in _TRUTHY:
            return True
        if normalized in _FALSEY:
            return False
        raise ValueError(f"Invalid chaplain_opt_in value: {raw_value}")
    raise ValueError(f"Unsupported chaplain_opt_in type: {type(raw_value).__name__}")


def _failure(message: str) -> dict[str, Any]:
    return {
        "issue_url": None,
        "issue_number": None,
        "issue_create_error": message,
    }


def create_issue(state: dict[str, Any]) -> dict[str, Any]:
    """Create a GitHub issue using gh CLI and return URL/number or explicit error."""
    extracted = state.get("extracted")
    if not isinstance(extracted, dict):
        return _failure("Missing extracted issue fields in state.extracted")

    try:
        issue_title = _required_text(extracted, "issue_title")
        issue_type = _required_text(extracted, "issue_type")
        issue_summary = _required_text(extracted, "issue_summary")
        chaplain_opt_in = _normalize_chaplain_opt_in(extracted.get("chaplain_opt_in"))
    except ValueError as exc:
        return _failure(str(exc))

    issue_body = f"### Issue type\n{issue_type}\n\n### Summary\n{issue_summary}"
    command = [
        "gh",
        "issue",
        "create",
        "--title",
        issue_title,
        "--body",
        issue_body,
    ]
    if chaplain_opt_in:
        command.extend(["--label", "chaplain"])

    try:
        completed = subprocess.run(  # noqa: S603
            command,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        return _failure(
            "GitHub CLI (gh) was not found. Install gh and authenticate with `gh auth login`."
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        detail = (
            stderr
            or stdout
            or f"`gh issue create` failed with exit code {exc.returncode}"
        )
        return _failure(f"Failed to create issue: {detail}")

    issue_url = completed.stdout.strip().splitlines()[-1] if completed.stdout else ""
    if not issue_url:
        return _failure("Failed to create issue: gh returned an empty issue URL")

    match = _ISSUE_NUMBER_PATTERN.search(issue_url)
    if not match:
        return _failure(f"Failed to parse issue number from URL: {issue_url}")

    return {
        "issue_url": issue_url,
        "issue_number": int(match.group(1)),
        "issue_create_error": None,
    }
