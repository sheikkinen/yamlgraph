"""FR-945 REQ-YG-635 offline tests for the LAN recon skill.

All tests are offline: DNS resolution and pypsrp Client are mocked. No
real socket ever opens. See FR-945 § 6 R-5 for the frozen 12-refusal
list; each is exercised below plus the semantic happy-path fixture.
"""

from __future__ import annotations

import importlib
import json
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# The skill lives under a hyphenated directory that isn't a valid Python
# package name; register it as a package under a valid alias so relative
# imports inside recon.py (from .boundary / .errors / .models) resolve.
_SKILL_DIR = Path(__file__).resolve().parents[2] / ".github" / "skills" / "lan-recon"
_PACKAGE_NAME = "lan_recon_under_test"


def _load_package():
    """Load the skill directory as a proper Python package with a valid name."""
    pkg_spec = importlib.util.spec_from_file_location(
        _PACKAGE_NAME,
        _SKILL_DIR / "__init__.py",
        submodule_search_locations=[str(_SKILL_DIR)],
    )
    assert pkg_spec and pkg_spec.loader
    pkg = importlib.util.module_from_spec(pkg_spec)
    sys.modules[_PACKAGE_NAME] = pkg
    pkg_spec.loader.exec_module(pkg)
    return importlib.import_module(f"{_PACKAGE_NAME}.recon")


_recon = _load_package()
_models = sys.modules[f"{_PACKAGE_NAME}.models"]
_boundary = sys.modules[f"{_PACKAGE_NAME}.boundary"]


@pytest.fixture
def recon():
    """The loaded recon module under test."""
    return _recon


@pytest.fixture
def creds(monkeypatch):
    monkeypatch.setenv("LAN_RECON_USER", "copilot")
    monkeypatch.setenv("LAN_RECON_PASS", "hunter2-not-real")


@pytest.fixture
def fixture_json():
    p = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "lan_recon"
        / "huutokauppakone.json"
    )
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# AC-07: inventory.ps1 is pure ASCII (no interpolation)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-635")
def test_inventory_ps1_is_pure_ascii():
    raw = (_SKILL_DIR / "inventory.ps1").read_bytes()
    for i, byte in enumerate(raw):
        if byte > 0x7F:
            pytest.fail(f"non-ASCII byte 0x{byte:02x} at offset {i}")


@pytest.mark.req("REQ-YG-635")
def test_inventory_ps1_uses_sid_not_localized_name():
    text = (_SKILL_DIR / "inventory.ps1").read_text(encoding="ascii")
    assert "S-1-5-32-580" in text, "inventory.ps1 must reference RMU by SID"
    assert (
        "'Remote Management Users'" not in text
    ), "inventory.ps1 must NOT use the localized group name"


@pytest.mark.req("REQ-YG-635")
def test_inventory_ps1_has_no_smb_queries():
    text = (_SKILL_DIR / "inventory.ps1").read_text(encoding="ascii")
    assert "Get-SmbShare" not in text
    assert "Get-SmbServerConfiguration" not in text


# ---------------------------------------------------------------------------
# Refusal path 1 & 2: missing credentials
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-635")
def test_refusal_missing_user(recon, monkeypatch):
    monkeypatch.delenv("LAN_RECON_USER", raising=False)
    monkeypatch.setenv("LAN_RECON_PASS", "x")
    with pytest.raises(recon.MissingCredentialError, match="LAN_RECON_USER"):
        recon.probe("Huutokauppakone.local")


@pytest.mark.req("REQ-YG-635")
def test_refusal_missing_pass(recon, monkeypatch):
    monkeypatch.setenv("LAN_RECON_USER", "copilot")
    monkeypatch.delenv("LAN_RECON_PASS", raising=False)
    with pytest.raises(recon.MissingCredentialError, match="LAN_RECON_PASS"):
        recon.probe("Huutokauppakone.local")


@pytest.mark.req("REQ-YG-635")
def test_refusal_qualified_user(recon, monkeypatch):
    monkeypatch.setenv("LAN_RECON_USER", "HUUTOKAUPPAKONE\\copilot")
    monkeypatch.setenv("LAN_RECON_PASS", "x")
    with pytest.raises(recon.QualifiedUserError):
        recon.probe("Huutokauppakone.local")


