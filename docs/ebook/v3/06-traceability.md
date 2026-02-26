# Chapter 06: Requirement Traceability Matrix

> *"Every test must be linked to a requirement in ARCHITECTURE.md."*
> — ADR-001, Requirement Traceability

---

## 1. The Vision: Living Documentation

Most software projects treat requirements as artifacts that decay — Word documents in SharePoint, Jira epics nobody reads after sprint planning, PDFs that diverge from code within weeks. YAMLGraph rejects this entirely. Requirements live *in the repository*, enforced by the same CI pipeline that enforces code quality.

The traceability system forms a closed loop through five artifacts:

```
┌─────────────────────────────────────────────────────────┐
│                  The Traceability Loop                  │
│                                                         │
│   Scripture (.github/copilot-instructions.md)           │
│       │  defines doctrine (10 Commandments)             │
│       ▼                                                 │
│   ARCHITECTURE.md                                       │
│       │  translates doctrine → numbered requirements    │
│       │  REQ-YG-001 through REQ-YG-092                  │
│       ▼                                                 │
│   Test Files (tests/unit/, tests/integration/)          │
│       │  prove requirements via @pytest.mark.req()      │
│       ▼                                                 │
│   Pre-commit Hooks (.pre-commit-config.yaml)            │
│       │  enforce coverage: req_coverage.py --strict     │
│       │  enforce tagging: conftest.py collection hook   │
│       ▼                                                 │
│   LLM Agents (Inquisitor, Chaplain)                     │
│       │  verify and correct drift                       │
│       └──────────────► back to Scripture                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

Each link in this chain is mechanically enforced. You cannot commit a test without a `@pytest.mark.req` tag. You cannot commit code when a requirement has zero tests. You cannot merge a `feat:` commit without a `FR-XXX` reference. The Inquisitor audits the whole chain periodically, and findings flow back into doctrine refinements.

This is not aspirational. It is the current state of the repository, running on every commit.

---

## 2. The Requirement Structure

### Capabilities and Requirements in ARCHITECTURE.md

ARCHITECTURE.md is the single source of truth for what YAMLGraph can do. It organizes functionality into **capabilities** (CAP-XX), each containing numbered **requirements** (REQ-YG-XXX).

The pattern is consistent:

```markdown
### CAP-01: Configuration Loading & Validation

Load YAML graph configs, validate schemas, build state models,
and ensure graph integrity through linting.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-001 | Load graph configurations from YAML files | `graph_loader.load_graph_config`, `cli/helpers`, `data_loader` |
| REQ-YG-002 | Validate graph configuration schemas and structures | `models/graph_schema`, `utils/validators` |
| REQ-YG-003 | Perform linting and pattern validation | `linter/graph_linter`, `linter/checks`, `linter/patterns/*` |
| REQ-YG-004 | Handle errors during configuration loading | `cli/helpers.GraphLoadError`, `data_loader.DataFileError` |
```

Each capability section includes:
- A prose description of the capability's purpose
- A table mapping requirements to descriptions and implementing modules
- Stable numbering — retired capabilities (e.g., CAP-27, CAP-29) are removed rather than renumbered to preserve cross-references

### The REQ-YG Numbering Scheme

Requirements use the format `REQ-YG-XXX` where XXX is a zero-padded three-digit number:

- **REQ-YG-001 through REQ-YG-077**: Core framework requirements (CAP-01 through CAP-26)
- **REQ-YG-083**: Graph-level thinking budget (CAP-28)
- **REQ-YG-087, REQ-YG-089**: Copilot node (CAP-30) — REQ-YG-088 was dropped as overengineering
- **REQ-YG-090**: Chaplain diary append (CAP-31)
- **REQ-YG-091, REQ-YG-092**: eBook authoring pipeline (CAP-32)

Gaps in the sequence are intentional. Some requirements were relocated to project-scoped tracking (REQ-YG-078–082 became OC-XXX for the Outcaller project; REQ-YG-084–086 became IC-XXX for Incaller). Others were dropped during planning. The numbering is append-only — no renumbering, no backfilling.

### The Capability Summary Table

ARCHITECTURE.md opens with a summary mapping all 32 capabilities to their module groups:

```markdown
| # | Capability | Primary Modules | Requirements |
|---|-----------|----------------|--------------|
| 1 | Configuration Loading & Validation | `graph_loader`, `models/graph_schema`, ... | REQ-YG-001 – 004 |
| 2 | Graph Compilation | `graph_loader`, `node_compiler` | REQ-YG-005 – 008 |
| 3 | Node Execution | `node_factory/llm_nodes`, ... | REQ-YG-009 – 011, 050 |
...
```

This table is the "map" — it tells you at a glance which requirements belong to which capability and which modules implement them. The detailed sections below it are the "territory."

---

## 3. Test Tagging with @pytest.mark.req

### The Pattern

Every test function in YAMLGraph must declare which requirement(s) it proves:

```python
@pytest.mark.req("REQ-YG-001", "REQ-YG-002", "REQ-YG-005")
def test_load_valid_yaml(self, sample_yaml_file):
    """Load a valid graph YAML file."""
    config = load_graph_config(sample_yaml_file)

    assert isinstance(config, GraphConfig)
    assert config.name == "test_graph"
    assert config.version == "1.0"
