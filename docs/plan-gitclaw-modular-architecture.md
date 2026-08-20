# GitClaw Modular Architecture and Roadmap

**Date:** 2026-08-20
**Status:** Planning baseline — implementation authority remains in judged FRs
**Repositories:**

- YAMLGraph: `https://github.com/sheikkinen/yamlgraph`
- GitClaw: `https://github.com/sheikkinen/gitclaw`

## Purpose

GitClaw is the public integration demo for a set of independently useful
agentic GitHub capabilities. It is not the abstraction that owns all of those
capabilities.

The target architecture separates:

1. trusted GitHub issue intake and generic LLM execution;
2. deterministic Git, branch, PR, and issue operations;
3. scheduled YAMLGraph execution and output publication;
4. testing and CI bootstrap;
5. executable development doctrine: instructions, skills, adapters, and hooks;
   and
6. GitClaw itself as the full composed demonstration and new-project template.

Each capability must be useful without GitClaw. GitClaw proves they compose.

## Central Decision

The current custom GitClaw process graph is failed evidence, not a platform to
preserve.

The target issue path is:

```text
trusted issue
  -> immutable request artifact
  -> one generic Copilot/YAMLGraph execution
  -> repository instructions select applicable skills/adapters
  -> artifacts remain in the working tree
  -> deterministic verification
  -> deterministic Git/PR/issue operations
```

Examples of issue commands:

```text
Plan Oulu civic intelligence as a Feature Request
Enforce feature-requests/FR-XXX-oulu-civic-intelligence.md
Review PR 12 against feature-requests/FR-XXX-oulu-civic-intelligence.md
Revise PR 12: address the review's source-timeout finding
```

GitClaw must not reimplement feature planning, judgement, graph authoring, or PR
review in custom prompts and graph edges. YAMLGraph's skills and canonical
adapters already own those workflows.

## Design Principles

### Skills own intellectual process

- `feature-request` owns FR planning.
- `judge-fr` owns independent judgement and frozen authority.
- `graph-authoring` owns graph/prompt/tool authoring and validation evidence.
- `review-pr` owns optional implementation assessment against a real PR head.

GitClaw supplies trusted input and invokes these routes. It does not paraphrase
their doctrine into another process engine.

### Scripts own external boundaries and side effects

Deterministic code owns:

- trust-gating GitHub events;
- request/reference snapshots and hashes;
- exact operation parsing;
- artifact and containment verification;
- test/lint/smoke invocation;
- explicit-path staging and commits;
- rebase/push race handling;
- branch/PR creation and updates;
- factual issue comments and closure;
- scheduled graph execution, process bounds, and failure artifacts; and
- duplicate event suppression where GitHub delivery semantics require it.

The generic Copilot process must not receive GitHub write credentials.

### Git is the lifecycle database

Use existing durable artifacts instead of duplicating semantic state:

| Process fact | Durable record |
|---|---|
| Owner intent | GitHub issue + immutable request artifact |
| Specification | FR commit |
| Authority | Judgement artifact and commit |
| Implementation | Branch commits and PR head |
| Assessment | Review artifact/comment tied to PR SHA |
| Requirement revision | Issue edit + new request hash + new FR version |
| Implementation revision | New commit on the same branch/PR |
| Delivery | Merge commit/tag |
| Scheduled result | Output or `.failed.json` commit |

Retain only event-delivery deduplication not already answered by Git/PR state.

### Artifacts connect capabilities

Capabilities communicate through versioned artifacts, not imports into one
large controller:

| Capability | Input | Output |
|---|---|---|
| Issue executor | verified `request.json` | working-tree artifacts + execution report |
| Doctrine bundle | request/FR/PR plus repository evidence | FR, judgement, authoring report, review |
| Git operations | verified diff + execution report | commit/branch/PR/issue URLs and SHAs |
| Test/CI | repository + declared test command | test report and status |
| Scheduled runner | graph + date/config | Markdown candidate or `.failed.json` |

## Capability 1: Executable Doctrine Bundle

### Goal

Make YAMLGraph's actual agent control environment available to a clean project:

- `.github/copilot-instructions.md`;
- feature-request, judge, graph-authoring, and review skills;
- judge, author, and review adapter graphs/prompts;
- `scripts/judge.sh`, `scripts/author.sh`, and `scripts/review.sh`;
- graph-authoring preflight and sentinel enforcement;
- relevant command and post-edit hooks; and
- minimal measured transitive helpers.

### Distribution

The bundle is pinned to one full YAMLGraph commit. A manifest records source,
target, SHA-256, mode, and whether each file is byte-identical or explicitly
adapted locally. Runtime download of mutable doctrine is forbidden.

Bundle updates arrive as reviewable Git commits/PRs.

### Current planning artifact

- [FR-846 GitClaw Executable Control Bundle](../feature-requests/FR-846-gitclaw-executable-control-bundle.md)

FR-846 is a spike prerequisite. It must prove in a clean clone that Copilot
loads the controls, canonical adapters execute, hooks enforce route boundaries,
and adapters perform no Git/GitHub side effects.

### Precedent

- [FR-844 GitClaw Repository Instructions](../feature-requests/FR-844-gitclaw-repository-instructions.md) proved non-interactive Copilot loads repository instructions.
- [FR-827 GitClaw Forkable Runner](../feature-requests/FR-827-gitclaw-forkable-runner.md) vendored skill prose but omitted executable adapters/hooks.
- YAMLGraph graph-authoring enforcement was established by FR-765/FR-806/FR-767, referenced by FR-846.

## Capability 2: Trusted Issue to Generic LLM Executor

### Goal

Turn one trusted issue command into one generic Copilot execution over verified
artifact paths and hashes.

The executor does not contain plan/judge/enforce/review routing. Repository
instructions and skill discovery determine the operation. Canonical adapters
create independent executions where doctrine requires them.

### Minimal contract

Input:

```json
{
  "repository": "owner/repo",
  "issue_number": 1,
  "request_path": ".../request.json",
  "request_sha256": "...",
  "operation": "plan|enforce|review|revise",
  "head_sha": "...",
  "reference_manifest": "optional path",
  "reference_sha256": "optional hash"
}
```

Output:

- governed artifacts in the working tree;
- adapter artifacts where applicable;
- a bounded execution report listing paths, hashes, validations, and failures;
- no commit, push, issue comment, PR mutation, or merge.

### Reuse

This capability is useful to YAMLGraph itself and to any repository that wants
trusted remote issue execution under local agent doctrine.

### Current planning artifact

- [FR-845 GitClaw Generic Skill Executor](../feature-requests/FR-845-gitclaw-generic-skill-executor.md)

FR-845 depends on FR-846. It deletes the custom semantic process rather than
preserving it as a fallback.

### Precedent and retained boundaries

- [FR-840 Minimal Authority Repair](../feature-requests/FR-840-gitclaw-minimal-authority-repair.md): immutable owner request artifact.
- [FR-841 Owner Reference Assets](../feature-requests/FR-841-gitclaw-reference-assets.md): owner-committed bounded reference staging.
- [FR-830 Repository-Scoped Ledger](../feature-requests/FR-830-gitclaw-repository-scoped-ledger.md): repository identity lesson; retain only event dedup if still needed.
- [FR-829 Read-Only Public Tool Policy](../feature-requests/FR-829-gitclaw-read-only-public-tool-policy.md): contradiction evidence that semantic policy was duplicated.

## Capability 3: Deterministic Git and GitHub Operations

### Goal

Publish verified agent output without exposing GitHub write credentials to the
agent process.

### Responsibilities

- verify expected operation-specific artifacts;
- verify immutable inputs remain unchanged;
- enforce write containment;
- stage explicit paths only;
- create conventional commits;
- pull/rebase before push;
- create or update implementation branches and PRs;
- post factual issue comments with artifact links and SHAs;
- close issues only when command semantics are terminal;
- preserve human merge authority; and
- suppress duplicate event delivery.

### Packaging decision

Start as a well-bounded GitClaw component. Extract to a reusable Action or CLI
after a second consumer—likely YAMLGraph—uses it independently.

Do not create a separate repository before that witness.

### Existing evidence

- FR-827's push-race repair established pull/rebase-before-push.
- [FR-830](../feature-requests/FR-830-gitclaw-repository-scoped-ledger.md) established repository-scoped event identity.
- GitClaw's current intake trust gate and containment code are implementation
  precedents, not immutable APIs.

