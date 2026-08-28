# Feature Request: Research Route Precedent Traceability — Committed-State Grounding Over Brief Echo

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-08-28
**First consumer / first event:** the next FR author who runs
`scripts/research.sh` — their alternatives table arrives with persona
findings grounded in committed repository state instead of their own
brief text, echo rows flagged as echo, and a librarian citation the
reducer has already reconciled against the recorded tool observations.
**Research:** [FR-896.research.md](FR-896.research.md)

## Summary

The FR-890 research route's knowledge boundary is broken in one
direction: personas receive ONLY the author's brief (plus demo graph
one-liners for one persona), so all repository knowledge routes through
the contaminated author context the closure was built to escape, and
"convergence" between personas is partly echo of the brief's framing.
Fix at the boundary, once: every finding's precedent must be traceable
to something that exists independently of the brief — committed
repository state or a tool observation recorded during the run — checked
deterministically in the reducer. Supporting changes: closure-safe
committed context supplied to all personas, a closed class taxonomy
replacing the label-entropy class-count gate, a cell length ceiling, and
a run-provenance stamp.

## Value Statement

FR authors and the Judge get a research signal that means something:
convergence becomes evidence of independent discovery instead of echo
amplification, and a research record becomes mechanically distinguishable
from a fabricated one.

## Problem

Witnessed across FR-893 and the 2026-08-28 self-referential run
(FR-896.research.md, log `tmp/research-echo-run.log`):

1. **Echo counted as signal.** FR-893's brief named corpus_census,
   philosopher, and diary_index in its constraints; three personas
   "converged" on a corpus_census consumer and the judgement counted the
   convergence as substance. In the 2026-08-28 run the os-infra persona
   returned one of the brief's own constraints verbatim as its candidate
   — its precedent cell admits "this is already a committed requirement"
   — and passed every gate. Null information, full compliance.
2. **Citations are shape-checked, never reconciled.** The librarian gate
   accepts any string matching `https?://\S+`. The graph already carries
   `librarian_tool_results` in state; nothing checks the cited URL
   appeared there. FR-893's citation is unverifiable after the fact; the
   2026-08-28 citation was verified only by a manual grep of the run log.
3. **The 4–6 distinct-class gate measures label entropy, not coverage.**
   Classes are self-declared free text. In the 2026-08-28 run four of
   five personas converged on one solution class (deterministic
   reconciliation against committed/recorded state) yet the gate scored
   five "distinct" classes from cosmetic label variation. Conversely an
   honest three-persona convergence under one label fails the run at
   class count 3 — the gate punishes exactly the convergence the
   judgements treat as signal.
4. **No committed grounding.** ARCHITECTURE.md, the CAP registry, the
   changelog, and the diary index are committed, author-independent, and
   closure-safe (they predate any brief) — none reach any persona.
5. **Novel cells.** Three artifacts in a row carry ~2000-character prose
   cells (FR-598's failure mode inside the instrument built after that
   lesson); no length ceiling exists in the schemas.
