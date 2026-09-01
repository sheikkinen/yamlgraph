"""Typed pre-launch exceptions for lan-delegate (FR-948, REQ-YG-636).

All exceptions raise BEFORE any WinRM connect attempt, DNS resolution,
or filesystem write. When one of these fires, no LanDelegationResult is
produced; the CLI wrapper converts them to non-zero exit + actionable
stderr.
"""

from pathlib import Path


class LanDelegateError(Exception):
    """Base for all pre-launch exceptions raised by delegate.py."""


class DirtyLocalTreeError(LanDelegateError):
    """Local git tree has uncommitted changes."""


class MissingReconError(LanDelegateError):
    """FR-945 recon receipt file absent for the requested host."""

    def __init__(self, host: str, expected_path: Path):
        super().__init__(
            f"Recon receipt missing for host {host!r}. Expected at: {expected_path}. "
            f"Run `.github/skills/lan-recon/recon.py {host}` first."
        )


class StaleReconError(LanDelegateError):
    """FR-945 recon receipt older than RECON_MAX_AGE_MIN."""

    def __init__(self, host: str, age_min: float, max_age_min: float):
        super().__init__(
            f"Recon receipt for {host!r} is {age_min:.1f} min old (> {max_age_min:.0f} min). "
            f"Re-run `.github/skills/lan-recon/recon.py {host}` for fresh state."
        )


class ReconDisqualifyingFieldError(LanDelegateError):
    """Recon receipt disqualifies the host (admin=True, RMU=False, etc.)."""


class MissingCredentialError(LanDelegateError):
    """Required environment variable is missing or empty."""

    def __init__(self, var_name: str):
        super().__init__(
            f"Required environment variable {var_name!r} is missing or empty. "
            f"Set it in .env or the shell before invoking delegate."
        )


class UnsafeHostError(LanDelegateError):
    """Host string violates FR-945's DNS/IP/allowlist rules or receipt mismatch."""


class PromptFileError(LanDelegateError):
    """Prompt file missing, oversized, or not UTF-8."""

    def __init__(self, path: Path, reason: str):
        super().__init__(f"Prompt file {path}: {reason}.")
        self.path = path
        self.reason = reason


class UnsafeRunIdError(LanDelegateError):
    """Run ID contains disallowed characters or exceeds length limit."""


class LocalPathCollisionError(LanDelegateError):
    """A pre-computed local output path already exists."""

    def __init__(self, path: Path):
        super().__init__(
            f"Local output path already exists: {path}. "
            f"Choose a distinct --run-id or move the existing file."
        )
        self.path = path


class RecursiveDelegationError(LanDelegateError):
    """Caller is running inside a delegated Copilot session.

    Presence of `YAMLGRAPH_LAN_DELEGATED=1` in the environment indicates
    the delegated Copilot on the remote is trying to re-invoke LAN
    delegation. Refuse to prevent an infinite delegation loop.
    """

    def __init__(self):
        super().__init__(
            "Already inside a delegated Copilot session "
            "(YAMLGRAPH_LAN_DELEGATED=1). Execute the workload locally in the "
            "current worktree; do not re-invoke LAN delegation."
        )


PRE_LAUNCH_EXCEPTIONS = (
    DirtyLocalTreeError,
    MissingReconError,
    StaleReconError,
    ReconDisqualifyingFieldError,
    MissingCredentialError,
    UnsafeHostError,
    PromptFileError,
    UnsafeRunIdError,
    LocalPathCollisionError,
    RecursiveDelegationError,
)
