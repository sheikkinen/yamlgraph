# Feature Request: Target-Tailoring Graph Suite — Doctrine, RTM, Incidents

**Priority:** HIGH
**Type:** Feature
**Status:** Judged — APPROVED WITH REVISIONS (2026-08-23), R-1…R-6 folded
**Effort:** 0.5 day
**Requested:** 2026-08-23
**Parent:** FR-864 (SPLIT) — child B per R-2
**First consumer / first event:** the operator, immediately after a
Tier-2 install. First event:
`yamlgraph graph run examples/demos/ramp_doctrine/graph.yaml --var target=/Users/sheikki/Documents/src/deviant-daily`
producing `tmp/ramp/doctrine-draft.md` for review.

**Prior art:** **FR-748** (`fr_atlas`) is the direct precedent and is
reused, not duplicated: it already renders *any* project's markdown
corpus via chunked map → merge judgement → count-in == count-out
reconciliation (`examples/demos/fr-atlas/graph.yaml`). `ramp_incidents`
is closest to it and must justify itself against it rather than
re-implement it. **FR-207** is non-overlapping — it contains no LLM
step; its failure was distribution, this FR's territory is derivation.
**FR-865** is non-overlapping by construction: mechanical copying, no
judgement. **FR-863** supplies the incident corpus `ramp_incidents`
reads. No REJECTED prior art occupies this territory.

## Summary

Three graphs that derive target-specific governance artifacts a copier
cannot produce: a tailored doctrine file, a requirement registry from
existing tests, and an incident record repatriated from wherever the
target's failures were actually written down. All three write drafts to
`tmp/ramp/`; none commits.

## Value Statement

The parts of the process that must be *about* the target repo are
written from the target repo, instead of pasted from someone else's and
left unowned.

## Problem

Three artifacts cannot be copied:

1. **Doctrine.** A trap list carrying `NC-141`, `FR-371` and yamlgraph's
   streaming boundaries into a DeviantArt publisher produces a document
   nobody owns and nobody reads. Which traps apply depends on what the
   target actually does.
2. **Requirements.** `deviant-daily` has 145 tests and zero requirement
   statements. Deriving `{req_id, statement, witness_tests}` from test
   behaviour is judgement, repeated per file — the N-items × one-LLM-call
   shape.
3. **Incidents.** The target's four 2026-08-23 failures are documented in
   *this* repo (FR-863, three diary entries). The repo that suffered them
   has no memory of them. Selecting which of 1,238 entries concern a
   given target is a relevance judgement.

## Ideal Result

Point each graph at a target path; read three drafts; land what is true.
Each draft is visibly derived — every trap kept cites the target code
that justifies it, every requirement cites the test it came from, every
incident cites the source FR or diary entry. Nothing plausible-but-
unsourced appears, and where derivation fails the graph says so instead
of padding.

## Proposed Solution

### Shared runtime contract (parent judgement R-2 requires one)

All three graphs: **target inventory in → draft artifact out → human
review before landing.** Concretely —

- input variable `target` (absolute repo path); optional `source` for
  corpus graphs (default: this repo)
- a python node performs deterministic collection (file lists, test
  names, corpus paths); no LLM sees a directory listing it did not get
  from that node
- a **map** node fans out one LLM call per item with a Pydantic schema
- a merge node reconciles and reports **count-in == count-out**
- graphs live in `examples/demos/ramp_<name>/`, prompts in
  `examples/demos/ramp_<name>/prompts/`

**Draft paths are the only destinations (R-1).** No graph, node, tool or
prompt may name a final target artifact path. Exact outputs:

| Graph | Draft artifacts |
|---|---|
| `ramp_doctrine` | `tmp/ramp/doctrine-draft.md`, `tmp/ramp/doctrine-draft.json` |
| `ramp_rtm` | `tmp/ramp/rtm-draft.md`, `tmp/ramp/rtm-draft.json` |
| `ramp_incidents` | `tmp/ramp/incidents-draft.md`, `tmp/ramp/incidents-draft.json` |

