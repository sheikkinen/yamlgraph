"""Write file tool for the enforcer demo.

Creates parent directories if needed, then writes content to the path.
Rejects paths outside the project root.
"""

from pathlib import Path


def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories as needed."""
    project_root = Path.cwd().resolve()
    p = Path(path).resolve()
    if not p.is_relative_to(project_root):
        return f"Error: path {path} is outside project root"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Wrote {len(content)} bytes to {path}"
