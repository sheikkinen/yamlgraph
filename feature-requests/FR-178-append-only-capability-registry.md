# FR-178: Append-Only Capability Registry

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 3 days
**Requested:** 2026-03-09

## Summary

Replace the monolithic capability table in ARCHITECTURE.md and the hardcoded `CAPABILITIES` dict in `scripts/req_coverage.py` with an append-only directory of individual YAML files under `capabilities/`. Each capability is one file; new FRs add files rather than editing shared artifacts. ARCHITECTURE.md capability sections become generated output.

## Value Statement

All contributors benefit from merge-conflict-free capability registration, since adding a capability becomes creating a new file instead of editing two shared hotspot files (ARCHITECTURE.md and req_coverage.py).

## Prerequisites

- **FR-177** (Remove Capability Counts) must be implemented first. FR-177 removes CAP-52, REQ-YG-150, and the hardcoded count sentence in ARCHITECTURE.md. The migration script in FR-178 must run against the post-FR-177 baseline to avoid generating a `CAP-52` file that would immediately need deletion.

## Problem

ARCHITECTURE.md and `scripts/req_coverage.py` are merge conflict hotspots. Every `feat` PR that introduces a new capability must:

1. **Add a row** to the capability summary table in ARCHITECTURE.md (~line 275).
2. **Add a detailed section** with requirement descriptions further down in ARCHITECTURE.md.
3. **Add an entry** to the `CAPABILITIES` dict in `scripts/req_coverage.py` (~line 67).
4. **Extend** `_ALL_FRAMEWORK_REQS` in `req_coverage.py` (~line 64).

When multiple feat PRs are in flight, all four edits conflict on the same lines. Git history shows ARCHITECTURE.md is modified by nearly every feat commit (10 of the last 10). The `CAPABILITIES` dict in req_coverage.py (190 lines) suffers the same serial-rebase pressure.

This is a **dual source of truth** problem: capability metadata lives in both a prose document and a Python dict, with no machine-enforced consistency between them.

**Known data integrity gap:** ARCHITECTURE.md line 273 claims "125 requirements" but `req_coverage.py` defines only 117. FR-177 removes the count line, but the migration script must use `req_coverage.py` as the authoritative source for requirement IDs and flag any requirements found in ARCHITECTURE.md prose but absent from the dict (see Migration section).

## Proposed Solution

### 1. Registry directory

```
capabilities/
  CAP-01-config-loading-validation.yaml
  CAP-02-graph-compilation.yaml
  ...
  CAP-64-concurrency-safety-map.yaml
```

**Filename convention:** `CAP-{XX}-{kebab-case-name}.yaml`

**Retired capabilities:** IDs are stable and never renumbered. Retired capabilities (CAP-27, CAP-29, CAP-58) have **no YAML file** — they are gaps in the numbering sequence. The validation script enforces that no new file reuses a retired ID. A comment block in `scripts/validate_capabilities.py` lists retired IDs with the reason for retirement:

```python
RETIRED_CAPS = {
    "CAP-27": "Telco Voice Call Demo — relocated to projects/outcaller/",
    "CAP-29": "Incaller Voice Demo — relocated to projects/incaller/",
    "CAP-58": "Removed (see git history for details)",
}
```

### 2. Capability schema

Each file follows a strict schema:

```yaml
id: CAP-64
name: Concurrency Safety Map
description: >
  Document concurrency invariants for shared resources
  (checkpointer, state, tools) across parallel graph execution.
modules:
  - docs/concurrency-safety.md
requirements:
  - id: REQ-YG-160
    description: Document thread-safety guarantees for checkpointer, state, and tool access
    modules:
      - docs/concurrency-safety.md
fr: FR-176
```

**Schema rules:**
- `id`: `CAP-{N}` where N is a stable integer (never renumbered). Must match filename.
- `name`: Human-readable capability name.
- `description`: One-paragraph description of the capability.
- `modules`: List of primary module paths (relative to repo root).
- `requirements`: List of requirement objects, each with `id`, `description`, and `modules`.
- `fr`: Feature request that introduced or last modified this capability.

### 3. Aggregation script

```bash
python scripts/aggregate_capabilities.py
```

Reads all `capabilities/CAP-*.yaml` files, validates schema, and generates the capability sections of ARCHITECTURE.md:
- Summary table (capability rows with `#`, name, modules, requirements).
- Detailed per-capability sections with requirement tables.

Output is written to a delimited section of ARCHITECTURE.md between markers:

```markdown
<!-- BEGIN GENERATED CAPABILITIES -->
...
<!-- END GENERATED CAPABILITIES -->
```

