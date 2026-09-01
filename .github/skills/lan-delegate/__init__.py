"""lan-delegate skill (FR-948, REQ-YG-636).

Submit ONE clean-committed workload to a FR-945-recon-verified LAN
Windows host via WinRM+Copilot CLI. Read-only on the mac; disposable
per-run worktree on the remote.
"""

from .errors import PRE_LAUNCH_EXCEPTIONS, LanDelegateError
from .models import (
    CreditStatus,
    DelegationPolicyStatus,
    FieldError,
    FieldErrorType,
    LanDelegationRequest,
    LanDelegationResult,
    RemoteCopilotPrerequisites,
    RepoInfo,
    ToolInfo,
    WrapperJsonSummary,
    resolve_status,
)

__all__ = [
    "CreditStatus",
    "DelegationPolicyStatus",
    "FieldError",
    "FieldErrorType",
    "LanDelegateError",
    "LanDelegationRequest",
    "LanDelegationResult",
    "PRE_LAUNCH_EXCEPTIONS",
    "RemoteCopilotPrerequisites",
    "RepoInfo",
    "ToolInfo",
    "WrapperJsonSummary",
    "resolve_status",
]
