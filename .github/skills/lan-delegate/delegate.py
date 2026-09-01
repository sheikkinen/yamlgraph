"""lan-delegate CLI + library (FR-948, REQ-YG-636).

Composes typed pre-launch validation (§ 4), remote WinRM dispatch of
wrapper.ps1 (§ 5), and result assembly into LanDelegationResult (§ 6).

The wrapper does the remote work; delegate.py owns the mac-local boundary
(input validation, transport construction, JSON parsing, log retrieval,
result composition).

Usage:
    python .github/skills/lan-delegate/delegate.py \\
        --host xxxx.local \\
        --prompt-file tmp/analyze.md \\
        --run-id analyze-20260901T120000Z-abc1234 \\
        [--max-reported-credits 60] \\
        [--timeout-s 300]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from .errors import (
    DirtyLocalTreeError,
    LocalPathCollisionError,
    MissingCredentialError,
    MissingReconError,
    PromptFileError,
    ReconDisqualifyingFieldError,
    RecursiveDelegationError,
    StaleReconError,
    UnsafeHostError,
    UnsafeRunIdError,
)
from .models import (
    DelegationPolicyStatus,
    FieldError,
    LanDelegationRequest,
    LanDelegationResult,
    WrapperJsonSummary,
)

WSMAN_CLEANUP_MARGIN_S = 60
RECON_MAX_AGE_MIN_DEFAULT = 10.0
MAX_PROMPT_BYTES = 32 * 1024
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
HOST_PATTERN = re.compile(
    r"^(?:[A-Za-z0-9](?:[A-Za-z0-9\-]{0,62}[A-Za-z0-9])?)"
    r"(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9\-]{0,62}[A-Za-z0-9])?))*$"
)

WRAPPER_SCRIPT = Path(__file__).parent / "wrapper.ps1"


def _slug_host(host: str) -> str:
    """Normalize the host for local path composition (§ 3.6)."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", host.lower())


def _validate_run_id(run_id: str) -> None:
    if not run_id or len(run_id) > 64 or not RUN_ID_PATTERN.match(run_id):
        raise UnsafeRunIdError(
            f"run-id {run_id!r} must match ^[A-Za-z0-9._-]+$ and be <= 64 chars"
        )


def _validate_host(host: str) -> None:
    if not host or len(host) > 253 or not HOST_PATTERN.match(host):
        raise UnsafeHostError(f"host {host!r} is not a well-formed DNS/mDNS name")


def _validate_prompt(path: Path) -> str:
    if not path.exists():
        raise PromptFileError(path, "missing")
    raw = path.read_bytes()
    if len(raw) > MAX_PROMPT_BYTES:
        raise PromptFileError(path, f"exceeds {MAX_PROMPT_BYTES} bytes ({len(raw)})")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:  # pragma: no cover
        raise PromptFileError(path, f"not UTF-8: {exc}") from None


