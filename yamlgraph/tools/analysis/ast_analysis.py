"""AST-based code analysis tools.

Provides structural analysis of Python files using the stdlib ast module.
Returns classes, functions, imports with line numbers for precise navigation.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_module_structure(file_path: str) -> dict:
    """Extract structure from Python file using AST.

    Args:
        file_path: Path to Python file

    Returns:
        Dict with imports, classes, functions and their line numbers.
        Returns {"error": "..."} on failure.
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    try:
        source = path.read_text()
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}

    return {
        "file": str(path),
        "docstring": ast.get_docstring(tree),
        "imports": _extract_imports(tree),
        "classes": _extract_classes(tree),
        "functions": _extract_functions(tree.body),
    }


def _extract_imports(tree: ast.Module) -> list[dict]:
    """Extract import statements from module."""
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({"module": alias.name, "alias": alias.asname})
        elif isinstance(node, ast.ImportFrom):
            imports.append(
                {
                    "module": node.module,
                    "names": [a.name for a in node.names],
                }
            )
    return imports


def _extract_classes(tree: ast.Module) -> list[dict]:
    """Extract class definitions from module."""
    return [
        {
            "name": node.name,
            "bases": [ast.unparse(b) for b in node.bases],
            "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
            "line": node.lineno,
            "end_line": node.end_lineno,
            "docstring": ast.get_docstring(node),
        }
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    ]


def _extract_functions(body: list) -> list[dict]:
    """Extract function definitions from module body (top-level only)."""
    return [
        {
            "name": node.name,
            "args": [arg.arg for arg in node.args.args],
            "returns": ast.unparse(node.returns) if node.returns else None,
            "decorators": [ast.unparse(d) for d in node.decorator_list],
            "line": node.lineno,
            "end_line": node.end_lineno,
            "docstring": ast.get_docstring(node),
        }
        for node in body
        if isinstance(node, ast.FunctionDef)
    ]
