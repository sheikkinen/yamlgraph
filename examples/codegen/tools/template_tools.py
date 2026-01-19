"""Template extraction tools for implementation agent.

Extract reusable templates from existing code for consistent new code generation.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def extract_function_template(file_path: str, function_name: str) -> dict:
    """Extract reusable function template.

    Args:
        file_path: Path to the Python file
        function_name: Name of the function to extract

    Returns:
        dict with 'template' string showing reusable pattern
        or dict with 'error' key if failed
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    try:
        source = path.read_text()
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}

    # Find the function
    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            target = node
            break

    if target is None:
        return {"error": f"Function '{function_name}' not found in {file_path}"}

    # Extract template
    lines = source.splitlines()
    template_parts = []

    # Build signature line
    sig = _build_signature(target)
    template_parts.append(sig)

    # Extract docstring
    docstring = ast.get_docstring(target)
    if docstring:
        template_parts.append(f'    """{docstring}"""')

    # Extract body structure
    body_template = _extract_body_structure(target, lines)
    template_parts.append(body_template)

    return {"template": "\n".join(template_parts)}


def _build_signature(func: ast.FunctionDef) -> str:
    """Build function signature with type hints."""
    args = []
    for arg in func.args.args:
        if arg.annotation:
            ann = _get_annotation(arg.annotation)
            args.append(f"{arg.arg}: {ann}")
        else:
            args.append(arg.arg)

    # Handle defaults
    defaults = func.args.defaults
    num_defaults = len(defaults)
    if num_defaults > 0:
        for i, default in enumerate(defaults):
            idx = len(args) - num_defaults + i
            default_val = _get_value(default)
            args[idx] = f"{args[idx]} = {default_val}"

    ret = ""
    if func.returns:
        ret = f" -> {_get_annotation(func.returns)}"

    return f"def {func.name}({', '.join(args)}){ret}:"


def _get_annotation(node: ast.expr) -> str:
    """Extract type annotation as string."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Constant):
        return repr(node.value)
    elif isinstance(node, ast.Subscript):
        value = _get_annotation(node.value)
        slice_val = _get_annotation(node.slice)
        return f"{value}[{slice_val}]"
    elif isinstance(node, ast.Attribute):
        return f"{_get_annotation(node.value)}.{node.attr}"
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left = _get_annotation(node.left)
        right = _get_annotation(node.right)
        return f"{left} | {right}"
    return "..."


def _get_value(node: ast.expr) -> str:
    """Extract default value as string."""
    if isinstance(node, ast.Constant):
        return repr(node.value)
    elif isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.List):
        return "[]"
    elif isinstance(node, ast.Dict):
        return "{}"
    return "..."


def _extract_body_structure(func: ast.FunctionDef, lines: list[str]) -> str:
    """Extract body structure as template."""
    body_parts = []

    for node in func.body:
        # Skip docstring
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue

        if isinstance(node, ast.Try):
            body_parts.append("    try:")
            body_parts.append("        {try_block}")
            for handler in node.handlers:
                exc = _get_annotation(handler.type) if handler.type else "Exception"
                body_parts.append(f"    except {exc}:")
                body_parts.append("        {except_block}")
        elif isinstance(node, ast.If):
            body_parts.append("    if {condition}:")
            body_parts.append("        {if_block}")
        elif isinstance(node, ast.For):
            body_parts.append("    for {item} in {iterable}:")
            body_parts.append("        {loop_block}")
        elif isinstance(node, ast.Return):
            if node.value:
                ret_val = _format_return(node.value)
                body_parts.append(f"    return {ret_val}")
            else:
                body_parts.append("    return")
        else:
            # Generic statement
            stmt_lines = lines[node.lineno - 1 : node.end_lineno]
            for line in stmt_lines:
                body_parts.append(line)

    if not body_parts:
        body_parts.append("    pass")

    return "\n".join(body_parts)


def _format_return(node: ast.expr) -> str:
    """Format return value for template."""
    if isinstance(node, ast.Dict):
        items = []
        for k, v in zip(node.keys, node.values, strict=False):
            key = _get_value(k) if k else "..."
            val = "{result}" if isinstance(v, ast.Name) else _get_value(v)
            items.append(f"{key}: {val}")
        return "{" + ", ".join(items) + "}"
    elif isinstance(node, ast.Call):
        return "{function_call}"
    return "{result}"


def extract_class_template(file_path: str, class_name: str) -> dict:
    """Extract reusable class template.

    Args:
        file_path: Path to the Python file
        class_name: Name of the class to extract

    Returns:
        dict with 'template' string showing reusable pattern
        or dict with 'error' key if failed
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    try:
        source = path.read_text()
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}

    # Find the class
    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            target = node
            break

    if target is None:
        return {"error": f"Class '{class_name}' not found in {file_path}"}

    template_parts = []

    # Class signature with bases
    bases = [_get_annotation(b) for b in target.bases]
    if bases:
        template_parts.append(f"class {class_name}({', '.join(bases)}):")
    else:
        template_parts.append(f"class {class_name}:")

    # Docstring
    docstring = ast.get_docstring(target)
    if docstring:
        template_parts.append(f'    """{docstring}"""')

    # Class variables
    for node in target.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
            ann = _get_annotation(node.annotation)
            if node.value:
                val = _get_value(node.value)
                template_parts.append(f"    {name}: {ann} = {val}")
            else:
                template_parts.append(f"    {name}: {ann}")

    # Methods (signatures only)
    for node in target.body:
        if isinstance(node, ast.FunctionDef):
            sig = _build_signature(node)
            template_parts.append("")
            template_parts.append(f"    {sig}")
            # Method docstring
            method_doc = ast.get_docstring(node)
            if method_doc:
                short_doc = method_doc.split("\n")[0]
                template_parts.append(f'        """{short_doc}"""')
            template_parts.append("        ...")

    return {"template": "\n".join(template_parts)}


