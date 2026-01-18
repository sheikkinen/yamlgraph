"""Tests for template extraction tools."""

from pathlib import Path

from yamlgraph.tools.analysis.template_tools import (
    extract_class_template,
    extract_function_template,
    extract_test_template,
)

# ============================================================================
# extract_function_template tests
# ============================================================================


class TestExtractFunctionTemplate:
    """Tests for extract_function_template."""

    def test_extracts_basic_function(self, tmp_path: Path):
        """Extract template from a simple function."""
        source = tmp_path / "example.py"
        source.write_text('''
def greet(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"
''')
        result = extract_function_template(str(source), "greet")

        assert "template" in result
        template = result["template"]
        assert "{function_name}" in template or "greet" in template
        assert "str" in template  # type hints preserved
        assert "hello" in template.lower() or "{" in template

    def test_extracts_function_with_error_handling(self, tmp_path: Path):
        """Extract template preserves try/except structure."""
        source = tmp_path / "example.py"
        source.write_text('''
def process(file_path: str) -> dict:
    """Process a file."""
    try:
        data = open(file_path).read()
        return {"result": data}
    except FileNotFoundError:
        return {"error": "File not found"}
''')
        result = extract_function_template(str(source), "process")

        assert "template" in result
        template = result["template"]
        assert "try" in template or "{try_block}" in template
        assert "except" in template or "{except_block}" in template

    def test_preserves_docstring_structure(self, tmp_path: Path):
        """Docstring is preserved in template."""
        source = tmp_path / "example.py"
        source.write_text('''
def analyze(file_path: str, depth: int = 3) -> dict:
    """Analyze something.

    Args:
        file_path: Path to the file
        depth: How deep to analyze

    Returns:
        dict with analysis results
    """
    return {}
''')
        result = extract_function_template(str(source), "analyze")

        assert "template" in result
        template = result["template"]
        assert "Args:" in template
        assert "Returns:" in template

    def test_handles_missing_function(self, tmp_path: Path):
        """Returns error for missing function."""
        source = tmp_path / "example.py"
        source.write_text("def other(): pass")

        result = extract_function_template(str(source), "missing")
        assert "error" in result

    def test_handles_missing_file(self):
        """Returns error for missing file."""
        result = extract_function_template("/nonexistent/file.py", "func")
        assert "error" in result

    def test_handles_syntax_error(self, tmp_path: Path):
        """Returns error for invalid Python."""
        source = tmp_path / "bad.py"
        source.write_text("def broken(:")

        result = extract_function_template(str(source), "broken")
        assert "error" in result


# ============================================================================
# extract_class_template tests
# ============================================================================


class TestExtractClassTemplate:
    """Tests for extract_class_template."""

    def test_extracts_basic_class(self, tmp_path: Path):
        """Extract template from a simple class."""
        source = tmp_path / "example.py"
        source.write_text('''
class Widget:
    """A widget."""

    def __init__(self, name: str):
        self.name = name

    def render(self) -> str:
        return f"<{self.name}>"
''')
        result = extract_class_template(str(source), "Widget")

        assert "template" in result
        template = result["template"]
        assert "class" in template
        assert "__init__" in template
        assert "render" in template

    def test_extracts_class_with_inheritance(self, tmp_path: Path):
        """Extract template preserves base classes."""
        source = tmp_path / "example.py"
        source.write_text('''
class MyError(ValueError, RuntimeError):
    """Custom error."""
    pass
''')
        result = extract_class_template(str(source), "MyError")

        assert "template" in result
        template = result["template"]
        assert "ValueError" in template or "{bases}" in template

    def test_extracts_class_variables(self, tmp_path: Path):
        """Extract template includes class variables."""
        source = tmp_path / "example.py"
        source.write_text('''
class Config:
    """Configuration."""

    DEFAULT_TIMEOUT: int = 30
    MAX_RETRIES: int = 3

    def __init__(self):
        self.value = None
''')
        result = extract_class_template(str(source), "Config")

        assert "template" in result
        template = result["template"]
        # Should capture class variable pattern
        assert "TIMEOUT" in template or "int" in template

    def test_handles_missing_class(self, tmp_path: Path):
        """Returns error for missing class."""
        source = tmp_path / "example.py"
        source.write_text("class Other: pass")

        result = extract_class_template(str(source), "Missing")
        assert "error" in result

    def test_handles_missing_file(self):
        """Returns error for missing file."""
        result = extract_class_template("/nonexistent/file.py", "MyClass")
        assert "error" in result


# ============================================================================
# extract_test_template tests
# ============================================================================


class TestExtractTestTemplate:
    """Tests for extract_test_template."""

    def test_extracts_pytest_patterns(self, tmp_path: Path):
        """Extract test template from pytest file."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text('''
import pytest
from mymodule import process

@pytest.fixture
def sample_data():
    return {"key": "value"}

class TestProcess:
    """Tests for process function."""

    def test_basic(self, sample_data):
        result = process(sample_data)
        assert result["status"] == "ok"

    def test_error_handling(self):
        with pytest.raises(ValueError):
            process(None)
''')
        result = extract_test_template(str(test_file), "mymodule")

        assert "template" in result
        template = result["template"]
        assert "@pytest.fixture" in template or "fixture" in template.lower()
        assert "class Test" in template or "{test_class}" in template

    def test_extracts_mock_patterns(self, tmp_path: Path):
        """Extract mock/patch patterns from tests."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text("""
from unittest.mock import patch, MagicMock
from mymodule import fetch_data

def test_with_mock():
    with patch("mymodule.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {}
        result = fetch_data()
        assert result == {}
""")
        result = extract_test_template(str(test_file), "mymodule")

        assert "template" in result
        template = result["template"]
        assert "patch" in template or "mock" in template.lower()

    def test_handles_missing_file(self):
        """Returns error for missing file."""
        result = extract_test_template("/nonexistent/test.py", "module")
        assert "error" in result

    def test_handles_empty_test_file(self, tmp_path: Path):
        """Returns minimal template for empty file."""
        test_file = tmp_path / "test_empty.py"
        test_file.write_text("# Empty test file")

        result = extract_test_template(str(test_file), "module")
        # Should return some default template structure
        assert "template" in result or "error" in result
