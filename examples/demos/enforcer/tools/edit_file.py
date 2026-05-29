"""Edit file tool for the enforcer demo.

Surgical text replacement with path restriction and unique-match validation.
"""

from pathlib import Path


def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Replace old_text with new_text in a file. old_text must appear exactly once."""
    project_root = Path.cwd().resolve()
    p = Path(path).resolve()
    if not p.is_relative_to(project_root):
        return f"Error: path {path} is outside project root"
    if not p.is_file():
        return f"Error: {path} does not exist"
    content = p.read_text()
    if old_text not in content:
        return f"Error: old_text not found in {path}"
    count = content.count(old_text)
    if count > 1:
        return f"Error: old_text appears {count} times in {path} — must be unique"
    content = content.replace(old_text, new_text, 1)
    p.write_text(content)
    return f"Replaced {len(old_text)} chars with {len(new_text)} chars in {path}"
