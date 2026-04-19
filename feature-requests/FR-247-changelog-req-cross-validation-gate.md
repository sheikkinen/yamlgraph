# Feature Request: Changelog REQ Cross-Validation Gate

**Priority:** HIGH
**Type:** Feature
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-04-19

## Summary

Add a validation gate that verifies changelog `req:` front-matter values reference the correct requirement — a mechanical pre-filter for single-REQ capabilities, and an LLM classifier (Haiku) for multi-REQ capabilities where mechanical disambiguation is impossible. This is the first LLM enforcement gate in the YAMLGraph pipeline.

## Value Statement

Maintainers get immediate feedback when a changelog fragment references the wrong requirement, preventing the silent traceability drift that allowed 4 of 12 fragments to ship cross-wired for 12 consecutive audit cycles (FR-242).

## Problem

The capability → requirement → test → changelog traceability chain has four artifacts but only one validated link: test `@pytest.mark.req` → capability registry (via `req_coverage.py --strict`). The changelog → capability link is ungated.

The existing `changelog-gate` CI check and `changelog-required` pre-commit hook verify only that a fragment *exists* for feat/fix commits. They do not validate the `req:` front-matter value. A simple existence check passes for cross-wired fragments because the REQ ID exists — it's just the wrong requirement for the FR.

The `req:` field is optional per CLAUDE.md convention (5 of 20 current unreleased fragments omit it). When present, it must be validated; when absent, the gate skips the fragment.

For single-REQ capabilities (~72 of 96 CAPs), mechanical validation suffices: the claimed `req:` must equal the CAP's sole REQ. For multi-REQ capabilities (24 CAPs with 2–10 REQs each), a purely mechanical check cannot distinguish which REQ within the CAP a given changelog fragment describes without understanding the *content* of both the changelog entry and the requirement description. This is the first enforcement task where a mechanical gate is structurally insufficient and an LLM classifier is the right tool.

## Prerequisites

- **FR-242** (Fix existing changelog fragment REQ cross-wiring): **Complete** — merged via commit `5842ba8b`. All current unreleased fragments have correct `req:` values.

## Proposed Solution

### Architecture

```
pre-commit hook
  └─ scripts/check_changelog_req.py
       ├─ Phase 1: Mechanical pre-filter (fast, free)
       │   ├─ Parse changelog YAML front-matter → extract req:
       │   ├─ Skip fragments with no req: field (optional per convention)
       │   ├─ Verify req: ID exists in capabilities/CAP-*.yaml (reject phantoms)
       │   └─ If single-REQ CAP → mechanical match. Done.
       │
       └─ Phase 2: LLM semantic cross-check (Haiku, per-fragment)
            └─ yamlgraph graph run graphs/enforcement/changelog-req-check.yaml
                 ├─ Input: changelog body, claimed REQ description, all REQs in the CAP
                 ├─ Model: claude-haiku-4-5 (fast, cheap, sufficient for comparison)
                 └─ Output: {match: bool, correct_req: str, reasoning: str}
```

### Phase 1: Mechanical Pre-Filter (`scripts/check_changelog_req.py`)

A Python script that:
1. Scans `changelog/unreleased/*.md` — extracts `req:` from YAML front-matter
2. **Skips** fragments with no `req:` field (the field is optional per CLAUDE.md)
3. Looks up the claimed REQ directly: `grep "id: {req}" capabilities/CAP-*.yaml` → find the owning CAP
4. If not found → phantom REQ → **fail**
5. Loads all REQ IDs in that CAP
6. If the CAP has exactly 1 REQ → mechanical check: changelog `req:` must equal that REQ. Done.
7. If the CAP has multiple REQs → invoke Phase 2 LLM check
8. Fails on: phantom `req:` (ID not in any CAP), unparseable front-matter

Single-REQ CAPs (~72 of 96) never hit the LLM. The LLM is only invoked when mechanical disambiguation is impossible.

**Note**: The `fr:` field in CAP files is NOT used for lookup. It tracks the *last FR that touched the CAP*, making it lossy and non-invertible (FR-231 → 2 CAPs, FR-236 → 0 CAPs). The gate uses direct REQ-ID lookup instead.

### Phase 2: LLM Semantic Check (YAMLGraph graph)

**Graph**: `graphs/enforcement/changelog-req-check.yaml`

