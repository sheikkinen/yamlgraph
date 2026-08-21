# Feature Request: FR-849 GitClaw Kalevala Lifecycle Acceptance Script

**Priority:** HIGH
**Type:** Acceptance test / investigation
**Status:** Completed 2026-08-21 - script published in GitClaw at `69fc2ce`
**Effort:** 0.5 day
**Requested:** 2026-08-21
**Depends on:** FR-845, FR-847, FR-848
**First consumer / first event:** The operator runs one shell script against the
GitClaw repository named by its required parameter and receives a durable RED witness at
the first unsupported lifecycle command.

**Prior art:** FR-845 introduced exact `Plan`, `Enforce`, `Review`, and `Revise`
issue commands plus deterministic publication. FR-847 proved independently
runnable YAMLGraph tasks. FR-848 established that acceptance evidence belongs
outside the live tree unless a current consumer exists. This FR creates the
current consumer: a repeatable shell witness for the full desired lifecycle.

## Summary

Add one executable shell acceptance script to GitClaw. It creates six GitHub
issues sequentially in the GitClaw repository supplied as its parameter:

1. plan conversion of the haiku example to Kalevala runic format;
2. judge the committed plan;
3. enforce the judged plan;
4. review the implementation PR;
5. test the implementation PR; and
6. lint and run the YAMLGraph implementation, expecting lint success and graph
   execution failure.

The script observes each issue-triggered workflow, captures logs, and records
changed-file lists for produced PRs. It uses only the operator's existing `gh`
keyring authentication and requests no additional GitHub token, scope, workflow
permission, or repository permission.

This FR authorizes the acceptance script only. It does not repair any failure
the script exposes. RED is the expected first result and is the evidence needed
to plan later lifecycle implementation.

## Value Statement

GitClaw gains one executable statement of its intended issue-driven lifecycle,
turning missing command phases and incorrect coupling into observable failures
instead of architectural discussion.

## Problem

The current GitClaw command contract supports only:

- `Plan <subject> as a Feature Request`;
- `Enforce <FR-path>`;
- `Review <PR> against <FR-path>`; and
- `Revise ...`.

Current `Plan` also produces and publishes both FR and judgement. The desired
acceptance lifecycle separates Plan and Judge, then adds explicit Test and Run
YAMLGraph issue operations. Therefore the full acceptance sequence cannot pass
today. Without one executable witness, later work can accidentally optimize
individual commands while the end-to-end artifact transitions remain broken.

The final YAMLGraph expectation is deliberately asymmetric:

- graph lint must exit zero;
- graph execution must exit nonzero; and
- the enclosing issue operation is successful only when both expectations are
  observed exactly.

A graph execution success is an acceptance failure for this scenario.

## Ideal Result

Running one script against a disposable, preconfigured GitClaw repository
creates six issues one by one, waits for and records each intake run, records
every generated PR's changed files, merges only authority PRs needed by the next
phase, and reports one final GREEN only when all issue commands complete with
their declared expectations.

Before lifecycle support exists, the same script exits nonzero with a durable
RED evidence directory identifying the first failed expectation and preserving
workflow logs and changed-file observations. The operator-selected repository
is the mutation boundary; the script never supplies a GitHub credential through
environment variables or command arguments.

## Proposed Solution

### 1. One acceptance artifact

Add exactly:

```text
acceptance/kalevala-lifecycle.sh
```

The script is executable, passes `bash -n`, and uses only standard POSIX/macOS
shell tools plus `git` and `gh`. It is not part of production intake execution.

### 2. Explicit repository and credential boundary

Invocation:

```bash
acceptance/kalevala-lifecycle.sh owner/repo
```

The repository parameter is required and is the sole target authority. The
operator is responsible for selecting and configuring the repository. It must
already:

- contain the GitClaw template under test;
- have Actions enabled;
- have required repository secrets and variables configured; and
- be writable by the operator's existing `gh` keyring identity.

The script:

- rejects missing or malformed `owner/repo`;
- fails before mutation if inherited `GH_TOKEN`, `GITHUB_TOKEN`, or another
  GitHub token variable used by the script is set;
- verifies `gh auth status` and that the named repository exists before
  creating issues;
- does not read, print, export, forward, create, or update secrets;
- does not set `GH_TOKEN`, `GITHUB_TOKEN`, or another token variable;
- does not call `gh auth login`; and
- requires no scope beyond the operator identity already used by `gh`.

### 3. Exact issue sequence

The script creates these titles dynamically, one only after observing the
previous issue workflow:

```text
Plan conversion of haiku based example to Kalevala runic format as a Feature Request
Judge <FR-path>
Enforce <FR-path>
Review <implementation-PR> against <FR-path>
Test PR <implementation-PR>
Run YAMLGraph PR <implementation-PR> expecting graph failure
```

