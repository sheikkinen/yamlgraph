# Feature Request: FR-835 GitClaw Composition Boundary

**Priority:** HIGH
**Type:** Platform / GitClaw runtime policy
**Status:** Enforced 2026-08-20 - canonical and consumer composition boundary
published after both human review gates; 16/16 acceptance criteria satisfied
**Effort:** 1 day
**Requested:** 2026-08-20
**Parent:** FR-831
**Depends on:** FR-829, FR-830, FR-831, FR-832, FR-833, FR-834
**Blocks:** FR-831 Tasks 6-7
**Prior art:** FR-831 makes a separate platform FR mandatory when generated
features cannot safely reuse one another. FR-832 through FR-834 prove three
independently runnable source adapters, but each exposes only one rendered
candidate from its own directory. GitClaw's generated-feature policy permits
bounded committed reads only inside that directory; `tools/contain.py` rejects
changes to other features; and `tools/cron_run.py` executes every graph
independently. Preserve those boundaries. Do not approve cross-directory
imports, adapter copying, stale output-file reads, or source re-fetching.
**First consumer / first event:** FR-831 Task 6, when one separately governed
composer declares the three Oulu source features and cron supplies their
same-run outcomes without granting it filesystem access to those features.

## Summary

Add one platform-owned composition boundary to GitClaw. A generated feature may
optionally commit `composition.json` inside its own directory, declaring the
exact feature slugs whose same-run results it consumes. The cron runner validates
the dependency graph, runs dependencies first, and passes a bounded JSON
envelope through the fixed `source_snapshots` graph variable.

The envelope contains only each declared dependency's slug, runner status, and
either its opaque Markdown candidate or bounded failure reason. The composer
runs on partial and all-source failure so its separately judged contract can
render explicit health. It cannot import another feature's Python, read another
feature directory, inspect prior `outputs/`, fetch the sources again, or mutate
shared state.

This is FR-831 Task 5 only. It establishes platform mechanics and policy; it does
not create the Oulu composer, interpret source facts, synthesize prose, alter
source adapters, or publish a bulletin.

## Decision

Cross-feature assets remain forbidden to generated features. Reuse is approved
only through platform orchestration of declared same-run outputs:

1. source implementations remain independently owned and immutable;
2. dependency names are explicit, reviewable, and contained with the consumer;
3. cron, not generated code, resolves and schedules dependencies;
4. source candidates remain opaque at the platform boundary;
5. source success/failure is represented structurally; and
6. a later composer owns deterministic interpretation and partial-failure
   behavior under its own judgement.

No adapter duplication is approved.

## Frozen Manifest Contract

A composing generated feature may contain `features/<slug>/composition.json`:

```json
{
  "version": 1,
  "dependencies": [
    "oulu-harbour-source-snapshot",
    "oulu-procurement-source-snapshot",
    "oulu-municipal-notice-source-snapshot"
  ]
}
```

Rules:

- The file is optional. A feature without it retains current behavior.
- Parse with `json`; reject duplicate keys, unknown keys, wrong types, and any
  version other than integer `1`.
- `dependencies` is a non-empty list of unique canonical feature slugs in
  declaration order. Reject self-dependency, missing graphs, traversal,
  absolute paths, and duplicate names.
- Dependencies may themselves compose. Validate the complete graph before
  execution and reject cycles deterministically with the cycle path.
- Only declared transitive scheduling is allowed; the direct consumer envelope
  contains direct dependencies only, in manifest order.
- The fixed graph input variable is `source_snapshots: str`. No manifest field
  can rename it, select arbitrary files, add commands, or declare origins.

## Frozen Runtime Envelope

For a composing feature, cron invokes YAMLGraph with its normal `date` plus one
`source_snapshots` JSON string. The decoded value is an ordered list with one
object per direct dependency:

```json
[
  {
    "feature": "oulu-harbour-source-snapshot",
    "status": "succeeded",
    "candidate": "..."
  },
  {
    "feature": "oulu-procurement-source-snapshot",
    "status": "failed",
    "reason": "exit 1: ..."
  }
]
```

Rules:

- `status` is exactly `succeeded` or `failed`.
- A succeeded entry has exactly `feature`, `status`, and `candidate`.
- A failed entry has exactly `feature`, `status`, and `reason`.
- Candidate text is passed unchanged; the platform does not parse, merge,
  summarize, relabel, or repair source facts.
