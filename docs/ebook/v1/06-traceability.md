# Chapter 06: Requirement Traceability Matrix

> *"Every test must be linked to a requirement in ARCHITECTURE.md."*
> — ADR-001, Requirement Traceability

---

## 1. The Vision: Living Documentation

Most software projects divorce their requirements from their code. Requirements live in Confluence pages, JIRA tickets, or PDF documents that drift out of sync the moment implementation begins. Tests verify behavior but never declare *which* requirement they prove. The result: features ship without proof, tests exist without purpose, and documentation lies.

YAMLGraph takes a different path. Requirements live *in the codebase*, enforced by the same toolchain that compiles and tests the code. The system forms a closed loop:

```
┌──────────────────────────────────────────────────────────────────┐
│                    THE TRACEABILITY LOOP                          │
│                                                                  │
│   Scripture                    ARCHITECTURE.md                   │
│   (.github/copilot-            (REQ-YG-XXX                      │
│    instructions.md)              definitions)                    │
│        │                            │                            │
│        │  defines doctrine          │  numbered requirements     │
│        ▼                            ▼                            │
│   ┌─────────┐    proves    ┌──────────────┐    enforces          │
│   │  Tests  │◄────────────►│ req_coverage │───────────┐          │
│   │ @pytest │              │    .py       │           │          │
│   │.mark.req│              └──────────────┘           ▼          │
│   └────┬────┘                                  ┌───────────┐    │
│        │                                       │pre-commit │    │
│        │  code changes                         │  hooks    │    │
│        ▼                                       └─────┬─────┘    │
│   ┌──────────┐    references    ┌───────────┐        │          │
│   │ Commits  │────────────────►│ CHANGELOG │◄───────┘          │
│   │ feat():  │                 │    .md    │                    │
│   │ FR-XXX   │                 └───────────┘                    │
│   └──────────┘                                                  │
│                                                                  │
│   LLM Agents (Inquisitor) verify and correct drift              │
└──────────────────────────────────────────────────────────────────┘
```

Each link in this chain is machine-enforced:

1. **Scripture** (`.github/copilot-instructions.md`) defines the doctrine — including ADR-001 itself:

   > *Every test function must have `@pytest.mark.req("REQ-YG-XXX")` linking it to a requirement in `ARCHITECTURE.md`.*

2. **ARCHITECTURE.md** translates doctrine into numbered, verifiable requirements grouped by capability.

3. **Tests** prove requirements via `@pytest.mark.req("REQ-YG-XXX")` decorators — creating a bidirectional link between test and requirement.

4. **Pre-commit hooks** run `req_coverage.py --strict` on every commit, blocking merges that leave requirements untested.

5. **LLM agents** (the Inquisitor) periodically audit the chain, detecting drift that static tools miss.

The key insight: requirements are not a phase of development. They are a *property* of the codebase, maintained with the same rigor as type annotations or test coverage.

---

## 2. The Requirement Structure

Requirements in YAMLGraph follow a strict hierarchy: **Capabilities** group related requirements, and each requirement has a unique identifier, description, and module mapping.

### The Capability Table

`ARCHITECTURE.md` organizes the system into numbered capabilities. Each capability maps to a group of requirements and their implementing modules:

```
| # | Capability | Key Modules | Requirements |
|---|-----------|-------------|--------------|
| 1 | Configuration Loading & Validation | graph_loader, models/graph_schema, ... | REQ-YG-001 – 004 |
| 2 | Graph Compilation | graph_loader, node_compiler | REQ-YG-005 – 008 |
| 3 | Node Execution | node_factory/llm_nodes, ... | REQ-YG-009 – 011, 050 |
```

### The Requirement Table

Each capability section then expands into individual requirements:

```markdown
### 1. Configuration Loading & Validation

Load YAML graph configs, validate schemas, build state models,
and ensure graph integrity through linting.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-001 | Load graph configurations from YAML files | graph_loader.load_graph_config, cli/helpers, data_loader |
| REQ-YG-002 | Validate graph configuration schemas and structures | models/graph_schema, utils/validators |
| REQ-YG-003 | Perform linting and pattern validation | linter/graph_linter, linter/checks, linter/patterns/* |
| REQ-YG-004 | Handle errors during configuration loading | cli/helpers.GraphLoadError, data_loader.DataFileError |
```