Landing a draft as `AGENTS.md`, `capabilities/*.yaml` or
`docs/incidents.md` in a target is **FR-867's** act, performed by a
human, never by these graphs.

### Authoring records (R-2)

One committed task brief and one retained authoring report **per
graph** — not one for the suite:

| Graph | Brief | Report |
|---|---|---|
| `ramp_doctrine` | `feature-requests/authoring-briefs/fr-866-ramp-doctrine-brief.md` | retained from `tmp/draft-authoring-report.md` |
| `ramp_rtm` | `feature-requests/authoring-briefs/fr-866-ramp-rtm-brief.md` | ″ |
| `ramp_incidents` | `feature-requests/authoring-briefs/fr-866-ramp-incidents-brief.md` | ″ |

### `ramp_doctrine`

Inventory: languages, entry points, external effect sites (network/API
writes), existing gates, workflow triggers.

**Maps over all three Scripture families — traps, cures, and questions
(R-3)** — not traps alone. Per item:
`{family: trap|cure|question, id, verdict: applies|not|tailor, reason,
target_evidence}`. The rendered draft carries a section per family, and
the strict-subset assertion applies to each family independently.

Merge → render an `AGENTS.md` **draft** whose lists are strict subsets,
with **witness citations emptied** and a "Local incidents" section left
explicitly blank for `ramp_incidents` to fill.

### `ramp_rtm`

Inventory: test files, test names, source modules. Map per test file →
`{req_id, statement, witness_tests[], confidence}`. Merge → dedupe by
statement similarity → emit registry YAML in the `capabilities/*.yaml`
shape with `status: proposed` on **every** entry, plus a gap list of
tests witnessing nothing. IEC-62304-styled RTM table in the draft.

**Honest-failure behaviour is the contract, not a floor (R-4).** There
is no minimum candidate count. The graph emits what it can defend and
**reports the number**; a low count is a finding about the target, not a
failure of the graph, and must never be padded. Acceptance tests assert
the *reporting*, never a quota.

Deliberately stricter than the successful replicant: csap has 985
`@pytest.mark.req` tags with no registry and no coverage gate, so
nothing detects a requirement losing its last witness.

### `ramp_incidents` — `fr_atlas` reuse decision (R-5)

**Decision, made here rather than deferred: author a separate graph,
reusing `fr_atlas`'s node topology but not its prompts or schema.**

Rationale: `fr_atlas` maps a corpus to an *onboarding narrative* for the
repo that owns it — one audience, one repo, prose output. `ramp_incidents`
filters a corpus by *relevance to a different repo* and emits typed
incident records with `source_ref`s that must resolve. The collection
node, chunked map and count reconciliation are the same shape and are
copied as precedent; the prompts and output schema are not compatible.
If authoring reveals a parameterisation that serves both, that is a
follow-up FR, not a scope expansion here.

Inventory: source-repo FRs and diary entries mentioning the target by
name or path. Map per document → `{date, defect, root_cause, cure,
witness, source_ref}` or `not_an_incident`. Merge → dedupe → render the
draft.

### Tests: committed fixtures, not sibling checkouts (R-6)

**No test, CI job or acceptance criterion may require
`/Users/sheikki/Documents/src/deviant-daily` to exist.** Committed
fixture repos under `tests/fixtures/ramp_target/` provide the inventory
surface for all automated tests. Smoke runs against the real sibling are
**local, operator-run evidence** recorded in this FR — they prove the
graphs work on a real target; they do not gate CI.

## Acceptance Criteria

Superseded by the judgement's revised set (2026-08-23); folded verbatim.

