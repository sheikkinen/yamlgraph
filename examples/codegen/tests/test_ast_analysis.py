"""Tests for AST-based code analysis tools."""

import tempfile
from pathlib import Path

from examples.codegen.tools.ast_analysis import get_module_structure


class TestGetModuleStructure:
    """Tests for get_module_structure function."""

    def test_extracts_classes_with_line_numbers(self):
        """Classes include name, bases, methods, line numbers."""
        # Use a known file in the project
        result = get_module_structure("yamlgraph/models/schemas.py")

        assert "error" not in result
        assert "classes" in result
        assert len(result["classes"]) > 0

        # Each class should have required fields
        for cls in result["classes"]:
            assert "name" in cls
            assert "line" in cls
            assert "end_line" in cls
            assert isinstance(cls["line"], int)
            assert isinstance(cls["end_line"], int)
            assert cls["end_line"] >= cls["line"]

    def test_extracts_functions_with_signature(self):
        """Functions include name, args, returns, decorators."""
        result = get_module_structure("yamlgraph/executor.py")

        assert "error" not in result
        assert "functions" in result
        assert len(result["functions"]) > 0

        # Each function should have required fields
        for func in result["functions"]:
            assert "name" in func
            assert "args" in func
            assert "line" in func
            assert "end_line" in func
            assert isinstance(func["args"], list)

    def test_extracts_imports(self):
        """Import statements are extracted."""
        result = get_module_structure("yamlgraph/executor.py")

        assert "error" not in result
        assert "imports" in result
        assert len(result["imports"]) > 0

    def test_extracts_module_docstring(self):
        """Module-level docstring is extracted."""
        result = get_module_structure("yamlgraph/executor.py")

        assert "error" not in result
        assert "docstring" in result
        # executor.py should have a docstring
        assert result["docstring"] is not None

    def test_handles_missing_file(self):
        """Returns error for non-existent file."""
        result = get_module_structure("nonexistent_file_12345.py")

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_handles_syntax_error(self):
        """Returns error for file with syntax errors."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def broken(\n")  # Invalid syntax
            temp_path = f.name

        try:
            result = get_module_structure(temp_path)
            assert "error" in result
            assert "syntax" in result["error"].lower()
        finally:
            Path(temp_path).unlink()

    def test_includes_file_path_in_result(self):
        """Result includes the file path."""
        result = get_module_structure("yamlgraph/executor.py")

        assert "error" not in result
        assert "file" in result
        assert "executor.py" in result["file"]

    def test_extracts_class_methods(self):
        """Class methods are listed."""
        result = get_module_structure("yamlgraph/models/schemas.py")

        assert "error" not in result
        # At least some classes should have methods
        # Note: Pydantic models may not have explicit methods
        assert "methods" in result["classes"][0]

    def test_extracts_class_bases(self):
        """Class base classes are extracted."""
        result = get_module_structure("yamlgraph/models/schemas.py")

        assert "error" not in result
        # Pydantic models inherit from BaseModel
        pydantic_classes = [
            c for c in result["classes"] if "BaseModel" in c.get("bases", [])
        ]
        assert len(pydantic_classes) > 0

    def test_extracts_function_decorators(self):
        """Function decorators are extracted."""
        # Create a temp file with decorators
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
def simple_decorator(func):
    return func

@simple_decorator
def decorated_function():
    pass
""")
            temp_path = f.name

        try:
            result = get_module_structure(temp_path)
            assert "error" not in result
            decorated = [
                f for f in result["functions"] if f["name"] == "decorated_function"
            ]
            assert len(decorated) == 1
            assert len(decorated[0]["decorators"]) > 0
        finally:
            Path(temp_path).unlink()

    def test_extracts_function_return_type(self):
        """Function return type annotations are extracted."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
def typed_function(x: int, y: str) -> bool:
    return True
""")
            temp_path = f.name

        try:
            result = get_module_structure(temp_path)
            assert "error" not in result
            typed = [f for f in result["functions"] if f["name"] == "typed_function"]
            assert len(typed) == 1
            assert typed[0]["returns"] == "bool"
            assert typed[0]["args"] == ["x", "y"]
        finally:
            Path(temp_path).unlink()

    def test_extracts_function_docstring(self):
        """Function docstrings are extracted."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write('''
def documented_function():
    """This is the docstring."""
    pass
''')
            temp_path = f.name

        try:
            result = get_module_structure(temp_path)
            assert "error" not in result
            documented = [
                f for f in result["functions"] if f["name"] == "documented_function"
            ]
            assert len(documented) == 1
            assert documented[0]["docstring"] == "This is the docstring."
        finally:
            Path(temp_path).unlink()
