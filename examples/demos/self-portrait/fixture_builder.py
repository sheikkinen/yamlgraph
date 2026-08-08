"""FR-782 — deterministic synthetic PersonalizationPortrait fixture (R-4, C-9).

Builds a `PPSQLDatabase.db` that mirrors the documented PersonalizationPortrait
schema with obviously fake data. No real personal data ever enters git: the
committed fixture is generated exclusively by this script and every row carries
the `SYNTHETIC_MARKER`.

Usage:
    python examples/demos/self-portrait/fixture_builder.py [OUT_DB]
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

#: Every synthetic source path is prefixed with this — the no-real-data guard
#: test asserts it appears and that no `~/Library` path does.
SYNTHETIC_MARKER = "SYNTHETIC-FIXTURE"

SCHEMA = """
CREATE TABLE ne_records (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category INTEGER NOT NULL,
    initial_score REAL NOT NULL,
    language TEXT
);
CREATE TABLE tp_records (
    id INTEGER PRIMARY KEY,
    topic_id TEXT NOT NULL,
    score REAL NOT NULL,
    language TEXT
);
CREATE TABLE loc_records (
    id INTEGER PRIMARY KEY,
    clp_locality TEXT NOT NULL,
    clp_country TEXT
);
CREATE TABLE significant_contacts (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    score REAL NOT NULL,
    first_seen TEXT,
    last_seen TEXT
);
CREATE TABLE sources (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    record_count INTEGER NOT NULL
);
"""

# (name, category, score, language) — categories per models.ENTITY_CATEGORIES
ENTITIES: list[tuple[str, int, float, str | None]] = [
    ("Testeri Testinen", 1, 0.97, "fi"),
    ("Fixture Fakename", 1, 0.91, "fi"),
    ("Sample Samuelsson", 1, 0.84, "sv"),
    ("Dummy Dummerson", 1, 0.62, "en"),
    ("Placeholder Oy", 2, 0.88, "fi"),
    ("Example Industries Ltd", 2, 0.71, "en"),
    ("Fakelinna", 5, 0.79, "fi"),
    ("Mocktown", 5, 0.55, "en"),
    ("Nonexistent Notebook 9000", 8, 0.48, "en"),
    ("Imaginary Summit 2099", 9, 0.44, "en"),
    ("The Unwritten Novel", 10, 0.39, "en"),
    ("Fictional Framework", 11, 0.66, "en"),
    ("Synthetic Concept", 12, 0.33, "en"),
]

# (topic Q-ID, score, language)
TOPICS: list[tuple[str, float, str]] = [
    ("Q7913", 0.93, "en"),  # artificial intelligence
    ("Q7163", 0.81, "en"),  # functional programming
    ("Q7411", 0.74, "en"),  # Linux
    ("Q1860", 0.69, "en"),  # English language
    ("Q33", 0.58, "fi"),  # Finland
    ("Q7204", 0.41, "en"),  # object-oriented programming
]

# (locality, country)
LOCATIONS: list[tuple[str, str | None]] = [
    ("Fakelinna", "Testland"),
    ("Fakelinna", "Testland"),
    ("Fakelinna", "Testland"),
    ("Mocktown", "Testland"),
    ("Mocktown", "Testland"),
    ("Sample Harbour", "Fixtureland"),
]

# (name, score, first_seen, last_seen)
CONTACTS: list[tuple[str, float, str, str]] = [
    ("Testeri Testinen", 0.99, "2024-01-05", "2026-08-01"),
    ("Fixture Fakename", 0.87, "2024-06-11", "2026-07-30"),
    ("Sample Samuelsson", 0.52, "2025-02-20", "2026-05-14"),
]

# (source label, record_count)
SOURCES: list[tuple[str, int]] = [
    (f"{SYNTHETIC_MARKER}/Safari", 120),
    (f"{SYNTHETIC_MARKER}/AddressBook", 40),
    (f"{SYNTHETIC_MARKER}/Messages", 18),
    (f"{SYNTHETIC_MARKER}/Notes", 7),
]

DEFAULT_OUT = Path(__file__).parent / "fixture" / "PPSQLDatabase.db"


def build_fixture(out_path: Path | str = DEFAULT_OUT) -> Path:
    """Create (or recreate) the deterministic synthetic fixture database."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()

    conn = sqlite3.connect(out)
    try:
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT INTO ne_records (name, category, initial_score, language)"
            " VALUES (?, ?, ?, ?)",
            ENTITIES,
        )
        conn.executemany(
            "INSERT INTO tp_records (topic_id, score, language) VALUES (?, ?, ?)",
            TOPICS,
        )
        conn.executemany(
            "INSERT INTO loc_records (clp_locality, clp_country) VALUES (?, ?)",
            LOCATIONS,
        )
        conn.executemany(
            "INSERT INTO significant_contacts (name, score, first_seen, last_seen)"
            " VALUES (?, ?, ?, ?)",
            CONTACTS,
        )
        conn.executemany(
            "INSERT INTO sources (source, record_count) VALUES (?, ?)",
            SOURCES,
        )
        conn.commit()
    finally:
        conn.close()
    return out


def build_drifted_fixture(out_path: Path | str) -> Path:
    """Second-run fixture for diff mode (AC-09).

    Differences from `build_fixture`: one new person, one shifted topic
    score, one dropped location.
    """
    out = build_fixture(out_path)
    conn = sqlite3.connect(out)
    try:
        conn.execute(
            "INSERT INTO ne_records (name, category, initial_score, language)"
            " VALUES (?, ?, ?, ?)",
            ("Newcomer Nobody", 1, 0.95, "en"),
        )
        conn.execute("UPDATE tp_records SET score = 0.12 WHERE topic_id = 'Q7411'")
        conn.execute("DELETE FROM loc_records WHERE clp_locality = 'Sample Harbour'")
        conn.commit()
    finally:
        conn.close()
    return out


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    print(f"✓ synthetic fixture written: {build_fixture(target)}")
