"""Tests for scripts/req_coverage.py — requirement coverage reporter.

FR-080: Infrastructure Script Unit Tests — Phase 4 (req_coverage).
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import req_coverage


@pytest.mark.req("REQ-YG-063")
class TestExtractReqMarkers:
    """Tests for extract_req_markers() function."""

    def test_single(self, tmp_path: Path) -> None:
        """Should extract single @pytest.mark.req decorator."""
        code = """\
import pytest

@pytest.mark.req("REQ-YG-014")
def test_example():
    pass
"""
        test_file = tmp_path / "test_foo.py"
        test_file.write_text(code)

        markers = req_coverage.extract_req_markers(test_file)

        assert "REQ-YG-014" in markers
        assert "test_foo::test_example" in markers["REQ-YG-014"]

    def test_multiple_args(self, tmp_path: Path) -> None:
        """Should extract multiple requirements from single decorator."""
        code = """\
import pytest

@pytest.mark.req("REQ-YG-014", "REQ-YG-031")
def test_multiple():
    pass
"""
        test_file = tmp_path / "test_multi.py"
        test_file.write_text(code)

        markers = req_coverage.extract_req_markers(test_file)

        assert "REQ-YG-014" in markers
        assert "REQ-YG-031" in markers
        assert "test_multi::test_multiple" in markers["REQ-YG-014"]
        assert "test_multi::test_multiple" in markers["REQ-YG-031"]

    def test_class_level(self, tmp_path: Path) -> None:
        """Should apply class-level marker to all test methods."""
        code = """\
import pytest

@pytest.mark.req("REQ-YG-005")
class TestClass:
    def test_method_one(self):
        pass

    def test_method_two(self):
        pass
"""
        test_file = tmp_path / "test_class.py"
        test_file.write_text(code)

        markers = req_coverage.extract_req_markers(test_file)

        assert "REQ-YG-005" in markers
        tests = markers["REQ-YG-005"]
        assert "test_class::TestClass::test_method_one" in tests
        assert "test_class::TestClass::test_method_two" in tests

    def test_syntax_error(self, tmp_path: Path) -> None:
        """Should return empty dict for files with syntax errors."""
        test_file = tmp_path / "test_broken.py"
        test_file.write_text("def broken(:\n    pass")

        markers = req_coverage.extract_req_markers(test_file)

        assert markers == {}

    def test_method_level_marker(self, tmp_path: Path) -> None:
        """Should extract method-level markers in classes."""
        code = """\
import pytest

class TestExample:
    @pytest.mark.req("REQ-YG-012")
    def test_with_marker(self):
        pass

    def test_without_marker(self):
        pass
"""
        test_file = tmp_path / "test_method.py"
        test_file.write_text(code)

        markers = req_coverage.extract_req_markers(test_file)

        assert "REQ-YG-012" in markers
        assert "test_method::TestExample::test_with_marker" in markers["REQ-YG-012"]


@pytest.mark.req("REQ-YG-063")
class TestModuleToPath:
    """Tests for _module_to_path() function."""

    def test_converts_dotted(self, tmp_path: Path) -> None:
        """Should convert dotted module name to path."""
        # Create a mock file structure
        module_dir = tmp_path / "yamlgraph" / "utils"
        module_dir.mkdir(parents=True)
        (module_dir / "llm_factory.py").write_text("")

        with patch.object(Path, "__new__", return_value=tmp_path):
            # The function uses Path(__file__).parent.parent as root
            original_file = req_coverage.__file__
            try:
                req_coverage.__file__ = str(tmp_path / "scripts" / "req_coverage.py")
                result = req_coverage._module_to_path("yamlgraph.utils.llm_factory")
            finally:
                req_coverage.__file__ = original_file

        assert result == "yamlgraph/utils/llm_factory.py"


@pytest.mark.req("REQ-YG-063")
class TestCollectYamlgraphImports:
    """Tests for _collect_yamlgraph_imports() function."""

    def test_collects_imports(self) -> None:
        """Should collect yamlgraph imports from AST nodes."""
        import ast

        source = """\
from yamlgraph.executor import execute_prompt
from yamlgraph.utils.llm_factory import create_llm
import yamlgraph.models
"""
        tree = ast.parse(source)
        nodes = [n for n in tree.body if isinstance(n, ast.Import | ast.ImportFrom)]

        with patch.object(req_coverage, "_module_to_path") as mock_to_path:
            mock_to_path.side_effect = lambda m: m.replace(".", "/") + ".py"
            paths = req_coverage._collect_yamlgraph_imports(nodes)

        assert len(paths) == 3
        assert "yamlgraph/executor.py" in paths
        assert "yamlgraph/utils/llm_factory.py" in paths
        assert "yamlgraph/models.py" in paths


@pytest.mark.req("REQ-YG-063")
class TestLoadReqDescriptions:
    """Tests for _load_req_descriptions() function."""

    def test_parses(self, tmp_path: Path) -> None:
        """Should parse requirement descriptions from ARCHITECTURE.md."""
        arch_md = tmp_path / "ARCHITECTURE.md"
        arch_md.write_text("""\
