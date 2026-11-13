"""Small file-reading tools for the FR-1159 map memo demo."""

from pathlib import Path


def prepare(state: dict[str, str]) -> dict[str, dict[str, list[str] | str]]:
    """Return sorted note paths and the selected memo store."""
    notes_dir = Path(state.get("notes_dir") or "examples/demos/map_memo/notes")
    paths = sorted(
        (path for path in notes_dir.glob("*.md") if path.is_file()),
        key=lambda path: path.name,
    )
    return {
        "plan": {
            "paths": [str(path) for path in paths],
            "store": state.get("store") or "outputs/map_memo_demo/memo.sqlite",
        }
    }


def read_note(state: dict[str, str]) -> dict[str, dict[str, str]]:
    """Return the requested path and its UTF-8 text."""
    path = state["path"]
    return {"note": {"path": path, "text": Path(path).read_text(encoding="utf-8")}}
