# Feature Request: FR-196 Portable Chaplain

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 3 days
**Requested:** 2026-03-13

## Judge Verdict: APPROVE

**Date:** 2026-03-13
**Verdict:** APPROVED — Scope frozen. Authority granted to implement.

### Evaluation

| Criterion | Assessment |
|-----------|-----------|
| Scope clear and minimal? | ✅ Yes — 5 well-defined phases with clear boundaries |
| Contradictions or ambiguities? | ⚠️ One minor (see note below) |
| Acceptance criteria measurable? | ✅ Yes — 18 criteria, all verifiable by grep/lint/test |
| Implementation approach feasible? | ✅ Yes — `spec_from_file_location` is standard Python |
| Aligned with architecture? | ✅ Yes — extends PythonToolConfig naturally, follows 3-layer pattern |
| Single responsibility? | ✅ Yes — Phase 1 (framework) enables Phases 2-5 (relocation); tightly coupled, not orthogonal |

### Note: Test import mechanism (Phase 4)

The consumer impact table (line 30) states test_philosopher.py will use `import .chaplain.lib.diary` — this is **not valid Python syntax** (`.chaplain` is a relative import marker, not a dotted-directory reference). The implementer must choose one of:

- **(a)** Add `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))` in conftest and import as `from chaplain.lib.diary import ...` — but `.chaplain` is not a valid package name.
- **(b)** Use `importlib.util.spec_from_file_location()` in a test helper (mirrors the production loading path).
- **(c)** Keep test imports pointing to `examples.shared.diary` (which is preserved) since the test exercises the Python function, not the YAML tool loading. The `path`-based loading of diary.py is covered by the new REQ-YG-193 unit tests.

**Recommendation:** Option (c) is simplest and correct — test_philosopher tests philosopher *logic*, not Chaplain *wiring*. The diary functions are identical in both locations. Monkeypatching `examples.shared.diary.DIARY_DIR` remains valid since that module is preserved. For philosopher tools/models imports (which DO move), option (b) with a small helper is appropriate.

This is an implementation-detail decision, not a scope issue. The FR's Phase 4 adequately identifies the work needed.

### Prior Judge Response

This revision addresses all four issues from the Judge verdict dated 2026-03-13.

### Issue 1: diary_digest breakage — RESOLVED (Option A)

**Decision:** Keep `examples/shared/diary.py` in place for non-Chaplain consumers. Copy `diary.py` to `.chaplain/lib/diary.py` for Chaplain graphs.

**Rationale:** The Chaplain portability goal requires `.chaplain/` to be self-contained. Moving `diary.py` and updating all consumers (option b) expands scope into diary_digest, its nodes, and two test files — none of which are Chaplain concerns. Option (a) preserves all existing consumers without changes and keeps this FR scoped to the Chaplain subsystem.

**DRY acknowledgment:** `.chaplain/lib/diary.py` will be a copy of `examples/shared/diary.py`. A follow-up FR should consolidate diary functionality into a single canonical location (likely `yamlgraph/tools/diary.py`, option c) and update all consumers.

**Consumer impact:**

| Consumer | Current import | After FR-196 | Breaks? |
|----------|---------------|--------------|---------|
| `examples/copilot/graph.yaml` | `module: examples.shared.diary` | Deleted; replaced by `.chaplain/graphs/copilot/graph.yaml` with `path: .chaplain/lib/diary.py` | No |
| `examples/philosopher/graph.yaml` | `module: examples.shared.diary` | Deleted; replaced by `.chaplain/graphs/philosopher/graph.yaml` with `path: .chaplain/lib/diary.py` | No |
| `examples/diary_digest/graph.yaml` | `module: examples.shared.diary` | Unchanged | No |
| `examples/diary_digest/nodes/writing.py` | `from examples.shared.diary import ...` | Unchanged | No |
| `tests/unit/test_diary_digest.py` | `monkeypatch.setattr("examples.shared.diary.DIARY_DIR", ...)` | Unchanged | No |
| `tests/unit/test_philosopher.py` | `import examples.shared.diary as diary_mod` | Updated to `import .chaplain.lib.diary` via path-based import | Yes (updated in Phase 4) |

### Issue 2: Path resolution semantics — RESOLVED

**Decision:** Resolve `path` relative to CWD (current working directory at runtime).