# Requirements

| REQ-YG-001 | Load graph configurations from YAML | modules |
| REQ-YG-002 | Validate graph configs with Pydantic | models |
""")

        descriptions = req_coverage._load_req_descriptions(tmp_path)

        assert descriptions["REQ-YG-001"] == "Load graph configurations from YAML"
        assert descriptions["REQ-YG-002"] == "Validate graph configs with Pydantic"

    def test_missing_file(self, tmp_path: Path) -> None:
        """Should return empty dict when ARCHITECTURE.md missing."""
        descriptions = req_coverage._load_req_descriptions(tmp_path)

        assert descriptions == {}


@pytest.mark.req("REQ-YG-063")
class TestMain:
    """Tests for main() function."""

    def test_produces_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Main should produce report output (smoke test)."""
        # Create minimal test directory structure
        test_dir = tmp_path / "tests" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_smoke.py"
        test_file.write_text("""\
import pytest

@pytest.mark.req("REQ-YG-001")
def test_smoke():
    pass
""")

        with (
            patch.object(req_coverage.sys, "argv", ["req_coverage.py"]),
            patch.object(req_coverage, "ALL_REQS", ["REQ-YG-001"]),
            patch.object(
                req_coverage, "CAPABILITIES", {"CAP-01": ("Test Cap", ["REQ-YG-001"])}
            ),
        ):
            original_file = req_coverage.__file__
            try:
                req_coverage.__file__ = str(tmp_path / "scripts" / "req_coverage.py")
                req_coverage.main()
            finally:
                req_coverage.__file__ = original_file

        captured = capsys.readouterr()
        assert "REQUIREMENT TRACEABILITY REPORT" in captured.out
        assert "CAP-01" in captured.out

    def test_strict_mode_fails_if_gap(self, tmp_path: Path) -> None:
        """--strict should exit 1 when requirements uncovered."""
        # Create empty test directory
        test_dir = tmp_path / "tests" / "unit"
        test_dir.mkdir(parents=True)

        with (
            patch.object(req_coverage.sys, "argv", ["req_coverage.py", "--strict"]),
            patch.object(req_coverage, "ALL_REQS", ["REQ-YG-999"]),  # Uncovered
            patch.object(req_coverage, "CAPABILITIES", {}),
            pytest.raises(SystemExit) as exc_info,
        ):
            original_file = req_coverage.__file__
            try:
                req_coverage.__file__ = str(tmp_path / "scripts" / "req_coverage.py")
                req_coverage.main()
            finally:
                req_coverage.__file__ = original_file

        assert exc_info.value.code == 1

    def test_no_strict_without_flag(self, tmp_path: Path) -> None:
        """Without --strict, should not exit on uncovered requirements."""
        # Create empty test directory
        test_dir = tmp_path / "tests" / "unit"
        test_dir.mkdir(parents=True)

        with (
            patch.object(req_coverage.sys, "argv", ["req_coverage.py"]),
            patch.object(req_coverage, "ALL_REQS", ["REQ-YG-999"]),  # Uncovered
            patch.object(req_coverage, "CAPABILITIES", {}),
        ):
            original_file = req_coverage.__file__
            try:
                req_coverage.__file__ = str(tmp_path / "scripts" / "req_coverage.py")
                # Should not raise SystemExit
                req_coverage.main()
            finally:
                req_coverage.__file__ = original_file


