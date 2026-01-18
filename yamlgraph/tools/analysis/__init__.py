"""Code analysis tools for impl-agent.

This subpackage provides static and semantic analysis capabilities:
- AST-based structure extraction
- Code context reading and search
- Code navigation and module discovery
- Jedi-based cross-file reference tracking (optional)
"""

from yamlgraph.tools.analysis.ast_analysis import get_module_structure
from yamlgraph.tools.analysis.code_context import (
    find_related_tests,
    read_lines,
    search_codebase,
    search_in_file,
)
from yamlgraph.tools.analysis.code_nav import list_package_modules
from yamlgraph.tools.analysis.git_tools import git_blame, git_log
from yamlgraph.tools.analysis.jedi_analysis import (
    JEDI_AVAILABLE,
    find_references,
    get_callees,
    get_callers,
)
from yamlgraph.tools.analysis.syntax_tools import syntax_check

__all__ = [
    # AST analysis
    "get_module_structure",
    # Code context
    "read_lines",
    "search_in_file",
    "search_codebase",
    "find_related_tests",
    # Code navigation
    "list_package_modules",
    # Jedi analysis
    "JEDI_AVAILABLE",
    "find_references",
    "get_callers",
    "get_callees",
    # Git analysis
    "git_blame",
    "git_log",
    # Syntax validation
    "syntax_check",
]
