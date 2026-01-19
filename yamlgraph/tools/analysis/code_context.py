"""Code context tools for reading specific code sections.

Provides targeted reading after structure analysis identifies relevant locations.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def read_lines(file_path: str, start_line: int, end_line: int) -> str | dict:
    """Read specific lines from a file.

    Use this AFTER getting line ranges from structure tools like get_module_structure.

    Args:
        file_path: Path to file
        start_line: Start line (1-indexed, inclusive)
        end_line: End line (1-indexed, inclusive)

    Returns:
        String with the requested lines, or error dict if file not found.
    """
    # Validate line arguments - handle placeholder strings like 'TBD' or '<dynamic>'
    try:
        start_line = int(start_line)
        end_line = int(end_line)
    except (ValueError, TypeError):
        return {
            "error": f"Invalid line numbers: start_line={start_line!r}, end_line={end_line!r}. "
            "Use get_structure first to get actual line numbers."
        }

    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    lines = path.read_text().splitlines(keepends=True)

    # Convert to 0-indexed
    start = max(0, start_line - 1)
    end = min(len(lines), end_line)

    # Handle invalid range
    if start >= end:
        return ""

    return "".join(lines[start:end])


def find_related_tests(symbol_name: str, tests_path: str = "tests") -> list[dict]:
    """Find test functions related to a symbol.

    Searches test files for functions that mention the symbol name.
    Uses simple text matching (case-insensitive) in test function bodies.

    Args:
        symbol_name: Name of symbol to search for (function, class, etc.)
        tests_path: Path to tests directory

    Returns:
        List of test info dicts with file, line, test_name.
    """
    path = Path(tests_path)
    if not path.exists():
        return []

    results = []
    symbol_lower = symbol_name.lower()

    for test_file in sorted(path.rglob("test_*.py")):
        # Skip __pycache__
        if "__pycache__" in str(test_file):
            continue

        try:
            source = test_file.read_text()
            tree = ast.parse(source)
        except SyntaxError:
            logger.warning(f"Skipping {test_file}: syntax error")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                # Get the source of the test function
                try:
                    test_source = ast.unparse(node)
                except Exception:
                    # Fallback: check if symbol appears in function body lines
                    func_lines = source.splitlines()[node.lineno - 1 : node.end_lineno]
                    test_source = "\n".join(func_lines)

                if symbol_lower in test_source.lower():
                    results.append(
                        {
                            "file": str(test_file),
                            "line": node.lineno,
                            "test_name": node.name,
                        }
                    )

    return results


def search_in_file(
    file_path: str, pattern: str, case_sensitive: bool = False
) -> list[dict] | dict:
    """Search for a pattern in a file and return matching lines.

    Use this to verify if a symbol/field exists before suggesting changes.

    Args:
        file_path: Path to file to search
        pattern: Text pattern to search for
        case_sensitive: If True, match case exactly (default: False)

    Returns:
        List of matches with line number and text, or error dict.
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    results = []
    search_pattern = pattern if case_sensitive else pattern.lower()

    for i, line in enumerate(path.read_text().splitlines(), start=1):
        check_line = line if case_sensitive else line.lower()
        if search_pattern in check_line:
            results.append({"line": i, "text": line.strip()})

    return results


def search_codebase(directory: str, query: str, pattern: str = "*.py") -> list[dict]:
    """Search for a pattern across multiple files in a directory.

    Like grep -r, searches recursively for text matches.

    Args:
        directory: Root directory to search
        query: Text pattern to search for (case-insensitive)
        pattern: Glob pattern for files to search (default: *.py)

    Returns:
        List of file results, each with file path and list of matches.
    """
    path = Path(directory)
    if not path.exists():
        return []

    results = []
    search_text = query.lower()

    for file_path in sorted(path.rglob(pattern)):
        # Skip __pycache__ and other hidden dirs
        if "__pycache__" in str(file_path) or "/.git/" in str(file_path):
            continue

        if not file_path.is_file():
            continue

        try:
            content = file_path.read_text()
        except (OSError, UnicodeDecodeError):
            continue

        matches = []
        for i, line in enumerate(content.splitlines(), start=1):
            if search_text in line.lower():
                matches.append({"line": i, "text": line.strip()})

        if matches:
            results.append({"file": str(file_path), "matches": matches})

    return results
