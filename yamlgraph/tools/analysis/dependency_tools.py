"""Dependency analysis tools for implementation agent.

Provides import analysis and reverse dependency tracking.
"""

import ast
import subprocess
from pathlib import Path


def get_imports(file_path: str) -> dict:
    """Extract all imports from a Python file.

    Args:
        file_path: Path to the Python file

    Returns:
        dict with 'imports' list, each containing:
        - module: The imported module name
        - names: List of imported names (None for 'import X')
        - alias: Alias if 'as' was used (optional)
        or dict with error key if failed
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    try:
        source = path.read_text()
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"Syntax error in {file_path}: {e}"}

    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            # import X, Y, Z
            for alias in node.names:
                imports.append(
                    {
                        "module": alias.name,
                        "names": None,
                        "alias": alias.asname,
                    }
                )
        elif isinstance(node, ast.ImportFrom):
            # from X import Y, Z
            module = node.module or ""
            names = []
            for alias in node.names:
                name_info = {"name": alias.name}
                if alias.asname:
                    name_info["alias"] = alias.asname
                names.append(name_info)
            imports.append(
                {
                    "module": module,
                    "names": names,
                    "level": node.level,  # Relative import level (0 = absolute)
                }
            )

    return {"imports": imports}


def get_dependents(module_path: str, project_path: str) -> dict:
    """Find all files that import a given module.

    Args:
        module_path: Module path to search for (e.g., 'yamlgraph.executor')
        project_path: Root path of the project to search in

    Returns:
        dict with 'dependents' list of file paths that import the module
        or dict with error key if failed
    """
    path = Path(project_path)
    if not path.exists():
        return {"error": f"Project path not found: {project_path}"}

    # Convert module path to patterns for grep
    # e.g., 'yamlgraph.executor' -> search for 'from yamlgraph.executor' or 'import yamlgraph.executor'
    full_module = module_path

    # Build grep patterns
    patterns = [
        f"from {full_module} import",
        f"from {full_module}\\b",
        f"import {full_module}\\b",
    ]

    # For single-word modules like 'logging', also search simpler patterns
    if "." not in module_path:
        patterns = [
            f"import {module_path}\\b",
            f"from {module_path} import",
        ]

    dependents = set()

    for pattern in patterns:
        try:
            result = subprocess.run(
                ["grep", "-rl", "-E", pattern, "--include=*.py", str(path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # grep returns 1 if no matches (not an error)
            if result.returncode == 0 and result.stdout.strip():
                for file_path in result.stdout.strip().split("\n"):
                    if file_path.strip():
                        dependents.add(file_path.strip())
        except subprocess.TimeoutExpired:
            return {"error": "Search timed out"}
        except Exception as e:
            return {"error": str(e)}

    return {"dependents": sorted(dependents)}
