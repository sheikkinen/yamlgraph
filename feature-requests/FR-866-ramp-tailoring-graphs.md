# Feature Request: Target-Tailoring Graph Suite — Doctrine, RTM, Incidents

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
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
- output: `tmp/ramp/<name>-draft.md` plus `tmp/ramp/<name>-draft.json`
- graphs live in `examples/demos/ramp_<name>/`, prompts in
  `examples/demos/ramp_<name>/prompts/`, authored through the governed
  route (parent C-3), never auto-committing (parent C-7)

### `ramp_doctrine`

Inventory: languages, entry points, external effect sites (network/API
writes), existing gates, workflow triggers. Map over this repo's
Scripture traps/cures/questions → `{id, verdict: applies|not|tailor,
reason, target_evidence}`. Merge → render an `AGENTS.md` draft whose
trap list is a **strict subset**, with **witness citations emptied** and
a "Local incidents" section left explicitly blank for FR-866's sibling
graph to fill.

### `ramp_rtm`

Inventory: test files, test names, source modules. Map per test file →
`{req_id, statement, witness_tests[], confidence}`. Merge → dedupe by
statement similarity → emit registry YAML in the `capabilities/*.yaml`
shape with `status: proposed` on **every** entry, plus a gap list of
tests witnessing nothing. IEC-62304-styled RTM table in the draft.

Deliberately stricter than the successful replicant: csap has 985
`@pytest.mark.req` tags with no registry and no coverage gate, so
nothing detects a requirement losing its last witness.

### `ramp_incidents`

Inventory: source-repo FRs and diary entries mentioning the target by
name or path. Map per document → `{date, defect, root_cause, cure,
witness, source_ref}` or `not_an_incident`. Merge → dedupe → render
`docs/incidents.md`. Must justify itself against `fr_atlas` in the FR
before implementation: if `fr_atlas` can be parameterised to do this,
parameterise it.

## Acceptance Criteria

Exhaustive for this surface alone; no criterion depends on FR-865/867/868.

- [ ] AC-01: all three graphs pass `yamlgraph graph lint`.
- [ ] AC-02: all three were authored through the governed authoring
      route; reports retained in `feature-requests/authoring-briefs/`
      and the enforcement record.
- [ ] AC-03: each graph declares its output schema; a test validates a
      sample output against it.
- [ ] AC-04: draft paths are exactly `tmp/ramp/<name>-draft.{md,json}`;
      a test asserts nothing is written outside `tmp/`.
- [ ] AC-05: zero auto-commit — a source scan asserts no graph or tool
      invokes `git commit`, `git push`, or `gh`.
- [ ] AC-06: `ramp_doctrine` smoke on `deviant-daily` emits a trap list
      that is a strict subset of the source's, contains **zero** foreign
      witness citations (asserted by regex for `NC-\d+`, `FR-\d+`), and
      names ≥ 1 target-specific boundary.
- [ ] AC-07: every trap kept by `ramp_doctrine` carries a
      `target_evidence` field naming a file or symbol in the target.
- [ ] AC-08: `ramp_rtm` smoke on `deviant-daily` emits ≥ 10 candidates,
      each citing ≥ 1 existing test **by name**; a test asserts every
      cited test name exists in the target.
- [ ] AC-09: `ramp_rtm` reports count-in == count-out over test files
      and lists tests witnessing no requirement.
- [ ] AC-10: every `ramp_rtm` entry carries `status: proposed`.
- [ ] AC-11: `ramp_incidents` smoke emits all four 2026-08-23
      `deviant-daily` failures (vision payload ceiling, DA title cap,
      degenerate corpus key, guard-flag hedging) each with root cause,
      cure, and a `source_ref` that resolves.
- [ ] AC-12: `ramp_incidents` count-in == count-out over scanned
      documents, with non-incidents explicitly classified.
- [ ] AC-13: the FR records a **raw-output read** before merge tuning —
      ≥ 3 raw map-node outputs per graph read end-to-end, each with a
      concrete surprising detail (`read_raw_output_first`).
- [ ] AC-14: `ramp_incidents` either reuses `fr_atlas` or the FR states
      in one sentence why it cannot.
- [ ] AC-15: tests added before implementation (RED/GREEN commits).

## Risks

**Derived requirements read as authoritative.** A plausible-but-wrong
requirement statement is worse than a gap: it gets traced against
forever. Mitigated by `status: proposed` (AC-10) and mandatory test
citation (AC-08).

**Doctrine tailoring becomes doctrine invention.** The graph must only
subset and annotate, never author new traps. AC-06's strict-subset
assertion is the mechanical guard.

**Tier 3 on a 14-test repo may be theatre.** If `ramp_rtm` yields fewer
than 10 defensible requirements, the honest result is to report that and
stop, not to pad. AC-08's floor is a *detector*, not a quota — failing
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
