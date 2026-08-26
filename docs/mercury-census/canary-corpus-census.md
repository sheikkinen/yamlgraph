# Canary precommitment — corpus-census skeleton reuse research (2026-08-26)

Held by initiator, absent from the brief.

- Primary canary: **parametric/template pipeline with dependency
  injection of the corpus adapters** — one shared census graph whose
  discovery and extraction tools are bound at invocation time (the
  operator's sketch; also the textbook software answer: strategy
  pattern / plugin adapters over a frozen skeleton).
- Secondary (not gating): graph generation — a generator that stamps out
  a per-corpus graph from a template (the code-gen alternative to
  runtime injection).