Everything outside the markers remains hand-authored (design philosophy, patterns, etc.).

### 4. req_coverage.py reads from registry

Replace the hardcoded `CAPABILITIES` dict and `_ALL_FRAMEWORK_REQS` list with a loader:

```python
def load_capabilities(registry_dir: Path = REPO_ROOT / "capabilities") -> dict:
    """Load all capability YAML files and return CAPABILITIES dict."""
    ...
```

`ALL_REQS` is derived by collecting all `requirements[].id` values from the registry. The hardcoded data structures are deleted entirely.

### 5. Pre-commit schema validation

A pre-commit hook validates every `capabilities/CAP-*.yaml` file against the schema on commit. Uses a lightweight Python script (no new dependencies) that checks:
- Required fields present (`id`, `name`, `description`, `modules`, `requirements`, `fr`).
- `id` matches filename pattern (`CAP-01-foo.yaml` → id must be `CAP-01`).
- Requirement IDs follow `REQ-YG-{NNN}` format.
- No duplicate capability or requirement IDs across files.
- No file reuses a retired ID (CAP-27, CAP-29, CAP-58).

Hook configuration follows existing local hooks pattern:

```yaml
- id: validate-capabilities
  name: Capability registry schema validation
  entry: .venv/bin/python scripts/validate_capabilities.py
  language: system
  pass_filenames: false
  always_run: true
  stages: [pre-commit]
```

### 6. Migration script

One-time script to split existing ARCHITECTURE.md table and req_coverage.py dict into individual YAML files:

```bash
python scripts/migrate_capabilities.py
```

**Authoritative sources:**
- `scripts/req_coverage.py` is authoritative for capability ID → requirement ID mapping.
- ARCHITECTURE.md is authoritative for descriptions and module paths.

**Reconciliation:** The migration script logs warnings for any requirements found in ARCHITECTURE.md prose but absent from the `CAPABILITIES` dict in `req_coverage.py`. These are treated as documentation errors in ARCHITECTURE.md and are not migrated. The 117 requirements in `req_coverage.py` are the source of truth.

**Retired capabilities:** The migration script skips CAP-27, CAP-29, and CAP-58 (no YAML files generated for retired IDs). It emits an info-level log for each skipped ID.

The migration script is retained in `scripts/` for reference but not run in CI.

### Cascade changes

| Artifact | Action | Reason |
|----------|--------|--------|
| `capabilities/` | Create directory with 60 YAML files (61 active minus CAP-52 removed by FR-177) | Primary change |
| `scripts/aggregate_capabilities.py` | Create | Generates ARCHITECTURE.md sections |
| `scripts/migrate_capabilities.py` | Create | One-time migration from current state |
| `scripts/validate_capabilities.py` | Create | Schema validation for pre-commit |
| `scripts/req_coverage.py` | Remove `CAPABILITIES` dict and `_ALL_FRAMEWORK_REQS`; load from registry | Eliminate dual source of truth |
| `ARCHITECTURE.md` | Add generation markers; replace capability sections with generated output | Becomes partially generated |
| `.pre-commit-config.yaml` | Add `validate-capabilities` hook | Schema enforcement |
| `CLAUDE.md` | Update "Adding a new capability" instructions | Process documentation |

### ID assignment

Capability and requirement IDs are assigned during the **Plan** phase. The Planner reserves the next `CAP-XX` and `REQ-YG-XXX` by scanning existing files:

```bash
ls capabilities/CAP-*.yaml | sort -t- -k2 -n | tail -1  # Highest CAP-XX
grep -roh 'REQ-YG-[0-9]\+' capabilities/ | sort -t- -k3 -n | tail -1  # Highest REQ-YG-XXX
```

This eliminates the current pattern of editing a shared list to "register" new IDs.

## Acceptance Criteria

- [ ] `capabilities/` directory exists with one YAML file per active capability (60 files, post-FR-177 baseline)
- [ ] Retired capability IDs (CAP-27, CAP-29, CAP-58) have no YAML files; gaps in numbering are expected
- [ ] Each capability YAML file passes schema validation (required fields, ID format, no duplicates, no retired ID reuse)
- [ ] `scripts/migrate_capabilities.py` generates all 60 files from current ARCHITECTURE.md and req_coverage.py (post-FR-177)
- [ ] `scripts/aggregate_capabilities.py` regenerates ARCHITECTURE.md capability sections from registry
- [ ] Round-trip verified: migrate → aggregate produces semantically equivalent ARCHITECTURE.md content (same table rows and requirement entries; whitespace and formatting differences are permitted)
- [ ] Migration script logs warnings for any requirements in ARCHITECTURE.md prose not present in `req_coverage.py`
- [ ] `scripts/validate_capabilities.py` catches: missing fields, ID mismatches, duplicate IDs, invalid REQ format, retired ID reuse
- [ ] Pre-commit hook runs `validate_capabilities.py` on changes to `capabilities/`
- [ ] `scripts/req_coverage.py` loads capabilities from YAML registry (no hardcoded `CAPABILITIES` dict)
- [ ] `python scripts/req_coverage.py --strict` passes against the registry
- [ ] ARCHITECTURE.md uses generation markers (`<!-- BEGIN/END GENERATED CAPABILITIES -->`); hand-authored sections preserved
- [ ] Tests added with `@pytest.mark.req` tags for new requirements
- [ ] Documentation updated (CLAUDE.md process for adding capabilities)

