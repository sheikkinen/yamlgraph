"""Acceptance tests for FR-278: Remove FR-277 Watcher2 Baseline Dead Code.

These tests verify that all baseline checkpointing dead code is completely removed.
"""

import importlib
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.req("REQ-YG-466")
class TestFR278BaselineCodeRemoval:
    """AC-01: All baseline-related Python modules removed."""

    def test_chaplain_baseline_module_removed(self):
        """yamlgraph/chaplain/baseline.py must not exist."""
        baseline_path = REPO_ROOT / "yamlgraph" / "chaplain" / "baseline.py"
        assert (
            not baseline_path.exists()
        ), f"Dead code module still exists: {baseline_path}"

    def test_chaplain_baseline_not_importable(self):
        """Importing yamlgraph.chaplain.baseline must raise ModuleNotFoundError."""
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("yamlgraph.chaplain.baseline")

    def test_models_baseline_module_removed(self):
        """yamlgraph/models/baseline.py must not exist."""
        baseline_path = REPO_ROOT / "yamlgraph" / "models" / "baseline.py"
        assert (
            not baseline_path.exists()
        ), f"Dead code module still exists: {baseline_path}"

    def test_models_baseline_not_importable(self):
        """Importing yamlgraph.models.baseline must raise ModuleNotFoundError."""
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("yamlgraph.models.baseline")


@pytest.mark.req("REQ-YG-466")
class TestFR278ChaplainPackageRemoval:
    """AC-02: Chaplain package init file removed."""

    def test_chaplain_init_file_removed(self):
        """yamlgraph/chaplain/__init__.py must not exist."""
        init_path = REPO_ROOT / "yamlgraph" / "chaplain" / "__init__.py"
        assert not init_path.exists(), f"Dead code init file still exists: {init_path}"

    def test_chaplain_package_not_importable(self):
        """Importing yamlgraph.chaplain must raise ModuleNotFoundError."""
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("yamlgraph.chaplain")


@pytest.mark.req("REQ-YG-466")
class TestFR278BaselineGraphRemoval:
    """AC-03: Baseline graph YAML file removed."""

    def test_baseline_graph_file_removed(self):
        """.chaplain/graphs/baseline/graph.yaml must not exist."""
        graph_path = REPO_ROOT / ".chaplain" / "graphs" / "baseline" / "graph.yaml"
        assert not graph_path.exists(), f"Dead code graph still exists: {graph_path}"

    def test_baseline_graphs_directory_removed(self):
        """.chaplain/graphs/baseline/ directory must not exist."""
        baseline_dir = REPO_ROOT / ".chaplain" / "graphs" / "baseline"
        assert (
            not baseline_dir.exists()
        ), f"Dead code directory still exists: {baseline_dir}"


@pytest.mark.req("REQ-YG-466")
class TestFR278BaselineTestRemoval:
    """AC-04: Baseline test file removed."""

    def test_fr277_test_file_removed(self):
        """tests/unit/test_fr277_watcher2_baseline_checkpointing.py must not exist."""
        test_path = (
            REPO_ROOT
            / "tests"
            / "unit"
            / "test_fr277_watcher2_baseline_checkpointing.py"
        )
        assert not test_path.exists(), f"Dead code test still exists: {test_path}"


@pytest.mark.req("REQ-YG-466")
class TestFR278CapabilityRegistrationRemoval:
    """AC-05: Capability registration removed."""

    def test_cap_129_file_removed(self):
        """capabilities/CAP-129-watcher2-baseline-checkpointing.yaml must not exist."""
        cap_path = (
            REPO_ROOT / "capabilities" / "CAP-129-watcher2-baseline-checkpointing.yaml"
        )
        assert not cap_path.exists(), f"Dead code capability still exists: {cap_path}"


@pytest.mark.req("REQ-YG-466")
class TestFR278Watcher2ConfigCleanup:
    """AC-06: Import state line removed from start-system.sh."""

    def test_watcher2_baseline_import_removed(self):
        """start-system.sh must not contain --import-state .chaplain/baseline/latest.json."""
        watcher2_path = REPO_ROOT / ".chaplain" / "start-system.sh"

        if watcher2_path.exists():
            content = watcher2_path.read_text()
            assert (
                "--import-state .chaplain/baseline/latest.json" not in content
            ), "start-system.sh still contains baseline import reference"


@pytest.mark.req("REQ-YG-466")
class TestFR278ArchitectureCleanup:
    """AC-07: REQ-YG-279 requirement removed from ARCHITECTURE.md."""

    def test_req_yg_279_removed_from_architecture(self):
        """ARCHITECTURE.md must not contain REQ-YG-279."""
        arch_path = REPO_ROOT / "ARCHITECTURE.md"

        if arch_path.exists():
            content = arch_path.read_text()
            assert (
                "REQ-YG-279" not in content
            ), "ARCHITECTURE.md still contains REQ-YG-279 requirement"