@pytest.mark.req("REQ-YG-063")
class TestArchitectureCrossCheck:
    """Tests for architecture cross-check in main() — FR-107."""

    def _setup_covered_env(self, tmp_path: Path, arch_reqs: list[str]) -> None:
        """Create test dir with a test covering REQ-YG-001 and an ARCHITECTURE.md."""
        test_dir = tmp_path / "tests" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_smoke.py"
        test_file.write_text("""\
import pytest

@pytest.mark.req("REQ-YG-001")
def test_smoke():
    pass
""")
        # Write ARCHITECTURE.md with given req IDs
        arch_md = tmp_path / "ARCHITECTURE.md"
        lines = ["# Requirements\n"]
        for req in arch_reqs:
            lines.append(f"| {req} | Description for {req} | modules |\n")
        arch_md.write_text("".join(lines))

    def test_phantom_req_strict_exits_nonzero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--strict exits 1 when a req is in ALL_REQS but missing from ARCHITECTURE.md."""
        # ARCHITECTURE.md has no REQ-YG-001 row → phantom requirement
        self._setup_covered_env(tmp_path, arch_reqs=[])

        with (
            patch.object(req_coverage.sys, "argv", ["req_coverage.py", "--strict"]),
            patch.object(req_coverage, "ALL_REQS", ["REQ-YG-001"]),
            patch.object(
                req_coverage, "CAPABILITIES", {"CAP-01": ("Test", ["REQ-YG-001"])}
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            original_file = req_coverage.__file__
            try:
                req_coverage.__file__ = str(tmp_path / "scripts" / "req_coverage.py")
                req_coverage.main()
            finally:
                req_coverage.__file__ = original_file

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "missing from ARCHITECTURE.md" in captured.out
        assert "REQ-YG-001" in captured.out

    def test_phantom_req_no_strict_warns_exits_zero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Without --strict, prints warning but exits zero for undocumented reqs."""
        self._setup_covered_env(tmp_path, arch_reqs=[])

        with (
            patch.object(req_coverage.sys, "argv", ["req_coverage.py"]),
            patch.object(req_coverage, "ALL_REQS", ["REQ-YG-001"]),
            patch.object(
                req_coverage, "CAPABILITIES", {"CAP-01": ("Test", ["REQ-YG-001"])}
            ),
        ):
            original_file = req_coverage.__file__
            try:
                req_coverage.__file__ = str(tmp_path / "scripts" / "req_coverage.py")
                req_coverage.main()  # Should NOT raise SystemExit
            finally:
                req_coverage.__file__ = original_file

        captured = capsys.readouterr()
        assert "missing from ARCHITECTURE.md" in captured.out

    def test_no_false_positive_when_all_documented(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """No warning when all ALL_REQS are documented in ARCHITECTURE.md."""
        self._setup_covered_env(tmp_path, arch_reqs=["REQ-YG-001"])

        with (
            patch.object(req_coverage.sys, "argv", ["req_coverage.py", "--strict"]),
            patch.object(req_coverage, "ALL_REQS", ["REQ-YG-001"]),
            patch.object(
                req_coverage, "CAPABILITIES", {"CAP-01": ("Test", ["REQ-YG-001"])}
            ),
        ):
            original_file = req_coverage.__file__
            try:
                req_coverage.__file__ = str(tmp_path / "scripts" / "req_coverage.py")
                req_coverage.main()  # Should NOT raise SystemExit
            finally:
                req_coverage.__file__ = original_file

        captured = capsys.readouterr()
        assert "missing from ARCHITECTURE.md" not in captured.out


@pytest.mark.req("REQ-YG-063")
class TestPhantomRequirementDetection:
    """Tests for reverse-check: phantom requirement detection — FR-145.

    Detects @pytest.mark.req markers that reference IDs not in ALL_REQS.
    """

    def _setup_env(
        self,
        tmp_path: Path,
        test_code: str,
        all_reqs: list[str],
        arch_reqs: list[str] | None = None,
    ) -> None:
        """Create test dir with given code and ARCHITECTURE.md."""
        test_dir = tmp_path / "tests" / "unit"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_phantom.py"
        test_file.write_text(test_code)
        arch_md = tmp_path / "ARCHITECTURE.md"
        lines = ["# Requirements\n"]
        for req in arch_reqs or all_reqs:
            lines.append(f"| {req} | Description for {req} | modules |\n")
        arch_md.write_text("".join(lines))

    def test_phantom_strict_exits_nonzero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--strict exits 1 when test references a req ID not in ALL_REQS."""
        self._setup_env(
            tmp_path,
            test_code="""\
import pytest

@pytest.mark.req("REQ-YG-FAKE")
def test_with_phantom():
    pass
""",
            all_reqs=["REQ-YG-001"],
        )

        with (
            patch.object(req_coverage.sys, "argv", ["req_coverage.py", "--strict"]),
            patch.object(req_coverage, "ALL_REQS", ["REQ-YG-001"]),
            patch.object(req_coverage, "CAPABILITIES", {}),
            pytest.raises(SystemExit) as exc_info,
        ):
            original_file = req_coverage.__file__
            try:
                req_coverage.__file__ = str(tmp_path / "scripts" / "req_coverage.py")
                req_coverage.main()
            finally:
                req_coverage.__file__ = original_file

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Phantom requirement IDs" in captured.out
        assert "REQ-YG-FAKE" in captured.out

    def test_phantom_output_lists_referencing_tests(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Output lists each phantom ID with the test function(s) referencing it."""
        self._setup_env(
            tmp_path,
            test_code="""\
import pytest

@pytest.mark.req("REQ-YG-GHOST")
def test_alpha():
    pass

@pytest.mark.req("REQ-YG-GHOST")
def test_beta():
    pass
""",
            all_reqs=["REQ-YG-001"],
        )

        with (
            patch.object(req_coverage.sys, "argv", ["req_coverage.py"]),
            patch.object(req_coverage, "ALL_REQS", ["REQ-YG-001"]),
            patch.object(req_coverage, "CAPABILITIES", {}),
        ):
            original_file = req_coverage.__file__
            try:
                req_coverage.__file__ = str(tmp_path / "scripts" / "req_coverage.py")
                req_coverage.main()
            finally:
                req_coverage.__file__ = original_file

        captured = capsys.readouterr()
        assert "REQ-YG-GHOST" in captured.out
        assert "2 test(s)" in captured.out
        assert "test_phantom::test_alpha" in captured.out
        assert "test_phantom::test_beta" in captured.out

    def test_no_phantom_no_warning(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """No phantom warning when all marker IDs exist in ALL_REQS."""
        self._setup_env(
            tmp_path,
            test_code="""\
import pytest

@pytest.mark.req("REQ-YG-001")
def test_valid():
    pass
""",
            all_reqs=["REQ-YG-001"],
        )

        with (
            patch.object(req_coverage.sys, "argv", ["req_coverage.py", "--strict"]),
            patch.object(req_coverage, "ALL_REQS", ["REQ-YG-001"]),
            patch.object(
                req_coverage, "CAPABILITIES", {"CAP-01": ("Test", ["REQ-YG-001"])}
            ),
        ):
            original_file = req_coverage.__file__
            try:
                req_coverage.__file__ = str(tmp_path / "scripts" / "req_coverage.py")
                req_coverage.main()  # Should NOT raise SystemExit
            finally:
                req_coverage.__file__ = original_file

        captured = capsys.readouterr()
        assert "Phantom requirement IDs" not in captured.out

    def test_phantom_without_strict_warns_exits_zero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Without --strict, prints phantom warning but exits zero."""
        self._setup_env(
            tmp_path,
            test_code="""\
import pytest

@pytest.mark.req("REQ-YG-NOPE")
def test_phantom():
    pass
""",
            all_reqs=["REQ-YG-001"],
        )

        with (
            patch.object(req_coverage.sys, "argv", ["req_coverage.py"]),
            patch.object(req_coverage, "ALL_REQS", ["REQ-YG-001"]),
            patch.object(req_coverage, "CAPABILITIES", {}),
        ):
            original_file = req_coverage.__file__
            try:
                req_coverage.__file__ = str(tmp_path / "scripts" / "req_coverage.py")
                req_coverage.main()  # Should NOT raise SystemExit
            finally:
                req_coverage.__file__ = original_file

        captured = capsys.readouterr()
        assert "Phantom requirement IDs" in captured.out
        assert "REQ-YG-NOPE" in captured.out

    def test_detail_mode_unaffected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--detail output is unaffected by phantom detection."""
        self._setup_env(
            tmp_path,
            test_code="""\
import pytest

@pytest.mark.req("REQ-YG-001")
def test_valid():
    pass
""",
            all_reqs=["REQ-YG-001"],
        )

        with (
            patch.object(req_coverage.sys, "argv", ["req_coverage.py", "--detail"]),
            patch.object(req_coverage, "ALL_REQS", ["REQ-YG-001"]),
            patch.object(
                req_coverage, "CAPABILITIES", {"CAP-01": ("Test", ["REQ-YG-001"])}
            ),
        ):
            original_file = req_coverage.__file__
            try:
                req_coverage.__file__ = str(tmp_path / "scripts" / "req_coverage.py")
                req_coverage.main()
            finally:
                req_coverage.__file__ = original_file

        captured = capsys.readouterr()
        assert "DETAILED MAPPING" in captured.out
        assert "REQ-YG-001" in captured.out

    def test_forward_checks_still_work_with_phantom(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Forward checks (uncovered + undocumented) still trigger alongside phantoms."""
        self._setup_env(
            tmp_path,
            test_code="""\
import pytest

@pytest.mark.req("REQ-YG-PHANTOM")
def test_phantom():
    pass
""",
            all_reqs=["REQ-YG-001"],
            arch_reqs=["REQ-YG-001"],
        )

        with (
            patch.object(req_coverage.sys, "argv", ["req_coverage.py", "--strict"]),
            patch.object(req_coverage, "ALL_REQS", ["REQ-YG-001"]),
            patch.object(
                req_coverage, "CAPABILITIES", {"CAP-01": ("Test", ["REQ-YG-001"])}
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            original_file = req_coverage.__file__
            try:
                req_coverage.__file__ = str(tmp_path / "scripts" / "req_coverage.py")
                req_coverage.main()
            finally:
                req_coverage.__file__ = original_file

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        # Both forward (uncovered) and reverse (phantom) reported
        assert "UNCOVERED" in captured.out
        assert "Phantom requirement IDs" in captured.out
