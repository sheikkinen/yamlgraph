# Census Brief

## Summary head (deterministic, code-generated)

- ../../../.github/hooks/logs/audit.jsonl#01d66261… (0.95)
- ../../../.github/hooks/logs/audit.jsonl#02b6cc6d… (0.9)
- ../../../.github/hooks/logs/audit.jsonl#053f0fa4… (0.95)
- ../../../.github/hooks/logs/audit.jsonl#07da1efb… (0.9)
- ../../../.github/hooks/logs/audit.jsonl#0d3a73dd… (0.95)
- ../../../.github/hooks/logs/audit.jsonl#1021c000… (0.98)
- ../../../.github/hooks/logs/audit.jsonl#117f39c2… (0.95)
- ../../../.github/hooks/logs/audit.jsonl#128acb02… (0.95)
- ../../../.github/hooks/logs/audit.jsonl#13cc58f2… (0.9)
- ../../../.github/hooks/logs/audit.jsonl#13d66441… (0.95)

## Findings

- Out of 44 prose sessions, exactly half (22) are verified and half (22) are unverified, representing 50% each. (confidence 0.99) [row:../../../.github/hooks/logs/audit.jsonl#01d66261…, row:../../../.github/hooks/logs/audit.jsonl#02b6cc6d…, row:../../../.github/hooks/logs/audit.jsonl#07da1efb…, row:../../../.github/hooks/logs/audit.jsonl#0d3a73dd…]
- Sessions labeled with judgement 'prose-verified' are the verified prose sessions. (confidence 0.98) [row:../../../.github/hooks/logs/audit.jsonl#01d66261…, row:../../../.github/hooks/logs/audit.jsonl#02b6cc6d…, row:../../../.github/hooks/logs/audit.jsonl#18907440…, row:../../../.github/hooks/logs/audit.jsonl#2164597b…]
- Sessions labeled with judgement 'prose-unverified' are the unverified prose sessions. (confidence 0.98) [row:../../../.github/hooks/logs/audit.jsonl#07da1efb…, row:../../../.github/hooks/logs/audit.jsonl#0d3a73dd…, row:../../../.github/hooks/logs/audit.jsonl#1021c000…, row:../../../.github/hooks/logs/audit.jsonl#128acb02…]
- Non‑prose activities (code‑with‑tests, git‑ops, code‑no‑tests) account for 11 of the 55 total rows, roughly 20% of the corpus. (confidence 0.97) [row:../../../.github/hooks/logs/audit.jsonl#053f0fa4…, row:../../../.github/hooks/logs/audit.jsonl#117f39c2…, row:../../../.github/hooks/logs/audit.jsonl#799c557b…]
- Verified prose entries are spread across the dataset, appearing both early (e.g., row 01d66261) and later (e.g., row 842de4a8). (confidence 0.98) [row:../../../.github/hooks/logs/audit.jsonl#01d66261…, row:../../../.github/hooks/logs/audit.jsonl#842de4a8…]
- Both verified and unverified prose rows have high confidence scores, typically 0.93 or above, indicating reliable classification. (confidence 0.96) [row:../../../.github/hooks/logs/audit.jsonl#01d66261…, row:../../../.github/hooks/logs/audit.jsonl#07da1efb…, row:../../../.github/hooks/logs/audit.jsonl#18907440…, row:../../../.github/hooks/logs/audit.jsonl#1021c000…]

## Run provenance

- model: mercury-2
- prompt_version: synthesize_brief.v1
- rows: 60
- source_jsonl_path: tmp/session-census-ledger.jsonl
