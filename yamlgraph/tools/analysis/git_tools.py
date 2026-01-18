"""Git analysis tools for implementation agent.

Provides git blame and git log information for code context.
"""

import subprocess
from pathlib import Path


def git_blame(file_path: str, line: int) -> dict:
    """Get blame info for a specific line.

    Args:
        file_path: Path to the file (relative or absolute)
        line: Line number (1-indexed)

    Returns:
        dict with author, date, commit, summary, line_content
        or dict with error key if failed
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    try:
        # Use porcelain format for machine-readable output
        result = subprocess.run(
            ["git", "blame", "-L", f"{line},{line}", "--porcelain", str(path)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return {
                "error": result.stderr.strip()
                or f"git blame failed for {file_path}:{line}"
            }

        # Parse porcelain output
        lines = result.stdout.strip().split("\n")
        if not lines or len(lines) < 2:
            return {"error": f"Invalid line number: {line}"}

        # First line is commit hash and original line number
        first_line = lines[0].split()
        if not first_line:
            return {"error": "Failed to parse git blame output"}

        commit = first_line[0]

        # Parse the rest of the porcelain output
        author = ""
        date = ""
        summary = ""
        line_content = ""

        for output_line in lines[1:]:
            if output_line.startswith("author "):
                author = output_line[7:]
            elif output_line.startswith("author-time "):
                # Convert Unix timestamp to readable format
                import datetime

                timestamp = int(output_line[12:])
                date = datetime.datetime.fromtimestamp(timestamp).strftime(
                    "%Y-%m-%d %H:%M"
                )
            elif output_line.startswith("summary "):
                summary = output_line[8:]
            elif output_line.startswith("\t"):
                # Actual line content starts with tab
                line_content = output_line[1:]

        return {
            "commit": commit[:8],  # Short hash
            "author": author,
            "date": date,
            "summary": summary,
            "line_content": line_content,
        }

    except subprocess.TimeoutExpired:
        return {"error": "git blame timed out"}
    except Exception as e:
        return {"error": str(e)}


def git_log(file_path: str, n: int = 5) -> dict:
    """Get recent commits for a file.

    Args:
        file_path: Path to the file (relative or absolute)
        n: Maximum number of commits to return (default 5)

    Returns:
        dict with commits list, each containing hash, author, date, message
        or dict with error key if failed
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    try:
        # Use format for clean parsing
        result = subprocess.run(
            [
                "git",
                "log",
                f"-{n}",
                "--format=%H|%an|%ai|%s",
                "--follow",
                "--",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            error = result.stderr.strip()
            if "does not have any commits" in error or not result.stdout.strip():
                return {"error": f"No git history for {file_path}"}
            return {"error": error or f"git log failed for {file_path}"}

        output = result.stdout.strip()
        if not output:
            return {"error": f"No git history for {file_path}"}

        commits = []
        for line in output.split("\n"):
            if not line.strip():
                continue
            parts = line.split("|", 3)
            if len(parts) >= 4:
                commits.append(
                    {
                        "hash": parts[0][:8],  # Short hash
                        "author": parts[1],
                        "date": parts[2][:10],  # Just the date part
                        "message": parts[3],
                    }
                )

        return {"commits": commits}

    except subprocess.TimeoutExpired:
        return {"error": "git log timed out"}
    except Exception as e:
        return {"error": str(e)}
