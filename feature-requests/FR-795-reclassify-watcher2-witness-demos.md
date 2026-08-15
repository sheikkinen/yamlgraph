# Feature Request: FR-795 Reclassify watcher2 witness demos out of the examples garden

**Priority:** MEDIUM
**Type:** Enhancement (garden curation)
**Status:** Proposed
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

- C-1: Pure relocation/deletion — no graph.yaml or prompt content changes
  (no authoring-route trigger; `git mv` preserves content byte-for-byte).
  If any relocated graph needs a content change to run from its new path,
  stop: that is authoring and takes the `scripts/author.sh` route.
- C-2: Relocated demos must still lint and run from `.chaplain/demos/`
  (witness one representative run, not all seven).
- C-3: Demo-gate interaction: the PR diff deletes/renames files under
  `examples/demos/<name>/`. Verify the gate's behavior on pure
  deletions/renames before pushing; if it blocks, the moved
  demo-output.log files travel in the same diff — do not weaken the gate.
- C-4: No claims removed without their evidence surviving: deleted demos'
  FRs get a one-line note (demo retired, witness in git history at the
  deleting commit SHA).
- C-5: Changelog fragment type `removal` for deletions; the relocation is
  `chore` scope.

## Acceptance Criteria

- [ ] AC-01: The three Tier-1 directories are deleted; their FR files note
      the retirement and the witnessing commit SHA.
- [ ] AC-02: The seven watcher2 directories exist under `.chaplain/demos/`
      with git history preserved (rename detection intact) and no content
      diff.
- [ ] AC-03: `yamlgraph graph lint` passes on all seven relocated graphs;
      one representative demo runs successfully from the new path with
      output captured.
- [ ] AC-04: `grep -r "examples/demos/watcher2\|examples/demos/script-retirement\|examples/demos/security-cve-ignore"`
      over tracked files (excluding git history, diary entries, and FR
      documents, which are records) returns no live references — indexes,
      taxonomy, CAP registry, and demo READMEs all updated.
- [ ] AC-05: MCP tool discovery no longer lists the relocated/deleted demos
      as tools.
- [ ] AC-06: `examples/README.md` Utility Demos table reflects the new
      state; `examples/demos/README.md` stale row removed.
- [ ] AC-07: Full test suite green; no test references the old paths.
- [ ] AC-08: Changelog fragment(s) + diary reflection included; the
      2026-07-01 plan document is annotated with what this FR executed.

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
