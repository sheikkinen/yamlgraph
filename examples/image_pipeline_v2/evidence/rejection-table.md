# Rejection table (sanitized — no prompt text; FR-879 R-5)

| ordinal | prompt_sha | register | nll_per_char | band | boundary_reason | verdict | selected |
|---|---|---|---|---|---|---|---|
| 1 | cc651f0a7bc0 | <prose> | 1.18 | in_band | ok | pass | False |
| 2 | 1ddb56fa08a8 | <prose> | 1.1451 | in_band | ok | pass | True |
| 3 | 3d387c8aad4c | <prose> | 1.2144 | in_band | ok | pass | False |
| 4 | f185ae538f7b | <prose> | 1.1601 | in_band | ok | pass | False |
| 5 | 6f8e1790f664 | <prose> | 1.1962 | in_band | ok | pass | False |
| 6 | 2a40b2bd241b | <prose> | 1.2329 | in_band | ok | pass | False |
| 7 | a4426536a052 | <prose> | 0.971 | in_band | ok | pass | True |
| 8 | f5e786d2300d | <prose> | 1.3839 | in_band | ok | pass | False |
| 9 | d039e8f3d376 | <prose> | 1.2522 | in_band | ok | pass | False |
| 10 | 15b7337b8fca | <prose> | 1.1395 | in_band | ok | pass | True |

## Read notes (enforcer, 2026-08-24 — all 10 candidates read in full locally)

- All 10 in_band, zero rejections: the frontier LLM given a
  corpus-adjacent style brief writes squarely in-distribution — the
  filter's value here is the RANKING (0.971–1.384 spread) and the spend
  cap, not rejection. Off-style briefs are where rejection bites (the
  R-1 fixture: business English 1.876 = too_unlikely).
- #7 (0.971, selected #1): densest corpus-idiom candidate — "throne of
  antlers and roses", "chiaroscuro lighting" — reads closest to the
  gallery register. Rendered image confirmed on-style.
- #8 (1.3839, rank 10): nearly too_unlikely (prose p90 = 1.4345) —
  "procession of plague doctors" is the most narrative, least tag-like
  candidate; the critic ranks exactly along the style axis.
- #4 contains a Cyrillic leak ("алхимic sigils") from the generator;
  the tokenizer skips unknown chars, so it was scored on the Latin
  subset (1.1601, not selected). Documented limit in README.
- All 10 truncated=True: every candidate exceeds the 256-char context;
  the critic judges openings. Honest per-row flag, as frozen in R-2.
