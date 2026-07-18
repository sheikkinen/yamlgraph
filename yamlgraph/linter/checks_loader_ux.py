"""FR-747 loader-error-UX lint checks.

The pre-run half of the two FR-744 boundary-error cures: `graph lint`
surfaces the defects the runtime raises actionably (AC-03 — the lint
ran clean over the broken prompt in FR-744, a witnessed gap).

- E006: prompt YAML uses a `messages:` role list (top-level key AND
  absent `system:`/`user:` — parsed structure, never text grep; F3).
- E008: tool declares `module:` while `<module>.py` exists next to the
  graph (verified file existence, never speculation; F2).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from yamlgraph.linter.checks import (
    LintIssue,
    get_prompt_path,
    load_graph,
    resolve_prompts_dir,
)
from yamlgraph.utils.prompts import check_messages_contract


def check_prompt_messages_contract(
    graph_path: Path, project_root: Path | None = None
) -> list[LintIssue]:
    """E006: node prompts must not use `messages:` role lists."""
    issues: list[LintIssue] = []
    graph = load_graph(graph_path)

    if project_root is None:
        project_root = graph_path.parent

    prompts_dir = resolve_prompts_dir(graph, graph_path, project_root)

    for node_name, node_config in graph.get("nodes", {}).items():
        prompt_name = node_config.get("prompt")
        if not prompt_name:
            continue
        prompt_path = get_prompt_path(prompt_name, prompts_dir)
        if not prompt_path.exists():
            continue  # check_prompt_files handles missing files (E004).
        with open(prompt_path) as f:
            content = yaml.safe_load(f)
        try:
            check_messages_contract(content, prompt_name)
        except ValueError as e:
            issues.append(
                LintIssue(
                    severity="error",
                    code="E006",
                    message=f"Node '{node_name}': {e}",
                    fix=(
                        f"Rewrite '{prompt_name}' with top-level 'system:' "
                        "and 'user:' keys (see author-prompt skill)."
                    ),
                )
            )

    return issues


def check_tool_module_graph_local(graph_path: Path) -> list[LintIssue]:
    """E008: `module:` pointing at a file that sits next to the graph."""
    issues: list[LintIssue] = []
    graph = load_graph(graph_path)
    graph_dir = graph_path.parent

    for tool_name, tool_config in graph.get("tools", {}).items():
        if not isinstance(tool_config, dict):
            continue
        module = tool_config.get("module")
        if not module:
            continue
        local_file = graph_dir / f"{module}.py"
        if local_file.is_file():
            issues.append(
                LintIssue(
                    severity="error",
                    code="E008",
                    message=(
                        f"Tool '{tool_name}' declares 'module: {module}' but "
                        f"'{module}.py' exists next to the graph — the import "
                        "will resolve from sys.path, not the graph dir"
                    ),
                    fix=(f"Graph-local tools use 'path: {module}.py', not 'module:'."),
                )
            )

    return issues
