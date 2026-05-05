#!/usr/bin/env python3
"""Standalone Anthropic Agent SDK planner spike for FR-329."""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import re
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError

FR_FILENAME_RE = re.compile(r"^FR-(\d+)-.+\.md$")
REQUIRED_TEMPLATE_SECTIONS = (
    "## Summary",
    "## Value Statement",
    "## Problem",
    "## Proposed Solution",
    "## Acceptance Criteria",
    "## Alternatives Considered",
    "## Related",
)
OUTPUT_PATTERN = "feature-requests/FR-{num:03d}-{slug}.md"


class NextFrNumberPayload(BaseModel):
    fr_number: int = Field(ge=1)
    fr_tag: str = Field(pattern=r"^FR-\d{3}$")


class PlannerDraft(BaseModel):
    fr_number: int = Field(ge=1)
    title: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    markdown: str = Field(min_length=1)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def next_fr_number(feature_requests_dir: Path) -> int:
    max_number = 0
    for path in sorted(feature_requests_dir.glob("FR-*.md")):
        match = FR_FILENAME_RE.match(path.name)
        if match is None:
            continue
        number = int(match.group(1))
        if number > max_number:
            max_number = number
    return max_number + 1


def read_fr_template(feature_requests_dir: Path) -> bytes:
    template_path = feature_requests_dir / "TEMPLATE.md"
    if not template_path.exists():
        raise FileNotFoundError(f"FR template not found: {template_path}")
    return template_path.read_bytes()


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "untitled"


def summarize_topic(topic_text: str) -> str:
    for raw_line in topic_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            line = line.lstrip("#").strip()
        if line:
            return line[:240]
    return "Standalone planner spike requested from topic input."


def ensure_draft_status(markdown: str) -> str:
    if "**Status:**" in markdown:
        return re.sub(r"\*\*Status:\*\*.*", "**Status:** Draft", markdown, count=1)

    lines = markdown.splitlines()
    output: list[str] = []
    inserted = False
    for line in lines:
        output.append(line)
        if not inserted and line.startswith("**Type:**"):
            output.append("**Status:** Draft")
            inserted = True
    if inserted:
        return "\n".join(output)
    return markdown.rstrip() + "\n\n**Status:** Draft\n"


def build_template_markdown(
    template_text: str,
    *,
    title: str,
    requested_date: str,
    topic_summary: str,
) -> str:
    rendered: list[str] = []
    inserted_status = False

    for line in template_text.splitlines():
        if line.startswith("# Feature Request:"):
            rendered.append(f"# Feature Request: {title}")
        elif line.startswith("**Priority:**"):
            rendered.append("**Priority:** MEDIUM")
        elif line.startswith("**Type:**"):
            rendered.append("**Type:** Feature")
        elif line.startswith("**Status:**"):
            rendered.append("**Status:** Draft")
            inserted_status = True
        elif line.startswith("**Effort:**"):
            rendered.append("**Effort:** 1 day")
        elif line.startswith("**Requested:**"):
            rendered.append(f"**Requested:** {requested_date}")
        elif line.strip() == "Brief description of the feature or bug.":
            rendered.append(topic_summary)
        elif line.strip().startswith("<!-- One sentence:"):
            rendered.append(
                "Chaplain maintainers get a standalone Agent SDK planner "
                "feasibility signal without runtime migration risk."
            )
        else:
            rendered.append(line)

    if not inserted_status:
        with_status: list[str] = []
        for line in rendered:
            with_status.append(line)
            if line.startswith("**Type:**"):
                with_status.append("**Status:** Draft")
        rendered = with_status

    return "\n".join(rendered).rstrip() + "\n"


