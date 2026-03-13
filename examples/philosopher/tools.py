"""FR-184/FR-185/FR-195: Philosopher Daemon tools.

Provides scan_diary_markers(), write_proposals(), unwrap_distill(),
and unwrap_challenge() for the philosopher graph.
"""

import re
from datetime import datetime, timedelta
from pathlib import Path

from yamlgraph.contrib import to_serializable
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

    # Wrap in scan_result key to match graph state_key declaration
    # (dict returns merge keys directly, so this becomes state.scan_result)
    return {
        "scan_result": {
            "heuristics": heuristics,
            "traps": traps,
            "seeds": seeds,
            "file_count": file_count,
        }
    }


def unwrap_distill(state: dict) -> dict:
    """Parse distill CopilotResult into a validated Proposal dict or None (FR-195).

    Does not use extract_json() because distill output is always a JSON object
    and extract_json's array-first search picks up inner arrays (e.g. files list).
    """
    import json
    import re

    from examples.philosopher.models import Proposal

    raw = state.get("distill_result")
    if not isinstance(raw, CopilotResult):
        return {"top_candidate": None}

    # Strip markdown fences
    text = raw.output.strip()
    text = re.sub(r"```(?:json)?\s*\n?", "", text).strip()
    if text.endswith("```"):
        text = text[:-3].strip()

    # Find outermost JSON object boundaries (always an object, never an array)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(
            f"No valid JSON object in distill output. Preview: {raw.output[:200]}"
        )
    json_str = text[start : end + 1]
    parsed = json.loads(json_str)

    # Handle {"selected": null} signal — check key presence, not just value
    if parsed is None or ("selected" in parsed and parsed["selected"] is None):
        return {"top_candidate": None}

    # If wrapped in {"selected": {...}}, unwrap; otherwise parse directly
    payload = parsed.get("selected", parsed)
    proposal = Proposal.model_validate(payload)
    return {"top_candidate": proposal.model_dump()}


def unwrap_challenge(state: dict) -> dict:
    """Parse challenge CopilotResult into a validated ChallengeVerdict dict (FR-195)."""
    from examples.philosopher.models import ChallengeVerdict, extract_json

    raw = state.get("challenge_result")
    if not isinstance(raw, CopilotResult):
        return {
            "challenge_parsed": {
                "verdict": "reject",
                "confidence": 0.0,
                "objections": ["No challenge result"],
                "surviving_arguments": [],
            }
        }

    json_str = extract_json(raw.output, "challenge")
    verdict = ChallengeVerdict.model_validate_json(json_str)
    return {"challenge_parsed": verdict.model_dump()}


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

    # FR-195: Single proposal path via top_candidate (already unwrapped by unwrap_distill)
    top = state.get("top_candidate")
    if isinstance(top, dict) and top:
        from examples.philosopher.models import Proposal

        proposals = [Proposal.model_validate(top)]
    # FR-185: Single parse path — CopilotResult → extract JSON → validate through Pydantic
    elif isinstance(proposals_raw, CopilotResult):
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
        # FR-186: Collapsed model_dump + dict branches into single dict branch
        # via to_serializable (normalizes both Pydantic models and dicts to dicts)
        serialized = to_serializable(proposals_raw)
        if isinstance(serialized, dict):
            proposals = serialized.get("proposals", [])
        elif isinstance(serialized, list):
            proposals = serialized
        else:
            proposals = []

    scripture_content = state.get("scripture_content", "")

    written_count = 0
    excluded_already_graduated = 0

    inbox_dir.mkdir(parents=True, exist_ok=True)

    for proposal in proposals:
        # FR-186: Use to_serializable instead of inline hasattr check
        proposal = to_serializable(proposal)
        if not isinstance(proposal, dict):
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