```yaml
version: "1.0"
name: changelog-req-cross-check
defaults:
  provider: anthropic
  model: claude-haiku-4-5
  temperature: 0
prompts_relative: true
prompts_dir: prompts
state:
  changelog_body: str
  claimed_req_id: str
  claimed_req_description: str
  candidate_reqs: str
  cap_id: str
nodes:
  check:
    type: llm
    prompt: cross_check
    variables:
      changelog_body: "{state.changelog_body}"
      claimed_req_id: "{state.claimed_req_id}"
      claimed_req_description: "{state.claimed_req_description}"
      candidate_reqs: "{state.candidate_reqs}"
      cap_id: "{state.cap_id}"
    state_key: verdict
edges:
  - from: START
    to: check
  - from: check
    to: END
```

**Prompt**: `graphs/enforcement/prompts/cross_check.yaml`

```yaml
system: |
  You are an enforcement gate for a software traceability system.
  You receive a changelog entry and must determine whether its claimed
  requirement ID (req:) correctly matches the change described.

  Rules:
  - A changelog entry describes ONE specific change delivered by a feature request
  - Each requirement (REQ-YG-XXX) has a description of what it covers
  - The changelog's req: must reference the requirement whose description
    matches the change described in the changelog body
  - If the claimed req: does not match, identify which candidate REQ is correct

  Be strict. Copy-paste errors are the most common failure mode.
  When in doubt, fail (match: false) — false positives are cheaper than
  false negatives in enforcement.

user: |
  ## Changelog Entry
  {changelog_body}

  ## Claimed Requirement
  {claimed_req_id}: {claimed_req_description}

  ## All Requirements in {cap_id}
  {candidate_reqs}

  Does the changelog entry describe a change that matches {claimed_req_id}?
  If not, which requirement from the candidates is the correct match?

schema:
  name: ReqCrossCheckVerdict
  fields:
    match:
      type: bool
      description: "True if claimed req: correctly matches the changelog content"
    correct_req:
      type: str
      description: "The REQ-YG-XXX that correctly matches (same as claimed if match=true)"
    reasoning:
      type: str
      description: "One-sentence explanation of why the match is correct or incorrect"
```

### Phase 3: Gate Integration

**Pre-commit hook** (`.pre-commit-config.yaml`):
```yaml
- id: changelog-req-cross-check
  name: changelog req cross-check
  entry: .venv/bin/python scripts/check_changelog_req.py --strict
  language: system
  pass_filenames: false
  always_run: true
  stages: [pre-commit]
```

**CI** (`.github/workflows/commitlint.yml`): Add `changelog-req-gate` as a required status check alongside existing `changelog-gate`. Runs the same script. Uses `--skip-llm` when `ANTHROPIC_API_KEY` is unavailable (mechanical checks only).

**Flags**:
- `--strict`: Exit non-zero on any validation failure (for CI/pre-commit)
- `--skip-llm`: Run mechanical pre-filter only, skip Phase 2 (for environments without API key)
- `--verbose`: Print reasoning for each LLM verdict

**Cost model**: Haiku at ~$0.80/M input, $4/M output. Each check processes ~500 tokens input, ~100 tokens output. Multi-REQ CAP fragments only — single-REQ CAPs skip the LLM entirely, so typical cost is $0.001–0.003 per commit.

## Acceptance Criteria

- [ ] `scripts/check_changelog_req.py` exists and passes `ruff check`
- [ ] Mechanical pre-filter catches: phantom REQs, unparseable front-matter, single-REQ CAP mismatches
- [ ] Fragments with no `req:` field are skipped without error
- [ ] REQ lookup uses direct `id:` grep in CAP files, not the lossy `fr:` reverse mapping
- [ ] LLM gate correctly classifies cross-wired fragments (tested with known-bad fixtures)
- [ ] `--skip-llm` flag runs mechanical-only checks without requiring API key
- [ ] `--strict` flag exits non-zero on any failure
- [ ] Graph at `graphs/enforcement/changelog-req-check.yaml` is runnable via `yamlgraph graph run` independently
- [ ] Prompt at `graphs/enforcement/prompts/cross_check.yaml` passes `yamlgraph graph lint`
- [ ] Pre-commit hook wired in `.pre-commit-config.yaml`
- [ ] CI job wired in `.github/workflows/commitlint.yml`
- [ ] All current `changelog/unreleased/*.md` fragments pass the gate
- [ ] `req_coverage.py --strict` continues to pass
- [ ] Cost per commit documented and validated < $0.01
- [ ] Unit tests for mechanical pre-filter with `@pytest.mark.req` markers
- [ ] Integration test for LLM gate with fixture fragments (requires API key guard)
- [ ] Tests added
- [ ] Documentation updated (CLAUDE.md pre-commit section)