### The REQ-YG Numbering Scheme

Requirements use the format `REQ-YG-XXX` where:

- **REQ** — requirement (always present)
- **YG** — YAMLGraph (framework scope)
- **XXX** — three-digit zero-padded number (`001` through `092` and growing)

The numbering is **sequential by capability introduction order**, not by importance. When a capability is retired (e.g., CAP-27 Telco Voice Call Demo was relocated to `projects/`), its requirement numbers are *removed from the framework set* but never reassigned:

```python
# From scripts/req_coverage.py
_ALL_FRAMEWORK_REQS = (
    list(range(1, 78))  # REQ-YG-001 through REQ-YG-077
    + [83]              # REQ-YG-083 (CAP-28 Thinking Budget)
    + [87, 89]          # REQ-YG-087, REQ-YG-089 (CAP-30 Copilot Node) — 088 dropped
    + [90]              # REQ-YG-090 (CAP-31 Chaplain Diary Append)
    + [91, 92]          # REQ-YG-091, REQ-YG-092 (CAP-32 eBook Authoring Pipeline)
)
```

Notice the gaps: REQ-YG-078–082 relocated to `projects/outcaller/`, REQ-YG-084–086 to `projects/incaller/`, REQ-YG-088 was dropped as overengineering. These gaps are documented in comments, preserving the audit trail. Stable numbering means cross-references in commits, CHANGELOG entries, and diary entries never go stale.

### The Full Landscape

As of this writing, YAMLGraph tracks **32 capabilities** spanning **85 active framework requirements** across:

| Range | Capabilities |
|-------|-------------|
| REQ-YG-001–004 | Config Loading & Validation |
| REQ-YG-005–008 | Graph Compilation |
| REQ-YG-009–011, 050 | Node Execution |
| REQ-YG-012–016 | Prompt Execution |
| REQ-YG-017–020 | Tool & Agent Integration |
| REQ-YG-021–023 | Routing & Flow Control |
| REQ-YG-024–026 | State Persistence |
| REQ-YG-027–031 | Error Handling & Reliability |
| REQ-YG-032–035 | CLI Interface |
| REQ-YG-036–039 | Export & Serialization |
| REQ-YG-040–042, 075 | Subgraph & Map Processing |
| REQ-YG-043–047 | Utilities & Infrastructure |
| REQ-YG-048–049, 065 | Graph-Level Streaming |
| REQ-YG-051–054, 069 | Expression Language & Linting |
| REQ-YG-055–062, 064 | Execution Safety Guards |
| REQ-YG-063 | Testing & Quality |
| REQ-YG-066–068 | MCP Server Interface |
| REQ-YG-070–077 | Contrib, Diary, Lints, Skip, RAG, Streaming |
| REQ-YG-083–092 | Thinking Budget, Copilot Node, Diary, eBook |

---

## 3. Test Tagging with @pytest.mark.req

The bridge between requirements and proof is a single pytest marker: `@pytest.mark.req`.

### The Basic Pattern

```python
@pytest.mark.req("REQ-YG-014")
def test_load_existing_prompt(self):
    """Should load an existing prompt file."""
    prompt = load_prompt("generate")
    assert "system" in prompt
    assert "user" in prompt
```

The decorator takes one or more requirement IDs as positional arguments. When pytest collects this test, the marker creates a machine-readable link: *this test proves REQ-YG-014 (Synchronous prompt execution)*.



### Many-to-Many Relationships

The relationship between tests and requirements is many-to-many:

**One test covering multiple requirements:**

```python
@pytest.mark.req("REQ-YG-001", "REQ-YG-002", "REQ-YG-005")
def test_load_valid_yaml(self, sample_yaml_file):
    """Load a valid graph YAML file."""
    config = load_graph_config(sample_yaml_file)
    assert isinstance(config, GraphConfig)
    assert config.name == "test_graph"
    assert config.version == "1.0"
```

This test from `test_graph_loader.py` covers three requirements simultaneously: loading YAML files (001), validating schemas (002), and compiling into a StateGraph (005). This is natural — loading a graph config inherently exercises all three.

**One requirement covered by multiple tests:**

REQ-YG-014 (Synchronous prompt execution) is covered by 11 tests across `test_executor.py`:

