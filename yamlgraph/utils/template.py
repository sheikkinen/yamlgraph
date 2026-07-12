"""Template utilities - Variable extraction and validation.

This module provides functions to extract required variables from
prompt templates and validate that all required variables are provided
before execution.

Supports both simple {variable} placeholders and Jinja2 templates.
"""

import logging
import re
from typing import Any

from jinja2 import Environment, meta
from jinja2 import nodes as jinja_nodes

logger = logging.getLogger(__name__)


def extract_variables(template: str) -> set[str]:
    """Extract all variable names required by a template.

    Handles both simple {var} and Jinja2 {{ var }}, {% for x in var %} syntax.
    Uses Jinja2's AST parser for Jinja2 templates to correctly handle edge cases
    like comments, raw blocks, macros, ternary expressions, and set statements.

    Args:
        template: Template string with placeholders

    Returns:
        Set of variable names required by the template

    Examples:
        >>> extract_variables("Hello {name}")
        {'name'}

        >>> extract_variables("{% for item in items %}{{ item }}{% endfor %}")
        {'items'}
    """
    variables: set[str] = set()

    # Check if template uses Jinja2 syntax
    is_jinja = "{{" in template or "{%" in template

    if is_jinja:
        # Use Jinja2 AST for correctness. autoescape stays False: templates
        # render LLM prompt text, never HTML (CONF-377).
        env = Environment()  # noqa: S701  # nosec B701
        ast = env.parse(template)
        variables = meta.find_undeclared_variables(ast)
        # Subtract variables assigned via {% set %} at any nesting depth.
        # find_undeclared_variables misses nested set targets inside for/if blocks.
        set_targets = {
            node.target.name
            for node in ast.find_all(jinja_nodes.Assign)
            if isinstance(node.target, jinja_nodes.Name)
        }
        variables -= set_targets
        # Also extract simple {var} placeholders (mixed syntax support)
        simple_pattern = r"(?<!\{)\{(\w+)\}(?!\})"
        variables.update(re.findall(simple_pattern, template))
    else:
        # Simple {var} format only
        simple_pattern = r"\{(\w+)\}"
        variables = set(re.findall(simple_pattern, template))

    # Remove common non-input variables
    # - state: injected by node_factory
    # - loop: Jinja2 loop context
    # - range: Jinja2 builtin function
    # - self: Jinja2 macro context
    excluded = {"state", "loop", "range", "true", "false", "none", "self"}
    return variables - excluded


def validate_variables(
    template: str,
    provided: dict[str, Any],
    prompt_name: str,
) -> None:
    """Validate that all required template variables are provided.

    Raises ValueError with helpful message listing all missing variables.

    Args:
        template: Template string with placeholders
        provided: Dictionary of provided variable values
        prompt_name: Name of the prompt (for error messages)

    Raises:
        ValueError: If any required variables are missing

    Examples:
        >>> validate_variables("Hello {name}", {"name": "World"}, "greet")
        # No error

        >>> validate_variables("Hello {name}", {}, "greet")
        ValueError: Missing required variable(s) for prompt 'greet': name
    """
    required = extract_variables(template)
    provided_keys = set(provided.keys())
    missing = required - provided_keys

    if missing:
        raise ValueError(
            f"Missing required variable(s) for prompt '{prompt_name}': "
            f"{', '.join(sorted(missing))}"
        )
