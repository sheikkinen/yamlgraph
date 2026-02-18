# Plan: SkipReport (FR-044a)

**Status:** IMPLEMENTED
**Implemented:** 2026-02-18

## Implementation Summary

- Created `yamlgraph/contrib/progress.py` with `SkipReport` class (~90 lines)
- Added 5 tests in `tests/unit/test_contrib_progress.py`
- Added REQ-YG-071 to ARCHITECTURE.md and req_coverage.py
- Wired into `projects/innovators_toolkit/nodes/assemble_report.py`
- Updated `reference/contrib.md` with SkipReport documentation

**Files created:**
- `yamlgraph/contrib/progress.py`
- `tests/unit/test_contrib_progress.py`

**Files modified:**
- `yamlgraph/contrib/__init__.py` — exports SkipReport
- `ARCHITECTURE.md` — added REQ-YG-071
- `scripts/req_coverage.py` — extended ALL_REQS to 72, added REQ-YG-071 to CAP-20
- `projects/innovators_toolkit/nodes/assemble_report.py` — added SkipReport integration
- `reference/contrib.md` — added SkipReport documentation

---

Bare-bones plan for `on_error: skip` visibility.

## Use Case

**innovators_toolkit** — 9 nodes with `on_error: skip` in a fan-out/fan-in diamond. When a tool fails, `assemble_report.py` line 51 (`if not content: continue`) silently omits the section. The report has 6 sections instead of 9 — nobody knows 3 failed.

**Current error flow:**
1. LLM node fails → `llm_nodes.py:186` catches, sets `state_key: None`, appends `PipelineError` to `state["errors"]`
2. `assemble_report.py` checks `state.get(key)` — `None` → `continue` (silent)
3. Report written. No mention of skips.

**`PipelineError` already captures:** node name, error type, message, timestamp, retryable flag. The data exists in `state["errors"]` — nobody reads it.

## What to Build

### `yamlgraph/contrib/progress.py` (~40 lines)

```python
from yamlgraph.models import PipelineError

class SkipReport:
    """Report on skipped nodes from state errors."""

    def __init__(self, errors: list[PipelineError], total_nodes: int | None = None):
        self.errors = errors
        self.total_nodes = total_nodes
        self.skipped = [e for e in errors]  # all errors from skip nodes

    @classmethod
    def from_state(cls, state: dict, node_keys: list[str] | None = None) -> "SkipReport":
        """Build from graph state. node_keys = expected state keys to check."""
        errors = list(state.get("errors") or [])
        total = len(node_keys) if node_keys else None
        return cls(errors=errors, total_nodes=total)

    @property
    def count(self) -> int:
        return len(self.skipped)

    def summary(self) -> str:
        """Human-readable summary."""
        if not self.skipped:
            return "All nodes completed successfully."
        parts = [f"{e.node}: {e.message}" for e in self.skipped]
        total = f"/{self.total_nodes}" if self.total_nodes else ""
        return f"⚠ {self.count}{total} skipped: [{', '.join(parts)}]"

    def log(self) -> None:
        """Log summary with logger."""
        import logging
        logging.getLogger(__name__).warning(self.summary())

    def to_dict(self) -> dict:
        return {
            "skipped_count": self.count,
            "total_nodes": self.total_nodes,
            "skipped_nodes": [{"node": e.node, "error": e.message, "type": e.type} for e in self.skipped],
        }
```

### Wire Into Use Case

**File:** `projects/innovators_toolkit/nodes/assemble_report.py`
**Change:** After assembling sections, call SkipReport and add skip summary to report.

```python
from yamlgraph.contrib.progress import SkipReport

# After the sections loop:
tool_keys = [key for key, _, _ in TOOL_SECTIONS]
report = SkipReport.from_state(state, node_keys=tool_keys)
if report.count > 0:
    report.log()
    sections.append(f"\n## ⚠ Skipped Tools\n\n{report.summary()}\n")
```

### Tests

**File:** `tests/unit/test_contrib_progress.py`

| Test | What |
|------|------|
| `test_skipreport_no_errors` | Empty errors → "All nodes completed successfully" |
| `test_skipreport_with_errors` | 2 PipelineErrors → summary with node names and messages |
| `test_skipreport_from_state` | Build from dict with `errors` key |
| `test_skipreport_to_dict` | Serializable output |
| `test_skipreport_with_total` | Shows "2/9 skipped" when total_nodes provided |

All tagged `@pytest.mark.req("REQ-YG-070")`.

## Actions

1. **`yamlgraph/contrib/progress.py`** — NEW — Create SkipReport class (~40 lines)
2. **`yamlgraph/contrib/__init__.py`** — CHANGE — Export SkipReport
3. **`tests/unit/test_contrib_progress.py`** — NEW — 5 tests
4. **`projects/innovators_toolkit/nodes/assemble_report.py`** — CHANGE — Wire SkipReport after section assembly, add skip summary to report
5. **`reference/contrib-utilities.md`** — CHANGE — Add SkipReport documentation
6. **`docs/diary.md`** — CHANGE — Distill entry

## Not In Scope

- Framework-level automatic reporting (would need `graph_loader.py` changes)
- Map node skip aggregation (different error path in `map_compiler.py`)
- CLI `--skip-report` flag