def extract_test_template(test_file: str, target_module: str) -> dict:
    """Extract test patterns for reuse.

    Args:
        test_file: Path to the test file
        target_module: Module being tested

    Returns:
        dict with 'template' string showing test patterns
        or dict with 'error' key if failed
    """
    path = Path(test_file)
    if not path.exists():
        return {"error": f"File not found: {test_file}"}

    try:
        source = path.read_text()
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}

    template_parts = []
    lines = source.splitlines()

    # Find imports
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "pytest":
                    imports.append("import pytest")
        elif isinstance(node, ast.ImportFrom) and node.module and "mock" in node.module:
            names = ", ".join(a.name for a in node.names)
            imports.append(f"from {node.module} import {names}")

    if imports:
        template_parts.extend(imports)
        template_parts.append("")

    # Find fixtures
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Attribute) and decorator.attr == "fixture":
                    template_parts.append("@pytest.fixture")
                    sig = _build_signature(node)
                    template_parts.append(f"{sig}")
                    template_parts.append("    {fixture_implementation}")
                    template_parts.append("")
                elif isinstance(decorator, ast.Name) and "fixture" in decorator.id:
                    template_parts.append(f"@{decorator.id}")
                    sig = _build_signature(node)
                    template_parts.append(f"{sig}")
                    template_parts.append("    {fixture_implementation}")
                    template_parts.append("")

    # Find test classes
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            template_parts.append(f"class {node.name}:")
            docstring = ast.get_docstring(node)
            if docstring:
                template_parts.append(f'    """{docstring}"""')
            template_parts.append("")

            # Extract test method patterns
            for method in node.body:
                if isinstance(method, ast.FunctionDef) and method.name.startswith(
                    "test_"
                ):
                    sig = _build_signature(method)
                    template_parts.append(f"    {sig}")
                    template_parts.append("        {test_implementation}")
                    template_parts.append("")
            break  # Just use first test class as pattern

    # Find standalone test functions with patch
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            # Check for patch usage in body
            func_source = "\n".join(lines[node.lineno - 1 : node.end_lineno])
            if "patch" in func_source:
                template_parts.append("def {test_name}():")
                template_parts.append('    with patch("{module}.{target}") as mock:')
                template_parts.append("        mock.return_value = {mock_value}")
                template_parts.append("        {test_implementation}")
                break

    if not template_parts:
        # Provide minimal template
        template_parts = [
            "import pytest",
            f"from {target_module} import {{symbols}}",
            "",
            "class Test{{ClassName}}:",
            '    """Tests for {{symbol}}."""',
            "",
            "    def test_basic(self):",
            "        {test_implementation}",
        ]

    return {"template": "\n".join(template_parts)}
