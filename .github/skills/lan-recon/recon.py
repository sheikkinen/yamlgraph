"""LAN host recon CLI + library (FR-945, REQ-YG-635).

Read-only WinRM inventory of a LAN Windows host. See:
    - errors.py    typed exception hierarchy
    - boundary.py  input validation, resolution, redaction, safe-slug
    - models.py    Pydantic LanHostInventory + nested typed models
    - inventory.ps1  fixed ASCII PowerShell inventory
    - SKILL.md     read-only contract + Option A transport doctrine
"""

import argparse
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from .boundary import (
    load_credentials,
    redact,
    resolve_target,
    safe_slug,
    select_computer_name,
    validate_target_shape,
)
from .errors import (
    AdminNotAllowedError,
    ComputerNameMismatchError,
    InventoryParseError,
    MissingComputerNameError,  # noqa: F401 -- re-exported for tests
    MissingCredentialError,  # noqa: F401 -- re-exported for tests
    QualifiedUserError,  # noqa: F401 -- re-exported for tests
    ReconError,
    UnresolvableTargetError,  # noqa: F401 -- re-exported for tests
    UnsafeSlugError,
    UnsafeTargetError,  # noqa: F401 -- re-exported for tests
    WinRMAuthError,
    WinRMTimeoutError,
)

try:
    from .models import LanHostInventory
except ImportError:
    import importlib.util as _iu

    _spec = _iu.spec_from_file_location(
        "lan_recon_models",
        Path(__file__).parent / "models.py",
    )
    if not (_spec and _spec.loader):
        raise
    _mod = _iu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    LanHostInventory = _mod.LanHostInventory  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

# Frozen defaults (FR-945 § 3 R-2.6):
DEFAULT_CONNECTION_TIMEOUT = 5
DEFAULT_OPERATION_TIMEOUT = 30
WINRM_PORT = 5985
INVENTORY_SCRIPT = Path(__file__).parent / "inventory.ps1"
DEFAULT_OUTPUT_DIR = Path("tmp/lan")


def _read_inventory_script() -> str:
    return INVENTORY_SCRIPT.read_text(encoding="ascii")


def _open_client(
    host_addr: str,
    user_qualified: str,
    password: str,
    *,
    connection_timeout: int,
    operation_timeout: int,
):
    """Construct a pypsrp Client with the frozen Option A transport contract.

    Contract (FR-945 § 4):
      - HTTP 5985 (ssl=False)
      - auth="negotiate"
      - encryption="always"
      - pinned host address (no re-resolution)
      - explicit finite timeouts
      - Basic and CredSSP are NOT constructed here
    """
    from pypsrp.client import Client  # type: ignore[import-untyped]

    return Client(
        host_addr,
        username=user_qualified,
        password=password,
        auth="negotiate",
        encryption="always",
        ssl=False,
        port=WINRM_PORT,
        connection_timeout=connection_timeout,
        operation_timeout=operation_timeout,
    )


