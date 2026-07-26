"""Tests for scripts/example_taxonomy_scan.py (FR-762)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
import example_taxonomy_scan  # noqa: E402
from example_taxonomy_scan import (  # noqa: E402
    _extras_covering,
    _has_main_entrypoint,
    _has_readme_usage_command,
    _is_example_root,
    _local_module_names,
    _readme_cli_surface_paths,
    _root_imports,
    _yaml_tool_module_paths,
    build_taxonomy,
    classify_root,
    discover_roots,
)

pytestmark = pytest.mark.process


def _write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


_USAGE_README = "# Demo\n\n```bash\npython run.py\n```\n"
_FIXTURE_README = "# Fixture corpus\n\nNo runnable command here, just data.\n"


@pytest.mark.req("REQ-YG-571")
def test_discover_roots_finds_top_level_and_nested_demos(tmp_path):
    examples = tmp_path / "examples"
    _write(examples / "rag" / "README.md", _USAGE_README)
    _write(examples / "demos" / "hello" / "graph.yaml", "nodes:\n  a: {}\n")
    _write(examples / "demos" / "chatterbox" / "graph.yaml", "nodes:\n  a: {}\n")

    roots = discover_roots(examples)
    rel = sorted(str(r.relative_to(tmp_path)) for r in roots)
    assert rel == [
        "examples/demos/chatterbox",
        "examples/demos/hello",
        "examples/rag",
    ]


@pytest.mark.req("REQ-YG-571")
def test_discover_roots_finds_nested_root_inside_another_root(tmp_path):
    """PR #464 review P1 regression: a directory nested inside another
    example root (e.g. `examples/dungeon_master/api/`) must get its own
    row when it independently qualifies as a root — omitting it was the
    reviewer's concrete finding."""
    examples = tmp_path / "examples"
    _write(examples / "dungeon_master" / "README.md", _USAGE_README)
    _write(
        examples / "dungeon_master" / "api" / "app.py",
        'if __name__ == "__main__":\n    pass\n',
    )

    roots = discover_roots(examples)
    rel = sorted(str(r.relative_to(tmp_path)) for r in roots)
    assert rel == [
        "examples/dungeon_master",
        "examples/dungeon_master/api",
    ]


@pytest.mark.req("REQ-YG-571")
def test_discover_roots_finds_nested_graph_yaml_root(tmp_path):
    """Mirrors the reviewer's second cited omission:
    `examples/demos/interrupt/subgraphs/` (a graph YAML two levels under a
    demos/ subdirectory that is itself a root)."""
    examples = tmp_path / "examples"
    _write(
        examples / "demos" / "interrupt" / "interrupt-parent.yaml",
        "nodes:\n  a: {}\n",
    )
    _write(
        examples / "demos" / "interrupt" / "subgraphs" / "interrupt-child.yaml",
        "nodes:\n  a: {}\n",
    )

    roots = discover_roots(examples)
    rel = sorted(str(r.relative_to(tmp_path)) for r in roots)
    assert rel == [
        "examples/demos/interrupt",
        "examples/demos/interrupt/subgraphs",
    ]


@pytest.mark.req("REQ-YG-571")
def test_prompt_yaml_with_nodes_substring_is_not_a_root(tmp_path):
    """PR #464 review P1 regression: prompt YAML files containing the
    substring `nodes:` (schema fields like `affected_nodes:`, or `nodes`
    nested below the top level) must NOT make their directory an example
    root. The reviewer's concrete findings were prompt dirs such as
    `examples/beautify/prompts/` falsely admitted as roots."""
    examples = tmp_path / "examples"
    _write(
        examples / "beautify" / "prompts" / "analyze.yaml",
        "name: analyze\nschema:\n  fields:\n"
        "    affected_nodes: {type: str, description: 'nodes: touched'}\n",
    )
    _write(
        examples / "run-analyzer" / "prompts" / "summarize.yaml",
        "name: summarize\nmeta:\n  nodes:\n    - not-a-graph\n",
    )
    _write(examples / "real" / "graph.yaml", "nodes:\n  a: {}\n")

    roots = discover_roots(examples)
    rel = sorted(str(r.relative_to(tmp_path)) for r in roots)
    assert rel == ["examples/real"]