## Alternatives Considered

1. **TOML instead of YAML** — TOML is simpler for flat key-value data but less natural for nested requirement lists. YAML is the native configuration language of the project. Rejected.

2. **Single registry YAML file instead of one-per-capability** — Reduces file count but reintroduces the merge conflict problem (all PRs edit the same file). Rejected: defeats the primary objective.

3. **JSON Schema validation** — More rigorous but adds a dependency (jsonschema) and indirection. A 50-line Python validator is sufficient for the schema complexity. Rejected for now; can upgrade later.

4. **Keep ARCHITECTURE.md as hand-authored, just fix req_coverage.py** — Solves half the problem (req_coverage.py conflicts) but leaves ARCHITECTURE.md as a hotspot. Rejected: the problem is the dual source of truth.

5. **Generate entire ARCHITECTURE.md** — Too aggressive; the design philosophy, patterns, and application layer sections are prose that benefits from hand authoring. Only the capability/requirements sections should be generated. Rejected.

6. **YAML file with `status: retired` for retired capabilities** — Adds noise: retired capabilities have no requirements, no modules, no tests. An empty file with `status: retired` carries no useful information. The validation script's `RETIRED_CAPS` dict documents the retirement reason. Rejected: gap-in-numbering is simpler and sufficient.

## Related

- `feature-requests/FR-177-remove-capability-counts.md` — **Prerequisite**. Removes CAP-52/REQ-YG-150 and the hardcoded count sentence. Must be implemented before FR-178 migration runs.
- `scripts/req_coverage.py` — Major refactor target (CAPABILITIES dict and ALL_REQS list deleted).
- `ARCHITECTURE.md` — Capability sections become generated; design sections remain hand-authored.
- `.pre-commit-config.yaml` — New validation hook.

## Judgement

**Verdict: APPROVE**
**Reviewed:** 2026-03-09

### Assessment

The FR is well-structured, addresses a real and measurable problem (9 of last 10 ARCHITECTURE.md commits are feat PRs), and proposes a solution that aligns with existing patterns (YAML-first, pre-commit hooks with `language: system`). The single responsibility is clear: eliminate the dual source of truth for capabilities. All sub-components (registry, aggregation, validation, migration, req_coverage refactor) are tightly coupled to this goal — SPLIT is not warranted.

**Claims verified against codebase:**
- ✅ ARCHITECTURE.md modified by 9/10 recent feat commits
- ✅ 61 active capabilities in CAPABILITIES dict (61 keys counted)
- ✅ CAP-27, CAP-29 retired and absent from dict
- ✅ CAP-58 vacant (stale comment at req_coverage.py:56 labels REQ-YG-155 as CAP-58, but actual dict maps it to CAP-57)
- ✅ FR-177 prerequisite exists with status Approved
- ✅ 117 requirements in `_ALL_FRAMEWORK_REQS` (not 125 as ARCHITECTURE.md claims — FR correctly identifies this discrepancy)

### Clarifications for implementer

1. **`fr` field for legacy capabilities.** The schema declares `fr` as required, but ~50 capabilities predate the FR system. The migration script must assign values. Recommendation: use `fr: legacy` as a sentinel for capabilities with no traceable FR. The validation script should accept `legacy` as a valid `fr` value.

2. **Generated output ordering.** The FR implies numeric order by CAP-ID but does not state it explicitly. Enforce: aggregation script MUST sort by numeric CAP-ID (ascending) for deterministic output.

3. **Stale comment at req_coverage.py:56.** The comment `# REQ-YG-155 (CAP-58 Verification Count Range Pydantic)` is incorrect — REQ-YG-155 maps to CAP-57 in the dict. The migration script should use dict keys as authoritative, not comments.

### Scope frozen

Authority granted to implement FR-178 against the post-FR-177 baseline. The three clarifications above are binding constraints on the implementation.