def probe(
    target: str,
    *,
    computer_name: str | None = None,
    output_dir: Path | None = None,
    connection_timeout: int = DEFAULT_CONNECTION_TIMEOUT,
    operation_timeout: int = DEFAULT_OPERATION_TIMEOUT,
) -> tuple[LanHostInventory, Path]:
    """Probe a LAN Windows host and return (inventory, output_path).

    Raises typed `ReconError` subclasses on refusal.
    """
    user, password = load_credentials()
    validate_target_shape(target)
    selected_name = select_computer_name(target, computer_name)
    resolved = resolve_target(target)
    script = _read_inventory_script()

    qualified_user = f"{selected_name}\\{user}"
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    slug = safe_slug(target, resolved)
    output_path = (output_dir / f"{slug}.json").resolve()
    tmp_root = output_dir.resolve()
    if (
        not str(output_path).startswith(str(tmp_root) + os.sep)
        and output_path.parent != tmp_root
    ):
        raise UnsafeSlugError(f"slug {slug!r} escapes {tmp_root}.")

    try:
        from pypsrp.exceptions import (  # type: ignore[import-untyped]
            AuthenticationError,
            WinRMTransportError,
            WSManFaultError,
        )
    except ImportError as exc:
        raise ReconError(
            f"pypsrp not installed: {exc}. `pip install -e '.[dev]'`"
        ) from exc

    try:
        client = _open_client(
            str(resolved),
            qualified_user,
            password,
            connection_timeout=connection_timeout,
            operation_timeout=operation_timeout,
        )
    except AuthenticationError as exc:
        raise WinRMAuthError(
            redact(
                f"authentication failed as {qualified_user}. Check: "
                "(a) LAN_RECON_PASS matches the Windows account; "
                "(b) the account is a member of Remote Management Users "
                f"(SID S-1-5-32-580). Underlying: {exc}",
                password,
            )
        ) from exc
    except (WinRMTransportError, TimeoutError) as exc:
        raise WinRMTimeoutError(
            redact(f"WinRM transport timeout to {resolved}: {exc}", password)
        ) from exc

    try:
        with client:
            name_out, _, _ = client.execute_ps("$env:COMPUTERNAME")
            actual_name = name_out.strip()
            if actual_name.upper() != selected_name.upper():
                raise ComputerNameMismatchError(
                    f"target {target!r} resolved to {resolved} but "
                    f"$env:COMPUTERNAME={actual_name!r} does not match "
                    f"selected {selected_name!r}."
                )
            probe_started = datetime.now(UTC)
            out, streams, had_error = client.execute_ps(script)
            probe_ended = datetime.now(UTC)
    except AuthenticationError as exc:
        raise WinRMAuthError(
            redact(f"authentication failed as {qualified_user}: {exc}", password)
        ) from exc
    except (WinRMTransportError, WSManFaultError, TimeoutError) as exc:
        raise WinRMTimeoutError(
            redact(f"WinRM operation timeout on {resolved}: {exc}", password)
        ) from exc

    if had_error:
        err_text = str(getattr(streams, "error", ""))[:400]
        raise InventoryParseError(
            redact(f"inventory.ps1 returned error stream: {err_text}", password)
        )

    try:
        payload = json.loads(out)
    except json.JSONDecodeError as exc:
        raise InventoryParseError(
            redact(f"inventory.ps1 did not emit valid JSON: {exc}", password)
        ) from exc

    payload["requested_target"] = target
    payload["resolved_address"] = str(resolved)
    payload.setdefault("probe_started_at", probe_started.isoformat())
    payload.setdefault("probe_ended_at", probe_ended.isoformat())

    try:
        inventory = LanHostInventory.model_validate(payload)
    except Exception as exc:  # pydantic.ValidationError subclass
        raise InventoryParseError(
            redact(
                f"inventory JSON does not match LanHostInventory: {exc}",
                password,
            )
        ) from exc

    if inventory.admin:
        raise AdminNotAllowedError(
            f"probe account is admin on {selected_name}; recon requires a "
            "non-admin least-privilege account."
        )

    tmp_path = output_path.with_suffix(".json.tmp")
    tmp_path.write_text(inventory.model_dump_json(indent=2), encoding="utf-8")
    tmp_path.replace(output_path)
    return inventory, output_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lan-recon",
        description="Read-only WinRM inventory of a LAN Windows host (FR-945).",
    )
    parser.add_argument("target", help="mDNS/DNS name or IP literal on the LAN")
    parser.add_argument(
        "--computer-name",
        default=None,
        help="Windows COMPUTERNAME (required for IP targets or non-derivable names)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"output directory for inventory JSON (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--connection-timeout",
        type=int,
        default=DEFAULT_CONNECTION_TIMEOUT,
        help=f"WinRM connect timeout seconds (default: {DEFAULT_CONNECTION_TIMEOUT})",
    )
    parser.add_argument(
        "--operation-timeout",
        type=int,
        default=DEFAULT_OPERATION_TIMEOUT,
        help=f"WinRM operation timeout seconds (default: {DEFAULT_OPERATION_TIMEOUT})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        inventory, path = probe(
            args.target,
            computer_name=args.computer_name,
            output_dir=Path(args.output_dir),
            connection_timeout=args.connection_timeout,
            operation_timeout=args.operation_timeout,
        )
    except ReconError as exc:
        print(f"lan-recon: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(str(path))
    print(
        f"host={inventory.computer_name} admin={inventory.admin} "
        f"rmu={inventory.remote_management_users_member} "
        f"cpu={inventory.cpu.name} ram_gb={inventory.total_memory_bytes // (1024**3)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
