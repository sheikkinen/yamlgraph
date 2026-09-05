# Outsider Doctrine — the context-free reader (FR-995, CAP-263)

## What it is

A third adversarial reader beside the judge (reads FRs against doctrine) and
the reviewer (reads PRs against FR + judgement with the files open). The
outsider reads a pull request's **title and body only** as someone who has
never seen this project, and reports in four fixed sections: restatement in
its own words; could it decide to merge from the text alone; words and
references it could not understand (≤ 8); what a merge decision would still
need (≤ 10).

Its ignorance is the instrument; doctrine, files and history would blunt it.

## Inverted input closure (hard boundary)

- Input: the PR title and body. Nothing else. Not the diff, not the FR, not
  the repo, not this file.
- The model runs with no file access and no tools (`allow_all_paths` and
  `allow_all_tools` are absent from the adapter; a test asserts it).
- The child process runs from a fresh directory **outside the repository**,
  so the Copilot CLI cannot load `.github/copilot-instructions.md`. A reader
  who can see the rulebook is not an outsider.
- The model is `gpt-5.6-sol`, pinned literally.

## Three readers of the output

1. **Author** ← section 3 (*could not understand*): gloss or remove each
   phrase. Project shorthand is a pointer into a document the reader has not
   opened; it is not content.
2. **Reviewer** ← section 4 (*would still need*): partition each item into
   *exists but unlinked* and *genuinely absent*. Only someone with the files
   can do this; the outsider must not try.
3. **Derived verdict** (first line, computed in code, never asked of the
   model): YES iff section 3 has at most two items **and** the restatement
   contains none of `does not say`, `something called`, `not stated`,
   `cannot tell`. The model's own YES/NO is recorded as opinion; the spike
   showed it says YES on nearly everything. The reader is a nagger — almost
   impossible to please, and the same text can draw five items in one run and
   none in the next. Hence advisory, and one run per PR, never a loop to YES.

## Fail closed

The model's text is a claim. It is parsed into a typed report or rejected:
four headings exactly once and in order, non-empty restatement, YES/NO
opinion line, item caps. A rejected report produces no verdict, no comment,
and no ledger row. The wrapper verifies the artifact by content; the exit
code is never trusted.

## Measurement before any gate

Each validated run against a real PR appends one attributable ledger row
(`docs/census/outsider-ledger.jsonl`). Fixtures, `--input` runs and failures
write none. Twenty **distinct** PRs are required before any blocking gate may
even be proposed — in its own FR.

## What it is not

Not a reviewer, not a rewriter, not a gate, not automated. It does not
comment unless `--comment` is passed, does not read FR bodies, does not
approve, merge, or block. Output is advisory until a human acts on it.
