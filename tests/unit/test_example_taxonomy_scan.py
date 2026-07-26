"""Tests for scripts/example_taxonomy_scan.py (FR-762)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from example_taxonomy_scan import (  # noqa: E402
    _has_main_entrypoint,
    _is_example_root,
    _local_module_names,
    _owning_extras,
    build_taxonomy,
    classify_root,
    discover_roots,
)

pytestmark = pytest.mark.process


def _write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.mark.req("REQ-YG-571")
def test_discover_roots_flattens_demos(tmp_path):
    examples = tmp_path / "examples"
    _write(examples / "rag" / "README.md")
    _write(examples / "demos" / "hello" / "graph.yaml", "nodes:\n  a: {}\n")
    _write(examples / "demos" / "chatterbox" / "graph.yaml", "nodes:\n  a: {}\n")
    _write(examples / "shared" / "README.md")  # excluded by name

    roots = discover_roots(examples)
    rel = sorted(str(r.relative_to(tmp_path)) for r in roots)
    assert rel == [
        "examples/demos/chatterbox",
        "examples/demos/hello",
        "examples/rag",
    ]


@pytest.mark.req("REQ-YG-571")
def test_discover_roots_excludes_empty_dirs(tmp_path):
    examples = tmp_path / "examples"
    _write(examples / "empty" / "notes.txt", "no graph, no readme, no main")
    roots = discover_roots(examples)
    assert roots == []


@pytest.mark.req("REQ-YG-571")
def test_is_example_root_detects_main_entrypoint(tmp_path):
    d = tmp_path / "thing"
    _write(d / "run.py", 'if __name__ == "__main__":\n    pass\n')
    assert _is_example_root(d)


@pytest.mark.req("REQ-YG-571")
def test_is_example_root_detects_graph_yaml(tmp_path):
    d = tmp_path / "thing"
    _write(d / "graph.yaml", "nodes:\n  a: {}\n")
    assert _is_example_root(d)


@pytest.mark.req("REQ-YG-571")
def test_is_example_root_false_without_markers(tmp_path):
    d = tmp_path / "thing"
    _write(d / "notes.txt", "just notes")
    assert not _is_example_root(d)


@pytest.mark.req("REQ-YG-571")
def test_has_main_entrypoint_finds_python_file(tmp_path):
    d = tmp_path / "thing"
    _write(d / "app.py", 'if __name__ == "__main__":\n    pass\n')
    _write(d / "lib.py", "def helper(): pass\n")
    entrypoints = _has_main_entrypoint(d, tmp_path)
    assert entrypoints == [str(Path("thing") / "app.py")]


@pytest.mark.req("REQ-YG-571")
def test_local_module_names_includes_nested_files_and_dirs(tmp_path):
    d = tmp_path / "root"
    _write(d / "tools" / "__init__.py")
    _write(d / "nodes" / "canon_tools.py")
    names = _local_module_names(d)
    assert "tools" in names
    assert "canon_tools" in names


@pytest.mark.req("REQ-YG-571")
def test_owning_extras_matches_normalized_distribution():
    deps_by_group = {
        "core": ["pydantic"],
        "dev": ["ruff"],
        "rag": ["pyarrow"],
        "replicate": ["litellm"],
    }
    owners = _owning_extras("pyarrow", deps_by_group)
    assert owners == ["rag"]


@pytest.mark.req("REQ-YG-571")
def test_owning_extras_excludes_core_and_dev():
    deps_by_group = {"core": ["pyarrow"], "dev": ["pyarrow"]}
    assert _owning_extras("pyarrow", deps_by_group) == []


@pytest.mark.req("REQ-YG-571")
def test_classify_root_extra_backed(tmp_path):
    repo_root = tmp_path
    root = repo_root / "examples" / "myroot"
    _write(root / "app.py", "import pyarrow\n")
    stdlib = frozenset(sys.stdlib_module_names)
    declared = {"pyarrow"}
    deps_by_group = {"core": [], "dev": [], "rag": ["pyarrow"]}

    row = classify_root(root, stdlib, declared, deps_by_group, repo_root)
    assert row["status"] == "extra-backed"
    assert row["extra"] == ["rag"]
    assert row["path"] == "examples/myroot"


@pytest.mark.req("REQ-YG-571")
def test_classify_root_externally_provisioned(tmp_path):
    repo_root = tmp_path
    root = repo_root / "examples" / "myroot"
    _write(root / "app.py", "import claude_agent_sdk\n")
    stdlib = frozenset(sys.stdlib_module_names)
    declared: set[str] = set()
    deps_by_group = {"core": [], "dev": []}

    row = classify_root(root, stdlib, declared, deps_by_group, repo_root)
    assert row["status"] == "externally-provisioned"
    assert "claude_agent_sdk" in row["external_reason"]


@pytest.mark.req("REQ-YG-571")
def test_classify_root_treats_local_sibling_module_as_local(tmp_path):
    """A root that imports its own local `tools` package must not be flagged
    as an undeclared third-party dependency (the sys.path-insert idiom)."""
    repo_root = tmp_path
    root = repo_root / "examples" / "myroot"
    _write(root / "app.py", "import tools\n")
    _write(root / "tools" / "__init__.py")
    stdlib = frozenset(sys.stdlib_module_names)
    declared: set[str] = set()
    deps_by_group = {"core": [], "dev": []}

    row = classify_root(root, stdlib, declared, deps_by_group, repo_root)
    assert row["status"] == "extra-backed"
    assert row["extra"] is None


@pytest.mark.req("REQ-YG-571")
def test_build_taxonomy_no_third_state(tmp_path):
    """Every discovered root must land in exactly one of the two states."""
    repo_root = tmp_path
    examples_root = repo_root / "examples"
    pyproject = repo_root / "pyproject.toml"
    _write(
        pyproject,
        '[project]\nname = "x"\nversion = "0"\ndependencies = []\n\n'
        '[project.optional-dependencies]\nrag = ["pyarrow"]\n',
    )
    _write(examples_root / "good" / "app.py", "import pyarrow\n")
    _write(examples_root / "bad" / "app.py", "import some_undeclared_thing\n")
    for d in (examples_root / "good", examples_root / "bad"):
        _write(d / "README.md")

    rows = build_taxonomy(examples_root, pyproject, repo_root)
    statuses = {r["path"]: r["status"] for r in rows}
    assert statuses == {
        "examples/good": "extra-backed",
        "examples/bad": "externally-provisioned",
    }
    assert all(r["status"] in ("extra-backed", "externally-provisioned") for r in rows)
