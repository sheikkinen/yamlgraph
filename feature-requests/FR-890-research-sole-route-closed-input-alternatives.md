# Feature Request: Research Sole Route — Closed-Input Alternatives Before Authority

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
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
doctrine clause withholds authority from solution-bearing FRs that lack a
genuine alternatives analysis.

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

- **Input contract (the closure):** a problem brief with mandatory
  fields — problem statement, problem classification (see §3), constraints,
  witnessed incidents — and a mandatory ABSENCE: no draft solution, no
  candidate list. A code preflight rejects briefs containing
  solution-shaped sections (the closure is checkable).
- **Map — 5 personas, orthogonal priors, one judgement each:**
  1. *OS/infra primitivist* — what does the platform/kernel already enforce?
  2. *Data & process planner* — what schema/process change dissolves it?
  3. *YAMLGraph-native planner* — the structurally empty seat; consults
     the graph list (`Task shapes:` clauses) by contract.
  4. *Subtractionist* — delete the requirement; `growth_as_default` check.
  5. *Librarian (web-grounded)* — reuses `search_web` from the
     web-research toolbelt (FR-780): how has the world solved this class;
     names prior art outside the repo.
- **Reduce (code, LLM-free):** alternatives table — candidate, class,
  verdict, precedent citation, effort guess — with **disagreement
  preserved as rows, never voted away** (ambiguity is information,
  FR-726). Written to `tmp/draft-alternatives.md`; verified by artifact,
  never exit code.

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

### 3. Problem classification (the regex-vs-yamlgraph settlement)

The brief's classification field is a closed enum, applied by the author
and checked by the personas:
- `enforcement/latency-critical` → code (never LLM in the deny path)
- `judgement/analysis/generation` → graph (`is_this_a_graph` = yes)
- `prediction-over-undecidable-input` → **neither: move the boundary**
  (FR-888's missing category — the class where parsing shell was the trap)
- `measurement` → raw-read gate applies (FR-884 doctrine)

### 4. The demand side — Judge doctrine clause (one paragraph)

Extend `.github/skills/judge-fr/doctrine.md`: **the Judge kills any plan
without research evidence** (operator decision 2026-08-25 — hardened from
"withhold for solution-bearing FRs"): an FR whose `**Research:**` field is
absent, dangling, or references a strawman record receives no authority —
verdict REJECTED or returned-to-plan, exactly as the raw-read clause kills
unevidenced measurement FRs. The Judge checks substance (genuine solution
classes, precedent lines, the `is_this_a_graph` answer); the template
field plus an optional hook check presence. Doctrine edit = enforcement
infrastructure = human review gate.

## Acceptance Criteria

- [ ] AC-01: Research graph authored via `scripts/author.sh` (lint clean,
      synthetic-brief smoke, demo-output.log); all LLM nodes pinned
      cheap-model
- [ ] AC-02: Brief preflight rejects solution-contaminated briefs
      (closure is mechanical) — witnessed by a fixture brief containing a
      draft solution
- [ ] AC-03: The librarian persona performs real web search via the
      reused `search_web` tool and its row carries an external citation —
      witnessed in the exemplar run
- [ ] AC-04: Reduce preserves planner disagreement as separate rows;
      no voting/collapse — witnessed by a fixture with conflicting verdicts
- [ ] AC-05: `scripts/research.sh` verifies by artifact
      (`tmp/draft-alternatives.md` non-empty with table markers), never
      exit code
- [ ] AC-06: **Exemplar run:** the FR-888 problem brief (write-guard,
      pre-solution) run through the route; the FR records whether the
      OS-permissions class surfaces without operator help — an honest
      witness either way
- [ ] AC-07: Judge doctrine clause added (human-reviewed per enforcement-
      infrastructure gate); judge.sh output shape unchanged
- [ ] AC-08: `feature-requests/TEMPLATE.md` carries the mandatory
      `**Research:**` file-reference field; the research artifact
      convention (`FR-XXX.research.md`, committed sibling of
      `.judgement.md`) is documented in the template and the
      feature-request skill
- [ ] AC-09: The kill is witnessed: one fixture FR without a Research
      reference is judged via the sole route and receives no authority,
      with the missing-research finding named in the verdict
- [ ] AC-10: Changelog fragment; diary reflection

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
