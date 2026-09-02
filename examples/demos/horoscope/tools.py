"""FR-201 Horoscope demo tools."""

from pathlib import Path


def save_horoscope(state: dict) -> dict:
    """Write horoscope document to outputs/horoscope-YYYY-MM-DD.md.

    Args:
        state: Graph state containing date and document

    Returns:
        Dict with output_path
    """
    date = state.get("date", "unknown")
    document = state.get("document", "")

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    filename = f"horoscope-{date}.md"
    output_path = output_dir / filename
    output_path.write_text(document, encoding="utf-8")

    return {"output_path": str(output_path)}
