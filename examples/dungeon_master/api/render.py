"""Full-story Markdown render for DM v2 (FR-494 Part 1) — the reader serialization.

The pure, human-readable sibling of the machine ``story.json``: one standalone
Markdown manuscript over the *whole* story doc. No LLM, no I/O — a deterministic
read, unit-testable from a fixture doc (FR-474 J3 visibility harness).

The chapter body is :func:`chapter_ops.compose_book_deterministic` reused
**verbatim** (FR-494 J3) — this module never reimplements chapter assembly; it
only frames that body with the front matter the JSON also holds: the tagline
(blockquote lead, **no invented title** — the doc has no title field and the
tagline is a paragraph, J1), the synopsis, and the cast. Every section sits at
**H1**, the same level the Book body emits, so the body drops in unchanged.

It inherits the Book compose's raise: when no chapter is played there is no
manuscript (Commandment 6 — the front matter alone is not a story). The
``world_state`` forward-carry ledger is plumbing for the next chapter's play, not
manuscript, so it never appears (suppressed by the reused Book body).
"""

from __future__ import annotations

from examples.dungeon_master.api import chapter_ops


def _summary_gloss(text: str) -> str:
    """The one-line cast gloss for a character card.

    The card is a labeled SHEET (``SUMMARY:`` / ``ROLE:`` / ``ORIGIN:`` …) joined
    by single newlines (FR-496 J1), so the FR-494 ``split("\\n\\n")[0]`` would leak
    the whole sheet. When a ``SUMMARY:`` line is present, return its value alone
    (the label is case- and leading-whitespace tolerant, J3); otherwise fall back
    to the first ``\\n\\n``-split paragraph — plain-prose cards keep the FR-494
    behaviour (J4).
    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("SUMMARY:"):
            return stripped[len("SUMMARY:") :].strip()
    return text.split("\n\n", 1)[0].strip()


def _cast_lines(doc: dict) -> list[str]:
    """One ``**name** — <summary gloss>`` bullet per non-empty character card.

    A character whose card ``text`` is empty is dropped (no dangling bullet, J2);
    the gloss is the card's ``SUMMARY:`` value when the sheet has one, else its
    first ``\\n\\n``-split paragraph (FR-496) — never the whole labeled sheet.
    """
    chars = doc.get("characters", {})
    cards = chars.get("cards", {})
    lines: list[str] = []
    for cid in chars.get("roster", []):
        card = cards.get(cid, {})
        text = (card.get("text") or "").strip()
        if not text:
            continue
        name = card.get("name") or cid
        gloss = _summary_gloss(text)
        lines.append(f"- **{name}** — {gloss}")
    return lines


def render_story_markdown(doc: dict) -> str:
    """Render the whole story doc as one standalone Markdown manuscript.

    Order: tagline (blockquote lead) → ``# Synopsis`` → optional ``# Cast`` →
    a ``---`` rule → the Book body (``compose_book_deterministic``, verbatim).
    Raises ``ValueError`` (via the Book compose) when no chapter has been played.
    """
    # Compose the body FIRST so an unplayed story raises before we frame it — the
    # front matter alone is not a story (J3, inherited raise).
    body = chapter_ops.compose_book_deterministic(doc)

    sections: list[str] = []
    tagline = (doc.get("tagline") or "").strip()
    if tagline:
        sections.append(f"> {tagline}")

    synopsis = (doc.get("synopsis", {}).get("text") or "").strip()
    if synopsis:
        sections.append(f"# Synopsis\n\n{synopsis}")

    cast = _cast_lines(doc)
    if cast:
        sections.append("# Cast\n\n" + "\n".join(cast))

    sections.append("---")
    sections.append(body)
    return "\n\n".join(sections)
