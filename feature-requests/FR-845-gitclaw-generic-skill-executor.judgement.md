# Judgement: FR-845 GitClaw Generic Skill Executor

**Verdict:** APPROVED WITH REVISIONS — the generic executor and subtraction are
sound, but authority activates only after R-1 through R-4 are folded and FR-846
is human-reviewed and enforced.

**Route:** Canonical YAMLGraph judge adapter, `scripts/judge.sh`, model
`gpt-5.5`, run `01a01fcd-5a73-7ca2-b5df-97a0748b7d68`, 2026-08-20.

**Prior art:** FR-827 owns the harness being retired; FR-829/840/841/843/844
provide boundary lessons; FR-835/836 cron contracts remain unchanged; FR-839
is rejected evidence; FR-846 is the mandatory bundle prerequisite. No committed
prior combined FR-845 judgement exists.

## What Is Sound

- The current semantic harness duplicates YAMLGraph's maintained skills.
- The split from bundle mirroring is correct.
- A credential-isolated generic node plus deterministic side effects strengthens
  the trust boundary.
- Mandatory deletion prevents two semantic process engines from coexisting.
- Cron and composition are correctly excluded as orthogonal useful logic.

## Required Revisions

1. **R-1:** Make human-reviewed/enforced FR-846 a hard prerequisite before any
   old-harness deletion or generic executor change.
2. **R-2:** Remove reliance on a missing prior combined FR-845 judgement.
3. **R-3:** Freeze exact per-command input, artifact, forbidden-mutation, staging,
   and GitHub-side-effect gates.
4. **R-4:** Make revision output deterministically exclusive: either new
   FR+judgement without implementation edits, or implementation repair under
   byte-stable authority; mixed/empty outputs fail.

All four are folded into FR-845.

## Scope Frozen

Authorized after FR-846 enforcement: one generic Copilot graph/prompt,
credential split in intake, exact command parser, operation/artifact validators,
explicit-path Git/PR/issue mechanics, containment updates, event-dedup-only
ledger if proven necessary, README/tests, and deletion of custom prompts,
semantic routing/resume/remediation, semantic ledger states, duplicate policy,
and marker tests.

Not authorized: cron or `tools/cron_run.py`; composition/candidate contracts;
feature migration; Oulu retry; YAMLGraph core or mirrored bundle edits;
automatic merge; new secrets; custom fallback process; Git/GitHub side effects
or write credentials inside Copilot/adapters.

## Revised Acceptance Criteria

- [ ] AC-01: FR-846 is human-reviewed and enforced in canonical GitClaw before FR-845 starts; its manifest, verifier, source SHA, witnesses, and review are recorded.
- [ ] AC-02: RED proves current intake runs the four-stage graph and exposes GitHub write/push capability to the semantic pipeline.
- [ ] AC-03: Parser accepts only the four exact commands and rejects malformed, ambiguous, traversal, multi-command, uncommitted-reference, and unsupported forms before Copilot.
- [ ] AC-04: `gitclaw.yaml` has one generic Copilot execution node and no semantic stage nodes/routing, resume, remediation loop, or fallback.
- [ ] AC-05: Thin prompt passes verified paths/hashes/metadata only and never interpolates raw issue prose into shell or graph state.
- [ ] AC-06: Plan gate proves exactly one new FR, required headings/Ideal Result, immutable request link/hash, no implementation changes, and durable judgement through `scripts/judge.sh`.
- [ ] AC-07: Enforce gate proves committed immutable authority, RED/GREEN, scoped diff, tests, and `scripts/author.sh` report/lint/smoke for graph/prompt work.
- [ ] AC-08: Review gate proves `scripts/review.sh` consumed actual PR head and produced a durable head-linked review artifact without side effects.
- [ ] AC-09: Revise gate accepts exactly replan or implementation revision, never both; scope change reports `replan-required`, implementation repair reruns review before terminal success.
- [ ] AC-10: Copilot has no `GH_TOKEN`, push credential, persisted checkout credential, or GitHub-write ambient auth.
- [ ] AC-11: Deterministic scripts reverify inputs, reports, artifacts, tests, scans, and containment before explicit-path Git/GitHub publication.
- [ ] AC-12: Failure of command, input, report, tests, containment, scan, or side-effect boundary cannot produce success-shaped updates.
- [ ] AC-13: Custom prompts, duplicated semantic policy, stage routing, resume, remediation loop, semantic ledger, and duplicate marker tests are absent.
- [ ] AC-14: Production semantic prompt/orchestration surface decreases and no fallback remains.
- [ ] AC-15: Cron/composition/candidate/source adapters/features/Oulu flow/bundle/dependencies/secrets/YAMLGraph core remain byte-unchanged.
- [ ] AC-16: Focused command/credential/containment/deletion tests, generic graph lint/compile, and full suite pass with evidence recorded.
- [ ] AC-17: Human reviews workflow, credential, prompt, side-effect, deletion, containment, and bundle-consumption diff before push.

## Conditions

1. FR-846 must be complete and verified in target GitClaw before deletion.
2. Command classification happens deterministically before Copilot execution.
3. Copilot creates working-tree artifacts only; scripts own side effects.
4. Graph/prompt changes use FR-846 authoring route and artifact verification.
5. Mixed authority and implementation revision fails closed.
6. Enforcement-infrastructure diff requires human review.

FR-846 was human-reviewed and enforced at GitClaw `8bb8763`; implementation
authority is active. The final FR-845 enforcement-infrastructure diff still
requires human review before push.
