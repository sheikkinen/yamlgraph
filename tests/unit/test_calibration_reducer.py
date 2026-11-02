"""FR-1155 calibration reducer: reliability table + ECE (AC-08).

RED-first suite. The reducer lives with the calibration-audit demo
(examples/demos/calibration-audit/tools.py — hyphenated path, loaded by
file location) and is condemned here by deterministic exact-value
fixtures hand-computed in the FR (R-3) before any implementation exists
(judgement condition C-3).
"""

import importlib.util
from pathlib import Path

import pytest

pytestmark = [pytest.mark.req("REQ-YG-726"), pytest.mark.process]

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_PATH = REPO_ROOT / "examples" / "demos" / "calibration-audit" / "tools.py"


@pytest.fixture(scope="module")
def tools():
    spec = importlib.util.spec_from_file_location("calibration_audit_tools", TOOLS_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _items(confidence: float, n: int, n_correct: int) -> list[dict]:
    """n census rows at one reported confidence, n_correct of them correct."""
    return [
        {"id": f"i{confidence}-{k}", "confidence": confidence, "correct": k < n_correct}
        for k in range(n)
    ]


class TestReliabilityReport:
    def test_planted_miscalibration_flagged(self, tools):
        """FR R-3 fixture: 10 items at 0.9 confidence, 5 correct → ECE 0.4."""
        report = tools.reliability_report(
            items=_items(0.9, n=10, n_correct=5), threshold=0.15
        )
        assert report.n_total == 10
        assert report.ece == pytest.approx(0.4)
        assert report.flagged is True
        occupied = [b for b in report.buckets if b.n > 0]
        assert len(occupied) == 1
        bucket = occupied[0]
        assert (bucket.lo, bucket.hi) == (0.8, 1.0)
        assert bucket.n == 10
        assert bucket.mean_confidence == pytest.approx(0.9)
        assert bucket.accuracy == pytest.approx(0.5)
        assert bucket.gap == pytest.approx(0.4)

    def test_calibrated_fixture_not_flagged(self, tools):
        """FR R-3 fixture: 10@0.9/9 correct + 10@0.5/5 correct → ECE 0.0."""
        items = _items(0.9, n=10, n_correct=9) + _items(0.5, n=10, n_correct=5)
        report = tools.reliability_report(items=items, threshold=0.15)
        assert report.n_total == 20
        assert report.ece == pytest.approx(0.0)
        assert report.flagged is False
        occupied = {(b.lo, b.hi): b for b in report.buckets if b.n > 0}
        assert set(occupied) == {(0.8, 1.0), (0.4, 0.6)}
        assert occupied[(0.8, 1.0)].gap == pytest.approx(0.0)
        assert occupied[(0.4, 0.6)].gap == pytest.approx(0.0)

    def test_five_fixed_buckets_half_open_last_closed(self, tools):
        """Bucket rule: [0,0.2) [0.2,0.4) [0.4,0.6) [0.6,0.8) [0.8,1.0]."""
        report = tools.reliability_report(
            items=_items(1.0, n=2, n_correct=2), threshold=0.15
        )
        assert len(report.buckets) == 5
        bounds = [(b.lo, b.hi) for b in report.buckets]
        assert bounds == [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
        # confidence 1.0 lands in the closed last bucket
        assert report.buckets[-1].n == 2

    def test_empty_buckets_excluded_from_ece(self, tools):
        """Empty buckets carry weight 0; occupied-bucket ECE is unaffected."""
        report = tools.reliability_report(
            items=_items(0.9, n=4, n_correct=2), threshold=0.15
        )
        empty = [b for b in report.buckets if b.n == 0]
        assert len(empty) == 4
        assert report.ece == pytest.approx(0.4)

    def test_threshold_is_configurable(self, tools):
        report = tools.reliability_report(
            items=_items(0.9, n=10, n_correct=5), threshold=0.5
        )
        assert report.ece == pytest.approx(0.4)
        assert report.flagged is False

    def test_report_serializes(self, tools):
        """ReliabilityReport is a Pydantic model with a stable dump shape."""
        report = tools.reliability_report(
            items=_items(0.9, n=10, n_correct=5), threshold=0.15
        )
        dumped = report.model_dump()
        assert set(dumped) == {"buckets", "ece", "n_total", "threshold", "flagged"}
        assert set(dumped["buckets"][0]) == {
            "lo",
            "hi",
            "n",
            "mean_confidence",
            "accuracy",
            "gap",
        }

    def test_empty_items_raise(self, tools):
        """No silent 'perfectly calibrated' verdict from zero evidence."""
        with pytest.raises(ValueError):
            tools.reliability_report(items=[], threshold=0.15)
