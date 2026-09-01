"""Pydantic boundary models for issue-queue delegation (FR-949, REQ-YG-637).

Every issue body crosses DelegationRequest before checkout or launch.
Execution truth (DelegationStatus) is separate from publication outcome
(PublicationStatus) per the third judgement's R-2.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# R-1: fixed inner payload deadline; the workflow's 30-min timeout-minutes
# is only the outer platform kill switch and is never published as TIMEOUT.
INNER_DEADLINE_SECONDS = 25 * 60

# Worker-side authoritative credit cap (issue may request less, never more).
MAX_REPORTED_CREDITS = 60

# owner/name, no leading dash on either segment (option-like shapes refused).
REPO_PATTERN = r"^[A-Za-z0-9._][A-Za-z0-9._-]*/[A-Za-z0-9._][A-Za-z0-9._-]*$"

DEFAULT_REPO = "sheikkinen/yamlgraph"


class RequestValidationError(ValueError):
    """Typed refusal raised before any checkout or payload launch."""


class ArtifactError(ValueError):
    """Artifact missing, stale, empty, or malformed — fails even on exit 0."""


class Task(str, Enum):
    JUDGE = "judge"
    RESEARCH = "research"


class DelegationRequest(BaseModel):
    """Closed request boundary — exactly one fenced YAML mapping per issue."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    task: Task
    sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    payload: str
    # O-1 as amended: free-form owner/name; the checkout PAT's grant set is
    # the sole target authorization boundary (unreadable repo => CHECKOUT_FAIL).
    repo: str = Field(default=DEFAULT_REPO, pattern=REPO_PATTERN)
    max_reported_credits: int = Field(gt=0, le=MAX_REPORTED_CREDITS)


class DelegationStatus(str, Enum):
    """Closed execution-truth enum (FR-949 § 8, third judgement R-2).

    COMMENT_POST_FAIL lives in PublicationStatus; UNTRUSTED_AUTHOR yields no
    status (authorization skip precedes delegation); outer platform
    cancellation is Actions-owned and has no member here.
    """

    TOKEN_LEAK_DETECTED = "TOKEN_LEAK_DETECTED"  # noqa: S105  # policy status literal
    PROCESS_TREE_KILL_FAIL = "PROCESS_TREE_KILL_FAIL"
    TIMEOUT = "TIMEOUT"
    CREDENTIAL_ISOLATION_FAIL = "CREDENTIAL_ISOLATION_FAIL"
    CHECKOUT_FAIL = "CHECKOUT_FAIL"
    SHA_UNREACHABLE = "SHA_UNREACHABLE"
    INVALID_REQUEST = "INVALID_REQUEST"
    ARTIFACT_MISSING = "ARTIFACT_MISSING"
    ARTIFACT_INVALID = "ARTIFACT_INVALID"
    PAYLOAD_NONZERO = "PAYLOAD_NONZERO"
    CREDIT_FAIL_HIGH = "CREDIT_FAIL_HIGH"
    CREDIT_FAIL_UNPARSEABLE = "CREDIT_FAIL_UNPARSEABLE"
    CLEANUP_FAIL = "CLEANUP_FAIL"
    OK = "OK"


# Total precedence, highest severity first (FR-949 § 8).
_PRECEDENCE: tuple[DelegationStatus, ...] = (
    DelegationStatus.TOKEN_LEAK_DETECTED,
    DelegationStatus.PROCESS_TREE_KILL_FAIL,
    DelegationStatus.TIMEOUT,
    DelegationStatus.CREDENTIAL_ISOLATION_FAIL,
    DelegationStatus.CHECKOUT_FAIL,
    DelegationStatus.SHA_UNREACHABLE,
    DelegationStatus.INVALID_REQUEST,
    DelegationStatus.ARTIFACT_MISSING,
    DelegationStatus.ARTIFACT_INVALID,
    DelegationStatus.PAYLOAD_NONZERO,
    DelegationStatus.CREDIT_FAIL_HIGH,
    DelegationStatus.CREDIT_FAIL_UNPARSEABLE,
    DelegationStatus.CLEANUP_FAIL,
    DelegationStatus.OK,
)


def resolve_status(observed: list[DelegationStatus]) -> DelegationStatus:
    """Highest-severity observed status; nothing observed means OK."""
    for status in _PRECEDENCE:
        if status in observed:
            return status
    return DelegationStatus.OK


class PublicationStatus(str, Enum):
    """Closed publication-outcome enum (third judgement R-2).

    Comments post before one atomic terminal mutation; a comment failure
    skips the terminal mutation and can never close an issue as done.
    """

    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    OK = "OK"
    COMMENT_POST_FAIL = "COMMENT_POST_FAIL"
    TERMINAL_MUTATION_FAIL = "TERMINAL_MUTATION_FAIL"
