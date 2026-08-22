# The Spine Is a Claim Store That Re-Observes Everything

**Date:** 2026-08-22
**Arc:** csap VBOT-101-A/B claims spike (merged 2026-08-21) → mirrored plan (`docs/2026-08-21-plan-architecture-claims-pipeline.md`) → reading yamlgraph's own traceability spine through the claims vocabulary.

## The insight

The operator posed the bigger claim: the RTM links CAP/REQ to FRs, tests link
to REQs, and the coverage report links code to tests — is the spine already
the claims pipeline? Edge-by-edge audit says: structurally yes, but the
spine's guarantee is **presence of the chain, not truth of each link**, and
the two systems differ in one load-bearing dimension: evidence cost.

The spine is a claim store whose verification strategy is *total
re-observation per commit*. `stale` cannot exist for gated edges because
every commit re-runs every verifier — invalidation selectors are unnecessary
when re-verification is cheap. The csap claims model (revision-addressed
observations, selectors, stale/refuted distinction) exists for the opposite
regime: evidence too expensive to re-run per commit. The two designs are
duals, not competitors.

## The trap the vocabulary exposed

The spine's weak edges are exactly its expensive-evidence edges, and both
degrade the same way:

- **test → code** (`req_coverage.py --implementation`): coverage-with-contexts
  is too slow for pre-commit, so the edge is advisory — the repo's own
  `detection_without_enforcement` pattern, hiding in its flagship spine.
- **CAP `modules:` bindings**: declared-modality claims nothing reconciles
  against what tagged tests exercise. The spine is monochrome — every REQ
  implicitly claims `tested`; module bindings are `declared, never verified
  implemented`. And 23 CAPs carry `fr: legacy` — provenance claims running
  on faith.

A `@pytest.mark.req` marker is a **citation, not an entailment** — the C4
renderer-invention finding in different clothes; `gate_checks_shape_not_
substance` at the test-relevance layer.

**Heuristic:** when auditing a traceability system, classify each edge by the
cost of re-verifying it. Cheap edges want gates (re-observe every commit);
expensive edges want revision-addressed observations with invalidation
selectors (observe once, void precisely). An advisory report on an expensive
edge is the tell that the wrong strategy was applied — the edge needed
claims-store machinery and got a gate-shaped script that couldn't afford to
run.

**Addendum (same day):** the two-regime heuristic was incomplete — there is a
third: **lower the frequency until re-observation is affordable again.** A
weekly cron re-running full coverage-with-contexts makes selector machinery
unnecessary for yamlgraph's test→code edge; staleness bounded by a week is
acceptable for a drift report. Frequency is a design axis, not a constraint:
per-commit gates (cheap), scheduled total re-observation (expensive but
batchable), selector invalidation (expensive and unbatchable — live calls,
deployments). Also a trigger-surface lesson: csap's per-PR check has no
firing moment in a direct-push repo — the same analysis needs a cron trigger
here. The mold already exists twice (`weekly-recap.yml` FR-821 with
commit-back automation PR; gitclaw `cron.yml` without).

**Addendum 2 (same day) — the existing report vs the planned reporting.**
Running `req_coverage.py --implementation` three times while authoring FR-850
turned the comparison from design speculation into observed fact:

- **Census vs ledger.** The existing report is a census: it re-describes the
  entire population every run — every CAP, every REQ, every one of 6555
  test-req pairs, thousands of lines, identical emphasis on the healthy mass
  and the anomalies. The planned report is a ledger: only the *change* since
  the previous snapshot gets prose; standing anomalies compress to an aging
  table; the healthy mass compresses to totals. Same data, opposite
  allocation of the scarce resource — reader attention. A census has no
  reader after its first run; a ledger has a reader exactly when it is
  non-empty.
