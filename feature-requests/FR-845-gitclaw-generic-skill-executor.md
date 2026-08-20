# Feature Request: FR-845 GitClaw Generic Skill Executor

**Priority:** CRITICAL
**Type:** Platform simplification
**Status:** Judged — APPROVED WITH REVISIONS folded; FR-846 prerequisite
satisfied; ready for separate enforcement approval
**Effort:** 1 day
**Requested:** 2026-08-20
**Depends on:** FR-846 ENFORCED, not merely judged
**First consumer / first event:** A trusted owner files
`Plan a daily Oulu civic brief as a Feature Request`; one generic Copilot node
reads the verified request and mirrored skills, creates an FR, invokes the
independent judge adapter, and leaves artifacts for deterministic Git/issue
scripts to commit and report.

**Prior art:** FR-827 created the broken custom four-stage harness. FR-829,
FR-840, FR-841, FR-843, and FR-844 supplied useful boundary controls but also
demonstrated doctrine duplication. FR-835/836 govern cron composition/output
and are explicitly unchanged. FR-839 is rejected evidence replaced by FR-840.
FR-305 is historical single-node precedent only. FR-846 supplies the executable
control bundle this FR consumes. No committed prior combined FR-845 judgement
exists or carries authority; the split is justified by this FR and FR-846.

## Summary

Delete GitClaw's custom semantic plan/judge/enforce/review process and replace
it with one generic Copilot node. The node processes an immutable trusted issue
request by following mirrored repository instructions, skills, hooks, and
canonical adapters. It leaves artifacts in the working tree and has no GitHub
write credentials.

Retain deterministic issue intake and Git/GitHub operations. Post-agent scripts
verify artifacts and containment, then commit, push, open/update a PR, comment,
or close according to the requested operation. Cron is retained unchanged by
this FR.

## Value Statement

GitClaw becomes a remote issue-to-Copilot executor rather than a second process
engine duplicating YAMLGraph's skills.

## Problem

Current GitClaw encodes semantic process in four prompts, a generated-feature
policy, a 443-line graph, ledger transitions, remediation edges, and marker
tests. It still runs all roles in one `yamlgraph graph run` and resumes the
planner session during enforcement. The harness has timed out, contradicted its
own tool policy, and accumulated more control code around responsibilities the
skills already own.

The useful GitClaw-specific logic is narrower:

- trusted GitHub issue intake;
- immutable request/reference snapshots;
- artifact and diff verification;
- Git branch/commit/push/PR mechanics;
- factual issue comments and closure; and
- cron execution, which this FR does not change.

## Ideal Result

An owner issue acts as a command. One generic Copilot node loads the same agent
controls as YAMLGraph, chooses the applicable skill, invokes canonical adapters
when required, validates, and stops. Copilot cannot commit or mutate GitHub.
Deterministic code publishes the resulting artifacts. Git commits, issue
versions, PR heads, and review reports are the process record.

## Proposed Solution

### Activation prerequisite

No FR-845 implementation begins until FR-846 is human-reviewed and ENFORCED in
canonical GitClaw. The target repository must contain the pinned bundle,
manifest/verifier, recorded YAMLGraph source SHA, passing clean-clone
judge/author/review/hook witnesses, and FR-846 human-review record. The executor
must verify that bundle before any old harness deletion or generic-node change.

### 1. Exact command surface

The first release accepts four exact command forms:

| Command | Inputs | Required output/gate | Allowed deterministic side effect |
|---|---|---|---|
| `Plan <text> as a Feature Request` | request path/hash, repository/issue/HEAD | exactly one new `feature-requests/FR-*.md` with required headings and immutable request link/hash; `scripts/judge.sh` draft promoted to durable sibling `.judgement.md`; no implementation paths changed | commit spec artifacts, push spec branch, factual issue comment; close only on explicit rejected terminal policy |
| `Enforce <FR-path>` | committed FR + sibling judgement paths/hashes, request hash, HEAD | authority files unchanged except explicitly allowed status fields; RED/GREEN evidence; changed paths within judgement; graph/prompt scope has valid author report, lint and smoke/blocked-smoke; tests and containment pass | commit implementation on branch, push, create/update PR, factual issue comment; never merge |
| `Review <PR> against <FR-path>` | actual PR number/head, committed FR/judgement paths/hashes | `scripts/review.sh` draft promoted to durable review artifact recording consumed PR head; no implementation/authority changes | commit/report review artifact or post factual review link/comment; no approval/merge by adapter |
| `Revise <FR-path or PR>: <feedback>` | committed target, feedback in immutable request, current PR/head when relevant | exactly one deterministic revision contract below; mixed or empty output fails | replan artifacts or implementation commit/PR update only after selected gate passes |

