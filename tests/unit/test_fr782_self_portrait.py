"""FR-782 — user self-portrait example: typed extraction, Wikidata resolution,
exact-payload consent gate, render/diff, and the no-real-data guard.

RED-first suite. Requirement: REQ-YG-584 (CAP-223).

Every test runs against the deterministic synthetic fixture — never against a
real PersonalizationPortrait database (judgement C-3).
"""

from __future__ import annotations

import importlib
import json
import sqlite3
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
DEMO = REPO / "examples" / "demos" / "self-portrait"
FIXTURE_DB = DEMO / "fixture" / "PPSQLDatabase.db"
GRAPH = DEMO / "graph.yaml"
PROMPT = DEMO / "prompts" / "synthesize_portrait.yaml"


def _mod(name: str):
    return importlib.import_module(f"examples.demos.self-portrait.{name}")


@pytest.fixture
def db(tmp_path: Path) -> Path:
    """A disposable copy of the synthetic fixture (committed copy untouched)."""
    builder = _mod("fixture_builder")
    return builder.build_fixture(tmp_path / "PPSQLDatabase.db")


# ─── AC-03: synthetic fixture + no-real-data guard ───────────────────────


@pytest.mark.req("REQ-YG-584")
def test_committed_fixture_exists_and_is_synthetic():
    assert FIXTURE_DB.exists(), "committed synthetic fixture missing"
    blob = FIXTURE_DB.read_bytes()
    assert b"SYNTHETIC-FIXTURE" in blob
    assert b"/Users/" not in blob
    assert b"Library/PersonalizationPortrait" not in blob


@pytest.mark.req("REQ-YG-584")
def test_fixture_covers_every_required_category(db: Path):
    conn = sqlite3.connect(db)
    try:
        categories = {row[0] for row in conn.execute("SELECT category FROM ne_records")}
        counts = {
            "tp_records": conn.execute("SELECT COUNT(*) FROM tp_records").fetchone()[0],
            "loc_records": conn.execute("SELECT COUNT(*) FROM loc_records").fetchone()[
                0
            ],
            "contacts": conn.execute(
                "SELECT COUNT(*) FROM significant_contacts"
            ).fetchone()[0],
            "sources": conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0],
        }
    finally:
        conn.close()
    assert {1, 2, 5, 8, 9, 10, 11, 12} <= categories
    assert all(count > 0 for count in counts.values()), counts


@pytest.mark.req("REQ-YG-584")
def test_fixture_builder_is_deterministic(tmp_path: Path):
    builder = _mod("fixture_builder")
    first = builder.build_fixture(tmp_path / "a.db").read_bytes()
    second = builder.build_fixture(tmp_path / "b.db").read_bytes()
    assert first == second


@pytest.mark.req("REQ-YG-584")
def test_demo_witness_contains_no_real_paths():
    log = DEMO / "demo-output.log"
    assert log.exists(), "demo-output.log missing (AC-11)"
    text = log.read_text(encoding="utf-8")
    assert "Library/PersonalizationPortrait" not in text
    assert "SYNTHETIC-FIXTURE" in text or "fixture" in text


# ─── AC-04: typed extraction at the SQLite boundary ──────────────────────


@pytest.mark.req("REQ-YG-584")
def test_extract_returns_typed_rows(db: Path):
    extraction = _mod("extract").extract_portrait(str(db))
    people = [e for e in extraction.entities if e.category == "person"]
    assert people, "no person entities extracted"
    assert people[0].score >= people[-1].score, "entities must be score-ranked"
    assert {t.topic_id for t in extraction.topics} >= {"Q7913"}
    assert any(
        loc.locality == "Fakelinna" and loc.visits == 3 for loc in extraction.locations
    )
    assert extraction.contacts[0].name == "Testeri Testinen"
    assert extraction.source_summary.entity_count == len(extraction.entities)
    assert extraction.source_summary.provenance


@pytest.mark.req("REQ-YG-584")
def test_extract_maps_every_documented_category(db: Path):
    extraction = _mod("extract").extract_portrait(str(db))
    assert {e.category for e in extraction.entities} == {
        "person",
        "organization",
        "place",
        "product",
        "event",
        "creative_work",
        "technology",
        "concept",
    }


@pytest.mark.req("REQ-YG-584")
def test_unknown_category_raises_schema_drift(db: Path):
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO ne_records (name, category, initial_score) VALUES (?, ?, ?)",
        ("Drifted Entity", 77, 0.5),
    )
    conn.commit()
    conn.close()
    models = _mod("models")
    with pytest.raises(models.SchemaDriftError, match="77"):
        _mod("extract").extract_portrait(str(db))


