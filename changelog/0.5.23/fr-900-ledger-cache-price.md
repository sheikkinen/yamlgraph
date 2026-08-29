---
type: fix
scope: scripts
req: REQ-YG-626
---
- **FR-900 Ledger cache-price fix + repo×model report**: `load_prices()` read
  the nonexistent `cache_price` key (schema: `cache_read_price`), pricing all
  cache reads at 0 — a ~5× best-bound underestimate ($796 vs $7,500 August
  invoice). Parser fixed, cache-write term added to the best bound, requests
  attributed to workspaces, and `--month --by-repo` prints cost split by
  (repo, model) with totals. Reconciles with the invoice within ~5%. (REQ-YG-626)