## Design Decisions

### Why Haiku, Not a Larger Model
- The task is comparison (does text A match description B), not generation
- Structured output with 3 fields — well within Haiku's capability
- Temperature 0 for determinism
- ~100ms latency per check — acceptable for pre-commit
- Cost negligible ($0.003/commit typical)

### Why YAMLGraph Graph, Not Inline Python LLM Call
- Dogfooding: enforcement infrastructure uses the framework it enforces (Scripture: `automation_inherits_doctrine`)
- The graph is testable via `yamlgraph graph run` independently
- Prompt is in YAML, not hardcoded in Python (Commandment 3)
- The graph can be linted by the linter it helps enforce — recursive integrity

### Why LLM in Enforcement Is Acceptable Here
- The gate is *classificatory* (boolean with structured output), not *generative* — audit trail via `reasoning` field
- False positives (incorrectly rejecting a correct `req:`) are caught by the human who can override or use `--skip-llm`
- False negatives (passing an incorrect `req:`) are no worse than the current state (no gate at all)
- The mechanical pre-filter handles ~75% of cases without LLM; the LLM is the fallback, not the primary path

### Why Direct REQ Lookup, Not FR-Based Reverse Mapping
- The `fr:` field in CAP files tracks the *last FR that touched the CAP*, not a 1:1 FR→REQ mapping
- FR-231 maps to 2 CAPs (CAP-89, CAP-90); FR-236 maps to 0 CAPs — the field is lossy and non-invertible
- Direct `id: {req}` grep in CAP files is simpler, reliable, and eliminates the ambiguity entirely
- The FR number from the changelog filename is not needed for validation

### Why `req:` Remains Optional
- CLAUDE.md (changelog fragment format) defines `req:` as "optional requirement ID (omit if none)"
- 5 of 20 current unreleased fragments have no `req:` field (bug fixes without capability scope)
- Making `req:` mandatory is a separate concern — if desired, split into a distinct FR for the format change
- The gate validates what is present, not what is absent

### Precedent This Sets
This is the **first LLM enforcement gate** in the YAMLGraph pipeline. If it proves reliable, the pattern generalizes to:
- Inquisitor findings → automated escalation
- FR validation — does implementation match acceptance criteria?
- Diary quality check — does the reflection contain trap/heuristic/seed?

Each extension must justify why mechanical validation is insufficient.

## Alternatives Considered

### Purely Mechanical Cross-Reference (FR number → CAP `fr:` → REQ)
Rejected: The `fr:` field is lossy and non-invertible. Multi-REQ capabilities make it ambiguous — CAP-02 has 6 REQs. A mechanical check passes for any REQ in the CAP, which is exactly the failure mode that caused the cross-wiring.

### Manual Review Only
Rejected: 12 consecutive Inquisitor audit cycles flagged the cross-wiring with zero human correction. Advisory-only enforcement has proven insufficient for this class of error (Scripture: `detection_without_enforcement`).

### Full Graph with Multiple Nodes (Loader → Validator → Classifier)
Rejected: Over-engineered for a single LLM call. The one-node graph keeps the enforcement graph minimal and auditable. The mechanical pre-filter lives in Python where it belongs (data loading, YAML parsing).

### Making `req:` Mandatory
Deferred: Would require updating 5 existing fragments and changing the documented format convention. Out of scope for this FR — if desired, propose as a separate FR for the format change.

## Related

- **FR-242**: Fix existing changelog fragment REQ cross-wiring (bug fix, **complete** — `5842ba8b`)
- **FR-179**: Append-only changelog fragments (established the `changelog/unreleased/` pattern)
- **FR-150**: Branch protection and CI gates (established the enforcement gate pattern)
- `scripts/req_coverage.py`: Existing REQ → test traceability validation
- `.github/workflows/commitlint.yml`: Existing `changelog-gate` CI check
- `.pre-commit-config.yaml`: Existing `changelog-required` hook
- `capabilities/CAP-*.yaml`: Capability registry with REQ definitions (96 CAPs, 169 REQs)
- Scripture: `automation_inherits_doctrine`, `detection_without_enforcement`, `changelog_ci_gate`