- **The report buries its own primary path.** The existing Summary line
  prints only the fallbacks: "2591 resolved via AST fallback, 2861
  unresolvable." The coverage-resolved count — the entire point of
  `--implementation` mode — is printed nowhere; I had to parse section
  headers to learn it was 3339. The report's shape fossilized when the AST
  fallback was the novel part, and nobody re-read it after the primary path
  mattered. A report that doesn't state its main denominator can't be
  wrong — which is the problem.
- **Statelessness hides instrument failure.** The sysmon-poisoned run
  produced a perfectly plausible report (1103/2591/2861) — populated
  sections, credible numbers, `plausible_wrong_answer` at the report level.
  Nothing flagged it because a stateless census has no previous run to
  contradict. The planned drift report would have screamed on the very next
  cycle: coverage-resolved collapsing 3339→1103 week-over-week is not code
  drift, it is the *measuring instrument* breaking — and the diff catches it
  for free. Drift-vs-previous is `changelog_first_diagnostic` applied to the
  measurement itself: the snapshot history verifies the verifier. That is a
  property no amount of polish on a stateless report can buy, and it is why
  FR-850's AC-03b (refuse a first-test-wins-poisoned baseline) exists —
  the one failure the ledger can't catch is a poisoned *first* entry.

**Heuristic:** a recurring report earns its existence by what it *omits* on
a healthy week. If the healthy-week output is indistinguishable from the
sick-week output at a glance, the report is a census, and its real reader
count is zero.

**Coda (same day):** the operator turned the heuristic on its author. The
drift-report FR was itself `growth_as_default` — a new tool filed while the
existing one was still unusable and untrusted. FR-850 re-scoped: polish the
census first (honest denominators, poisoning tripwire, anomaly view), and
let the drift machinery earn its filing from a value-added / issues-learned
table populated by real use. The cheapest kill rung worked exactly as the
questions canon says it should — in conversation, before any code.

**Addendum 3 (same day) — a report is an answer; name the question.** The
operator's third correction completes the arc: *reports should carry the
questions they are supposed to answer.* Test coverage answers "what
percentage, and which modules are undertested?" Requirement coverage
answers "which REQs lack a witness test?" Ask the same of the
`--implementation` census and the silence is the diagnosis: it answers no
named question — it prints everything it knows, which is why nobody reads
it and why its summary could omit its own primary denominator for months
without anyone noticing. The three defects found today are all downstream
of the missing question: no question → no denominator that matters → no
way to notice the number is wrong → no anomaly view, because "anomaly" is
only definable relative to a question.

This is `who_reads_this_when` sharpened one notch: not just *who reads it
and when*, but *what question do they arrive with*. A section that cannot
be titled with its question is inventory, not reporting — the same
inventory/analysis line `research_as_inventory` draws for research output.
And it composes with the census/ledger heuristic: the question determines
what a healthy answer looks like, and only then can the report omit it.

**Heuristic:** design a report by writing its section headers as questions
first; every section that survives must answer its header, and every datum
that answers no header is cut. A report whose questions cannot be written
down is a data dump awaiting deletion.

**Addendum 4 (same day) — the question canon for the spine's reports, and
what today's runs left unanswered.** Applying the header-as-question
heuristic to the actual reports run this morning yields the canon:

*Answered today:*

- What fraction of lines execute under tests? → 94% (gated at 85).
- Which modules are least covered? → boundary code: FSM event sender 45%,
  bench/skill CLI 62/65%, timeout 78%.
- Does every REQ have a witness test? Are there phantom IDs? → 410/410,
  none (gated).
- How are pairs linked to code? → 3339 coverage / 509 AST / 2707 no-link —
  answerable only by parsing section headers by hand (FR-850).

*Unanswered — ranked by how much the answer would change:*

1. **What does "no-link" mean, per test?** The 2707 bucket conflates three
   causes with three different remedies: (a) ran and touched no measured
   source (doc-witness or subprocess-escape), (b) not in the recording run
   at all (integration, slow — deselected this morning), (c) recording
   failure. Probe: only 3173 distinct test ids appear in contexts vs 5957
   that ran — so ~2800 passing tests left no context at all. The causes ARE
   mechanically separable (context-table membership × run manifest), but no
   report separates them. One bucket, three meanings — the split's biggest
   lie of omission.