### Required future FR

Plan a separate FR after FR-846 proves adapter behavior. It should freeze the
execution-report schema, branch/PR semantics, credential separation, and issue
closure rules. FR-845 may compose this work only if judgement confirms the
surface remains one responsibility; otherwise split it.

## Capability 4: Scheduled YAMLGraph Runner

### Goal

Run one declared YAMLGraph on a schedule and commit either a bounded candidate
or explicit failure artifact.

### Basic reusable runner

- schedule + manual dispatch;
- pinned YAMLGraph/runtime install;
- one graph path and date/config variables;
- bounded subprocess time/stdout/stderr;
- strict JSON-state candidate extraction;
- candidate byte limit;
- `.failed.json` on failure;
- commit output before surfacing failure;
- attribution/provenance; and
- source/schema drift visible as failure.

### Advanced optional runner

Multi-feature DAG composition is a separate profile:

- strict `composition.json`;
- cycle/missing-dependency validation;
- dependency-first execution and same-run reuse;
- bounded candidate envelopes; and
- unrelated-feature failure isolation.

The new-project template should default to one graph. GitClaw may demonstrate
the advanced profile, but the simple runner must not depend on it.

### Existing evidence

- [FR-819 GitHub-Native Daily Digest](../feature-requests/FR-819-github-native-digest-poc-repo.md): repository-as-runtime and scheduled publication.
- [FR-827](../feature-requests/FR-827-gitclaw-forkable-runner.md): initial cron runner.
- [FR-835 Composition Boundary](../feature-requests/FR-835-gitclaw-composition-boundary.md): advanced same-run composition.
- [FR-836 Candidate Output Contract](../feature-requests/FR-836-gitclaw-candidate-output-contract.md): exact `candidate` output.

### Required future FR

Extract the one-graph runner contract before changing cron. Preserve the current
runner until the extracted runner proves output/failure parity. Advanced DAG
retention requires a named consumer outside the basic template.

## Capability 5: Testing and CI

### Two distinct modes

**Bootstrap CI** exists before an agent runs:

- checkout;
- install declared test dependencies;
- run repository test command on push/PR;
- read-only permissions where possible.

**Issue-created CI** is an agent task:

```text
Add pytest CI to this repository
```

It passes through the generic executor, doctrine, artifact verification, and
Git operations.

### Bootstrap paradox

The built-in `GITHUB_TOKEN` cannot normally create/modify workflow files in the
required way. Issue-created CI therefore needs one explicit path:

- an installation PR merged by a human;
- a GitHub App installation token;
- a narrowly scoped PAT; or
- a pre-installed generic workflow whose behavior is configured outside the
  workflow file.

Do not conceal this boundary inside agent permissions.

### Existing evidence

- GitClaw's `tests.yml` is the minimal bootstrap precedent.
- [FR-842 Lint/Compile Validation Parity](../feature-requests/FR-842-lint-compile-validation-parity.md) demonstrates mechanically aligned validation in YAMLGraph.

### Required future FR

First plan the test-command/config contract and bootstrap installation path.
Treat “CI runner” and “agent authors CI workflow” as separate acceptance cases.

## Capability 6: GitClaw Integration Demo and Template

### Role

GitClaw composes the preceding capabilities and demonstrates the full journey:

```text
trusted issue
  -> generic skill-driven execution
  -> verified artifacts
  -> deterministic commit/PR/issue update
  -> optional CI
  -> optional scheduled YAMLGraph output
```

GitClaw is also the **new-project template**.

### Template baseline

```text
.github/
  workflows/       issue executor, tests, optional schedule
  skills/          pinned executable doctrine bundle
  hooks/           pinned/adapted executable controls
  copilot-instructions.md
scripts/           canonical adapter wrappers + deterministic mechanics
.gitclaw/          bundle manifest + local configuration
feature/           one writable project/feature
feature-requests/
references/        owner-curated read-only inputs
examples/          read-only precedents, not active products
tests/
outputs/
```

Fresh templates ship with no operational issue history, no generated sibling
products, and no copied runtime outputs.

