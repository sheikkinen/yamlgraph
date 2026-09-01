"""Wire-level tests for FR-948 lan-delegate skill (REQ-YG-636).

Complements test_lan_delegate_scaffold.py (which covers models + errors +
enum precedence). This module exercises delegate.py's pre-launch validation,
wrapper.ps1's contract compliance (forbidden ops), and offline behavior of
the wire path via mocked pypsrp.

Live witnesses (AC-19 short-timeout, AC-20 real skill invocation) are
recorded in the FR body once implementation lands.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

_SKILL_DIR = Path(__file__).parent.parent.parent / ".github" / "skills" / "lan-delegate"


def _load(name: str):
    """Load a module from the dashed-package path via importlib."""
    if name == "delegate":
        # delegate.py imports from siblings — force the whole package to load first.
        pkg_spec = importlib.util.spec_from_file_location(
            "lan_delegate_pkg",
            _SKILL_DIR / "__init__.py",
            submodule_search_locations=[str(_SKILL_DIR)],
        )
        pkg = importlib.util.module_from_spec(pkg_spec)
        sys.modules["lan_delegate_pkg"] = pkg
        pkg_spec.loader.exec_module(pkg)
        spec = importlib.util.spec_from_file_location(
            "lan_delegate_pkg.delegate",
            _SKILL_DIR / "delegate.py",
        )
    else:
        spec = importlib.util.spec_from_file_location(
            f"lan_delegate_{name}",
            _SKILL_DIR / f"{name}.py",
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


errors = _load("errors")
models = _load("models")

# --- wrapper.ps1 contract compliance ----------------------------------------

WRAPPER_PATH = _SKILL_DIR / "wrapper.ps1"


@pytest.mark.req("REQ-YG-636")
def test_wrapper_is_pure_ascii():
    """PS 5.1 codepage constraint. Every wrapper byte must be printable ASCII or whitespace."""
    raw = WRAPPER_PATH.read_bytes()
    for i, b in enumerate(raw):
        assert 0x09 <= b <= 0x7E or b in (
            0x0A,
            0x0D,
        ), f"non-ASCII byte 0x{b:02x} at offset {i}"


@pytest.mark.req("REQ-YG-636")
def test_wrapper_has_no_active_forbidden_operations():
    """AC-15 / AC-16: wrapper.ps1 must not perform install / fetch / clone / mutation.

    Comments and error-message strings that MENTION the forbidden operations
    are OK; only actual command invocations at line start are rejected.
    """
    forbidden_active = re.compile(
        r"^\s*(?:&\s*)?"
        r"(?:winget\s+install"
        r"|npm\s+i(?:nstall)?\s"
        r"|pip\s+install"
        r"|git\s+(?:clone|fetch)"
        r"|Add-WindowsCapability"
        r"|wsl\s+--install"
        r"|Set-Service"
        r"|New-NetFirewallRule"
        r"|Add-LocalGroupMember)",
        re.MULTILINE,
    )
    text = WRAPPER_PATH.read_text(encoding="utf-8")
    # Strip block comments and lines that are pure comments.
    scrubbed = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )
    violations = forbidden_active.findall(scrubbed)
    assert violations == [], f"wrapper.ps1 performs forbidden operations: {violations}"


@pytest.mark.req("REQ-YG-636")
def test_wrapper_does_not_use_filesystem_redirection_for_capture():
    """R-3: wrapper must capture Copilot output in memory (Start-Job / Receive-Job),
    never via -RedirectStandardOutput or -RedirectStandardError with a filesystem path."""
    text = WRAPPER_PATH.read_text(encoding="utf-8")
    scrubbed = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )
    assert "-RedirectStandardOutput" not in scrubbed
    assert "-RedirectStandardError" not in scrubbed


@pytest.mark.req("REQ-YG-636")
def test_wrapper_declares_expected_parameters():
    """Wrapper must bind Token / Prompt / RunId / TimeoutS / LocalSha / MaxReportedCredits."""
    text = WRAPPER_PATH.read_text(encoding="utf-8")
    for param in (
        "$Token",
        "$Prompt",
        "$RunId",
        "$TimeoutS",
        "$LocalSha",
        "$MaxReportedCredits",
    ):
        assert param in text, f"wrapper.ps1 missing parameter {param}"


@pytest.mark.req("REQ-YG-636")
def test_wrapper_sets_recursive_delegation_marker():
    """R-5 recursive-delegation guard: wrapper must set YAMLGRAPH_LAN_DELEGATED=1."""
    text = WRAPPER_PATH.read_text(encoding="utf-8")
    assert "YAMLGRAPH_LAN_DELEGATED" in text and "= '1'" in text


@pytest.mark.req("REQ-YG-636")
def test_wrapper_clears_env_in_finally():
    """AC-11: cleanup must run in outer finally regardless of failure."""
    text = WRAPPER_PATH.read_text(encoding="utf-8")
    assert "Remove-Item Env:GH_TOKEN" in text
    assert "} finally {" in text or "}\nfinally {" in text


@pytest.mark.req("REQ-YG-636")
def test_wrapper_uses_taskkill_for_full_tree_termination():
    """R-2: on timeout, use taskkill /T /F to kill the whole tree."""
    text = WRAPPER_PATH.read_text(encoding="utf-8")
    assert "taskkill" in text
    assert "/T" in text and "/F" in text


# --- delegate.py pre-launch refusals ----------------------------------------

# Delegate imports pypsrp at call time. Skip these tests entirely if the
# .env-driven runtime happens to be absent from the test env; models/errors
# import path is independent.
try:
    delegate_mod = _load("delegate")
except ImportError as exc:  # pragma: no cover
    delegate_mod = None
    _DELEGATE_IMPORT_ERR = exc
else:
    _DELEGATE_IMPORT_ERR = None
    # Rebind `errors` + `models` to the delegate package's submodules — the
    # classes raised/instantiated by delegate.py are from THOSE modules,
    # not the standalone top-level loads.
    import lan_delegate_pkg.errors as errors  # noqa: E402  # noqa: F811
    import lan_delegate_pkg.models as models  # noqa: E402  # noqa: F811


@pytest.fixture
def make_request(tmp_path):
    def _make(**overrides):
        prompt = tmp_path / "prompt.md"
        prompt.write_text("test prompt", encoding="utf-8")
        defaults = {
            "host": "Huutokauppakone.local",
            "prompt_file": prompt,
            "run_id": "test-run-1",
            "max_reported_credits": 60.0,
            "timeout_s": 300,
            "local_sha": "a" * 40,
            "local_clean": True,
        }
        defaults.update(overrides)
        return models.LanDelegationRequest(**defaults)

    return _make


@pytest.fixture
def recon_receipt(tmp_path):
    def _write(host_slug="huutokauppakone.local", **overrides):
        receipt = {
            "resolved_address": "192.168.50.172",
            "computer_name": "HUUTOKAUPPAKONE",
            "probe_started_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
            "probe_ended_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
            "admin": False,
            "remote_management_users_member": True,
        }
        receipt.update(overrides)
        target = tmp_path / "tmp" / "lan" / f"{host_slug}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(receipt), encoding="utf-8")
        return receipt, target

    return _write


@pytest.mark.req("REQ-YG-636")
def test_recursive_delegation_refused(make_request, tmp_path, monkeypatch):
    """AC-17: presence of YAMLGRAPH_LAN_DELEGATED=1 refuses before receipt / WinRM."""
    if delegate_mod is None:
        pytest.skip(f"delegate import failed: {_DELEGATE_IMPORT_ERR}")
    monkeypatch.setenv("YAMLGRAPH_LAN_DELEGATED", "1")
    monkeypatch.setenv("LAN_RECON_USER", "u")
    monkeypatch.setenv("LAN_RECON_PASS", "p")
    monkeypatch.setenv("GH_TOKEN", "t")
    with pytest.raises(errors.RecursiveDelegationError):
        delegate_mod.delegate(make_request(), workdir=tmp_path)


@pytest.mark.req("REQ-YG-636")
def test_unsafe_host_refused(make_request, tmp_path, monkeypatch):
    if delegate_mod is None:
        pytest.skip(f"delegate import failed: {_DELEGATE_IMPORT_ERR}")
    monkeypatch.delenv("YAMLGRAPH_LAN_DELEGATED", raising=False)
    monkeypatch.setenv("LAN_RECON_USER", "u")
    monkeypatch.setenv("LAN_RECON_PASS", "p")
    monkeypatch.setenv("GH_TOKEN", "t")
    with pytest.raises(errors.UnsafeHostError):
        delegate_mod.delegate(
            make_request(host="not a host / with spaces"), workdir=tmp_path
        )


@pytest.mark.req("REQ-YG-636")
def test_unsafe_run_id_refused(make_request, tmp_path, monkeypatch):
    if delegate_mod is None:
        pytest.skip(f"delegate import failed: {_DELEGATE_IMPORT_ERR}")
    monkeypatch.delenv("YAMLGRAPH_LAN_DELEGATED", raising=False)
    monkeypatch.setenv("LAN_RECON_USER", "u")
    monkeypatch.setenv("LAN_RECON_PASS", "p")
    monkeypatch.setenv("GH_TOKEN", "t")
    for bad in ("../evil", "run/id", r"run\id", "with space", "control\x00"):
        with pytest.raises(errors.UnsafeRunIdError):
            delegate_mod.delegate(make_request(run_id=bad), workdir=tmp_path)


@pytest.mark.req("REQ-YG-636")
def test_missing_credential_refused(make_request, tmp_path, monkeypatch):
    if delegate_mod is None:
        pytest.skip(f"delegate import failed: {_DELEGATE_IMPORT_ERR}")
    monkeypatch.delenv("YAMLGRAPH_LAN_DELEGATED", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setenv("LAN_RECON_USER", "u")
    monkeypatch.setenv("LAN_RECON_PASS", "p")
    with pytest.raises(errors.MissingCredentialError) as exc:
        delegate_mod.delegate(make_request(), workdir=tmp_path)
    assert "GH_TOKEN" in str(exc.value)


@pytest.mark.req("REQ-YG-636")
def test_prompt_file_missing_refused(make_request, tmp_path, monkeypatch):
    if delegate_mod is None:
        pytest.skip(f"delegate import failed: {_DELEGATE_IMPORT_ERR}")
    monkeypatch.delenv("YAMLGRAPH_LAN_DELEGATED", raising=False)
    monkeypatch.setenv("LAN_RECON_USER", "u")
    monkeypatch.setenv("LAN_RECON_PASS", "p")
    monkeypatch.setenv("GH_TOKEN", "t")
    with pytest.raises(errors.PromptFileError):
        delegate_mod.delegate(
            make_request(prompt_file=tmp_path / "does-not-exist.md"),
            workdir=tmp_path,
        )


@pytest.mark.req("REQ-YG-636")
def test_prompt_file_oversized_refused(make_request, tmp_path, monkeypatch):
    if delegate_mod is None:
        pytest.skip(f"delegate import failed: {_DELEGATE_IMPORT_ERR}")
    monkeypatch.delenv("YAMLGRAPH_LAN_DELEGATED", raising=False)
    monkeypatch.setenv("LAN_RECON_USER", "u")
    monkeypatch.setenv("LAN_RECON_PASS", "p")
    monkeypatch.setenv("GH_TOKEN", "t")
    big = tmp_path / "big.md"
    big.write_bytes(b"x" * (33 * 1024))  # > 32 KiB
    with pytest.raises(errors.PromptFileError):
        delegate_mod.delegate(make_request(prompt_file=big), workdir=tmp_path)


@pytest.mark.req("REQ-YG-636")
def test_local_path_collision_refused(make_request, tmp_path, monkeypatch):
    if delegate_mod is None:
        pytest.skip(f"delegate import failed: {_DELEGATE_IMPORT_ERR}")
    monkeypatch.delenv("YAMLGRAPH_LAN_DELEGATED", raising=False)
    monkeypatch.setenv("LAN_RECON_USER", "u")
    monkeypatch.setenv("LAN_RECON_PASS", "p")
    monkeypatch.setenv("GH_TOKEN", "t")
    # Pre-create the .result.json path where delegate would want to write.
    result_dir = tmp_path / "tmp" / "lan" / "delegate" / "huutokauppakone.local"
    result_dir.mkdir(parents=True)
    (result_dir / "test-run-1.result.json").write_text("stale", encoding="utf-8")
    with pytest.raises(errors.LocalPathCollisionError):
        delegate_mod.delegate(make_request(), workdir=tmp_path)


@pytest.mark.req("REQ-YG-636")
def test_missing_recon_refused(make_request, tmp_path, monkeypatch):
    if delegate_mod is None:
        pytest.skip(f"delegate import failed: {_DELEGATE_IMPORT_ERR}")
    monkeypatch.delenv("YAMLGRAPH_LAN_DELEGATED", raising=False)
    monkeypatch.setenv("LAN_RECON_USER", "u")
    monkeypatch.setenv("LAN_RECON_PASS", "p")
    monkeypatch.setenv("GH_TOKEN", "t")
    with pytest.raises(errors.MissingReconError):
        delegate_mod.delegate(make_request(), workdir=tmp_path)


@pytest.mark.req("REQ-YG-636")
def test_stale_recon_refused(make_request, recon_receipt, tmp_path, monkeypatch):
    if delegate_mod is None:
        pytest.skip(f"delegate import failed: {_DELEGATE_IMPORT_ERR}")
    monkeypatch.delenv("YAMLGRAPH_LAN_DELEGATED", raising=False)
    monkeypatch.setenv("LAN_RECON_USER", "u")
    monkeypatch.setenv("LAN_RECON_PASS", "p")
    monkeypatch.setenv("GH_TOKEN", "t")
    stale_time = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    recon_receipt(probe_started_at=stale_time, probe_ended_at=stale_time)
    with pytest.raises(errors.StaleReconError):
        delegate_mod.delegate(make_request(), workdir=tmp_path)


@pytest.mark.req("REQ-YG-636")
def test_recon_admin_true_refused(make_request, recon_receipt, tmp_path, monkeypatch):
    if delegate_mod is None:
        pytest.skip(f"delegate import failed: {_DELEGATE_IMPORT_ERR}")
    monkeypatch.delenv("YAMLGRAPH_LAN_DELEGATED", raising=False)
    monkeypatch.setenv("LAN_RECON_USER", "u")
    monkeypatch.setenv("LAN_RECON_PASS", "p")
    monkeypatch.setenv("GH_TOKEN", "t")
    recon_receipt(admin=True)
    with pytest.raises(errors.ReconDisqualifyingFieldError):
        delegate_mod.delegate(make_request(), workdir=tmp_path)


@pytest.mark.req("REQ-YG-636")
def test_recon_rmu_false_refused(make_request, recon_receipt, tmp_path, monkeypatch):
    if delegate_mod is None:
        pytest.skip(f"delegate import failed: {_DELEGATE_IMPORT_ERR}")
    monkeypatch.delenv("YAMLGRAPH_LAN_DELEGATED", raising=False)
    monkeypatch.setenv("LAN_RECON_USER", "u")
    monkeypatch.setenv("LAN_RECON_PASS", "p")
    monkeypatch.setenv("GH_TOKEN", "t")
    recon_receipt(remote_management_users_member=False)
    with pytest.raises(errors.ReconDisqualifyingFieldError):
        delegate_mod.delegate(make_request(), workdir=tmp_path)


# --- WinRM client construction assertions -----------------------------------


class _FakePool:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _FakePS:
    def __init__(self, pool):
        self.script = None
        self.parameters: dict = {}

    def add_script(self, s):
        self.script = s

    def add_parameter(self, name, value):
        self.parameters[name] = value

    def invoke(self):
        # Emit a minimal valid WrapperJsonSummary so build_result stays typed.
        summary = {
            "prerequisites": None,
            "remote_sha": "a" * 40,
            "remote_worktree": "C:\\Users\\copilot\\yamlgraph-runs\\test-run-1",
            "copilot_exit_code": 0,
            "delegation_policy_status": "OK",
            "timed_out": False,
            "elapsed_s": 1.0,
            "credits_reported": 5.0,
            "tokens_up": 1000,
            "tokens_down": 100,
            "artifacts": [],
            "artifact_root": None,
            "errors": [],
        }
        return [json.dumps(summary)]


@pytest.mark.req("REQ-YG-636")
def test_winrm_construction_uses_pinned_option_a_kwargs(
    make_request, recon_receipt, tmp_path, monkeypatch
):
    """AC-08: pypsrp.WSMan kwargs match FR-945 Option A contract."""
    if delegate_mod is None:
        pytest.skip(f"delegate import failed: {_DELEGATE_IMPORT_ERR}")
    monkeypatch.delenv("YAMLGRAPH_LAN_DELEGATED", raising=False)
    monkeypatch.setenv("LAN_RECON_USER", "copilot")
    monkeypatch.setenv("LAN_RECON_PASS", "pw")
    monkeypatch.setenv("GH_TOKEN", "gho_test")
    recon_receipt()

    captured: dict = {}

    def fake_wsman(host, **kwargs):
        captured["host"] = host
        captured.update(kwargs)
        return object()

    with patch.dict(
        sys.modules,
        {
            "pypsrp": type(sys)("pypsrp"),
            "pypsrp.powershell": type(sys)("pypsrp.powershell"),
            "pypsrp.wsman": type(sys)("pypsrp.wsman"),
        },
    ):
        sys.modules["pypsrp.wsman"].WSMan = fake_wsman
        sys.modules["pypsrp.powershell"].RunspacePool = lambda w: _FakePool()
        sys.modules["pypsrp.powershell"].PowerShell = _FakePS
        result = delegate_mod.delegate(make_request(), workdir=tmp_path)

    assert captured["host"] == "192.168.50.172"  # pinned resolved address
    assert captured["auth"] == "negotiate"
    assert captured["encryption"] == "always"
    assert captured["ssl"] is False
    assert captured["port"] == 5985
    assert captured["operation_timeout"] == 300 + delegate_mod.WSMAN_CLEANUP_MARGIN_S
    assert result.delegation_policy_status == models.DelegationPolicyStatus.OK
    assert result.sha_matched is True


@pytest.mark.req("REQ-YG-636")
def test_qualified_username_is_used(make_request, recon_receipt, tmp_path, monkeypatch):
    """AC-08: bare LAN_RECON_USER is qualified to COMPUTERNAME\\user."""
    if delegate_mod is None:
        pytest.skip(f"delegate import failed: {_DELEGATE_IMPORT_ERR}")
    monkeypatch.delenv("YAMLGRAPH_LAN_DELEGATED", raising=False)
    monkeypatch.setenv("LAN_RECON_USER", "copilot")
    monkeypatch.setenv("LAN_RECON_PASS", "pw")
    monkeypatch.setenv("GH_TOKEN", "gho_test")
    recon_receipt()

    captured: dict = {}

    def fake_wsman(host, **kwargs):
        captured.update(kwargs)
        return object()

    with patch.dict(
        sys.modules,
        {
            "pypsrp": type(sys)("pypsrp"),
            "pypsrp.powershell": type(sys)("pypsrp.powershell"),
            "pypsrp.wsman": type(sys)("pypsrp.wsman"),
        },
    ):
        sys.modules["pypsrp.wsman"].WSMan = fake_wsman
        sys.modules["pypsrp.powershell"].RunspacePool = lambda w: _FakePool()
        sys.modules["pypsrp.powershell"].PowerShell = _FakePS
        delegate_mod.delegate(make_request(), workdir=tmp_path)

    assert captured["username"] == "HUUTOKAUPPAKONE\\copilot"


@pytest.mark.req("REQ-YG-636")
def test_wrapper_parameters_include_token_and_prompt_bindings(
    make_request, recon_receipt, tmp_path, monkeypatch
):
    """AC-09: prompt + token cross WinRM only as bound parameters."""
    if delegate_mod is None:
        pytest.skip(f"delegate import failed: {_DELEGATE_IMPORT_ERR}")
    monkeypatch.delenv("YAMLGRAPH_LAN_DELEGATED", raising=False)
    monkeypatch.setenv("LAN_RECON_USER", "copilot")
    monkeypatch.setenv("LAN_RECON_PASS", "pw")
    monkeypatch.setenv("GH_TOKEN", "gho_test_token_1234")
    recon_receipt()

    captured_ps: dict = {"instance": None}

    class _CapturingPS(_FakePS):
        def __init__(self, pool):
            super().__init__(pool)
            captured_ps["instance"] = self

    with patch.dict(
        sys.modules,
        {
            "pypsrp": type(sys)("pypsrp"),
            "pypsrp.powershell": type(sys)("pypsrp.powershell"),
            "pypsrp.wsman": type(sys)("pypsrp.wsman"),
        },
    ):
        sys.modules["pypsrp.wsman"].WSMan = lambda host, **k: object()
        sys.modules["pypsrp.powershell"].RunspacePool = lambda w: _FakePool()
        sys.modules["pypsrp.powershell"].PowerShell = _CapturingPS
        delegate_mod.delegate(make_request(), workdir=tmp_path)

    ps = captured_ps["instance"]
    assert ps is not None
    assert ps.parameters["Token"] == "gho_test_token_1234"  # noqa: S105  # test fixture literal, not a real token
    assert ps.parameters["Prompt"] == "test prompt"
    assert ps.parameters["RunId"] == "test-run-1"
    # Token must NOT appear in the script text (it must be a bound parameter).
    assert "gho_test_token_1234" not in ps.script
    # Prompt content likewise.
    assert "test prompt" not in ps.script
