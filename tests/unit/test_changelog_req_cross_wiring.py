"""FR-242: Condemning test for changelog req cross-wiring.

Proves that changelog fragment `req:` front-matter values are cross-wired —
multiple fragments reference requirement IDs that belong to unrelated
capabilities. The capabilities registry (capabilities/CAP-*.yaml) is the
source of truth; each capability declares its `fr:` (origin Feature Request)
and its `requirements:` (REQ-YG-XXX list). A fragment's `req:` must appear
in a capability whose `fr:` matches the fragment's FR number.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAPABILITIES_DIR = REPO_ROOT / "capabilities"
CHANGELOG_DIR = REPO_ROOT / "changelog"


def _build_fr_to_reqs() -> dict[str, set[str]]:
    """Build FR → {valid REQ IDs} mapping from capabilities registry."""
    fr_to_reqs: dict[str, set[str]] = {}
    for filepath in sorted(CAPABILITIES_DIR.glob("CAP-*.yaml")):
        with open(filepath) as f:
            data = yaml.safe_load(f)
        fr_ref = data.get("fr")
        if not fr_ref or fr_ref == "legacy":
            continue
        reqs = {r["id"] for r in data.get("requirements", [])}
        fr_to_reqs.setdefault(fr_ref, set()).update(reqs)
    return fr_to_reqs


def _parse_fragment_req(filepath: Path) -> tuple[str | None, set[str] | None]:
    """Extract (FR number, set of req IDs) from a changelog fragment.

    Returns (None, None) if the fragment has no req or no FR number.
    Handles both single values and comma-separated lists.
    """
    content = filepath.read_text()
    if not content.startswith("---"):
        return None, None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, None
    front_matter = yaml.safe_load(parts[1])
    if not front_matter:
        return None, None
    raw_req = front_matter.get("req")
    if not raw_req:
        return None, None
    fr_match = re.search(r"(FR-\d+)", filepath.name, re.IGNORECASE)
    if not fr_match:
        return None, None
    # Handle comma-separated req values (e.g. "REQ-YG-206,REQ-YG-207")
    req_ids = {r.strip() for r in str(raw_req).split(",") if r.strip()}
    return fr_match.group(1).upper(), req_ids


@pytest.mark.req("REQ-YG-162", "REQ-YG-161")
class TestChangelogReqIntegrity:
    """Changelog fragment req: must match capability registry for same FR."""

    def test_fragment_req_matches_capability_for_its_fr(self) -> None:
        """Every fragment's req: must exist in a capability mapped to its FR.

        Detects cross-wiring: a fragment claiming a REQ that belongs to a
        different feature's capability.
        """
        fr_to_reqs = _build_fr_to_reqs()

        errors: list[str] = []
        checked = 0
        for filepath in sorted(CHANGELOG_DIR.rglob("*.md")):
            fr_num, fragment_reqs = _parse_fragment_req(filepath)
            if not fr_num or not fragment_reqs:
                continue
            if fr_num not in fr_to_reqs:
                continue  # no capability for this FR; can't validate
            valid_reqs = fr_to_reqs[fr_num]
            checked += 1
            invalid = fragment_reqs - valid_reqs
            if invalid:
                errors.append(
                    f"{filepath.relative_to(CHANGELOG_DIR)}: "
                    f"req={sorted(invalid)} not in {fr_num} capability {sorted(valid_reqs)}"
                )

        assert checked > 0, "No fragments with FR+req found; test is vacuous"
        assert not errors, (
            f"Cross-wired changelog req: values ({len(errors)} of {checked} checked):\n"
            + "\n".join(f"  • {e}" for e in errors)
        )

    def test_no_req_collision_across_unrelated_frs(self) -> None:
        """Different FRs should not claim the same primary req unless they
        share a capability.

        When FR-234 (fan-out) and FR-235 (pipeline) both claim REQ-YG-235,
        one of them is wrong.
        """
        fr_to_reqs = _build_fr_to_reqs()

        # Collect fragment req by FR
        fr_fragment_reqs: dict[str, set[str]] = {}
        for filepath in sorted(CHANGELOG_DIR.rglob("*.md")):
            fr_num, fragment_reqs = _parse_fragment_req(filepath)
            if not fr_num or not fragment_reqs:
                continue
            fr_fragment_reqs.setdefault(fr_num, set()).update(fragment_reqs)

        # Build reverse: REQ → set of FRs that claim it in fragments
        req_claimants: dict[str, set[str]] = {}
        for fr_num, reqs in fr_fragment_reqs.items():
            for req in reqs:
                req_claimants.setdefault(req, set()).add(fr_num)

        # For each REQ claimed by multiple FRs, check they share a capability
        collisions: list[str] = []
        for req, frs in sorted(req_claimants.items()):
            if len(frs) <= 1:
                continue
            # Check: do all these FRs map to a capability that owns this req?
            for fr in frs:
                valid = fr_to_reqs.get(fr, set())
                if req not in valid:
                    collisions.append(
                        f"{req} claimed by {fr} (fragment) but {fr} capability "
                        f"has {sorted(valid) if valid else 'no capability'}"
                    )

        assert not collisions, (
            f"Cross-FR req collisions ({len(collisions)}):\n"
            + "\n".join(f"  • {c}" for c in collisions)
        )
