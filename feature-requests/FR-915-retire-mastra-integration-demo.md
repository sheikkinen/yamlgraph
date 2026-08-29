# Feature Request: Retire the Mastra integration demo (`examples/demos/mastra-integration/`)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.25 days
**Requested:** 2026-08-29
**First consumer / first event:** every maintainer and CI run from the merge
onward — the first event is this FR's own PR pipeline, which stops carrying a
demo that cannot run, stops shipping a `demo-output.log` that certifies a
capability the repo no longer has, and stops advertising a retired protocol
in `examples/README.md`.
**Research:** in-body dispositioned alternatives table below (FR-889 style),
grounded in the evidence table under Problem — every row verified in a
worktree at HEAD on 2026-08-29 and reproducible by the command shown.
Historical design record `docs/research-mastra.md` is retained untouched.
**Prior art:** FR-910 (retired the MCP server this demo consumes; flagged this
demo as out of its frozen scope and deferred the disposition — operator
disposition "retire", 2026-08-29); FR-291/CAP-136 (created this demo; CAP
already retired by FR-910); FR-717 PR2 (deleted `yamlgraph/mcp_server.py`, the
exact path this demo's client resolves); FR-375 (`typescript-node` demo, the
surviving TypeScript integration); FR-206/CAP-79 (demo proof gate);
FR-465/FR-466/CAP-163 (CAP retirement mechanism), CAP-169 (retired-CAP format);
concurrent pruning arc FR-909, FR-912 (skill export), FR-913 (`graph bench`),
FR-914 (`discovery.py`).

## Summary

Delete `examples/demos/mastra-integration/` and its advertising rows. Its
subject — the YAMLGraph MCP server — was retired by FR-910; its client has
pointed at a deleted file since 2026-07-18.

## Value Statement

The examples garden stops shipping a demo that cannot execute, and the
`demo-output.log` proof gate stops certifying a capability that no longer
exists.

## Problem

`examples/demos/mastra-integration/` demonstrates a Mastra (TypeScript)
client discovering YAMLGraph graphs as typed MCP tools. FR-910 retired the
MCP server. The demo's entire subject is gone.

It was already broken before that, independently:

| # | Claim | Reality (verified at HEAD, 2026-08-29) | Command |
|---|---|---|---|
| E-1 | The demo connects to a YAMLGraph MCP server | `mastra-app/src/index.ts:23` resolves `yamlgraph/mcp_server.py` — **deleted 2026-07-18 by FR-717 PR2**. The demo has been broken for six weeks on its own, before FR-910 touched anything | `rg -n 'mcp_server' examples/demos/mastra-integration/mastra-app/src/index.ts` |
| E-2 | The demo is maintained | Last commit touching the directory is `ad1b229e` (2026-04-28), and that was an unrelated `chore: vertex in pyproject` sweep — four months with no substantive change | `git log -1 --format='%ci %h %s' -- examples/demos/mastra-integration/` |
| E-3 | `demo-output.log` proves the demo runs | The committed proof was produced on a machine path (`/Users/sami.j.p.heikkinen/src/yamlgraph`) that is not the current checkout, and predates both breakages. The demo gate (CAP-79) checks the artifact's presence, not its currency — `gate_checks_shape_not_substance` | `head -2 examples/demos/mastra-integration/demo-output.log` |
| E-4 | The capability is live | CAP-136 (Per-Graph Typed MCP Tools), the capability this demo exists to prove, carries `status: retired` / `RETIRED by FR-910` | `rg -n 'status: retired' capabilities/CAP-136-per-graph-typed-mcp-tools.yaml` |
| E-5 | Removing it loses TypeScript coverage | `examples/demos/typescript-node/` (FR-375) demonstrates TypeScript integration via `graph run --json` over `child_process.execFile` — the transport that works and is exercised | `ls examples/demos/typescript-node/` |

A demo is an executable claim about the framework. This one claims a
protocol surface the framework no longer has, backed by a proof artifact
that could not be reproduced on any current checkout.

## Ideal Result

`rg -ri mastra examples/` returns nothing; `examples/README.md` advertises
only integrations that run; no `demo-output.log` in the tree certifies a
retired capability; the design record survives in `docs/research-mastra.md`
and git history, so a future MCP client demo is a disposition of this FR
rather than archaeology.

## Proposed Solution

1. **Demo**: delete `examples/demos/mastra-integration/` (9 files: README,
   `demo.sh`, `demo-output.log`, `graph.yaml`, `prompts/greet.yaml`, and the
   `mastra-app/` Node project).
2. **Advertising**: remove the `mastra-integration` row from
   `examples/README.md`, and rewrite the TypeScript-integration guidance
   sentence (`examples/README.md`, "Subprocess vs MCP") so it names only
   `demos/typescript-node/` — MCP is no longer an alternative to choose.