- [x] AC-01: FR-866 is revised to define exact draft paths, per-graph authoring records, doctrine-entry semantics, `ramp_rtm` honest-failure semantics, the `fr_atlas` reuse decision, and fixture-vs-live-smoke boundaries from R-1 through R-6.
- [x] AC-02: Each graph is authored through the governed graph-authoring route with a committed task brief and a uniquely retained report naming artifacts, precedent, validation commands, repairs, and blocked validation if any.
- [x] AC-03: All three graphs pass `yamlgraph graph lint` against their final committed `graph.yaml` files.
- [x] AC-04: Each graph declares Pydantic output schemas for its map and final JSON output; tests validate representative fixture outputs against those schemas.
- [x] AC-05: Draft paths are exactly `tmp/ramp/doctrine-draft.{md,json}`, `tmp/ramp/rtm-draft.{md,json}`, and `tmp/ramp/incidents-draft.{md,json}`; tests assert no graph/tool writes outside `tmp/ramp/`.
- [x] AC-06: Source scans assert no graph, prompt, or tool invokes `git commit`, `git push`, `gh`, or writes into a target repository.
- [x] AC-07: `ramp_doctrine` fixture tests prove every retained doctrine entry is selected from the source doctrine by stable id, no new doctrine ids are invented, and every retained entry has target evidence or an explicit rejection/tailoring reason.
- [x] AC-08: `ramp_doctrine` smoke on `deviant-daily`, when that target is available, emits a strict subset of the source doctrine, contains zero foreign witness citations matching `NC-\d+` or `FR-\d+`, and names at least one target-specific boundary.
- [x] AC-09: `ramp_rtm` fixture tests prove every emitted requirement has `status: proposed`, cites at least one existing test by name, and rejects or flags any cited test name absent from the target inventory.
- [x] AC-10: `ramp_rtm` reports count-in == count-out over test files, lists tests witnessing no requirement, and either emits at least ten cited candidates for the smoke target or an explicit insufficiency finding without padding.
- [x] AC-11: `ramp_incidents` fixture tests prove document classification emits either an incident object with `date`, `defect`, `root_cause`, `cure`, `witness`, and resolvable `source_ref`, or `not_an_incident`.
- [x] AC-12: `ramp_incidents` smoke on `deviant-daily`, when that target is available, emits the four 2026-08-23 failures named by FR-866: vision payload ceiling, DA title cap, degenerate corpus key, and guard-flag hedging.
- [x] AC-13: `ramp_incidents` count-in == count-out covers every scanned FR/diary document, with non-incidents explicitly classified and no silently dropped files.
- [x] AC-14: The FR records the `fr_atlas` reuse decision before authoring; implementation follows that decision or records a judged deviation before changing course.
- [x] AC-15: Before merge tuning for each graph, the FR records at least three raw map-node outputs read end-to-end, each with a concrete surprising detail a generated dump could not supply.
- [x] AC-16: Tests are added before implementation for the graph behavior above, with RED/GREEN evidence recorded in the FR.

## Risks

**Derived requirements read as authoritative.** A plausible-but-wrong
requirement statement is worse than a gap: it gets traced against
forever. Mitigated by `status: proposed` and mandatory test
citation (AC-09).

**Doctrine tailoring becomes doctrine invention.** The graph must only
subset and annotate, never author new traps. AC-07's stable-id selection
and AC-08's strict-subset assertion are the mechanical guards.

**Tier 3 on a 14-test repo may be theatre.** If `ramp_rtm` yields fewer
than 10 defensible requirements, the honest result is to report that and
stop, not to pad. AC-10's floor is a *detector*, not a quota — failing
it is a finding.

**Three graphs is three surfaces.** If they cannot share the runtime
contract above, that is evidence they are not one FR, and this FR should
itself be split.

## Alternatives Considered

- **Subagents or scripts per step.** Rejected: each is an N-items ×
  one-LLM-call fan-out with a merge — the map node's native shape
  (`is_this_a_graph`).
- **One graph with three modes.** Rejected: different corpora, different
  schemas, different reconciliations; a router here would be a costume.
- **Hand-write the three artifacts for `deviant-daily` once.** Cheaper
  today, and it is exactly what has not happened for any repo since
  March.

## Related

- `feature-requests/FR-864-ramp-spike-to-governed.md` (parent, SPLIT) and its judgement
- `examples/demos/fr-atlas/graph.yaml` — corpus map + merge + reconciliation precedent
- `feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md` — the incident corpus
- `.github/skills/graph-authoring/doctrine.md` — the mandatory authoring route

## Implementation Record (2026-08-23)

