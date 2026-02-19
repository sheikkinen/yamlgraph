#!/usr/bin/env python3
"""Lint check for inline LLM calls bypassing graph execution (FR-047).

Detects scripts with def main() that import LLM execution functions
but NOT graph loading — the code smell of bypassing YAMLGraph's
three-layer architecture.

Usage:
    python scripts/lint_inline_llm.py [--verbose]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# LLM execution imports that indicate orchestration
LLM_IMPORTS = {
    "execute_prompt",
    "execute_prompt_streaming",
    "ChatAnthropic",
    "ChatOpenAI",
    "ChatMistral",
    "create_llm",
}

# Module-level imports that indicate direct LLM provider usage
LLM_MODULES = {
    "langchain_anthropic",
    "langchain_openai",
    "langchain_mistral",
}

# Graph loader imports that make LLM imports acceptable
GRAPH_IMPORTS = {
    "load_graph_config",
    "compile_graph",
    "load_and_compile",
}

# Paths to exclude from scanning
EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "htmlcov",
    ".mypy_cache",
    ".ruff_cache",
}

# Paths to exclude (demos showing low-level API are acceptable)
EXCLUDE_PATHS = {
    "examples/demos/",  # Demos show low-level API usage
    "spike_",  # Research spikes are temporary inline code
}

MAIN_PATTERN = re.compile(r"^\s*(async\s+)?def\s+main\s*\(", re.MULTILINE)
IMPORT_PATTERN = re.compile(r"^(?:from\s+[\w.]+\s+)?import\s+.+$", re.MULTILINE)


def extract_imports(content: str) -> set[str]:
    """Extract imported names from Python source."""
    imports = set()
    for match in IMPORT_PATTERN.finditer(content):
        line = match.group(0)
        # Handle: from x import a, b, c
        if "import" in line:
            # Get everything after 'import'
            after_import = line.split("import", 1)[1]
            # Remove comments
            after_import = after_import.split("#")[0]
            # Split by comma and clean
            for name in after_import.split(","):
                name = name.strip()
                # Handle 'as' aliases: import x as y
                if " as " in name:
                    name = name.split(" as ")[0].strip()
                # Handle parentheses
                name = name.strip("() ")
                if name:
                    imports.add(name)
        # Also add the module name for 'from x import'
        if line.startswith("from "):
            module = line.split("from ", 1)[1].split(" import")[0].strip()
            imports.add(module)
    return imports


def check_file(filepath: Path) -> str | None:
    """Check a single file for inline LLM calls.

    Returns:
        Error message if violation found, None if OK or skipped.
    """
    try:
        content = filepath.read_text()
    except (OSError, UnicodeDecodeError):
        return None

    # Skip files without main()
    if not MAIN_PATTERN.search(content):
        return None

    # Extract actual imports
    imports = extract_imports(content)

    # Check for LLM imports
    found_llm = [imp for imp in LLM_IMPORTS if imp in imports]

    # Check for LLM module imports
    found_llm_modules = [
        mod for mod in LLM_MODULES if any(mod in imp for imp in imports)
    ]

    all_llm_found = found_llm + found_llm_modules
    if not all_llm_found:
        return None  # No LLM imports, OK

    # Check for graph loader imports
    found_graph = any(imp in imports for imp in GRAPH_IMPORTS)
    if found_graph:
        return None  # Has graph loader, OK

    # Violation: LLM imports without graph loader
    return f"Inline LLM imports without graph loader: {', '.join(all_llm_found)}"


def scan_directory(root: Path, verbose: bool = False) -> list[tuple[Path, str]]:
    """Scan directory for inline LLM violations.

    Returns:
        List of (filepath, error_message) tuples for violations.
    """
    violations: list[tuple[Path, str]] = []

    for filepath in root.rglob("*.py"):
        # Skip excluded directories
        if any(excl in filepath.parts for excl in EXCLUDE_DIRS):
            continue

        # Skip excluded paths
        rel_path = (
            str(filepath.relative_to(root))
            if root in filepath.parents or filepath.parent == root
            else str(filepath)
        )
        if any(excl in rel_path for excl in EXCLUDE_PATHS):
            if verbose:
                print(f"  ⊘ {rel_path} (excluded)")
            continue

        result = check_file(filepath)
        if result:
            violations.append((filepath, result))
        elif verbose:
            print(f"  ✓ {rel_path}")

    return violations


def main() -> int:
    """Run inline LLM lint check."""
    parser = argparse.ArgumentParser(
        description="Check for inline LLM calls bypassing graph execution"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show all scanned files"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory to scan (default: current)",
    )
    args = parser.parse_args()

    root = Path(args.path).resolve()
    print(f"🔍 Scanning {root} for inline LLM calls...")

    violations = scan_directory(root, verbose=args.verbose)

    if violations:
        print(f"\n❌ Found {len(violations)} violation(s):\n")
        for filepath, error in violations:
            rel = (
                filepath.relative_to(root)
                if root in filepath.parents or filepath.parent == root
                else filepath
            )
            print(f"  {rel}")
            print(f"    → {error}")
        print("\n💡 Fix: Move LLM orchestration to a YAML graph and use")
        print("   load_graph_config/compile_graph in the script.")
        return 1

    print("✅ No inline LLM violations found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
