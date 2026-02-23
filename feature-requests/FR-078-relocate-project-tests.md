# Feature Request: FR-078 Relocate Project-Specific Tests

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** In Progress
**Effort:** 0.5 day
**Requested:** 2026-02-23

## Summary

Move 10 test files from `tests/` to `projects/{incaller,outcaller}/tests/`. Tests belong with the code they test.

## Problem

Project-specific tests live in yamlgraph's `tests/` but test code from gitignored `projects/` repos:
- Projects can't run their own tests standalone
- Framework test count inflated by project tests
- Sync burden between repos

## Files to Relocate

| Source | Destination |
|--------|-------------|
| `tests/unit/test_incaller.py` | `projects/incaller/tests/unit/` |
| `tests/unit/test_telco_nodes.py` | `projects/outcaller/tests/unit/` |
| `tests/unit/test_outcaller_tts.py` | `projects/outcaller/tests/unit/` |
| `tests/unit/test_probe_recap.py` | `projects/outcaller/tests/unit/` |
| `tests/unit/test_questionnaire_flow.py` | `projects/outcaller/tests/unit/` |
| `tests/integration/test_telco_twilio.py` | `projects/outcaller/tests/integration/` |
| `tests/integration/test_outcaller_probe_recap.py` | `projects/outcaller/tests/integration/` |
| `tests/integration/test_outcaller_refusal.py` | `projects/outcaller/tests/integration/` |
| `tests/integration/test_telco_elevenlabs.py` | `projects/outcaller/tests/integration/` |
| `tests/integration/test_elevenlabs_stt.py` | `projects/outcaller/tests/integration/` |

## Implementation

### 0. Fix REQ-YG-083 Collision (Pre-requisite)

REQ-YG-083 belongs to CAP-28 (Thinking Budget) but outcaller tests incorrectly use it for probe-recap.

**Decision:** Project tests use project-local namespace:
- Outcaller tests: `@pytest.mark.req("OC-XXX")` (e.g., OC-005)
- Incaller tests: `@pytest.mark.req("IC-XXX")`
- Framework tests: `@pytest.mark.req("REQ-YG-XXX")`

**Re-tag these files before relocation:**

| File | Old Tag | New Tag |
|------|---------|---------|
| `test_probe_recap.py` | REQ-YG-083 | OC-005 |
| `test_questionnaire_flow.py` | REQ-YG-083 | OC-005 |
| `test_outcaller_probe_recap.py` | REQ-YG-083 | OC-005 |

### 1. Shared req enforcement plugin

```python
# yamlgraph/testing/conftest_plugin.py
def pytest_collection_modifyitems(config, items):
    """Enforce @pytest.mark.req on every test."""
    missing = [item.nodeid for item in items if "req" not in item.keywords]
    if missing:
        raise pytest.UsageError(f"{len(missing)} tests missing @pytest.mark.req")
```

Project conftest files can customize the pattern:
```python
# projects/outcaller/tests/conftest.py
from yamlgraph.testing.conftest_plugin import pytest_collection_modifyitems  # noqa: F401
# Accepts any @pytest.mark.req("...") - both OC-XXX and REQ-YG-XXX valid
```

### 2. Root conftest for conditional discovery

```python
# conftest.py (repo root)
import pathlib

def pytest_configure(config):
    root = pathlib.Path(__file__).parent
    for project in ["incaller", "outcaller"]:
        project_tests = root / "projects" / project / "tests"
        if project_tests.is_dir():
            config.addinivalue_line("testpaths", str(project_tests))
```

### 3. Clean req_coverage.py

Remove project capabilities from framework tracking:

```python
# Remove CAP-27 and CAP-29 (project demos, now use OC-XXX/IC-XXX)
# Keep CAP-28 (Thinking Budget) — framework feature
```

`req_coverage.py` only tracks `REQ-YG-XXX` (framework tests). Project tests use `OC-XXX`/`IC-XXX` and are not scanned.

### 4. Delete originals

Remove 9 relocated files from `tests/`.

## Constraints

- `projects/` is gitignored — relocated tests enter project repos
- `pytest tests/` must work on clean yamlgraph clone
- Each project repo owns its CI pipeline for running its tests
- `test_incaller.py` depends on `projects.outcaller` — documented, not changed

## Acceptance Criteria

- [x] Re-tag probe-recap tests from REQ-YG-083 to OC-005
- [x] Remove CAP-27, CAP-29 from `req_coverage.py` (project demos)
- [x] 10 test files relocated to project repos
- [x] `pytest tests/` runs framework tests only
- [ ] `pytest` discovers project tests when dirs exist
- [ ] Add CONF-XXX for `# noqa: F401` in conftest re-exports

## Related

- `tests/conftest.py` — req enforcement hook source
- REQ-YG-083 → CAP-28 (Thinking Budget) — collision fixed by namespace split
