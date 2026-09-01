"""Pydantic schemas for LAN Copilot delegation (FR-948, REQ-YG-636).

Boundary contract: every WinRM/wrapper output crosses these types before
reaching control flow. No untyped dict propagates from receipt or
wrapper JSON.

Schema tables mirrored from FR-948-lan-copilot-delegation.md § 5-6.
"""

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress

FieldErrorType = Literal[
    "absent",
    "malformed",
    "version_too_low",
    "path_taken",
    "access_denied",
    "probe_timeout",
    "unknown",
]

CreditStatus = Literal[
    "OK",
    "FAIL_HIGH",
    "FAIL_UNPARSEABLE",
    "NOT_APPLICABLE",
]


class DelegationPolicyStatus(str, Enum):
    """Closed enum for FR-948 § 6.

    Precedence when multiple failures occur (highest severity wins):
    TOKEN_LEAK_DETECTED > PROCESS_TREE_KILL_FAIL > WRAPPER_JSON_MALFORMED >
    OUTPUT_CAPTURE_FAIL > TIMEOUT > WORKTREE_ADD_FAIL >
    OUTPUT_DIR_CREATE_FAIL > WRAPPER_EXEC_FAIL > WINRM_AUTH_FAIL >
    WINRM_CONNECT_FAIL > WINRM_TRANSPORT_TIMEOUT > PREFLIGHT_FAIL >
    SMB_DEST_EXISTS > COPILOT_NONZERO > CREDIT_FAIL_HIGH >
    CREDIT_FAIL_UNPARSEABLE > ARTIFACT_COPY_FAIL > WORKTREE_CLEANUP_FAIL >
    OK.
    """

    OK = "OK"
    PREFLIGHT_FAIL = "PREFLIGHT_FAIL"
    WINRM_CONNECT_FAIL = "WINRM_CONNECT_FAIL"
    WINRM_AUTH_FAIL = "WINRM_AUTH_FAIL"
    WINRM_TRANSPORT_TIMEOUT = "WINRM_TRANSPORT_TIMEOUT"
    WORKTREE_ADD_FAIL = "WORKTREE_ADD_FAIL"
    OUTPUT_DIR_CREATE_FAIL = "OUTPUT_DIR_CREATE_FAIL"
    WRAPPER_EXEC_FAIL = "WRAPPER_EXEC_FAIL"
    COPILOT_NONZERO = "COPILOT_NONZERO"
    TIMEOUT = "TIMEOUT"
    PROCESS_TREE_KILL_FAIL = "PROCESS_TREE_KILL_FAIL"
    OUTPUT_CAPTURE_FAIL = "OUTPUT_CAPTURE_FAIL"
    CREDIT_FAIL_HIGH = "CREDIT_FAIL_HIGH"
    CREDIT_FAIL_UNPARSEABLE = "CREDIT_FAIL_UNPARSEABLE"
    WRAPPER_JSON_MALFORMED = "WRAPPER_JSON_MALFORMED"
    ARTIFACT_COPY_FAIL = "ARTIFACT_COPY_FAIL"
    WORKTREE_CLEANUP_FAIL = "WORKTREE_CLEANUP_FAIL"
    TOKEN_LEAK_DETECTED = "TOKEN_LEAK_DETECTED"  # noqa: S105  # policy status literal
    SMB_DEST_EXISTS = "SMB_DEST_EXISTS"


# Precedence table matches the docstring above; index 0 is highest severity.
_PRECEDENCE: list[DelegationPolicyStatus] = [
    DelegationPolicyStatus.TOKEN_LEAK_DETECTED,
    DelegationPolicyStatus.PROCESS_TREE_KILL_FAIL,
    DelegationPolicyStatus.WRAPPER_JSON_MALFORMED,
    DelegationPolicyStatus.OUTPUT_CAPTURE_FAIL,
    DelegationPolicyStatus.TIMEOUT,
    DelegationPolicyStatus.WORKTREE_ADD_FAIL,
    DelegationPolicyStatus.OUTPUT_DIR_CREATE_FAIL,
    DelegationPolicyStatus.WRAPPER_EXEC_FAIL,
    DelegationPolicyStatus.WINRM_AUTH_FAIL,
    DelegationPolicyStatus.WINRM_CONNECT_FAIL,
    DelegationPolicyStatus.WINRM_TRANSPORT_TIMEOUT,
    DelegationPolicyStatus.PREFLIGHT_FAIL,
    DelegationPolicyStatus.SMB_DEST_EXISTS,
    DelegationPolicyStatus.COPILOT_NONZERO,
    DelegationPolicyStatus.CREDIT_FAIL_HIGH,
    DelegationPolicyStatus.CREDIT_FAIL_UNPARSEABLE,
    DelegationPolicyStatus.ARTIFACT_COPY_FAIL,
    DelegationPolicyStatus.WORKTREE_CLEANUP_FAIL,
    DelegationPolicyStatus.OK,
]


