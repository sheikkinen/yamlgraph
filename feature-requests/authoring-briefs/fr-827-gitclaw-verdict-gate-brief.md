# Task Brief: verdict extraction from artifacts, not session tokens

Governing FR: feature-requests/FR-827-gitclaw-forkable-runner.md.
Defect found in sanity run (issue #1): judge session's final token
said `VERDICT: REJECTED` while its artifact
`features/haiku/judgement.md` says `**Verdict:** APPROVED WITH
REVISIONS`. The gate trusted the token — verdict-inflation at the
instruction boundary. Fix `/Users/sheikki/Documents/src/gitclaw/`
(external repo, write directly, no git commit):

## Change 1: gitclaw.yaml — deterministic verdict gates

Replace the passthrough `judge_gate` with a shell tool node
`read_judge_verdict` that extracts the verdict FROM THE FILE:

```
sed -n 's/^\*\*Verdict:\*\* \([A-Z][A-Z ]*[A-Z]\).*/\1/p' features/{feature_name}/judgement.md | head -1
```

(parse: text, state_key e.g. judge_verdict). Route on equality:
- `'APPROVED'` or `'APPROVED WITH REVISIONS'` → ledger_judged_approved
- `'REJECTED'` → reject_close
- anything else (missing file, unparseable) → END fail-closed with NO
  ledger transition (state stays `planned`, non-terminal, rerun
  resumes).

Note the shell output may carry trailing whitespace/newline — check
how `parse: text` normalizes (reference/graph-yaml.md, tools
section); if it does not strip, add `| tr -d '\n'` to the command.

Similarly replace `review_gate` with `read_review_verdict` reading
`features/{feature_name}/review.md`. The review.md verdict line shape
must be pinned by the review prompt (Change 2): route
- `'APPROVED'`/`'APPROVED WITH REVISIONS'` → ledger_reviewed_approved
- `'REJECTED'` → the existing rejected lanes (first lap → enforce,
  second → reject_final; keep the loop-count conditions)
- else → END fail-closed.

Keep all existing ledger/contain/push tool nodes and loop_limits
intact (adjust gate node names in loop_limits/edges as needed).

## Change 2: prompts — align contracts

- `prompts/judge.yaml`: drop the "final line must be exactly
  VERDICT: ..." stdout requirement; instead require the judgement
  file to begin its verdict line with `**Verdict:** APPROVED`,
  `**Verdict:** APPROVED WITH REVISIONS`, or `**Verdict:** REJECTED`
  (the vendored judgement.template.md already has this shape). State
  explicitly: the file is the verdict; stdout is ignored.
- `prompts/review.yaml`: same change — review.md must contain a line
  starting `**Verdict:**` with one of the three values; stdout
  ignored.
- `prompts/enforce.yaml`: add — if the judgement verdict is APPROVED
  WITH REVISIONS, first fold every required revision into
  `features/{feature_name}/FR.md`, then implement the folded FR.

## Validation

Lint + structure only (no copilot/gh/git side effects). Additionally
verify the sed extraction command works against the REAL artifact
left by the sanity run:

```bash
yamlgraph graph lint /Users/sheikki/Documents/src/gitclaw/gitclaw.yaml
yamlgraph graph info /Users/sheikki/Documents/src/gitclaw/gitclaw.yaml
sed -n 's/^\*\*Verdict:\*\* \([A-Z][A-Z ]*[A-Z]\).*/\1/p' /Users/sheikki/Documents/src/gitclaw/features/haiku/judgement.md
```

The sed check must print `APPROVED WITH REVISIONS`.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
