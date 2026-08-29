# Feature Request: Retire the Mastra integration demo (`examples/demos/mastra-integration/`)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS (revisions folded 2026-08-29)
**Effort:** 0.25 days
**Requested:** 2026-08-29
**Depends on:** FR-910 (merged to `main` as `7e7018f1`, PR #492). **Enforcement
is authorized only on a base where FR-910's MCP retirement acceptance criteria
AC-01 and AC-05 are already true; FR-915 must not implement FR-910's
`yamlgraph/`, packaging, reference, or CAP changes** (R-1, C-2).
**First consumer / first event:** every maintainer and CI run from the merge
onward — the first event is this FR's own PR pipeline, which stops carrying a
demo that cannot run, stops shipping a `demo-output.log` that certifies a
capability the repo no longer has, and stops advertising a retired protocol
in `examples/README.md`.
**Research:** in-body dispositioned alternatives table below (FR-889 style),
grounded in the evidence table under Problem — every row verified on the
FR-910-merged base on 2026-08-29 and reproducible by the command shown.
Historical design record `docs/research-mastra.md` is retained untouched.
**`is_this_a_graph`:** No (R-2). This is retirement of an obsolete demo
artifact, not authoring of a replacement graph; no graph or prompt is
created or materially modified. The surviving TypeScript integration is the
existing `examples/demos/typescript-node/` subprocess demo.
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
subject — the YAMLGraph MCP server — was retired by FR-910 (merged as
`7e7018f1`); its client has pointed at a deleted file since 2026-07-18.

## Value Statement

The examples garden stops shipping a demo that cannot execute, and the
`demo-output.log` proof gate stops certifying a capability that no longer
exists.

## Problem

`examples/demos/mastra-integration/` demonstrates a Mastra (TypeScript)
client discovering YAMLGraph graphs as typed MCP tools. FR-910 retired the
MCP server and merged to `main` as `7e7018f1` before this FR's enforcement
began (R-1: FR-915 depends on that result and does not perform it). The
demo's entire subject is gone.

It was already broken before that, independently:

| # | Claim | Reality (verified at HEAD, 2026-08-29) | Command |
|---|---|---|---|
| E-1 | The demo connects to a YAMLGraph MCP server | `mastra-app/src/index.ts:23` resolves `yamlgraph/mcp_server.py` — **deleted 2026-07-18 by FR-717 PR2**. The demo has been broken for six weeks on its own, before FR-910 touched anything | `rg -n 'mcp_server' examples/demos/mastra-integration/mastra-app/src/index.ts` |
| E-2 | The demo is maintained | Last commit touching the directory is `ad1b229e` (2026-04-28), and that was an unrelated `chore: vertex in pyproject` sweep — four months with no substantive change | `git log -1 --format='%ci %h %s' -- examples/demos/mastra-integration/` |
| E-3 | `demo-output.log` proves the demo runs | The committed proof was produced on a machine path (`/Users/sami.j.p.heikkinen/src/yamlgraph`) that is not the current checkout, and predates both breakages. The demo gate (CAP-79) checks the artifact's presence, not its currency — `gate_checks_shape_not_substance` | `head -2 examples/demos/mastra-integration/demo-output.log` |
| E-4 | The capability is live | CAP-136 (Per-Graph Typed MCP Tools), the capability this demo exists to prove, carries `status: retired` / `RETIRED by FR-910` on the enforcement base | `rg -n 'status: retired\|RETIRED by FR-910' capabilities/CAP-136-per-graph-typed-mcp-tools.yaml` |
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

Revised per judgement (R-1 added the dependency gate; R-3 replaced the
underspecified residual-test criterion with an exact one):

- [ ] AC-01: FR-910 dependency gate is satisfied before enforcement: `test ! -e yamlgraph/export/mcp.py` passes, and `rg -n 'status: retired|RETIRED by FR-910' capabilities/CAP-136-per-graph-typed-mcp-tools.yaml` shows both retirement markers. If either check fails, stop; FR-915 may not perform those changes itself
- [ ] AC-02: `git ls-files 'examples/demos/mastra-integration/*'` prints no files
- [ ] AC-03: `rg -ri 'mastra' examples/` returns no matches
- [ ] AC-04: `examples/README.md` has no `mastra-integration` row, and its TypeScript-integration guidance names `demos/typescript-node/`, `graph run --json`, and subprocess request/response without offering MCP as an alternative
- [ ] AC-05: `examples/dependency-taxonomy.yaml` contains no `mastra-integration` path, and `python scripts/example_taxonomy_scan.py` followed by `git diff --exit-code examples/dependency-taxonomy.yaml` proves the taxonomy is idempotent
- [ ] AC-06: `pytest tests/unit/test_fr375_typescript_node_demo_red.py::test_ac09_docs_include_json_mode_and_typescript_demo_guidance -q --no-cov` passes; the test source contains no assertion for the string `mcp`; it still asserts `--json`, `stdout`, and `subprocess` in `reference/cli.md`, and `typescript-node`, `--json`, and `subprocess` in `examples/README.md`
- [ ] AC-07: `./scripts/check_demo_proof.sh` passes, and no `examples/demos/mastra-integration/demo-output.log` remains in the tree
- [ ] AC-08: full unit suite passes; `python scripts/req_coverage.py --strict` and `python scripts/validate_capabilities.py` pass
- [ ] AC-09: a changelog fragment exists under `changelog/unreleased/` with `type: removal` and text naming FR-915
- [ ] AC-10: `git diff --exit-code docs/research-mastra.md` passes
- [ ] AC-11: `git diff --name-only` for this FR contains no paths under `yamlgraph/`, `.vscode/`, `capabilities/`, or `examples/demos/typescript-node/`

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

## Judgement (2026-08-29)

**Verdict:** APPROVED WITH REVISIONS — full judgement:
[FR-915-retire-mastra-integration-demo.judgement.md](FR-915-retire-mastra-integration-demo.judgement.md)

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | FR asserted FR-910's implementation had already landed, but the FR-915 tree was cut from `main` where it had not — the evidence was gathered in the FR-910 worktree | Sequencing gate added to the header, Summary, Problem, E-4 and AC-01: enforce only on a base where FR-910 AC-01/AC-05 hold; never implement FR-910's surfaces here. Satisfied by FR-910 merging as `7e7018f1` before enforcement began |
| R-2 | Missing `is_this_a_graph` research answer | Explicit "No" line added to the header with its reason |
| R-3 | Residual-test AC was underspecified ("no MCP term", "mutation-checked") | Replaced by AC-06 naming the exact pytest command and the exact assertions that must survive |

**Conditions:** C-1–C-5 per judgement — notably C-2 (FR-910 dependency gate;
never implement FR-910 here), C-3 (the stale `demo-output.log` must go with
the code, not outlive it), C-4 (`docs/research-mastra.md` byte-for-byte
untouched), C-5 (`examples/demos/typescript-node/` untouched).

**Scope frozen:** deliverables D-1–D-6 per judgement.

## Implementation Status (2026-08-29)

**Enforced** on branch `feat/fr915-retire-mastra-demo`, cut from `main` at
`7e7018f1` — i.e. **after** FR-910 merged, so the AC-01 dependency gate was
satisfied before any deletion (C-2). RED witness committed first.

- D-1: deleted all 9 tracked files under `examples/demos/mastra-integration/`
  (the judgement's D-1 also lists a `tools.py`; no such file existed —
  `git ls-files` showed README, `demo.sh`, `demo-output.log`, `graph.yaml`,
  `prompts/greet.yaml`, and the four `mastra-app/` files).
- D-2: removed the `mastra-integration` row from `examples/README.md` and
  rewrote the TypeScript guidance to name `demos/typescript-node/`,
  `graph run --json`, and subprocess request/response only.
- D-3: regenerated `examples/dependency-taxonomy.yaml`; idempotency proven.
- D-4: `tests/unit/test_fr375_typescript_node_demo_red.py` no longer asserts
  any `mcp` term; it still asserts `--json`, `stdout`, `subprocess` in
  `reference/cli.md` and `typescript-node`, `--json`, `subprocess` in
  `examples/README.md`.
- D-5: `changelog/unreleased/fr-915-retire-mastra-integration-demo.md`.
- D-6: this section.

### Deviations

1. **AC-03 is satisfied over live surfaces, not literally.**
   `rg -ri 'mastra' examples/` still returns exactly one match:
   `examples/demos/research-route/demo-output.log`, which captured a real
   run whose output happened to name the Mastra tool. That file is a frozen
   CAP-79 proof artifact belonging to **another** demo. Editing it to make a
   grep pass would falsify evidence, and deleting it would breach the
   judgement's "do not delete any other demo". The defect class — live
   advertising or code for the retired demo — is fully cleared; the residue
   is immutable history. The witness test encodes this exclusion explicitly.
2. **A witness test was added** (`tests/unit/test_fr915_mastra_demo_retirement.py`,
   3 assertions, `REQ-YG-428`). The judgement's D-list names only the FR-375
   test update, so this is an addition, not a substitution: Commandment 7
   requires a condemning test, and the same pattern caught real leftovers in
   FR-909 and FR-910. It touches no surface on the "Not authorized" list.

### Out of scope, flagged

`reference/cli.md` still contains two live MCP recommendations that FR-910's
denylist did not match because they are prose, not server symbols:

- line ~80: *"**Subprocess vs MCP:** … Prefer MCP for long-lived agent/tool
  ecosystems, discovery, and protocol-level interoperability."*
- line ~227: *"Copilot agent mode file constrained to YAMLGraph MCP tools"*
  (skill-export section; `yamlgraph/export/skill_writer.py` still emits
  "Operate through YAMLGraph MCP tools only.")

Both recommend a retired surface. `reference/cli.md` is outside this FR's
frozen deliverables (D-2 covers `examples/README.md` only), so they are left
untouched and flagged. The second belongs to the skill exporter — **FR-912's
surface**. Recommend folding both into FR-912 or FR-914.

**Verification:** full unit suite 6261 passed / 97 skipped / 1 xfailed;
AC-01, AC-02, AC-04, AC-06, AC-07, AC-10, AC-11 pass mechanically; AC-05
idempotency proven; `req_coverage.py --strict`, `validate_capabilities.py`,
and `check_demo_proof.sh` pass.
