"""
Standalone proof: extract_event fails on plain dicts.

Theory:
  The judge copilot node stores CopilotResult (Pydantic model) in graph state.
  When LangGraph's ainvoke returns the final state dict, the TypedDict annotation
  `judge_result: dict` causes the value to arrive as a plain Python dict
  (not a Pydantic model). extract_event() only handles str and Pydantic models;
  it cannot find APPROVE inside a plain dict, so it returns None and the FSM
  falls back to success_event = "error".

Run:
  python tmp/test_extract_event_dict_bug.py
"""

import sys
from pathlib import Path

# Make yamlgraph importable without install
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yamlgraph.models.schemas import CopilotResult
from yamlgraph.utils.fsm.helpers import extract_event

EVENT_MAP = {
    "approve": "approve",
    "amend": "revise",
    "reject": "reject",
    "split": "revise",
}

VERDICTS = [
    "APPROVE\nThis FR is clear and minimal. Scope frozen.",
    "AMEND\nItem 3 lacks measurable acceptance criteria.",
    "REJECT\nProblem is not real; existing abstractions suffice.",
    "SPLIT\nTwo orthogonal concerns bundled.",
]

OK = "\033[32mPASS\033[0m"  # noqa: S105 — ANSI colour label, not a credential
FAIL = "\033[31mFAIL\033[0m"


def run():
    failures = 0

    print("=" * 60)
    print("Case 1: extract_event receives a CopilotResult Pydantic instance")
    print("  (what used to work before LangGraph state serialization)")
    print("=" * 60)
    for verdict_text in VERDICTS:
        cr = CopilotResult(output=verdict_text, exit_code=0, backend="cli")
        result = extract_event(cr, EVENT_MAP)
        expected_key = verdict_text.split("\n")[0].lower()
        expected = EVENT_MAP.get(expected_key)
        ok = result == expected
        status = OK if ok else FAIL
        print(
            f"  [{status}] input={verdict_text[:20]!r}... → {result!r}  (expected {expected!r})"
        )
        if not ok:
            failures += 1

    print()
    print("=" * 60)
    print("Case 2: extract_event receives a plain dict (CopilotResult.model_dump())")
    print("  (what LangGraph returns when TypedDict annotation is `dict`)")
    print("=" * 60)
    for verdict_text in VERDICTS:
        cr = CopilotResult(output=verdict_text, exit_code=0, backend="cli")
        as_dict = cr.model_dump()  # ← what ainvoke returns after serialization
        result = extract_event(as_dict, EVENT_MAP)
        expected_key = verdict_text.split("\n")[0].lower()
        expected = EVENT_MAP.get(expected_key)
        ok = result == expected
        # We EXPECT this to fail (None) — that's the bug we're proving
        status = OK if not ok and result is None else FAIL
        print(
            f"  [BUG {'confirmed' if not ok else 'gone'}] input={verdict_text[:20]!r}... → {result!r}  (expected {expected!r}, got None=bug)"
        )

    print()
    print("=" * 60)
    print("Case 3: LangGraph state simulation — ainvoke returns full state dict")
    print('  result = {"judge_result": <CopilotResult or plain dict>}')
    print("=" * 60)

    # In graph_runner._resolve_event:
    #   if event_map and event_key and isinstance(result, dict):
    #       mapped = extract_event(result.get(event_key), event_map)
    event_key = "judge_result"

    for label, value_factory in [
        (
            "Pydantic instance",
            lambda t: CopilotResult(output=t, exit_code=0, backend="cli"),
        ),
        (
            "plain dict     ",
            lambda t: CopilotResult(output=t, exit_code=0, backend="cli").model_dump(),
        ),
    ]:
        verdict_text = "APPROVE\nThis FR is clear, minimal, frozen."
        result_state = {event_key: value_factory(verdict_text)}
        mapped = extract_event(result_state.get(event_key), EVENT_MAP)
        ok = mapped == "approve"
        status = OK if ok else FAIL
        print(f"  [{status}] {label}: extract_event → {mapped!r}")
        if not ok:
            failures += 1

    print()
    if failures == 0:
        print("⚠️  All expected behaviors confirmed.")
        print("   Case 2 proves the bug: plain dict → None → event=error")
        print("   Case 3 confirms the production failure path.")
    else:
        print(f"❌ {failures} unexpected result(s)")

    return failures


if __name__ == "__main__":
    sys.exit(run())
