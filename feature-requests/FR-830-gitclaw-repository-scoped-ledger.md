# Feature Request: FR-830 gitclaw Repository-Scoped Issue Ledger

**Priority:** CRITICAL
**Type:** Bug
**Status:** ENFORCED 2026-08-20 — 12/12 ACs satisfied; human-reviewed
**Effort:** 0.5 day
**Requested:** 2026-08-20
**Prior art:** FR-827 owns gitclaw's frozen ledger state machine and template
adoption claim; FR-828 provides the live failing template witness; FR-829 is a
separate generated-feature policy repair. FR-243/CAP-106 concern GitHub issue
inbox import, not gitclaw ledger identity. This judgement is the verdict for
FR-830, not prior art.
**First consumer / first event:** A fresh gitclaw template instance processing
its first issue, where copied source-repository ledger entries must not affect
the new repository's idempotency decision.

## Summary

Key gitclaw ledger entries by repository identity plus issue number instead of
issue number alone. Pass `${{ github.repository }}` to every intake/ledger
operation, migrate the canonical gitclaw ledger records to their source
repository identity, and add RED/GREEN tests proving copied source entries are
ignored in a template instance while canonical retries remain idempotent.

## Value Statement

Every gitclaw template instance can process issue #1 correctly without losing
the source repo's durable retry/idempotency history.

## Problem

FR-828 created a fresh public repository from the approved gitclaw template,
configured exactly two secrets, passed the Copilot spike, and filed owner issue
#1. Intake run `32331842032` skipped the feature slug and pipeline because the
copied `state/issues.jsonl` already contained canonical gitclaw issue #1 in
terminal state `judged_rejected`.

The source and template-instance ledger blobs were identical:
`13aa80ca4b35660417f5d0b44d9be8f72f123df4`. `tools/ledger.py` filters only on
`entry["issue"] == issue`; repository identity is absent. GitHub template
creation correctly copies committed files, so every template instance inherits
all source issue numbers and terminal decisions.

This violates the first consumer of FR-827/FR-828. It also produces a dangerous
false green: the Actions job succeeds while the requested issue remains open
and no pipeline runs.

Skipping to issue #4 is rejected. It would make the test pass while every new
adopter's first three issues still fail.

## Ideal Result

Ledger identity is `(repository, issue)`. Canonical gitclaw retries still see
their existing terminal/interrupted states. A template instance may contain a
copied canonical history for audit/reference, but its issue #1 is fresh because
its repository differs. Every new record carries repository identity. Missing
runtime repository identity fails closed in Actions rather than silently
falling back to cross-repository matching. Unit-level APIs remain explicit and
testable.

## Proposed Solution

### 1. Typed ledger identity at the boundary

Extend `tools/ledger.py` functions `_entries`, `current`, `record`,
`should_run`, and `gate_code` with a required `repository: str` argument.
Validate repository identity as non-empty `owner/name` text before reading or
writing. A ledger entry becomes:

```json
{"repository":"sheikkinen/gitclaw","issue":1,"state":"seen","ts":"..."}
```

Filtering requires both exact repository and issue matches. Do not infer
identity from git remotes inside domain functions.

The CLI reads `GITCLAW_REPOSITORY` and fails closed with a clear error if it is
missing or malformed. This environment variable is the external boundary; unit
tests pass repository explicitly.

### 2. Workflow identity injection

Set job-level environment in `.github/workflows/intake.yml`:

```yaml
env:
  GITCLAW_REPOSITORY: ${{ github.repository }}
```

This covers the idempotency gate and every `python -m tools.ledger record`
invoked inside the YAMLGraph pipeline. Do not change trust conditions,
permissions, triggers, concurrency, secrets, or issue-body handling.

### 3. Canonical state migration

Mechanically add `"repository":"sheikkinen/gitclaw"` to every existing line in
the canonical `state/issues.jsonl`, preserving issue, state, timestamp, order,
and all extra fields byte-for-byte in value. This is data provenance, not a
state transition. No entry may be deleted, reordered, or synthesized.

Once copied into another repository, those canonical entries remain inert
because the workflow supplies the new `${{ github.repository }}` identity.

### 4. RED/GREEN witnesses

Extend ledger tests before implementation:

1. same issue number in two repositories has independent state;
2. canonical terminal issue #1 yields gate code 78 for
   `sheikkinen/gitclaw` but 0 for
   `sheikkinen/gitclaw-oulu-civic-intelligence`;
3. record writes repository on every line;
4. malformed/empty repository is rejected;
5. CLI without `GITCLAW_REPOSITORY` fails closed;
6. all pre-existing transition/remediation/idempotency tests remain green after
   passing explicit repository identity; and
7. every migrated canonical ledger line has repository
   `sheikkinen/gitclaw`, with original state sequence unchanged.

RED and GREEN are separate commits. Full gitclaw tests and remote CI must pass.

### 5. FR-828 retry boundary

After GREEN is pushed and human-reviewed, create a **fresh replacement template
instance** from the corrected commit. Do not manually patch the failed instance
and do not create placeholder issues. The failed instance and run remain linked
as evidence; deletion/retirement is decided only after the replacement proves
the full cycle.

FR-830 itself does not retry FR-828, set secrets in a replacement, or file its
issue. It only restores the template's first-issue contract and records the
corrected template SHA in FR-828.