```python
@pytest.mark.req("REQ-YG-014")
def test_load_existing_prompt(self):
    """Should load an existing prompt file."""
    ...

@pytest.mark.req("REQ-YG-014")
def test_format_single_variable(self):
    """Should format single variable."""
    ...

@pytest.mark.req("REQ-YG-014")
def test_execute_prompt_function_passes_path_params(self, tmp_path):
    """execute_prompt() should accept and forward path params."""
    ...
```

Multiple tests per requirement is not redundancy — it's coverage of different code paths through the same capability.

### Class-Level Markers

When an entire test class covers one requirement, the marker can be applied at class level:

```python
@pytest.mark.req("REQ-YG-024")
class TestBuildStateClass:
    def test_includes_base_infrastructure_fields(self):
        ...
    def test_extracts_state_key_from_nodes(self):
        ...
```

The `req_coverage.py` script handles both patterns, using class-qualified keys (`test_state_builder::TestBuildStateClass::test_includes_base_infrastructure_fields`) to avoid collisions.

---

## 4. The Enforcement Script: req_coverage.py

The traceability chain has two enforcement mechanisms: a pytest collection hook that blocks unmarked tests, and `scripts/req_coverage.py` that audits coverage completeness.

### The Collection Hook

In `tests/conftest.py`, a `pytest_collection_modifyitems` hook fires before any test runs:

```python
def pytest_collection_modifyitems(config, items):
    """Enforce that every test has @pytest.mark.req decorator.

    Implements ADR-001: Requirement Traceability.
    Enforces Commandment #10: Preserve and improve the doctrine.

    Raises:
        pytest.UsageError: If any test lacks @pytest.mark.req marker.
    """
    missing = []
    for item in items:
        # Check if the test has the 'req' marker
        if "req" not in item.keywords:
            missing.append(item.nodeid)

    if missing:
        error_msg = (
            f"\n{'=' * 70}\n"
            f"REQUIREMENT TRACEABILITY VIOLATION (ADR-001)\n"
            f"{'=' * 70}\n"
            f"{len(missing)} test(s) missing @pytest.mark.req('REQ-YG-XXX'):\n\n"
            + "\n".join(f"  - {nodeid}" for nodeid in missing)
            + f"\n\n"
            f"Every test must be linked to a requirement in ARCHITECTURE.md.\n"
            f"See: .github/copilot-instructions.md (Commandment #10)\n"
            f"{'=' * 70}\n"
        )
        raise pytest.UsageError(error_msg)
```

This is *structural enforcement*: not a lint warning, not a suggestion — an error that prevents the test suite from running. Write a test without `@pytest.mark.req`? The entire suite refuses to collect. This is codified as REQ-YG-063 and tested by `test_requirement_enforcement.py`:

```python
@pytest.mark.req("REQ-YG-063")
def test_untagged_test_is_rejected(tmp_path: Path):
    """Verify pytest fails when a test lacks @pytest.mark.req."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text(textwrap.dedent("""
        def test_missing_req_tag():
            '''This test has no @pytest.mark.req tag.'''
            assert True
    """))

    conftest_src = Path(__file__).parent.parent / "conftest.py"
    conftest_dst = tmp_path / "conftest.py"
    conftest_dst.write_text(conftest_src.read_text())

    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
        capture_output=True, text=True,
    )

    assert result.returncode != 0
    assert "REQUIREMENT TRACEABILITY VIOLATION" in result.stderr
```

The enforcement tests its own enforcement — a meta-requirement that the traceability system is itself traceable.

### The Coverage Script

While the conftest hook ensures every *test* links to a requirement, `req_coverage.py` ensures every *requirement* has at least one test. It operates in three modes:

**Summary mode** (default):

```
$ python scripts/req_coverage.py

======================================================================
REQUIREMENT TRACEABILITY REPORT
======================================================================

Requirements: 85/85 covered
Tagged tests: 1,247 unique, 1,583 test-req pairs

CAPABILITY COVERAGE
----------------------------------------------------------------------
  ✅ CAP-01 Config Loading & Validation: 4/4 reqs, 78 tests
  ✅ CAP-02 Graph Compilation: 4/4 reqs, 52 tests
  ✅ CAP-03 Node Execution: 4/4 reqs, 41 tests
  ✅ CAP-04 Prompt Execution: 5/5 reqs, 89 tests
  ...
  ✅ CAP-32 eBook Authoring Pipeline: 2/2 reqs, 8 tests
```

