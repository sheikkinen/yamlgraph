"""Render canon YAML pages as Obsidian-compatible wiki markdown (FR-648).

Reads canon/*.yaml, emits wiki/*.md with YAML frontmatter + markdown body.
Prose fields become sections; references become [[wiki_links]].
Pure template expansion — no LLM calls.
"""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# Fields rendered as markdown body sections (not in frontmatter)
PROSE_FIELDS: dict[str, list[str]] = {
    "character": ["backstory"],
    "event": [],
    "faction": ["description"],
    "location": ["description"],
    "rule": ["description"],
    "premise": ["text"],
    "synopsis": ["text"],
}


def render_page(page: dict) -> str:
    """Convert a canon page dict to Obsidian-compatible markdown."""
    page_type = page.get("type", "")
    page_id = page.get("id", "unknown")
    name = page.get("name", page_id)
    prose_keys = PROSE_FIELDS.get(page_type, [])

    # Separate frontmatter fields from prose fields
    fm = {}
    prose = {}
    skip_keys = {"relationships"}  # rendered separately in body
    for key, value in page.items():
        if key in prose_keys and value:
            prose[key] = value
        elif key not in skip_keys:
            fm[key] = value

    # Build frontmatter
    fm_str = yaml.dump(
        fm, default_flow_style=False, allow_unicode=True, sort_keys=False
    )

    # Build body
    lines = [f"# {name}", ""]

    # Type-specific header line
    if page_type == "character":
        header_parts = []
        if page.get("faction"):
            header_parts.append(f"**Faction:** [[{page['faction']}]]")
        if page.get("birth_year") is not None:
            header_parts.append(f"**Born:** year {page['birth_year']}")
        if page.get("role"):
            header_parts.append(f"**Role:** {page['role']}")
        if header_parts:
            lines.append(" | ".join(header_parts))
            lines.append("")
    elif page_type == "event":
        header_parts = []
        if page.get("year") is not None:
            header_parts.append(f"**Year:** {page['year']}")
        if page.get("scope"):
            header_parts.append(f"**Scope:** {page['scope']}")
        if header_parts:
            lines.append(" | ".join(header_parts))
            lines.append("")

    # Prose sections
    for key in prose_keys:
        if key in prose:
            section_title = key.replace("_", " ").title()
            lines.append(f"## {section_title}")
            lines.append("")
            lines.append(prose[key])
            lines.append("")

    # Goals
    if page.get("goals"):
        lines.append("## Goals")
        lines.append("")
        for goal in page["goals"]:
            lines.append(f"- {goal}")
        lines.append("")

    # Participants (events)
    if page.get("participants"):
        lines.append("## Participants")
        lines.append("")
        for p in page["participants"]:
            if isinstance(p, dict):
                entity = p.get("entity", p.get("name", "?"))
                lines.append(f"- [[{entity}]]")
            else:
                lines.append(f"- [[{p}]]")
        lines.append("")

    # Consequences (events)
    if page.get("consequences"):
        lines.append("## Consequences")
        lines.append("")
        cons = page["consequences"]
        if isinstance(cons, dict):
            for key, val in cons.items():
                lines.append(f"- **{key}**: {val}")
        elif isinstance(cons, list):
            for c in cons:
                lines.append(f"- {c}")
        else:
            lines.append(f"- {cons}")
        lines.append("")

    # Relationships
    relationships = page.get("relationships", [])
    if relationships:
        lines.append("## Relationships")
        lines.append("")
        if isinstance(relationships, dict):
            for target, desc in relationships.items():
                lines.append(f"- [[{target}]] — {desc}")
        elif isinstance(relationships, list):
            for rel in relationships:
                if isinstance(rel, str):
                    lines.append(f"- {rel}")
                elif isinstance(rel, dict):
                    to = rel.get("to", rel.get("id", rel.get("target_id", "?")))
                    kind = rel.get("kind", rel.get("type", ""))
                    desc = rel.get("description", "")
                    valence = rel.get("valence", "")
                    label = kind or desc or "related"
                    val_str = f" ({valence})" if valence else ""
                    lines.append(f"- [[{to}]] — {label}{val_str}")
        lines.append("")

    # Fears
    if page.get("fears"):
        lines.append("## Fears")
        lines.append("")
        for fear in page["fears"]:
            lines.append(f"- {fear}")
        lines.append("")

    # References
    refs = page.get("references", [])
    if refs:
        lines.append("## References")
        lines.append("")
        for ref in refs:
            if isinstance(ref, dict):
                ref_id = ref.get("pageId", ref.get("id", str(ref)))
                lines.append(f"- [[{ref_id}]]")
            else:
                lines.append(f"- [[{ref}]]")
        lines.append("")

    body = "\n".join(lines)
    return f"---\n{fm_str}---\n{body}"


def render_wiki(canon_dir: str, wiki_dir: str) -> dict:
    """Render all canon YAML files to Obsidian wiki markdown.

    Args:
        canon_dir: Path to canon/*.yaml directory.
        wiki_dir: Output path for wiki/*.md files.

    Returns:
        Dict with written_paths and count for state update.
    """
    canon_path = Path(canon_dir)
    wiki_path = Path(wiki_dir)
    wiki_path.mkdir(parents=True, exist_ok=True)

    written = []
    for yaml_file in sorted(canon_path.rglob("*.yaml")):
        page = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        if not isinstance(page, dict) or "id" not in page:
            continue

        md_content = render_page(page)
        md_file = wiki_path / f"{page['id']}.md"
        md_file.write_text(md_content, encoding="utf-8")
        written.append(str(md_file))

    logger.info("📖 Rendered %d wiki pages to %s", len(written), wiki_dir)
    return {"wiki_paths": written, "wiki_count": len(written)}


if __name__ == "__main__":
    import sys

    base = Path(__file__).parent.parent
    c_dir = str(base / "canon")
    w_dir = str(base / "wiki")
    if len(sys.argv) > 1:
        w_dir = sys.argv[1]
    result = render_wiki(c_dir, w_dir)
    print(f"✓ Rendered {result['wiki_count']} pages to {w_dir}")