**RED:** commit `3dae424c` — 22 contract tests
(`tests/unit/test_ramp_tailoring.py`, +1 scrub test added at GREEN =
23), fixture target `tests/fixtures/ramp_target/`, CAP-245
(REQ-YG-614..617), three authoring briefs committed. RED run:
`logs/fr866-red.log` (22 failed).

**Authoring (sole route, AC-02):** each graph authored via
`scripts/author.sh` with committed brief and retained report:

| graph | brief | report | route session |
|---|---|---|---|
| ramp_doctrine | fr-866-ramp-doctrine-brief.md | tmp/fr866-doctrine-authoring-report.md | 2164597b (gpt-5.5) |
| ramp_rtm | fr-866-ramp-rtm-brief.md | tmp/fr866-rtm-authoring-report.md | fa6bd9f2 (gpt-5.5) |
| ramp_incidents | fr-866-ramp-incidents-brief.md | tmp/fr866-incidents-authoring-report.md | 9bc6d595 (gpt-5.5) |

**AC-14 (`fr_atlas` reuse):** decided before authoring, recorded in
each brief: topology only (corpus map + merge + count reconciliation);
prompts and schemas NOT reused — atlas classifies FR lifecycle, these
classify doctrine applicability / requirement candidacy / operational
incidents; the schemas share no fields.

**GREEN:** 23/23 (`logs/fr866-green.log`), ruff clean, all three
graphs lint clean (test-asserted, AC-03).

**Live smokes on `deviant-daily` (target present):**
- ramp_doctrine (`logs/fr866-smoke-doctrine.log`): 55 dispositions,
  33 kept — strict subset per family (trap 17, cure 11, question 5);
  zero `FR-\d+`/`NC-\d+` citations in both draft files (AC-08).
  Defect found and cured mid-smoke: source Scripture witness
  parentheticals leaked into the draft (10 hits). Condemned by
  `test_write_drafts_scrubs_source_citations`, cured at the
  write boundary (`_scrub_citations` in `doctrine_tools.py`) —
  normalize where the draft exits, not downstream.
- ramp_rtm (`logs/fr866-smoke-rtm.log`): 66 proposed candidates from
  the target's test inventory, 16 gap tests listed, zero validation
  errors — ≥10 cited candidates, floor passed without padding (AC-10).
- ramp_incidents (`logs/fr866-smoke-incidents2.log`): 33 corpus docs,
  count reconciled, 8 incidents; all four named 2026-08-23 failures
  present: vision payload ceiling, DA title cap, degenerate corpus
  key, guard-flag hedging (AC-12). First run (`...incidents.log`)
  correctly FAILED at merge: one map branch's JSON truncated mid-value
  and dropped its `path` — the count-reconciliation validator caught
  it and named the missing document. The failure is the validator
  working as designed; rerun passed.

**AC-15 raw map-output reads (before merge tuning):**
1. doctrine/`mock_escape_hatch` → `not`, reason cites absence of E2E
   workflows AND correctly leaves `target_evidence` empty on a
   rejection — the model respected the asymmetric evidence contract
   unprompted.
2. doctrine/`is_this_a_graph` → `not` — SURPRISING and wrong-ish:
   deviant-daily has a root `graph.yaml`, but `collect_inventory`
   doesn't surface root-level yamlgraph artifacts, so the model never
   saw it. Honest finding: the inventory boundary, not the model, sets
   the verdict ceiling. Candidate FR-867 review note.
3. rtm/REQ-XXX-001 (confidence 0.93) — statement bundles FOUR
   behaviors (POST refresh token, mandatory User-Agent, rotated pair
   return, DAApiError on failure) from two witness tests; human review
   in FR-867 should consider splitting.
4. incidents/process-transfers diary → incident with root_cause "the
   repo that had the incidents had no memory of them" — the model
   independently reproduced the FR-864 famine diagnosis from the raw
   diary.

**Deviations:** none from judged scope. One post-route repair to an
ungoverned file (`nodes/doctrine_tools.py` citation scrub) with
condemning test; graph.yaml/prompts untouched after route delivery.