```

This creates a many-to-many relationship:
- **One test can cover multiple requirements**: The test above proves REQ-YG-001 (loading from YAML), REQ-YG-002 (schema validation), and REQ-YG-005 (compiling into StateGraph) simultaneously.
- **One requirement can have multiple tests**: REQ-YG-061 (linter contracts) has 12 tests in `test_linter_contracts.py`, each exercising a different contract scenario. REQ-YG-075 (interactive tool node) has over 30 tests across unit and integration files.

### The Enforcement Hook

The marker alone is documentation. What makes it *enforced* is the collection hook in `tests/conftest.py`:

```python
def pytest_collection_modifyitems(config, items):
    """Enforce that every test has @pytest.mark.req decorator.

    Implements ADR-001: Requirement Traceability.
    Enforces Commandment #10: Preserve and improve the doctrine.
    """
    missing = []
    for item in items:
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

This runs at *collection time* — before any test executes. A single untagged test aborts the entire suite with a clear error identifying the offending test and citing the doctrine it violates.

The enforcement itself is tested. `test_requirement_enforcement.py` verifies both sides:

```python
@pytest.mark.req("REQ-YG-063")
def test_untagged_test_is_rejected(tmp_path):
    """Verify pytest fails when a test lacks @pytest.mark.req."""
    # Creates a test file WITHOUT @pytest.mark.req, runs pytest,
    # and asserts it fails with REQUIREMENT TRACEABILITY VIOLATION

@pytest.mark.req("REQ-YG-063")
def test_tagged_test_is_accepted(tmp_path):
    """Verify pytest allows tests with proper @pytest.mark.req."""
    # Creates a test file WITH @pytest.mark.req, runs pytest,
    # and asserts it passes
```

The enforcement mechanism proving itself — tagged with the requirement it implements (REQ-YG-063, Testing & Quality). Turtles all the way down.

---

## 4. The Enforcement Script: req_coverage.py

While the conftest hook ensures every test *has* a tag, it doesn't verify that every *requirement* has tests. That's the job of `scripts/req_coverage.py`.

### How It Works

The script performs AST analysis on every test file to extract `@pytest.mark.req()` decorators, then cross-references against the known requirement set:

```python
# All known requirements (framework only)
_ALL_FRAMEWORK_REQS = (
    list(range(1, 78))  # REQ-YG-001 through REQ-YG-077
    + [83]              # REQ-YG-083 (CAP-28 Thinking Budget)
    + [87, 89]          # REQ-YG-087, REQ-YG-089 (CAP-30 Copilot Node)
    + [90]              # REQ-YG-090 (CAP-31 Chaplain Diary Append)
    + [91, 92]          # REQ-YG-091, REQ-YG-092 (CAP-32 eBook Authoring Pipeline)
)
ALL_REQS = [f"REQ-YG-{i:03d}" for i in _ALL_FRAMEWORK_REQS]
```

The capability grouping mirrors ARCHITECTURE.md exactly:

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
    # ... 28 more capabilities
}
```

### Running Modes

**Summary mode** (default):

```bash
$ python scripts/req_coverage.py

======================================================================
REQUIREMENT TRACEABILITY REPORT
======================================================================

Requirements: 82/82 covered
Tagged tests: 1247 unique, 1589 test-req pairs

CAPABILITY COVERAGE
----------------------------------------------------------------------
  ✅ CAP-01 Config Loading & Validation: 4/4 reqs, 48 tests
  ✅ CAP-02 Graph Compilation: 4/4 reqs, 34 tests
  ✅ CAP-03 Node Execution: 4/4 reqs, 41 tests
  ✅ CAP-04 Prompt Execution: 5/5 reqs, 77 tests
  ...
```

**Detail mode** (`--detail`): Shows which specific tests cover each requirement:

```bash
$ python scripts/req_coverage.py --detail

DETAILED MAPPING
----------------------------------------------------------------------

  REQ-YG-001 (18 tests):
    - test_graph_loader::TestLoadGraphConfig::test_load_valid_yaml
    - test_graph_loader::TestLoadGraphConfig::test_load_missing_file_raises
    - test_graph_loader::TestLoadGraphConfig::test_parse_nodes
    ...

  REQ-YG-002 (18 tests):
    - test_graph_loader::TestLoadGraphConfig::test_load_valid_yaml
    ...
```

**Implementation mode** (`--implementation`): Traces the full chain from requirement → source files → tests, using both coverage data and AST import analysis as fallback:

```bash
$ python scripts/req_coverage.py --implementation

IMPLEMENTATION TRACEABILITY
======================================================================

── CAP-01 Config Loading & Validation (4 reqs, 48 tests) ──────────

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

**Strict mode** (`--strict`): Exits with code 1 if any requirement lacks tests. This is the mode used by CI.

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

This creates a hard gate: if you add a requirement to ARCHITECTURE.md and update the `ALL_REQS` list in `req_coverage.py`, but forget to write a test, **the commit is rejected**. The gap is caught before it reaches the remote repository.

---

## 5. Conventional Commits Integration

Requirements don't exist in isolation — they flow through the entire development lifecycle via Conventional Commits and feature request traceability.

### The Chain: Doctrine → Requirement → Test → Code → Commit → Changelog

```
Scripture defines        "Thou shalt sanctify thy outputs with types"
    ↓
ARCHITECTURE.md adds     REQ-YG-044: Schema loading and model building
    ↓
Test tags               @pytest.mark.req("REQ-YG-044")
    ↓
Code implements         yamlgraph/schema_loader.py
    ↓
Commit references       feat(schema): FR-038 add inline schema support
    ↓
CHANGELOG records       - **Schema**: Inline YAML schema support (CAP-12)
```

### Commit Message Enforcement

Three pre-commit hooks enforce commit discipline:

**1. Conventional Commits** — Every commit must follow the `type(scope): description` format:

```yaml
- repo: https://github.com/compilerla/conventional-pre-commit
  rev: v4.3.0
  hooks:
    - id: conventional-pre-commit
      stages: [commit-msg]
      args: [feat, fix, chore, docs, refactor, test, ci, perf, style, build]
```

**2. Feature Request Reference** — Every `feat:` commit must include a `FR-XXX` tag:

