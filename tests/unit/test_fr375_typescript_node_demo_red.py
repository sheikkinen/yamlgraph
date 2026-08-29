"""Acceptance tests for FR-375 TypeScript Node.js subprocess demo assets."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.req("REQ-YG-354")
def test_ac08_typescript_demo_files_exist_and_execfile_uses_json_flag() -> None:
    demo_dir = ROOT / "examples" / "demos" / "typescript-node"
    assert demo_dir.exists(), "Expected examples/demos/typescript-node/ to exist"

    required_files = [
        demo_dir / "package.json",
        demo_dir / "tsconfig.json",
        demo_dir / "README.md",
        demo_dir / "demo.sh",
        demo_dir / "demo-output.log",
        demo_dir / "src" / "index.ts",
    ]
    for file_path in required_files:
        assert file_path.exists(), f"Missing required demo file: {file_path}"

    package_json = json.loads((demo_dir / "package.json").read_text(encoding="utf-8"))
    assert package_json["name"]
    assert "typescript" in package_json.get("devDependencies", {})

    index_ts = (demo_dir / "src" / "index.ts").read_text(encoding="utf-8")
    assert "execFile" in index_ts
    assert "--json" in index_ts
    assert "JSON.parse" in index_ts
    assert "yamlgraph" in index_ts


@pytest.mark.req("REQ-YG-355")
def test_ac09_docs_include_json_mode_and_typescript_demo_guidance() -> None:
    cli_doc = (ROOT / "reference" / "cli.md").read_text(encoding="utf-8")
    examples_doc = (ROOT / "examples" / "README.md").read_text(encoding="utf-8")

    assert "--json" in cli_doc
    assert "stdout" in cli_doc.lower() and "json" in cli_doc.lower()
    assert "subprocess" in cli_doc.lower()
    assert "mcp" in cli_doc.lower()

    assert "typescript-node" in examples_doc
    assert "subprocess" in examples_doc.lower()
    assert "mcp" in examples_doc.lower()
