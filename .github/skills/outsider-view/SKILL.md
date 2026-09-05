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
scripts/outsider.sh <pr-number>            # report under tmp/ only; not an observation
scripts/outsider.sh <pr-number> --comment  # post the report on the PR: the one durable record
scripts/outsider.sh --input <file.md>      # any title+body text; report only
scripts/outsider.sh --selftest             # fixtures must derive NO/NO/NO/YES
```

The first line of the report is the **derived verdict** (computed in code:
≤ 2 "could not understand" items and no hedge in the restatement). Section 2
is the model's own opinion and is labelled non-authoritative.

## Counting distinct PRs (FR-1004)

There is no committed ledger. Each posted report carries a typed HTML marker
(`<!-- outsider reader | ts: … | repo: … | pr: … | head: … | input: … |
model: … | prompt: … | tool: … | verdict: … | s3: … | s4: … -->`). Only a
validated report that was **successfully posted** with `--comment` counts;
`--input`, `--selftest`, non-comment runs and every failure are not
observations. The count is a query (transition-safe: it also matches the
pre-FR-1004 `<!-- outsider reader | source: …` comments):

```bash
gh search prs --repo sheikkinen/yamlgraph --match comments 'outsider reader' --limit 1000 --json number
gh search prs --repo sheikkinen/yamlgraph --match comments 'outsider reader' --limit 1000 --json number --jq length
```

GitHub returns each PR once however many matching comments it has. Do not
write the qualifier inline as `'in:comments "…"'` — gh 2.98 silently drops it
and returns every PR in the repository.

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