**Detail mode** (`--detail`): Shows which specific tests cover each requirement:

```
$ python scripts/req_coverage.py --detail

DETAILED MAPPING
----------------------------------------------------------------------

  REQ-YG-001 (18 tests):
    - test_graph_loader::TestLoadGraphConfig::test_load_valid_yaml
    - test_graph_loader::TestLoadGraphConfig::test_parse_nodes
    - test_graph_loader::TestLoadGraphConfig::test_parse_edges
    ...

  REQ-YG-002 (15 tests):
    - test_graph_schema::TestGraphConfig::test_valid_config
    ...
```

**Implementation mode** (`--implementation`): Traces the full chain from requirement through source files to tests, using both `.coverage` database analysis and AST-based import resolution as fallback:

```
$ python scripts/req_coverage.py --implementation

IMPLEMENTATION TRACEABILITY
======================================================================

── CAP-01 Config Loading & Validation (4 reqs, 78 tests) ──────────

    REQ-YG-001  Load graph configurations from YAML files
      (6 files, 18 tests)
      Implementation:
        yamlgraph/graph_loader.py
        yamlgraph/cli/helpers.py
        yamlgraph/data_loader.py
      Tests (coverage):
        test_graph_loader::TestLoadGraphConfig::test_load_valid_yaml
        ...
```

**Strict mode** (`--strict`): Returns exit code 1 if any requirement has zero tests. This is the mode used by the pre-commit hook.

### How It Works Internally

The script uses Python's `ast` module to parse test files without executing them:

```python
def extract_req_markers(filepath: Path) -> dict[str, list[str]]:
    """Extract @pytest.mark.req(...) markers from a test file."""
    tree = ast.parse(filepath.read_text(), filename=str(filepath))
    req_map: dict[str, list[str]] = defaultdict(list)
    # ... walks the AST looking for decorator nodes matching
    # pytest.mark.req("REQ-YG-XXX") pattern
```

It scans both `tests/unit/` and `tests/integration/`, building a mapping of requirement IDs to test function names. The capability grouping comes from the `CAPABILITIES` dict hardcoded in the script — which must be updated when adding new capabilities.

### Pre-commit Integration

The script runs as a pre-commit hook on every commit:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: req-coverage-strict
      name: req_coverage --strict
      entry: .venv/bin/python scripts/req_coverage.py --strict
      language: system
      pass_filenames: false
      always_run: true
      stages: [pre-commit]
```

Key properties:
- `always_run: true` — runs even when no test files changed, because adding a requirement to `ARCHITECTURE.md` without a test should be caught
- `pass_filenames: false` — always scans the full test suite
- `--strict` — exits non-zero on any gap, blocking the commit

---

## 5. Conventional Commits Integration

Requirements don't just live in tests — they flow through the entire commit lifecycle.

### The Commit Message Chain

YAMLGraph uses Conventional Commits with feature request (FR) enforcement:

```
feat(ebook): FR-100 add eBook authoring pipeline

- 14-node pipeline with copilot research nodes, LLM writing, and judge
- CAP-32, REQ-YG-091
- write_chapters_tool writes formatted chapter content to disk

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

The chain from requirement to release:

1. **Feature Request** (e.g., `feature-requests/FR-100-ebook-pipeline.md`) defines objectives and acceptance criteria
2. **Requirements** (REQ-YG-091, REQ-YG-092) are added to `ARCHITECTURE.md` under a new capability (CAP-32)
3. **Tests** tagged with `@pytest.mark.req("REQ-YG-091")` prove the requirements
4. **Code** implements the capability
5. **Commit** references both FR and capability: `feat(ebook): FR-100 add eBook authoring pipeline`
6. **CHANGELOG** entry links them all together:

```markdown
### Added
- **FR-100 eBook Authoring Pipeline** (CAP-32, REQ-YG-091):
  YAMLGraph-driven pipeline to write development pipeline
  documentation as an eBook
```

### Pre-commit Commit Message Hooks

Two commit-msg hooks enforce the convention:

- **feat-requires-fr**: Any `feat(...)` commit must include an `FR-XXX` reference
- **changelog-required**: Feature and fix commits must have corresponding CHANGELOG entries

This creates a paper trail that can be audited in either direction:
- *Forward*: "What did FR-100 deliver?" → Check CHANGELOG, find CAP-32, find REQ-YG-091/092, find tagged tests
- *Backward*: "Why does this test exist?" → Check `@pytest.mark.req("REQ-YG-091")`, find REQ-YG-091 in ARCHITECTURE.md, find CAP-32 in CHANGELOG, find FR-100

---

## 6. Pervasive Verification

The traceability system isn't just for humans to audit — it's designed so LLM agents can maintain it autonomously.

### When Adding a Capability

The Scripture defines the procedure in `.github/copilot-instructions.md`:

> *When adding a new capability: add requirement(s) to `ARCHITECTURE.md`, extend `ALL_REQS` range and `CAPABILITIES` dict in `scripts/req_coverage.py`, tag tests with the new req ID.*

Concretely, adding a capability requires four synchronized changes:

1. **ARCHITECTURE.md**: Add the capability section with requirement table
2. **req_coverage.py**: Extend `_ALL_FRAMEWORK_REQS` list and `CAPABILITIES` dict
3. **Test files**: Tag tests with `@pytest.mark.req("REQ-YG-XXX")`
4. **CHANGELOG.md**: Reference capability and requirement IDs

Miss any step, and the pre-commit hooks catch it:
- Missing requirement numbers in `req_coverage.py` → tests reference unknown requirements
- Missing tests → `--strict` mode fails
- Missing CHANGELOG → commit-msg hook rejects the commit

### When Tests Fail

Failed tests are traceable back to requirements. A CI failure report shows:

```
FAILED tests/unit/test_executor.py::TestExecutePrompt::test_structured_output
```

The developer can immediately determine:
- This test carries `@pytest.mark.req("REQ-YG-014")`
- REQ-YG-014 is "Synchronous prompt execution"
- It belongs to CAP-04 (Prompt Execution)
- The implementing module is `executor.py`

This eliminates the archaeology of "what was this test supposed to prove?" — the answer is encoded in the marker.

### When Doctrine Changes

When the Scripture evolves, requirements may need updating. The traceability chain makes impact analysis mechanical:

1. Doctrine change identifies affected capability
2. `ARCHITECTURE.md` requirements for that capability are reviewed
3. `req_coverage.py --detail` shows which tests cover those requirements
4. Tests are updated, new requirements added if needed
5. Pre-commit hooks verify the chain is intact

---

## 7. The Inquisitor's Verification Runs

The most distinctive element of YAMLGraph's traceability system is the Inquisitor — an LLM agent that periodically audits the entire chain. Where static tools check syntax, the Inquisitor checks *semantics*.

### What the Inquisitor Audits

Each audit covers the recent commit range against:
- All 10 Commandments from the Scripture
- ADR-001 (Requirement Traceability)
- noqa Confessions compliance
- Conventional Commits formatting
- The Sermon's Distill step (diary entries)

### A Real Verification Run

From the project diary, here is an actual Inquisitor audit entry:

> **2026-02-25: Inquisitor Audit — FR-103 Cycle Complete, Doctrine Holding**
>
> **Context:** Audit of HEAD (`0704063`), covering 5 commits: `0704063` (docs: FR-103 diary), `b0fa74c` (feat: FR-103 judge-amend subgraph), `9048d03` (docs: FR-100 progress), `bd1d6ce` (feat: FR-100 ebook scaffold), `e909641` (docs: FR-100 feature request). Two `feat` commits introduce new capabilities (CAP-32, REQ-YG-091, REQ-YG-092). Audited against all 10 Commandments, ADR-001, Confessions, and the Sermon.
>
> **Findings:**
>
> - ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** REQ-YG-091 (4 tests in `test_ebook_writing.py`) and REQ-YG-092 (4 tests in `test_ebook_doctrine_validation.py`) all carry `@pytest.mark.req` tags. Both requirements documented in ARCHITECTURE.md. `req_coverage.py` updated.
> - ✓ COMPLIANT — **noqa Confessions:** 2 suppressions (CONF-002: ARG002, CONF-003: ANN001) remain confessed. No new suppressions introduced across the 5-commit range.
> - ⚠ DRIFT — **Co-authored-by trailer:** 0/5 commits include the required `Co-authored-by: Copilot` trailer.
>
> **Heuristic:** A full FR cycle (FR-100→FR-101→FR-102→FR-103) that ends with a diary entry closing every prior audit finding is the doctrine working as designed.