# ---------------------------------------------------------------------------
# Refusal 3: public IP target
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-635")
def test_refusal_public_ip(recon, creds):
    with pytest.raises(recon.UnsafeTargetError, match="non-LAN"):
        recon.probe("8.8.8.8", computer_name="ANYBOX")


# ---------------------------------------------------------------------------
# Refusal 4: loopback / multicast / unspecified
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-635")
# CONF-444: "0.0.0.0" here is a probe TARGET string, not a bind address.
@pytest.mark.parametrize("bad", ["127.0.0.1", "224.0.0.1", "0.0.0.0"])  # noqa: S104
def test_refusal_special_targets(recon, creds, bad):
    with pytest.raises(recon.UnsafeTargetError):
        recon.probe(bad, computer_name="ANYBOX")


# ---------------------------------------------------------------------------
# Refusal 5: unresolvable
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-635")
def test_refusal_unresolvable(recon, creds, monkeypatch):
    import socket as sock_mod

    def _boom(*a, **kw):
        raise sock_mod.gaierror("mocked nxdomain")

    monkeypatch.setattr(_boundary.socket, "getaddrinfo", _boom)
    with pytest.raises(recon.UnresolvableTargetError, match="mocked nxdomain"):
        recon.probe("no-such-host.invalid")


# ---------------------------------------------------------------------------
# Refusal 6: IP without --computer-name
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-635")
def test_refusal_ip_without_computer_name(recon, creds):
    with pytest.raises(recon.MissingComputerNameError, match="--computer-name"):
        recon.probe("192.168.50.172")


# ---------------------------------------------------------------------------
# Refusal 7: post-handshake computer name mismatch
# ---------------------------------------------------------------------------


def _mock_client_with(recon_mod, execute_ps_side_effect):
    """Build a MagicMock pypsrp client where execute_ps has the given side effect."""
    client = MagicMock()
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=None)
    client.execute_ps.side_effect = execute_ps_side_effect
    return client


@pytest.mark.req("REQ-YG-635")
def test_refusal_computer_name_mismatch(recon, creds, monkeypatch, tmp_path):
    calls = []

    def _side(script):
        calls.append(script)
        if script.strip() == "$env:COMPUTERNAME":
            return ("SOMEOTHERBOX\n", MagicMock(error=""), False)
        return ("{}", MagicMock(error=""), False)

    monkeypatch.setattr(
        recon, "_open_client", lambda *a, **k: _mock_client_with(recon, _side)
    )
    monkeypatch.setattr(
        _boundary.socket,
        "getaddrinfo",
        lambda *a, **k: [
            (_boundary.socket.AF_INET, None, None, None, ("192.168.50.172", 0))
        ],
    )
    with pytest.raises(recon.ComputerNameMismatchError):
        recon.probe("Huutokauppakone.local", output_dir=tmp_path)


# ---------------------------------------------------------------------------
# Refusal 8: WinRM auth failure + password redaction (AC-06 partial)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-635")
def test_refusal_auth_failure_and_password_redaction(
    recon, creds, monkeypatch, tmp_path, caplog
):
    from pypsrp.exceptions import AuthenticationError

    def _open_client_boom(host_addr, user, pw, **kw):
        raise AuthenticationError(f"bad creds for {user} (pw was: {pw})")

    monkeypatch.setattr(recon, "_open_client", _open_client_boom)
    monkeypatch.setattr(
        _boundary.socket,
        "getaddrinfo",
        lambda *a, **k: [
            (_boundary.socket.AF_INET, None, None, None, ("192.168.50.172", 0))
        ],
    )
    with pytest.raises(recon.WinRMAuthError) as excinfo:
        recon.probe("Huutokauppakone.local", output_dir=tmp_path)
    msg = str(excinfo.value)
    assert "S-1-5-32-580" in msg
    assert "hunter2-not-real" not in msg, "password leaked into exception message"
    # And it must never appear in captured logs from this call.
    assert not any("hunter2-not-real" in r.getMessage() for r in caplog.records)