@pytest.mark.req("REQ-YG-584")
def test_missing_optional_column_still_extracts(db: Path):
    conn = sqlite3.connect(db)
    conn.executescript(
        "ALTER TABLE ne_records DROP COLUMN language;"
        "ALTER TABLE significant_contacts DROP COLUMN first_seen;"
    )
    conn.close()
    extraction = _mod("extract").extract_portrait(str(db))
    assert extraction.entities
    assert extraction.entities[0].language is None
    assert extraction.contacts[0].first_seen is None


@pytest.mark.req("REQ-YG-584")
def test_missing_required_table_raises_schema_drift(db: Path):
    conn = sqlite3.connect(db)
    conn.executescript("DROP TABLE ne_records;")
    conn.close()
    models = _mod("models")
    with pytest.raises(models.SchemaDriftError, match="ne_records"):
        _mod("extract").extract_portrait(str(db))


@pytest.mark.req("REQ-YG-584")
def test_missing_database_names_full_disk_access_remediation(tmp_path: Path):
    models = _mod("models")
    with pytest.raises(models.DatabaseUnreadableError) as excinfo:
        _mod("extract").extract_portrait(str(tmp_path / "absent.db"))
    message = str(excinfo.value)
    assert "Full Disk Access" in message
    assert "Privacy & Security" in message


@pytest.mark.req("REQ-YG-584")
def test_extraction_opens_database_read_only(db: Path):
    extract = _mod("extract")
    with (
        extract.open_readonly(str(db)) as conn,
        pytest.raises(sqlite3.OperationalError, match="readonly"),
    ):
        conn.execute("DELETE FROM ne_records")


@pytest.mark.req("REQ-YG-584")
def test_output_dir_confinement_rejects_escape(tmp_path: Path):
    io_mod = _mod("portrait_io")
    root = tmp_path / "out"
    assert io_mod.confined_path(root, "self-portrait.json").parent == root.resolve()
    with pytest.raises(ValueError, match="outside the output directory"):
        io_mod.confined_path(root, "../escaped.json")


# ─── AC-05: supplementary sources are probes only ────────────────────────


@pytest.mark.req("REQ-YG-584")
def test_supplementary_sources_absent_do_not_fail(tmp_path: Path):
    probes = _mod("extract").probe_supplementary(home=tmp_path)
    names = {p.name for p in probes}
    assert {
        "knowledgeC.db",
        "Safari History.db",
        "Calendar.sqlitedb",
        "WhatsApp ChatStorage.sqlite",
    } <= names
    assert all(
        p.available is False and p.status in {"absent", "not configured"}
        for p in probes
    )


@pytest.mark.req("REQ-YG-584")
def test_present_supplementary_source_is_not_parsed(tmp_path: Path):
    target = tmp_path / "Library" / "Application Support" / "Knowledge"
    target.mkdir(parents=True)
    (target / "knowledgeC.db").write_bytes(b"")
    probes = _mod("extract").probe_supplementary(home=tmp_path)
    knowledge = next(p for p in probes if p.name == "knowledgeC.db")
    assert knowledge.available is True
    assert knowledge.status == "present (not parsed)"


@pytest.mark.req("REQ-YG-584")
def test_supplementary_probe_paths_never_carry_the_account_name(
    tmp_path: Path, db: Path
):
    """The probe list rides along in the outbound payload — no home paths."""
    io_mod = _mod("portrait_io")
    extraction = _mod("extract").extract_portrait(str(db))
    _, envelope = io_mod.build_payload(extraction, tmp_path, portrait_date="2026-08-08")
    home = str(Path.home())
    assert home not in envelope.payload_json
    assert all(s.path.startswith("~/") for s in extraction.source_summary.supplementary)


# ─── AC-06: Wikidata batching, cache, offline degradation ────────────────


@pytest.mark.req("REQ-YG-584")
def test_wikidata_batches_at_fifty(tmp_path: Path):
    wikidata = _mod("wikidata")
    calls: list[list[str]] = []

    def fake_fetch(qids, language):
        calls.append(list(qids))
        return {q: f"label-{q}" for q in qids}

    qids = [f"Q{i}" for i in range(1, 52)]
    labels = wikidata.resolve_labels(qids, cache_dir=tmp_path, fetch=fake_fetch)
    assert [len(batch) for batch in calls] == [50, 1]
    assert labels["Q51"] == "label-Q51"


