"""Output-schema constrainability checks (FR-1123 E016/W028, FR-1125 E017/W029).

Extracted from ``checks_prompts.py`` (FR-1125 R-5). One check, two finding
kinds, on every ``llm``/``router`` node whose provider is statically Anthropic
(error) or chosen at run time (warning); a known non-Anthropic provider is
silent. The walker and the provider resolution live in
``yamlgraph.utils.schema_walk`` so compile, bind and lint agree.
"""

from __future__ import annotations

from pathlib import Path

from yamlgraph.linter.checks import (
    LintIssue,
    get_prompt_path,
    load_graph,
    resolve_prompts_dir,
)
from yamlgraph.utils.schema_walk import (
    SchemaFinding,
    find_unconstrainable,
    node_subject,
    refusal_message,
    resolve_static_provider,
)

_CODES: dict[str, tuple[str, str]] = {
    # kind -> (static Anthropic error code, run-time provider warning code)
    "untyped": ("E016", "W028"),
    "open_object": ("E017", "W029"),
}
_FIXES: dict[str, str] = {
    "untyped": "Declare a concrete type (e.g. list[str]) or a nested schema with declared properties.",
    "open_object": (
        "Declare the object's properties with the output_schema form "
        "(items: {type: object, properties: {...}}), or run the node on a "
        "provider that accepts open objects."
    ),
}


def check_unconstrainable_schemas(
    graph_path: Path, project_root: Path | None = None
) -> list[LintIssue]:
    """E016/W028 untyped and E017/W029 open-object paths on Anthropic-bound nodes."""
    from yamlgraph.schema_loader import load_schema_from_yaml

    graph = load_graph(graph_path)
    prompts_dir = resolve_prompts_dir(
        graph, graph_path, project_root or graph_path.parent
    )
    default_provider = (graph.get("defaults") or {}).get("provider")
    issues: list[LintIssue] = []
    for node_name, node in graph.get("nodes", {}).items():
        if node.get("type", "llm") not in ("llm", "router") or node.get("parse_json"):
            continue
        prompt_name = node.get("prompt")
        prompt_path = get_prompt_path(prompt_name, prompts_dir) if prompt_name else None
        if prompt_path is None or not prompt_path.exists():
            continue
        provider = resolve_static_provider(node.get("provider"), default_provider)
        if provider not in ("anthropic", None):
            continue
        model = load_schema_from_yaml(prompt_path)
        findings = find_unconstrainable(model.model_json_schema()) if model else []
        subject = node_subject(node_name, prompt_name, node.get("model"))
        for finding in findings:
            issues.append(_issue(subject, finding, static=provider is not None))
    return issues


def _issue(subject: str, finding: SchemaFinding, *, static: bool) -> LintIssue:
    message = refusal_message(subject, [finding])
    if not static:
        message += " (provider is chosen at run time; Anthropic would reject it)"
    error_code, warning_code = _CODES[finding.kind]
    return LintIssue(
        severity="error" if static else "warning",
        code=error_code if static else warning_code,
        message=message,
        fix=_FIXES[finding.kind],
    )


__all__ = ["check_unconstrainable_schemas"]