- Failure reasons retain the existing bounded diagnostic tail and must not
  expose environment values or command arguments containing secrets.
- Enforce a 32 KiB UTF-8 limit per candidate and 96 KiB limit for the encoded
  envelope. The envelope stays below Linux's approximately 128 KiB
  single-argument ceiling because YAMLGraph receives it through one `--var`
  argument. Oversize becomes a failed dependency result; it is never truncated
  into plausible content.
- Results exist only in memory for the current cron invocation. A composer must
  not read prior output files, and cron must not substitute stale success for a
  current failure.
- A composer runs when any or all dependencies fail. Its output contract decides
  how to represent partial/all failure. Its own execution failure is recorded by
  the existing `.failed.json` mechanism.
- Each graph executes at most once per cron invocation even when multiple
  composers depend on it. Its one result is reused in memory.
- `composition.json` must be a non-symlink regular file of at most 16 KiB.
  Process stdout and stderr are bounded while the child runs; reaching a bound
  terminates that graph and records a bounded failure instead of exhausting
  runner memory or disk. Process-spawn errors are recorded per feature.

## Validation-Failure Semantics

Cron validates every manifest and the complete dependency graph before graph
execution. An invalid manifest, missing dependency, self-dependency, or cycle
does not abort unrelated work:

- the invalid feature receives a bounded failed result and its normal
  `outputs/<date>-<slug>.failed.json` artifact;
- every direct or transitive dependent receives its own bounded failed result
  naming the unavailable dependency and does not execute;
- unrelated valid cycle-free features still run and record outputs normally;
- no current or prior `outputs/` file is read as input;
- cycle diagnostics contain the deterministic canonical cycle path;
- stderr identifies every invalid/blocked feature in canonical slug order; and
- cron exits `1` after attempting all runnable features whenever any invalid,
  blocked, or executed feature failed.

The failed artifact uses the existing `feature`, `date`, and `reason` shape.
Diagnostics are bounded by the same existing failure-reason limit. Focused
tests assert exact failed/output files, stderr ordering, graph execution set,
and exit code for every validation-failure class.

## Platform Changes

Implement in canonical `sheikkinen/gitclaw`:

1. write failing focused tests for the frozen validation-failure semantics
  before changing runtime code;
2. extend `tools/cron_run.py` with strict manifest parsing, dependency graph
   validation, deterministic topological scheduling, same-run result caching,
   envelope bounds, and `source_snapshots` variable injection;
3. add focused `tests/test_cron_run.py` covering legacy and composition paths;
4. update `policy/generated-features.md` to permit only the declared envelope
   boundary while preserving same-directory reads and all forbidden behavior;
5. update plan, judge, enforce, and review prompts so composition manifests are
   planned, judged, implemented, and independently checked against the shared
   policy;
6. update README composition and failure semantics; and
7. make no workflow, dependency, ledger, containment allowlist, timeout, secret,
   or public-retrieval-policy change.

After canonical tests pass, a human must review the complete canonical runtime,
policy, prompt, test, and README diff plus validation evidence before the
canonical implementation is marked complete or pushed. Apply only those exact
reviewed platform files to `sheikkinen/gitclaw-oulu-civic-intelligence`. A human
must then review the consumer parity diff before rollout completion. The parity
check compares content hashes for every changed platform file before Task 6 is
filed. This is an operator-owned platform rollout, not an issue-generated diff;
issue #1 remains untouched.

## Validation

Focused tests must prove:

- legacy features run in sorted order with only `date` and unchanged output and
  failure-file behavior;
- valid manifest parsing and declaration-order envelopes;
- unknown/duplicate keys, wrong version/types, empty/duplicate dependencies,
  invalid slugs, self/missing dependencies, and cycles fail closed;
- deterministic dependency-first ordering and execute-once caching for shared
  dependencies;
- success, partial failure, and all-failure envelopes;
- composers still run on dependency failure;
- exact candidate preservation, Unicode/newline JSON round-trip, per-candidate
  and aggregate byte limits, Linux single-argument feasibility, bounded
  in-flight process output, spawn errors, and oversize-as-failure behavior;