@pytest.mark.req("REQ-YG-571")
def test_unparseable_yaml_is_not_a_root(tmp_path):
    """Invalid YAML containing the substring `nodes:` must not qualify."""
    examples = tmp_path / "examples"
    _write(examples / "broken" / "graph.yaml", "nodes: [unclosed\n  a: {}\n")

    assert discover_roots(examples) == []


@pytest.mark.req("REQ-YG-571")
def test_discover_roots_excludes_empty_dirs(tmp_path):
    examples = tmp_path / "examples"
    _write(examples / "empty" / "notes.txt", "no graph, no readme, no main")
    roots = discover_roots(examples)
    assert roots == []


@pytest.mark.req("REQ-YG-571")
def test_has_readme_usage_command_requires_fenced_command(tmp_path):
    """PR #464 review regression guard: a README merely existing (no
    runnable command in a fenced code block) must not count — otherwise
    fixture/docs directories like `examples/plot_modeller/fixtures/`
    would be misdiscovered as roots."""
    with_command = tmp_path / "with_command"
    _write(with_command / "README.md", _USAGE_README)
    assert _has_readme_usage_command(with_command)

    without_command = tmp_path / "without_command"
    _write(without_command / "README.md", _FIXTURE_README)
    assert not _has_readme_usage_command(without_command)

    no_readme = tmp_path / "no_readme"
    no_readme.mkdir()
    assert not _has_readme_usage_command(no_readme)


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
def test_is_example_root_false_for_fixture_readme_without_command(tmp_path):
    d = tmp_path / "fixtures"
    _write(d / "README.md", _FIXTURE_README)
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
    examples_root = tmp_path / "examples"
    d = examples_root / "root"
    _write(d / "tools" / "__init__.py")
    _write(d / "nodes" / "canon_tools.py")
    names = _local_module_names(d, examples_root)
    assert "tools" in names
    assert "canon_tools" in names


@pytest.mark.req("REQ-YG-571")
def test_local_module_names_includes_ancestor_sibling_package(tmp_path):
    """PR #464 review follow-up: a nested root's local-module resolution
    must also see sibling packages one level up (e.g.
    `examples/fsm-router/tests/` importing `examples/fsm-router/actions/`),
    not just names within its own subtree."""
    examples_root = tmp_path / "examples"
    parent = examples_root / "fsm-router"
    nested_root = parent / "tests"
    _write(parent / "actions" / "__init__.py")
    _write(nested_root / "test_thing.py", "import actions\n")

    names = _local_module_names(nested_root, examples_root)
    assert "actions" in names


@pytest.mark.req("REQ-YG-571")
def test_extras_covering_prefers_single_full_owner_over_partial_owners():
    """PR #464 review P2 regression: when one extra's declared distributions
    fully cover the root's non-core imports, use that single extra — never
    credit an unrelated extra that merely happens to own ONE of the
    imports (the `openai_proxy` bug: fastapi/uvicorn/starlette all needed,
    `openai-proxy` alone covers them, but `booking`/`digest`/`npc` etc.
    each partially overlap too)."""
    deps_by_group = {
        "core": [],
        "dev": [],
        "openai-proxy": ["fastapi", "uvicorn", "starlette"],
        "booking": ["fastapi", "httpx", "uvicorn"],
        "digest": ["fastapi", "uvicorn"],
    }
    extras = _extras_covering({"fastapi", "uvicorn", "starlette"}, deps_by_group)
    assert extras == ["openai-proxy"]


@pytest.mark.req("REQ-YG-571")
def test_extras_covering_empty_for_no_required_distributions():
    assert _extras_covering(set(), {"core": [], "dev": [], "rag": ["pyarrow"]}) == []


@pytest.mark.req("REQ-YG-571")
def test_classify_root_extra_backed(tmp_path):
    repo_root = tmp_path
    examples_root = repo_root / "examples"
    root = examples_root / "myroot"
    _write(root / "app.py", "import pyarrow\n")
    stdlib = frozenset(sys.stdlib_module_names)
    declared = {"pyarrow"}
    deps_by_group = {"core": [], "dev": [], "rag": ["pyarrow"]}

    row = classify_root(root, stdlib, declared, deps_by_group, repo_root, examples_root)
    assert row["status"] == "extra-backed"
    assert row["extra"] == ["rag"]
    assert row["path"] == "examples/myroot"


