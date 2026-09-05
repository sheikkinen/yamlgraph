---
name: judge-fr
description: "Judge a feature request and render a .judgement.md verdict. Use when: asked to judge an FR, review a feature request for approval, act as the independent judge in the plan-judge-enforce pipeline, or produce a judgement artifact. Input closure: FR content + repo doctrine ONLY — never the author's chat narrative."
argument-hint: "path to feature-requests/<ID>-*.md"
---

# Judge a Feature Request (discovery wrapper)

The canonical judge contract lives in the adjacent, non-invocable
`doctrine.md` — that file is the single source of judging doctrine
(NC-412 zero-duplication invariant). This wrapper only tells you where
things are and how humans invoke the adapters.

## To judge an FR

Read `.github/skills/judge-fr/doctrine.md` and apply it to the target
FR. Honor its input closure: FR content + cited evidence + repo
doctrine only — never the author's chat narrative. Write the judgement
per `.github/skills/judge-fr/judgement.template.md`. Output is advisory
until human-reviewed (NC-412 C-6).

## Bundle map

- `doctrine.md` — canonical judge contract (CORE fence = cross-repo
  invariant; Local conventions = per-repo)
- `judgement.template.md` — output skeleton
- `MANIFEST.yaml` — provenance, lineage, distribution model
- `adapters/` — thin invocation surfaces; execution instructions in
  `adapters/README.md`

## Invocation surfaces

**One judge to rule them all:** the YAMLGraph adapter is the ONLY
permitted execution route. Since FR-960 the adapter graph carries two
backend nodes — Copilot CLI (default) and Claude Code
(`JUDGE_BACKEND=claude`) — selected inside the one graph by a
state-conditioned edge; two brains, still one route.

1. **YAMLGraph adapter (SOLE ROUTE)** — invoke via the operator
   wrapper `scripts/judge.sh <fr-path>` (csap NC-415: OS lock +
   lineage sentinel; the wrapper only launches — the graph judges);
   details in `adapters/README.md`. Output is a draft in
   `tmp/draft-judgement-<backend>-<fr-slug>.md`, advisory until
   human-reviewed.

Forbidden routes:

- `/judge-fr` VS Code prompt — FORBIDDEN as an execution route.
- Manual sister-session or subagent judgement — FORBIDDEN.

Rationale: a single executable route keeps the verdict provenance
uniform (same model pin, same prompt path, same artifact location) and
leaves no ambiguity for the Scripture to resolve. If the graph
toolchain is broken, fix the toolchain — do not route around the
judge.