```yaml
- id: feat-requires-fr
  name: feat commits require FR-XXX
  entry: "bash -c 'msg=$(cat \"$1\"); if echo \"$msg\" | grep -qE
    \"^feat(\\(.*\\))?:\" && ! echo \"$msg\" | grep -qE \"FR-[0-9]+\";
    then echo \"ERROR: feat: commits require FR-XXX reference\"; exit 1; fi' _"
  stages: [commit-msg]
```

**3. CHANGELOG Required** — Every `feat:` or `fix:` commit must stage CHANGELOG.md:

```yaml
- id: changelog-required
  name: feat/fix commits require CHANGELOG.md
  entry: "bash -c 'msg=$(cat \"$1\"); if echo \"$msg\" | grep -qE
    \"^(feat|fix)(\\(.*\\))?:\" && ! git diff --cached --name-only
    | grep -qE \"^CHANGELOG\\.md$\"; then echo \"ERROR: feat:/fix: commits
    must include CHANGELOG.md changes\"; exit 1; fi' _"
  stages: [commit-msg]
```

Together, these hooks create a traceable chain: a `feat(streaming): FR-030 add subgraphs parameter` commit can be traced to feature request FR-030, which defines which requirements it addresses, which are in turn tested and documented in ARCHITECTURE.md.

---

## 6. Pervasive Verification

The traceability system is designed for LLM agents to maintain, not just humans. The doctrine in `.github/copilot-instructions.md` specifies the exact protocol:

> *"When adding a new capability: add requirement(s) to `ARCHITECTURE.md`, extend `ALL_REQS` range and `CAPABILITIES` dict in `scripts/req_coverage.py`, tag tests with the new req ID."*

### Adding a New Capability

When an LLM agent implements a new feature, the traceability update is part of the implementation:

1. **ARCHITECTURE.md**: Add a new `### CAP-XX` section with requirement table
2. **req_coverage.py**: Extend `_ALL_FRAMEWORK_REQS` with the new range and add a `CAPABILITIES` entry
3. **Test files**: Tag every new test with `@pytest.mark.req("REQ-YG-XXX")`
4. **Pre-commit**: Both `conftest.py` and `req_coverage.py --strict` validate the chain

If any step is skipped, the commit fails. The agent cannot "forget" to update traceability because the hooks will reject the commit.

### Tracing Test Failures Back to Requirements

When a test fails, the `@pytest.mark.req` tag immediately identifies which requirement is at risk. This is invaluable during refactoring — if `test_load_valid_yaml` fails, you know REQ-YG-001, REQ-YG-002, and REQ-YG-005 are potentially violated. The Inquisitor uses this information to assess the scope of impact.

### When Doctrine Changes

If the Scripture is amended (e.g., a new Commandment is added), the question becomes: which requirements does this affect? The capability structure in ARCHITECTURE.md makes this traceable. The Inquisitor audits the chain from doctrine change → affected capabilities → affected requirements → test coverage gaps.

---

## 7. The Inquisitor's Verification Runs

The Inquisitor is the LLM agent responsible for auditing ADR-001 compliance (see Chapter 04). Its verification runs produce structured findings that demonstrate the traceability system in action.

### What a Verification Run Looks Like

From the diary entry dated 2026-02-25:

> **Context:** Audit of HEAD (`0704063`), covering 5 commits. Two `feat` commits introduce new capabilities (CAP-32, REQ-YG-091, REQ-YG-092). Audited against all 10 Commandments, ADR-001, Confessions, and the Sermon.
>
> **Findings:**
>
> - ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** REQ-YG-091 (4 tests in `test_ebook_writing.py`) and REQ-YG-092 (4 tests in `test_ebook_doctrine_validation.py`) all carry `@pytest.mark.req` tags. Both requirements documented in ARCHITECTURE.md. `req_coverage.py` updated.

This finding traces the complete chain: new requirements exist in ARCHITECTURE.md → tests are tagged with those requirements → the coverage script is updated to include them. The Inquisitor verifies all three links.

