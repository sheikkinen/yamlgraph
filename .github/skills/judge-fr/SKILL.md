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

- VS Code prompt: `/judge-fr` with a path like
  `feature-requests/NC-412-...md`
- YAMLGraph prototype (manual only, advisory output): see
  `adapters/README.md`
