# Judgement: FR-849 GitClaw Kalevala Lifecycle Acceptance Script

**Verdict:** APPROVED WITH REVISIONS - authority is active after R-1 through R-4 were folded into FR-849.

**Prior art:** FR-845's current Plan/Enforce/Review/Revise contract, FR-847's independently runnable task, and FR-848's current-tree evidence discipline remain authoritative. FR-849 adds an investigation witness only and does not repair lifecycle support.

## What Is Sound

The missing lifecycle witness is real. Current Plan couples judgement, while standalone Judge, Test PR, and Run YAMLGraph issue commands are absent. One disposable-repository shell test can expose the full artifact chain before product changes are planned.

The scope is correctly limited to one script, expects RED first, uses the
required repository parameter as operator-selected target authority, uses
existing operator authentication, and keeps the implementation PR unmerged.

## Required Revisions

| # | Finding | Binding resolution |
|---|---|---|
| R-1 | Current coupled Plan could pass and merge before Judge | Gate Plan changed files to exactly one new FR and no judgement, implementation, workflow, graph, prompt, or runtime path |
| R-2 | Avoiding token assignment did not prevent inherited token consumption | Reject inherited GitHub token variables or explicitly unset them for every `gh` invocation |
| R-3 | Wrong or unconfigured target could produce a false lifecycle RED | Superseded by operator direction: `owner/repo` is a required positional parameter and sole target authority; validate syntax, keyring auth, and repository existence only |
| R-4 | Workflow conclusion alone did not prove semantic success | Emit machine-readable phase summaries and inspect lint/run exit codes, outputs, and empty Run diff |

All revisions are folded into FR-849.

## Frozen Scope

Authorized:

- `../gitclaw/acceptance/kalevala-lifecycle.sh` only in GitClaw;
- FR-849, this judgement, generated board, and one diary reflection in YAMLGraph;
- issues, runs, two authority PR merges, implementation PR, and evidence in the repository explicitly named by the operator.

Not authorized: any GitClaw parser, workflow, permission, control bundle, skill,
adapter, hook, prompt, graph, runtime, request/reference, publisher, test,
dependency, secret, schedule, README, or lifecycle repair; implementation PR
merge.

## Enforcement Gates

1. Do not re-run the judge during enforcement.
2. GitClaw tracked diff must contain only the executable acceptance script.
3. Real execution targets exactly the required `owner/repo` parameter and
	enforces keyring-only authentication.
4. The first RED evidence must be preserved, not repaired in this scope.
5. Human review of mutation boundaries and RED evidence is mandatory before push.

Authority granted for the folded acceptance-script-only scope.
