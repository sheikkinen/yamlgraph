# Chapter 06: Requirement Traceability Matrix

*How YAMLGraph creates a closed loop from doctrine to code — and back again.*

---

## 1. The Vision: Living Documentation

Most software projects maintain requirements in separate documents — PDFs, wikis, Jira tickets — disconnected from the code that implements them. Requirements drift. Tests prove nothing in particular. Features ship without anyone knowing which objective they satisfy. The gap between what the system *should do* and what tests *actually verify* widens silently, until a production incident reveals it.

YAMLGraph takes a different approach: **requirements live in the codebase itself**, forming a closed loop that can be verified mechanically at every commit.

The loop has five links:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Scripture (.github/copilot-instructions.md)               │
│   "Every test function must have @pytest.mark.req..."       │
│                          │                                  │
│                          ▼                                  │
│   ARCHITECTURE.md                                           │
│   REQ-YG-001 ... REQ-YG-092  (numbered requirements)       │
│                          │                                  │
│                          ▼                                  │
│   Tests (tests/unit/, tests/integration/)                   │
│   @pytest.mark.req("REQ-YG-042") ← proves requirement      │
│                          │                                  │
│                          ▼                                  │
│   Pre-commit hooks (req_coverage.py --strict)               │
│   ← blocks commit if any requirement has zero tests         │
│                          │                                  │
│                          ▼                                  │
│   Inquisitor (post-commit audit)                            │
│   ← verifies chain integrity, detects drift                 │
│                          │                                  │
│                          └──────────────────────────────────┘
│                             (feeds back into doctrine)       │
└─────────────────────────────────────────────────────────────┘
```

**Scripture** (`.github/copilot-instructions.md`) defines the doctrine — the ADR-001 decision that every test must link to a requirement:

> Every test function must have `@pytest.mark.req("REQ-YG-XXX")` linking it to a requirement in `ARCHITECTURE.md`.

**ARCHITECTURE.md** translates that doctrine into numbered requirements grouped by capability. Each `REQ-YG-XXX` defines *what* the system must do and *which modules* implement it.

**Tests** prove the requirements via `@pytest.mark.req` decorators. The marker creates a machine-readable link from test to requirement.

**Pre-commit hooks** enforce coverage — `req_coverage.py --strict` runs before every commit and fails if any requirement has zero tests.

**The Inquisitor** (a post-commit LLM audit) verifies the chain's integrity: are the markers correct? Do commit messages reference the right feature requests? Has doctrine drifted from implementation?

This is not documentation *about* the code. It is documentation *that is* the code.

---

## 2. The Requirement Structure

Requirements in `ARCHITECTURE.md` follow a strict pattern. Each capability is a numbered group with a description, and each requirement within it maps to specific implementation modules.

### Capability Summary Table

The top-level summary maps every capability to its requirement range:

```markdown
| # | Capability | Primary Modules | Requirements |
|---|-----------|----------------|--------------|
| 1 | Configuration Loading & Validation | `graph_loader`, `models/graph_schema`, `utils/validators`, `linter/`, `data_loader` | REQ-YG-001 – 004 |
| 2 | Graph Compilation | `graph_loader`, `node_compiler` | REQ-YG-005 – 008 |
| 3 | Node Execution | `node_factory/llm_nodes`, `node_factory/streaming`, `utils/llm_factory`, `utils/llm_factory_async` | REQ-YG-009 – 011, 050 |
```

### Per-Capability Requirement Tables

Each capability expands into a detailed table with three columns — the requirement ID, a human-readable description, and the modules that implement it:

```markdown
### 1. Configuration Loading & Validation

