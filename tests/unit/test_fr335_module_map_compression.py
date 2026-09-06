"""RED acceptance tests for FR-335 module-map compression."""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[2]
SCRIPT_PATH = WORKTREE / "scripts" / "generate_module_map.py"
MODULE_MAP_PATH = WORKTREE / "reference" / "module-map.md"
SOURCE_ROOT = WORKTREE / "yamlgraph"
FR331_TEST_PATH = (
    WORKTREE / "tests" / "unit" / "test_fr331_static_module_map_tier2_context.py"
)

_DEP_TOKEN_RE = re.compile(r"`([^`]+)`|([A-Za-z_][A-Za-z0-9_\.]*)")
_DEP_KEYWORDS = {
    "import",
    "imports",
    "dependency",
    "dependencies",
    "none",
    "_none_",
    "deps",
}


def _run_generator() -> str:
    assert SCRIPT_PATH.exists(), f"Missing generator script: {SCRIPT_PATH}"
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        out = Path(f.name)
    try:
        completed = subprocess.run(
            ["python", str(SCRIPT_PATH), str(out)],
            cwd=WORKTREE,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert out.exists(), f"Missing generated map: {out}"
        return out.read_text(encoding="utf-8")
    finally:
        out.unlink(missing_ok=True)


def _extract_dependency_tokens(module_map: str) -> set[str]:
    deps: set[str] = set()
    in_dep_block = False

    for raw_line in module_map.splitlines():
        stripped = raw_line.strip()
        lowered = stripped.lower()

        is_dep_header = "import dependenc" in lowered or re.match(
            r"-?\s*deps?:", lowered
        )
        if is_dep_header:
            in_dep_block = True
        elif in_dep_block and not raw_line.startswith("  "):
            in_dep_block = False

        if not (is_dep_header or in_dep_block):
            continue

        for match in _DEP_TOKEN_RE.findall(raw_line):
            token = (match[0] or match[1]).strip().strip(",").lstrip(".")
            if not token:
                continue
            lowered_token = token.lower()
            if lowered_token in _DEP_KEYWORDS:
                continue
            if "/" in token or token.endswith(".py"):
                continue
            deps.add(token)

    return deps


def _public_exports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    exports: list[str] = []
    for node in tree.body:
        if isinstance(
            node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        ) and not node.name.startswith("_"):
            exports.append(node.name)
    return exports


def _trivial_init_modules() -> list[str]:
    trivial: list[str] = []
    for path in sorted(SOURCE_ROOT.rglob("__init__.py")):
        rel = path.relative_to(WORKTREE).as_posix()
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        exports = _public_exports(path)
        if line_count < 10 and len(exports) <= 1:
            trivial.append(rel)
    return trivial


def _import_roots_from_script(script_path: Path) -> set[str]:
    tree = ast.parse(script_path.read_text(encoding="utf-8"), filename=str(script_path))
    roots: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            roots.add((node.module or "").split(".", 1)[0])
    return roots


@pytest.mark.req("REQ-YG-667")
class TestFR335ModuleMapCompression:
    """AC-01..AC-05 contract for compressed module-map output."""

    def test_ac01_regenerated_module_map_stays_within_line_budget(self) -> None:
        module_map = _run_generator()
        line_count = len(module_map.splitlines())
        # FR-677: temporarily bumped 250 -> 260 to admit node_timeout.py split.
        # FR-716/719: 260 -> 265 for node_schema, streaming_events,
        # conditions_smt (judged splits); FR-723: route_log, mermaid_export,
        # export_commands (route hook + authored-map export). FR-717
        # sub-packaging then ADDED three __init__ entries — the promised
        # restoration needs the generator to collapse package inits
        # (follow-up seed). Bound re-measured at rebase: 274 with both
        # arcs landed. FR-759: 275 -> 277 for the observability package
        # (otel.py, __init__.py) and compile/node_otel.py.
        # FR-768: 277 -> 279 for tools/manifest.py (tool manifests).
        # FR-797: 279 -> 285 for the size-gate extraction of the subgraph
        # interrupt relay (compile/subgraph_relay.py, models/relay_fields.py,
        # models/state_codegen.py).
        # FR-810: 285 -> 287 for linter/checks_tool_call.py (size-gate split
        # of check_tool_call_nodes out of checks_semantic.py at the cap).
        # FR-807/808: 287 -> 291 for artifact_hash.py and
        # regulated_evidence.py (content identity + policy split).
        # FR-892: 291 -> 293 for tools/tool_slots.py (invocation-time
        # tool-slot binding).
        assert line_count <= 293, f"module-map too large: {line_count} lines (max 293)"

    def test_ac02_dependency_lists_contain_only_yamlgraph_imports(self) -> None:
        module_map = _run_generator()
        deps = _extract_dependency_tokens(module_map)
        assert deps, "Expected at least one dependency token in generated module map"
        non_internal = sorted(
            dep
            for dep in deps
            if dep != "yamlgraph" and not dep.startswith("yamlgraph.")
        )
        assert not non_internal, f"Non-yamlgraph dependencies found: {non_internal}"

    def test_ac03_trivial_init_modules_are_not_rendered_as_verbose_sections(
        self,
    ) -> None:
        module_map = _run_generator()
        trivial_modules = _trivial_init_modules()
        assert (
            trivial_modules
        ), "Expected at least one trivial __init__.py module for AC coverage"

        for module_path in trivial_modules:
            assert f"`{module_path}`" in module_map
            assert (
                f"### `{module_path}`" not in module_map
            ), f"Trivial module rendered as verbose section: {module_path}"

    def test_ac04_existing_fr331_acceptance_tests_still_pass(self) -> None:
        assert FR331_TEST_PATH.exists(), f"Missing FR-331 test file: {FR331_TEST_PATH}"
        completed = subprocess.run(
            ["pytest", str(FR331_TEST_PATH), "-q", "--no-cov"],
            cwd=WORKTREE,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stdout + "\n" + completed.stderr

    def test_ac05_generator_script_remains_stdlib_only(self) -> None:
        import_roots = _import_roots_from_script(SCRIPT_PATH)
        allowed = set(sys.stdlib_module_names) | {"__future__", ""}
        unexpected = sorted(root for root in import_roots if root not in allowed)
        assert not unexpected, f"Non-stdlib imports in generator: {unexpected}"
