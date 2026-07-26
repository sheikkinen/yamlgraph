"""Tests for scripts/direct_import_scan.py (FR-761 direct-import scanner).

Every case builds an isolated fixture tree (tmp_path) with its own
pyproject.toml and scans it via scan(repo_root=..., pyproject_path=...,
core_roots=..., report_only_roots=..., pending_gaps=...) — never the live
repository — so results are deterministic regardless of what the real
codebase currently imports.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.direct_import_scan import PATH_PREFIX_OWNERS, _normalize, scan

pytestmark = pytest.mark.process

STDLIB = frozenset({"os", "sys", "typing", "pathlib", "dataclasses"})


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _pyproject(
    root: Path, core_deps: list[str], extras: dict[str, list[str]] | None = None
) -> Path:
    extras = extras or {}
    lines = ["[project]", "name = 'fixture'", "dependencies = ["]
    lines += [f'  "{d}",' for d in core_deps]
    lines.append("]")
    if extras:
        lines.append("[project.optional-dependencies]")
        for group, deps in extras.items():
            lines.append(f"{group} = [")
            lines += [f'  "{d}",' for d in deps]
            lines.append("]")
    path = root / "pyproject.toml"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


@pytest.mark.req("REQ-YG-572")
def test_undeclared_core_import_fails(tmp_path: Path) -> None:
    """A core (yamlgraph/) import with no matching pyproject entry is a core failure."""
    _write(tmp_path, "yamlgraph/mod.py", "import totally_undeclared_pkg\n")
    pyproject = _pyproject(tmp_path, core_deps=["pydantic"])

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert len(result.core_failures) == 1
    assert result.core_failures[0].distribution == "totally_undeclared_pkg"
    assert result.pending == []


@pytest.mark.req("REQ-YG-572")
def test_declared_core_import_passes(tmp_path: Path) -> None:
    """A core import whose distribution is declared in pyproject core deps is not a failure."""
    _write(tmp_path, "yamlgraph/mod.py", "import pydantic\n")
    pyproject = _pyproject(tmp_path, core_deps=["pydantic"])

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert result.core_failures == []
    assert result.findings == []


@pytest.mark.req("REQ-YG-572")
def test_stdlib_and_first_party_excluded(tmp_path: Path) -> None:
    """stdlib modules and first-party top-level packages never produce findings."""
    _write(
        tmp_path,
        "yamlgraph/mod.py",
        "import os\nimport typing\nimport yamlgraph.utils.foo\nfrom . import sibling\n",
    )
    pyproject = _pyproject(tmp_path, core_deps=[])

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert result.findings == []


@pytest.mark.req("REQ-YG-572")
def test_nested_and_lazy_imports_are_caught(tmp_path: Path) -> None:
    """Imports inside functions/try-except (not just top-level statements) are extracted."""
    _write(
        tmp_path,
        "yamlgraph/mod.py",
        "def lazy():\n"
        "    try:\n"
        "        import lazy_undeclared_pkg\n"
        "    except ImportError:\n"
        "        pass\n",
    )
    pyproject = _pyproject(tmp_path, core_deps=[])

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert len(result.core_failures) == 1
    assert result.core_failures[0].distribution == "lazy_undeclared_pkg"


@pytest.mark.req("REQ-YG-572")
def test_alias_table_resolves_import_to_distribution(tmp_path: Path) -> None:
    """import yaml resolves to distribution 'pyyaml' via the alias table."""
    _write(tmp_path, "yamlgraph/mod.py", "import yaml\n")
    pyproject = _pyproject(tmp_path, core_deps=["pyyaml"])

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert result.core_failures == []


@pytest.mark.req("REQ-YG-572")
def test_underscore_hyphen_normalization(tmp_path: Path) -> None:
    """import langchain_anthropic matches a declared 'langchain-anthropic' dependency (PEP 503)."""
    _write(tmp_path, "yamlgraph/mod.py", "import langchain_anthropic\n")
    pyproject = _pyproject(tmp_path, core_deps=["langchain-anthropic>=0.3.0"])

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert result.core_failures == []


@pytest.mark.req("REQ-YG-572")
def test_normalize_helper() -> None:
    assert _normalize("langchain_anthropic") == "langchain-anthropic"
    assert _normalize("Langchain.Anthropic") == "langchain-anthropic"
    assert _normalize("langchain-anthropic>=0.3.0") != _normalize("langchain-anthropic")


@pytest.mark.req("REQ-YG-572")
def test_optional_extra_import_satisfies_core_ownership(tmp_path: Path) -> None:
    """An import in yamlgraph/ declared only in an optional extra still passes (FR-761 C-4):
    optional-extra dependencies used by lazy/nested imports inside core files must not be
    forced into core deps merely because the module lives under yamlgraph/.
    """
    _write(
        tmp_path,
        "yamlgraph/utils/llm_providers.py",
        "def azure():\n    import langchain_azure_ai\n",
    )
    pyproject = _pyproject(
        tmp_path, core_deps=[], extras={"azure": ["langchain-azure-ai>=0.1.0"]}
    )

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert result.core_failures == []


@pytest.mark.req("REQ-YG-572")
def test_report_only_roots_never_fail_strict(tmp_path: Path) -> None:
    """Undeclared imports under examples/, scripts/, tests/ are findings but never core failures."""
    _write(tmp_path, "examples/demo/run.py", "import some_example_only_pkg\n")
    _write(tmp_path, "scripts/tool.py", "import another_script_only_pkg\n")
    _write(tmp_path, "tests/unit/test_x.py", "import yet_another_test_only_pkg\n")
    pyproject = _pyproject(tmp_path, core_deps=[])

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert result.core_failures == []
    assert result.pending == []
    assert {f.path_class for f in result.findings} == {"report_only"}
    assert len(result.findings) == 3


@pytest.mark.req("REQ-YG-572")
def test_pending_gaps_are_reported_but_not_blocking(tmp_path: Path) -> None:
    """A core import matching a surface-scoped PENDING_GAPS entry is reported
    separately and does not fail --strict."""
    _write(tmp_path, "yamlgraph/mod.py", "import langchain_core\n")
    pyproject = _pyproject(tmp_path, core_deps=[])

    result = scan(
        STDLIB,
        repo_root=tmp_path,
        pyproject_path=pyproject,
        pending_gaps={("yamlgraph/mod.py", "langchain_core"): "FR-760 test fixture"},
    )

    assert result.core_failures == []
    assert len(result.pending) == 1
    assert result.pending[0].distribution == "langchain_core"
    assert len(result.findings) == 1


@pytest.mark.req("REQ-YG-572")
def test_excluded_roots_produce_no_findings(tmp_path: Path) -> None:
    """A directory outside core_roots/report_only_roots (e.g. docs/) is never scanned."""
    _write(tmp_path, "docs/snippet.py", "import totally_ignored_pkg\n")
    pyproject = _pyproject(tmp_path, core_deps=[])

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert result.findings == []


@pytest.mark.req("REQ-YG-572")
def test_module_level_import_not_satisfied_by_unrelated_extra(tmp_path: Path) -> None:
    """PR #463 review P1 regression: a module-level (unconditional) import in a
    yamlgraph/ file with no recognized owner mapping must fail if its
    distribution is declared ONLY under an unrelated extra — declaring it
    "anywhere" is not enough. This is the exact gap the flattened-declared
    model previously missed.
    """
    _write(tmp_path, "yamlgraph/new_module.py", "import some_new_pkg\n")
    pyproject = _pyproject(
        tmp_path, core_deps=[], extras={"unrelated_extra": ["some-new-pkg>=1.0"]}
    )

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert len(result.core_failures) == 1
    assert result.core_failures[0].distribution == "some_new_pkg"


@pytest.mark.req("REQ-YG-572")
def test_module_level_import_satisfied_by_recognized_owner_extra(
    tmp_path: Path,
) -> None:
    """A module-level import in a file matching PATH_PREFIX_OWNERS passes when
    declared under its owning extra specifically (not just any extra).
    """
    assert "yamlgraph/storage/simple_redis.py" in PATH_PREFIX_OWNERS
    _write(tmp_path, "yamlgraph/storage/simple_redis.py", "import orjson\n")
    pyproject = _pyproject(
        tmp_path, core_deps=[], extras={"redis-simple": ["orjson>=3.9.0"]}
    )

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert result.core_failures == []


@pytest.mark.req("REQ-YG-572")
def test_module_level_import_owner_mapping_is_specific_not_flattened(
    tmp_path: Path,
) -> None:
    """A recognized-surface file's module-level import must be declared under
    ITS owning extra — declaring the same distribution under a completely
    different, unrelated extra must still fail.
    """
    _write(tmp_path, "yamlgraph/storage/simple_redis.py", "import orjson\n")
    pyproject = _pyproject(
        tmp_path, core_deps=[], extras={"totally_unrelated": ["orjson>=3.9.0"]}
    )

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert len(result.core_failures) == 1
    assert result.core_failures[0].distribution == "orjson"


@pytest.mark.req("REQ-YG-572")
def test_report_only_excludes_local_sibling_module(tmp_path: Path) -> None:
    """PR #463 review P2 regression: a report-only file importing a local
    sibling module/package (first-party example code reachable via
    sys.path insertion, not a third-party distribution) must not be
    reported as an undeclared dependency.
    """
    _write(tmp_path, "examples/plot_modeller/run.py", "import nodes\n")
    _write(tmp_path, "examples/plot_modeller/nodes/__init__.py", "")
    _write(tmp_path, "examples/plot_modeller/nodes/step.py", "")
    pyproject = _pyproject(tmp_path, core_deps=[])

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert result.findings == []


@pytest.mark.req("REQ-YG-572")
def test_report_only_excludes_local_sibling_module_file(tmp_path: Path) -> None:
    """Same as above, but the local sibling is a single `.py` file (not a
    package directory), e.g. `examples/daily_digest/tests/test_api.py`
    importing `examples/daily_digest/api.py`."""
    _write(tmp_path, "examples/daily_digest/tests/test_api.py", "import api\n")
    _write(tmp_path, "examples/daily_digest/api.py", "")
    pyproject = _pyproject(tmp_path, core_deps=[])

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert result.findings == []


@pytest.mark.req("REQ-YG-572")
def test_report_only_still_flags_genuinely_undeclared_import(tmp_path: Path) -> None:
    """The local-module exclusion must not suppress genuine report-only
    findings — only names that actually resolve to a real sibling file/dir
    are excluded.
    """
    _write(tmp_path, "examples/plot_modeller/run.py", "import genuinely_missing_pkg\n")
    pyproject = _pyproject(tmp_path, core_deps=[])

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert len(result.findings) == 1
    assert result.findings[0].distribution == "genuinely_missing_pkg"


@pytest.mark.req("REQ-YG-572")
def test_top_level_try_import_is_core_surface(tmp_path: Path) -> None:
    """PR #463 review P1 regression: a top-level try/except import still
    executes at module import time, so it is part of the strict core
    import surface — an unrelated optional extra declaring the same
    distribution must not exempt it.
    """
    _write(
        tmp_path,
        "yamlgraph/core.py",
        "try:\n    import httpx\nexcept ImportError:\n    pass\n",
    )
    pyproject = _pyproject(tmp_path, core_deps=[], extras={"booking": ["httpx>=0.27"]})

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert len(result.core_failures) == 1
    assert result.core_failures[0].distribution == "httpx"
    assert result.core_failures[0].nested is False


@pytest.mark.req("REQ-YG-572")
def test_top_level_try_import_satisfied_by_owner_extra(tmp_path: Path) -> None:
    """A top-level try/except import inside a recognized optional feature
    surface may still be satisfied by that surface's owning extra —
    module-level ownership rules apply, not the any-extra shortcut.
    """
    owned = next(iter(PATH_PREFIX_OWNERS))
    owner_extra = next(iter(PATH_PREFIX_OWNERS[owned]))
    _write(
        tmp_path,
        owned if owned.endswith(".py") else f"{owned}/mod.py",
        "try:\n    import ownedpkg\nexcept ImportError:\n    pass\n",
    )
    pyproject = _pyproject(
        tmp_path, core_deps=[], extras={owner_extra: ["ownedpkg>=1.0"]}
    )

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert result.core_failures == []


@pytest.mark.req("REQ-YG-572")
def test_pending_gap_is_path_specific(tmp_path: Path) -> None:
    """PR #463 review P2 regression: a pending-gap disposition is tied to
    the specific file it was granted for — the same import name in any
    other file is a blocking core failure, not a pending entry.
    """
    _write(tmp_path, "yamlgraph/providers.py", "import litellm\n")
    _write(tmp_path, "yamlgraph/new_core.py", "import litellm\n")
    pyproject = _pyproject(tmp_path, core_deps=[])

    result = scan(
        STDLIB,
        repo_root=tmp_path,
        pyproject_path=pyproject,
        pending_gaps={("yamlgraph/providers.py", "litellm"): "FR-762 fixture"},
    )

    assert len(result.pending) == 1
    assert result.pending[0].file.endswith("providers.py")
    assert len(result.core_failures) == 1
    assert result.core_failures[0].file.endswith("new_core.py")


@pytest.mark.req("REQ-YG-572")
def test_pending_gap_directory_prefix_scopes_matches(tmp_path: Path) -> None:
    """A pending-gap entry may name a directory prefix; files under it
    match, files outside it do not.
    """
    _write(tmp_path, "yamlgraph/a2a/server.py", "import starlette\n")
    _write(tmp_path, "yamlgraph/other.py", "import starlette\n")
    pyproject = _pyproject(tmp_path, core_deps=[])

    result = scan(
        STDLIB,
        repo_root=tmp_path,
        pyproject_path=pyproject,
        pending_gaps={("yamlgraph/a2a", "starlette"): "FR-762 fixture"},
    )

    assert len(result.pending) == 1
    assert result.pending[0].file.endswith("server.py")
    assert len(result.core_failures) == 1
    assert result.core_failures[0].file.endswith("other.py")


@pytest.mark.req("REQ-YG-572")
def test_dotted_namespace_import_requires_namespace_distribution(
    tmp_path: Path,
) -> None:
    """PR #463 review P1 regression: `from langgraph.checkpoint.redis import
    RedisSaver` must be checked against distribution
    `langgraph-checkpoint-redis`, not collapsed to top-level `langgraph`
    (declared in core) — the reviewer's probe showed the gate passing even
    with the namespace distribution undeclared."""
    _write(
        tmp_path,
        "yamlgraph/storage/factory.py",
        "def make():\n    from langgraph.checkpoint.redis import RedisSaver\n"
        "    return RedisSaver\n",
    )
    pyproject = _pyproject(tmp_path, core_deps=["langgraph"])

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert len(result.core_failures) == 1
    assert result.core_failures[0].distribution == "langgraph-checkpoint-redis"


@pytest.mark.req("REQ-YG-572")
def test_dotted_namespace_import_satisfied_by_declared_distribution(
    tmp_path: Path,
) -> None:
    """The same dotted namespace import passes when its actual distribution
    is declared (nested import: any declared extra counts)."""
    _write(
        tmp_path,
        "yamlgraph/storage/factory.py",
        "def make():\n    from langgraph.checkpoint.redis import RedisSaver\n"
        "    return RedisSaver\n",
    )
    pyproject = _pyproject(
        tmp_path,
        core_deps=["langgraph"],
        extras={"redis": ["langgraph-checkpoint-redis"]},
    )

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert result.core_failures == []
    assert result.findings == []


@pytest.mark.req("REQ-YG-572")
def test_opentelemetry_namespace_resolution(tmp_path: Path) -> None:
    """FR-759 merge: opentelemetry is a namespace package — nested imports
    of the api, sdk, and otlp-exporter surfaces resolve to their own
    distributions, all declared by the otel extra."""
    _write(
        tmp_path,
        "yamlgraph/observability/otel.py",
        "def setup():\n"
        "    from opentelemetry import trace\n"
        "    from opentelemetry.sdk.trace import TracerProvider\n"
        "    from opentelemetry.exporter.otlp.proto.http.trace_exporter"
        " import OTLPSpanExporter\n"
        "    return trace, TracerProvider, OTLPSpanExporter\n",
    )
    pyproject = _pyproject(
        tmp_path,
        core_deps=[],
        extras={
            "otel": [
                "opentelemetry-api",
                "opentelemetry-sdk",
                "opentelemetry-exporter-otlp",
            ]
        },
    )

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert result.core_failures == []
    assert result.findings == []


@pytest.mark.req("REQ-YG-572")
def test_google_protobuf_dotted_resolution(tmp_path: Path) -> None:
    """`from google.protobuf.json_format import ParseDict` resolves to
    distribution `protobuf` via the dotted-prefix table."""
    _write(
        tmp_path,
        "yamlgraph/mod.py",
        "def f():\n    from google.protobuf.json_format import ParseDict\n"
        "    return ParseDict\n",
    )
    pyproject = _pyproject(tmp_path, core_deps=[], extras={"a2a": ["protobuf"]})

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert result.core_failures == []
    assert result.findings == []


@pytest.mark.req("REQ-YG-572")
def test_report_only_excludes_sys_path_inserted_example_root(
    tmp_path: Path,
) -> None:
    """PR #463 review P2 regression: a test that inserts an example root
    onto sys.path (Path(__file__)... / "examples" / "book_translator")
    and imports a first-party package from it must not be reported as an
    undeclared dependency."""
    _write(tmp_path, "examples/book_translator/nodes/__init__.py", "")
    _write(tmp_path, "examples/book_translator/nodes/tools.py", "X = 1\n")
    _write(
        tmp_path,
        "tests/unit/test_splitter.py",
        "import sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).parent.parent.parent"
        ' / "examples" / "book_translator"))\n'
        "from nodes.tools import X\n",
    )
    pyproject = _pyproject(tmp_path, core_deps=[])

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert result.findings == []


@pytest.mark.req("REQ-YG-572")
def test_report_only_excludes_sys_path_inserted_src_root(tmp_path: Path) -> None:
    """PR #463 review P2 regression (rtm-hello shape): a test inserting a
    sibling `src/` dir onto sys.path and importing a module from it is
    first-party, not an undeclared dependency."""
    _write(tmp_path, "examples/rtm/src/calculator.py", "def add(a, b): return a + b\n")
    _write(
        tmp_path,
        "examples/rtm/tests/test_calculator.py",
        "import sys\n"
        "from pathlib import Path\n"
        'sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))\n'
        "from calculator import add\n",
    )
    pyproject = _pyproject(tmp_path, core_deps=[])

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert result.findings == []


@pytest.mark.req("REQ-YG-572")
def test_sys_path_exclusion_does_not_hide_third_party(tmp_path: Path) -> None:
    """sys.path-root exclusion is evidence-based: an import with no matching
    module under any inserted root is still reported."""
    _write(
        tmp_path,
        "tests/unit/test_thing.py",
        "import sys\n"
        "from pathlib import Path\n"
        'sys.path.insert(0, str(Path(__file__).parent / "helpers"))\n'
        "import genuinely_missing_pkg\n",
    )
    pyproject = _pyproject(tmp_path, core_deps=[])

    result = scan(STDLIB, repo_root=tmp_path, pyproject_path=pyproject)

    assert len(result.findings) == 1
    assert result.findings[0].distribution == "genuinely_missing_pkg"
