---
name: review-pr
description: "Review a PR against its governing FR and judgement, rendering a merge verdict. Use when: asked to review a PR, act as the independent reviewer in the plan-judge-enforce-review pipeline, check a PR diff against frozen scope, or document review findings as PR comments. Input closure: GitHub PR head/diff + FR + judgement + repo doctrine ONLY — never the author's chat narrative."
argument-hint: "PR number or branch, plus the governing FR path"
---

# Review a Pull Request (discovery wrapper)

The canonical review contract lives in the adjacent, non-invocable
`doctrine.md` — the single source of review doctrine (NC-413,
mirroring the judge-fr zero-duplication invariant). This wrapper only
tells you where things are and how humans invoke them.

## To review a PR

Read `.github/skills/review-pr/doctrine.md` and apply it to the target
PR. Honor its input closure: GitHub PR head + PR diff + governing
FR + judgement + cited evidence + repo doctrine only — never the
author's chat narrative. Report per
`.github/skills/review-pr/review.template.md`. Output is advisory —
the human merge decision is the gate (NC-413 C-6).

## Bundle map

- `doctrine.md` — canonical review contract (the single source of the
  review rubric and reporting rules)
- `review.template.md` — output skeleton
- `adapters/` — graph + pointer prompt; execution instructions in
  `adapters/README.md`; operator wrapper `scripts/review.sh`

## Invocation surfaces

**One reviewer to rule them all:** the YAMLGraph adapter is the ONLY
permitted execution route.

1. **YAMLGraph adapter (SOLE ROUTE)** — invoke via the operator
   wrapper `scripts/review.sh <pr> <fr-path>` (OS lock +
   REVIEW_EXECUTION lineage sentinel; the wrapper only launches — the
   graph reviews); details in `adapters/README.md`. Output is a draft
   in `tmp/draft-review.md`, advisory until the human merge decision.

Forbidden routes:

- `/review-pr` VS Code prompt — FORBIDDEN and deleted.
- Manual sister-session or subagent review — FORBIDDEN.

Rationale: single-route provenance (same model pin, same prompt path,
same artifact location); if the toolchain breaks, fix it — do not
route around the reviewer.