3. **Taxonomy**: regenerate `examples/dependency-taxonomy.yaml` via
   `python scripts/example_taxonomy_scan.py` (drops the row mechanically).
4. **Residual test**: `tests/unit/test_fr375_typescript_node_demo_red.py::test_ac09_docs_include_json_mode_and_typescript_demo_guidance`
   asserts `"mcp" in examples_doc.lower()`. That assertion was already
   narrowed by FR-909; with the last MCP demo gone it must drop the MCP term
   entirely and assert the `typescript-node`/`--json`/subprocess guidance
   only. Same for the `cli.md` half of that test if it still names MCP.
5. **Changelog**: fragment `type: removal`.

**Kept:** `docs/research-mastra.md` (historical research record — the
`docs/` archive is not swept by retirement FRs, per FR-910's "Not
authorized" precedent); `examples/demos/typescript-node/` untouched.

**Boundary:** this FR does NOT delete any other demo, does not touch
`yamlgraph/`, does not retire any CAP (CAP-136 is already retired by
FR-910), and does not modify `docs/research-mastra.md`, the diary, or any
archived record that mentions Mastra.

## Acceptance Criteria

- [ ] AC-01: `git ls-files 'examples/demos/mastra-integration/*'` prints no files
- [ ] AC-02: `rg -ri 'mastra' examples/` returns no matches
- [ ] AC-03: `examples/README.md` has no `mastra-integration` row, and its TypeScript-integration guidance names `demos/typescript-node/` without offering MCP as an alternative
- [ ] AC-04: `examples/dependency-taxonomy.yaml` is regenerated and contains no `mastra-integration` path; `python scripts/example_taxonomy_scan.py` reports no diff on a second run (idempotent)
- [ ] AC-05: `test_fr375_typescript_node_demo_red.py` passes without asserting any MCP term, and still fails if the `typescript-node` guidance is removed from `examples/README.md` (mutation-checked, not just green)
- [ ] AC-06: `./scripts/check_demo_proof.sh` (CAP-79 demo gate) passes, and the CI `demo-gate` does not demand a `demo-output.log` for a deleted demo
- [ ] AC-07: full unit suite passes; `python scripts/req_coverage.py --strict` and `python scripts/validate_capabilities.py` pass
- [ ] AC-08: changelog fragment under `changelog/unreleased/` with `type: removal` naming FR-915
- [ ] AC-09: `docs/research-mastra.md` is unmodified (`git diff --exit-code docs/research-mastra.md`)

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| **Retire (chosen)** | The demo's subject is retired, its client points at a file deleted six weeks ago, and its proof artifact is stale. Cheap, reversible, precedented, and explicitly dispositioned by the operator on 2026-08-29. |
| Rewrite it against the CLI (`graph run --json`) | REFUTED — `examples/demos/typescript-node/` (FR-375) already demonstrates exactly that. Rewriting produces a `false_duplicate`: two demos of one transport, distinguished only by an npm dependency. |
| Keep as a protocol-integration reference with a "server retired" header | REFUTED — a demo that cannot run is a shim with extra steps. `demo_vs_test`: demos exist to prove an abstraction is worth having; this one proves a retired abstraction. |
| Keep and re-point at an external MCP server | REFUTED — `would_you_use_this` has no answer: no named consumer speaks MCP to yamlgraph (FR-910's operator-confirmed evidence), and the demo would then demonstrate Mastra, not YAMLGraph. |
| Fold into FR-910's PR | REFUTED — FR-910's scope is frozen and explicitly excludes this demo. Expanding it inside the PR it constrains is the silent scope creep the freeze exists to prevent. |
| Fold into FR-912/FR-913 | REFUTED — both are already judged with frozen scope in a parallel session; amending a judged FR to absorb an unrelated surface reopens a closed judgement. |

## Related

- Retirement that orphaned it: FR-910 (PR #492), which flagged this demo as out of scope and deferred the disposition
- Origin: FR-291 / CAP-136 (retired by FR-910)
- Breakage origin: FR-717 PR2 (`yamlgraph/mcp_server.py` deleted 2026-07-18)
- Surviving alternative: FR-375 (`examples/demos/typescript-node/`)
- Demo proof gate: FR-206 / CAP-79 — E-3 is a live witness of `gate_checks_shape_not_substance`
- Concurrent pruning arc: FR-909, FR-912, FR-913, FR-914
- Retained record: `docs/research-mastra.md`

## Judgement (pending)

Not yet judged. Route: `scripts/judge.sh feature-requests/FR-915-retire-mastra-integration-demo.md`.