**Rationale:** This matches the existing `module` loading behavior, which adds CWD to `sys.path[0]` before calling `importlib.import_module()`. A `path` value of `.chaplain/lib/diary.py` resolves to `{CWD}/.chaplain/lib/diary.py`.

**Documentation:** The CWD-relative semantics will be documented in `reference/graph-yaml.md` and in the `PythonToolConfig` docstring.

### Issue 3: Missing REQ-YG-XXX — RESOLVED

**Decision:** Assign REQ-YG-193 for path-based Python tool loading.

Added to acceptance criteria:
- REQ-YG-193 added to `ARCHITECTURE.md`
- Tests tagged with `@pytest.mark.req("REQ-YG-193")`

### Issue 4: Missing reference documentation — RESOLVED

**Decision:** Add `reference/graph-yaml.md` to documentation update scope.

The `path` field for `type: python` tools will be documented alongside the existing `module` field in the Python tools section of `reference/graph-yaml.md`.

---

## Summary

Move Chaplain-related graphs, prompts, and Python tools from `examples/` into `.chaplain/` so the entire Chaplain subsystem is self-contained and portable to other projects.

## Value Statement

Any YAMLGraph-based project gains a ready-made Plan → Judge → Enforce → Philosopher pipeline by copying a single `.chaplain/` directory, eliminating per-project re-creation of the workflow.

## Problem

The Chaplain pipeline is currently split across multiple locations:

| Component | Current location |
|-----------|-----------------|
| Plan/Judge/Summarize/Write graph | `examples/copilot/graph.yaml` + `examples/copilot/prompts/` |
| Enforce graph | `examples/enforce/graph.yaml` + `examples/enforce/prompts/` |
| Philosopher graph | `examples/philosopher/graph.yaml` + `examples/philosopher/prompts/` + `tools.py` + `models.py` |
| Shared diary tool | `examples/shared/diary.py` |
| Shell daemons | `.chaplain/watch.sh`, `inquisitor.sh`, `philosopher.sh` |
| ID registry | `.chaplain/id-registry.yaml` |
| Inbox / Drafts | `.chaplain/inbox/`, `.chaplain/drafts/` |

The shell scripts already live in `.chaplain/` but reference graphs in `examples/`. This coupling means:

1. **Not portable** — copying `.chaplain/` to another project leaves broken graph references and missing Python tools.
2. **Misleading location** — `examples/` implies demo code; the Chaplain is production infrastructure.
3. **Mixed concerns** — `examples/` contains both demo examples (hello, npc, ebook) and core automation (copilot, enforce, philosopher).
4. **Hidden dependency** — the philosopher graph depends on `examples.shared.diary` (outside its own directory), breaking the portability contract silently.

## Proposed Solution

### Phase 1: Extend python_tool.py with file-path-based loading (REQ-YG-193)

The `.chaplain` directory name starts with a dot, making it an invalid Python package name. The current `python_tool.py` resolves tools exclusively via `importlib.import_module(config.module)`, which requires valid dotted Python package paths.

Add a `path` field to `PythonToolConfig` as an alternative to `module`. When `path` is set, use `importlib.util.spec_from_file_location()` to load the module from a file path instead of a package path.

```python
# yamlgraph/tools/python_tool.py — PythonToolConfig enhancement
@dataclass
class PythonToolConfig:
    module: str | None = None    # Dotted import path (existing)
    path: str | None = None      # File path, CWD-relative (new, mutually exclusive with module)
    function: str = ""
    description: str = ""
```

Loading logic:

```python
def load_python_function(config: PythonToolConfig) -> Callable:
    if config.path and config.module:
        raise ValueError("PythonToolConfig: set 'path' or 'module', not both")
    if not config.path and not config.module:
        raise ValueError("PythonToolConfig: one of 'path' or 'module' is required")

    if config.path:
        # File-path-based loading, resolved relative to CWD
        resolved = Path(config.path).resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Python tool path not found: {resolved}")
        spec = importlib.util.spec_from_file_location(resolved.stem, resolved)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        # Existing dotted-path loading
        cwd = os.getcwd()
        if cwd not in sys.path:
            sys.path.insert(0, cwd)
        module = importlib.import_module(config.module)

    return getattr(module, config.function)
```