@pytest.mark.req("REQ-YG-584")
def test_wikidata_cache_hit_forbids_network(tmp_path: Path):
    wikidata = _mod("wikidata")
    wikidata.resolve_labels(
        ["Q42"], cache_dir=tmp_path, fetch=lambda qids, language: {"Q42": "Answer"}
    )

    def forbidden(qids, language):
        raise AssertionError("network used on cache hit")

    assert wikidata.resolve_labels(["Q42"], cache_dir=tmp_path, fetch=forbidden) == {
        "Q42": "Answer"
    }


@pytest.mark.req("REQ-YG-584")
def test_wikidata_offline_keeps_q_ids(tmp_path: Path):
    wikidata = _mod("wikidata")

    def failing(qids, language):
        raise OSError("offline")

    assert wikidata.resolve_labels(["Q42"], cache_dir=tmp_path, fetch=failing) == {}


@pytest.mark.req("REQ-YG-584")
def test_wikidata_missing_language_label_keeps_q_id(tmp_path: Path, db: Path):
    wikidata = _mod("wikidata")
    labels = wikidata.resolve_labels(
        ["Q7913", "Q33"],
        cache_dir=tmp_path,
        fetch=lambda qids, language: {"Q7913": "AI"},
    )
    extraction = _mod("extract").extract_portrait(str(db))
    enriched = wikidata.apply_labels(extraction.topics, labels)
    by_id = {t.topic_id: t for t in enriched}
    assert by_id["Q7913"].label == "AI"
    assert by_id["Q33"].label is None


@pytest.mark.req("REQ-YG-584")
def test_wikidata_uses_standard_library_http_only():
    source = (DEMO / "wikidata.py").read_text(encoding="utf-8")
    assert "import requests" not in source
    assert "urllib.request" in source


# ─── AC-07: exact outbound-payload consent identity ──────────────────────


@pytest.mark.req("REQ-YG-584")
def test_consent_envelope_hashes_the_exact_outbound_payload(tmp_path: Path, db: Path):
    io_mod = _mod("portrait_io")
    extraction = _mod("extract").extract_portrait(str(db))
    payload, envelope = io_mod.build_payload(
        extraction, tmp_path, portrait_date="2026-08-08"
    )

    written = Path(envelope.payload_path).read_bytes()
    assert written == envelope.payload_json.encode("utf-8")
    assert envelope.byte_count == len(written)
    assert envelope.sha256 == io_mod.sha256_hex(written)
    assert json.loads(envelope.payload_json)["schema_version"] == payload.schema_version


@pytest.mark.req("REQ-YG-584")
def test_synthesis_input_is_byte_identical_to_preview(tmp_path: Path, db: Path):
    io_mod = _mod("portrait_io")
    extraction = _mod("extract").extract_portrait(str(db))
    _, envelope = io_mod.build_payload(extraction, tmp_path, portrait_date="2026-08-08")
    verified = io_mod.verify_payload_identity(envelope.model_dump())
    assert verified.encode("utf-8") == Path(envelope.payload_path).read_bytes()


@pytest.mark.req("REQ-YG-584")
def test_tampered_payload_file_blocks_synthesis(tmp_path: Path, db: Path):
    io_mod = _mod("portrait_io")
    models = _mod("models")
    extraction = _mod("extract").extract_portrait(str(db))
    _, envelope = io_mod.build_payload(extraction, tmp_path, portrait_date="2026-08-08")
    Path(envelope.payload_path).write_text(
        '{"schema_version": "tampered"}', encoding="utf-8"
    )
    with pytest.raises(models.ConsentPayloadMismatchError):
        io_mod.verify_payload_identity(envelope.model_dump())


@pytest.mark.req("REQ-YG-584")
def test_consent_summary_exposes_counts_hash_and_payload_path(tmp_path: Path, db: Path):
    tools = _mod("tools")
    state = {
        "db_path": str(db),
        "output_dir": str(tmp_path),
        "portrait_date": "2026-08-08",
    }
    state.update(tools.extract_sources(state))
    state.update(tools.enrich_topics(state))
    result = tools.build_synthesis_payload(state)
    summary = result["consent_summary"]
    envelope = result["consent"]
    assert envelope["sha256"] in summary
    assert str(envelope["byte_count"]) in summary
    assert envelope["payload_path"] in summary
    assert "person" in summary


