"""Tests for FR-783 API discovery leaf tool manifests (REQ-YG-585)."""

from __future__ import annotations

import json
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread

import pytest
import yaml

from yamlgraph.tools.manifest import ToolManifest

TOOLS_DIR = Path(__file__).resolve().parents[2] / "examples" / "api-discovery" / "tools"

# ---------------------------------------------------------------------------
# Manifest validation (AC-01, AC-02)
# ---------------------------------------------------------------------------

MANIFEST_FILES = [
    "curl_probe.tool.yaml",
    "fetch_page.tool.yaml",
    "gh_code_search.tool.yaml",
    "parse_openapi.tool.yaml",
]


@pytest.mark.req("REQ-YG-585")
@pytest.mark.parametrize("filename", MANIFEST_FILES)
def test_manifest_validates_as_tool_manifest(filename: str):
    """Each manifest file validates as an FR-768 ToolManifest."""
    path = TOOLS_DIR / filename
    assert path.exists(), f"missing: {path}"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    manifest = ToolManifest.model_validate(raw)
    # name must match the expected tool key (filename stem minus .tool)
    expected_name = filename.replace(".tool.yaml", "")
    assert manifest.name == expected_name


@pytest.mark.req("REQ-YG-585")
def test_all_four_manifests_exist():
    """AC-01: All four manifest files exist."""
    for filename in MANIFEST_FILES:
        assert (TOOLS_DIR / filename).exists(), f"missing: {filename}"


# ---------------------------------------------------------------------------
# curl_probe (AC-03, AC-07)
# ---------------------------------------------------------------------------


