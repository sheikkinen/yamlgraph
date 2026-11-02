"""FR-1155 calibration-audit reducer (REQ-YG-726, AC-08).

Reliability table + expected calibration error (ECE) over labeled
decision items. Algorithm fixed by the FR (R-3):

- 5 fixed-width confidence buckets over [0,1]: ``[0,0.2) [0.2,0.4)
  [0.4,0.6) [0.6,0.8) [0.8,1.0]`` — half-open, last closed.
- Empty buckets carry weight 0 in ECE and render with ``n=0``.
- ``ECE = Σ_b (n_b/N) * |accuracy_b − mean_confidence_b|``.
- ``flagged = ece > threshold`` (threshold configurable; the demo uses
  0.15).

Calibration is an operator onboarding gate only: this reducer reports;
nothing here certifies providers or blocks execution at runtime.
"""

from pydantic import BaseModel, ConfigDict, Field

N_BUCKETS = 5


class ReliabilityBucket(BaseModel):
    """One confidence bucket of the reliability table."""

    model_config = ConfigDict(frozen=True)

    lo: float
    hi: float
    n: int
    mean_confidence: float | None
    accuracy: float | None
    gap: float | None


class ReliabilityReport(BaseModel):
    """Serialized reliability table with ECE and threshold verdict."""

    model_config = ConfigDict(frozen=True)

    buckets: list[ReliabilityBucket]
    ece: float
    n_total: int
    threshold: float
    flagged: bool


class CalibrationItem(BaseModel):
    """One scored decision: reported confidence and observed correctness."""

    model_config = ConfigDict(frozen=True, extra="allow")

    id: str
    confidence: float = Field(ge=0.0, le=1.0)
    correct: bool


def _bucket_index(confidence: float) -> int:
    """Half-open buckets, last closed: confidence 1.0 lands in bucket 4."""
    if confidence >= 1.0:
        return N_BUCKETS - 1
    return int(confidence * N_BUCKETS)


def reliability_report(
    items: list[dict] | list[CalibrationItem],
    threshold: float,
) -> ReliabilityReport:
    """Reduce labeled decision items to a reliability table and ECE.

    Args:
        items: Scored items (``id``, ``confidence``, ``correct``).
        threshold: ECE above this flags the provider's confidence.

    Raises:
        ValueError: On an empty item list — zero evidence must never
            read as perfect calibration (Commandment 6).
    """
    if not items:
        raise ValueError("Calibration requires at least one scored item")
    parsed = [
        item if isinstance(item, CalibrationItem) else CalibrationItem(**item)
        for item in items
    ]

    grouped: dict[int, list[CalibrationItem]] = {i: [] for i in range(N_BUCKETS)}
    for item in parsed:
        grouped[_bucket_index(item.confidence)].append(item)

    n_total = len(parsed)
    buckets: list[ReliabilityBucket] = []
    ece = 0.0
    for i in range(N_BUCKETS):
        lo, hi = i / N_BUCKETS, (i + 1) / N_BUCKETS
        members = grouped[i]
        if not members:
            buckets.append(
                ReliabilityBucket(
                    lo=lo, hi=hi, n=0, mean_confidence=None, accuracy=None, gap=None
                )
            )
            continue
        mean_conf = sum(m.confidence for m in members) / len(members)
        accuracy = sum(1 for m in members if m.correct) / len(members)
        gap = abs(accuracy - mean_conf)
        ece += (len(members) / n_total) * gap
        buckets.append(
            ReliabilityBucket(
                lo=lo,
                hi=hi,
                n=len(members),
                mean_confidence=mean_conf,
                accuracy=accuracy,
                gap=gap,
            )
        )

    return ReliabilityReport(
        buckets=buckets,
        ece=ece,
        n_total=n_total,
        threshold=threshold,
        flagged=ece > threshold,
    )


def score_items(items: list[dict], decisions: dict[str, dict]) -> list[dict]:
    """Join labeled fixture items with decision answers into scored rows.

    Args:
        items: Fixture rows with ``id`` and ``expected`` (a choice label).
        decisions: Per-item answers keyed by item id; each carries the
            decision node's answer (dict or ChoiceDecision model) for the
            audited question.

    Returns:
        Rows consumable by :func:`reliability_report`.
    """
    scored = []
    for item in items:
        answer = decisions[item["id"]]
        if not isinstance(answer, dict):
            answer = answer.model_dump()
        scored.append(
            {
                "id": item["id"],
                "confidence": answer["confidence"],
                "correct": answer["choice"] == item["expected"],
            }
        )
    return scored


def score_audit(state: dict | None = None, **kwargs) -> dict:
    """Graph tool: join ``audit_items`` fixtures with the ``audit`` answers."""
    effective = state if isinstance(state, dict) else kwargs
    items = effective.get("audit_items")
    answers = effective.get("audit")
    if not items or not answers:
        raise ValueError("score_audit requires audit_items and audit in state")
    return {"scored": score_items(items, answers)}


def audit_report(state: dict | None = None, **kwargs) -> dict:
    """Graph tool: reduce ``scored`` rows to the serialized reliability report."""
    effective = state if isinstance(state, dict) else kwargs
    scored = effective.get("scored")
    if scored is None:
        raise ValueError("audit_report requires scored rows in state")
    threshold = effective.get("threshold") or 0.15
    report = reliability_report(items=scored, threshold=float(threshold))
    return {"report": report.model_dump()}
