"""Jedi-based code analysis tools for cross-file reference tracking.

Provides semantic analysis capabilities using jedi:
- find_references: All usages of a symbol across project
- get_callers: Functions that call a given function
- get_callees: Functions called by a given function

Requires: pip install jedi (optional dependency)
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import jedi - graceful degradation if not available
try:
    import jedi

    JEDI_AVAILABLE = True
except ImportError:
    jedi = None  # type: ignore[assignment]
    JEDI_AVAILABLE = False


def find_references(
    file_path: str,
    symbol_name: str,
    line: int,
    column: int = 0,
    project_path: str | None = None,
) -> list[dict] | dict:
    """Find all references to a symbol across the project.

    Args:
        file_path: Path to file containing the symbol definition
        symbol_name: Name of the symbol to find references for
        line: Line number where symbol is defined (1-indexed)
        column: Column offset (default: 0)
        project_path: Root directory for cross-file analysis

    Returns:
        List of reference dicts with file, line, column, type.
        Or error dict if file not found or jedi unavailable.
    """
    # Validate line argument - handle placeholder strings like 'TBD' or '<dynamic>'
    try:
        line = int(line)
    except (ValueError, TypeError):
        return {
            "error": f"Invalid line number: {line!r}. "
            "Use get_structure first to get actual line numbers."
        }

    if line <= 0:
        return {
            "error": f"Invalid line number: {line}. "
            "Line numbers must be >= 1. Use get_structure first."
        }

    if not JEDI_AVAILABLE:
        return {"error": "jedi not installed. Run: pip install jedi"}

    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    try:
        source = path.read_text()

        # Create jedi project for cross-file analysis
        project = None
        if project_path:
            project = jedi.Project(path=project_path)

        script = jedi.Script(source, path=path, project=project)

        # Find the position of the symbol on the given line
        # Try to find the symbol in the line to get correct column
        lines = source.splitlines()
        if 0 < line <= len(lines):
            line_text = lines[line - 1]
            if symbol_name in line_text:
                column = line_text.find(symbol_name)

        # Get references
        references = script.get_references(line=line, column=column)

        results = []
        for ref in references:
            ref_type = "usage"
            if ref.is_definition():
                ref_type = "definition"

            results.append(
                {
                    "file": str(ref.module_path) if ref.module_path else file_path,
                    "line": ref.line,
                    "column": ref.column,
                    "type": ref_type,
                    "name": ref.name,
                }
            )

        return results

    except Exception as e:
        logger.warning(f"jedi analysis failed: {e}")
        return {"error": str(e)}


def get_callers(
    file_path: str,
    function_name: str,
    line: int,
    project_path: str | None = None,
) -> list[dict] | dict:
    """Find all functions that call a given function.

    Args:
        file_path: Path to file containing the function
        function_name: Name of the function to find callers for
        line: Line number where function is defined (1-indexed)
        project_path: Root directory for cross-file analysis

    Returns:
        List of caller dicts with file, line, caller name.
        Or error dict if file not found.
    """
    # Validate line argument - handle placeholder strings like 'TBD' or '<dynamic>'
    try:
        line = int(line)
    except (ValueError, TypeError):
        return {
            "error": f"Invalid line number: {line!r}. "
            "Use get_structure first to get actual line numbers."
        }

    if line <= 0:
        return {
            "error": f"Invalid line number: {line}. "
            "Line numbers must be >= 1. Use get_structure first."
        }

    if not JEDI_AVAILABLE:
        return {"error": "jedi not installed. Run: pip install jedi"}

    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    try:
        # Get all references to the function
        refs = find_references(
            file_path, function_name, line, project_path=project_path
        )

        if isinstance(refs, dict) and "error" in refs:
            return refs

        # Filter to only usages (not definitions)
        callers = []
        for ref in refs:
            if ref.get("type") == "usage":
                # Try to find which function contains this call
                caller_info = _find_enclosing_function(
                    ref.get("file", file_path),
                    ref.get("line", 0),
                )
                if caller_info:
                    callers.append(
                        {
                            "file": ref.get("file"),
                            "line": ref.get("line"),
                            "caller": caller_info.get("name"),
                            "caller_line": caller_info.get("line"),
                        }
                    )

        return callers

    except Exception as e:
        logger.warning(f"get_callers failed: {e}")
        return {"error": str(e)}


def get_callees(
    file_path: str,
    function_name: str,
    line: int,
    project_path: str | None = None,
) -> list[dict] | dict:
    """Find all functions called by a given function.

    Args:
        file_path: Path to file containing the function
        function_name: Name of the function to analyze
        line: Line number where function is defined (1-indexed)
        project_path: Root directory for cross-file analysis

    Returns:
        List of callee dicts with name, line, file.
        Or error dict if file not found.
    """
    # Validate line argument - handle placeholder strings like 'TBD' or '<dynamic>'
    try:
        line = int(line)
    except (ValueError, TypeError):
        return {
            "error": f"Invalid line number: {line!r}. "
            "Use get_structure first to get actual line numbers."
        }

    if line <= 0:
        return {
            "error": f"Invalid line number: {line}. "
            "Line numbers must be >= 1. Use get_structure first."
        }

    if not JEDI_AVAILABLE:
        return {"error": "jedi not installed. Run: pip install jedi"}

    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    try:
        source = path.read_text()
        tree = ast.parse(source)

        # Find the function AST node
        func_node = None
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name == function_name
                and (
                    node.lineno == line
                    or node.lineno <= line <= (node.end_lineno or line)
                )
            ):
                func_node = node
                break

        if not func_node:
            return []

        # Find all function calls within the function body
        callees = []
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                callee_name = None
                if isinstance(node.func, ast.Name):
                    callee_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    callee_name = node.func.attr

                if callee_name:
                    callees.append(
                        {
                            "callee": callee_name,
                            "line": node.lineno,
                            "file": str(path),
                        }
                    )

        return callees

    except Exception as e:
        logger.warning(f"get_callees failed: {e}")
        return {"error": str(e)}


def _find_enclosing_function(file_path: str, line: int) -> dict | None:
    """Find the function that contains a given line.

    Args:
        file_path: Path to file
        line: Line number to find enclosing function for

    Returns:
        Dict with function name and line, or None if not found.
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return None

        source = path.read_text()
        tree = ast.parse(source)

        # Find the innermost function containing this line
        best_match = None
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.FunctionDef)
                and node.lineno <= line <= (node.end_lineno or line)
                and (best_match is None or node.lineno > best_match.lineno)
            ):
                best_match = node

        if best_match:
            return {"name": best_match.name, "line": best_match.lineno}

        return None

    except Exception:
        return None
