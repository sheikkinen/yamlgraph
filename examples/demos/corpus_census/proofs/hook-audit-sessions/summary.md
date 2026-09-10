# Hook-audit session census — 2026-09-10 (FR-1041)

Run 2 of `corpus_census` over `.github/hooks/logs/audit.jsonl` (gitignored),
sessions with ≥ 20 events since 2026-08-20, judged by `mercury-2` with the
`audit-discover` / `audit-extract` adapters. The raw ledger is **not**
committed: rows carry full session ids and command lines from the private
log. This file is the code-computed aggregate (client tag re-derived by
re-running `audit_extract` on each ledger `item_ref`, no LLM).

| client | label | sessions | mean confidence |
|---|---|---|---|
| copilot-cli | prose-unverified | 45 | 0.96 |
| copilot-cli | prose-verified | 14 | 0.96 |
| copilot-cli | code-with-tests | 2 | 0.97 |
| copilot-cli | git-ops | 1 | 0.95 |
| vscode | prose-verified | 29 | 0.96 |
| vscode | code-with-tests | 12 | 0.97 |
| vscode | prose-unverified | 11 | 0.97 |
| vscode | git-ops | 6 | 0.96 |
| vscode | code-no-tests | 2 | 0.97 |
| vscode | inspect-only | 2 | 0.97 |

Total: 124 sessions; abstained: 0; repaired: 0.

Observations (from reading the ledger, not the brief):

- All 45 `copilot-cli / prose-unverified` rows are judge sessions writing
  `tmp/draft-judgement.md` — the judge route is structurally unverified by
  this rubric (it runs no verifier; the graph adapter validates its output).
- Run 1 labelled 62/124 sessions `inspect-only`; every one was a Copilot-CLI
  child session (tool names `Read/Grep/Glob/Bash/Edit/Write`) the adapter did
  not yet parse. The `client:` tag and the `Bash`/`Edit`/`Write` branches
  were added for run 2 — the label was an adapter blind spot, not a finding.
- `brief.md` reports percentages over its 60-row synthesis window ("55 rows",
  "11 of the 55"); the corpus-level counts are the table above.
