"""FR-782 — PersonalizationPortrait extraction at the typed boundary.

The one law applies here: everything is normalized and asserted where the
external database enters, never downstream. Reads are read-only URI mode
(C-2); drift is loud (`SchemaDriftError`); an unreadable primary database
names its Full Disk Access remediation instead of degrading to an empty
portrait.
"""

from __future__ import annotations

import logging
import sqlite3
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

from .models import (
    ENTITY_CATEGORIES,
    ContactRow,
    DatabaseUnreadableError,
    EntityRow,
    Extraction,
    LocationRow,
    ProvenanceRow,
    SchemaDriftError,
    SourceSummary,
    SupplementarySource,
    TopicRow,
)

logger = logging.getLogger(__name__)

#: Canonical primary database location (macOS).
DEFAULT_DB_PATH = "~/Library/PersonalizationPortrait/PPSQLDatabase.db"

FDA_REMEDIATION = (
    "Cannot read the PersonalizationPortrait database at {path}.\n"
    "On macOS this database is TCC-protected: the *executing binary* "
    "(your terminal, or the python interpreter launchd runs) needs Full "
    "Disk Access.\n"
    "Grant it in System Settings → Privacy & Security → Full Disk Access, "
    "then restart that binary and re-run."
)

REQUIRED_TABLES = ("ne_records", "tp_records", "loc_records")

#: Supplementary sources are probed, never parsed under FR-782 (R-3).
SUPPLEMENTARY_SOURCES: dict[str, str] = {
    "knowledgeC.db": "Library/Application Support/Knowledge/knowledgeC.db",
    "Safari History.db": "Library/Safari/History.db",
    "Calendar.sqlitedb": "Library/Calendars/Calendar.sqlitedb",
    "WhatsApp ChatStorage.sqlite": (
        "Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite"
    ),
}