@pytest.mark.req("REQ-YG-571")
def test_classify_root_externally_provisioned(tmp_path):
    repo_root = tmp_path
    examples_root = repo_root / "examples"
    root = examples_root / "myroot"
    _write(root / "app.py", "import claude_agent_sdk\n")
    stdlib = frozenset(sys.stdlib_module_names)
    declared: set[str] = set()
    deps_by_group = {"core": [], "dev": []}

    row = classify_root(root, stdlib, declared, deps_by_group, repo_root, examples_root)
    assert row["status"] == "externally-provisioned"
    assert "claude_agent_sdk" in row["external_reason"]


@pytest.mark.req("REQ-YG-571")
def test_classify_root_treats_local_sibling_module_as_local(tmp_path):
    """A root that imports its own local `tools` package must not be flagged
    as an undeclared third-party dependency (the sys.path-insert idiom)."""
    repo_root = tmp_path
    examples_root = repo_root / "examples"
    root = examples_root / "myroot"
    _write(root / "app.py", "import tools\n")
    _write(root / "tools" / "__init__.py")
    stdlib = frozenset(sys.stdlib_module_names)
    declared: set[str] = set()
    deps_by_group = {"core": [], "dev": []}

    row = classify_root(root, stdlib, declared, deps_by_group, repo_root, examples_root)
    assert row["status"] == "extra-backed"
    assert row["extra"] is None


@pytest.mark.req("REQ-YG-571")
def test_classify_root_partial_owner_does_not_satisfy_full_coverage(tmp_path):
    """PR #464 review P2 regression at the classify_root level: a root
    needing two distributions must not be marked extra-backed by an extra
    that only declares one of them, even if every individual import
    resolves to *some* declared distribution."""
    repo_root = tmp_path
    examples_root = repo_root / "examples"
    root = examples_root / "myroot"
    _write(root / "app.py", "import fastapi\nimport starlette\n")
    stdlib = frozenset(sys.stdlib_module_names)
    declared = {"fastapi", "starlette"}
    deps_by_group = {
        "core": [],
        "dev": [],
        "partial-a": ["fastapi"],
        "partial-b": ["starlette"],
        "full": ["fastapi", "starlette"],
    }

    row = classify_root(root, stdlib, declared, deps_by_group, repo_root, examples_root)
    assert row["status"] == "extra-backed"
    assert row["extra"] == ["full"]


@pytest.mark.req("REQ-YG-571")
def test_yaml_tool_module_paths_resolves_module_reference(tmp_path):
    """PR #464 review, round 2: a `type: python` tool's `module:` reference
    points at a yamlgraph/ file whose imports never show up in a plain
    `*.py`-under-root scan — the a2a_call bug (module:
    yamlgraph.contrib.a2a_client declared in graph.yaml, but a2a_client.py
    lives outside the example root)."""
    repo_root = tmp_path
    root = repo_root / "examples" / "myroot"
    _write(
        root / "graph.yaml",
        "tools:\n"
        "  send:\n"
        "    type: python\n"
        "    module: yamlgraph.contrib.fake_client\n"
        "    function: send\n"
        "nodes:\n  a: {}\n",
    )
    module_file = repo_root / "yamlgraph" / "contrib" / "fake_client.py"
    _write(module_file, "import httpx\n")

    paths = _yaml_tool_module_paths(root, repo_root)
    assert paths == {module_file}


@pytest.mark.req("REQ-YG-571")
def test_yaml_tool_module_paths_ignores_non_yamlgraph_module(tmp_path):
    repo_root = tmp_path
    root = repo_root / "examples" / "myroot"
    _write(
        root / "graph.yaml",
        "tools:\n"
        "  send:\n"
        "    type: python\n"
        "    module: some_other_package.helper\n"
        "nodes:\n  a: {}\n",
    )
    assert _yaml_tool_module_paths(root, repo_root) == set()