2. **Which REQs are witnessed ONLY by no-link tests?** The aggregate hides
   the per-REQ projection: a REQ whose entire evidence is doc-witness tests
   is `gate_checks_shape_not_substance` passing the gate daily. Nobody has
   ever seen this list.
3. **Which code belongs to no requirement?** The spine only asks
   REQ→test→code; nobody asks code→REQ. Unclaimed modules are invisible by
   construction — the registry's blind hemisphere.
4. **Are the missed 6% load-bearing?** 609 missed lines have locations but
   no criticality ranking (incident-density would rank them —
   `inventory_by_visibility`).
5. **Can the numbers be trusted?** Instrument health (context sanity, core
   provenance) required manual SQLite inspection today; the report should
   answer it in its header (FR-850 AC-02).
6. **What changed since last run?** Stateless census; the ledger question,
   deferred behind FR-850's AC-07 evidence table — correctly, but it stays
   on the canon.
7. **Does the tagged test actually witness its REQ?** Citation vs
   entailment — the one question no deterministic tool can answer; the only
   candidate for LLM machinery anywhere in this arc, and it stays unfiled
   until the cheaper six above are answered and still insufficient.

The ranking itself is the reflection's yield: the unanswered questions are
ordered by *decreasing mechanical answerability* — 1–3 are joins over data
we already have, 7 needs a judge. The spine's next report should climb this
ladder bottom-up and stop at the first rung whose answer changes no
decision (`would_you_use_this` applied per question).

**Addendum 5 (same day) — the ranking inverted; wickedness is
frame-relative.** The operator took question 7 — the one I ranked hardest —
and called it the *easiest*. He is right, and the error is instructive: I
ranked by mechanical answerability, a script-writer's cost model. In a repo
whose product is LLM orchestration, the cost curve is inverted — a semantic
judgement mapped over batches with a typed schema and a haiku-tier model is
*routine machinery* (map node, Pydantic schema, provider factory, boundary
reconciliation — all shelf parts), while every new deterministic join is
bespoke code. What is wicked for a script is a Tuesday for the product.
This is `does_the_tool_fit_or_merely_exist` running in reverse: instead of
asking whether the tool fits the task, ask whether the task inventory was
ranked by the tools actually on the shelf.

The design (FR-851) also closes the arc with a pleasing recursion:
Addendum 3 said reports must carry their questions — this pipeline makes
the questions the *literal payload*, one file per REQ in a temp folder,
constructed deterministically and judged by LLM. The payload contract
(LLM→graph, no-LLM→script) lands both branches inside one feature: the
constructor is plain Python because question assembly is mechanical; the
judging is a graph because entailment is not. And the raw read paid out a
third time before any code: the resolution class must travel *inside* the
question file, or the model grades every doc-witness REQ as unwitnessed —
the boundary label is input, not decoration.

**Heuristic:** rank open questions against the machinery on the shelf, not
against a generic difficulty scale — in an LLM-orchestration repo, the
semantic question with typed outputs and a map node is often cheaper than
the next deterministic join.

**Seed:** if the witness audit's `no`/`partial` list proves actionable, the
same constructor+map pattern generalizes to every registry in the repo —
CAP descriptions vs module reality, confession penances vs current code,
changelog claims vs shipped behavior. Which registry's hollow entries cost
the most, and would the audit's second instantiation justify extracting the
pattern into a cookbook (`graduation` at two occurrences)?

**Seed:** the FR corpus is a graveyard of delta claims ("after this change, X
holds") frozen at enforcement time. What would it take to extract the
standing-claim residue at merge — each AC becoming an assertion with
selectors — so an FR's truth decays visibly instead of silently? And would
the first mismatch report (REQ-without-meaningful-test,
modules-without-coverage-hit) justify the extraction cost, per
`would_you_use_this`?