## Acceptance Criteria

- [x] AC-01: RED tests prove source-repo terminal issue #1 incorrectly blocks a
      different repository's issue #1 under current code
- [x] AC-02: All ledger domain functions require and validate explicit
      repository identity; identity is exact `(repository, issue)`
- [x] AC-03: CLI fails closed when `GITCLAW_REPOSITORY` is absent or malformed
- [x] AC-04: Intake workflow sets `GITCLAW_REPOSITORY` from
      `${{ github.repository }}` at job scope without changing triggers,
      permissions, concurrency, trust gates, secrets, or issue handling
- [x] AC-05: Every new ledger entry persists `repository`; reads ignore entries
      from other repositories with the same issue number
- [x] AC-06: Existing canonical ledger entries are migrated to
      `sheikkinen/gitclaw` without deletion, reordering, state/timestamp change,
      or invented transitions
- [x] AC-07: Tests prove canonical issue #1 remains terminal in canonical repo
      while issue #1 is fresh in the Oulu template repo
- [x] AC-08: Existing transition, remediation, terminal, and interrupted-state
      behavior remains unchanged within one repository
- [x] AC-09: Full gitclaw suite and remote CI pass; RED and GREEN commit SHAs
      and exact test outputs are recorded
- [x] AC-10: Human reviews the ledger/workflow/state migration diff before the
      corrected template is used for another public issue
- [x] AC-11: FR-828 records failed run `32331842032`, corrected template SHA,
      and fresh-retry requirement; no placeholder issue or manual instance
      repair is used
- [x] AC-12: No YAMLGraph core/capability/example, gitclaw prompt/policy/cron,
      secret, permission, generated feature, output, or unrelated fixture
      change

## Implementation Status (2026-08-20)

**RED:** gitclaw `e3a2242` — eight focused failures proved the ledger API had no
repository identity/validation and CLI did not fail closed. Nine existing FSM
tests remained green.

**GREEN:** gitclaw `fc5a844` — explicit `(repository, issue)` identity, job-level
`GITCLAW_REPOSITORY`, canonical state migration, and updated tests.

```text
python -m pytest tests/test_ledger.py tests/test_intake_tools.py -q
33 passed in 0.10s

python -m pytest tests/ -q
55 passed in 0.10s
```

Migration check stripped only the new `repository` key and proved all 17
ordered canonical records exactly equal the pre-migration values. Every migrated
entry has `repository: sheikkinen/gitclaw`. No scope deviation found.

Remote CI run `32332787182` passed in 14 seconds. The operator reviewed and
approved the complete ledger/workflow/state migration diff. Corrected source
template SHA is `fc5a844`; fresh replacement template initial SHA is `b7e0bcf`.
The failed instance was preserved as
`sheikkinen/gitclaw-oulu-civic-intelligence-failed-witness`; no files there were
repaired. FR-828 retry proceeds only in the fresh replacement.

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-827 ledger FSM | Preserve the frozen states/transitions, append-only history, terminal semantics, and one-remediation rule. Change only identity from issue to `(repository, issue)`. |
| FR-828 attempt 1 | Canonical live RED witness. Preserve run, issue, and copied-blob evidence; retry only from a fresh corrected template. |
| FR-829 policy fix | Unrelated prerequisite already enforced; do not alter shared generated-feature policy or prompts. |
| GitHub template behavior | Copying tracked state is expected platform behavior. Normalize identity at the ledger boundary rather than expecting GitHub to omit files. |

## Alternatives Considered

- **Create issues #2/#3/#4 until an unused number appears:** rejected as
  acceptance gaming and a broken first-user experience.
- **Clear the ledger manually after template creation:** rejected; violates the
  two-secrets-plus-issue cookbook and destroys source audit history.
- **Ship an empty ledger in canonical gitclaw:** impossible while the canonical
  repo also uses the ledger operationally; future operations would repopulate
  it and templates would regress.
- **Infer repository from `git remote`:** rejected at the domain boundary;
  brittle in tests and detached/custom remotes. GitHub already provides the
  authoritative repository identity.
- **Ignore unscoped entries only in non-template repos:** requires hard-coded
  source heuristics and risks canonical retries. Explicit migration is clearer.

## Related

- `feature-requests/FR-827-gitclaw-forkable-runner.md`
- `feature-requests/FR-828-gitclaw-oulu-civic-intelligence-cookbook.md`
- `../gitclaw/tools/ledger.py`
- `../gitclaw/tests/test_ledger.py`
- `../gitclaw/tests/test_intake_tools.py`
- `../gitclaw/.github/workflows/intake.yml`
- `../gitclaw/state/issues.jsonl`

## Judgement (2026-08-20)

**Verdict:** APPROVED — no revisions; repository-scoped identity is the smallest
safe repair and preserves FR-827's frozen state machine.

| # | Finding | Resolution (binding) |
|---|---|---|
| - | No required revisions | Enforce only the frozen ledger/workflow/migration/test/evidence surfaces |

**Purge list:** Placeholder issues; failed-instance repair; ledger clearing;
prompt/policy/cron/permission changes; YAMLGraph core changes; FR-828 retry under
FR-830.

**Scope frozen:** Yes.

### Questions for the human

Human review of the ledger/workflow/state migration diff is required after
GREEN and before a corrected template retry.
