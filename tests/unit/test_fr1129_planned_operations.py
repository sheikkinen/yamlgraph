"""REQ-YG-716: FR Planned Operations section replaces the Effort field (FR-1129).

Witnesses the template, its ramp mirror, and the feature-request skill:
the five-key operations contract, the no-duration rule, the marked I1
sample, and the manual completion reconciliation schema.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

TEMPLATE = Path("feature-requests/TEMPLATE.md")
MIRROR = Path("ramp/assets/tier2/feature-requests/TEMPLATE.md")
SKILL = Path(".github/skills/feature-request/SKILL.md")
PLANNING_SKILL_DIR = Path(".github/skills/planning")

BEGIN = "<!-- fr1129-planned-operations-sample:begin -->"
END = "<!-- fr1129-planned-operations-sample:end -->"
KEYS = {"probes", "branches", "delegations", "waits", "commands"}
RECONCILIATION_HEADER = (
    "| Planned operation | Outcome (ran / did not run / changed) | Witness |"
)
UNPLANNED = "**Unplanned operations:**"

DURATION = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:"
    r"ms|msecs?|milliseconds?|s|secs?|seconds?|mins?|minutes?|"
    r"h|hrs?|hours?|d|days?|w|wks?|weeks?|mos?|months?|y|yrs?|years?"
    r")\b",
    re.IGNORECASE,
)


def _headings(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith("## ")]


def _sample() -> dict:
    text = SKILL.read_text(encoding="utf-8")
    assert text.count(BEGIN) == 1 and text.count(END) == 1
    region = text.split(BEGIN, 1)[1].split(END, 1)[0]
    blocks = re.findall(r"```yaml\n(.*?)```", region, re.DOTALL)
    assert len(blocks) == 1, "exactly one fenced YAML document between markers"
    return yaml.safe_load(blocks[0])


@pytest.mark.req("REQ-YG-716")
def test_template_drops_effort_and_adds_planned_operations() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    assert "**Effort:**" not in text
    heads = _headings(text)
    idx = heads.index("## Ideal Result")
    assert heads[idx + 1] == "## Planned Operations"
    section = text.split("## Planned Operations", 1)[1].split("\n## ", 1)[0]
    assert ".github/skills/feature-request/SKILL.md" in section


@pytest.mark.req("REQ-YG-716")
def test_ramp_mirror_is_byte_identical() -> None:
    assert MIRROR.read_bytes() == TEMPLATE.read_bytes()


@pytest.mark.req("REQ-YG-716")
def test_skill_inline_template_drops_effort() -> None:
    text = SKILL.read_text(encoding="utf-8")
    after = text.split("## FR Template", 1)[1]
    inline = after.split("```markdown\n", 1)[1].split("\n```", 1)[0]
    assert "**Effort:**" not in inline
    assert "## Planned Operations" in inline


@pytest.mark.req("REQ-YG-716")
def test_no_standalone_planning_skill() -> None:
    assert not PLANNING_SKILL_DIR.exists()


@pytest.mark.req("REQ-YG-716")
def test_sample_has_exactly_the_five_keys_of_non_empty_string_lists() -> None:
    sample = _sample()
    assert set(sample) == KEYS
    for key, value in sample.items():
        assert isinstance(value, list) and value, key
        assert all(isinstance(item, str) and item.strip() for item in value), key


@pytest.mark.req("REQ-YG-716")
def test_sample_contains_no_numeric_duration() -> None:
    region = SKILL.read_text(encoding="utf-8").split(BEGIN, 1)[1].split(END, 1)[0]
    assert DURATION.findall(region) == []


@pytest.mark.req("REQ-YG-716")
@pytest.mark.parametrize(
    "text",
    [
        "2 days",
        "0.5 day",
        "30s",
        "15 MIN",
        "4h",
        "3 hrs",
        "1 wk",
        "2 months",
        "1 yr",
        "200ms",
    ],
)
def test_duration_pattern_catches_durations(text: str) -> None:
    assert DURATION.search(text)


@pytest.mark.req("REQ-YG-716")
@pytest.mark.parametrize(
    "text", ["read 10 raw issues", "1 run", "FR-899", "7,529 items"]
)
def test_duration_pattern_allows_counts(text: str) -> None:
    assert DURATION.search(text) is None


@pytest.mark.req("REQ-YG-716")
def test_skill_defines_manual_reconciliation_schema() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert RECONCILIATION_HEADER in text
    assert UNPLANNED in text
    for witness in ("audit-log", "commit", "CI run", "human decision"):
        assert witness in text, witness