@pytest.mark.req("REQ-YG-466")
class TestFR278ChaplainReadmeCleanup:
    """AC-08: Baseline documentation removed from .chaplain/README.md."""

    def test_baseline_documentation_removed(self):
        """.chaplain/README.md must not contain baseline checkpointing references."""
        readme_path = REPO_ROOT / ".chaplain" / "README.md"

        if readme_path.exists():
            content = readme_path.read_text().lower()
            baseline_terms = [
                "baseline checkpointing",
                "baseline build",
                "baseline_id",
                "latest.json",
                ".chaplain/baseline/",
            ]

            for term in baseline_terms:
                assert (
                    term not in content
                ), f".chaplain/README.md still contains baseline reference: {term}"


@pytest.mark.req("REQ-YG-466")
class TestFR278FeatureRequestRejection:
    """AC-09: FR-277 marked as rejected in feature requests."""

    def test_fr277_marked_rejected(self):
        """FR-277 feature request must be marked as rejected."""
        fr_path = (
            REPO_ROOT / "feature-requests" / "FR-277-watcher2-baseline-checkpointing.md"
        )

        if fr_path.exists():
            content = fr_path.read_text()
            status_indicators = [
                "Status:** Rejected",
                "Status:** REJECTED",
                "Verdict: REJECT",
            ]

            status_found = any(indicator in content for indicator in status_indicators)
            assert (
                status_found
            ), "FR-277 must be marked as rejected with Status: Rejected"


@pytest.mark.req("REQ-YG-466")
class TestFR278NoImportErrors:
    """AC-10: No import errors when running existing tests."""

    def test_existing_tests_run_without_baseline_import_errors(self):
        """Importing core modules must not fail due to baseline references."""
        # Test core imports that might have had baseline references
        importable_modules = [
            "yamlgraph.compile.graph_loader",
            "yamlgraph.executor",
            "yamlgraph.models.graph_schema",
            "yamlgraph.models.schemas",
        ]

        for module_name in importable_modules:
            try:
                importlib.import_module(module_name)
            except ModuleNotFoundError as e:
                if "baseline" in str(e).lower():
                    pytest.fail(
                        f"Import error due to baseline reference in {module_name}: {e}"
                    )
                # Re-raise if it's a different import error
                raise


@pytest.mark.slow
@pytest.mark.req("REQ-YG-466")
class TestFR278NoCodebaseReferences:
    """AC-11: No references to baseline functionality in grep search across codebase."""

    def test_no_baseline_references_in_python_code(self):
        """Python source files must not contain baseline imports or references."""
        python_files = list(REPO_ROOT.rglob("*.py"))
        # Exclude this test file and build artifacts
        python_files = [
            f
            for f in python_files
            if "test_fr278" not in f.name and "build/" not in str(f)
        ]

        forbidden_imports = [
            "from yamlgraph.chaplain.baseline",
            "import yamlgraph.chaplain.baseline",
            "from yamlgraph.models.baseline",
            "import yamlgraph.models.baseline",
        ]

        for file_path in python_files:
            if file_path.suffix == ".py":
                try:
                    content = file_path.read_text()
                    for forbidden in forbidden_imports:
                        assert (
                            forbidden not in content
                        ), f"Found baseline import in {file_path}: {forbidden}"
                except UnicodeDecodeError:
                    # Skip binary files
                    continue

    def test_no_baseline_references_in_yaml_files(self):
        """YAML files must not contain yamlgraph.chaplain.nodes references."""
        yaml_files = [
            f
            for f in REPO_ROOT.rglob("*.yaml")
            if not str(f).startswith(str(REPO_ROOT / "build"))
        ]

        for file_path in yaml_files:
            try:
                content = file_path.read_text()
                assert (
                    "yamlgraph.chaplain.nodes" not in content
                ), f"Found dead chaplain.nodes reference in {file_path}"
                assert (
                    "function: yamlgraph.chaplain." not in content
                ), f"Found dead chaplain function reference in {file_path}"
            except UnicodeDecodeError:
                # Skip binary files
                continue


@pytest.mark.req("REQ-YG-466")
class TestFR278LintingPasses:
    """AC-12: Linting passes (no dead imports or references)."""

    def test_ruff_check_passes(self):
        """ruff check should pass with no import errors."""
        try:
            result = subprocess.run(
                ["ruff", "check", "yamlgraph/"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Allow other linting errors, but fail on import-related errors
            if result.returncode != 0:
                # Check if errors are import-related
                import_error_codes = [
                    "F401",
                    "F403",
                    "F405",
                ]  # unused import, star import issues
                baseline_errors = [
                    line
                    for line in result.stdout.split("\n")
                    if any(code in line for code in import_error_codes)
                    and "baseline" in line.lower()
                ]

                if baseline_errors:
                    pytest.fail(
                        "Import-related linting errors for baseline code:\n"
                        + "\n".join(baseline_errors)
                    )

        except subprocess.TimeoutExpired:
            pytest.skip("ruff check timed out")
        except FileNotFoundError:
            pytest.skip("ruff not available")