### What Drift Looks Like

The Inquisitor detects categories of drift that static tools cannot:

**Requirement drift**: A capability's tests exist but no longer match the requirement's intent — the code evolved but the requirement description didn't.

**Ceremony drift**: The Sermon's Distill step (writing diary entries after completing work) being skipped:

> *⚠ DRIFT — No diary entry was written for the documentation sprint (FR-087 through FR-092). Six FRs were planned, judged, and enforced in sequence — a substantive task list. The Sermon's Distill step was skipped.*

**Entropy drift**: The audit log itself becoming bloated:

> *⚠ DRIFT — Diary entropy (Commandment 8): 25 entries for 2026-02-25 in 340 lines. The Inquisitor's own entries remain the dominant entropy contributor.*

This last finding is particularly notable — the Inquisitor detecting that *its own operation* violates Commandment 8 (kill entropy). The system is self-aware enough to flag its own overhead.

### The Correction Flow

When drift is detected, it flows back through the traceability chain:

1. Inquisitor flags the drift in a diary entry
2. If actionable, a feature request is created (e.g., FR-095 Documentation Staleness Monitor)
3. The FR defines new requirements or refines existing ones
4. Tests are written, code is changed, pre-commit hooks verify
5. The next Inquisitor audit confirms the fix

This is the Rite of Correction in practice: **Inspect → Amend → Escalate**.

---

## 8. Why This Matters

The traceability matrix is not bureaucracy. It is a machine-enforced property of the codebase that prevents four specific failure modes:

### Untested Features

Without traceability, a developer can add a capability to `ARCHITECTURE.md`, write the code, and ship without any test. The `--strict` flag on `req_coverage.py` makes this impossible: every requirement must have at least one test, or the commit is rejected.

### Orphan Tests

Without traceability, tests accumulate without clear purpose. When a feature is removed, its tests linger — consuming CI time, confusing developers, providing false confidence. With `@pytest.mark.req`, every test declares its purpose. When a capability is retired (like CAP-27 Telco Voice Call Demo being moved to `projects/`), the requirement IDs are removed from `_ALL_FRAMEWORK_REQS`, and any tests still referencing them become visible as referencing unknown requirements.

### Doctrine Drift

Without traceability, the Scripture says one thing and the code does another. The gap grows invisibly until a production incident reveals it. With the Inquisitor auditing the chain, drift is detected within the same working session — not months later.

### Commit Chaos

Without traceability, commit history is a flat stream of changes with no structural connection to requirements or features. With the FR → REQ → test → commit → CHANGELOG chain, any change can be traced forward to its impact and backward to its motivation.

### The Cost

The overhead is real but bounded:
- Adding `@pytest.mark.req("REQ-YG-XXX")` to each test: ~5 seconds per test
- Updating `req_coverage.py` for new capabilities: ~2 minutes per capability
- Running the pre-commit hook: ~3 seconds per commit
- Inquisitor audits: automated, zero developer time

The return: a codebase where the answer to "why does this exist?" is always one grep away.

---

## Summary

YAMLGraph's requirement traceability is not a documentation exercise — it is a *property of the system*, enforced at every layer:

| Layer | Mechanism | What It Catches |
|-------|----------|-----------------|
| Test collection | `conftest.py` hook | Tests without requirement links |
| Pre-commit | `req_coverage.py --strict` | Requirements without tests |
| Commit message | `feat-requires-fr` hook | Features without FR references |
| CHANGELOG | `changelog-required` hook | Features without release notes |
| LLM audit | Inquisitor diary entries | Semantic drift, ceremony gaps |

The result is a codebase that can answer, at any point in time:

- **What is required?** → `ARCHITECTURE.md`
- **What is proven?** → `req_coverage.py --detail`
- **What is implemented?** → `req_coverage.py --implementation`
- **What changed?** → `git log` with FR references
- **What drifted?** → Inquisitor audit entries in `docs/diary.md`

What survives the fire may merge.

