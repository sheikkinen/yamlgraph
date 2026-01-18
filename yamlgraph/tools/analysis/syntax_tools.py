"""Syntax validation tools for implementation agent.

Provides syntax checking for proposed code changes.
"""

import ast


def syntax_check(code: str) -> dict:
    """Check if Python code is syntactically valid.

    Args:
        code: Python code string to check

    Returns:
        dict with 'valid' boolean. If invalid, includes 'error' string
        with line number and description.
    """
    try:
        ast.parse(code)
        return {"valid": True}
    except SyntaxError as e:
        error_msg = f"line {e.lineno}: {e.msg}"
        if e.text:
            error_msg += f" (near: {e.text.strip()[:50]})"
        return {"valid": False, "error": error_msg}
