"""FR-806 RED witnesses — author.sh brief pre-flight (premise + budget).

Judged contract (FR-806 judgement, R-1..R-4): mechanical pre-flight
before the copilot backend spawns. Premise failures ONLY for paths
asserted as existing inputs (outputs pass); command checks are static
(env assignments, python -m, ./relative-script; brief text never
executed); budget warning at 2+ live full-pipeline smokes citing the
900s ceiling, advisory only; --no-preflight skips only the pre-flight;
no LLM in the pre-flight path.
"""

import ast
import importlib.util
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.process  # exercises scripts/ (FR-756 process boundary)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PREFLIGHT_PY = REPO_ROOT / "scripts" / "author_preflight.py"
AUTHOR_SH = REPO_ROOT / "scripts" / "author.sh"


def _load_module():
    spec = importlib.util.spec_from_file_location("author_preflight", PREFLIGHT_PY)
    module = importlib.util.module_from_spec(spec)
    sys.modules["author_preflight"] = module  # dataclass annotation resolution
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def preflight():
    assert PREFLIGHT_PY.exists(), f"Missing helper: {PREFLIGHT_PY}"
    return _load_module()


def _brief(tmp_path: Path, text: str) -> Path:
    brief = tmp_path / "brief.md"
    brief.write_text(text, encoding="utf-8")
    return brief


CLEAN_BRIEF = """\
# Task: demo graph

Create the graph at examples/demos/newdemo/graph.yaml with a single
llm node. Write prompts to examples/demos/newdemo/prompts/step.yaml.

## Validation

```bash
yamlgraph graph lint examples/demos/newdemo/graph.yaml
```
"""


# ---------------------------------------------------------------------------
# AC-01: asserted-but-absent existing input fails pre-flight
# ---------------------------------------------------------------------------


class TestPremiseFailures:
    @pytest.mark.req("REQ-YG-598")
    def test_absent_asserted_fixture_is_violation(self, preflight, tmp_path):
        brief = _brief(
            tmp_path,
            CLEAN_BRIEF
            + "\nUse the existing fixture server tests/fixtures/spa_server.py"
            " which serves /api/data.\n",
        )
        result = preflight.run_preflight(brief, workdir=tmp_path)
        assert not result.ok
        assert any("tests/fixtures/spa_server.py" in v for v in result.violations)

    @pytest.mark.req("REQ-YG-598")
    def test_violation_quotes_the_line(self, preflight, tmp_path):
        line = "Validation runs against the existing fixture tests/fixtures/gone.json."
        brief = _brief(tmp_path, CLEAN_BRIEF + "\n" + line + "\n")
        result = preflight.run_preflight(brief, workdir=tmp_path)
        assert not result.ok
        assert any(
            "gone.json" in v and "existing fixture" in v for v in result.violations
        )

    @pytest.mark.req("REQ-YG-598")
    def test_present_asserted_fixture_passes(self, preflight, tmp_path):
        fixtures = tmp_path / "tests" / "fixtures"
        fixtures.mkdir(parents=True)
        (fixtures / "spa_server.py").write_text("# fixture\n", encoding="utf-8")
        brief = _brief(
            tmp_path,
            CLEAN_BRIEF
            + "\nUse the existing fixture server tests/fixtures/spa_server.py.\n",
        )
        result = preflight.run_preflight(brief, workdir=tmp_path)
        assert result.ok


# ---------------------------------------------------------------------------
# AC-02: output paths the run will create are NOT premises
# ---------------------------------------------------------------------------


class TestOutputPathsPass:
    @pytest.mark.req("REQ-YG-598")
    def test_created_graph_path_is_not_a_premise(self, preflight, tmp_path):
        brief = _brief(tmp_path, CLEAN_BRIEF)
        result = preflight.run_preflight(brief, workdir=tmp_path)
        assert result.ok, result.violations

    @pytest.mark.req("REQ-YG-598")
    def test_neutral_mention_is_not_a_premise(self, preflight, tmp_path):
        brief = _brief(
            tmp_path,
            CLEAN_BRIEF + "\nSee also docs/some-unrelated-notes.md for style.\n",
        )
        result = preflight.run_preflight(brief, workdir=tmp_path)
        assert result.ok, result.violations