### Existing projects

Existing repositories use an additive installation PR, initially produced by a
local installer command and eventually possibly by a GitHub App:

```text
gitclaw init --repo .
```

The installer must not overwrite existing CI, project instructions, hooks,
dependencies, branch protection, or application code. It adds a managed bundle,
thin workflows, configuration, and adapter wrappers on a branch for human
review.

Existing project doctrine remains primary for product-specific rules. The
GitClaw bundle contributes process instructions through a deterministic managed
include/scoped instruction surface rather than replacing local instructions.

### Git workflow

Use one flow for templates and existing projects:

```text
issue -> specification artifacts -> implementation branch/PR
      -> optional review -> revisions -> human merge
```

Review is optional. Requirement changes replan; implementation feedback revises
the current branch under unchanged judged scope.

## FR Lineage and Disposition

### Foundation retained

| FR | Result retained |
|---|---|
| [FR-827](../feature-requests/FR-827-gitclaw-forkable-runner.md) | Public template, trusted issue trigger, GitHub Actions/Copilot viability, cron/publication proof |
| [FR-829](../feature-requests/FR-829-gitclaw-read-only-public-tool-policy.md) | Public-read safety lessons; custom semantic policy itself is retirement candidate |
| [FR-830](../feature-requests/FR-830-gitclaw-repository-scoped-ledger.md) | Repository identity must scope event dedup/state |
| [FR-840](../feature-requests/FR-840-gitclaw-minimal-authority-repair.md) | Immutable owner request and per-stage hash verification |
| [FR-841](../feature-requests/FR-841-gitclaw-reference-assets.md) | Bounded owner reference assets and provenance |
| [FR-842](../feature-requests/FR-842-lint-compile-validation-parity.md) | Validation commands must match actual compile/runtime semantics |
| [FR-844](../feature-requests/FR-844-gitclaw-repository-instructions.md) | Copilot loads repository instructions; mirrored upstream instructions replace local restatement |

### Advanced runtime retained independently

| FR | Disposition |
|---|---|
| [FR-835](../feature-requests/FR-835-gitclaw-composition-boundary.md) | Advanced multi-feature scheduled composition; not required by basic template |
| [FR-836](../feature-requests/FR-836-gitclaw-candidate-output-contract.md) | Preserve candidate contract for simple and advanced runners |

### Historical evidence, not target architecture

| FR | Lesson |
|---|---|
| [FR-828](../feature-requests/FR-828-gitclaw-oulu-civic-intelligence-cookbook.md) | Full template acceptance exposed copied state and continuous-enforce ceiling |
| [FR-831](../feature-requests/FR-831-oulu-bulletin-staged-source-reuse.md) | Recover prior art before implementation; product decomposition did not repair process abstraction |
| [FR-832](../feature-requests/FR-832-gitclaw-oulu-harbour-source.md), [FR-833](../feature-requests/FR-833-gitclaw-oulu-procurement-source.md), [FR-834](../feature-requests/FR-834-gitclaw-oulu-municipal-source.md) | One-source implementation scale and public-source contracts |
| [FR-837](../feature-requests/FR-837-gitclaw-oulu-source-health-assembly.md), [FR-838](../feature-requests/FR-838-gitclaw-oulu-assembly-recovery.md) | Assembly/recovery planning evidence; do not continue as default template process |
| [FR-839](../feature-requests/FR-839-gitclaw-immutable-owner-contract.md) | Rejected overcorrection; replaced by FR-840 |
| [FR-843](../feature-requests/FR-843-gitclaw-remediation-convergence.md) | One-repair convergence lesson; custom graph loop is retirement candidate |
| Obsolete Oulu FR-845 | Removed; five issue-driven sibling features are not the target process |

### Current replacement plans

| FR | Purpose | Dependency |
|---|---|---|
| [FR-846](../feature-requests/FR-846-gitclaw-executable-control-bundle.md) | Prove minimal executable mirrored doctrine bundle | none |
| [FR-845](../feature-requests/FR-845-gitclaw-generic-skill-executor.md) | Replace custom semantic harness with one generic node and deterministic outer mechanics | FR-846 |

FR-846 is enforced and human-reviewed at GitClaw `8bb8763`. FR-845 is
independently judged, folded, and now has active implementation authority.

