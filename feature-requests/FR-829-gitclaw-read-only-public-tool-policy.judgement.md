# Judgement: FR-829 gitclaw Read-Only Public Tool Policy

**Verdict:** APPROVED WITH REVISIONS — the policy repair is necessary and
correctly bounded, but authority activates only after R-1 through R-4 are
folded into the FR and human-reviewed.

**Route:** Canonical YAMLGraph judge adapter, `scripts/judge.sh`, model
`gpt-5.5`, run `01a01d44-5e95-75b5-b17d-72087ab0bf5e`, 2026-08-20.
The full generated draft was reviewed; its binding revisions are preserved
below and folded into FR-829.

**Prior art:** FR-827 governs gitclaw's platform and threat model; FR-828 is the
first blocked consumer; FR-824 supplies bounded public-source precedent. FR-425
is a false noun match. FR-829 itself is the proposal under judgement.

## What Is Sound

- The contradiction is proven in current README, authoring doctrine, judge,
  and enforce contracts.
- One gitclaw-local policy referenced by all four stages is the smallest repair
  that prevents future drift.
- The proposed boundary permits only named, bounded, unauthenticated public
  observation while preserving prohibitions on secrets and external writes.
- The FR retains gitclaw's honest statement that prompt policy and containment
  are not a sandbox against a malicious model.
- FR-828 provides a concrete first consumer and post-fix preflight witness.

## Required Revisions

### R-1: Preserve pre-shipped fixture status

Scope the new policy to issue-generated features. Do not retroactively require
the pre-shipped horoscope fixture to carry issue-pipeline provenance or migrate
it under FR-829.

**Folded:** policy and AC-01 now distinguish issue-generated artifacts from
pre-shipped fixtures.

### R-2: Use gitclaw's actual test environment

PyYAML is not installed by gitclaw's test workflow. Policy tests must use
pytest plus the standard library, and banned contradictory wording must be an
exact token list rather than an untestable semantic-equivalence claim.

**Folded:** tests are standard-library-only and four exact banned strings are
named.

### R-3: Mechanize the FR-828 witness and evidence boundary

The unblock witness must be a pushed gitclaw SHA plus exact output from the
policy/containment test command. YAMLGraph evidence is limited to FR status and
implementation notes, judgement, FR-828 preflight/AC-05, FR board, and diary.

**Folded:** command and exact allowed evidence surface are named.

### R-4: Human-review enforcement policy changes

A human must review the final judgement and complete gitclaw policy/prompt diff
before FR-828 is unblocked or a public issue runs under the corrected contract.

**Folded:** explicit gate added to solution, AC-13, and FR judgement.

## Scope Frozen

Authorized after human review: `policy/generated-features.md`; the four root
stage prompts; one standard-library policy-contract test; narrow containment
test paths; README trust/limitation alignment; bounded FR/judgement/board/diary
evidence in YAMLGraph.

Not authorized: existing fixture migration; YAMLGraph package, capability,
requirement, example, graph, prompt, hook, CI, or runtime changes; gitclaw
workflow, dependency, secret, permission, ledger, cron, containment
implementation, or vendored-skill changes; arbitrary-code scanner; runtime
sandbox; FR-828 cookbook creation or execution.

## Conditions for Enforcement

1. Human-review this judgement and the final policy/prompt diff.
2. Keep tests runnable under gitclaw's existing pytest-only workflow.
3. Do not claim sandboxing or malicious-model secret protection.
4. Restrict FR-828 activity to its static preflight note and AC-05 update.
5. Stay within the frozen surfaces above.

Authority remains advisory pending human review.
