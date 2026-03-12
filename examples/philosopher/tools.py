"""FR-184/FR-185: Philosopher Daemon tools.

Provides scan_diary_markers() and write_proposals() for the philosopher graph.
"""

import re
from datetime import datetime, timedelta
from pathlib import Path

from yamlgraph.models.schemas import CopilotResult


def get_today() -> str:
    """Get today's date as YYYY-MM-DD. Mockable for testing."""
    return datetime.now().strftime("%Y-%m-%d")


def scan_diary_markers(state: dict) -> dict:
    """Scan diary files for heuristic/trap/Seed markers.

    Args:
        state: Dict with diary_dir (str) and lookback_days (int)

    Returns:
        dict with:
          - heuristics: {text: [file1, file2, ...]}
          - traps: {name: [file1, file2, ...]}
          - seeds: {question: file}
          - file_count: int
    """
    diary_dir = Path(state["diary_dir"])
    lookback_days = int(state.get("lookback_days", 30))

    heuristics: dict[str, list[str]] = {}
    traps: dict[str, list[str]] = {}
    seeds: dict[str, str] = {}
    file_count = 0

    if not diary_dir.exists():
        return {
            "heuristics": heuristics,
            "traps": traps,
            "seeds": seeds,
            "file_count": file_count,
        }

    # Calculate cutoff date
    today = datetime.strptime(get_today(), "%Y-%m-%d")
    cutoff = today - timedelta(days=lookback_days)

    # Patterns for markers (case-insensitive)
    trap_pattern = re.compile(r"\*\*Trap:\*\*\s*(.+?)(?:\n|$)", re.IGNORECASE)
    heuristic_pattern = re.compile(r"\*\*Heuristic:\*\*\s*(.+?)(?:\n|$)", re.IGNORECASE)
    seed_pattern = re.compile(r"\*\*Seed:\*\*\s*(.+?)(?:\n|$)", re.IGNORECASE)

    for file_path in diary_dir.glob("*.md"):
        # Extract date from filename (diary-YYYY-MM-DD.md format)
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", file_path.name)
        if date_match:
            try:
                file_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                if file_date < cutoff:
                    continue  # Skip files outside lookback window
            except ValueError:
                pass  # If date parsing fails, include the file

        file_count += 1
        content = file_path.read_text()
        filename = file_path.name

        # Extract traps
        for match in trap_pattern.finditer(content):
            trap_name = match.group(1).strip()
            if trap_name not in traps:
                traps[trap_name] = []
            if filename not in traps[trap_name]:
                traps[trap_name].append(filename)

        # Extract heuristics
        for match in heuristic_pattern.finditer(content):
            heuristic_text = match.group(1).strip()
            if heuristic_text not in heuristics:
                heuristics[heuristic_text] = []
            if filename not in heuristics[heuristic_text]:
                heuristics[heuristic_text].append(filename)

        # Extract seeds
        for match in seed_pattern.finditer(content):
            seed_text = match.group(1).strip()
            if seed_text not in seeds:
                seeds[seed_text] = filename

    return {
        "heuristics": heuristics,
        "traps": traps,
        "seeds": seeds,
        "file_count": file_count,
    }


def write_proposals(state: dict) -> dict:
    """Write graduation proposals to .chaplain/inbox/.

    Only writes proposals where occurrence count >= graduation_threshold.
    Deduplicates against existing Scripture entries.

    Args:
        state: Dict with:
          - inbox_dir: str
          - graduation_threshold: int
          - proposals: list[dict] with type, name, count, files
          - scripture_content: str (optional)

    Returns:
        dict with written_count, excluded_already_graduated
    """
    inbox_dir = Path(state["inbox_dir"])
    threshold = int(state.get("graduation_threshold", 3))
    proposals_raw = state.get("proposals", [])

    # FR-185: Single parse path — CopilotResult → extract JSON → validate through Pydantic
    if isinstance(proposals_raw, CopilotResult):
        from examples.philosopher.models import ProposalList, extract_json

        json_str = extract_json(proposals_raw.output, "analyze")
        proposal_list = ProposalList.model_validate_json(
            json_str
            if json_str.strip().startswith("{")
            else f'{{"proposals": {json_str}}}'
        )
        proposals = proposal_list.proposals
    elif hasattr(proposals_raw, "proposals"):
        proposals = proposals_raw.proposals
    else:
        proposals = proposals_raw if isinstance(proposals_raw, list) else []

    scripture_content = state.get("scripture_content", "")

    written_count = 0
    excluded_already_graduated = 0

    inbox_dir.mkdir(parents=True, exist_ok=True)

    for proposal in proposals:
        # Handle both dict and Pydantic model
        if hasattr(proposal, "model_dump"):
            proposal = proposal.model_dump()
        elif hasattr(proposal, "get"):
            pass  # Already a dict
        else:
            continue  # Skip unknown types

        name = proposal.get("name", "")
        count = proposal.get("count", 0)
        proposal_type = proposal.get("type", "unknown")
        files = proposal.get("files", [])

        # Skip if below threshold
        if count < threshold:
            continue

        # Skip if already in Scripture
        if scripture_content and name in scripture_content:
            excluded_already_graduated += 1
            continue

        # Write proposal file
        safe_name = re.sub(r"[^\w\-]", "_", name)[:50]
        filename = f"graduate-{proposal_type}-{safe_name}.md"
        proposal_path = inbox_dir / filename

        content = f"""# Graduate {proposal_type}: {name}

**Occurrences:** {count} times across {len(files)} diary entries

**Type:** {proposal_type}

**Evidence:**
{chr(10).join(f'- {f}' for f in files)}

## Proposal

Add `{name}` to Scripture under `{proposal_type}s:` section.

This pattern has appeared {count} times, meeting the graduation threshold.
"""

        proposal_path.write_text(content)
        written_count += 1

    return {
        "written_count": written_count,
        "excluded_already_graduated": excluded_already_graduated,
    }