**Path resolution:** `Path(config.path).resolve()` resolves relative paths against CWD, matching the existing `module` loading behavior where CWD is prepended to `sys.path`.

Graph YAML usage after this change:

```yaml
# .chaplain/graphs/philosopher/graph.yaml
tools:
  scan_diary_tool:
    type: python
    path: .chaplain/graphs/philosopher/tools.py
    function: scan_diary_markers
```

### Phase 2: Inline philosopher models into tools

`examples/philosopher/models.py` (68 lines) is imported only by `examples/philosopher/tools.py` via:

```python
from examples.philosopher.models import ProposalList, extract_json
```

After relocation, this dotted import path breaks. Since `models.py` is small (3 Pydantic models + 1 utility function, 68 lines) and used exclusively by `tools.py` (~205 lines), inline it into `tools.py`. The combined file (~270 lines) stays well under the 400-line module limit.

### Phase 3: Relocate files

Move all Chaplain files. Copy the shared diary dependency.

Target structure:

```
.chaplain/
├── graphs/
│   ├── copilot/
│   │   ├── graph.yaml
│   │   └── prompts/
│   │       ├── plan.yaml
│   │       ├── judge.yaml
│   │       └── summarize.yaml
│   ├── enforce/
│   │   ├── graph.yaml
│   │   └── prompts/
│   │       ├── enforce-implement.yaml
│   │       ├── enforce-test-demo.yaml
│   │       ├── enforce-critique-and-distill.yaml
│   │       └── enforce-finalize.yaml
│   └── philosopher/
│       ├── graph.yaml
│       ├── tools.py              # includes inlined models from models.py
│       └── prompts/
│           ├── analyze.yaml
│           └── reflect.yaml
├── lib/
│   └── diary.py                  # COPY of examples/shared/diary.py (see Issue 1)
├── watch.sh
├── inquisitor.sh
├── philosopher.sh
├── id-registry.yaml
├── inbox/
├── drafts/
└── .gitignore
```

**Shared diary dependency (Issue 1, Option A):** Copy `examples/shared/diary.py` to `.chaplain/lib/diary.py`. The original file stays in place for non-Chaplain consumers (diary_digest, tests). The DRY violation is acknowledged; consolidation is deferred to a follow-up FR.

### Phase 4: Update all references

**Graph YAML updates:**

```yaml
# .chaplain/graphs/philosopher/graph.yaml — tools section
tools:
  scan_diary_tool:
    type: python
    path: .chaplain/graphs/philosopher/tools.py
    function: scan_diary_markers
  write_diary_tool:
    type: python
    path: .chaplain/lib/diary.py
    function: write_diary
  write_proposal_tool:
    type: python
    path: .chaplain/graphs/philosopher/tools.py
    function: write_proposals

# .chaplain/graphs/copilot/graph.yaml — tools section
tools:
  write_diary_tool:
    type: python
    path: .chaplain/lib/diary.py
    function: write_diary
```

**Shell script updates:**

```bash
# .chaplain/watch.sh
yamlgraph graph run .chaplain/graphs/copilot/graph.yaml ...

# .chaplain/philosopher.sh
yamlgraph graph run .chaplain/graphs/philosopher/graph.yaml ...

# scripts/enforce_worktree.sh (line 134)
yamlgraph graph run .chaplain/graphs/enforce/graph.yaml ...
```

**Test updates:**

`tests/unit/test_philosopher.py` imports from `examples.shared.diary` and `examples.philosopher.tools`. These update to reference the new `.chaplain/` locations. Since path-based loading uses `spec_from_file_location`, test monkeypatching will target the loaded module rather than a dotted import path.

### Phase 5: Remove old locations

- Delete `examples/copilot/` (graph.yaml, prompts/, README.md)
- Delete `examples/enforce/` (graph.yaml, prompts/, README.md)
- Delete `examples/philosopher/` (graph.yaml, prompts/, tools.py, models.py, README.md)
- **Keep** `examples/shared/diary.py` (non-Chaplain consumers still depend on it)

### Documentation update scope

Update **living documentation only**:
- `ARCHITECTURE.md` — Add REQ-YG-193; update Chaplain subsystem references
- `CLAUDE.md` — Chaplain path references, running examples section
- `reference/graph-yaml.md` — Document `path` field for `type: python` tools
- `.chaplain/*.sh` script headers/comments
- `scripts/enforce_worktree.sh` comments