def _load_recon_receipt(
    host_slug: str, host: str, workdir: Path, max_age_min: float
) -> dict:
    receipt_path = workdir / "tmp" / "lan" / f"{host_slug}.json"
    if not receipt_path.exists():
        raise MissingReconError(host, receipt_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    probe_ended_at = datetime.fromisoformat(receipt["probe_ended_at"])
    age_min = (datetime.now(UTC) - probe_ended_at).total_seconds() / 60.0
    if age_min > max_age_min:
        raise StaleReconError(host, age_min, max_age_min)
    if receipt.get("admin") is True:
        raise ReconDisqualifyingFieldError(
            f"host {host} recon shows admin=True; least-privilege refuses"
        )
    if receipt.get("remote_management_users_member") is False:
        raise ReconDisqualifyingFieldError(
            f"host {host} recon shows remote_management_users_member=False"
        )
    return receipt


def _check_local_tree_clean(workdir: Path) -> str:
    result = subprocess.run(  # noqa: S603
        ["git", "-C", str(workdir), "status", "--porcelain"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise DirtyLocalTreeError(f"git status failed: {result.stderr.strip()}")
    if result.stdout.strip():
        raise DirtyLocalTreeError(
            "local tree has uncommitted changes; commit or stash before delegating"
        )
    head = subprocess.run(  # noqa: S603
        ["git", "-C", str(workdir), "rev-parse", "HEAD"],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    )
    return head.stdout.strip()


def _check_recursive_delegation() -> None:
    if os.environ.get("YAMLGRAPH_LAN_DELEGATED") == "1":
        raise RecursiveDelegationError()


def _compose_result_paths(
    workdir: Path, host_slug: str, run_id: str
) -> tuple[Path, Path, Path]:
    base = workdir / "tmp" / "lan" / "delegate" / host_slug
    return (
        base / f"{run_id}.result.json",
        base / f"{run_id}.stdout.log",
        base / f"{run_id}.stderr.log",
    )


def _check_local_collision(paths: tuple[Path, ...]) -> None:
    for p in paths:
        if p.exists():
            raise LocalPathCollisionError(p)


def _read_credentials() -> tuple[str, str, str]:
    def _get(name: str) -> str:
        v = os.environ.get(name, "")
        if not v:
            raise MissingCredentialError(name)
        return v

    return _get("LAN_RECON_USER"), _get("LAN_RECON_PASS"), _get("GH_TOKEN")


def _run_wrapper(
    receipt: dict,
    user: str,
    password: str,
    token: str,
    prompt_text: str,
    run_id: str,
    timeout_s: int,
    local_sha: str,
    max_reported_credits: float,
    wrapper_source: str,
) -> WrapperJsonSummary | None:
    """Dispatch the wrapper via WinRM. Returns parsed summary or None on transport failure."""
    from pypsrp.powershell import PowerShell, RunspacePool
    from pypsrp.wsman import WSMan

    computer_name = receipt["computer_name"]
    address = receipt["resolved_address"]
    qualified_user = f"{computer_name.upper()}\\{user}"

    outer_timeout = timeout_s + WSMAN_CLEANUP_MARGIN_S
    wsman = WSMan(
        address,
        username=qualified_user,
        password=password,
        auth="negotiate",
        encryption="always",
        ssl=False,
        port=5985,
        connection_timeout=5,
        operation_timeout=outer_timeout,
    )
    with RunspacePool(wsman) as pool:
        ps = PowerShell(pool)
        ps.add_script(wrapper_source)
        ps.add_parameter("Token", token)
        ps.add_parameter("Prompt", prompt_text)
        ps.add_parameter("RunId", run_id)
        ps.add_parameter("TimeoutS", timeout_s)
        ps.add_parameter("LocalSha", local_sha)
        ps.add_parameter("MaxReportedCredits", max_reported_credits)

        output = ps.invoke()
        # The wrapper emits exactly one JSON document on stdout.
        for line in reversed(output):
            text = str(line).strip()
            if text.startswith("{") and text.endswith("}"):
                try:
                    return WrapperJsonSummary.model_validate_json(text)
                except Exception:
                    return None
    return None


def _copy_smb_logs(
    host: str, run_id: str, stdout_target: Path, stderr_target: Path
) -> None:
    """Copy stdout.log/stderr.log from the SMB drop into the mac-local diagnostic paths."""
    mac_mount = Path("/Volumes/Images") / "yamlgraph-delegations" / run_id
    if not mac_mount.exists():
        return
    stdout_target.parent.mkdir(parents=True, exist_ok=True)
    src_stdout = mac_mount / "stdout.log"
    src_stderr = mac_mount / "stderr.log"
    if src_stdout.exists():
        stdout_target.write_bytes(src_stdout.read_bytes())
    if src_stderr.exists():
        stderr_target.write_bytes(src_stderr.read_bytes())


def delegate(
    request: LanDelegationRequest,
    workdir: Path | None = None,
    recon_max_age_min: float = RECON_MAX_AGE_MIN_DEFAULT,
) -> LanDelegationResult:
    """Run one delegation. Pre-launch failures raise typed exceptions; launched
    runs always return a validated LanDelegationResult."""
    workdir = workdir or Path.cwd()

    _check_recursive_delegation()
    _validate_host(request.host)
    _validate_run_id(request.run_id)
    prompt_text = _validate_prompt(request.prompt_file)

    host_slug = _slug_host(request.host)
    result_path, stdout_path, stderr_path = _compose_result_paths(
        workdir, host_slug, request.run_id
    )
    _check_local_collision((result_path, stdout_path, stderr_path))

    user, password, token = _read_credentials()
    receipt = _load_recon_receipt(host_slug, request.host, workdir, recon_max_age_min)

    wrapper_source = WRAPPER_SCRIPT.read_text(encoding="utf-8")
    started_at = datetime.now(UTC)

    try:
        summary = _run_wrapper(
            receipt=receipt,
            user=user,
            password=password,
            token=token,
            prompt_text=prompt_text,
            run_id=request.run_id,
            timeout_s=request.timeout_s,
            local_sha=request.local_sha,
            max_reported_credits=request.max_reported_credits,
            wrapper_source=wrapper_source,
        )
    except (
        Exception
    ) as exc:  # pragma: no cover - transport failures require live sockets
        message = str(exc)
        elapsed = (datetime.now(UTC) - started_at).total_seconds()
        status = DelegationPolicyStatus.WINRM_CONNECT_FAIL
        if "auth" in message.lower():
            status = DelegationPolicyStatus.WINRM_AUTH_FAIL
        elif "timeout" in message.lower() or "timed out" in message.lower():
            status = DelegationPolicyStatus.WINRM_TRANSPORT_TIMEOUT
        return _build_result(
            request=request,
            receipt=receipt,
            summary=None,
            status=status,
            elapsed_s=elapsed,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            transport_error=message,
        )

    elapsed = (datetime.now(UTC) - started_at).total_seconds()
    _copy_smb_logs(request.host, request.run_id, stdout_path, stderr_path)

    if summary is None:
        return _build_result(
            request=request,
            receipt=receipt,
            summary=None,
            status=DelegationPolicyStatus.WRAPPER_JSON_MALFORMED,
            elapsed_s=elapsed,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            transport_error="wrapper returned no parseable JSON summary",
        )

    return _build_result(
        request=request,
        receipt=receipt,
        summary=summary,
        status=summary.delegation_policy_status,
        elapsed_s=elapsed,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
    )


def _build_result(
    *,
    request: LanDelegationRequest,
    receipt: dict,
    summary: WrapperJsonSummary | None,
    status: DelegationPolicyStatus,
    elapsed_s: float,
    stdout_path: Path,
    stderr_path: Path,
    transport_error: str | None = None,
) -> LanDelegationResult:
    errors: list[FieldError] = list(summary.errors) if summary else []
    if transport_error:
        errors.append(
            FieldError(field="transport", message=transport_error, error_type="unknown")
        )
    credits_reported = summary.credits_reported if summary else None
    credit_status: str
    if summary is None:
        credit_status = "NOT_APPLICABLE"
    elif credits_reported is None:
        credit_status = "FAIL_UNPARSEABLE"
    elif credits_reported > request.max_reported_credits:
        credit_status = "FAIL_HIGH"
    else:
        credit_status = "OK"

    remote_sha = summary.remote_sha if summary else None
    sha_matched = bool(remote_sha and remote_sha == request.local_sha)

    return LanDelegationResult(
        request=request,
        host_resolved_address=receipt["resolved_address"],
        remote_computer_name=receipt["computer_name"],
        prerequisites=summary.prerequisites if summary else None,
        local_sha=request.local_sha,
        remote_sha=remote_sha,
        sha_matched=sha_matched,
        remote_worktree=summary.remote_worktree if summary else None,
        copilot_exit_code=summary.copilot_exit_code if summary else None,
        delegation_policy_status=status,
        timed_out=bool(summary and summary.timed_out),
        elapsed_s=summary.elapsed_s if summary else elapsed_s,
        credits_reported=credits_reported,
        credit_status=credit_status,
        tokens_up=summary.tokens_up if summary else None,
        tokens_down=summary.tokens_down if summary else None,
        artifacts=list(summary.artifacts) if summary else [],
        artifact_root=summary.artifact_root if summary else None,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        errors=errors,
    )


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="delegate.py", description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--max-reported-credits", type=float, default=60.0)
    parser.add_argument("--timeout-s", type=int, default=300)
    args = parser.parse_args(argv)

    workdir = Path.cwd()
    try:
        _check_recursive_delegation()
        local_sha = _check_local_tree_clean(workdir)
    except (RecursiveDelegationError, DirtyLocalTreeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    request = LanDelegationRequest(
        host=args.host,
        prompt_file=args.prompt_file,
        run_id=args.run_id,
        max_reported_credits=args.max_reported_credits,
        timeout_s=args.timeout_s,
        local_sha=local_sha,
        local_clean=True,
    )
    try:
        result = delegate(request, workdir=workdir)
    except (
        MissingReconError,
        StaleReconError,
        ReconDisqualifyingFieldError,
        MissingCredentialError,
        UnsafeHostError,
        UnsafeRunIdError,
        PromptFileError,
        LocalPathCollisionError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 4

    result_json = result.model_dump_json(indent=2)
    host_slug = _slug_host(request.host)
    result_path = (
        workdir
        / "tmp"
        / "lan"
        / "delegate"
        / host_slug
        / f"{request.run_id}.result.json"
    )
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(result_json, encoding="utf-8")
    print(f"result: {result_path}")
    print(f"status: {result.delegation_policy_status.value}")
    return 0 if result.delegation_policy_status == DelegationPolicyStatus.OK else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_cli())
