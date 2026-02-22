# Feature Request: FR-074 Outcaller Test & Traceability Fixes

**Priority:** HIGH
**Type:** Bug Fix / Quality
**Status:** Approved
**Effort:** 0.5 day
**Requested:** 2026-02-22
**Judged:** 2026-02-22

---

## Summary

Fix the defects surfaced by the Inquisition audit of `projects/outcaller` and FR-071/FR-072.
Two unit tests fail due to MagicMock truthy defaults, `req_coverage.py` is blind to
class-level `@pytest.mark.req` decorators (hiding 21 tests from the traceability report),
integration tests validate an obsolete batch STT code path, and `server.py` has a ruff
SIM105 violation.

---

## Problem

### 1. Two unit tests fail (MagicMock truthy `is_disconnected`)

Both `test_speak_generates_tts_and_sends` and `test_listen_raises_on_no_loop` fail because
`MagicMock()` attributes are truthy by default. When `speak()` and
`listen_and_transcribe()` check `session.is_disconnected`, the mock returns a truthy
`MagicMock` object, short-circuiting into the "Call disconnected" early-exit path before
the tested logic executes.

```
FAILED test_speak_generates_tts_and_sends - assert '' == 'Hello!'
  📴 Call disconnected - cannot speak

FAILED test_listen_raises_on_no_loop - DID NOT RAISE CallHangupError
  📴 Call disconnected - cannot listen
```

**Root cause:** Missing `mock_session.is_disconnected = False` in test setup.
**File:** `tests/unit/test_telco_nodes.py` lines 137, 219.

### 2. `req_coverage.py` ignores class-level `@pytest.mark.req`

The `extract_req_markers()` function in `scripts/req_coverage.py` only inspects decorators
on `FunctionDef` nodes, not `ClassDef` nodes. All 7 test classes in `test_telco_nodes.py`
place `@pytest.mark.req("REQ-YG-XXX")` on the class, not individual methods:

```python
@pytest.mark.req("REQ-YG-078")
class TestInitiateCall:
    def test_missing_stream_url_raises(self): ...
    def test_phone_required(self): ...
    def test_initiates_call_and_waits(self): ...
```

**Impact:** 21 unit tests (7 classes) are invisible to the traceability report. CAP-27
shows 9 tests (all integration) instead of ~30.

**File:** `scripts/req_coverage.py`, function `extract_req_markers()` around line 175.

### 3. Integration test REQ-YG-080 validates obsolete batch STT

`tests/integration/test_telco_elevenlabs.py` tagged `@pytest.mark.req("REQ-YG-080")` still
tests the batch REST `scribe_v1` endpoint:

```python
response = httpx.post(
    "https://api.elevenlabs.io/v1/speech-to-text",
    data={"model_id": "scribe_v1"},
)
```

The implementation now uses `scribe_v2_realtime` WebSocket via the ElevenLabs SDK. The
integration test validates a code path that no longer exists in production code. REQ-YG-080
states: *"listen_and_transcribe node streams Twilio audio to ElevenLabs scribe_v2_realtime"*.

**File:** `tests/integration/test_telco_elevenlabs.py` lines 104, 169, 173, 223, 227.

### 4. Ruff SIM105 in `server.py`

Bare `try/except CancelledError: pass` should use `contextlib.suppress()`.

**File:** `projects/outcaller/server.py` line 108.

### 5. FR-071 ID collision

Two different features share the FR-071 identifier:
- `feature-requests/FR-071-thinking-budget-graph-level.md` — Graph-Level Thinking Budget
- `projects/outcaller/071-telco-voice-call-demo.md` — Telco Voice Call Demo

The telco demo FR never received a proper ID in `feature-requests/`. Code comments in
`twilio_call.py`, `coordinator.py`, and `server.py` all reference "FR-071" meaning the
telco demo.

### 6. `twilio_call.py` at 448 lines (target < 400)

Within hard max (450) but violates the 400-line target. Not blocking but noted for future
refactoring into `tts.py` / `stt.py` submodules.

---

## Proposed Solution

### Fix 1: Unit test mock setup

Add `mock_session.is_disconnected = False` in both failing tests:

```python
# test_speak_generates_tts_and_sends
mock_session = MagicMock()
mock_session.is_disconnected = False  # ← add

# test_listen_raises_on_no_loop
mock_session = MagicMock()
mock_session.loop = None
mock_session.is_disconnected = False  # ← add
```

### Fix 2: `req_coverage.py` — propagate class-level markers to methods

In `extract_req_markers()`, when processing a `ClassDef`, extract any `@pytest.mark.req`
from the class decorator list and apply those requirement IDs to every `test_*` method
within the class:

```python
for node in ast.iter_child_nodes(tree):
    if isinstance(node, ast.ClassDef):
        # NEW: extract class-level @pytest.mark.req decorators
        class_reqs: list[str] = []
        for decorator in node.decorator_list:
            class_reqs.extend(_extract_req_from_decorator(decorator))

        for item in node.body:
            if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                _process_func(item, node.name, class_reqs)  # pass class_reqs
```

### Fix 3: Update integration test for REQ-YG-080

Replace the batch `scribe_v1` test with a `scribe_v2_realtime` integration test that
validates the SDK streaming path. If the realtime WebSocket test is too complex for CI,
update the docstring and `@pytest.mark.req` tag to reflect what is actually tested (e.g.,
test audio generation only, tag as REQ-YG-079).

### Fix 4: Ruff SIM105 in `server.py`

```python
# Before
try:
    await send_task
except asyncio.CancelledError:
    pass

# After
import contextlib
with contextlib.suppress(asyncio.CancelledError):
    await send_task
```

### Fix 5: FR-071 ID collision (documentation only)

Rename `projects/outcaller/071-telco-voice-call-demo.md` to clarify it is a local project
doc, not a tracked FR. Add a note at the top: *"Note: This is a project-local design doc.
The `feature-requests/FR-071` ID belongs to Graph-Level Thinking Budget."*

---

## Acceptance Criteria

- [ ] `pytest tests/unit/test_telco_nodes.py` — 21/21 pass (0 failures)
- [ ] `python scripts/req_coverage.py --detail` shows unit tests from `test_telco_nodes.py` under REQ-YG-078–082
- [ ] CAP-27 test count increases from 9 to ~30
- [ ] `ruff check projects/outcaller/` — 0 errors
- [ ] Integration test `test_telco_elevenlabs.py::TestElevenLabsSTT` docstring and REQ tag accurately describe what is tested
- [ ] FR-071 ID collision documented or resolved

---

## Constraints

- No changes to production code (`twilio_call.py`, `coordinator.py`, `server.py` logic)
  except the ruff SIM105 fix in `server.py`
- No changes to `graph.yaml` or `prompts/`
- `req_coverage.py` fix must not break existing test-req mappings (method-level markers
  still take precedence; class-level markers are additive)

---

## Related

- `feature-requests/FR-072-outcaller-streaming-voice-pipeline.md` — FR-072 cannot be marked
  Complete until these test failures are fixed
- `tests/unit/test_telco_nodes.py` — 2 failing tests
- `scripts/req_coverage.py` — class-level marker blindness
- `tests/integration/test_telco_elevenlabs.py` — stale batch STT test
- `projects/outcaller/server.py` — ruff violation
