# Canary precommitment — rounds 9–11 (2026-08-26, post-FR-891)

Written BEFORE the runs; absent from all prompts.

- Run 9 (operation class: TRANSFORM — per-item rewriting/distillation):
  canary = whole-book / catalog translation with per-segment QA
  (book_translator + style_convert + ocr_cleanup are in-repo v0s; the
  world's canonical cheap-transform market is localization).
- Run 10 (grounded librarian, commoditization question): canary = named
  commercial crawl-to-LLM-data / embedding-ingestion services with real
  URLs (Firecrawl-class). Gate: zero URL-bearing rows = invalid run —
  now mechanically enforced by the FR-891 fail-closed boundary.
- Run 11 (operation class: GENERATE — per-item synthesis at scale):
  canary = synthetic / weak-supervision training-data generation
  (pseudo-labels surfaced in run 7 as a class; the canonical named
  practice must appear as a candidate, not a fragment).
