---
type: removal
scope: outsider
req: REQ-YG-662
---
- **FR-1004 Retire the outsider ledger**: `docs/census/outsider-ledger.jsonl` — an append-only file every outsider run against a real PR committed one line to, so concurrent PRs conflicted pairwise on merge — is deleted along with its helpers (`ledger_row`, `append_ledger`, `distinct_pr_count`) and `OUTSIDER_LEDGER`. The observation moved into the report's HTML marker as a typed `Observation` (UTC timestamp, repo, PR, full head SHA, full input SHA-256, model, prompt digest, tool SHA, derived verdict, s3/s4 counts; `source:` dropped, `report_path` retired). The wrapper threads the base fields through graph state; the posted PR comment is the only durable record, and only a successfully posted validated report counts. Distinct-PR count: `gh search prs --repo sheikkinen/yamlgraph --match comments 'outsider reader' --json number --jq length`. (REQ-YG-662)