def estimate_cost_usd(usage: dict[str, Any] | None) -> float | None:
    if usage is None:
        return None

    input_tokens = int(usage.get("input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    cache_read_tokens = int(usage.get("cache_read_input_tokens", 0))
    cache_create_tokens = int(usage.get("cache_creation_input_tokens", 0))
    if input_tokens + output_tokens + cache_read_tokens + cache_create_tokens == 0:
        return None

    # Approximate Sonnet-tier rates per 1M tokens.
    estimated = (
        ((input_tokens + cache_create_tokens) / 1_000_000.0) * 3.0
        + (cache_read_tokens / 1_000_000.0) * 0.3
        + (output_tokens / 1_000_000.0) * 15.0
    )
    return round(estimated, 6)


async def generate_draft_with_agent_sdk(
    *,
    topic_text: str,
    feature_requests_dir: Path,
    model: str | None,
    max_budget_usd: float,
) -> tuple[PlannerDraft, float | None, list[str]]:
    try:
        from claude_agent_sdk import (
            ClaudeAgentOptions,
            HookMatcher,
            create_sdk_mcp_server,
            query,
            tool,
        )
    except ImportError as exc:
        raise RuntimeError(
            "claude-agent-sdk is required for this spike. "
            "Install with: pip install claude-agent-sdk"
        ) from exc

    post_tool_use_audit: list[str] = []

    @tool(
        name="next_fr_number",
        description="Return deterministic next FR number from feature-requests/FR-*.md",
        input_schema={},
    )
    async def next_fr_number_tool(_: dict[str, Any]) -> dict[str, Any]:
        number = next_fr_number(feature_requests_dir)
        payload = NextFrNumberPayload(fr_number=number, fr_tag=f"FR-{number:03d}")
        return {"content": [{"type": "text", "text": payload.model_dump_json()}]}

    @tool(
        name="read_fr_template",
        description="Return exact bytes/content of feature-requests/TEMPLATE.md",
        input_schema={},
    )
    async def read_fr_template_tool(_: dict[str, Any]) -> dict[str, Any]:
        template_text = read_fr_template(feature_requests_dir).decode("utf-8")
        return {"content": [{"type": "text", "text": template_text}]}

    async def post_tool_use_hook(
        hook_input: dict[str, Any],
        _tool_use_id: str | None,
        _context: dict[str, Any],
    ) -> dict[str, Any]:
        """PostToolUse hook to emit exploration audit traces."""
        tool_name = str(hook_input.get("tool_name", "<unknown-tool>"))
        traced_paths: list[str] = []
        raw_tool_input = hook_input.get("tool_input")
        if isinstance(raw_tool_input, dict):
            for key in ("file_path", "path", "directory", "cwd"):
                value = raw_tool_input.get(key)
                if isinstance(value, str) and value:
                    traced_paths.append(value)
        if not traced_paths:
            traced_paths.append("<none>")

        post_tool_use_audit.append(f"{tool_name}: {', '.join(traced_paths)}")
        return {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "audit trace recorded",
            }
        }

    planner_server = create_sdk_mcp_server(
        name="planner_tools",
        tools=[next_fr_number_tool, read_fr_template_tool],
    )
    output_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["fr_number", "title", "slug", "markdown"],
        "properties": {
            "fr_number": {"type": "integer", "minimum": 1},
            "title": {"type": "string", "minLength": 1},
            "slug": {"type": "string", "minLength": 1},
            "markdown": {"type": "string", "minLength": 1},
        },
    }
    options = ClaudeAgentOptions(
        mcp_servers={"planner": planner_server},
        allowed_tools=[
            "mcp__planner__next_fr_number",
            "mcp__planner__read_fr_template",
        ],
        permission_mode="dontAsk",
        setting_sources=[],
        cwd=str(project_root()),
        model=model,
        max_budget_usd=max_budget_usd,
        output_format={"type": "json_schema", "schema": output_schema},
        hooks={"PostToolUse": [HookMatcher(hooks=[post_tool_use_hook])]},
    )

    prompt = (
        "Create a YAMLGraph feature request draft from the topic text.\n"
        "You must call `next_fr_number` and `read_fr_template` before drafting.\n"
        "Return only valid JSON with keys: fr_number, title, slug, markdown.\n"
        "The markdown must include template section headings and set "
        "`**Status:** Draft`.\n\n"
        f"Topic text:\n{topic_text}"
    )

    structured_output: dict[str, Any] | None = None
    text_chunks: list[str] = []
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None

    async for message in query(prompt=prompt, options=options):
        payload = getattr(message, "structured_output", None)
        if isinstance(payload, dict):
            structured_output = payload

        raw_cost = getattr(message, "total_cost_usd", None)
        if isinstance(raw_cost, int | float):
            total_cost_usd = float(raw_cost)

        raw_usage = getattr(message, "usage", None)
        if isinstance(raw_usage, dict):
            usage = raw_usage

        content = getattr(message, "content", None)
        if isinstance(content, list):
            for block in content:
                text = getattr(block, "text", None)
                if isinstance(text, str) and text.strip():
                    text_chunks.append(text)

    if structured_output is not None:
        draft = PlannerDraft.model_validate(structured_output)
    else:
        candidate = "\n".join(text_chunks).strip()
        if not candidate.startswith("{"):
            match = re.search(r"\{.*\}", candidate, flags=re.DOTALL)
            if match is None:
                raise ValueError("Agent SDK response did not contain JSON output.")
            candidate = match.group(0)
        draft = PlannerDraft.model_validate_json(candidate)

    if total_cost_usd is None:
        total_cost_usd = estimate_cost_usd(usage)
    return draft, total_cost_usd, post_tool_use_audit


