"""FR-850 shared coverage-context loader: tripwire + normalization (RED).

One boundary for reading ``.coverage`` context data
(scripts/coverage_contexts.py): hard refusal on missing/context-free/
poisoned DBs, ``[param]`` suffix normalization, the shared five-class
``derive_resolution``, and measured-scope module reconciliation.
Consumed by both ``req_coverage.py --implementation`` and
``req_audit_questions.py`` — no second resolution truth (AC-01, AC-07).
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from coverage_contexts import (  # noqa: E402
    POISON_RATIO,
    CoverageContextError,
    derive_resolution,
    load_coverage_contexts,
    normalize_context,
    reconcile_modules,
)


def _make_coverage_db(
    root: Path,
    contexts: list[str],
    links: list[tuple[str, str]] = (),
) -> Path:
    """Write a minimal synthetic ``.coverage`` SQLite DB (AC-04).

    *links* is (source file absolute path, raw context string).
    """
    db_path = root / ".coverage"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        "CREATE TABLE file (id INTEGER PRIMARY KEY, path TEXT);"
        "CREATE TABLE context (id INTEGER PRIMARY KEY, context TEXT);"
        "CREATE TABLE line_bits (file_id INTEGER, context_id INTEGER, "
        "numbits BLOB);"
    )
    ctx_ids: dict[str, int] = {}
    for i, ctx in enumerate(["", *contexts], start=1):
        conn.execute("INSERT INTO context (id, context) VALUES (?, ?)", (i, ctx))
        ctx_ids[ctx] = i
    file_ids: dict[str, int] = {}
    for path, ctx in links:
        if path not in file_ids:
            file_ids[path] = len(file_ids) + 1
            conn.execute(
                "INSERT INTO file (id, path) VALUES (?, ?)", (file_ids[path], path)
            )
        conn.execute(
            "INSERT INTO line_bits (file_id, context_id, numbits) VALUES (?, ?, ?)",
            (file_ids[path], ctx_ids[ctx], b"\x01"),
        )
    conn.commit()
    conn.close()
    return db_path


@pytest.mark.req("REQ-YG-608")
class TestHardRefusal:
    """AC-03: invalid instrument state is a refusal, not a warning."""

    def test_missing_db_refuses_with_remedy(self, tmp_path: Path) -> None:
        with pytest.raises(CoverageContextError) as exc:
            load_coverage_contexts(tmp_path)
        msg = str(exc.value)
        assert "COVERAGE_CORE=ctrace" in msg
        assert "--cov-context=test" in msg
        assert "-n auto" in msg

    def test_contextless_db_refuses(self, tmp_path: Path) -> None:
        _make_coverage_db(tmp_path, contexts=[])
        with pytest.raises(CoverageContextError) as exc:
            load_coverage_contexts(tmp_path)
        assert "COVERAGE_CORE=ctrace" in str(exc.value)

    def test_poisoned_db_refuses(self, tmp_path: Path) -> None:
        """Distinct contexts < POISON_RATIO x tagged tests → refusal."""
        _make_coverage_db(
            tmp_path,
            contexts=["tests/unit/test_a.py::test_one|run"],
        )
        tagged = {f"test_x::test_{i}" for i in range(100)}
        with pytest.raises(CoverageContextError) as exc:
            load_coverage_contexts(tmp_path, tagged_test_ids=tagged)
        assert "COVERAGE_CORE=ctrace" in str(exc.value)

    def test_healthy_ratio_accepted(self, tmp_path: Path) -> None:
        contexts = [f"tests/unit/test_a.py::test_{i}|run" for i in range(50)]
        _make_coverage_db(tmp_path, contexts=contexts)
        tagged = {f"test_a::test_{i}" for i in range(100)}
        _, recorded = load_coverage_contexts(tmp_path, tagged_test_ids=tagged)
        assert len(recorded) == 50
        assert POISON_RATIO * len(tagged) <= 50


@pytest.mark.req("REQ-YG-608")
class TestNormalization:
    """AC-05: [param] suffixes normalize to marker keys at the boundary."""

    def test_param_suffix_stripped(self) -> None:
        raw = "tests/unit/test_p.py::test_q[case-1]|run"
        assert normalize_context(raw) == "test_p::test_q"

    def test_class_qualified_param_stripped(self) -> None:
        raw = "tests/unit/test_a.py::TestC::test_m[x-y[0]]|run"
        assert normalize_context(raw) == "test_a::TestC::test_m"

    def test_plain_context_unchanged(self) -> None:
        raw = "tests/unit/test_a.py::TestC::test_m|run"
        assert normalize_context(raw) == "test_a::TestC::test_m"

    def test_loader_normalizes_map_and_recorded(self, tmp_path: Path) -> None:
        ctx = "tests/unit/test_p.py::test_q[case-1]|run"
        src = str(tmp_path / "yamlgraph" / "executor.py")
        _make_coverage_db(tmp_path, contexts=[ctx], links=[(src, ctx)])
        coverage_map, recorded = load_coverage_contexts(tmp_path)
        assert "test_p::test_q" in recorded
        assert coverage_map.get("test_p::test_q") == {"yamlgraph/executor.py"}


@pytest.mark.req("REQ-YG-608")
class TestSingleDerivationTruth:
    """AC-01/AC-07: one loader, one five-class derivation."""

    def test_audit_constructor_reexports_shared_derivation(self) -> None:
        import req_audit_questions

        assert req_audit_questions.derive_resolution is derive_resolution

    def test_duplicated_readers_removed(self) -> None:
        import req_audit_questions

        from scripts import req_coverage

        assert not hasattr(req_audit_questions, "_load_recorded_contexts")
        assert not hasattr(req_coverage, "_load_coverage_map")

    def test_constructor_hard_fails_without_db(self, tmp_path: Path) -> None:
        """AC-03 applies to req_audit_questions too."""
        from req_audit_questions import collect_questions

        with pytest.raises(CoverageContextError):
            collect_questions(root=tmp_path)


@pytest.mark.req("REQ-YG-608")
class TestModuleReconciliation:
    """AC-08: never-hit only for measured yamlgraph/ declarations."""

    def test_partitions_measured_and_unmeasured(self) -> None:
        never_hit, unmeasured = reconcile_modules(
            ["yamlgraph/graph_loader.py", "yamlgraph/utils", "scripts"],
            {"yamlgraph/utils/llm_factory.py"},
        )
        assert never_hit == ["yamlgraph/graph_loader.py"]
        assert unmeasured == ["scripts"]

    def test_directory_prefix_counts_as_hit(self) -> None:
        never_hit, _ = reconcile_modules(
            ["yamlgraph/utils"], {"yamlgraph/utils/fsm/engine.py"}
        )
        assert never_hit == []

    def test_exact_file_hit(self) -> None:
        never_hit, _ = reconcile_modules(
            ["yamlgraph/executor.py"], {"yamlgraph/executor.py"}
        )
        assert never_hit == []


@pytest.mark.req("REQ-YG-608")
class TestReportSummary:
    """AC-06/AC-09: five-class split with honest denominator, question-headed."""

    def test_summary_names_all_five_classes_and_total(self) -> None:
        from scripts import req_coverage

        counts = {
            "coverage": 3,
            "ast": 2,
            "doc-witness": 1,
            "no-link-ran": 0,
            "no-link-unrecorded": 4,
        }
        line = req_coverage.format_resolution_summary(counts, 10)
        for cls in counts:
            assert cls in line
        assert "10" in line

    def test_summary_rejects_dishonest_denominator(self) -> None:
        from scripts import req_coverage

        counts = {
            "coverage": 1,
            "ast": 0,
            "doc-witness": 0,
            "no-link-ran": 0,
            "no-link-unrecorded": 0,
        }
        with pytest.raises(ValueError):
            req_coverage.format_resolution_summary(counts, 99)

    def test_question_headings_defined(self) -> None:
        from scripts import req_coverage

        for const in (
            req_coverage.QUESTION_LINKAGE,
            req_coverage.QUESTION_TRUST,
            req_coverage.QUESTION_MODULES,
        ):
            assert isinstance(const, str)
            assert const.endswith("?")


@pytest.mark.req("REQ-YG-608")
class TestDerivationClasses:
    """The shared derivation keeps the frozen five-class enum (AC-10 guard)."""

    def test_coverage_wins(self) -> None:
        cls, files = derive_resolution(
            "test_a::test_x", {"test_a::test_x": {"yamlgraph/cli.py"}}, set(), None
        )
        assert cls == "coverage"
        assert files == ["yamlgraph/cli.py"]

    def test_unrecorded_when_absent_everywhere(self) -> None:
        cls, files = derive_resolution("test_a::test_x", {}, set(), None)
        assert cls == "no-link-unrecorded"
        assert files == []
