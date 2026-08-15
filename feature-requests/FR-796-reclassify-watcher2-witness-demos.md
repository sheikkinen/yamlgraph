# Feature Request: FR-796 Reclassify watcher2 witness demos out of the examples garden

**Priority:** MEDIUM
**Type:** Enhancement (garden curation)
**Status:** In Progress — implementation complete 2026-08-15; enforcement blocked on AC-10 full-suite integration failures
**Effort:** 0.5–1 day
**Requested:** 2026-08-15

**Prior art:** `examples/2026-07-01-plan-cleanup.md` (Tier 1 + Tier 3 disposition
of these exact directories — never executed for this slice; `purgatory/` and the
archival of `commit-delta-gate`/`session-test` prove the plan was partially
enacted and then stalled); FR-196 (chaplain infrastructure relocated to
`.chaplain/graphs/` — the destination precedent); FR-279/280/281/283/286/287/288/289
(the FRs these demos witness — all Implemented).

## Summary

Ten directories under `examples/demos/` are regression witnesses for
watcher2/CI infrastructure fixes, not demos: nobody runs
`watcher2-red-verification` to learn YAMLGraph. They satisfied the demo-gate's
shape (a runnable graph + demo-output.log) while violating the garden's
substance (teach a concept or exemplify a production pattern). Execute the
already-written disposition: delete three one-shot witnesses, relocate seven
watcher2 regression proofs to `.chaplain/demos/`, and update every index and
discovery surface that references them.

## Ideal Result

`examples/demos/` contains only demos a newcomer or integrator would
deliberately run; infrastructure regression witnesses live with the
infrastructure they witness (`.chaplain/`); no index, MCP tool list, or
taxonomy file references a path that no longer exists.

## Value Statement

**First consumer / first event:** the next newcomer scanning
[examples/README.md](../examples/README.md) — first event is the next
`garden` survey or learning-path walk that no longer wades through ten
watcher2 entries to find the 7-step learning path. Secondary consumer: the
MCP tool list, which currently exposes `Watcher2DeduplicationGateDemo` etc.
as Copilot tools nobody will ever invoke — tool-list noise has a per-session
context cost.

## Problem

The demo-gate (FR-206) requires anything under `examples/demos/<name>/` to
prove execution. Side effect: infrastructure fixes whose FRs touched demo
paths had to *become* demos, so eight watcher2 fixes plus two one-time
verification artifacts (`script-retirement`, `security-cve-ignore`) cosplay
as teaching material. This is gate_checks_shape_not_substance in reverse:
the gate forced presence, and presence was mistaken for membership. The
2026-07-01 plan diagnosed this and prescribed the cure; the slice was never
executed (audit_as_ritual risk: a second inventory without action).

## Proposed Solution

Execute the prior plan's disposition for this slice, unchanged where it
still holds:

**Delete** (one-shot witnesses; their FRs are Implemented, their
demo-output.log evidence survives in git history):

- `examples/demos/script-retirement/` — commit-history assertion, no graph
- `examples/demos/security-cve-ignore/` — validates a temporary pip-audit
  workaround, obsolete by design
- `examples/demos/watcher2-red-verification/` — thinnest witness
  (README + graph.yaml), proves a timestamp fix

**Relocate** via `git mv` to `.chaplain/demos/` (regression proofs for the
chaplain/watcher2 runtime, kept runnable beside the code they guard):

- `watcher2-changelog-gen/`, `watcher2-ci-remediation/`,
  `watcher2-deduplication-gate/`, `watcher2-hook-preflight-gate/`,
  `watcher2-merged-branch-collision-guard/`,
  `watcher2-post-merge-inbox-consumption/`, `watcher2-remediation/`

**Update references** (known from grep; enforce must re-enumerate):

- `examples/README.md` — remove the ten rows from the Utility Demos table;
  add one line pointing to `.chaplain/demos/` for infrastructure witnesses
- `examples/demos/README.md` — remove the stale `watcher2-deduplication-gate`
  row (broader index drift is out of scope — separate proposal)
- `examples/dependency-taxonomy.yaml` — update the ten path entries
- MCP server discovery — relocated demos must not be exposed as MCP tools;
  verify the `Watcher2*Demo` and `Security_CVE_Ignore_Demo` tools disappear
  from the tool list
- README run commands inside each relocated demo — path updates
- CAP registry entries citing these demo paths as evidence, if any

