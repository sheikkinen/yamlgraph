"""Write file tool for the planner demo.

Creates parent directories if needed, then writes content to the path.
"""

from pathlib import Path


def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories as needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Wrote {len(content)} bytes to {path}"
