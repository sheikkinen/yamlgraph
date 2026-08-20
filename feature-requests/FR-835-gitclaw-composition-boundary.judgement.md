# Judgement: FR-835 GitClaw Composition Boundary

**Verdict:** ENFORCED - APPROVED WITH REVISIONS. R-1 through R-3 and the
resource/lifecycle enforcement corrections were folded. Human review approved
the canonical diff and the exact consumer parity diff separately on 2026-08-20.

**Prior art:** FR-831 is the direct staged-source parent and makes a separate
platform FR mandatory when cross-feature reuse is forbidden. FR-829 preserves
the same-directory and bounded public-read policy; FR-830 preserves ledger
identity. FR-832 through FR-834 are independently governed source witnesses,
not importable libraries. Canonical GitClaw `tools/cron_run.py`,
`tools/contain.py`, and `policy/generated-features.md` establish the current
independent-execution and containment boundaries. FR-835 extends orchestration
without weakening them.

**Reviewed against:** `feature-requests/FR-835-gitclaw-composition-boundary.md`;
FR-829 through FR-834; canonical `sheikkinen/gitclaw` commit
`415cd55f4d9aeb16f73403deb4cd56639e257bf1` versions of
`tools/cron_run.py`, `tools/contain.py`, and
`policy/generated-features.md`; repository judge doctrine; and repository
Copilot instructions.

## What is sound

FR-835 identifies the actual Task 5 gap: generated features are independently
contained and cron-compatible, but sibling feature directories are not a
reusable library. The proposed platform primitive keeps source ownership intact:
a contained strict manifest names dependencies, cron schedules them, and the
consumer receives only a bounded same-run envelope through a fixed graph
variable.

The platform remains semantically neutral. It preserves candidate text as an
opaque string and supplies only runner success/failure metadata. A later
separately judged composer owns deterministic source-health interpretation.
Cross-directory imports, adapter copying, source re-fetching, stale outputs,
broader containment, and platform parsing of source Markdown remain forbidden.

The strategic classification is **framework primitive for GitClaw**. Three
independently governed source features need same-run reuse, while no current
abstraction permits it safely.

## Required revisions

### R-1: Define validation-failure semantics

**Folded.** The FR now requires pre-execution manifest/graph validation,
bounded failed artifacts for invalid and dependent features, deterministic
cycle diagnostics and stderr order, continued execution of unrelated valid
features, no stale reads, and exit status `1` whenever any feature is invalid,
blocked, or fails. Tests must assert exact files, stderr, execution set, and
exit code.

### R-2: Require adversarial human review of infrastructure diffs

**Folded.** Human review is required for the complete canonical runtime, policy,
prompt, test, and README diff before canonical completion or push. A second
human review is required for the consumer parity diff before rollout
completion.

### R-3: Use preservation wording

**Folded.** The FR requires legacy behavior, ordering, outputs, exit status, and
failure recording to remain unchanged; it does not use compatibility framing.

### Enforcement correction: feasible transport and bounded local input

Independent canonical-diff review found that the original 768 KiB envelope
could not be passed as one Linux command argument and that post-process file
measurement did not bound output while the child ran. The folded FR now caps
candidates at 32 KiB and envelopes at 96 KiB, requires a non-symlink regular
manifest capped at 16 KiB, bounds process output in flight, and records spawn
errors per feature. These corrections tighten the approved boundary and must be
included in the canonical human diff review before push.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Canonical strict `composition.json` parser and graph validation in `tools/cron_run.py` |
| D-2 | Deterministic dependency scheduling, execute-once result cache, envelope bounds, and `source_snapshots` injection |
| D-3 | Focused `tests/test_cron_run.py`, written red-first for validation failures |
| D-4 | Generated-feature policy and plan/judge/enforce/review prompt alignment |
| D-5 | README composition and failure documentation |
| D-6 | Human-reviewed canonical diff and validation evidence |
| D-7 | Exact content-hash-verified rollout plus human-reviewed parity diff in the Oulu consumer |
| D-8 | Synthetic consumer witness using three synthetic sources and one composer |
| D-9 | FR-835 closure evidence before Task 6 |

Not authorized: Oulu composer implementation; source-adapter edits; adapter
imports or copying; source re-fetching; stale output reads; platform parsing or
repair of source facts; workflow, dependency, ledger, containment allowlist,
timeout, secret, public-retrieval-policy, issue #1, live-output, notification,
or publication changes; YAMLGraph core changes; or broader runtime redesign.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Human review approves this judgement and folded FR before implementation starts. | GATE |
| C-2 | Failing validation-semantics tests are written before `tools/cron_run.py` changes. | GATE |
| C-3 | `tools/contain.py` remains unchanged absent a new judged FR. | GATE |
| C-4 | Generated features receive composition input only through the bounded same-run envelope. | GATE |
| C-5 | Human review approves the complete canonical infrastructure diff before canonical completion or push. | GATE |
| C-6 | Human review approves the exact consumer parity diff before rollout completion. | GATE |
| C-7 | Every rolled-out platform file matches canonical content by hash. | GATE |
| C-8 | Task 6 remains blocked until all FR-835 acceptance criteria and closure evidence are complete. | GATE |

Authority granted: only after C-1, implement the frozen canonical GitClaw
composition boundary. Consumer rollout and Task 6 remain separately gated by
C-5 through C-8.

## Enforcement Outcome (2026-08-20)

Conditions C-1 through C-8 are satisfied. Canonical GitClaw published
`a99f7b90f0be547beb1115dabf7731a40aae45d6`; the exact eleven-file consumer
rollout published `eb640cc1f496f9c7b599301560ff4f3f440c4351`. Both full suites
passed 92 tests. Content hashes matched for every rolled-out file, both human
review gates approved their exact diffs, and the bounded synthetic consumer
witness proved ordering, execute-once caching, deterministic envelopes,
partial/all-source failure, and output recording without network or LLM use.
No forbidden surface changed. FR-831 Task 6 may proceed only under its own
separate governed task.