Load YAML graph configs, validate schemas, build state models, and
ensure graph integrity through linting.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-001 | Load graph configurations from YAML files | `graph_loader.load_graph_config`, `cli/helpers`, `data_loader` |
| REQ-YG-002 | Validate graph configuration schemas and structures | `models/graph_schema`, `utils/validators` |
| REQ-YG-003 | Perform linting and pattern validation | `linter/graph_linter`, `linter/checks`, `linter/patterns/*` |
| REQ-YG-004 | Handle errors during configuration loading | `cli/helpers.GraphLoadError`, `data_loader.DataFileError` |
```

### The REQ-YG Numbering Scheme

Requirements use the format `REQ-YG-XXX` where XXX is a zero-padded three-digit number:

- **REQ-YG-001 through REQ-YG-077**: Core framework requirements (CAP-01 through CAP-26)
- **REQ-YG-083**: Graph-level thinking budget (CAP-28)
- **REQ-YG-087, REQ-YG-089**: Copilot node (CAP-30)
- **REQ-YG-090**: Chaplain diary append (CAP-31)
- **REQ-YG-091, REQ-YG-092**: eBook authoring pipeline (CAP-32)

Numbers are *stable identifiers*. When requirements are retired or relocated (e.g., REQ-YG-078–082 moved to project-scoped tracking, REQ-YG-088 was dropped as overengineering), their numbers are not reused. This preserves cross-references in commit messages, diary entries, and test markers.

As the `req_coverage.py` script declares:

```python
# REQ-YG-078-082 (CAP-27) and REQ-YG-084-086 (CAP-29) relocated to projects/ with OC/IC-XXX tags
# REQ-YG-088 (sampling backend) was DROPPED as overengineering (FR-082)
_ALL_FRAMEWORK_REQS = (
    list(range(1, 78))  # REQ-YG-001 through REQ-YG-077
    + [83]  # REQ-YG-083 (CAP-28 Thinking Budget)
    + [87, 89]  # REQ-YG-087, REQ-YG-089 (CAP-30 Copilot Node) — 088 dropped
    + [90]  # REQ-YG-090 (CAP-31 Chaplain Diary Append)
    + [91, 92]  # REQ-YG-091, REQ-YG-092 (CAP-32 eBook Authoring Pipeline)
)
```

The gaps in numbering tell a story. They are scars from decisions — features reconsidered, scope relocated, overengineering caught and purged.

---

## 3. Test Tagging with @pytest.mark.req

The `@pytest.mark.req` decorator is the bridge between architecture and code. It declares: "this test proves this requirement."

### Basic Pattern

```python
import pytest

@pytest.mark.req("REQ-YG-014")
def test_synchronous_prompt_execution():
    """Verify that execute_prompt() calls LLM and returns structured output."""
    result = execute_prompt("test_prompt", {"topic": "testing"})
    assert result is not None
    assert isinstance(result, ExpectedModel)
```

### Multi-Requirement Tagging

A single test can prove multiple requirements. This is common for integration-level tests that exercise several capabilities in one flow:

```python
@pytest.mark.req("REQ-YG-001", "REQ-YG-002", "REQ-YG-005")
def test_load_and_compile_graph(self):
    """Loading a graph validates config (001, 002) and compiles it (005)."""
    config = load_graph_config(self.graph_path)
    assert config.metadata.name == "test-graph"
    graph = compile_graph(config)
    assert graph is not None
```

In the YAMLGraph test suite, this pattern appears extensively. The `test_graph_loader.py` file, for example, tags nearly every test with `("REQ-YG-001", "REQ-YG-002", "REQ-YG-005")` because loading, validating, and compiling are inseparable in practice.

### Class-Level Tagging

When every test in a class covers the same requirement, the marker can be applied at the class level:

```python
@pytest.mark.req("REQ-YG-027")
class TestErrorHandlingStrategies:
    def test_skip_strategy(self): ...
    def test_fail_strategy(self): ...
    def test_retry_strategy(self): ...
```

The enforcement script understands both patterns — it applies class-level markers to all methods within the class.

### The Many-to-Many Relationship

The relationship between tests and requirements is many-to-many:

- **One test → many requirements**: A graph compilation test may prove loading (001), validation (002), and compilation (005) simultaneously.
- **One requirement → many tests**: REQ-YG-014 (synchronous prompt execution) has 11 tests in `test_executor.py` alone, each covering a different aspect — basic invocation, retry behavior, error handling, structured output.

This creates a dense web of traceability. When a test fails, you know *exactly which requirements are at risk*. When a requirement changes, you know *exactly which tests must be updated*.

### The Enforcement Hook

The `@pytest.mark.req` marker is not just advisory — it's enforced. In `tests/conftest.py`, a pytest collection hook rejects any test that lacks the marker:

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

An untagged test doesn't just fail — it prevents the *entire* test suite from running. This is a deliberate design choice: orphan tests are treated as a traceability defect, not a testing defect.

This enforcement itself is tested. REQ-YG-063 in `test_requirement_enforcement.py` verifies that the hook works in both directions:

```python
@pytest.mark.req("REQ-YG-063")
def test_untagged_test_is_rejected(tmp_path):
    """Verify pytest fails when a test lacks @pytest.mark.req."""
    # Creates an untagged test, runs pytest, asserts failure
    ...

