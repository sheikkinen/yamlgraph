"""Tests for FR-784 Playwright network sniff utility (REQ-YG-590).

Deterministic witnesses per judgement R-2/C-2: browser tests run only
against the committed local SPA fixture (tests/fixtures/fr784_spa/)
served by a pytest-local HTTP server — never a public website.

Browser-dependent tests skip with a named reason when the committed
Playwright setup (npm ci + npx playwright install chromium) has not
been installed.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest
import yaml

from yamlgraph.tools.manifest import ShellRuntime, ToolManifest

pytestmark = pytest.mark.process  # references examples/ (FR-756)

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "examples" / "api-discovery" / "tools"
SCRIPT = TOOLS_DIR / "network-sniff.js"
MANIFEST = TOOLS_DIR / "network_sniff.tool.yaml"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "fr784_spa"

# Canary value planted by the fixture's token-bearing fetch (AC-09)
CANARY = "SECRET_TOKEN_VALUE_123"
# 32-hex canary mimicking the x-algolia-api-key leak found live (2026-08-15)
HEX_CANARY = "cafebabe0123456789abcdef01234567"


def _node_helper(expr: str) -> str:
    """Evaluate an expression against network-sniff.js exported helpers."""
    result = subprocess.run(
        ["node", "-e", f"const m = require({str(SCRIPT)!r}); console.log({expr});"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Skip guards for browser-dependent tests (AC-02 setup contract)
# ---------------------------------------------------------------------------


def _chromium_available() -> str | None:
    """Return a skip reason, or None when the pinned setup is installed."""
    if shutil.which("node") is None:
        return "node not on PATH"
    if not (TOOLS_DIR / "node_modules" / "playwright").is_dir():
        return "playwright not installed: cd examples/api-discovery/tools && npm ci"
    probe = subprocess.run(
        [
            "node",
            "-e",
            "console.log(require('playwright').chromium.executablePath())",
        ],
        capture_output=True,
        text=True,
        cwd=TOOLS_DIR,
        timeout=30,
    )
    if probe.returncode != 0 or not Path(probe.stdout.strip()).exists():
        return "chromium not installed: npx playwright install chromium"
    return None


_SKIP_REASON = _chromium_available() if SCRIPT.exists() else "script missing (RED)"

browser = pytest.mark.skipif(
    _SKIP_REASON is not None, reason=_SKIP_REASON or "available"
)


# ---------------------------------------------------------------------------
# Local fixture server (R-2: one data fetch, one telemetry fetch, one
# token-bearing fetch, an auth wall, a CAPTCHA page, a hanging request)
# Handler semantics live in tests/fixtures/fr784_spa/spa_server.py (shared
# with FR-809 live authoring smokes) — single source of truth.
# ---------------------------------------------------------------------------


def _load_spa_server():
    spec = importlib.util.spec_from_file_location(
        "fr784_spa_server", FIXTURE_DIR / "spa_server.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["fr784_spa_server"] = module
    spec.loader.exec_module(module)
    return module


_SpaHandler = _load_spa_server().SpaHandler


@pytest.fixture(scope="module")
def spa_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _SpaHandler)
    server.daemon_threads = True
    port = server.server_address[1]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


def _sniff(url: str, timeout_ms: int = 15000) -> dict:
    """Run network-sniff.js and parse its JSON output."""
    result = subprocess.run(
        ["node", str(SCRIPT), url, "--timeout", str(timeout_ms)],
        capture_output=True,
        text=True,
        timeout=timeout_ms / 1000 + 30,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Static contract: script + manifest + package boundary (AC-01, AC-02, AC-10)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-590")
def test_script_exists():
    """AC-01: network-sniff.js exists under examples/api-discovery/tools/."""
    assert SCRIPT.exists()


@pytest.mark.req("REQ-YG-590")
def test_package_boundary_pins_playwright():
    """AC-02: committed package.json + lockfile pin playwright."""
    pkg_path = TOOLS_DIR / "package.json"
    lock_path = TOOLS_DIR / "package-lock.json"
    assert pkg_path.exists(), "missing package.json"
    assert lock_path.exists(), "missing package-lock.json"
    pkg = json.loads(pkg_path.read_text())
    version = pkg["dependencies"]["playwright"]
    assert version[0].isdigit(), f"playwright must be pinned exactly, got {version}"


@pytest.mark.req("REQ-YG-590")
def test_manifest_is_fr768_shell_with_json_parse():
    """AC-10: manifest uses FR-768 shell schema, parse: json, timeout."""
    raw = yaml.safe_load(MANIFEST.read_text())
    manifest = ToolManifest.model_validate(raw)
    assert manifest.name == "network_sniff"
    assert isinstance(manifest.runtime, ShellRuntime)
    assert manifest.runtime.parse == "json"
    assert manifest.runtime.timeout >= 10, "runtime timeout must cover script default"
    assert "examples/api-discovery/tools/network-sniff.js" in manifest.runtime.command


@pytest.mark.req("REQ-YG-590")
def test_manifest_expands_in_graph_context():
    """AC-10: manifest reference expands like an inline shell tool."""
    from yamlgraph.tools.manifest import expand_tool_manifests

    tools = {"network_sniff": {"manifest": str(MANIFEST)}}
    expanded = expand_tool_manifests(tools, source_path=None)
    assert expanded["network_sniff"]["type"] == "shell"
    assert expanded["network_sniff"]["parse"] == "json"


@pytest.mark.req("REQ-YG-590")
def test_missing_playwright_gives_diagnostic(tmp_path):
    """AC-02: missing playwright package -> non-zero exit naming the cure."""
    if shutil.which("node") is None:
        pytest.skip("node not on PATH")
    orphan = tmp_path / "network-sniff.js"
    orphan.write_text(SCRIPT.read_text())
    result = subprocess.run(
        ["node", str(orphan), "http://127.0.0.1:1/", "--timeout", "1000"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=tmp_path,
    )
    assert result.returncode != 0
    assert "playwright" in result.stderr.lower()
    assert "npm ci" in result.stderr


@pytest.mark.req("REQ-YG-590")
def test_vendor_prefixed_key_param_redacted():
    """AC-09: x-vendor-api-key style params are redacted (live leak, hn.algolia.com)."""
    if shutil.which("node") is None:
        pytest.skip("node not on PATH")
    url = f"https://api.example.com/query?x-fixture-api-key={HEX_CANARY}&q=climate"
    out = _node_helper(f"m.redactUrl({url!r})")
    assert HEX_CANARY not in out, "vendor-prefixed api key leaked"
    assert "q=climate" in out, "non-token params must survive redaction"


@pytest.mark.req("REQ-YG-590")
def test_token_shaped_query_value_redacted():
    """AC-09: 32+ hex query values are redacted regardless of param name."""
    if shutil.which("node") is None:
        pytest.skip("node not on PATH")
    url = f"https://api.example.com/query?oddly_named={HEX_CANARY}"
    out = _node_helper(f"m.redactUrl({url!r})")
    assert HEX_CANARY not in out, "token-shaped value leaked via unlisted param name"


@pytest.mark.req("REQ-YG-590")
def test_telemetry_hostname_label_classified():
    """R-4: telemetry.<vendor> hosts are telemetry (live miss, telemetry.algolia.com)."""
    if shutil.which("node") is None:
        pytest.skip("node not on PATH")
    out = _node_helper(
        "m.classify('https://telemetry.example.com/1/settings', 200, 'application/json')"
    )
    assert out == "telemetry"
    keep = _node_helper(
        "m.classify('https://api.example.com/1/data', 200, 'application/json')"
    )
    assert keep == "data", "label check must not over-classify plain api hosts"


# ---------------------------------------------------------------------------
# Browser witnesses against the committed fixture (AC-03..AC-09)
# ---------------------------------------------------------------------------


@browser
@pytest.mark.slow
@pytest.mark.req("REQ-YG-590")
def test_captures_data_request(spa_server: str):
    """AC-03/AC-04/AC-05: data fetch captured with the full request shape."""
    out = _sniff(f"{spa_server}/index.html")
    assert set(out) == {"requests", "auth_required", "needs_manual_reason", "warnings"}
    data = [r for r in out["requests"] if r["classification"] == "data"]
    assert data, f"no data request captured: {out['requests']}"
    row = data[0]
    for field in ("url", "method", "status", "content_type", "body_preview"):
        assert field in row
    assert row["status"] == 200
    assert "json" in row["content_type"]
    assert "fixture-row" in row["body_preview"]
    assert out["auth_required"] is False
    assert out["needs_manual_reason"] is None


@browser
@pytest.mark.slow
@pytest.mark.req("REQ-YG-590")
def test_telemetry_classified_behind_data(spa_server: str):
    """AC-06: denylisted telemetry is demoted behind data, not dropped."""
    out = _sniff(f"{spa_server}/index.html")
    classes = [r["classification"] for r in out["requests"]]
    assert "telemetry" in classes, "telemetry request must be kept (demote-never-drop)"
    assert classes.index("data") < classes.index("telemetry")
    telemetry = next(r for r in out["requests"] if r["classification"] == "telemetry")
    assert "/analytics/collect" in telemetry["url"]


@browser
@pytest.mark.slow
@pytest.mark.req("REQ-YG-590")
def test_token_redaction(spa_server: str):
    """AC-09: token query values are redacted everywhere in the output."""
    result = subprocess.run(
        ["node", str(SCRIPT), f"{spa_server}/index.html", "--timeout", "15000"],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0
    assert CANARY not in result.stdout, "raw token leaked into output"
    assert HEX_CANARY not in result.stdout, "vendor api-key canary leaked into output"
    out = json.loads(result.stdout)
    token_reqs = [r for r in out["requests"] if "/api/item" in r["url"]]
    assert token_reqs, "token-bearing request must still be inventoried"
    assert "REDACTED" in token_reqs[0]["url"]


@browser
@pytest.mark.slow
@pytest.mark.req("REQ-YG-590")
def test_auth_wall_flagged_not_failed(spa_server: str):
    """AC-08: 401 API -> auth_required + needs_manual_reason, exit 0."""
    out = _sniff(f"{spa_server}/auth.html")
    assert out["auth_required"] is True
    assert out["needs_manual_reason"] == "auth_token"


@browser
@pytest.mark.slow
@pytest.mark.req("REQ-YG-590")
def test_captcha_flagged(spa_server: str):
    """AC-08: CAPTCHA markup -> needs_manual_reason captcha."""
    out = _sniff(f"{spa_server}/captcha.html")
    assert out["needs_manual_reason"] == "captcha"


@browser
@pytest.mark.slow
@pytest.mark.req("REQ-YG-590")
def test_timeout_exits_cleanly_with_warning(spa_server: str):
    """AC-07: never-settling page -> exit 0, valid JSON, timeout warning."""
    out = _sniff(f"{spa_server}/hang.html", timeout_ms=4000)
    assert isinstance(out["requests"], list)
    assert any("timeout" in w for w in out["warnings"]), out["warnings"]
