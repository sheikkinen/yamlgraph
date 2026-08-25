# Feature Request: Research Sole Route — Closed-Input Alternatives Before Authority

**Priority:** HIGH
**Type:** Feature
**Status:** Judged (APPROVED WITH REVISIONS 2026-08-25, R-1..R-6 folded)
**Effort:** 2 days
**Requested:** 2026-08-25
**First consumer / first event:** the next solution-bearing FR — its author
runs `scripts/research.sh <problem-brief.md>` and receives an alternatives
table produced outside the session's loaded context; the Judge withholds
authority without it.

**Prior art:** `examples/demos/innovation_matrix` (capability×constraint
ideation — Scripture names it for exactly this moment,
`capability_constraint_matrix`: "MOMENT: research (Commandment 1)"; never
fired in practice — `builders_never_call` witnessed in the plan phase) and
`examples/demos/web-research` (FR-780 toolbelt; its `search_web` tool is
reused here for the web-grounded persona — operator note 2026-08-25).
`examples/research-agent` is the agent-mode sibling. CAP-113 (chaplain
research step) is the autonomous-lane precedent that died with the daemon —
this is its blocking-graph-run revival, minutes not hours. FR-737/738
(prior-art hook) mechanized the "how did WE solve this before" half; FR-890
adds the missing "what ELSE could solve it" half. FR-888's post-mortem is
the priced failure (tool-space never explored; the winning alternative came
from the operator); FR-889's tool-space table is the exemplar output this
route produces mechanically. Judge/review/author sole routes are the
input-closure precedent being extended to research.

## Summary

