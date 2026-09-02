"""Chinese horoscope demo tools."""

from pathlib import Path


def save_chinese_horoscope(state: dict) -> dict:
    """Write Chinese horoscope document to outputs/chinese-horoscope-YYYY-MM-DD.md."""
    date = state.get("date", "unknown")
    document = state.get("document", "")

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    filename = f"chinese-horoscope-{date}.md"
    output_path = output_dir / filename
    output_path.write_text(document, encoding="utf-8")

    return {"output_path": str(output_path)}