@pytest.mark.req("REQ-YG-584")
def test_denied_consent_renders_extraction_only(tmp_path: Path, db: Path):
    tools = _mod("tools")
    state = {
        "db_path": str(db),
        "output_dir": str(tmp_path),
        "portrait_date": "2026-08-08",
    }
    state.update(tools.extract_sources(state))
    state.update(tools.enrich_topics(state))
    state.update(tools.build_synthesis_payload(state))
    outputs = tools.render_extraction_only(state)["outputs"]
    written = Path(outputs["markdown_path"]).read_text(encoding="utf-8")
    assert "not synthesized" in written.lower()
    assert not (tmp_path / "self-portrait.json").exists()


# ─── AC-02 / AC-07: graph contract ───────────────────────────────────────


@pytest.mark.req("REQ-YG-584")
def test_graph_declares_checkpointer_and_consent_interrupt():
    config = yaml.safe_load(GRAPH.read_text(encoding="utf-8"))
    assert config["checkpointer"]["type"] in {"memory", "sqlite"}
    interrupts = [n for n, c in config["nodes"].items() if c.get("type") == "interrupt"]
    assert interrupts == ["confirm_egress"]
    assert config["nodes"]["confirm_egress"]["resume_key"] == "consent_answer"
    assert "auto_approve" in config["state"]


@pytest.mark.req("REQ-YG-584")
def test_graph_routes_auto_approve_around_the_interrupt():
    config = yaml.safe_load(GRAPH.read_text(encoding="utf-8"))
    conditions = [e.get("condition", "") for e in config["edges"]]
    assert any("auto_approve" in c for c in conditions)
    assert any("consent_answer" in c for c in conditions)


@pytest.mark.req("REQ-YG-584")
def test_graph_compiles():
    from yamlgraph.compile.graph_loader import load_graph_config

    config = load_graph_config(str(GRAPH))
    assert config.name == "self-portrait"


@pytest.mark.req("REQ-YG-584")
def test_synthesis_prompt_declares_frozen_schema_fields():
    prompt = yaml.safe_load(PROMPT.read_text(encoding="utf-8"))
    fields = set(prompt["schema"]["fields"])
    assert {
        "identity",
        "social_graph",
        "expertise",
        "geography",
        "rhythms",
        "evolution",
        "agent_briefing",
    } <= fields


# ─── AC-08: stable JSON contract + narrative render ──────────────────────


def _portrait() -> dict:
    return {
        "identity": "Synthetic operator",
        "social_graph": ["Testeri Testinen — inner circle"],
        "expertise": ["synthetic testing"],
        "geography": "Home base: Fakelinna",
        "rhythms": "Evening builder",
        "evolution": "Linux interest fading",
        "agent_briefing": "The user prefers terse, evidence-backed answers.",
    }


@pytest.mark.req("REQ-YG-584")
def test_render_writes_frozen_json_contract(tmp_path: Path, db: Path):
    io_mod = _mod("portrait_io")
    extraction = _mod("extract").extract_portrait(str(db))
    payload, _ = io_mod.build_payload(extraction, tmp_path, portrait_date="2026-08-08")
    outputs = io_mod.render_outputs(_portrait(), payload, tmp_path)

    data = json.loads(Path(outputs["json_path"]).read_text(encoding="utf-8"))
    assert set(data) == {
        "schema_version",
        "portrait_date",
        "generated_at",
        "source_summary",
        "identity",
        "social_graph",
        "expertise",
        "geography",
        "rhythms",
        "evolution",
        "agent_briefing",
        "provenance",
    }
    assert data["agent_briefing"].startswith("The user")
    narrative = Path(outputs["markdown_path"]).read_text(encoding="utf-8")
    assert "Agent Briefing" in narrative
    assert "Fakelinna" in narrative


# ─── AC-09: diff mode ────────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-584")
def test_second_run_diff_reports_new_person_shifted_topic_dropped_location(
    tmp_path: Path,
):
    builder = _mod("fixture_builder")
    extract = _mod("extract")
    io_mod = _mod("portrait_io")
    out = tmp_path / "out"

    first_db = builder.build_fixture(tmp_path / "first.db")
    payload_a, _ = io_mod.build_payload(
        extract.extract_portrait(str(first_db)), out, portrait_date="2026-08-01"
    )
    io_mod.render_outputs(_portrait(), payload_a, out)

    second_db = builder.build_drifted_fixture(tmp_path / "second.db")
    payload_b, _ = io_mod.build_payload(
        extract.extract_portrait(str(second_db)), out, portrait_date="2026-08-08"
    )
    outputs = io_mod.render_outputs(_portrait(), payload_b, out)

    diff = Path(outputs["diff_path"]).read_text(encoding="utf-8")
    assert "Newcomer Nobody" in diff
    assert "Q7411" in diff
    assert "Sample Harbour" in diff
