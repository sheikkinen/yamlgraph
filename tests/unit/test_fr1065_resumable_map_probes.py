"""FR-1065 investigation witnesses (REQ-YG-689).

Each test pins one behavior the investigation report relies on, measured on
the minimal LangGraph fixtures in tests/fixtures/fr1065/probes.py.
"""

from __future__ import annotations

import ast
import importlib.util
import signal
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "fr1065_probes", REPO_ROOT / "tests" / "fixtures" / "fr1065" / "probes.py"
)
probes = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = probes
_SPEC.loader.exec_module(probes)

pytestmark = pytest.mark.slow


@pytest.mark.req("REQ-YG-689")
def test_sqlite_cache_holds_under_concurrent_branches(tmp_path):
    out = probes.probe_cache_in_process(str(tmp_path / "c.db"), n=200)
    assert out["errors"] == 0
    assert out["stored"] == 200


@pytest.mark.req("REQ-YG-689")
def test_sqlite_cache_persists_across_two_writer_processes(tmp_path):
    out = probes.probe_cache_two_process(str(tmp_path / "c.db"), n=100, precreate=True)
    assert out["writer_crashes"] == []
    assert out["read_back"] == 200
    assert out["pids"] == 2


@pytest.mark.req("REQ-YG-689")
def test_sqlite_cache_gives_no_lease_exclusion():
    out = probes.probe_lease("cache", rounds=3, precreate=True)
    assert out["rounds_with_two_winners"] == 3


@pytest.mark.req("REQ-YG-689")
def test_sqlite_unique_insert_lease_excludes_second_process():
    out = probes.probe_lease("sqlite", rounds=3)
    assert out["claimant_crashes"] == []
    assert out["rounds_with_two_winners"] == 0


@pytest.mark.req("REQ-YG-689")
def test_store_results_shrink_final_checkpoint(tmp_path):
    out = probes.probe_checkpoint_size(str(tmp_path), n=1000, payload=400, select=50)
    assert out["collect"]["final_checkpoint_bytes"] > 1000 * 400
    assert (
        out["store"]["final_checkpoint_bytes"]
        < out["collect"]["final_checkpoint_bytes"] / 10
    )


@pytest.mark.req("REQ-YG-689")
def test_batch_loop_bounds_peak_memory():
    out = probes.probe_batches(n=2000, batch=200)
    assert out["batched"]["count"] == out["one_step"]["count"] == 2000
    assert out["batched"]["peak_bytes"] < out["one_step"]["peak_bytes"]


@pytest.mark.req("REQ-YG-689")
def test_sigkill_mid_superstep_reruns_completed_branches(tmp_path):
    out = probes.probe_resume(str(tmp_path), signal.SIGKILL)
    assert out["completed_before_interrupt"] > 0
    assert out["completed_items_rerun"] == out["completed_before_interrupt"]
    assert out["results_equal_uninterrupted"]


@pytest.mark.req("REQ-YG-689")
def test_sigkill_in_batch_loop_loses_only_the_open_batch(tmp_path):
    out = probes.probe_resume(str(tmp_path), signal.SIGKILL, "sync", batch=4)
    assert out["completed_before_interrupt"] == 6
    assert out["completed_items_rerun"] == 2
    assert out["calls_on_resume"] == 16
    assert out["results_equal_uninterrupted"]


@pytest.mark.req("REQ-YG-689")
def test_sigint_mid_superstep_reruns_no_completed_branch(tmp_path):
    out = probes.probe_resume(str(tmp_path), signal.SIGINT)
    assert out["completed_items_rerun"] == 0
    assert out["results_equal_uninterrupted"]


@pytest.mark.req("REQ-YG-689")
def test_new_thread_reuses_no_earlier_result(tmp_path):
    out = probes.probe_cross_run(str(tmp_path), n=10)
    assert out["total_calls"] == 20


@pytest.mark.req("REQ-YG-689")
def test_cache_policy_is_inert_without_compile_cache():
    out = probes.probe_cache_policy()
    assert out == {"calls_without_cache": 2, "calls_with_in_memory_cache": 1}


@pytest.mark.req("REQ-YG-689")
def test_no_runtime_route_passes_cache_to_compile():
    offenders = []
    for path in (REPO_ROOT / "yamlgraph").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "compile"
                and any(kw.arg == "cache" for kw in node.keywords)
            ):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}")
    assert offenders == []
