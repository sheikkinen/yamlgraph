---
type: feat
scope: census
req: REQ-YG-709
---
- **FR-1120 Person-profile census map memo**: `map_memo_split` takes an optional `versions` object for items that are not files (each key's version is the caller's string; no item path is read). The census gains `gh_authored_prs_versions` (`{ref: updatedAt}` over discover's population) and wraps extract + classify in memo split/merge, so a re-run extracts and classifies only new or updated PRs; changing the rubric, labels, model, graph, prompt, tools or adapter re-runs everything. `memo_store` is required. Ledger rows are now written in item order. (REQ-YG-709)
