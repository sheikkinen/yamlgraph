# Chapter 06: Requirement Traceability Matrix

> *"Every test function must have `@pytest.mark.req("REQ-YG-XXX")` linking it to a requirement in `ARCHITECTURE.md`."*
> — ADR-001, The Scripture

---

## 1. The Vision: Living Documentation

Most software projects treat requirements as a write-once artifact. A product manager drafts a specification in a PDF or a wiki, developers read it once, and over months of iteration the code drifts from the document until neither reflects reality. Requirements become archaeological records of intent, not verifiable properties of the system.

YAMLGraph takes a different approach: requirements live *in the code*, enforced by the same toolchain that compiles and tests the software. The result is a closed loop where doctrine, requirements, tests, and commits form a single traceable chain:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    The Traceability Chain                            │
│                                                                     │
│  Scripture (.github/copilot-instructions.md)                        │
│      │  "Every test function must have @pytest.mark.req..."         │
│      ▼                                                              │
│  ARCHITECTURE.md                                                    │
│      │  REQ-YG-001: "Load graph configurations from YAML files"     │
│      ▼                                                              │
│  Test Code (@pytest.mark.req("REQ-YG-001"))                        │
│      │  test_load_valid_yaml() → asserts GraphConfig created        │
│      ▼                                                              │
│  Pre-commit Hook (req_coverage.py --strict)                         │
│      │  Blocks commit if any REQ has zero tests                     │
│      ▼                                                              │
│  Inquisitor Audit (diary.md)                                        │
│      │  "✓ COMPLIANT — ADR-001 (Requirement Traceability)"          │
│      ▼                                                              │
│  Commit & CHANGELOG                                                 │
│      "feat(loader): FR-042 add data file support"                   │
└─────────────────────────────────────────────────────────────────────┘
```

Each layer reinforces the next:

- **Scripture** (`.github/copilot-instructions.md`) defines the doctrine — the non-negotiable rules that govern development, including ADR-001 which mandates requirement traceability.
- **ARCHITECTURE.md** translates doctrine into numbered requirements (`REQ-YG-XXX`), grouped by capability.
- **Test code** proves requirements via `@pytest.mark.req("REQ-YG-XXX")` decorators.
- **Pre-commit hooks** enforce coverage — no commit lands if a requirement lacks tests.
- **The Inquisitor** (an LLM agent) periodically audits the chain and reports drift.

This is not aspirational. It runs on every commit.

---

## 2. The Requirement Structure

### Capabilities and Requirements in ARCHITECTURE.md

YAMLGraph organizes its architecture around *capabilities* — numbered groups of related functionality. Each capability contains a table of requirements:

```markdown
### 1. Configuration Loading & Validation

Load YAML graph configs, validate schemas, build state models,
and ensure graph integrity through linting.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-001 | Load graph configurations from YAML files | `graph_loader.load_graph_config`, `cli/helpers`, `data_loader` |
| REQ-YG-002 | Validate graph configuration schemas and structures | `models/graph_schema`, `utils/validators` |
| REQ-YG-003 | Perform linting and pattern validation | `linter/graph_linter`, `linter/checks`, `linter/patterns/*` |
| REQ-YG-004 | Handle errors during configuration loading | `cli/helpers.GraphLoadError`, `data_loader.DataFileError` |
```

Each row captures three things:

1. **A unique identifier** (`REQ-YG-001`) — the anchor that tests, commits, and audits reference.
2. **A description** — what the system must do, in plain language.
3. **Key modules** — where the implementation lives, creating the requirement → code link.

### The Numbering Scheme

Requirements use the pattern `REQ-YG-XXX` where `XXX` is a zero-padded three-digit number:

- `REQ-YG-001` through `REQ-YG-004` → CAP-01: Config Loading & Validation
- `REQ-YG-005` through `REQ-YG-008` → CAP-02: Graph Compilation
- `REQ-YG-009` through `REQ-YG-011`, `REQ-YG-050` → CAP-03: Node Execution
- ...continuing through...
- `REQ-YG-091`, `REQ-YG-092` → CAP-32: eBook Authoring Pipeline

Numbers are assigned sequentially as capabilities are added. They are never reused — when a capability is retired (e.g., CAP-27 and CAP-29 were relocated to `projects/`), its requirement numbers are removed from the tracked set, not reassigned. This prevents historical references from becoming ambiguous.

### The Capability Map

The `scripts/req_coverage.py` script maintains the authoritative mapping from capabilities to requirements:

```python
CAPABILITIES: dict[str, tuple[str, list[str]]] = {
    "CAP-01": (
        "Config Loading & Validation",
        ["REQ-YG-001", "REQ-YG-002", "REQ-YG-003", "REQ-YG-004"],
    ),
    "CAP-02": (
        "Graph Compilation",
        ["REQ-YG-005", "REQ-YG-006", "REQ-YG-007", "REQ-YG-008"],
    ),
    # ...32 capabilities total
    "CAP-32": (
        "eBook Authoring Pipeline",
        ["REQ-YG-091", "REQ-YG-092"],
    ),
}
```

This dictionary serves as both documentation and the executable truth that the coverage checker uses to verify completeness.

---

## 3. Test Tagging with @pytest.mark.req

### The Pattern

Every test function in YAMLGraph carries a `@pytest.mark.req` decorator linking it to one or more requirements:

```python
class TestLoadGraphConfig:
    """Tests for loading YAML graph configs."""

    @pytest.mark.req("REQ-YG-001", "REQ-YG-002", "REQ-YG-005")
    def test_load_valid_yaml(self, sample_yaml_file):
        """Load a valid graph YAML file."""
        config = load_graph_config(sample_yaml_file)

        assert isinstance(config, GraphConfig)
        assert config.name == "test_graph"
        assert config.version == "1.0"

    @pytest.mark.req("REQ-YG-001", "REQ-YG-002", "REQ-YG-005")
    def test_load_missing_file_raises(self, tmp_path):
        """FileNotFoundError for missing file."""
        missing = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            load_graph_config(missing)
