# Feature Request: Map the skills layer into the development-process overview

**Priority:** LOW
**Type:** Documentation
**Status:** Enforced — 2026-08-28 (D-1..D-3 applied; ACs verified)
**Effort:** 0.25 days
**Requested:** 2026-08-28
**First consumer / first event:** The next agent or human asked "how do
skills, hooks, pre-commit, caps, and copilot-instructions relate?" — the
question was asked verbatim on 2026-08-28 and the answer required manual
cross-referencing of four documents because the canonical overview
(docs/development-process.md) predates the skills-as-contracts
architecture and mentions skills exactly once, incidentally.
**Research:** In-body dispositioned alternatives table — see
[Alternatives Considered](#alternatives-considered). The gap was located
by direct survey (grep + section reads of the five candidate overview
docs), recorded below; no candidate-exploration run needed for a
docs-gap fix. `is_this_a_graph`: No — the deliverable is a deterministic
documentation edit to docs/development-process.md, not a multi-stage LLM
pipeline or graph artifact; graph-authoring is not triggered because no
graph.yaml or prompts/*.yaml artifact is created or materially modified.

## Summary

docs/development-process.md is the repository's relationship overview
(5 mermaid diagrams: big picture, chaplain FSM, traceability spine,
enforcement rings, self-correction loop). It covers copilot-instructions,
hooks, pre-commit, CI, and capabilities — but the `.github/skills/` layer
is absent (1 incidental mention), despite skills now carrying canonical
doctrine (`judge-fr/doctrine.md`, `graph-authoring/doctrine.md`,
`review-pr/doctrine.md` are the sole-route contracts the Scripture cites)
and being mechanically enforced by Ring-1 hooks (FR-767 sole-route guard).
Amend the overview to add the skills (and agents) vertex and its edges.

## Value Statement

Anyone orienting in the repo gets the complete doctrine-surface map from
one document, instead of discovering the skills↔hooks↔Scripture edges by
cross-referencing .github/hooks/README.md, three skill doctrine files,
and copilot-instructions.md.

## Problem

Verified 2026-08-28 (survey of docs/development-process.md,
.github/hooks/README.md, docs/process.md, docs/sheikkinen-process.md,
reference/skills-export.md):

- `grep -c skill docs/development-process.md` → 1 hit (§7 dogfooding
  table, incidental).
- §2 "Doctrine Layer" presents copilot-instructions.md as the doctrine
  location; since the sole-route FRs, three skills carry `doctrine.md`
  files that the Scripture defers to as canonical (judge, authoring,
  review) — doctrine no longer lives in one file.
- §5 Ring 1 lists pre-command-guard and post-edit checks but not the
  FR-767 graph-authoring sole-route guard — the one hook whose policy is
  *defined in a skill*, i.e. the skills↔hooks edge.
- `.github/agents/code-analysis.agent.md` appears in no diagram.
- Skill inventory (verified): 9 skills; graph-authoring, judge-fr,
  review-pr have doctrine.md + adapters/; the other six
  (chaplain-ops, check-langsmith-trace, feature-request, release-version,
  run-code-analysis, session-introspection) are operational knowledge
  without adapter routes.

## Ideal Result

A reader of docs/development-process.md sees the skills layer as a
first-class doctrine surface: present in the §1 big-picture DOCTRINE
subgraph, described in §2 with a table mapping each sole-route skill to
its doctrine, adapter, and enforcing mechanism, and reflected in §5
Ring 1 via the FR-767 guard. No other document needs to change; the
hooks README already carries the hook-side detail.

## Proposed Solution

Three edits to docs/development-process.md, nothing else:

1. **§1 big picture**: add `SK[.github/skills/<br/>doctrine.md + adapters]`
   to the DOCTRINE subgraph (skills constrain the pipeline like the other
   doctrine nodes).
2. **§2 Doctrine Layer**: add a short "Doctrine is federated" paragraph +
   table: skill → doctrine.md? → adapter route → enforcing mechanism
   (graph-authoring → scripts/author.sh → FR-767 PreToolUse sentinel
   guard; judge-fr → scripts/judge.sh → judge.sh lock + artifact contract
   + NC-414 re-entry sentinel; review-pr → scripts/review.sh → same
   pattern; remaining six = operational skills, no adapter). One row for
   `.github/agents/code-analysis.agent.md`.
3. **§5 Ring 1**: add the FR-767 sole-route guard bullet (sentinel armed
   by the adapter; unsentineled writes to governed graph paths denied),
   citing hooks README for detail.

## Acceptance Criteria (revised per judgement, binding)

- [x] AC-01: §1 DOCTRINE subgraph contains a `.github/skills/` node; the
  mermaid fenced block remains syntactically parseable.
- [x] AC-02: §2 contains a skill→doctrine→adapter→enforcement table that
  names `graph-authoring`, `judge-fr`, `review-pr` individually; names
  `chaplain-ops`, `check-langsmith-trace`, `feature-request`,
  `release-version`, `run-code-analysis`, `session-introspection` in one
  operational-skills row; and includes one
  `.github/agents/code-analysis.agent.md` row.
- [x] AC-03: §5 Ring 1 names the FR-767 graph-authoring sole-route guard
  and states sentineled adapter executions are allowed while unsentineled
  writes to governed graph artifacts are denied.
- [x] AC-04: implementation modifies only docs/development-process.md,
  plus required process artifacts in feature-requests/,
  changelog/unreleased/ if the submit path requires it, and docs/diary/;
  no graph YAML, prompt YAML, hook, script, capability, or skill source
  files are modified.
- [x] AC-05: every route/enforcement claim traceable to cited artifacts
  (author.sh + FR-767 sentinel; judge.sh + lock/lineage sentinel +
  artifact contract; review.sh + same pattern); no route attributed to
  the six operational skills.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| New standalone "doctrine surfaces mindmap" doc | REJECTED — development-process.md is the established overview; a second map creates two sources to drift (`who_reads_this_when`: its reader is the same person) |
| Submit to .chaplain/inbox for the FSM | REJECTED — operator present and judging interactively; manual rite is the measured-dominant path for small bounded changes (§3.1 of the very doc being edited) |
| Auto-generate the skills table from the filesystem | REJECTED (scope) — 9 rows, low churn; a generator is `growth_as_default` until the table goes stale twice |
| Also update reference/getting-started.md | REJECTED (scope) — it is a framework-user doc, not a process doc; the process overview is the single intended home |

## Related

- [docs/development-process.md](../docs/development-process.md) — the target
- [.github/hooks/README.md](../.github/hooks/README.md) — hook-side detail (FR-767 guard)
- FR-767 (sole-route mechanical enforcement), FR-853 (skills-as-contracts arc)

**Prior art:** development-process.md itself is the precedent being
amended. reference/skills-export.md concerns *exporting graphs as skill
bundles* (a product feature), not the repo's own skill layer — keyword
overlap only. docs/plan-yamlgraph-skills.md and docs/plan-skills-export.md
are historical planning notes for that export feature, same disposition.

## Judgement (2026-08-28)

**Verdict:** APPROVED with corrections — see
[FR-901-skills-layer-in-process-overview.judgement.md](FR-901-skills-layer-in-process-overview.judgement.md)

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | Graph-dispatch answer inferred, not stated | `is_this_a_graph: No` folded into Research field |
| R-2 | AC-04 self-contradictory ("no other files" vs the target edit) | AC-04 rewritten to enumerate authorized surfaces |
| R-3 | Collapsed row permitted count-only compliance | AC-02 now names all six operational skills |

**Purge list:** none.

**Scope frozen:** D-1..D-4 (three sections of docs/development-process.md
+ process artifacts). Not authorized: skills/agents/hooks/scripts/
capabilities/graph sources, generators, getting-started.md.

### Questions for the human (as options, or 'none')

none
