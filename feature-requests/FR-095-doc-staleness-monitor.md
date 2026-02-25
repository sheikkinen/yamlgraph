# Feature Request: Documentation Staleness Monitor

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-02-25

## Summary

Automated script that detects documentation drift — missing node types, orphan docs, and stale requirement references — and reports findings to `.chaplain/inbox/` for triage.

## Value Statement

Maintainers catch documentation staleness at commit time instead of during painful manual audits, preventing the 7+ class of drift issues found on 2025-02-24.

## Problem

Architecture, README, and reference docs drift from code reality. A manual audit on 2025-02-24 revealed:

- Stale requirement ranges (REQ-YG-088 deleted but still referenced) → FR-087
- Missing node types from reference tables (`copilot`, `interactive_tool`) → FR-091
- Orphan docs not linked in reference index → FR-092
- Capability numbering gaps from strikethrough → FR-089

Each was fixed individually (FR-087 through FR-092). Without automation, the same classes of drift will recur with every new node type, requirement, or reference doc.

`scripts/req_coverage.py --strict` already catches requirement gaps in pre-commit, but the other three checks have no automated equivalent.

## Proposed Solution

A single Python script `scripts/doc_staleness.py` with three checks, runnable standalone or as a pre-commit hook.

### Checks

**1. Node type table completeness** — compare `yamlgraph/node_factory/` exports against `reference/README.md` Node Types table.

```python
# Pseudocode
registered = get_node_types_from_factory()  # e.g. from NODE_TYPE_MAP keys
documented = parse_node_types_table("reference/README.md")
missing = registered - documented
```

**2. Orphan reference docs** — compare `reference/*.md` files against links in `reference/README.md`.

```python
reference_files = glob("reference/*.md") - {"reference/README.md"}
linked_files = extract_markdown_links("reference/README.md")
orphans = reference_files - linked_files
```

**3. Stale requirement ranges** — scan `ARCHITECTURE.md` for range notations (e.g. `REQ-YG-087–089`) and flag any that span a dropped requirement.

```python
ranges = find_req_ranges("ARCHITECTURE.md")
dropped = get_dropped_reqs()  # from req_coverage.py's ALL_REQS gaps
for r in ranges:
    if r.spans_any(dropped):
        report(f"Range {r} spans dropped {dropped}")
```

### Output

- **Pre-commit mode** (`--strict`): exits non-zero on findings, prints summary to stderr. Suitable for `.pre-commit-config.yaml`.
- **Report mode** (`--report`): writes `.chaplain/inbox/doc-audit-YYYY-MM-DD.md` with structured findings for watcher triage.
- **Default**: prints findings to stdout.

### Integration

```yaml
# .pre-commit-config.yaml addition
- repo: local
  hooks:
    - id: doc-staleness
      name: doc-staleness-check
      entry: python scripts/doc_staleness.py --strict
      language: system
      pass_filenames: false
      files: ^(reference/|yamlgraph/node_factory/|ARCHITECTURE\.md)
```

### CLI

```bash
# Check and print
python scripts/doc_staleness.py

# Strict mode (pre-commit)
python scripts/doc_staleness.py --strict

# Generate inbox report
python scripts/doc_staleness.py --report
```

## Acceptance Criteria

- [ ] `scripts/doc_staleness.py` exists with `--strict` and `--report` flags
- [ ] Check 1: detects node types in factory but missing from `reference/README.md` Node Types table
- [ ] Check 2: detects `reference/*.md` files not linked in `reference/README.md`
- [ ] Check 3: detects requirement range notations spanning dropped requirements
- [ ] `--strict` exits non-zero when any check finds issues
- [ ] `--report` writes findings to `.chaplain/inbox/doc-audit-YYYY-MM-DD.md`
- [ ] Pre-commit hook added, triggered only on relevant file changes
- [ ] Tests added with `@pytest.mark.req` traceability
- [ ] Script runs in < 2 seconds (no LLM calls, pure file parsing)

## Alternatives Considered

**YAMLGraph graph orchestration** — The inbox file proposed a `graph.yaml` with LLM nodes for each check. Rejected for v1 because: (a) these checks are deterministic string comparisons, not LLM tasks; (b) a Python script is faster, testable without mocks, and has zero API cost; (c) the graph approach can be layered on later for richer audit reports that *do* need LLM reasoning (e.g. "is this doc section semantically outdated?").

**Extend `req_coverage.py`** — Would overload a focused script. The staleness checks are a distinct concern (doc completeness vs. test coverage).

**Inquisitor integration** — The existing `.chaplain/inquisitor.sh` runs post-commit LLM audits. Could add these checks there, but the inquisitor is async and LLM-based. Deterministic checks deserve fast, synchronous pre-commit feedback.

## Related

- FR-087: Stale requirement range notation (manual fix, now automatable by check 3)
- FR-089: Capability numbering gaps (adjacent concern)
- FR-091: Missing node types in reference table (manual fix, now automatable by check 1)
- FR-092: Orphan reference docs (manual fix, now automatable by check 2)
- FR-025: Linter cross-reference checks (similar philosophy, different scope)
- `scripts/req_coverage.py`: Existing requirement traceability script (pattern to follow)
- `.chaplain/inquisitor.sh`: Async post-commit audit (complementary, not replacement)

## Implementation Notes

- Follow `scripts/req_coverage.py` structure: `sys.argv` flags, `--strict`/`--report` modes, clear exit codes.
- Parse `reference/README.md` node types table with regex (markdown table rows).
- Get registered node types from `yamlgraph/constants.py` `NodeType(StrEnum)` — parse the source file with regex to avoid import dependency.
- For orphan detection, extract `[text](file.md)` links from README.
- Keep script dependency-free (stdlib only, no yamlgraph imports needed).

## Judgement Notes (2026-02-25)

**Verdict: APPROVED** — Scope frozen. Authority granted.

**Corrections applied during review:**
1. `NODE_TYPE_MAP` does not exist in `node_factory/__init__.py`. The canonical node type registry is `NodeType(StrEnum)` in `yamlgraph/constants.py` (12 members: llm, router, tool, agent, python, map, tool_call, interrupt, subgraph, passthrough, interactive_tool, copilot).
2. `scripts/req_coverage.py` uses `sys.argv` checking, not `argparse`. FR implementation notes updated accordingly.

**Assessment:**
- ✅ Scope: Three discrete, well-bounded checks — no scope creep risk.
- ✅ Acceptance criteria: Each criterion is binary-testable.
- ✅ Feasibility: All data sources confirmed to exist and be parseable.
- ✅ Architecture alignment: Follows established `scripts/` + pre-commit pattern.
- ✅ Alternatives analysis: Sound rejection of LLM-based approach for deterministic checks.