def write_planner_output(
    *,
    topic_file: Path,
    model: str | None,
    max_budget_usd: float,
) -> Path:
    repo_root = project_root()
    feature_requests_dir = repo_root / "feature-requests"
    if not topic_file.exists():
        raise FileNotFoundError(f"Topic file not found: {topic_file}")
    if not feature_requests_dir.exists():
        raise FileNotFoundError(
            f"feature-requests directory not found: {feature_requests_dir}"
        )

    topic_text = topic_file.read_text(encoding="utf-8")
    template_text = read_fr_template(feature_requests_dir).decode("utf-8")

    draft, run_cost, audit_entries = asyncio.run(
        generate_draft_with_agent_sdk(
            topic_text=topic_text,
            feature_requests_dir=feature_requests_dir,
            model=model,
            max_budget_usd=max_budget_usd,
        )
    )

    authoritative_fr_number = next_fr_number(feature_requests_dir)
    slug = slugify(draft.slug or draft.title)
    title = draft.title.strip() or f"FR-{authoritative_fr_number:03d} planner spike"
    markdown = ensure_draft_status(draft.markdown)
    if not all(section in markdown for section in REQUIRED_TEMPLATE_SECTIONS):
        markdown = build_template_markdown(
            template_text,
            title=title,
            requested_date=dt.date.today().isoformat(),
            topic_summary=summarize_topic(topic_text),
        )

    output_path = feature_requests_dir / f"FR-{authoritative_fr_number:03d}-{slug}.md"
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing FR file: {output_path}")

    output_path.write_text(markdown, encoding="utf-8")

    if run_cost is None:
        raise RuntimeError("Per-run cost was not measurable from Agent SDK output.")
    if run_cost >= 0.15:
        raise RuntimeError(
            f"Per-run cost ${run_cost:.6f} exceeds target budget <$0.15."
        )

    print(f"✓ Wrote {output_path.relative_to(repo_root)}")
    print(f"✓ Estimated run cost: ${run_cost:.6f}")
    print("✓ PostToolUse audit:")
    for entry in audit_entries:
        print(f"  - {entry}")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent SDK planner spike.")
    parser.add_argument("topic_file", help="Path to topic markdown file")
    parser.add_argument("--model", default=None, help="Optional model override.")
    parser.add_argument("--max-budget-usd", type=float, default=0.15)
    args = parser.parse_args()
    try:
        write_planner_output(
            topic_file=Path(args.topic_file),
            model=args.model,
            max_budget_usd=args.max_budget_usd,
        )
    except (FileNotFoundError, RuntimeError, ValidationError, ValueError) as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