```

This test from `tests/unit/test_graph_loader.py` demonstrates the core principle: `test_load_valid_yaml` proves three requirements simultaneously — that YAML loading works (REQ-YG-001), that validation succeeds (REQ-YG-002), and that the result is a compilable graph definition (REQ-YG-005).

### The Many-to-Many Relationship

The relationship between tests and requirements is many-to-many:

**One test can cover multiple requirements.** The `test_load_valid_yaml` example above covers REQ-YG-001, REQ-YG-002, and REQ-YG-005 because loading a valid YAML file exercises the loader, validator, and compiler entry point in a single path.

**One requirement can have multiple tests.** REQ-YG-014 (synchronous prompt execution) has 11 tests across `test_executor.py` covering different execution scenarios — structured output, retries, error handling, and variable resolution.

**Tests can combine requirements from different capabilities.** The retry tests in `test_executor_retry.py` tag both REQ-YG-014 (prompt execution) and REQ-YG-031 (retry capability):

```python
@pytest.mark.req("REQ-YG-014", "REQ-YG-031")
def test_retries_on_retryable_error_then_succeeds(self, mock_sleep):
    """Retryable error triggers retry; second attempt succeeds."""
    ...
```

This cross-capability tagging reveals how features compose — you can't test retries without executing a prompt, so both requirements must be cited.

### Self-Enforcement: REQ-YG-063

YAMLGraph even has a requirement that *the traceability system itself works*. REQ-YG-063 (Testing & Quality) is proven by `test_requirement_enforcement.py`:

```python
@pytest.mark.req("REQ-YG-063")
def test_untagged_test_is_rejected(tmp_path: Path):
    """Verify pytest fails when a test lacks @pytest.mark.req."""
    # Create a test file without @pytest.mark.req
    test_file = tmp_path / "test_example.py"
    test_file.write_text(
        textwrap.dedent(
            """
            def test_missing_req_tag():
                '''This test has no @pytest.mark.req tag.'''
                assert True
            """
        )
    )

    # Copy conftest.py to tmp_path so enforcement hook is active
    conftest_src = Path(__file__).parent.parent / "conftest.py"
    conftest_dst = tmp_path / "conftest.py"
    conftest_dst.write_text(conftest_src.read_text())

    # Run pytest via subprocess - should fail at collection
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
        capture_output=True,
        text=True,
    )

    # Should fail with UsageError (non-zero exit)
    assert result.returncode != 0, \
        "Pytest should reject tests without @pytest.mark.req"
    assert (
        "REQUIREMENT TRACEABILITY VIOLATION" in result.stderr
    ), f"Expected enforcement error message in stderr. Got: {result.stderr}"