def resolve_status(observed: list[DelegationPolicyStatus]) -> DelegationPolicyStatus:
    """Return the highest-severity status per FR-948 § 6 precedence."""
    if not observed:
        return DelegationPolicyStatus.OK
    ranks = {s: i for i, s in enumerate(_PRECEDENCE)}
    return min(observed, key=lambda s: ranks[s])


class FieldError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    message: str
    error_type: FieldErrorType


class ToolInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    present: bool
    path: str | None = None
    version: str | None = None
    error: FieldError | None = None


class RepoInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    exists: bool
    contains_sha: bool | None = None
    error: FieldError | None = None


class RemoteCopilotPrerequisites(BaseModel):
    """Non-LLM preflight before Copilot invocation."""

    model_config = ConfigDict(extra="forbid")

    git: ToolInfo
    node: ToolInfo
    copilot: ToolInfo
    canonical_clone: RepoInfo
    run_worktree_free: bool
    smb_destination_free: bool
    errors: list[FieldError] = Field(default_factory=list)

    def all_ok(self) -> bool:
        """True iff every required prerequisite is satisfied."""
        if not self.git.present:
            return False
        if not self.node.present:
            return False
        # Node version major >= 22 (parsed as "vNN.MM.PP")
        if self.node.version is None:
            return False
        try:
            major_token = self.node.version.lstrip("v").split(".")[0]
            if int(major_token) < 22:
                return False
        except (ValueError, IndexError):
            return False
        if not self.copilot.present:
            return False
        if not self.canonical_clone.exists:
            return False
        if self.canonical_clone.contains_sha is not True:
            return False
        if not self.run_worktree_free:
            return False
        return self.smb_destination_free


class LanDelegationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str
    prompt_file: Path
    run_id: str
    max_reported_credits: float = 60.0
    timeout_s: int = 300
    local_sha: str
    local_clean: bool


class LanDelegationResult(BaseModel):
    """Diagnostic produced whenever WinRM was attempted.

    Pre-launch typed exceptions raise BEFORE this is constructed;
    no LanDelegationResult exists for those refusals.

    Phase invariants:
    - WINRM_CONNECT_FAIL / WINRM_AUTH_FAIL / WINRM_TRANSPORT_TIMEOUT:
      prerequisites=None, copilot_exit_code=None, remote_sha=None,
      artifact_root=None.
    - PREFLIGHT_FAIL: prerequisites present, copilot_exit_code=None.
    - WORKTREE_ADD_FAIL or later: prerequisites present, remote_sha
      present iff worktree was created before failure.
    - WRAPPER_JSON_MALFORMED: prerequisites=None allowed (no valid
      wrapper document existed).
    """

    model_config = ConfigDict(extra="forbid")

    request: LanDelegationRequest
    host_resolved_address: IPvAnyAddress
    remote_computer_name: str
    prerequisites: RemoteCopilotPrerequisites | None = None
    local_sha: str
    remote_sha: str | None = None
    sha_matched: bool
    remote_worktree: str | None = None
    copilot_exit_code: int | None = None
    delegation_policy_status: DelegationPolicyStatus
    timed_out: bool
    elapsed_s: float
    credits_reported: float | None = None
    credit_status: CreditStatus
    tokens_up: int | None = None
    tokens_down: int | None = None
    artifacts: list[str] = Field(default_factory=list)
    artifact_root: str | None = None
    stdout_path: Path
    stderr_path: Path
    errors: list[FieldError] = Field(default_factory=list)


class WrapperJsonSummary(BaseModel):
    """Subset emitted by wrapper.ps1 on stdout; merged into LanDelegationResult."""

    model_config = ConfigDict(extra="forbid")

    prerequisites: RemoteCopilotPrerequisites | None = None
    remote_sha: str | None = None
    remote_worktree: str | None = None
    copilot_exit_code: int | None = None
    delegation_policy_status: DelegationPolicyStatus
    timed_out: bool
    elapsed_s: float
    credits_reported: float | None = None
    tokens_up: int | None = None
    tokens_down: int | None = None
    artifacts: list[str] = Field(default_factory=list)
    artifact_root: str | None = None
    errors: list[FieldError] = Field(default_factory=list)