A sole research route: `scripts/research.sh <problem-brief.md>` runs a
map+reduce graph — N planner personas with orthogonal priors, each
receiving ONLY the problem brief (never the author's draft solution) —
producing `tmp/draft-alternatives.md`: a dispositioned alternatives table
with precedent citations and planner disagreement preserved. A Judge
doctrine clause kills **any newly created plan** lacking committed
research evidence (R-1: one rule — the earlier "solution-bearing"
narrowing is superseded by the operator amendment).

**Activation boundary (R-1, frozen):** the rule is prospective from the
commit that lands the template field and doctrine clause; it does not
retro-gate already judged or completed FRs; **FR-890 itself is the
bootstrap case, judged under the prior doctrine** — without this clause
the FR would self-invalidate (the template it amends has no Research
field yet).

## Value Statement

The planning phase gets the input closure that judge/review/author already
have: solutions stop being whatever the loaded context resembles (shell in
the diff → shell solutions; hooks in context → hook solutions; yamlgraph
never proposed despite being the house framework).

## Problem

Witnessed 2026-08-25, three ways:

1. FR-888 shipped a 13-AC enumerative grammar without OS permissions ever
   being considered — a first-reach solution class for the problem. The
   operator supplied it as a throwaway. Cost of the unexplored
   alternative: ~3 h, 5 review rounds, 601-line hook
   (`docs/analysis-fr888-post-mortem-2026-08-25.md`).
2. The instrument for this moment exists (`innovation_matrix`) and has
   never been fired at a real FR — the plan-phase `builders_never_call`.
3. Structural cause: plan is the only phase without input closure. The
   planner's context IS the contamination; a fresh context with a closed
   brief samples the solution space differently — the same reason judge
   verdicts are never rendered in the author's session.

## Ideal Result

Before any solution-bearing FR is judged, a one-command research run has
put a table in front of the author: 4–6 solution classes, each with a
verdict, a precedent line ("how the world solves this"), and the
`is_this_a_graph` answer — including at least one candidate the loaded
context would never have produced. The fable planner becomes a selector
over that table instead of a generator of the first idea in context. The
FR-889 tool-space table becomes the norm, produced for pennies instead of
by operator intervention.

## Proposed Solution

### 1. The graph (authored via the sole authoring route)

`examples/demos/research-route/` — map+reduce, pinned cheap model
(haiku-class), FR-884 classifier architecture:

- **Input contract (the closure, R-2 mechanical):** the brief carries
  required headings — `## Problem statement`, `## Classification` (enum
  value from §3), `## Constraints`, `## Witnessed incidents` — and no
  others from the forbidden set: `Proposed Solution`, `Candidates`,
  `Alternatives`, `Design`, or bullet lists naming implementation
  technologies as candidates. The preflight is a **deterministic stdlib
  check in the wrapper** (never an LLM — enforcement infrastructure);
  fixtures witness one rejected contaminated brief and one accepted
  clean brief.
- **Map — 5 personas, orthogonal priors, one judgement each:**
  1. *OS/infra primitivist* — what does the platform/kernel already enforce?
  2. *Data & process planner* — what schema/process change dissolves it?
  3. *YAMLGraph-native planner* — the structurally empty seat; consults
     the graph list (`Task shapes:` clauses) by contract.
  4. *Subtractionist* — delete the requirement; `growth_as_default` check.
  5. *Librarian (web-grounded)* — reuses `search_web` from the
     web-research toolbelt (FR-780): how has the world solved this class;
     names prior art outside the repo.
- **Reduce (code, LLM-free):** alternatives table written to
  `tmp/draft-alternatives.md` with the **frozen schema (R-3)**: columns
  candidate / persona / class / verdict / precedent citation /
  `is_this_a_graph` / effort-risk; 4–6 distinct solution classes; one row
  per persona output unless explicitly marked duplicate; **disagreement
  preserved as rows, never voted away** (ambiguity is information,
  FR-726); no empty required cells; a `Error:`/`No results` string is not
  a citation (R-4 — the librarian fails closed; its row must carry a
  URL-bearing external citation). The wrapper checks presence + schema
  shape; the Judge checks substance — both named, never blurred
  (`gate_checks_shape_not_substance`).

### 2. The wrapper — `scripts/research.sh <problem-brief.md>`

judge.sh lineage: OS lock, sentinel, artifact check, advisory output.
Blocking run, minutes. No daemon (CAP-113's death mode).

### 2b. The persistent artifact + FR template field (operator amendment 2026-08-25)

The research output is not a tmp ephemeral: on acceptance the author
promotes `tmp/draft-alternatives.md` to
**`feature-requests/FR-XXX.research.md`** — a committed sibling of
`.judgement.md`, same lifecycle. `feature-requests/TEMPLATE.md` gains a
mandatory header field:

```
**Research:** [FR-XXX.research.md](FR-XXX.research.md)
```

The reference is the mechanical check surface (prior-art-gate style:
presence checkable by hook, substance checkable by the Judge). An FR may
alternatively reference an equivalent committed record (e.g. FR-889's
in-body tool-space table) — the field must point at SOMETHING committed;
a dangling or absent reference is a gate failure.

**Lifecycle (R-6, frozen):** the FR author promotes
`tmp/draft-alternatives.md` to `feature-requests/FR-XXX.research.md` at
FR filing (or amendment) time, adding a header with brief filename, run
date, and personas executed; dangling links are detected by the Judge
(substance) and may later gain a lint check (not authorized here, C-6).
`.github/skills/feature-request/SKILL.md` is updated to the new
template/lifecycle as a named deliverable (D-6), not a footnote.

### 3. Problem classification (the regex-vs-yamlgraph settlement)

The brief's classification field is a closed enum, applied by the author
and checked by the personas:
- `enforcement/latency-critical` → code (never LLM in the deny path)
- `judgement/analysis/generation` → graph (`is_this_a_graph` = yes)
- `prediction-over-undecidable-input` → **neither: move the boundary**
  (FR-888's missing category — the class where parsing shell was the trap)
- `measurement` → raw-read gate applies (FR-884 doctrine)

### 4. The demand side — Judge doctrine clause (one paragraph)

Extend **`.github/skills/judge-fr/doctrine.md` only** (R-5: the sole
pinned doctrine surface; no judge.sh output-shape change, no new judge
invocation path): **the Judge kills any newly created plan without
research evidence** — an FR whose `**Research:**` field is absent,
dangling, or references a strawman record receives no authority —
verdict REJECTED or returned-to-plan, exactly as the raw-read clause
kills unevidenced measurement FRs; prospective per the R-1 activation
boundary. The Judge checks substance (genuine solution classes,
precedent lines, the `is_this_a_graph` answer); the template field plus
an optional future hook check presence. Doctrine edit = enforcement
infrastructure = **human review recorded before the clause is binding**
(AC-14).

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: `examples/demos/research-route/` is authored through `scripts/author.sh`; `tmp/draft-authoring-report.md` lists the graph/prompt artifacts and records graph lint plus a synthetic-brief smoke; all LLM nodes explicitly pin a cheap model.
- [ ] AC-02: A deterministic problem-brief preflight rejects a fixture brief containing forbidden solution/candidate sections and accepts a fixture containing only problem statement, classification enum value, constraints, and witnessed incidents.
- [ ] AC-03: The route runs five orthogonal personas: OS/infra primitivist, data/process planner, YAMLGraph-native planner, subtractionist, and web-grounded librarian.
- [ ] AC-04: The YAMLGraph-native planner records the `is_this_a_graph` answer and consults available graph `Task shapes:` descriptions; the exemplar or test output names the matching graph shape or says none.
- [ ] AC-05: The librarian row uses the reused `search_web` tool and carries at least one URL-bearing external citation; `Error:`, `No results found`, or empty URL output fails the exemplar.
- [ ] AC-06: The reducer writes `tmp/draft-alternatives.md` with the required columns: candidate, planner/persona, class, verdict, precedent citation, `is_this_a_graph`, effort/risk; the artifact has 4-6 distinct solution classes and no empty required cells.
- [ ] AC-07: Conflicting planner outputs are preserved as separate rows; a fixture with conflicting verdicts does not collapse them by vote or summary.
- [ ] AC-08: `scripts/research.sh <problem-brief.md>` serializes runs, exports a lineage sentinel, invokes only the research graph, and verifies the artifact by schema/shape rather than graph exit code.
- [ ] AC-09: The FR-888 pre-solution problem brief is run through the route; the FR records whether the OS-permissions class surfaced without operator help, with the resulting artifact or summarized table cited.
- [ ] AC-10: `feature-requests/TEMPLATE.md` adds a mandatory `**Research:** [FR-XXX.research.md](FR-XXX.research.md)` field and documents the committed sibling artifact convention plus allowed equivalent committed records.
- [ ] AC-11: `.github/skills/feature-request/SKILL.md` is updated to match the research-reference lifecycle and no longer presents a template that omits first-consumer or research evidence.
- [ ] AC-12: `.github/skills/judge-fr/doctrine.md` gains a prospective research-evidence clause: after FR-890 activation, newly created FRs without a non-dangling committed research reference receive no authority; already judged/completed FRs and this bootstrap FR are not retro-gated.
- [ ] AC-13: A fixture FR lacking `**Research:**` is judged through the sole route and the draft judgement grants no authority with a named missing-research finding; the existing judge output artifact shape remains unchanged.
- [ ] AC-14: Human review of the judge-doctrine edit is recorded before the doctrine change is treated as binding.
- [ ] AC-15: Changelog fragment, FR implementation-status update, and diary reflection are included.

## Out of Scope

- Routing the ideation conversation itself (human-paired by design —
  ruled 2026-08-25).
- Any hook/deny mechanism for planning (plan is not a hazard; the Judge
  clause is the gate, the graph is the supply — FR-886 ordering: supply
  before demand).
- Reviving the chaplain FSM runtime.
- Auto-running research on FR creation (measure adoption first; the
  FR-884 re-census shows whether the Judge clause suffices).

## Alternatives Considered

- **Prompt instruction "consider alternatives"** — instruction text loses
  to loaded context; that is the finding, not a fix (`two_strike_split`).
- **Bigger main-planner context** (feed it the graph list + precedents) —
  adds tokens to the contaminated context instead of escaping it; the
  bias is structural, not informational.
- **Human always supplies alternatives** — the current de-facto process;
  single point of failure, witnessed twice today (chmod, map+reduce).
- **Subagent instead of graph** — `is_this_a_graph` says map/fan-out is
  the native shape; subagents are the fallback, not the default
  (FR-853 graduation).

## Related

- `docs/analysis-fr888-post-mortem-2026-08-25.md` (the priced failure)
- FR-889 (exemplar table), FR-884 (census + classifier architecture),
  FR-737/738 (past-solutions half), FR-780 (search toolbelt reused),
  CAP-113 (dead autonomous precedent)
- Scripture: `capability_constraint_matrix`, `is_this_a_graph`,
  `does_the_platform_already_do_this`, `builders_never_call`,
  `ask_before_generate`