```

This is the ouroboros of the traceability chain: a test that proves the system will reject tests that lack traceability markers. The doctrine enforces itself.

---

## 4. The Enforcement Script: req_coverage.py

### How It Works

The script `scripts/req_coverage.py` is the mechanical heart of ADR-001. It uses Python's `ast` module to parse every test file, extract `@pytest.mark.req` decorators, and cross-reference them against the canonical list of requirements.

```python
# All known requirements (framework only)
_ALL_FRAMEWORK_REQS = (
    list(range(1, 78))   # REQ-YG-001 through REQ-YG-077
    + [83]               # REQ-YG-083 (CAP-28 Thinking Budget)
    + [87, 89]           # REQ-YG-087, REQ-YG-089 (CAP-30 Copilot Node)
    + [90]               # REQ-YG-090 (CAP-31 Chaplain Diary Append)
    + [91, 92]           # REQ-YG-091, REQ-YG-092 (CAP-32 eBook Authoring Pipeline)
)
ALL_REQS = [f"REQ-YG-{i:03d}" for i in _ALL_FRAMEWORK_REQS]
```

The script walks `tests/unit/` and `tests/integration/`, parses each `test_*.py` file as an AST, and collects every `@pytest.mark.req(...)` invocation. It then reports:

1. **Summary** — how many of the total requirements are covered.
2. **Per-capability breakdown** — which capabilities have full, partial, or zero coverage.
3. **Uncovered requirements** — the specific REQ-YG-XXX identifiers with no tests.

### Three Modes of Operation

**Summary mode** (default):

```bash
$ python scripts/req_coverage.py
======================================================================
REQUIREMENT TRACEABILITY REPORT
======================================================================

Requirements: 82/82 covered
Tagged tests: 247 unique, 389 test-req pairs

CAPABILITY COVERAGE
----------------------------------------------------------------------
  ✅ CAP-01 Config Loading & Validation: 4/4 reqs, 28 tests
  ✅ CAP-02 Graph Compilation: 4/4 reqs, 19 tests
  ✅ CAP-03 Node Execution: 4/4 reqs, 16 tests
  ✅ CAP-04 Prompt Execution: 5/5 reqs, 34 tests
  ...
  ✅ CAP-32 eBook Authoring Pipeline: 2/2 reqs, 8 tests
```

**Detail mode** (`--detail`) shows which specific tests cover each requirement:

```bash
$ python scripts/req_coverage.py --detail
...
DETAILED MAPPING
----------------------------------------------------------------------

  REQ-YG-001 (15 tests):
    - test_graph_loader::TestLoadGraphConfig::test_load_valid_yaml
    - test_graph_loader::TestLoadGraphConfig::test_load_missing_file_raises
    - test_graph_loader::TestLoadGraphConfig::test_parse_nodes
    ...

  REQ-YG-014 (11 tests):
    - test_executor::TestPromptExecution::test_basic_execution
    - test_executor::TestPromptExecution::test_structured_output
    ...
```

**Implementation mode** (`--implementation`) traces the full chain from requirement to source code to test, using both coverage data and AST analysis to determine which source files each test exercises:

```bash
$ python scripts/req_coverage.py --implementation
...
IMPLEMENTATION TRACEABILITY
======================================================================

── CAP-01 Config Loading & Validation (4 reqs, 28 tests) ──────────

    REQ-YG-001  Load graph configurations from YAML files
      (3 files, 15 tests)
      Implementation:
        yamlgraph/graph_loader.py
        yamlgraph/cli/helpers.py
        yamlgraph/data_loader.py
      Tests (coverage):
        test_graph_loader::TestLoadGraphConfig::test_load_valid_yaml
        ...
```

**Strict mode** (`--strict`) makes the script exit with code 1 if any requirement has zero tests — this is the mode used by the pre-commit hook.

### Pre-commit Integration

The `.pre-commit-config.yaml` includes `req_coverage.py --strict` as a gate that runs on every commit:

```yaml
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

This means:

- **Every commit** runs the requirement coverage check.
- **If any requirement has zero tests**, the commit is blocked.
- **No `--no-verify` escape** — the Scripture declares that bypassing hooks results in "immediate termination; automatically enforced by CI."

The pre-commit hook is the mechanical enforcement of ADR-001. It doesn't care about intent, deadlines, or excuses. If the requirement isn't tested, the code doesn't ship.

---

## 5. Conventional Commits Integration

### The Traceability Chain in Commits

Requirements don't just link to tests — they link forward into the project history through conventional commits and feature requests:

```
REQ-YG-091 (requirement)
    ↓
test_ebook_writing.py::test_chapter_generation (test)
    ↓
yamlgraph/ebook/ (implementation)
    ↓
feat(ebook): FR-100 add eBook authoring pipeline (commit)
    ↓
CHANGELOG.md: "Added: eBook authoring pipeline (CAP-32)" (release note)
```

The commit message format `feat(scope): FR-XXX description` encodes three signals:

1. **`feat`** — the type (following Conventional Commits), telling CI what kind of change this is.
2. **`(scope)`** — the affected subsystem, often matching a capability name.
3. **`FR-XXX`** — the feature request identifier, linking to the planning document that motivated the change.