@pytest.mark.req("REQ-YG-571")
def test_readme_cli_surface_paths_resolves_documented_subcommand(tmp_path, monkeypatch):
    """PR #464 review, round 2: a README-documented `yamlgraph <subcommand>`
    invocation drives an optional CLI surface (subprocess launch, not a
    Python import) whose implementing module's imports must still count —
    the a2a_server bug (README says `yamlgraph a2a serve`/`card`, both
    implemented in yamlgraph/cli/a2a_commands.py, but the example root has
    no .py files of its own)."""
    repo_root = tmp_path
    root = repo_root / "examples" / "myroot"
    _write(root / "README.md", "Run `yamlgraph widget serve` to start.\n")
    module_file = repo_root / "yamlgraph" / "cli" / "widget_commands.py"
    _write(module_file, "import uvicorn\n")
    monkeypatch.setitem(
        example_taxonomy_scan.README_CLI_SUBCOMMAND_MODULES, "widget", module_file
    )

    paths = _readme_cli_surface_paths(root)
    assert paths == {module_file}


@pytest.mark.req("REQ-YG-571")
def test_readme_cli_surface_paths_empty_without_matching_subcommand(tmp_path):
    root = tmp_path / "examples" / "myroot"
    _write(root / "README.md", "No CLI commands documented here.\n")
    assert _readme_cli_surface_paths(root) == set()


@pytest.mark.req("REQ-YG-571")
def test_root_imports_follows_yaml_tool_module_reference(tmp_path):
    """classify_root-level regression: the extra import surface reached via
    a YAML tool-module reference is folded into the same import list used
    for undeclared/extras classification."""
    repo_root = tmp_path
    root = repo_root / "examples" / "myroot"
    _write(root / "app.py", "import pyarrow\n")
    _write(
        root / "graph.yaml",
        "tools:\n"
        "  send:\n"
        "    type: python\n"
        "    module: yamlgraph.contrib.fake_client\n"
        "nodes:\n  a: {}\n",
    )
    _write(repo_root / "yamlgraph" / "contrib" / "fake_client.py", "import httpx\n")

    names = _root_imports(root, repo_root)
    assert "pyarrow" in names
    assert "httpx" in names


@pytest.mark.req("REQ-YG-571")
def test_classify_root_credits_extra_reached_via_yaml_tool_module(tmp_path):
    """End-to-end classify_root regression mirroring the a2a_call fix: a
    root with no local third-party imports of its own, but a graph.yaml
    tool `module:` reference to a yamlgraph/ file that imports a
    declared distribution, must be extra-backed by the owning extra —
    not `extra: null`."""
    repo_root = tmp_path
    examples_root = repo_root / "examples"
    root = examples_root / "myroot"
    _write(
        root / "graph.yaml",
        "tools:\n"
        "  send:\n"
        "    type: python\n"
        "    module: yamlgraph.contrib.fake_client\n"
        "nodes:\n  a: {}\n",
    )
    _write(repo_root / "yamlgraph" / "contrib" / "fake_client.py", "import httpx\n")
    stdlib = frozenset(sys.stdlib_module_names)
    declared = {"httpx"}
    deps_by_group = {"core": [], "dev": [], "a2a": ["httpx"]}

    row = classify_root(root, stdlib, declared, deps_by_group, repo_root, examples_root)
    assert row["status"] == "extra-backed"
    assert row["extra"] == ["a2a"]


@pytest.mark.req("REQ-YG-571")
def test_real_a2a_examples_are_extra_backed_by_a2a():
    """Regression guard for the exact PR #464 review finding: a2a_call and
    a2a_server must resolve to `extra: [a2a, ...]`, never `extra: null`,
    against the real repo tree (not a synthetic fixture)."""
    rows = build_taxonomy()
    by_path = {r["path"]: r for r in rows}

    a2a_call = by_path["examples/demos/a2a_call"]
    assert a2a_call["status"] == "extra-backed"
    assert "a2a" in (a2a_call["extra"] or [])

    a2a_server = by_path["examples/demos/a2a_server"]
    assert a2a_server["status"] == "extra-backed"
    assert "a2a" in (a2a_server["extra"] or [])


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
        _write(d / "README.md", _USAGE_README)

    rows = build_taxonomy(examples_root, pyproject, repo_root)
    statuses = {r["path"]: r["status"] for r in rows}
    assert statuses == {
        "examples/good": "extra-backed",
        "examples/bad": "externally-provisioned",
    }
    assert all(r["status"] in ("extra-backed", "externally-provisioned") for r in rows)