There is no feature-request adapter today. Planning is direct skill-guided work
inside the generic node. Before judge invocation, deterministic validation
requires: one new FR path under `feature-requests/`, required template headings,
verbatim link/hash to immutable owner request, no implementation files, and no
modification outside planning-owned paths. Failure stops before judgement.

Unknown, malformed, or ambiguous command forms fail before Copilot execution.
Parsing selects an operation and referenced artifact only; product semantics
remain issue data for the skill.

### 2. One generic node

Replace the semantic content of `gitclaw.yaml` with one Copilot node using one
thin prompt:

> Process the verified owner request artifact. Follow repository instructions.
> Use the applicable skills and canonical executable adapters. Complete only
> the requested operation, validate it, and leave artifacts in the working
> tree. Do not commit, push, use GitHub APIs, merge, or expose credentials.

Inputs are immutable request/reference paths and hashes, operation, repository,
issue, current HEAD, and referenced FR/PR identifiers. Raw issue prose is not
interpolated into shell or graph state.

The node has no `GH_TOKEN`, push credential, or persisted checkout credential.
Required provider credentials remain narrowly scoped. Adapter re-entry guards
remain binding: the generic node requests adapter execution; the adapter's
Copilot execution does the independent judge/author/review work.

### 3. Deterministic outer shell

Keep and simplify issue/Git mechanics:

1. enforce existing owner/trust gate;
2. snapshot/hash request and optional references;
3. parse exact operation;
4. run generic node without GitHub write credentials;
5. reverify immutable inputs;
6. verify operation-specific artifacts, adapter reports, tests, and containment;
7. stage explicit paths, commit, pull/rebase, push branch;
8. create/update PR where appropriate;
9. post factual issue comment with operation, SHA, artifact/PR links,
   validations, and failures; and
10. close only when command semantics are terminal.

Use a minimal event-dedup record only if duplicate GitHub deliveries require
it. Delete semantic ledger states that mirror FR/commit/PR status.

### 4. Revision semantics

The agent may recommend a route, but deterministic diff validation accepts
exactly one:

1. **Replan:** one new versioned FR and sibling judgement are produced; prior
   FR, judgement, implementation branch/PR, and implementation files are not
   edited. The factual issue/PR update says `replan-required` and links the new
   authority artifacts.
2. **Implementation revision:** current implementation/test/documentation paths
   change within existing judged scope on the same branch/PR; request, FR, and
   judgement remain byte-identical except explicitly permitted status fields;
   optional/required review is rerun before any terminal success update.

If both classes change, neither changes, authority and implementation are mixed,
or scope cannot be proven from judgement, validation fails before any Git or
GitHub side effect. Owner issue edits always change request hash and therefore
select replan. Review findings or owner feedback can select implementation
revision only when the changed paths remain inside frozen scope. Review remains
optional unless judgement or owner requires it; human remains merge authority.

### 5. Mandatory deletion

The replacement deletes, in the same reviewed change:

- four custom stage prompts;
- duplicated semantic `policy/generated-features.md` (a short local path/
  side-effect addendum may remain if FR-846 does not cover it);
- semantic plan/judge/enforce/review nodes and routing;
- Copilot session resume;
- review-remediation graph loop;
- semantic ledger transitions and tests;
- marker tests that pin deleted duplicated prose.

One thin generic prompt, operation/artifact contract tests, and FR-846 bundle
integrity tests replace them. The production semantic orchestration/prompt line
count must decrease. The old harness is not preserved as fallback.

### 6. Exact change surface

Authorized in `sheikkinen/gitclaw`:

- `.github/workflows/intake.yml` for generic invocation and credential split;
- `gitclaw.yaml` reduced to one generic node;
- one new generic prompt; deletion of four stage prompts;
- request/operation/artifact/Git mechanics under `tools/` or `scripts/`;
- `tools/contain.py` only as needed for operation-specific paths;
- `tools/ledger.py` reduced to event dedup if tests prove it necessary;
- README and focused tests;
- deletion/reduction of duplicated policy and prompt marker tests.