### Feature Requests Bridge Requirements to Implementation

Feature requests in `feature-requests/` are the planning layer between requirements and code. A typical FR references:

- The **capability** being extended (e.g., CAP-32)
- The **requirements** being added or modified (e.g., REQ-YG-091, REQ-YG-092)
- The **acceptance criteria** that map to test assertions
- The **implementation approach** that maps to code changes

When the FR is implemented, the commit references the FR, and the CHANGELOG references the capability. The chain is complete:

```
Doctrine → Requirement → FR → Test → Code → Commit → CHANGELOG
```

Every link is verifiable. You can start from a CHANGELOG entry and trace backward to the doctrine that motivated it, or start from a doctrine rule and trace forward to every test that proves it.

---

## 6. Pervasive Verification

### The LLM's Role in Maintaining Traceability

In YAMLGraph's development workflow, LLM agents (Copilot, the Chaplain, the Inquisitor) are active participants in the traceability chain. They don't just generate code — they maintain the integrity of the system.

**When adding a new capability**, the workflow is:

1. **Add requirements** to `ARCHITECTURE.md` under a new `CAP-XX` section with `REQ-YG-XXX` entries.
2. **Extend `req_coverage.py`** — add the new requirement numbers to `_ALL_FRAMEWORK_REQS` and the new capability to `CAPABILITIES`.
3. **Write tests** with `@pytest.mark.req("REQ-YG-XXX")` decorators.
4. **Implement** the feature.
5. **Commit** with `feat(scope): FR-XXX description`.

The doctrine from `.github/copilot-instructions.md` states this explicitly:

> When adding a new capability: add requirement(s) to `ARCHITECTURE.md`, extend `ALL_REQS` range and `CAPABILITIES` dict in `scripts/req_coverage.py`, tag tests with the new req ID.

**When tests fail**, the traceability chain tells you immediately *which requirement is violated*. A failing `test_load_valid_yaml` doesn't just mean "something broke in the loader" — it means REQ-YG-001, REQ-YG-002, and REQ-YG-005 are all potentially compromised. This transforms debugging from "what broke?" to "which contract is violated?"

**When doctrine changes**, the chain flows forward: if a new commandment is added to the Scripture, it may require new requirements in ARCHITECTURE.md, which require new tests, which require new code. The traceability matrix makes the blast radius explicit — you can query which requirements would need updating and which tests would need amending.

---

## 7. The Inquisitor's Verification Runs

### Auditing ADR-001 Compliance

The Inquisitor is an LLM agent that periodically audits the codebase against doctrine. Its verification runs check ADR-001 compliance as a standard audit item, producing findings like this:

> **Context:** Audit of HEAD (`a9bffc8`), covering 5 commits: `a9bffc8` (fix: FR-103 per-chapter persistence), `0704063` (docs: FR-103 diary), `b0fa74c` (feat: FR-103 judge-amend subgraph), `9048d03` (docs: FR-100 progress), `bd1d6ce` (feat: FR-100 ebook scaffold). Two `feat` and one `fix` commit introduce or restore capabilities. Audited against Commandments, ADR-001, Confessions, and the Sermon.
>
> **Findings:**
>
> - ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** REQ-YG-091 and REQ-YG-092 both present in ARCHITECTURE.md. 8 tests across `test_ebook_writing.py` (4) and `test_ebook_doctrine_validation.py` (4) all carry `@pytest.mark.req` tags. Full chain intact.

The Inquisitor doesn't just check that requirements *exist* — it traces the full chain:

1. Are the requirement IDs in `ARCHITECTURE.md`?
2. Are they registered in `req_coverage.py`?
3. Do tests carry the corresponding `@pytest.mark.req` tags?
4. Do commits reference the correct FRs?

### What Drift Looks Like

When the Inquisitor finds a break in the chain, it reports drift explicitly. From a recent audit:

> - ⚠ DRIFT — **Co-authored-by trailer:** 0/5 commits include the required `Co-authored-by: Copilot` trailer. Recurring accepted deviation — awaiting mechanical enforcement via pre-commit hook.

This is a textbook example of the traceability philosophy: the doctrine requires something (Co-authored-by trailer), the audit detects its absence, and the finding persists until either the doctrine is amended or the enforcement is mechanized. The system doesn't forget.

### The Correction Flow

When the Inquisitor detects traceability drift, the correction follows the Rite of Correction:

1. **Inspect** — The audit identifies the specific break: which requirement is missing tests, which tests lack markers, which commits lack FR references.
2. **Amend** — Write the failing test first, then fix the gap.
3. **Escalate** — If the fix requires scope beyond a quick patch, create a feature request citing the audit findings.

The subsequent audit then verifies the fix:

> - ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** REQ-YG-091 and REQ-YG-092 both present in ARCHITECTURE.md. 8 tests across `test_ebook_writing.py` (4) and `test_ebook_doctrine_validation.py` (4) all carry `@pytest.mark.req` tags. Full chain intact.

The keyword is *"Full chain intact."* This is the Inquisitor's way of saying: doctrine → requirement → test → code → commit — every link verified.

### A Real Audit Entry

Here is an abridged Inquisitor audit from the diary, demonstrating both compliance and drift detection in a single review:

```markdown
## 2026-02-25: Inquisitor Audit — FR-103 Cycle Complete, Doctrine Holding

**Context:** Audit of HEAD (`0704063`), covering 5 commits. Two `feat` commits
introduce new capabilities (CAP-32, REQ-YG-091, REQ-YG-092). Audited against
all 10 Commandments, ADR-001, Confessions, and the Sermon.

**Findings:**

- ✓ COMPLIANT — **Conventional Commits + CHANGELOG (Commandment 10):** All 5
  commits use correct type/scope/FR-tag format. Both `feat` commits have
  corresponding CHANGELOG 0.4.58 entries.
- ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** REQ-YG-091 (4 tests in
  `test_ebook_writing.py`) and REQ-YG-092 (4 tests in
  `test_ebook_doctrine_validation.py`) all carry `@pytest.mark.req` tags. Both
  requirements documented in ARCHITECTURE.md. `req_coverage.py` updated.
- ✓ COMPLIANT — **Distill (Sermon):** FR-103 has a diary entry documenting the
  normalize-at-boundary trap, the FR-101→FR-102→FR-103 convergence path, and
  a seed for generalizing the judge-amend pattern.
- ⚠ DRIFT — **Co-authored-by trailer:** 0/5 commits include the required
  trailer. Accepted deviation per prior ruling.

**Heuristic:** A full FR cycle (FR-100→FR-101→FR-102→FR-103) that ends with a
diary entry closing every prior audit finding is the doctrine working as
designed.
```

Notice how the Inquisitor explicitly traces the REQ → test → ARCHITECTURE.md → `req_coverage.py` chain. This isn't a style check — it's a structural audit of whether the traceability loop is closed.

---

## 8. Why This Matters

The traceability matrix prevents four categories of failure:

### Untested Features (Requirements Without Tests)

Without traceability enforcement, it's easy to add a requirement to ARCHITECTURE.md, implement it, and forget to write tests. The pre-commit hook running `req_coverage.py --strict` makes this mechanically impossible — the commit is blocked until every requirement has at least one test carrying its `@pytest.mark.req` tag.

### Orphan Tests (Tests Proving Nothing)

A test without a `@pytest.mark.req` decorator is a test that proves no requirement. It may pass, but it contributes nothing to the system's verified contract. The pytest plugin enforced by REQ-YG-063 rejects such tests at collection time — they cannot run, let alone pass.

### Doctrine Drift (Scripture Disconnected from Code)

The Scripture says "every test function must have `@pytest.mark.req`." If this rule were merely advisory, it would erode within weeks. Instead, the pre-commit hook enforces it mechanically, and the Inquisitor audits it periodically. The chain from doctrine to enforcement is itself enforced.

### Commit Chaos (Features Without Traceability)

Without the conventional commit format (`feat(scope): FR-XXX description`), the project history becomes an undifferentiated stream of changes. With it, every feature can be traced back through its FR to the requirements it fulfills and forward through the CHANGELOG to its public documentation.

---

### The Closed Loop

```
         ┌──────────────────────────────────────┐
         │         The Traceability Loop          │
         │                                        │
         │   Doctrine ──────► Requirements        │
         │      ▲                    │             │
         │      │                    ▼             │
         │   Inquisitor         Tests              │
         │   Audits                  │             │
         │      ▲                    ▼             │
         │      │              Implementation      │
         │      │                    │             │
         │      │                    ▼             │
         │   CHANGELOG ◄──── Commit + FR          │
         │                                        │
         └──────────────────────────────────────┘
```

Every link in this loop is mechanically enforced or periodically verified. The system has no gaps where a requirement can exist without proof, where a test can exist without purpose, or where a commit can land without traceability.

This is what living documentation looks like: not a document that describes the system, but a system that *is* the document.

---

*Next: [Chapter 07](07-changelog-evolution.md) — how the CHANGELOG bears witness to the evolution of the Word.*