**Leave historical documentation as-is** (feature-requests/, changelog/, capabilities/, docs/diary/) — these record the state at time of writing and should not be retroactively modified.

### Portability contract

After this change, the following copies the full Chaplain to another YAMLGraph project:

```bash
cp -r .chaplain/ /path/to/other-project/.chaplain/
```

**Requirements on the receiving project:**
- `yamlgraph` installed (provides CLI, executor, LLM factory)
- `scripts/enforce_worktree.sh` copied separately if enforce pipeline is needed (it lives outside `.chaplain/` because it manages git worktrees at repository level)

No other files from this repository are required for the Chaplain to function.

## Acceptance Criteria

- [ ] `PythonToolConfig` supports `path` field for file-path-based tool loading, resolved relative to CWD
- [ ] Validation rejects configs where both `path` and `module` are set, or neither is set
- [ ] Unit tests for path-based loading: happy path, missing file, both fields set, neither field set — tagged `@pytest.mark.req("REQ-YG-193")`
- [ ] REQ-YG-193 added to `ARCHITECTURE.md`
- [ ] `examples/philosopher/models.py` content inlined into philosopher `tools.py`; combined file < 400 lines
- [ ] All Chaplain graphs and prompts relocated from `examples/{copilot,enforce,philosopher}/` to `.chaplain/graphs/`
- [ ] `examples/shared/diary.py` copied to `.chaplain/lib/diary.py`; original preserved for non-Chaplain consumers
- [ ] Shell scripts (`.chaplain/watch.sh`, `philosopher.sh`) updated to reference new graph paths
- [ ] `scripts/enforce_worktree.sh` updated to reference `.chaplain/graphs/enforce/graph.yaml`
- [ ] All existing tests pass (test references updated where needed)
- [ ] `yamlgraph graph lint .chaplain/graphs/copilot/graph.yaml` succeeds
- [ ] `yamlgraph graph lint .chaplain/graphs/enforce/graph.yaml` succeeds
- [ ] `yamlgraph graph lint .chaplain/graphs/philosopher/graph.yaml` succeeds
- [ ] No remaining references to `examples/copilot/`, `examples/enforce/`, or `examples/philosopher/` in `.chaplain/` scripts or `scripts/enforce_worktree.sh`
- [ ] `reference/graph-yaml.md` updated with `path` field documentation for `type: python` tools
- [ ] Living documentation updated (`CLAUDE.md`, `ARCHITECTURE.md`)
- [ ] Old directories removed (`examples/copilot/`, `examples/enforce/`, `examples/philosopher/`)
- [ ] `examples/shared/diary.py` preserved (non-Chaplain consumers untouched)
- [ ] Diary entry written

## Alternatives Considered

1. **Move diary.py and update ALL consumers (Judge option b)** — Rejected for this FR: expands scope into diary_digest graph, nodes/writing.py, and two test files. None are Chaplain concerns. Deferred to follow-up FR.

2. **Move diary.py to framework-level `yamlgraph/tools/diary.py` (Judge option c)** — Rejected for this FR: contradicts the portability goal and expands scope. Better suited as the follow-up consolidation FR.

3. **Top-level `chaplain/` directory (without dot prefix)** — Rejected: the dot-prefix convention is established and signals infrastructure tooling, consistent with `.github/`, `.pre-commit-config.yaml`.

4. **Symlinks from `examples/` to `.chaplain/graphs/`** — Rejected: symlinks break portability (the exact problem we're solving).

5. **Leave graphs in `examples/` with configurable base path** — Rejected: adds configuration complexity without achieving true portability.

6. **Rename to `chaplain/` without dot prefix for standard Python imports** — Rejected: breaks established `.chaplain/` convention. File-path-based loading solves importability.

## Related

- FR-098: Consolidated copilot workflow into `examples/copilot/graph.yaml`
- FR-106/FR-183: Enforce pipeline in `examples/enforce/graph.yaml`
- FR-184/FR-185: Philosopher daemon in `examples/philosopher/graph.yaml`
- FR-097: Shared diary extraction (`examples/shared/diary.py`)
- `.chaplain/watch.sh`, `.chaplain/philosopher.sh`, `.chaplain/inquisitor.sh`
