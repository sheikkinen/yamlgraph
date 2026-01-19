"""Code navigation tools for finding relevant files.

Provides package-level module discovery and search capabilities.
"""

from __future__ import annotations

import logging
from pathlib import Path

from examples.codegen.tools.ast_analysis import get_module_structure

logger = logging.getLogger(__name__)


def list_package_modules(package_path: str) -> list[dict]:
    """List all Python modules in a package with high-level summaries.

    Args:
        package_path: Path to package directory

    Returns:
        List of module summaries with file, docstring, classes, functions.
        Returns empty list if path doesn't exist or has no Python files.
    """
    path = Path(package_path)
    if not path.exists():
        return []

    results = []
    for py_file in sorted(path.rglob("*.py")):
        # Skip __pycache__ directories
        if "__pycache__" in str(py_file):
            continue

        structure = get_module_structure(str(py_file))

        # Skip files with errors (syntax errors, etc.)
        if "error" in structure:
            logger.warning(f"Skipping {py_file}: {structure['error']}")
            continue

        results.append(
            {
                "file": str(py_file),
                "docstring": structure.get("docstring"),
                "classes": [c["name"] for c in structure.get("classes", [])],
                "functions": [f["name"] for f in structure.get("functions", [])],
            }
        )

    return results
