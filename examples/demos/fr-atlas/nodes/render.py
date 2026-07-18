"""FR-748 renderer — mechanical assembly of the atlas (REQ-YG-566)."""

from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path


def _fr_line(digest: dict) -> str:
    return f"- **{digest['id']}** — {digest['title']}  `[{digest['status']}]`"


def render_atlas(
    story: str,
    themes: list[dict],
    digests: list[dict],
    parse_notes: dict,
    project_name: str,
    has_cap_registry: bool = True,
) -> str:
    by_id = {d["id"]: d for d in digests}
    histogram = Counter(d["status_bucket"] for d in digests)

    def last_activity(theme: dict) -> str:
        return max(
            (by_id[i].get("last_activity") or "" for i in theme["fr_ids"]),
            default="",
        )

    ordered = sorted(themes, key=last_activity, reverse=True)
    lines = [
        # The atlas lands in docs/ where Jekyll renders it as LIQUID: a
        # literal Jinja2 tag in any FR title kills the Pages build
        # (2026-07-18, 6 consecutive failures). Normalize at the boundary
        # where the artifact enters Jekyll's jurisdiction — wrap the whole
        # document; titles stay verbatim.
        "{% raw %}",
        f"# FR Atlas — {project_name}",
        "",
        f"> Generated {date.today().isoformat()} by "
        "`examples/demos/fr-atlas` (FR-748) — the project as told by its "
        "feature requests, for a newcomer. Status tags are verbatim from "
        "each FR at HEAD; theme grouping is a model judgement reconciled "
        "in code (every FR appears exactly once).",
        "",
    ]
    if not has_cap_registry:
        lines += [
            "> ⚠ No `capabilities/` registry in this corpus — the module "
            "axis is derived from git-touched paths only.",
            "",
        ]
    lines += [
        story.strip(),
        "",
        "## Themes (most recently active first)",
    ]
    for theme in ordered:
        lines += ["", f"### {theme['name']}", "", theme.get("arc", "").strip()]
        modules = theme.get("modules") or []
        if modules:
            lines += ["", f"*Modules:* {', '.join(f'`{m}`' for m in modules[:8])}"]
        lines.append("")
        members = sorted(
            theme["fr_ids"],
            key=lambda i: by_id[i].get("last_activity") or "",
            reverse=True,
        )
        lines += [_fr_line(by_id[i]) for i in members]

    rejected = [d for d in digests if d["status_bucket"] == "rejected"]
    lines += [
        "",
        "## Graveyard (rejections that taught the doctrine)",
        "",
    ]
    if rejected:
        lines += [_fr_line(d) for d in rejected]
    else:
        lines.append(f"- {len(rejected)} rejections on record.")

    lines += [
        "",
        "## Mechanical counts",
        "",
        f"- FRs: {len(digests)}"
        + (
            f" (+{parse_notes['excluded']} companion files excluded)"
            if parse_notes.get("excluded")
            else ""
        ),
        "- Status histogram: "
        + ", ".join(f"{k} {v}" for k, v in histogram.most_common()),
    ]
    if parse_notes.get("headerless"):
        lines.append(
            "- No status header (reported, not dropped): "
            + ", ".join(parse_notes["headerless"])
        )
    lines.append("{% endraw %}")
    return "\n".join(lines) + "\n"


def write_atlas(state: dict) -> dict:
    """Graph-facing wrapper: render and write the dated atlas."""
    project_dir = Path(state["project_dir"]).expanduser()
    story = state["story"]
    if isinstance(story, dict):  # inline-schema node stores the dict
        story = story.get("story", "")
    text = render_atlas(
        story=story,
        themes=state["final_themes"],
        digests=state["fr_digests"],
        parse_notes=state["parse_notes"],
        project_name=project_dir.resolve().name,
        has_cap_registry=bool(state.get("module_index")),
    )
    out_dir = project_dir / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{date.today().isoformat()}-fr-atlas.md"
    out_path.write_text(text)
    print(f"✓ atlas → {out_path}")
    return {"atlas_path": str(out_path), "written": True}