- non-regular, symlinked, oversized, and non-UTF-8 manifests fail only the
  affected feature/dependents while unrelated features continue;
- no stale `outputs/` read and no filesystem access granted to generated code;
- existing containment and generated-feature-policy tests remain green; and
- the full GitClaw test suite passes in canonical and consumer repositories.

A bounded consumer witness then runs three synthetic source graphs plus one
synthetic composer without network or LLM use. It must prove dependency order,
partial failure, deterministic envelope bytes, one execution per graph, and
normal output/failure recording. It must not use the live Oulu adapters as test
fixtures or create the Task 6 feature.

## Acceptance Criteria

- [x] AC-01: Human review approves this judgement and the folded FR before
  implementation starts
- [x] AC-02: FR records the explicit decision that cross-directory imports,
      adapter duplication, source re-fetching, and stale output reads remain
  forbidden, and the platform does not parse source Markdown
- [x] AC-03: `composition.json` has the frozen strict schema and fixed
      `source_snapshots` variable
- [x] AC-04: Cron validates the complete graph before execution, schedules
  dependency-first deterministically, executes each runnable graph at most
  once, and preserves sorted independent legacy ordering
- [x] AC-05: Invalid manifests, missing dependencies, and cycles fail closed
  with bounded deterministic diagnostics and failed artifacts; dependents
  are blocked while unrelated valid features still run
- [x] AC-06: Same-run envelopes contain direct dependencies only, in manifest
  order, with exact succeeded/failed shapes and unchanged candidate text
- [x] AC-07: Partial and all-source failures still run the composer; its own
  failure uses the existing failed-artifact mechanism
- [x] AC-08: Per-candidate and aggregate UTF-8 limits fail closed without
      truncating candidate content
- [x] AC-09: Legacy feature behavior, ordering, outputs, exit status, and
  failure recording remain unchanged
- [x] AC-10: Policy and all four pipeline prompts enforce the same composition
      boundary without weakening containment or public retrieval restrictions
- [x] AC-11: Focused composition tests and the full canonical GitClaw suite pass
- [x] AC-12: A human reviews the canonical runtime/policy/prompt/test/README
  diff and validation evidence before canonical completion or push
- [x] AC-13: Exact reviewed platform files are rolled out to the Oulu consumer
      and verified by content hash and full consumer suite
- [x] AC-14: Synthetic consumer witness proves ordering, caching, deterministic
  envelope bytes, partial and all-source failure, and output recording
  without network, LLM, live Oulu adapters, or Task 6
- [x] AC-15: No workflow, dependency, ledger, containment allowlist, timeout,
  secret, source adapter, issue #1, live output, notification, or
  publication change
- [x] AC-16: FR-835 records canonical and consumer commits, tests, witness,
  parity hashes, both human reviews, deviations, and failed attempts before
  Task 6 is filed

## Implementation Status (2026-08-20)

Canonical GitClaw published the composition boundary at
`a99f7b90f0be547beb1115dabf7731a40aae45d6`. The human canonical gate approved
the exact runtime, policy, four prompts, README, and focused-test diff after
independent review reported no blocker or high finding. The post-rebase full
suite passed 92 tests; Ruff lint/format, the grade-D complexity scan, editor
diagnostics, file-size checks, and `git diff --check` were clean. Canonical
`main` was verified at the full SHA. The push created no GitHub Actions run.

The exact eleven reviewed files were rolled out to the Oulu consumer at
`eb640cc1f496f9c7b599301560ff4f3f440c4351` after a separate human parity-diff
approval. The consumer full suite also passed 92 tests, and every file matched
canonical byte-for-byte:

| Platform file | SHA-256 |
|---|---|
| `README.md` | `73240459e3e8931a97878004f0342b99ad82d87964bf22f0f2cf03cf84f619dd` |
| `policy/generated-features.md` | `b45cddbb522064bea540163b2c9e599de829e6531a7bbbf3a21a1e821154f3ec` |
| `prompts/enforce.yaml` | `a4a9cf4da478d771750163994da5a8e83cec8214a9b6376db4b4ef70c695824c` |
| `prompts/judge.yaml` | `d43c17e3c8933e759d7fb631aef29bba4eeaaf7597aff8b325df0910d90924a0` |
| `prompts/plan.yaml` | `59ad941a61c50162bd5868b208b580b45a0509f5dadec67a0da104ea4484fb90` |
| `prompts/review.yaml` | `7534cb4abf706fe35c52a5142d4c70c6f39ce6fe7fa5aac1880d0ba1b90917d5` |
| `tests/test_generated_feature_policy.py` | `8c1c61dd16d5401a41a3009cc4fd9b123b5fc2e7d9f83e728a7f1fb495590f78` |
| `tests/test_intake_tools.py` | `3ed4b1ddad755af83185b4aecd2edc922d17550a08ea5a82a3c4a7571a69b195` |
| `tools/cron_run.py` | `3b4d2de0cb5d17da960dbc92a791d02ad6fdf1f3604b98bbf128dcac405b3192` |
| `tests/test_cron_run.py` | `3f18dc4c5820ea0bd5dcaeb81277f2b06fd6c1a80f9a53a2f485bdceed7d0106` |
| `tests/test_cron_run_process.py` | `16c58acbc0aba561802c578b5a2ac46100f44b35414664dddda6a4bfb4540c74` |

A bounded consumer witness used three temporary synthetic source graphs and one
synthetic composer, with graph execution replaced locally so no network, LLM,
live adapter, or Task 6 feature was involved. Partial-failure and all-source-
failure runs proved sorted dependency execution, one execution per graph,
manifest-order deterministic envelope bytes, composer execution, successful
Markdown recording, and failed JSON recording.

Independent reviews and red-first tests found and repaired non-UTF-8 manifest
handling, recursive deep-graph traversal, Linux-infeasible envelope sizing,
symlink/TOCTOU manifest reads, post-capture-only process bounds, surviving
descendant processes, closed-pipe timeout bypass, leader-exit cleanup races,
and invisible pipe-closing descendants. The first canonical push was rejected
non-fast-forward because cron had advanced `main`; the approved commit was
rebased over that unrelated output-only commit and the 92-test suite reran
before a normal push. The initial 525-line focused test file was split into
386- and 131-line modules before commit and independently re-reviewed.

No workflow, dependency, ledger, state, containment allowlist, timeout, secret,
source adapter, issue #1, live output, notification, publication, YAMLGraph
core, or Task 6 change was made. The only deviations from the initial proposal
were stricter resource limits and lifecycle containment required by review.

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-831 | Direct parent; implement Task 5's mandatory stop gate only |
| FR-829 | Preserve read-only public retrieval and same-directory committed-read policy |
| FR-830 | Preserve repository-scoped ledger; composition does not add ledger states |
| FR-832 / FR-833 / FR-834 | Treat outputs as opaque same-run candidates; do not import or alter adapters |
| `tools/cron_run.py` | Extend continue-past-failure execution with validated dependencies and in-memory result reuse |
| `tools/contain.py` | Preserve unchanged; a generated issue still changes only its own feature and ledger |
| `policy/generated-features.md` | Add the sole permitted composition channel; preserve all forbidden behavior |
| Prior `outputs/` files | Explicitly reject as composition input because they may be stale or absent |

## Alternatives Rejected

- **Import sibling feature tools:** creates undeclared coupling and bypasses the
  owning feature's graph contract.
- **Copy all three adapters into the composer:** duplicates source logic and
  invalidates Tasks 2-4 as reusable witnesses.
- **Have the composer re-fetch all sources:** repeats source ownership and turns
  Task 6 back into the failed monolith.
- **Read today's or yesterday's Markdown files:** creates ordering races and
  silently substitutes stale state.
- **Broaden containment to shared directories:** lets one issue mutate code used
  by already approved features.
- **Make cron parse source Markdown:** assigns product semantics to the platform;
  the later deterministic composer owns that judgement.
- **Skip composers when a dependency fails:** prevents explicit partial/all
  failure output, the primary reason composition is needed.

## Scope Fence

FR-835 authorizes a separately governed platform implementation in canonical
GitClaw and an exact reviewed rollout to the Oulu consumer. It authorizes no
GitClaw issue-generated platform edit, Oulu composer, source-adapter edit,
source call, LLM synthesis, cron cadence change, or bulletin publication. Task
6 remains blocked until every acceptance criterion is evidenced.
