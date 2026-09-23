"""Template utilities - Variable extraction and validation.

This module provides functions to extract required variables from
prompt templates and validate that all required variables are provided
before execution.

Supports both simple {variable} placeholders and Jinja2 templates.
"""

import logging
import re
import string
from dataclasses import dataclass
from typing import Any

from jinja2 import Environment, meta
from jinja2 import nodes as jinja_nodes

logger = logging.getLogger(__name__)

# Injected by the framework or supplied by Jinja itself, never by the caller.
_EXCLUDED_VARIABLES = {"state", "loop", "range", "true", "false", "none", "self"}

# The format-spec mini-language, transcribed from its own definition:
# [[fill]align][sign][z][#][0][width][grouping][.precision][type]
_FORMAT_SPEC = re.compile(
    r"^(?:.?[<>=^])?[-+ ]?z?#?0?\d*[,_]?(?:\.\d+)?[bcdeEfFgGnosxX%]?$"
)
_CONVERSIONS = frozenset("rsa")


def _is_substitution(spec: str | None, conversion: str | None) -> bool:
    """Does this field look like a substitution rather than prose?

    `{score:.2f}` and `{name!r}` do. `{pred: alive, args: []}` is an author
    documenting an output shape; its tail is not a format spec, and that —
    not the mere presence of a `:` — is what says so.

    A guess, and deliberately only used where guessing is safe. Python hands
    the format spec to the value's own `__format__`, so `{when:%Y-%m-%d}` is
    valid for a `datetime` and this function will still say no. Ask it only
    on the Jinja side, where a stray `{x}` renders as literal text and a
    wrong answer costs an advisory warning. The `str.format` side must use
    `roots`: there a wrong answer is a `KeyError` at render time.
    """
    if conversion is not None and conversion not in _CONVERSIONS:
        return False
    if not spec or "{" in spec:  # nested field width/precision
        return True
    return _FORMAT_SPEC.match(spec) is not None


def is_jinja(text: str) -> bool:
    """Decide which engine renders one message (FR-1057).

    The single source of truth. Every layer — rendering, validation, and the
    linter — must ask this question about the same unit of text: one message.
    """
    return "{{" in text or "{%" in text


@dataclass(frozen=True)
class SimpleFieldScan:
    """What `str.format` would make of a piece of text.

    Attributes:
        roots: Root identifiers of every well-formed field. This is the set a
            `str.format` message is validated against, because this is the
            set `str.format` itself will look up: a format spec is passed to
            the value's `__format__` and cannot be used to rule a field out.
        substitution_roots: `roots` minus the fields whose tail is not a
            format spec at all — the `{pred: alive, args: []}` an author
            writes to document an output shape. A heuristic, safe only where
            a wrong answer is advisory: the Jinja side, where such a field
            renders as literal text rather than raising.
        invalid_fields: Fields whose root is not an identifier, such as the
            `"chapters"` that `{"chapters": []}` parses into.
        brace_error: The formatter's own complaint about unbalanced braces,
            or None.
    """

    roots: set[str]
    substitution_roots: set[str]
    invalid_fields: tuple[str, ...]
    brace_error: str | None


def _field_root(field_name: str) -> str:
    """Strip the attribute/index tail `str.format` resolves after lookup."""
    for index, char in enumerate(field_name):
        if char in ".[":
            return field_name[:index]
    return field_name


def strip_jinja_raw_blocks(text: str) -> str:
    """Remove `{% raw %}...{% endraw %}` spans from a Jinja template.

    A raw block is the author declaring that the braces inside are literal
    output. Scanning it for substitutions would report the escape itself as
    the defect — the remedy E013 recommends.
    """
    return re.sub(
        r"\{%-?\s*raw\s*-?%\}.*?\{%-?\s*endraw\s*-?%\}",
        "",
        text,
        flags=re.DOTALL,
    )


def scan_simple_fields(text: str) -> SimpleFieldScan:
    """Read `text` with Python's own format-string parser (FR-1057).

    Uses `string.Formatter.parse` rather than a brace regex: the regex and the
    real field grammar disagreeing is defect D2 itself, so the checks built on
    this must inherit the grammar they are policing instead of approximating
    it. Never raises — an unbalanced brace is reported, not thrown.
    """
    formatter = string.Formatter()
    roots: set[str] = set()
    substitution_roots: set[str] = set()
    invalid: set[str] = set()
    brace_error: str | None = None
    remaining = text

    while remaining:
        try:
            for _literal, field_name, spec, conversion in formatter.parse(remaining):
                if field_name is None:
                    continue
                root = _field_root(field_name)
                if not root.isidentifier():
                    invalid.add(field_name)
                    continue
                roots.add(root)
                if _is_substitution(spec, conversion):
                    substitution_roots.add(root)
                if spec and "{" in spec:
                    # A nested width/precision is a required variable too:
                    # `{value:{width}}` cannot render without `width`.
                    nested = scan_simple_fields(spec)
                    roots |= nested.roots
                    substitution_roots |= nested.substitution_roots
            break
        except ValueError as exc:
            if brace_error is None:
                brace_error = str(exc)
            # Restart the formatter's own parser past the offending brace. The
            # alternative — recovering by hand — would mean inventing a second
            # grammar, which is the defect this function exists to close.
            offsets = [
                pos for pos in (remaining.find("{"), remaining.find("}")) if pos >= 0
            ]
            if not offsets:
                break
            remaining = remaining[min(offsets) + 1 :]

    return SimpleFieldScan(
        roots=roots,
        substitution_roots=substitution_roots,
        invalid_fields=tuple(sorted(invalid)),
        brace_error=brace_error,
    )


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

    if is_jinja(template):
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
        # Simple {var} fields survive Jinja rendering untouched; they are still
        # declared inputs until E014 removes them. Raw blocks are literal.
        variables.update(
            scan_simple_fields(strip_jinja_raw_blocks(template)).substitution_roots
        )
    else:
        # Every field, documentation-looking or not: `str.format` will try to
        # resolve it, so validation must require it.
        variables = scan_simple_fields(template).roots

    return variables - _EXCLUDED_VARIABLES


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
