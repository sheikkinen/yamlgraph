"""FR-337 context assembler for watcher-enforce pre-node."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from pydantic import BaseModel, Field

CONTEXT_BUDGET_CHARS = 12_000
SOURCE_SNIPPET_CHARS = 1_200
DOC_SNIPPET_CHARS = 1_200

MODULE_MAP_PATH = "reference/module-map.md"


def load_module_map(state: dict) -> dict:
    """Read the static module map into state for the context planner prompt."""
    repo_root = Path(state.get("worktree_dir") or ".").resolve()
    map_path = repo_root / MODULE_MAP_PATH
    if not map_path.exists():
        return {"module_map": "(module map not found)"}
    return {"module_map": map_path.read_text(encoding="utf-8")}


class ContextPlan(BaseModel):
    """Validated planner output for context assembly."""

    source_files: list[str] = Field(default_factory=list)
    test_files: list[str] = Field(default_factory=list)
    doc_sections: list[str] = Field(default_factory=list)
    key_symbols: list[str] = Field(default_factory=list)
    rationale: str = ""


def _extract_json_object(text: str) -> dict:
    """Extract and decode the outermost JSON object from arbitrary text."""
    stripped = re.sub(r"```(?:json)?\s*\n?", "", text).strip()
    if stripped.endswith("```"):
        stripped = stripped[:-3].strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("Context plan output does not contain a JSON object")

    return json.loads(stripped[start : end + 1])


def _coerce_context_plan(raw_plan: object) -> ContextPlan:
    """Normalize plan payloads into a validated ContextPlan model."""
    if isinstance(raw_plan, ContextPlan):
        return raw_plan

    if hasattr(raw_plan, "model_dump"):
        raw_plan = raw_plan.model_dump()

    if isinstance(raw_plan, dict):
        return ContextPlan.model_validate(raw_plan)

    if isinstance(raw_plan, str):
        return ContextPlan.model_validate(_extract_json_object(raw_plan))

    output = getattr(raw_plan, "output", None)
    if isinstance(output, str):
        return ContextPlan.model_validate(_extract_json_object(output))

    raise ValueError(f"Unsupported context plan payload type: {type(raw_plan)!r}")


def _resolve_repo_file(repo_root: Path, relative_path: str) -> Path:
    """Resolve and validate a relative file path within repository root."""
    cleaned = relative_path.split("#", maxsplit=1)[0].strip()
    if not cleaned:
        raise ValueError("Empty context path is not allowed")

    candidate = (repo_root / cleaned).resolve()
    try:
        candidate.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"Path escapes repository root: {relative_path}") from exc

    if not candidate.exists() or not candidate.is_file():
        raise ValueError(f"Context file does not exist: {cleaned}")
    return candidate


def _read_snippet(path: Path, max_chars: int) -> str:
    return path.read_text(encoding="utf-8")[:max_chars]


def _extract_source_signatures(path: Path) -> list[str]:
    """Extract top-level class/function signatures using ast.parse()."""
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    signatures: list[str] = []
    for node in module.body:
        if isinstance(node, ast.ClassDef):
            signatures.append(f"class {node.name}")
        elif isinstance(node, ast.AsyncFunctionDef):
            signatures.append(f"async def {node.name}()")
        elif isinstance(node, ast.FunctionDef):
            signatures.append(f"def {node.name}()")
    return signatures


def _extract_test_names(path: Path) -> list[str]:
    """Extract test function names using ast.parse()."""
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    test_names: list[str] = []
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            test_names.append(node.name)
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name.startswith(
                    "test_"
                ):
                    test_names.append(f"{node.name}.{child.name}")
    return test_names


def _fr_slug(fr_path: str) -> str:
    """Convert feature request path to docs/context/<fr-id>.md slug."""
    match = re.search(r"(FR-\d+)", Path(fr_path).name, re.IGNORECASE)
    return match.group(1).lower().replace("-", "-") if match else "fr-unknown"


def _enforce_budget(text: str, budget: int = CONTEXT_BUDGET_CHARS) -> str:
    """Bound assembled context size to a deterministic budget."""
    if len(text) <= budget:
        return text
    truncated = text[:budget].rstrip()
    return f"{truncated}\n\n[context truncated to budget={budget} chars]"


def assemble_context(state: dict) -> dict:
    """Assemble bounded codebase context and write docs/context/<fr-id>.md artifact."""
    if "context_plan" not in state:
        raise ValueError("State is missing required key: context_plan")
    if "fr_path" not in state:
        raise ValueError("State is missing required key: fr_path")

    repo_root = Path(state.get("worktree_dir") or ".").resolve()
    plan = _coerce_context_plan(state["context_plan"])

    sections: list[str] = [f"# Context Plan for {state['fr_path']}", ""]
    sections.append("## Planner Rationale")
    sections.append(plan.rationale or "No rationale provided.")

    if plan.key_symbols:
        sections.append("")
        sections.append("## Key Symbols")
        sections.extend([f"- {symbol}" for symbol in plan.key_symbols])

    for source in plan.source_files:
        try:
            source_path = _resolve_repo_file(repo_root, source)
        except ValueError:
            sections.append(f"\n## Source: {source} (not found, skipped)")
            continue
        signatures = _extract_source_signatures(source_path)
        sections.append("")
        sections.append(f"## Source: {source}")
        sections.append("### Signatures")
        sections.extend(
            [f"- {signature}" for signature in signatures] or ["- (none found)"]
        )
        sections.append("### Snippet")
        sections.append("```python")
        sections.append(_read_snippet(source_path, SOURCE_SNIPPET_CHARS))
        sections.append("```")

    for test_file in plan.test_files:
        try:
            test_path = _resolve_repo_file(repo_root, test_file)
        except ValueError:
            sections.append(f"\n## Tests: {test_file} (not found, skipped)")
            continue
        test_names = _extract_test_names(test_path)
        sections.append("")
        sections.append(f"## Tests: {test_file}")
        sections.append("### Test Functions")
        sections.extend([f"- {name}" for name in test_names] or ["- (none found)"])

    for doc_ref in plan.doc_sections:
        try:
            doc_path = _resolve_repo_file(repo_root, doc_ref)
        except ValueError:
            sections.append(f"\n## Docs: {doc_ref} (not found, skipped)")
            continue
        sections.append("")
        sections.append(f"## Docs: {doc_ref}")
        sections.append("```markdown")
        sections.append(_read_snippet(doc_path, DOC_SNIPPET_CHARS))
        sections.append("```")

    assembled_context = _enforce_budget("\n".join(sections), CONTEXT_BUDGET_CHARS)

    artifact_dir = repo_root / "docs" / "context"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / f"{_fr_slug(state['fr_path'])}.md"
    artifact_path.write_text(assembled_context, encoding="utf-8")

    return {
        "assembled_context": assembled_context,
        "context_artifact_path": str(artifact_path.relative_to(repo_root)),
    }
