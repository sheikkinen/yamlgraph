"""Typed exception hierarchy for the LAN recon skill (FR-945, REQ-YG-635).

Every refusal path in `recon.py` maps to a subclass here so callers can
discriminate at the exception type, not by string matching. CLI shims
translate any `ReconError` to a non-zero exit + actionable stderr.
"""


class ReconError(Exception):
    """Base class for typed recon refusals. CLI translates to exit code 2."""


class MissingCredentialError(ReconError):
    """LAN_RECON_USER or LAN_RECON_PASS not set."""


class QualifiedUserError(ReconError):
    """User value is already qualified/domain-shaped; v1 refuses these."""


class UnresolvableTargetError(ReconError):
    """DNS resolution failed for the target."""


class UnsafeTargetError(ReconError):
    """Resolved target is loopback/multicast/unspecified/public."""


class MissingComputerNameError(ReconError):
    """IP literal or non-derivable DNS label without --computer-name."""


class ComputerNameMismatchError(ReconError):
    """Post-handshake $env:COMPUTERNAME did not match the selected name."""


class WinRMAuthError(ReconError):
    """WinRM authentication failed."""


class WinRMTimeoutError(ReconError):
    """Connection or operation timeout."""


class InventoryParseError(ReconError):
    """inventory.ps1 emitted non-JSON or non-validating JSON."""


class AdminNotAllowedError(ReconError):
    """The probing account is admin; recon requires least privilege."""


class UnsafeSlugError(ReconError):
    """Slug derivation would escape tmp/lan/."""
