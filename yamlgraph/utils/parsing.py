"""Shared parsing utilities.

This module consolidates common parsing functions used across
conditions.py and expressions.py to eliminate code duplication.
"""

from typing import Any


def parse_literal(value_str: str) -> Any:
    """Parse a literal value from expression string.

    Handles:
    - Quoted strings (single or double)
    - Booleans (true/false, case-insensitive)
    - None/null
    - Numbers (int and float)
    - Unquoted strings (returned as-is)

    Args:
        value_str: String representation of value

    Returns:
        Parsed Python value
    """
    value_str = value_str.strip()

    # Handle quoted strings
    if (value_str.startswith('"') and value_str.endswith('"')) or (
        value_str.startswith("'") and value_str.endswith("'")
    ):
        return value_str[1:-1]

    # Handle booleans (case-insensitive)
    if value_str.lower() == "true":
        return True
    if value_str.lower() == "false":
        return False

    # Handle null/none
    if value_str.lower() in ("null", "none"):
        return None

    # Handle numbers
    try:
        if "." in value_str:
            return float(value_str)
        return int(value_str)
    except ValueError:
        pass

    # Return as string
    return value_str
