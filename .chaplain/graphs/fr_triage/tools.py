"""FR-745: fr_triage tools — append + gate. REQ-YG-564.

Never a verdict: append_triage cannot change Status and refuses
non-Proposed FRs. F3 caps enforced here, not just in the prompt.
Zero-yield raises (Commandment 6).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

CANON_CAP = 3
WITNESS_CAP = 5
STATUS_RE = re.compile(r"^\*\*Status:?\*\*:?\s*(.+)$", re.M)
PENDING_RE = re.compile(r"^- \[pending\]", re.M)


def read_fr(state: dict) -> dict:
    """Load the FR text for the triage prompt."""
    text = Path(state["fr_path"]).read_text(encoding="utf-8", errors="replace")
    return {"fr_text": text[:20000]}


def append_triage(state: dict) -> dict:
    """Append '## Triage' with [pending] claims. Refuses non-Proposed
    FRs and never touches the Status line (authority_is_not_a_checklist)."""
    fr_path = Path(state["fr_path"])
    triage = state.get("triage") or {}
    canon = [str(x).splitlines()[0] for x in (triage.get("canon_answers") or [])][
        :CANON_CAP
    ]
    witnesses = [
        str(x).splitlines()[0] for x in (triage.get("pre_mortem_witnesses") or [])
    ][:WITNESS_CAP]
    value_prop = str(triage.get("value_prop_check") or "").splitlines()[:1]
    if not (canon or witnesses):
        raise ValueError("empty triage output — refusing to append nothing")

    text = fr_path.read_text(encoding="utf-8", errors="replace")
    m = STATUS_RE.search(text)
    status = (m.group(1).strip() if m else "").lower()
    if not status.startswith("proposed"):
        raise ValueError(
            f"FR status is {status!r} — triage appends to Proposed FRs only"
        )
    if "## Triage" in text:
        raise ValueError("FR already carries a Triage section — re-run not stacked")

    lines = ["", "## Triage (generated — claims requiring disposition)", ""]
    lines += [f"- [pending] canon: {c}" for c in canon]
    lines += [f"- [pending] pre-mortem: {w}" for w in witnesses]
    if value_prop and value_prop[0]:
        lines.append(f"- [pending] value-prop: {value_prop[0]}")
    lines.append("")
    fr_path.write_text(text + "\n".join(lines), encoding="utf-8")
    logger.info(
        "📋 triage appended to %s (%d claims)",
        fr_path.name,
        len(canon) + len(witnesses),
    )
    return {"appended": True}


def gate_check(fr_text: str) -> bool:
    """F4: True = passes. Blocks only Judged-or-later FRs carrying
    [pending] triage claims; Proposed drafts pass freely."""
    m = STATUS_RE.search(fr_text)
    status = (m.group(1).strip() if m else "").lower()
    if status.startswith("proposed") or not status:
        return True
    if "## Triage" not in fr_text:
        return True
    return not PENDING_RE.search(fr_text)
