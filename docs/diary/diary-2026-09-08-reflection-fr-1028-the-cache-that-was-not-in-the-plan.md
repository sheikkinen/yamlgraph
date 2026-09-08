# Reflection: the cache that was not in the plan

**Date:** 2026-09-08
**Trigger:** operator, after three live runs of the org AI dossier each
aborted late: "bruteforcing is slow and gathers unneeded info … active repos
can be identified without LLM … gh artifacts have been fetched 3 times
already — cache needed, but no llm."
**Context:** FR-1028 (graph run `--provider/--model` override — merged via
this PR) and FR-1029 (org AI dossier: GitHub + Jira census with onepager —
judged, enforced, shelved the same day; implementation moved to a private
YAMLGraph consumer). One session, one day, thirteen commits, no dossier.

## What happened

The dossier FR was researched, judged (R-1..R-8, twenty acceptance
criteria), enforced RED/GREEN with ~100 witnesses, smoked on a public org,
and run three times against the real one. Each live run aborted on a
boundary defect that only reality exposed:

1. the corpus ceiling fired on the *listing* (590 repos) instead of the
   *active set* (200) it was written for;
2. the Azure test deployment returned 631 HTTP 429s at concurrency 4 and
   15 classifications exhausted their retries — the fail-closed
   `MAX_MAP_FAILED=5` did exactly its job;
3. at concurrency 1 (24 harmless 429s) one Jira finding carried
   `kind: "feature"`, and the reducer treated a model's enum drift as a
   structural failure.

Each was fixed with a witness within minutes. Each retry cost two hours.

## The trap: the cost structure was invisible in the plan

Nothing in the FR, the judgement, or the twenty criteria priced a
*second* run. The judge froze ceilings, canaries, atomic writes, locality
— all correct for a public contrib demo — and never asked "what does
iteration N+1 cost?" The answer was ~1,600 `gh` calls re-fetched from
scratch, because the pipeline had no persisted intermediate between
`extract` and `classify`. The Scripture already names this seed
(`verification_checkpoint_primitive`: checkpoint/resume for long enforce
pipelines); it sat in the seeds list while the run re-paid it three times.

A sibling trap rode along: **the LLM was asked first**. Of the three
questions — which projects are active, which use AI, who carries them —
the first is entirely mechanical and most of the second is too: manifest
hits, instruction files, workflow hits, bot PR authors, code-search hits
are all deterministic and were already in the bundles. The model earns its
keep only on *purpose*, *product-vs-dev-tooling*, and prose. Ordering the
pipeline "everything, then LLM, then reduce" meant the expensive,
rate-limited, drift-prone stage gated the cheap answers behind it. The
operator's re-plan inverts it: fetch → cache → activity (no LLM) →
AI-signals (no LLM) → purpose/structure (LLM on cached READMEs) →
contacts → onepager. Each stage a committed artifact; a failure in stage
3 costs stage 3.

## What the day did get right

- The judge's fail-closed contract is why there is no wrong dossier: three
  aborts, zero success-shaped artifacts. `read_raw_output_first` on the
  smoke output changed code eight times before any aggregate was trusted
  (tool-name drift, README-only evidence, CI bots ranked as persons,
  citation ids echoed into prose).
- FR-1028 exists because the research route was blocked by a dead key
  while Azure credentials sat valid in the same `.env`; the override is
  generic, tiny, and the live witness ran the dossier's own research on
  Azure. It merges alone.
- The private-repo move is the right boundary: the daily-digest /
  hva-bulletin pattern — a YAMLGraph *consumer* whose repo is its state
  store — fits a research tool whose outputs must never enter a public
  repo better than a public demo with a locality audit guarding it.

## Heuristics

- **Price the second run.** Any pipeline with an external fetch stage and
  an LLM stage must persist the fetch result before the first LLM call;
  a plan that cannot state "iteration N+1 costs X" has not planned the
  enforce phase, only the happy path.
- **Mechanical first, model last.** Sort the questions by how much of each
  is decidable without a model; ship the mechanical layers as their own
  artifacts before the model sees anything. The model stage then reads a
  cache, and its failures are cheap.
- **Model output is a claim at every field, not just the cited one.** Enum
  drift in a sub-field is the same class as an unsupported evidence path;
  containment (`map_failed`, dropped entry) is the reducer's job, an abort
  is not.
- **ID allocation is a race even for FR numbers.** A parallel session
  merged an unrelated FR-1027 to main during this arc; the dossier became
  FR-1029 at PR time. `git fetch` + grep across `origin/*` before every
  allocating commit — not just for CAP/REQ.

**Seed:** should `type: map` over an external-fetch tool get a
first-class `cache:` key (content-addressed by an operator-named
invalidation field such as `pushed_at`), so that "the second run is cheap"
is a YAML declaration rather than a discipline every consumer rediscovers
after its third two-hour retry?
