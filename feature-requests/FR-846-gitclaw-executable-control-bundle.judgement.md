# Judgement: FR-846 GitClaw Executable Control Bundle

**Verdict:** APPROVED WITH REVISIONS — the executable mirror spike is the right
prerequisite for FR-845; authority activates after R-1 through R-6 are folded
and human-reviewed.

**Route:** Canonical YAMLGraph judge adapter, `scripts/judge.sh`, model
`gpt-5.5`, run `01a01fc5-9e05-7e68-961f-2124ac409390`, 2026-08-20.

**Prior art:** FR-827 is the prose-only GitClaw snapshot being superseded;
FR-844 proves instruction injection; FR-765/806/767 govern authoring route,
preflight, and sentinel; NC-412/413/415 govern judge/review routes. FR-839 is
rejected evidence only and is not revived.

## What Is Sound

- The bundle is correctly separated from the generic executor replacement.
- Instructions, skills, adapters, wrappers, and hooks are the actual authority
  surfaces missing from GitClaw's current snapshot.
- Source pinning, byte-identical mirrors, explicit local adaptations, and
  human review respect the instruction boundary.
- Clean-clone artifact witnesses test the known exit-zero/write-denied failure
  class rather than trusting process status.

## Required Revisions

1. **R-1:** Define bundle roots/explicit targets so unlisted-file closure is
   mechanically decidable; reject duplicate sources and targets.
2. **R-2:** Replace subjective minimality with a path-reference trace artifact
   classifying every helper as mirror, adapt-local, or not-runtime.
3. **R-3:** Freeze named GitClaw hook guarantees and rationale/tests for every
   YAMLGraph path/check adaptation.
4. **R-4:** Give every clean-clone witness a command, expected artifact path,
   and exact assertion; verify artifacts, never exit status alone.
5. **R-5:** Declare the clean-clone runtime and executable-resolution contract.
6. **R-6:** Disposition rejected FR-839 explicitly.

All six revisions are folded into FR-846.

## Scope Frozen

Authorized after human review: one pinned control manifest, traced runtime file
set, mirrored/adapted instructions/skills/adapters/wrappers/hooks, verifier,
adaptation rationales, focused tests, README setup/provenance, and disposable
clean-clone witness artifacts.

Not authorized: semantic GitClaw harness, graph/prompt/policy/workflow/ledger/
cron changes; Oulu work; feature migration; YAMLGraph source edits; new secrets;
production generic executor; or Git/GitHub side effects inside adapters.

## Conditions

1. One immutable YAMLGraph source SHA per run.
2. Mirrors remain byte-identical; local changes are explicit adaptations.
3. Verifier and hooks fail closed.
4. Sole-route, sentinel, artifact, and human-review guarantees cannot weaken.
5. Witnesses run from documented setup in a disposable clean clone.
6. Human review precedes push because controls are enforcement infrastructure.

**Human review:** APPROVED by the operator after the complete mirror/adaptation,
hook, verifier, clean-clone witness, and secret-scan evidence was presented.
Authority activated and enforcement completed at GitClaw `8bb8763`.