6. **Persona drift.** In the 2026-08-28 run the librarian — the one seat
   whose job is world precedent — proposed a solution (a "secondary
   contamination gate") and used its URL as decoration; the verdict
   vocabulary is free text ("Plan this.", "PURSUE:", "Deserves planning
   attention"), the verdict-inflation surface FR-727/730 already cured
   elsewhere.
7. **Research records are forgeable.** The provenance header of a
   promoted `.research.md` is self-asserted; nothing ties the committed
   record to an actual `scripts/research.sh` run
   (`artifact_carries_code_identity`, unimplemented at the boundary that
   needed it most).

## Ideal Result

A research run's table is trustworthy at a glance: every row's precedent
cell either names a committed repository artifact that exists, or a URL
the run's own tool log recorded — checked by code before the artifact is
written; rows whose precedent is only the brief's own language are
visibly flagged as echo rather than silently counted as discovery;
convergence of personas under the closed taxonomy reads as signal because
the personas were grounded in the same committed state, not the same
author paragraph; the whole table fits on one screen; and the promoted
record carries a stamp the Judge can match against the run log without
trusting the author.

## Proposed Solution

One boundary rule, enforced in the LLM-free reducer, plus the minimal
supply changes to make it satisfiable (all findings and dispositions in
FR-896.research.md; the four-persona convergent core is this design):

### 1. Precedent traceability check (the core, reducer + preflight)

- Librarian row: cited URL must appear in `librarian_tool_results`
  captured in graph state — reconciliation at the boundary
  (`two_strike_split` cure), fail closed.
- Non-librarian rows: precedent must reference at least one verifiable
  committed identifier — an `FR-\d+` that exists in `feature-requests/`,
  a `CAP-\d+` in `capabilities/`, a repo-relative path that exists, or a
  Scripture trap/cure name — OR be explicitly marked `brief-echo`.
- Echo demotion, never drop (`junk_drawer_cap` lineage): a row whose
  precedent traces only to brief text gets `verdict: echo` set by the
  reducer and is excluded from the class-coverage count, but stays in
  the table as a visible row.
- One librarian predicate: reducer and artifact verifier share a single
  `is_librarian` check (`"librarian" in persona.lower()`) — the current
  `==` vs `in` seam lets a self-labeled "web-librarian" skip the
  fail-closed check in one place and trip it in the other.

### 2. Closure-safe committed grounding (supply)

All five personas additionally receive a deterministic, author-independent
context block assembled by a Python node (no LLM): CAP registry
one-liners (id + name + description, same treatment `collect_graph_shapes`
gives demos), ARCHITECTURE.md section headings, and the Scripture
trap/cure names. Bounded size (~200 lines). The closure invariant is
preserved: everything supplied is committed state that predates the brief.
`collect_graph_shapes` is widened from `examples/demos/*/graph.yaml` to
also cover `graphs/` and `.chaplain/graphs/` — the yamlgraph-native
persona currently answers `is_this_a_graph` against a partial map — and
the brittle hardcoded `map-demo:` canary check is replaced with a count
threshold.

### 3. Class gate replacement

`solution_class` becomes a closed enum (`os-permissions`,
`process-boundary`, `schema-data`, `graph-pipeline`, `subtraction`,
`external-method`, `boundary-enforcement`) validated in Pydantic. The
4–6 distinct-class artifact gate is replaced by: >= 3 distinct classes
among non-echo rows, convergence recorded (rows sharing a class are
annotated `convergent xN`), never failed for converging. `verdict`
becomes a closed enum too (`pursue`, `dissent`, `duplicate`; the reducer
alone may set `echo`) — free-text verdicts are the inflation surface
FR-727/730 already cured at other boundaries; a one-sentence rationale
moves to a separate bounded `rationale` field.

### 3b. Librarian role pin

The librarian prompt and schema are constrained to *reporting* external
precedent: `candidate` describes how the world solves the problem class
(named method/pattern/system), never a proposal for this repo; the
structure prompt instructs rejection-by-schema of solution-shaped
candidates. Prompt-level fix on first strike; if drift recurs, the
abstraction moves to code per `two_strike_split`.

### 4. Cell ceiling

`max_length=400` on every finding field in both the prompt schemas and
`PersonaFinding`; the reducer rejects (not truncates) violations so the
model contract, not post-processing, carries the constraint.

### 5. Run provenance stamp

`scripts/research.sh` appends one JSON line to the **committed**
`feature-requests/research-runs.jsonl` (tmp/ is gitignored — a log the
Judge cannot see from the commit proves nothing): brief SHA-256,
artifact SHA-256, UTC timestamp, graph path. At promotion the record's
header quotes its line; the Judge reconciles header against log by hash
equality instead of trusting prose (`artifact_carries_code_identity`).
The brief hash is recomputable from the committed brief, the artifact
hash from the committed record's table body.

## Acceptance Criteria

- [ ] AC-01: Reducer rejects a librarian row whose URL is absent from
  `librarian_tool_results`; fixture witnesses both directions.
- [ ] AC-02: A non-librarian row whose precedent names a nonexistent
  FR/CAP/path is demoted to `brief-echo`; a row citing an existing
  committed identifier passes; fixtures witness both.
- [ ] AC-03: Echo rows remain in the artifact, visibly flagged, and do
  not count toward class coverage (demote-never-drop).
- [ ] AC-04: All five personas receive the committed-context block; the
  assembling node is Python, deterministic, and its output is bounded;
  a test witnesses CAP one-liners and Scripture trap names present in
  persona input; `collect_graph_shapes` covers `graphs/` and
  `.chaplain/graphs/` in addition to demos.
- [ ] AC-05: `solution_class` and `verdict` are closed enums; free-text
  values fail Pydantic validation; only the reducer can set
  `verdict: echo`; convergent rows are annotated, and a fixture with
  three same-class non-echo rows passes the artifact gate.
- [ ] AC-06: Every finding field carries `max_length=400`; an over-length
  fixture is rejected by the reducer with a named violation.
- [ ] AC-07: `scripts/research.sh` appends the provenance line to the
  committed `feature-requests/research-runs.jsonl`; a deterministic check
  distinguishes a promoted record whose header hashes match the log and
  recompute from the committed brief/table from one whose header is
  unbacked; fixtures witness both.
- [ ] AC-07b: Reducer and artifact verifier use one shared librarian
  predicate; a `web-librarian`-labeled fixture row is treated identically
  by both.
- [ ] AC-07c: The librarian schema/prompt pin the role to external
  precedent reporting; the 2026-08-28 solution-shaped librarian output,
  replayed as a fixture, is rejected or re-shaped; recurrence of drift is
  named a `two_strike_split` trigger in the FR.
- [ ] AC-08: The self-referential brief
  (`research-briefs/research-route-grounding-echo.md`) re-run through the
  upgraded route yields an artifact where the os-infra-style verbatim
  echo row is flagged `brief-echo` and the four-way convergence is
  annotated as convergent, not scored as five classes; result cited in
  the implementation record.
- [ ] AC-09: `scripts/research_preflight.py --verify-artifact` updated to
  the new gate semantics; existing FR-890 fixtures updated, none deleted
  without replacement witnesses.
- [ ] AC-10: Changelog fragment, FR status update, diary reflection.

## Out of Scope

- Fuzzy/semantic echo detection (token-overlap scoring against brief
  text) — the deterministic committed-identifier check is the boundary;
  semantic echo remains Judge substance territory.
- Multi-citation librarian expansion beyond reconciliation (separate
  proposal if the one-URL ceiling proves limiting after grounding lands).
- Any judge-doctrine edit — FR-890's clause already demands substance;
  this FR upgrades what substance is mechanically checkable.
- Persona seat changes (security/cost personas) — measure after
  grounding.

## Alternatives Considered

Dispositioned in [FR-896.research.md](FR-896.research.md): brief-schema
restructuring with FR-keyed repository injection (data-process persona —
folded into §2 in reduced form); replacing the fan-out with
guard-pattern preflight (yamlgraph-native — the guard elements adopted
into §1/§3/§4, the orchestration change rejected as scope creep);
deleting the convergence/class gates outright (subtractionist — adopted
for the class-count gate, rejected for removing coverage signal
entirely); post-hoc contamination-flagging gate (librarian — subsumed by
§1's echo demotion, which flags at write time rather than after).

## Related

- FR-890 (the route; this FR fixes its knowledge boundary)
- FR-893 (echo witnessed), FR-598 (kill the novel), FR-727/730
  (verdict/label inflation cured at the boundary)
- Scripture: `the_one_law`, `two_strike_split`, `junk_drawer_cap`,
  `gate_checks_shape_not_substance`, `artifact_carries_code_identity`
  (seed, partially implemented here)
- `tmp/research-echo-run.log` (the observed run), 2026-08-28 review
  session
