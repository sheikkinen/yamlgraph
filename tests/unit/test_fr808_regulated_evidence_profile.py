"""FR-808 regulated evidence profile witnesses (REQ-YG-552)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from yamlgraph.models.graph_schema import validate_graph_schema
from yamlgraph.utils import route_log


def _graph(observability: dict) -> dict:
    return {
        "name": "regulated",
        "nodes": {"step": {"type": "passthrough"}},
        "edges": [
            {"from": "START", "to": "step"},
            {"from": "step", "to": "END"},
        ],
        "observability": observability,
    }


@pytest.mark.req("REQ-YG-552")
@pytest.mark.parametrize(
    "observability,match",
    [
        ({"profile": "regulated", "judgement_ref": "FR-test"}, "route_log_sink"),
        ({"profile": "regulated", "route_log_sink": "logs"}, "judgement_ref"),
        (
            {
                "profile": "regulated",
                "route_log_sink": "logs",
                "judgement_ref": "FR-test",
                "route_log": False,
            },
            "route_log",
        ),
        ({"strict_evidence": True}, "regulated"),
    ],
)
def test_regulated_profile_schema_rejects_incomplete_contract(observability, match):
    with pytest.raises(ValidationError, match=match):
        validate_graph_schema(_graph(observability))


@pytest.mark.req("REQ-YG-552")
def test_regulated_profile_writes_per_run_bound_record(tmp_path, monkeypatch):
    graph_path = tmp_path / "graph.yaml"
    sink_dir = tmp_path / "routes"
    graph_path.write_text(
        "name: regulated\nobservability:\n  profile: regulated\n"
        f"  route_log_sink: {sink_dir}\n  judgement_ref: FR-808-test\n"
        "nodes:\n  step:\n    type: passthrough\n"
        "edges:\n  - from: START\n    to: step\n  - from: step\n    to: END\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("YAMLGRAPH_ROUTE_LOG", raising=False)

    with route_log.route_run_context(graph_path) as run:
        route_log.emit_route("step", "default", "END")

    sink = sink_dir / f"{run.run_id}.route.jsonl"
    assert sink.exists()
    assert '"judgement": "FR-808-test"' in sink.read_text()


@pytest.mark.req("REQ-YG-552")
def test_regulated_file_valued_sink_fails_before_header(tmp_path, monkeypatch):
    graph_path = tmp_path / "graph.yaml"
    sink_file = tmp_path / "not-a-directory"
    sink_file.write_text("occupied", encoding="utf-8")
    graph_path.write_text(
        "name: regulated\nobservability:\n  profile: regulated\n"
        f"  route_log_sink: {sink_file}\n  judgement_ref: FR-test\n"
        "nodes:\n  step:\n    type: passthrough\n"
        "edges:\n  - from: START\n    to: step\n  - from: step\n    to: END\n",
        encoding="utf-8",
    )
    delivered = []
    monkeypatch.setattr(route_log, "_deliver_record", delivered.append)

    with (
        pytest.raises(ValueError, match="directory"),
        route_log.route_run_context(graph_path),
    ):
        pass
    assert delivered == []


@pytest.mark.req("REQ-YG-552")
def test_regulated_unwritable_sink_fails_before_header(tmp_path, monkeypatch):
    from yamlgraph.utils import regulated_evidence

    policy = regulated_evidence.RegulatedPolicy(
        enabled=True, sink_dir=tmp_path / "routes", strict=False
    )
    monkeypatch.setattr(
        Path, "write_text", lambda *args, **kwargs: (_ for _ in ()).throw(OSError())
    )
    with pytest.raises(ValueError, match="not writable"):
        regulated_evidence.preflight_regulated_sink(policy, "run-id")


@pytest.mark.req("REQ-YG-552")
def test_regulated_disable_override_and_strict_precedence(
    tmp_path, monkeypatch, caplog
):
    config = {
        "profile": "regulated",
        "route_log_sink": str(tmp_path),
        "judgement_ref": "FR-test",
        "strict_evidence": False,
    }
    monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG", "0")
    assert route_log.resolve_regulated_policy(config, "graph.yaml").enabled is True
    assert "ignored" in caplog.text

    monkeypatch.setenv("YAMLGRAPH_ROUTE_LOG_OVERRIDE", "1")
    assert route_log.resolve_regulated_policy(config, "graph.yaml").enabled is False
    assert "recorded_exception" in caplog.text

    config["strict_evidence"] = True
    with pytest.raises(ValueError, match="strict_evidence"):
        route_log.resolve_regulated_policy(config, "graph.yaml")


@pytest.mark.req("REQ-YG-552")
def test_strict_evidence_raises_at_run_boundary_after_counted_loss(
    tmp_path, monkeypatch
):
    graph_path = tmp_path / "graph.yaml"
    sink_dir = tmp_path / "routes"
    graph_path.write_text(
        "name: regulated\nobservability:\n  profile: regulated\n"
        f"  route_log_sink: {sink_dir}\n  judgement_ref: FR-test\n"
        "  strict_evidence: true\nnodes:\n  step:\n    type: passthrough\n"
        "edges:\n  - from: START\n    to: step\n  - from: step\n    to: END\n",
        encoding="utf-8",
    )
    original = route_log._deliver_record

    def fail_route(record):
        if record["event"] == "route":
            raise OSError("sink unavailable")
        original(record)

    monkeypatch.setattr(route_log, "_deliver_record", fail_route)

    with (
        pytest.raises(route_log.EvidenceLossError, match="dropped_events=1"),
        route_log.route_run_context(graph_path),
    ):
        route_log.emit_route("step", "default", "END")