**Explicitly NOT in scope** (the rest of the 2026-07-01 plan): Tier 2
merges, Tier 4 quarantines, Tier 5 fixes, and the other Tier 3 candidates
(`enforcer`, `req-cross-check`, `pipeline_audit`, `run-analyzer`,
`system-status`, `forensic-failure-diary`, `hook_classifier`,
`code-analysis`) — those have ongoing utility-demo use and deserve their own
disposition; bundling them here recreates the stalled mega-plan.

## Constraints

- C-1 (R-1): Moving or deleting governed `graph.yaml` and `prompts/*.yaml`
  artifacts must be performed through the graph-authoring route/sentinel —
  doctrine's trigger is the artifact class, explicitly including `mv`. The
  content-preservation goal remains in scope, but it does not bypass the
  route. If the route fails, enforcement stops and fixes the route rather
  than moving graph artifacts manually.
- C-2 (R-2): For relocated demos, `graph.yaml`, `prompts/**`, Python node
  files, scripts, and existing `demo-output.log` files are byte-for-byte
  identical after relocation; README files may change only to update old
  `examples/demos/...` command paths to `.chaplain/demos/...`. Any other
  content change is unauthorized — stop and re-enter planning.
- C-3: Relocated demos must still lint and run from `.chaplain/demos/`
  (witness one representative run, not all seven).
- C-4: Demo-gate interaction: the PR diff deletes/renames files under
  `examples/demos/<name>/`. Verify the gate's behavior on pure
  deletions/renames before pushing; if it blocks, the moved
  demo-output.log files travel in the same diff — do not weaken the gate.
- C-5 (R-3): Deleted demos' governing FRs receive one-line retirement notes
  naming FR-796, the retired path, and the fact that witness evidence
  remains in git history; FR-796 implementation notes record the PR URL
  and, after it exists, the relevant deleting or merge commit identifier.
- C-6: Changelog fragment type `removal` for deletions; the relocation is
  `chore` scope.

## Acceptance Criteria

Frozen by the judgement (AC-01 satisfied by this revision):

- [x] AC-01: FR-796 is amended with R-1 through R-3 before enforcement
      authority is used.
- [x] AC-02: The three delete-target directories are removed from
      `examples/demos/`; their governing FR records contain one-line
      retirement notes naming FR-796, the retired path, and git-history
      witness retention.
- [x] AC-03: The seven watcher2 directories exist under `.chaplain/demos/`;
      `git diff --find-renames` reports them as renames/moves rather than
      unrelated delete/add churn where Git can detect it.
- [x] AC-04: For each relocated watcher2 demo, `graph.yaml`, `prompts/**`,
      node files, scripts, and existing `demo-output.log` files are
      byte-for-byte preserved; README changes are limited to path updates
      for runnable commands.
- [x] AC-05: `yamlgraph graph lint` passes for all seven relocated graphs,
      and one representative relocated demo run succeeds with output
      captured under its new `.chaplain/demos/...` directory.
- [x] AC-06: A tracked-file search for
      `examples/demos/(watcher2-|script-retirement|security-cve-ignore)`
      returns no live references outside record artifacts
      (`feature-requests/**`, `docs/diary/**`, and git history); indexes,
      taxonomy, relocated READMEs, tests, and CAP registry files are
      updated or confirmed clean.
- [x] AC-07: MCP graph/tool discovery no longer lists the deleted or
      relocated demos, including `Watcher2DeduplicationGateDemo`,
      `Watcher2HookPreflightGateDemo`,
      `Watcher2MergedBranchCollisionGuardDemo`,
      `Watcher2PostMergeInboxConsumptionDemo`, and
      `Security CVE Ignore Demo`.
- [x] AC-08: `examples/README.md` removes the ten Utility Demo rows and
      adds a concise pointer to `.chaplain/demos/` for infrastructure
      witnesses; `examples/demos/README.md` removes the stale
      `watcher2-deduplication-gate` row.
- [x] AC-09: `examples/dependency-taxonomy.yaml` no longer records deleted
      paths and records relocated watcher2 entrypoints at
      `.chaplain/demos/...` only if that taxonomy intentionally covers
      `.chaplain` witnesses; otherwise the entries are removed with
      rationale in FR-796 implementation notes.
- [ ] AC-10: Full tests pass, and no test file references the retired
      `examples/demos/...` paths.
- [x] AC-11: Changelog fragment(s), diary reflection, and an annotation to
      `examples/2026-07-01-plan-cleanup.md` are included in the
      implementation diff.
- [x] AC-12: FR-796 implementation notes record the PR URL and, after
      available, the deleting or merge commit identifier that preserves
      deleted witness evidence in git history.