The Plan body requires conversion of the existing haiku example to Finnish
Kalevala runic format while preserving its self-sufficient date tool and
optional city. Plan is explicitly plan-only; judgement is the next issue.

The script discovers `<FR-path>` from the Plan PR's changed files and discovers
the implementation PR from Enforce publication. It does not hardcode FR or PR
numbers.

Before merging Plan, its changed-file list must contain exactly one newly added
`feature-requests/FR-*.md` and no sibling judgement, implementation, workflow,
graph, prompt, or runtime path. Coupled Plan+Judge output is RED at the Plan
phase and must not be merged.

### 4. Sequencing and mutation

For each issue the script:

1. creates the issue with `gh issue create`;
2. discovers the matching `intake.yml` run by exact issue title;
3. waits for completion and captures full run logs;
4. records the run conclusion and URL;
5. discovers any PR URL from the factual GitClaw issue comment; and
6. captures `gh pr diff --name-only` for that PR.

It also writes one machine-readable per-phase summary containing issue URL, run
URL, run conclusion, PR URL when present, changed-file-list path, phase status,
and pass/fail or skip reason. A workflow conclusion alone is insufficient.

Plan and Judge authority PRs may be squash-merged by the script using the
operator's existing `gh` session because later phases require committed
authority. The implementation PR is not merged. Review, Test, and Run observe
the implementation PR head.

The script makes no direct commit, push, branch, file edit, issue close, secret
mutation, workflow mutation, or merge other than the two explicit authority PR
merges.

### 5. Expected-failure YAMLGraph operation

The Run YAMLGraph issue body requires deterministic execution at the named PR
head:

```text
yamlgraph graph lint features/haiku/graph.yaml
yamlgraph graph run features/haiku/graph.yaml --full
```

The issue operation succeeds only if:

- lint returns zero;
- graph run returns nonzero;
- both exit codes and command outputs are recorded; and
- no files change.

The script must inspect observed output for both exit codes and command-output
evidence, and must verify the Run phase changed-file list is empty.

The shell acceptance script treats that successful inversion as GREEN for the
Run phase. If graph execution returns zero, the phase is RED.

### 6. RED is the first deliverable

The current repository is expected to fail this script because standalone
`Judge`, `Test PR`, and `Run YAMLGraph PR ...` are unsupported, and Plan still
pairs judgement with planning. The first execution must:

- exit nonzero;
- identify failed/skipped expectations;
- preserve all evidence gathered before failure;
- avoid repairing parser/workflow/executor behavior.

The RED result is not a failed implementation of FR-849. It is FR-849's primary
acceptance artifact and input to a later feature request.

## Exact Change Surface

Authorized:

- new executable `acceptance/kalevala-lifecycle.sh` only in GitClaw;
- FR-849, sibling judgement, generated FR board, and diary reflection in
  YAMLGraph;
- creation of issues, intake runs, authority PR merges, implementation PR, and
  evidence in the explicitly supplied repository during execution.

Not authorized in GitClaw:

- command parser, containment, publisher, request/reference contracts;
- intake, tests, cron, or other workflows;
- generic prompt or `gitclaw.yaml`;
- control bundle, mirrored skills/adapters/hooks, README, tests, dependencies,
  permissions, secrets, schedules, graph, prompt, or runtime artifacts; or
- any edit besides the one acceptance script.

## Acceptance Criteria

- [x] AC-01: GitClaw diff contains exactly one new tracked executable file, `acceptance/kalevala-lifecycle.sh`; no existing tracked file changes
- [x] AC-02: Script passes `bash -n`; `shellcheck` passes when available, and absence is recorded
- [x] AC-03: Missing or malformed repository parameter, failed keyring auth, or unavailable named repository fails before GitHub mutation; the script applies no canonical/disposable classification
- [x] AC-04: Script rejects or explicitly unsets inherited `GH_TOKEN`, `GITHUB_TOKEN`, and every GitHub token variable it could consume; it never sets, prints, forwards, creates, or updates tokens/secrets and never calls `gh auth login`
- [x] AC-05: Script encodes the six exact dynamic issue titles in required order and never creates a later issue until the preceding workflow and phase gates pass
- [x] AC-06: Plan records changed files and fails before merge unless exactly one new FR exists with no judgement, implementation, workflow, graph, prompt, or runtime path
- [x] AC-07: Judge dynamically uses the committed FR, requires and records a judgement-only authority PR, and only Plan/Judge PRs may be squash-merged
- [x] AC-08: Enforce dynamically discovers and records the implementation PR, which remains unmerged
- [x] AC-09: Review, Test, and Run observe the implementation PR head without direct file, Git, secret, permission, workflow, issue-close, or merge mutation
- [x] AC-10: Every phase records full logs, URLs, conclusion, changed-file-list path, and machine-readable status/reason; later phases are explicitly skipped after RED
- [x] AC-11: Run YAMLGraph requires lint exit zero, graph-run exit nonzero, both outputs/exit codes, and an empty changed-file list; graph-run zero or missing evidence is RED
- [x] AC-12: First real execution against the operator-selected repository exits nonzero at the first unsupported/mismatched lifecycle expectation and preserves all gathered RED evidence
- [x] AC-13: Existing GitClaw suite, haiku lint, and control-bundle verification remain green with evidence recorded
- [x] AC-14: Human reviews mutation boundary, token guard, repository-parameter authority, authority merges, and first RED evidence before push