# ---------------------------------------------------------------------------
# AC-03 + AC-04: static command resolution in the validation section
# ---------------------------------------------------------------------------


class TestCommandResolution:
    @pytest.mark.req("REQ-YG-598")
    def test_unresolvable_executable_is_violation(self, preflight, tmp_path):
        brief = _brief(
            tmp_path,
            CLEAN_BRIEF.replace(
                "yamlgraph graph lint examples/demos/newdemo/graph.yaml",
                "totally-missing-executable-fr806 --flag",
            ),
        )
        result = preflight.run_preflight(brief, workdir=tmp_path)
        assert not result.ok
        assert any("totally-missing-executable-fr806" in v for v in result.violations)

    @pytest.mark.req("REQ-YG-598")
    def test_python_dash_m_resolves(self, preflight, tmp_path):
        brief = _brief(
            tmp_path,
            CLEAN_BRIEF.replace(
                "yamlgraph graph lint examples/demos/newdemo/graph.yaml",
                "python3 -m pytest tests/unit -q",
            ),
        )
        result = preflight.run_preflight(brief, workdir=tmp_path)
        assert result.ok, result.violations

    @pytest.mark.req("REQ-YG-598")
    def test_env_assignment_prefix_resolves(self, preflight, tmp_path):
        brief = _brief(
            tmp_path,
            CLEAN_BRIEF.replace(
                "yamlgraph graph lint examples/demos/newdemo/graph.yaml",
                "PROVIDER=anthropic python3 -m pytest tests/unit -q",
            ),
        )
        result = preflight.run_preflight(brief, workdir=tmp_path)
        assert result.ok, result.violations

    @pytest.mark.req("REQ-YG-598")
    def test_relative_script_resolves_when_executable(self, preflight, tmp_path):
        script = tmp_path / "smoke.sh"
        script.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        brief = _brief(
            tmp_path,
            CLEAN_BRIEF.replace(
                "yamlgraph graph lint examples/demos/newdemo/graph.yaml",
                "./smoke.sh",
            ),
        )
        result = preflight.run_preflight(brief, workdir=tmp_path)
        assert result.ok, result.violations

    @pytest.mark.req("REQ-YG-598")
    def test_missing_relative_script_is_violation(self, preflight, tmp_path):
        brief = _brief(
            tmp_path,
            CLEAN_BRIEF.replace(
                "yamlgraph graph lint examples/demos/newdemo/graph.yaml",
                "./does-not-exist.sh",
            ),
        )
        result = preflight.run_preflight(brief, workdir=tmp_path)
        assert not result.ok

    @pytest.mark.req("REQ-YG-598")
    def test_brief_command_bodies_are_never_executed(self, preflight, tmp_path):
        canary = tmp_path / "pwned"
        brief = _brief(
            tmp_path,
            CLEAN_BRIEF.replace(
                "yamlgraph graph lint examples/demos/newdemo/graph.yaml",
                f'echo "$(touch {canary})"',
            ),
        )
        preflight.run_preflight(brief, workdir=tmp_path)
        assert not canary.exists(), "pre-flight executed brief-controlled text"


# ---------------------------------------------------------------------------
# AC-05: budget heuristic warns, proceeds
# ---------------------------------------------------------------------------