# ---------------------------------------------------------------------------
# Refusal 9: connection timeout (asserts kwargs seen by Client)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-635")
def test_client_kwargs_are_option_a(recon, creds, monkeypatch, tmp_path):
    """AC-06: assert the exact Option A transport kwargs."""
    captured = {}

    def _fake_client(host, **kwargs):
        captured["host"] = host
        captured.update(kwargs)
        client = MagicMock()
        client.__enter__ = MagicMock(return_value=client)
        client.__exit__ = MagicMock(return_value=None)
        client.execute_ps.side_effect = [
            ("HUUTOKAUPPAKONE\n", MagicMock(error=""), False),
            (json.dumps(_minimal_inventory()), MagicMock(error=""), False),
        ]
        return client

    # Patch pypsrp.client.Client at the import point inside _open_client.
    import pypsrp.client

    monkeypatch.setattr(pypsrp.client, "Client", _fake_client)
    monkeypatch.setattr(
        _boundary.socket,
        "getaddrinfo",
        lambda *a, **k: [
            (_boundary.socket.AF_INET, None, None, None, ("192.168.50.172", 0))
        ],
    )

    recon.probe("Huutokauppakone.local", output_dir=tmp_path)

    assert captured["host"] == "192.168.50.172"
    assert captured["auth"] == "negotiate"
    assert captured["encryption"] == "always"
    assert captured["ssl"] is False
    assert captured["port"] == 5985
    assert (
        isinstance(captured["connection_timeout"], int)
        and captured["connection_timeout"] > 0
    )
    assert (
        isinstance(captured["operation_timeout"], int)
        and captured["operation_timeout"] > 0
    )
    assert captured["username"] == "HUUTOKAUPPAKONE\\copilot"
    # AC-06 explicit ban: no basic/credssp kwarg found
    assert "basic" not in {k.lower() for k in captured}
    assert "credssp" not in {k.lower() for k in captured}


def _minimal_inventory() -> dict:
    """Smallest valid LanHostInventory payload (fields recon.py doesn't add)."""
    return {
        "computer_name": "HUUTOKAUPPAKONE",
        "os_version": "Microsoft Windows NT 10.0.26200.0",
        "manufacturer": "ASUSTeK",
        "model": "ROG",
        "total_memory_bytes": 25678995456,
        "logical_processors": 16,
        "cpu": {
            "name": "AMD Ryzen 7 5800X 8-Core Processor",
            "cores": 8,
            "logical_processors": 16,
            "max_clock_mhz": 3801,
        },
        "gpus": [
            {
                "name": "NVIDIA GeForce RTX 3070",
                "adapter_ram_bytes": 4293918720,
                "driver_version": "1.0",
            }
        ],
        "disks": [{"drive": "C", "free_bytes": 1, "used_bytes": 1}],
        "python_native": None,
        "py_launcher": [],
        "wsl": None,
        "openssh_server_state": "NotPresent",
        "sshd_service": None,
        "lm_studio_cli_present": True,
        "lm_studio_service": None,
        "listening_ports": [],
        "admin": False,
        "remote_management_users_member": True,
        "errors": [],
    }


# ---------------------------------------------------------------------------
# Refusal 10: malformed PowerShell JSON
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-635")
def test_refusal_bad_json(recon, creds, monkeypatch, tmp_path):
    def _side(script):
        if script.strip() == "$env:COMPUTERNAME":
            return ("HUUTOKAUPPAKONE\n", MagicMock(error=""), False)
        return ("this is not json <<<", MagicMock(error=""), False)

    monkeypatch.setattr(
        recon, "_open_client", lambda *a, **k: _mock_client_with(recon, _side)
    )
    monkeypatch.setattr(
        _boundary.socket,
        "getaddrinfo",
        lambda *a, **k: [
            (_boundary.socket.AF_INET, None, None, None, ("192.168.50.172", 0))
        ],
    )
    with pytest.raises(recon.InventoryParseError, match="valid JSON"):
        recon.probe("Huutokauppakone.local", output_dir=tmp_path)