@contextmanager
def open_readonly(db_path: str):
    """Open the database in read-only URI mode, or raise a named error."""
    path = Path(db_path).expanduser()
    uri = f"file:{path}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True)
    except sqlite3.Error as exc:
        raise DatabaseUnreadableError(
            FDA_REMEDIATION.format(path=path) + f"\nUnderlying error: {exc}"
        ) from exc
    try:
        yield conn
    finally:
        conn.close()


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """Columns present in `table`; raises when the table itself is absent."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()  # noqa: S608
    if not rows:
        raise SchemaDriftError(
            f"required table {table!r} is missing from the database — "
            "PersonalizationPortrait schema drift; re-enter planning before adapting"
        )
    return {row[1] for row in rows}


def _optional(columns: set[str], name: str) -> str:
    """Select-list fragment for an optional column (NULL when absent)."""
    return name if name in columns else f"NULL AS {name}"


def _entities(conn: sqlite3.Connection, limit: int) -> list[EntityRow]:
    columns = _columns(conn, "ne_records")
    for required in ("name", "category", "initial_score"):
        if required not in columns:
            raise SchemaDriftError(
                f"ne_records is missing required column {required!r} — schema drift"
            )
    language = _optional(columns, "language")
    rows = conn.execute(
        "SELECT name, category, initial_score, "  # noqa: S608 — fixed identifiers
        f"{language} FROM ne_records ORDER BY initial_score DESC, name ASC LIMIT ?",
        (limit,),
    ).fetchall()

    entities: list[EntityRow] = []
    for name, category, score, lang in rows:
        if category not in ENTITY_CATEGORIES:
            raise SchemaDriftError(
                f"unknown ne_records.category {category!r} for entity {name!r} — "
                "PersonalizationPortrait schema drift; map it explicitly before use"
            )
        entities.append(
            EntityRow(
                name=name,
                category=ENTITY_CATEGORIES[category],
                score=float(score),
                language=lang,
            )
        )
    return entities


def _topics(conn: sqlite3.Connection, limit: int) -> list[TopicRow]:
    columns = _columns(conn, "tp_records")
    for required in ("topic_id", "score"):
        if required not in columns:
            raise SchemaDriftError(
                f"tp_records is missing required column {required!r} — schema drift"
            )
    rows = conn.execute(
        "SELECT topic_id, score FROM tp_records ORDER BY score DESC, topic_id ASC LIMIT ?",
        (limit,),
    ).fetchall()
    return [TopicRow(topic_id=str(qid), score=float(score)) for qid, score in rows]


def _locations(conn: sqlite3.Connection) -> list[LocationRow]:
    columns = _columns(conn, "loc_records")
    if "clp_locality" not in columns:
        raise SchemaDriftError(
            "loc_records is missing required column 'clp_locality' — schema drift"
        )
    country = _optional(columns, "clp_country")
    rows = conn.execute(
        f"SELECT clp_locality, {country} FROM loc_records"  # noqa: S608 — fixed identifiers
    ).fetchall()
    counts = Counter((locality, country_name) for locality, country_name in rows)
    return [
        LocationRow(locality=locality, country=country_name, visits=visits)
        for (locality, country_name), visits in sorted(
            counts.items(), key=lambda item: (-item[1], item[0][0])
        )
    ]


def _contacts(conn: sqlite3.Connection) -> list[ContactRow]:
    """Significant contacts; the table is optional across macOS versions."""
    try:
        columns = _columns(conn, "significant_contacts")
    except SchemaDriftError:
        logger.info("significant_contacts absent — inner circle section will be empty")
        return []
    score = _optional(columns, "score")
    first_seen = _optional(columns, "first_seen")
    last_seen = _optional(columns, "last_seen")
    rows = conn.execute(
        f"SELECT name, {score}, {first_seen}, {last_seen} "  # noqa: S608 — fixed identifiers
        "FROM significant_contacts ORDER BY score DESC, name ASC"
    ).fetchall()
    return [
        ContactRow(
            name=name,
            score=float(contact_score or 0.0),
            first_seen=first,
            last_seen=last,
        )
        for name, contact_score, first, last in rows
    ]


def _provenance(conn: sqlite3.Connection) -> list[ProvenanceRow]:
    """Where the device learned things; `sources` is optional."""
    try:
        columns = _columns(conn, "sources")
    except SchemaDriftError:
        logger.info("sources absent — provenance section will be empty")
        return []
    if "source" not in columns:
        raise SchemaDriftError(
            "sources is missing required column 'source' — schema drift"
        )
    count = _optional(columns, "record_count")
    rows = conn.execute(
        f"SELECT source, {count} FROM sources ORDER BY {count} DESC, source ASC"  # noqa: S608
    ).fetchall()
    return [
        ProvenanceRow(source=str(source), record_count=int(record_count or 0))
        for source, record_count in rows
    ]


def _display_path(path: Path) -> str:
    """Home-relative rendering for anything that rides in the outbound
    payload: an absolute path carries the account name (C-9)."""
    try:
        return f"~/{path.relative_to(Path.home())}"
    except ValueError:
        return str(path)


def probe_supplementary(home: Path | str | None = None) -> list[SupplementarySource]:
    """Availability probes for supplementary databases — never parsers (R-3).

    Reported paths are home-relative (`~/Library/…`): the absolute path
    carries the account name, and this list is part of the outbound
    consent payload.
    """
    root = Path(home).expanduser() if home else Path.home()
    probes: list[SupplementarySource] = []
    for name, relative in SUPPLEMENTARY_SOURCES.items():
        available = (root / relative).exists()
        probes.append(
            SupplementarySource(
                name=name,
                path=f"~/{relative}",
                available=available,
                status="present (not parsed)" if available else "absent",
            )
        )
    return probes


def extract_portrait(
    db_path: str,
    *,
    entity_limit: int = 200,
    topic_limit: int = 100,
    home: Path | str | None = None,
) -> Extraction:
    """Read the primary database into typed rows.

    Raises:
        DatabaseUnreadableError: database missing or TCC-blocked.
        SchemaDriftError: the schema differs from the asserted contract.
    """
    path = Path(db_path).expanduser()
    if not path.exists():
        raise DatabaseUnreadableError(FDA_REMEDIATION.format(path=path))

    with open_readonly(str(path)) as conn:
        for table in REQUIRED_TABLES:
            _columns(conn, table)
        entities = _entities(conn, entity_limit)
        topics = _topics(conn, topic_limit)
        locations = _locations(conn)
        contacts = _contacts(conn)
        provenance = _provenance(conn)

    summary = SourceSummary(
        db_path=_display_path(path),
        entity_count=len(entities),
        topic_count=len(topics),
        location_count=len(locations),
        contact_count=len(contacts),
        provenance=provenance,
        supplementary=probe_supplementary(home=home),
    )
    logger.info(
        "extracted %d entities, %d topics, %d locality clusters, %d contacts from %s",
        len(entities),
        len(topics),
        len(locations),
        len(contacts),
        path,
    )
    return Extraction(
        entities=entities,
        topics=topics,
        locations=locations,
        contacts=contacts,
        source_summary=summary,
    )