## Judgement (2026-08-15)

APPROVED WITH REVISIONS — R-1..R-3 folded above; full verdict in
`FR-796-reclassify-watcher2-witness-demos.judgement.md`. Enforcement gates:

- C-1 (GATE): R-1..R-3 folded before implementation — satisfied by this
  revision.
- C-2 (GATE): any relocation/deletion of `graph.yaml`/`prompts/*.yaml`
  proceeds through the graph-authoring route/sentinel.
- C-3 (GATE): if a relocated graph needs graph/prompt/node-code/behavior
  changes to run from `.chaplain/demos/`, stop — not authorized here.
- C-4 (GATE): do not add `.chaplain/demos/` to `DEFAULT_GRAPH_PATTERNS`;
  disappearance from MCP discovery is the intended outcome.
- C-5 (GATE): do not weaken or bypass demo-gate, hooks, CI, or branch
  protection; gate defects exposed by pure deletes/renames get their own
  FR.
- C-6 (GATE): no other item from the 2026-07-01 cleanup plan under this
  authority.

Not authorized: other cleanup-plan tiers; moving `enforcer`,
`req-cross-check`, `pipeline_audit`, `run-analyzer`, `system-status`,
`forensic-failure-diary`, `hook_classifier`, or `code-analysis`; adding
`.chaplain/demos/*/*.yaml` to discovery; converting witnesses into tests;
moving these demos to `purgatory/`; changing graph semantics, prompts,
node code, or demo behavior.

## Alternatives Considered

1. **Fold witnesses into `tests/`** — loses the runnable-demo property the
   chaplain runtime benefits from; these graphs exercise real watcher2
   paths that unit tests mock.
2. **Move to `purgatory/`** — wrong semantics: purgatory is for examples
   that fail the bar pending fixes; these succeed at a different job in the
   wrong place.
3. **Leave in place, add `category: witness` metadata** — cheaper, but the
   MCP tool noise and index dilution remain; metadata doesn't move the
   context cost.
4. **Execute the whole 2026-07-01 plan** — rejected as scope: the plan
   stalled precisely because it was 45 items in one bite; this FR takes the
   least-contested slice.

## Related

- `examples/2026-07-01-plan-cleanup.md` — the prior plan this executes a slice of
- `feature-requests/FR-206-*` — demo-gate (the shape-forcing mechanism)
- `feature-requests/FR-196-*` — chaplain relocation precedent
- FR-279, FR-280, FR-281, FR-283, FR-286, FR-287, FR-288, FR-289 — witnessed FRs
- Diary seed: gate_checks_shape_not_substance — the gate forced these into
  demo costume; this FR is the substance correction

## Implementation Notes (2026-08-15)

- Routed all governed graph and prompt moves/deletions through `scripts/author.sh tmp/fr-796-authoring-brief.md`; an independent audit records 26/26 non-README byte matches and seven graph-local lint passes.
- Deleted the three one-shot witnesses and relocated seven watcher2 witnesses to `.chaplain/demos/`. Only README runnable paths changed inside retained directories; Git detects all unchanged retained files as renames.
- Removed all ten records from the examples-only dependency taxonomy rather than extending that taxonomy beyond its `examples/` ownership boundary.
- Verified default discovery excludes all nine deleted/relocated graph names. A graph-local run of `.chaplain/demos/watcher2-ci-remediation/graph.yaml --var failure_type=ruff --full` completed successfully and was captured in `.chaplain/demos/watcher2-ci-remediation/fr796-verification.log`.
- The adapter's initial deduplication witness exposed historical rot: it references removed `.chaplain/watcher2.sh`. A post-merge witness also failed its stale README contract. Neither graph was changed; the unchanged CI-remediation witness supplied the required representative run.
- With `.venv` activated, the complete unit suite passes: 5,819 passed, 91 skipped, 1 xfailed. The full suite reaches 6,013 passed but has eight stable integration failures reproduced in isolation: memory-demo mocking, three multi-turn/checkpointer assertions, three subgraph-interrupt assertions, and OpenAI `insufficient_quota`. None references the retired paths, but AC-10 remains open because the frozen criterion requires a fully green suite.
- `scripts/check_demo_proof.sh` passes against the staged pure rename/delete shape without weakening or bypassing the gate.
- PR URL: none; the operator requested a direct push to `main`. Deleting commit: `bdf3ad3c` (`chore(examples): FR-796 relocate watcher2 witnesses`).