class _ProbeHandler(SimpleHTTPRequestHandler):
    """Minimal HTTP handler for curl_probe/fetch_page tests."""

    def do_GET(self):
        if self.path == "/api/v1/status":
            body = json.dumps({"status": "ok", "version": "1.0"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/redirect":
            self.send_response(301)
            self.send_header("Location", "/api/v1/status")
            self.end_headers()
        elif self.path == "/page":
            body = b"<html><body><h1>Test Page</h1></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress output


@pytest.fixture(scope="module")
def local_http_server():
    """Start a local HTTP server for probe tests."""
    server = HTTPServer(("127.0.0.1", 0), _ProbeHandler)
    port = server.server_address[1]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.mark.req("REQ-YG-585")
def test_curl_probe_returns_structured_json(local_http_server: str):
    """AC-03: curl_probe returns {status, redirect, content_type, body_head}."""
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        from curl_probe import curl_probe
    finally:
        sys.path.pop(0)

    result = curl_probe(
        url=f"{local_http_server}/api/v1/status",
        user_agent="test-agent",
        timeout="5",
    )
    assert isinstance(result, dict)
    assert result["status"] == 200
    assert isinstance(result["redirect"], str)
    assert "json" in result["content_type"].lower()
    assert "ok" in result["body_head"]
    assert len(result["body_head"]) <= 2048


@pytest.mark.req("REQ-YG-585")
def test_curl_probe_404(local_http_server: str):
    """curl_probe handles 404 without error."""
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        from curl_probe import curl_probe
    finally:
        sys.path.pop(0)

    result = curl_probe(
        url=f"{local_http_server}/nonexistent",
        user_agent="test-agent",
        timeout="5",
    )
    assert result["status"] == 404


@pytest.mark.req("REQ-YG-585")
def test_curl_probe_body_head_capped():
    """AC-03: body_head is capped at 2048 characters."""
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        from curl_probe import BODY_HEAD_LIMIT
    finally:
        sys.path.pop(0)

    assert BODY_HEAD_LIMIT == 2048


# ---------------------------------------------------------------------------
# fetch_page — command shape (AC-04)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-585")
def test_fetch_page_manifest_shape():
    """AC-04: fetch_page is a shell manifest with required url and user_agent, no extra quotes."""
    raw = yaml.safe_load((TOOLS_DIR / "fetch_page.tool.yaml").read_text(encoding="utf-8"))
    manifest = ToolManifest.model_validate(raw)
    assert manifest.runtime.type == "shell"
    cmd = manifest.runtime.command
    assert "{url}" in cmd
    assert "{user_agent}" in cmd
    # No extra quotes around placeholders (R-2)
    assert "'{url}'" not in cmd
    assert "'{user_agent}'" not in cmd


# ---------------------------------------------------------------------------
# gh_code_search — manifest shape (AC-05)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-585")
def test_gh_code_search_manifest_shape():
    """AC-05: gh_code_search declares parse: json and has {query} placeholder."""
    raw = yaml.safe_load((TOOLS_DIR / "gh_code_search.tool.yaml").read_text(encoding="utf-8"))
    manifest = ToolManifest.model_validate(raw)
    assert manifest.runtime.type == "shell"
    assert manifest.runtime.parse == "json"
    assert "{query}" in manifest.runtime.command


# ---------------------------------------------------------------------------
# parse_openapi (AC-06)
# ---------------------------------------------------------------------------

VALID_OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Petstore", "version": "1.0.0"},
    "paths": {
        "/pets": {
            "get": {
                "summary": "List all pets",
                "parameters": [
                    {"name": "limit", "in": "query", "schema": {"type": "integer"}}
                ],
            },
            "post": {
                "summary": "Create a pet",
                "description": "Creates a new pet in the store",
            },
        },
        "/pets/{petId}": {
            "get": {
                "summary": "Info for a specific pet",
                "parameters": [{"name": "petId", "in": "path", "required": True}],
            },
        },
    },
}


@pytest.mark.req("REQ-YG-585")
def test_parse_openapi_valid_spec():
    """AC-06: parse_openapi returns endpoint inventory for valid spec."""
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        from parse_openapi import parse_openapi
    finally:
        sys.path.pop(0)

    result = parse_openapi(VALID_OPENAPI_SPEC)
    assert "endpoints" in result
    assert "info" in result
    assert result["info"]["title"] == "Petstore"
    assert result["info"]["version"] == "1.0.0"
    assert len(result["endpoints"]) == 3
    methods = {(e["method"], e["path"]) for e in result["endpoints"]}
    assert ("GET", "/pets") in methods
    assert ("POST", "/pets") in methods
    assert ("GET", "/pets/{petId}") in methods


@pytest.mark.req("REQ-YG-585")
def test_parse_openapi_from_json_string():
    """AC-06: parse_openapi accepts JSON string input."""
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        from parse_openapi import parse_openapi
    finally:
        sys.path.pop(0)

    result = parse_openapi(json.dumps(VALID_OPENAPI_SPEC))
    assert len(result["endpoints"]) == 3


@pytest.mark.req("REQ-YG-585")
def test_parse_openapi_invalid_json():
    """AC-06: parse_openapi raises ValueError for invalid JSON."""
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        from parse_openapi import parse_openapi
    finally:
        sys.path.pop(0)

    with pytest.raises(ValueError, match="invalid JSON"):
        parse_openapi("not valid json {{{")


@pytest.mark.req("REQ-YG-585")
def test_parse_openapi_non_object():
    """AC-06: parse_openapi raises ValueError for non-object spec."""
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        from parse_openapi import parse_openapi
    finally:
        sys.path.pop(0)

    with pytest.raises(ValueError, match="must be a JSON object"):
        parse_openapi([1, 2, 3])


@pytest.mark.req("REQ-YG-585")
def test_parse_openapi_missing_paths():
    """AC-06: parse_openapi raises ValueError for missing paths key."""
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        from parse_openapi import parse_openapi
    finally:
        sys.path.pop(0)

    with pytest.raises(ValueError, match="missing required 'paths'"):
        parse_openapi({"openapi": "3.0.0", "info": {}})


@pytest.mark.req("REQ-YG-585")
def test_parse_openapi_invalid_paths_type():
    """AC-06: parse_openapi raises ValueError for non-object paths."""
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        from parse_openapi import parse_openapi
    finally:
        sys.path.pop(0)

    with pytest.raises(ValueError, match="'paths' must be a JSON object"):
        parse_openapi({"openapi": "3.0.0", "paths": "not-a-dict"})


# ---------------------------------------------------------------------------
# Manifest loading via graph fixture (AC-08)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-585")
def test_manifest_loads_in_graph_context():
    """AC-08: A fixture graph consuming curl_probe via manifest: loads."""
    from yamlgraph.tools.manifest import expand_tool_manifests

    tools = {
        "curl_probe": {
            "manifest": str(TOOLS_DIR / "curl_probe.tool.yaml"),
        },
    }
    expanded = expand_tool_manifests(tools, source_path=None)
    assert "curl_probe" in expanded
    assert expanded["curl_probe"]["type"] == "python"
    assert expanded["curl_probe"]["function"] == "curl_probe"