## Retirement Plan

The target explicitly retires failed or duplicated surfaces:

| Current surface | Target disposition |
|---|---|
| Four custom stage prompts | Delete; applicable skills/adapters own semantics |
| 443-line semantic process graph | Replace with one generic node |
| Planner-session resume | Delete |
| Review-remediation edge loop | Delete; feedback becomes a new issue command/commit |
| Semantic ledger states mirroring Git/PR | Delete; retain event dedup only if evidenced |
| Duplicated generated-feature policy | Delete or reduce to local path/side-effect addendum |
| Prompt-policy marker tests | Replace with bundle parity, command, artifact, and side-effect tests |
| Copied active generated features in template | Remove from active surface; examples become read-only precedents |
| Multi-feature slug allocation | Remove from one-feature template |
| Multi-feature cron/DAG in basic template | Replace with one-graph runner after parity; retain advanced profile only for named consumers |

Every surviving surface needs a named consumer. “Temporary fallback” is not a
consumer.

## Sequenced Roadmap

### Stage 0 — Planning cleanup

1. Remove obsolete Oulu phased-delivery FR.
2. ~~Human-review FR-846's folded judgement.~~ Complete.
3. ~~Enforce FR-846 and record clean-clone bundle witnesses.~~ Complete.
4. Enforce FR-845; human-review its exact replacement/deletion diff before
  canonical push.

### Stage 1 — Executable bundle spike — Complete

Enforce FR-846 in a disposable clean clone. Stop if canonical adapters or hooks
cannot retain their guarantees without broad YAMLGraph-monorepo coupling.

### Stage 2 — Generic issue executor

Enforce FR-845 RED/GREEN:

- generic command parsing;
- one Copilot node;
- no GitHub credentials in agent environment;
- direct skill/adapter use;
- artifact verification;
- deterministic Git/PR/issue mechanics; and
- deletion of the old semantic harness.

### Stage 3 — Extract independent Git operations

After GitClaw and YAMLGraph both consume the mechanics, plan extraction as a
reusable Action/CLI. Do not extract before the second consumer.

### Stage 4 — Scheduled runner extraction

Plan and enforce a one-graph runner contract. Keep advanced composition as an
optional profile with explicit consumers.

### Stage 5 — Testing/CI capability

Plan bootstrap CI and issue-authored CI separately. Resolve workflow-write
credentials explicitly.

### Stage 6 — Rebuild GitClaw template/demo

Create a clean template from the proven components. Validate:

- new project path: template -> two required secrets/config -> trusted issue;
- existing project path: installer branch/PR -> human review -> issue command;
- plan -> judged FR;
- enforce -> implementation PR;
- optional review -> implementation revision;
- issue edit -> specification replan; and
- scheduled graph -> committed output/failure.

### Stage 7 — Return to Oulu cookbook

Replan the Oulu civic brief as one project using the rebuilt template. Reuse the
source contracts and failed-attempt evidence from FR-828/831-834, but do not
reuse the old custom process or generate five sibling products.

## Open Decisions

These require explicit future judgement, not implementation inference:

1. Where the reusable issue-executor and Git-operations components live after a
   second consumer exists: YAMLGraph package, dedicated Action, or GitClaw CLI.
2. Whether the basic scheduled runner is a reusable workflow, composite Action,
   or small Python package.
3. The exact existing-project instruction/hook merge mechanism.
4. The credential route for issue-authored workflow changes.
5. Whether advanced multi-feature composition retains a named consumer after
   the basic template becomes single-feature.
6. Versioning/release cadence for the executable doctrine bundle.

## Success Measures

The architecture succeeds when:

- a clean trusted issue can invoke applicable skills without custom semantic
  routing;
- judgement, authoring, and review retain their independent canonical routes;
- the agent process has no GitHub write credentials;
- Git/PR/issue operations are deterministic and artifact-driven;
- new and existing projects use the same core executor contract;
- scheduled execution is independently reusable;
- CI bootstrap and issue-authored CI are explicit separate capabilities;
- GitClaw remains the full public demo; and
- production semantic orchestration/prompt surface is materially smaller after
  deleting the superseded harness.