# ---------------------------------------------------------------------------
# Refusal 11: validation failure (missing required field)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-635")
def test_refusal_pydantic_validation(recon, creds, monkeypatch, tmp_path):
    payload = _minimal_inventory()
    payload.pop("cpu")

    def _side(script):
        if script.strip() == "$env:COMPUTERNAME":
            return ("HUUTOKAUPPAKONE\n", MagicMock(error=""), False)
        return (json.dumps(payload), MagicMock(error=""), False)

    monkeypatch.setattr(
        recon, "_open_client", lambda *a, **k: _mock_client_with(recon, _side)
    )
    monkeypatch.setattr(
        _boundary.socket,
        "getaddrinfo",
        lambda *a, **k: [
            (_boundary.socket.AF_INET, None, None, None, ("192.168.50.172", 0))
        ],
    )
    with pytest.raises(recon.InventoryParseError):
        recon.probe("Huutokauppakone.local", output_dir=tmp_path)


# ---------------------------------------------------------------------------
# Refusal 12: unsafe output slug
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-635")
@pytest.mark.parametrize(
    "bad",
    [
        "../escape",
        "a/b",
        "a\\b",
        "a\x00b",
        "..",
        ".",
    ],
)
def test_refusal_unsafe_slug(recon, creds, bad):
    with pytest.raises(recon.ReconError):
        recon.probe(bad, computer_name="ANYBOX")


# ---------------------------------------------------------------------------
# admin=True is refused (AC-06/AC-08 least privilege)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-635")
def test_admin_true_is_refused(recon, creds, monkeypatch, tmp_path):
    payload = _minimal_inventory()
    payload["admin"] = True

    def _side(script):
        if script.strip() == "$env:COMPUTERNAME":
            return ("HUUTOKAUPPAKONE\n", MagicMock(error=""), False)
        return (json.dumps(payload), MagicMock(error=""), False)

    monkeypatch.setattr(
        recon, "_open_client", lambda *a, **k: _mock_client_with(recon, _side)
    )
    monkeypatch.setattr(
        _boundary.socket,
        "getaddrinfo",
        lambda *a, **k: [
            (_boundary.socket.AF_INET, None, None, None, ("192.168.50.172", 0))
        ],
    )
    with pytest.raises(recon.AdminNotAllowedError):
        recon.probe("Huutokauppakone.local", output_dir=tmp_path)


# ---------------------------------------------------------------------------
# AC-11: happy-path fixture asserts witnessed HW values
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-635")
def test_huutokauppakone_fixture_semantic_values(fixture_json):
    inv = _models.LanHostInventory.model_validate(fixture_json)
    assert inv.computer_name == "HUUTOKAUPPAKONE"
    assert inv.admin is False
    assert inv.remote_management_users_member is True
    assert inv.cpu.name == "AMD Ryzen 7 5800X 8-Core Processor"
    assert inv.cpu.cores == 8
    assert inv.logical_processors == 16
    # ~24 GB band (23-25 GB)
    assert 23 * 1024**3 <= inv.total_memory_bytes <= 25 * 1024**3
    gpu_names = [g.name for g in inv.gpus]
    assert any(re.match(r"NVIDIA GeForce RTX 30\d\d", n) for n in gpu_names), gpu_names
    assert inv.openssh_server_state == "NotPresent"
    assert inv.lm_studio_cli_present is True
    assert inv.sshd_service is None


# ---------------------------------------------------------------------------
# AC-09: JSON round-trip
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-635")
def test_fixture_json_roundtrip(fixture_json):
    inv = _models.LanHostInventory.model_validate(fixture_json)
    serialized = inv.model_dump_json()
    reparsed = _models.LanHostInventory.model_validate_json(serialized)
    assert reparsed.computer_name == inv.computer_name
    assert reparsed.gpus[0].name == inv.gpus[0].name


# ---------------------------------------------------------------------------
# CLI shim returns non-zero + actionable stderr on refusal
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-635")
def test_cli_returns_nonzero_on_missing_creds(recon, monkeypatch, capsys):
    monkeypatch.delenv("LAN_RECON_USER", raising=False)
    monkeypatch.delenv("LAN_RECON_PASS", raising=False)
    rc = recon.main(["Huutokauppakone.local"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "MissingCredentialError" in err
    assert "LAN_RECON_USER" in err
