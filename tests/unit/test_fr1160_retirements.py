"""FR-1160 — the FR-1159 map memo contrib and demo are retired (REQ-YG-727, CAP-303).

RED on the pre-removal tree, GREEN after the removal commit.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SHARED = REPO / "examples/shared"

# process: reads capabilities/, changelog/, examples/ (FR-756)
pytestmark = pytest.mark.process

DELETED = [
    "yamlgraph/contrib/map_memo.py",
    "examples/demos/map_memo",
    "tests/unit/test_fr1159_map_memo_contrib.py",
    "capabilities/CAP-302-map-memo-contrib.yaml",
    "changelog/unreleased/fr-1159-map-memo-contrib.md",
]


@pytest.mark.req("REQ-YG-727")
@pytest.mark.parametrize("rel", DELETED)
def test_contrib_artifact_deleted(rel: str) -> None:
    assert not (REPO / rel).exists()


@pytest.mark.req("REQ-YG-727")
def test_memo_lives_in_examples_shared() -> None:
    assert (SHARED / "map_memo.py").is_file()


@pytest.mark.req("REQ-YG-727")
@pytest.mark.parametrize("name", ["map_memo_split", "map_memo_merge"])
def test_manifest_loads_memo_by_path(name: str) -> None:
    manifest = yaml.safe_load((SHARED / f"{name}.tool.yaml").read_text("utf-8"))
    assert manifest["runtime"].get("path") == "map_memo.py"
    assert "module" not in manifest["runtime"]


@pytest.mark.req("REQ-YG-727")
@pytest.mark.parametrize(
    "rel",
    ["yamlgraph/contrib/__init__.py", "vulture_whitelist.py", "examples/README.md"],
)
def test_no_map_memo_token(rel: str) -> None:
    assert "map_memo" not in (REPO / rel).read_text(encoding="utf-8")
