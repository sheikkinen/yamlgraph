---
name: outsider-view
description: "Read a PR's title and body as someone with no project context and report what was understood, what could not be understood, and what a merge decision would still need. Use when: a feat/fix PR has just been opened, before scripts/review.sh; an author wants to know which parts of a description only make sense to insiders. Advisory. Input closure: PR title + body ONLY — no files, no tools, no doctrine, no chat narrative."
argument-hint: "PR number (or --input <file> for any title+body text)"
---

# Outsider view of a PR description (discovery wrapper)

The canonical contract lives in the adjacent, non-invocable `doctrine.md`.
This wrapper only tells you where things are and how humans invoke them.

## To get an outsider view

```bash
scripts/outsider.sh <pr-number>            # report under tmp/, one ledger row
scripts/outsider.sh <pr-number> --comment  # additionally post the report on the PR
scripts/outsider.sh --input <file.md>      # any title+body text; no ledger row
scripts/outsider.sh --selftest             # fixtures must derive NO/NO/NO/YES
```

The first line of the report is the **derived verdict** (computed in code:
≤ 2 "could not understand" items and no hedge in the restatement). Section 2
is the model's own opinion and is labelled non-authoritative.

## Bundle map

- `doctrine.md` — what the reader is, its inverted input closure, the three
  readers of its output, what it is not
- `adapters/` — graph (copilot node, `gpt-5.6-sol`, no path/tool grants),
  prompt (copied from the spike), typed tool module; execution notes in
  `adapters/README.md`; operator wrapper `scripts/outsider.sh`
- `fixtures/` — the historical canaries and their pre-written expectations
- `docs/spikes/outsider-reader-2026-09-05/` — the spike this skill copies

## Not this skill

Reviewing a PR against its FR (`review-pr`), judging an FR (`judge-fr`),
rewriting descriptions, gating merges, or reading FR bodies (FR-995 scope).