@pytest.mark.req("REQ-YG-063")
def test_tagged_test_is_accepted(tmp_path):
    """Verify pytest allows tests with proper @pytest.mark.req."""
    # Creates a tagged test, runs pytest, asserts success
    ...
```

A test that tests the testing enforcement — the traceability system is self-referential. The guard is guarded.

---

## 4. The Enforcement Script: req_coverage.py

While `conftest.py` enforces that every test *has* a marker, `scripts/req_coverage.py` answers a different question: does every *requirement* have at least one test?

### How It Works

The script uses Python's `ast` module to parse every test file and extract `@pytest.mark.req` decorators. It then cross-references against the master list of requirements (`ALL_REQS`) to find gaps.

```python
def extract_req_markers(filepath: Path) -> dict[str, list[str]]:
    """Extract @pytest.mark.req(...) markers from a test file.

    Returns mapping of requirement ID -> list of test names.
    Uses class-qualified keys (Class::method) to avoid collisions
    when multiple classes share method names."""
    tree = ast.parse(filepath.read_text(), filename=str(filepath))
    # ... walks AST, finds decorators, extracts REQ-YG-XXX strings
```

The script uses class-qualified keys (`stem::ClassName::method`) to avoid collisions when multiple test classes share method names.

### Three Modes of Operation

**Summary mode** (default): Shows coverage statistics per capability.

```
$ python scripts/req_coverage.py
======================================================================
REQUIREMENT TRACEABILITY REPORT
======================================================================

Requirements: 83/83 covered
Tagged tests: 412 unique, 1754 test-req pairs

CAPABILITY COVERAGE
----------------------------------------------------------------------
  ✅ CAP-01 Config Loading & Validation: 4/4 reqs, 89 tests
  ✅ CAP-02 Graph Compilation: 4/4 reqs, 72 tests
  ✅ CAP-03 Node Execution: 4/4 reqs, 48 tests
  ✅ CAP-04 Prompt Execution: 5/5 reqs, 61 tests
  ✅ CAP-05 Tool & Agent Integration: 4/4 reqs, 34 tests
  ...
```

**Detail mode** (`--detail`): Shows which specific tests cover each requirement.

```
$ python scripts/req_coverage.py --detail

DETAILED MAPPING
----------------------------------------------------------------------

  REQ-YG-001 (18 tests):
    - test_graph_loader::TestLoadGraphConfig::test_load_basic_graph
    - test_graph_loader::TestLoadGraphConfig::test_load_graph_with_metadata
    - test_graph_loader::TestLoadGraphConfig::test_load_graph_with_nodes
    ...

  REQ-YG-014 (11 tests):
    - test_executor::TestPromptExecutor::test_execute_basic
    - test_executor::TestPromptExecutor::test_execute_with_schema
    ...
```

**Strict mode** (`--strict`): Exits with code 1 if any requirement has zero tests. This is the mode used by pre-commit hooks.

```
$ python scripts/req_coverage.py --strict
# Exit code 0: all requirements covered
# Exit code 1: gaps found — commit blocked
```

### Implementation Traceability Mode

The script also supports `--implementation` mode, which traces the full chain from requirement → source files → tests, using either coverage data or AST-based import analysis as a fallback:

```
$ python scripts/req_coverage.py --implementation

IMPLEMENTATION TRACEABILITY
======================================================================

── CAP-01 Config Loading & Validation (4 reqs, 89 tests) ─────

    REQ-YG-001  Load graph configurations from YAML files
      (3 files, 18 tests)
      Implementation:
        yamlgraph/graph_loader.py
        yamlgraph/cli/helpers.py
        yamlgraph/data_loader.py
      Tests (AST imports):
        test_graph_loader::TestLoadGraphConfig::test_load_basic_graph
        ...