## Implementation Status - 2026-08-21

GitClaw implementation is exactly one untracked executable artifact:
`acceptance/kalevala-lifecycle.sh`. No existing tracked GitClaw file changed.

Static/local validation:

- `bash -n acceptance/kalevala-lifecycle.sh`: passed;
- ShellCheck: unavailable and recorded;
- inherited `GH_TOKEN` refusal: passed;
- full GitClaw suite: 117 passed;
- haiku graph lint: no issues;
- control bundle: verified.

First real execution targeted the operator-supplied `sheikkinen/gitclaw`:

- issue: `https://github.com/sheikkinen/gitclaw/issues/4`;
- run: `https://github.com/sheikkinen/gitclaw/actions/runs/32443301071`;
- evidence: `gitclaw-kalevala-acceptance-20260821T062500-8398` under the
  platform temporary directory;
- result: RED at Plan; Judge, Enforce, Review, Test, and Run YAMLGraph skipped;
- workflow: generic agent and artifact verification succeeded; publisher failed
  while creating the PR after pushing branch `gitclaw/issue-4-plan`;
- orphan branch head: `a4076a9f4f90cb174df0d75cf83a97536c0e310d`;
- Plan semantic gate also failed: the branch contains immutable request, FR,
  and sibling judgement rather than exactly one FR;
- no PR was created or merged; no later issue was created.

The first execution exposed an interactive `gh run watch` defect in the test
script itself. The sole script was repaired to use noninteractive API polling;
the product RED was preserved rather than repaired. No GitClaw lifecycle or
publisher code changed.

**Human review and publication:** The operator reviewed the sole executable
script, repository-parameter mutation boundary, keyring-only token guard,
Plan/Judge authority merge gates, and first RED evidence, then selected
“Approve commit and push.” GitClaw `main` was pushed at
`69fc2ce` (`acceptance/kalevala-lifecycle.sh`, mode `100755`, no other GitClaw
path changed).

## Alternatives Considered

- **Implement missing lifecycle commands now:** rejected; the user explicitly
  restricted this task to the acceptance test. The witness must precede repair.
- **Use one monolithic issue:** rejected; it would hide artifact transitions and
  violate the requested one-command-per-issue sequence.
- **Use direct local function calls:** rejected; the subject under test is
  GitHub issue intake, workflow execution, publication, and observable diffs.
- **Script-selected safe repository list:** rejected; the required repository
  parameter is the operator's explicit target authority.
- **Inject a temporary token:** rejected; the operator's existing `gh` keyring
  session is the explicit boundary.
- **Treat graph failure as overall failure:** rejected; this scenario tests
  expected-failure semantics, so lint success plus graph failure is success.

## Related

- `feature-requests/FR-845-gitclaw-generic-skill-executor.md`
- `feature-requests/FR-847-cron-schedules-one-yamlgraph-task.md`
- `feature-requests/FR-848-gitclaw-obsolete-artifact-purge.md`
- `../gitclaw/acceptance/kalevala-lifecycle.sh`

## Judgement

**Verdict:** APPROVED WITH REVISIONS - all revisions folded; authority is active
for the acceptance script only.

| # | Finding | Folded resolution |
|---|---|---|
| R-1 | Coupled current Plan could be merged before Judge RED | Require exactly one FR and no judgement/implementation/platform path before Plan merge |
| R-2 | “Does not set token” did not prevent inherited token consumption | Fail before mutation on inherited GitHub token variables or explicitly unset them for every `gh` call |
| R-3 | Wrong/unconfigured repository could masquerade as lifecycle RED | Superseded by operator direction: the required repository parameter is authoritative; only syntax, keyring auth, and repository existence are checked |
| R-4 | Workflow success did not prove phase semantics | Require machine-readable phase summaries and substantive Run exit-code/output/no-diff evidence |

**Purge list:** No product repair, helper library, workflow, parser, prompt,
test, README, or archive file. One acceptance script only.

**Scope frozen:** Yes. Do not re-run the judge during enforcement. First RED
evidence and human review are mandatory before push.

### Questions for the human

None.