Not authorized: cron workflow or `tools/cron_run.py`; composition/candidate
contracts; existing feature migration/deletion; Oulu issue retry; YAMLGraph
core; mirrored doctrine/hook edits; automatic merge; new secrets.

## Acceptance Criteria

- [ ] AC-01: RED proves current intake runs custom four-stage graph and exposes GitHub credentials to its semantic pipeline
- [ ] AC-02: One generic node processes verified artifacts and invokes FR-846 skill/adapters without custom stage routing
- [ ] AC-03: Plan command directly uses feature-request skill, passes deterministic FR artifact gate, and invokes independent judge adapter
- [ ] AC-04: Enforce command proves RED/GREEN and graph-authoring sole route when applicable
- [ ] AC-05: Optional review consumes actual PR head through review adapter; human remains merge authority
- [ ] AC-06: Owner issue edit replans; in-scope review/user feedback revises implementation; scope change fails `replan-required`
- [ ] AC-07: Copilot process has no GitHub write/push credentials and performs no GitHub side effect
- [ ] AC-08: Post-agent scripts alone commit explicit paths and create/update PR/comments/closure after artifact validation
- [ ] AC-09: Unknown commands, immutable-input changes, missing reports, failed tests, or containment violations fail before success-shaped issue updates
- [ ] AC-10: Custom stage prompts, routing, session resume, remediation loop, semantic ledger states, and duplicate marker tests are absent
- [ ] AC-11: Production semantic prompt/orchestration surface is smaller; no fallback custom process remains
- [ ] AC-12: Cron/composition/candidate behavior and files are byte-unchanged
- [ ] AC-13: Focused/full tests and clean-template acceptance for plan, enforce, review, revise pass with run/commit/PR/artifact evidence
- [ ] AC-14: Secret scans cover history, logs, comments, artifacts, and outputs
- [ ] AC-15: Human reviews workflow, credential, generic prompt, side-effect, deletion, and containment diff before push

The revised acceptance criteria from the judgement are binding; the list above
is superseded by the exact criteria in the Judgement section below.

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-827 | Retire custom semantic harness; retain trusted issue/Git mechanics |
| FR-829 | Its policy contradiction proves duplication; mirrored doctrine replaces semantic restatement |
| FR-835/836 | Preserve unchanged; cron/runtime retirement is outside this FR |
| FR-839 | Rejected evidence only; immutable authority comes from FR-840 |
| FR-840/841 | Retain immutable request/reference boundaries |
| FR-843 | Retire graph remediation loop; revision becomes another owner command/commit |
| FR-844 | Superseded by FR-846 mirrored instructions; no second prompt doctrine |
| FR-846 | Required executable control bundle prerequisite |
| Prior combined FR-845 judgement | No committed artifact exists; it is not authority. The split is justified by FR-845 and FR-846 only. |

## Alternatives Considered

- Repair current graph: rejected; preserves the failed abstraction.
- Add durable phase/recap engine: rejected; skills communicate through artifacts.
- Let Copilot commit/use `gh`: rejected; deterministic shell owns side effects.
- Keep old harness as fallback: rejected; leaves two semantic process engines.
- Change cron now: rejected; it is useful scripted runtime logic and orthogonal.

## Judgement (2026-08-20)

**Verdict:** APPROVED WITH REVISIONS — R-1 through R-4 folded above; authority
remains blocked until FR-846 is human-reviewed and enforced.

| # | Finding | Resolution (binding) |
|---|---|---|
| R-1 | FR-846 was only judged | Added hard activation gate requiring enforced bundle, verifier, witnesses, source SHA, and human review |
| R-2 | Missing prior combined judgement cited | Removed it as authority and recorded its absence |
| R-3 | Command gates too high-level | Added exact inputs, outputs, forbidden mutations, and allowed side effects per command |
| R-4 | Revise route trusted model prose | Added mutually exclusive deterministic replan/implementation diff gates |

**Purge list:** Old harness fallback; Copilot GitHub credentials/side effects;
mixed authority+implementation revision; cron/composition changes; invented
feature-request adapter; absent chat/uncommitted judgement authority.

**Scope frozen:** Yes, after FR-846 enforcement and human review.

### Questions for the human

Human reviews FR-846 first, then separately reviews the FR-845 replacement and
deletion diff before push.