### What Drift Looks Like

From the diary entry dated 2026-02-26:

> - ✗ VIOLATION — **CHANGELOG gap (Commandment 10):** HEAD commit `76f2873` is a `feat` adding 9 per-chapter graph files, `run-chapters.sh` parallel runner, FR-104 feature request, and `test_copilot_subgraph_variables.py` (391 lines) — yet CHANGELOG 0.4.58 has no entry for these additions. The prior 4 commits are properly reflected; only the latest `feat` is missing.
>
> - ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** REQ-YG-091, REQ-YG-092 in ARCHITECTURE.md. 7 new tests across `test_copilot_subgraph_variables.py` (3) and `test_ebook_doctrine_validation.py` (4) all carry `@pytest.mark.req("REQ-YG-092")`. No orphan tests.

Note the precision: the Inquisitor counts exact tests, names exact files, and cites exact requirement IDs. This is possible *because* the traceability system provides machine-readable links between artifacts.

### The Correction Flow

When the Inquisitor finds drift, the correction flows back through the chain:

```
Inquisitor detects: CHANGELOG missing for feat commit
    ↓
Heuristic recorded in diary:
    "A feat commit that ships code without updating CHANGELOG
     is invisible to users who rely on release notes."
    ↓
Seed planted:
    "Could a pre-commit hook parse the commit message type
     and reject commits that don't include staged changes
     to CHANGELOG.md?"
    ↓
Solution implemented as pre-commit hook:
    changelog-required hook in .pre-commit-config.yaml
    ↓
Future drift mechanically prevented
```

This is the doctrine improving itself — Commandment 10 in action: *"Every failure shalt refine the law. After correction, amend tests and linters to guard against recurrence."*

---

## 8. Why This Matters

The closed traceability loop prevents four categories of defects that plague most software projects:

### Untested Features (Requirements Without Tests)

`req_coverage.py --strict` makes this impossible. Every requirement in `ALL_REQS` must have at least one test tagged with its ID, or the pre-commit hook rejects the commit.

```
❌ REQ-YG-083    ← req_coverage.py --strict exits with code 1
```

### Orphan Tests (Tests Proving Nothing)

The `conftest.py` collection hook makes this impossible. Every test function must have a `@pytest.mark.req` decorator, or pytest aborts at collection time:

```
REQUIREMENT TRACEABILITY VIOLATION (ADR-001)
======================================================================
1 test(s) missing @pytest.mark.req('REQ-YG-XXX'):

  - tests/unit/test_example.py::test_orphan_function
```

### Doctrine Drift (Scripture Disconnected from Code)

The Inquisitor audits the chain from Scripture through ARCHITECTURE.md through tests. When doctrine changes but requirements don't follow, or when requirements exist but tests don't prove them, the audit exposes the gap with specific citations.

### Commit Chaos (Features Without Traceability)

The three commit-message hooks enforce the chain from implementation back to planning:
- `conventional-pre-commit`: Enforces structured commit types
- `feat-requires-fr`: Links features to feature requests
- `changelog-required`: Links features and fixes to release documentation

### The Broader Principle

Traditional traceability matrices are spreadsheets maintained by project managers who have never read the code. They are stale on arrival. YAMLGraph's traceability lives in the same repository as the code, enforced by the same CI pipeline, and verified by the same LLM agents that write the code. It is not a parallel artifact — it is *part of the code*.

The result: at any point, you can answer these questions mechanically:
- **"Is this requirement tested?"** → `python scripts/req_coverage.py --detail`
- **"What does this test prove?"** → Read the `@pytest.mark.req` decorator
- **"Which code implements this requirement?"** → `python scripts/req_coverage.py --implementation`
- **"Is the chain intact?"** → The Inquisitor's latest diary entry tells you

When requirements, tests, and code share a single source of truth, traceability is not overhead. It is a feature.

---