class TestBudgetHeuristic:
    @pytest.mark.req("REQ-YG-598")
    def test_two_full_pipeline_smokes_warn_and_proceed(self, preflight, tmp_path):
        brief = _brief(
            tmp_path,
            CLEAN_BRIEF.replace(
                "yamlgraph graph lint examples/demos/newdemo/graph.yaml",
                "yamlgraph graph run examples/demos/newdemo/graph.yaml"
                ' --var url="https://a.example" --full\n'
                "yamlgraph graph run examples/demos/newdemo/graph.yaml"
                ' --var url="https://b.example" --full',
            ),
        )
        result = preflight.run_preflight(brief, workdir=tmp_path)
        assert result.ok
        assert any("900" in w for w in result.warnings)

    @pytest.mark.req("REQ-YG-598")
    def test_single_full_pipeline_smoke_does_not_warn(self, preflight, tmp_path):
        brief = _brief(
            tmp_path,
            CLEAN_BRIEF.replace(
                "yamlgraph graph lint examples/demos/newdemo/graph.yaml",
                "yamlgraph graph run examples/demos/newdemo/graph.yaml --full",
            ),
        )
        result = preflight.run_preflight(brief, workdir=tmp_path)
        assert result.ok
        assert not result.warnings

    @pytest.mark.req("REQ-YG-598")
    def test_three_narrow_smokes_warn(self, preflight, tmp_path):
        narrow = "\n".join(
            f"yamlgraph graph run examples/demos/newdemo/steps/step{i}.yaml --full"
            for i in range(3)
        )
        brief = _brief(
            tmp_path,
            CLEAN_BRIEF.replace(
                "yamlgraph graph lint examples/demos/newdemo/graph.yaml", narrow
            ),
        )
        result = preflight.run_preflight(brief, workdir=tmp_path)
        assert result.ok
        assert any("900" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# AC-06: clean brief passes; AC-08: no LLM in the pre-flight path
# ---------------------------------------------------------------------------


class TestCleanBriefAndPurity:
    @pytest.mark.req("REQ-YG-598")
    def test_clean_brief_passes(self, preflight, tmp_path):
        brief = _brief(tmp_path, CLEAN_BRIEF)
        result = preflight.run_preflight(brief, workdir=tmp_path)
        assert result.ok
        assert not result.violations

    @pytest.mark.req("REQ-YG-598")
    def test_preflight_imports_stdlib_only(self):
        tree = ast.parse(PREFLIGHT_PY.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        non_stdlib = {m for m in imported if m not in sys.stdlib_module_names}
        assert not non_stdlib, f"non-stdlib imports in pre-flight: {non_stdlib}"


# ---------------------------------------------------------------------------
# AC-01 (route half) + AC-07: shell-level — backend spawn boundary
# ---------------------------------------------------------------------------


def _run_author(tmp_path: Path, brief: Path, *flags: str) -> tuple[int, str, Path]:
    """Run author.sh with a stub backend; return (rc, output, marker)."""
    marker = tmp_path / "backend-spawned"
    stub = tmp_path / "yamlgraph-stub"
    stub.write_text(f'#!/bin/sh\ntouch "{marker}"\nexit 0\n', encoding="utf-8")
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    env = dict(os.environ)
    env.pop("AUTHOR_EXECUTION", None)
    env["AUTHOR_WORKDIR"] = str(tmp_path)
    env["YAMLGRAPH_BIN"] = str(stub)
    proc = subprocess.run(
        ["bash", str(AUTHOR_SH), *flags, str(brief)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        timeout=60,
    )
    return proc.returncode, proc.stdout + proc.stderr, marker


class TestRouteBoundary:
    @pytest.mark.req("REQ-YG-598")
    def test_doomed_brief_exits_64_without_backend_spawn(self, tmp_path):
        brief = _brief(
            tmp_path,
            CLEAN_BRIEF
            + "\nUse the existing fixture server tests/fixtures/spa_server.py.\n",
        )
        rc, output, marker = _run_author(tmp_path, brief)
        assert rc == 64, output
        assert not marker.exists(), "backend was spawned despite premise failure"
        assert "tests/fixtures/spa_server.py" in output

    @pytest.mark.req("REQ-YG-598")
    def test_no_preflight_skips_only_preflight(self, tmp_path):
        brief = _brief(
            tmp_path,
            CLEAN_BRIEF
            + "\nUse the existing fixture server tests/fixtures/spa_server.py.\n",
        )
        rc, output, marker = _run_author(tmp_path, brief, "--no-preflight")
        # Backend spawned (pre-flight skipped) but the report gate still
        # fails the run: stub writes no artifact -> contract violation 65.
        assert marker.exists(), "backend was not spawned under --no-preflight"
        assert rc == 65, output

    @pytest.mark.req("REQ-YG-598")
    def test_clean_brief_reaches_backend(self, tmp_path):
        brief = _brief(tmp_path, CLEAN_BRIEF)
        rc, output, marker = _run_author(tmp_path, brief)
        assert marker.exists(), f"backend not spawned for clean brief: {output}"
        assert rc == 65, output  # stub writes no artifact; report gate holds