```

### The Capability Map

The script maintains a `CAPABILITIES` dictionary that groups requirements by capability — the same grouping as `ARCHITECTURE.md`:

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
    # ... 30+ capabilities
}
```

This dictionary *must stay in sync* with ARCHITECTURE.md. When a new capability is added, three things must happen simultaneously:

1. Add the requirement table to `ARCHITECTURE.md`
2. Add the requirement IDs to `ALL_REQS` and `CAPABILITIES` in `req_coverage.py`
3. Tag tests with the new `REQ-YG-XXX`

If any one of these is missed, either the pre-commit hook or the Inquisitor will catch the drift.

### Pre-commit Integration

The script runs as a pre-commit hook in `.pre-commit-config.yaml`:

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

The `always_run: true` setting means it runs on *every* commit, not just when test files change. A code change that removes test coverage will be caught even if the test files themselves weren't modified. Combined with `fail_fast: true` at the repo level, a traceability gap blocks the entire commit pipeline.

---

## 5. Conventional Commits Integration

Requirements don't just link tests to architecture — they flow through the entire change management chain.

### The Commit Chain

```
Feature Request (FR-XXX)
    └── defines scope and acceptance criteria
         └── maps to requirements (REQ-YG-XXX)
              └── proven by tests (@pytest.mark.req)
                   └── committed (feat(scope): FR-XXX description)
                        └── recorded (CHANGELOG.md)
```

### Commit Message Format

YAMLGraph uses Conventional Commits with mandatory feature request references for `feat:` commits:

```
feat(ebook): FR-100 add eBook authoring pipeline
fix(streaming): FR-030 handle provider disconnect during astream
docs: FR-103 update diary with judge-amend reflection
```

The pre-commit config enforces this mechanically:

```yaml
- id: feat-requires-fr
  name: feat commits require FR-XXX
  entry: "bash -c 'msg=$(cat \"$1\"); if echo \"$msg\" | grep -qE
    \"^feat(\\(.*\\))?:\" && ! echo \"$msg\" | grep -qE \"FR-[0-9]+\";
    then echo \"ERROR: feat: commits require FR-XXX reference\";
    echo \"Example: feat: FR-038 add commit enforcement\"; exit 1; fi' _"
```

A `feat:` commit without `FR-XXX` is rejected. This ensures every new feature traces back to a feature request, which in turn traces to requirements.

### CHANGELOG as Witness

The same pre-commit config requires that `feat:` and `fix:` commits include changes to `CHANGELOG.md`:

```yaml
- id: changelog-required
  name: feat/fix commits require CHANGELOG.md
  entry: "bash -c 'msg=$(cat \"$1\"); if echo \"$msg\" | grep -qE
    \"^(feat|fix)(\\(.*\\))?:\" && ! git diff --cached --name-only |
    grep -qE \"^CHANGELOG\\.md$\"; then echo \"ERROR: feat:/fix: commits
    must include CHANGELOG.md changes\";
    echo \"Add your entry under the current [Unreleased] or version heading.\"; exit 1; fi' _"
```

This creates the final link in the chain: features are logged publicly in the changelog, with entries that reference capabilities:

```markdown
## [0.4.58] - 2026-02-25

### Added
- CAP-32: eBook authoring pipeline with per-chapter graphs (FR-100/FR-103)
```

The chain is now complete and auditable: **REQ → test → code → commit → changelog**.

---

## 6. Pervasive Verification

The LLM agents that develop YAMLGraph are not just code generators — they are participants in the traceability loop. The doctrine in `.github/copilot-instructions.md` instructs them explicitly:

> When adding a new capability: add requirement(s) to `ARCHITECTURE.md`, extend `ALL_REQS` range and `CAPABILITIES` dict in `scripts/req_coverage.py`, tag tests with the new req ID.

### When Adding a Capability

An agent adding, say, a new "Copilot Node" capability must:

1. **Add requirements** to `ARCHITECTURE.md`:
   ```markdown
   ### 30. Copilot Node

   | Requirement | Description | Key Modules |
   |------------|-------------|-------------|
   | REQ-YG-087 | Copilot node creates subprocess agent | `node_factory/copilot_node` |
   | REQ-YG-089 | Copilot task prompt with file context | `node_factory/copilot_node` |
   ```

2. **Update the enforcement script** (`scripts/req_coverage.py`):
   ```python
   _ALL_FRAMEWORK_REQS = (
       ...
       + [87, 89]  # REQ-YG-087, REQ-YG-089 (CAP-30 Copilot Node)
   )

   CAPABILITIES = {
       ...
       "CAP-30": ("Copilot Node", ["REQ-YG-087", "REQ-YG-089"]),
   }
   ```

3. **Write tests with markers**:
   ```python
   @pytest.mark.req("REQ-YG-087")
   def test_copilot_node_creates_subprocess():
       ...

   @pytest.mark.req("REQ-YG-089")
   def test_copilot_task_prompt_with_file_context():
       ...
   ```

4. **Commit with FR reference**:
   ```
   feat(copilot-node): FR-090 add copilot subprocess node
   ```

If the agent skips step 2, the pre-commit hook (`req_coverage.py --strict`) won't know the new requirements exist — they'll pass silently. But the Inquisitor will catch the gap when it audits ARCHITECTURE.md against the enforcement script.

If the agent skips step 3, the pre-commit hook *will* catch it: the new requirements will appear in `ALL_REQS` with zero tests, and `--strict` mode will block the commit.

### When Tests Fail

When a test fails, the `@pytest.mark.req` marker tells you immediately *which requirement is at risk*:

```
FAILED tests/unit/test_executor.py::TestPromptExecutor::test_execute_with_schema
```

This test carries `@pytest.mark.req("REQ-YG-014")` — synchronous prompt execution is broken. The developer (human or LLM) doesn't need to reason about *what* the test was supposed to prove; the marker makes it explicit.

### When Doctrine Changes

If a Commandment is updated in Scripture, the change propagates through the chain:

1. Scripture changes → which requirements in ARCHITECTURE.md are affected?
2. Requirements change → which tests need updating?
3. Tests update → does `req_coverage.py` still pass?

The traceability links make impact analysis mechanical rather than archaeological.

---

## 7. The Inquisitor's Verification Runs

The Inquisitor — a post-commit LLM audit triggered by `.pre-commit-config.yaml` — verifies the traceability chain's integrity after every commit. It doesn't just check that tests pass; it audits the *connections* between layers.

### What the Inquisitor Checks

From an actual audit entry (2026-02-25):

> **Context:** Audit of HEAD (`a9bffc8`), covering 5 commits. Two `feat` and one `fix` commit introduce or restore capabilities. Audited against Commandments, ADR-001, Confessions, and the Sermon.

The Inquisitor verifies:

- **ADR-001 compliance**: Are new requirements in ARCHITECTURE.md? Are tests tagged? Is `req_coverage.py` updated?
- **Conventional Commits**: Do `feat:` commits reference FR-XXX? Are CHANGELOG entries present?
- **Confessions**: Are any new `# noqa` suppressions documented?
- **Distill**: Did the developer write a metacognitive diary entry?

### What Compliance Looks Like

From the diary (2026-02-25, Inquisitor Audit — FR-103 Cycle Complete):

> ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** REQ-YG-091 (4 tests in `test_ebook_writing.py`) and REQ-YG-092 (4 tests in `test_ebook_doctrine_validation.py`) all carry `@pytest.mark.req` tags. Both requirements documented in ARCHITECTURE.md. `req_coverage.py` updated. Full traceability chain holds from prior commit.

Every link in the chain is explicitly verified: requirement exists → tests are tagged → enforcement script updated → the chain is intact.

### What Drift Looks Like

From the same audit:

> ⚠ DRIFT — **Co-authored-by trailer:** 0/5 commits include the required `Co-authored-by: Copilot` trailer. Recurring accepted deviation — awaiting mechanical enforcement via pre-commit hook.

Drift is categorized, not just detected. The Inquisitor notes whether drift is new, recurring, or accepted. Recurring drift that goes unresolved is itself flagged as entropy:

> **Heuristic:** When the same drift is flagged across 5+ audits without resolution, the finding has graduated from observation to technical debt. Either apply the existing fix or accept the drift formally — repeated flagging without action is itself entropy.

### The Correction Flow

When drift is detected, the correction flows backward through the traceability chain:

```
Inquisitor detects drift
    → Diary entry documents finding
        → Feature request created (if fix needed)
            → Requirements updated in ARCHITECTURE.md
                → Tests written with @pytest.mark.req
                    → Code implemented
                        → Pre-commit hooks verify
                            → Inquisitor confirms resolution
```

From the diary (2026-02-25):

> ✓ COMPLIANT — **Distill (Sermon):** FR-103 has a diary entry documenting the normalize-at-boundary trap, the FR-101→FR-102→FR-103 convergence path, and a seed for generalizing the judge-amend pattern. This resolves the prior audit's drift finding about missing Distill for this work.

The Inquisitor explicitly notes when a previously flagged drift is resolved — closing the loop.

---

## 8. Why This Matters

The traceability matrix is not bureaucracy. It is a machine-enforceable guarantee against four specific failure modes:

### Untested Features (Requirements Without Tests)

**Without traceability:** A developer adds a feature, writes no tests, ships it. The feature works until it doesn't. Nobody knows when it broke because nobody knows what "working" means for that feature.

**With traceability:** The requirement exists in `ARCHITECTURE.md`. The pre-commit hook (`req_coverage.py --strict`) blocks the commit until at least one test carries the `@pytest.mark.req` marker for that requirement. The feature cannot ship untested.

### Orphan Tests (Tests Proving Nothing)

**Without traceability:** A test passes. What does it prove? It asserts that some code returns some value. But which system capability does it protect? When requirements change, which tests should be updated? Nobody knows.

**With traceability:** Every test declares what it proves via `@pytest.mark.req`. The `conftest.py` hook rejects tests without markers — *they cannot even run*. There are no orphan tests because unlinked tests are collection errors, not test failures.

### Doctrine Drift (Scripture Disconnected from Code)

**Without traceability:** The architecture document says "all prompts must be in YAML." The code has three hardcoded prompts. The document and the code diverge silently.

**With traceability:** Doctrine defines requirements. Requirements demand tests. Tests exercise code. If the code violates doctrine, either a test fails (catching the violation) or a requirement is missing (caught by `req_coverage.py`). The Inquisitor audits the full chain periodically, catching subtler forms of drift.

### Commit Chaos (Features Without Traceability)

**Without traceability:** A commit message says "fix stuff." What requirement does it address? Which feature request does it complete? The git log is noise.

**With traceability:** `feat:` commits require `FR-XXX` references. `feat:` and `fix:` commits require CHANGELOG updates. Conventional commit format is enforced by pre-commit hooks. The git log becomes an auditable record of requirement fulfillment.

### The Numbers

At the time of writing, the YAMLGraph traceability matrix contains:

- **83 active requirements** across 30+ capabilities
- **1,754 test-requirement pairs** (many-to-many links)
- **412 unique tagged tests** across unit and integration suites
- **100% requirement coverage** enforced at every commit

These are not aspirational targets. They are pre-commit gates. A commit that drops coverage below 100% is mechanically rejected.

---

## Summary

The Requirement Traceability Matrix is YAMLGraph's answer to the oldest problem in software engineering: ensuring that what the system *does* is what the system *should do*. It works because every link in the chain is enforced mechanically:

| Layer | Artifact | Enforcement |
|-------|----------|-------------|
| Doctrine | `.github/copilot-instructions.md` | Inquisitor audit |
| Requirements | `ARCHITECTURE.md` (REQ-YG-XXX) | `req_coverage.py --strict` |
| Tests | `@pytest.mark.req("REQ-YG-XXX")` | `conftest.py` collection hook |
| Commits | `feat(scope): FR-XXX` | Conventional commit hook |
| Changelog | `CHANGELOG.md` entries | `changelog-required` hook |
| Integrity | Full chain verification | Inquisitor post-commit audit |

No link is optional. No link is advisory. What survives the fire may merge.

---

*Next: [Chapter 07](07-yamlgraph-core.md) — how it works, how to use it, how to extend it.*
