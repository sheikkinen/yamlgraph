# FR-981 pre-authority raw read (judgement R-6, AC-01)

Three source/brief pairs, read before authority. Required by the 2026-09-04
judgement R-6 and by `read_raw_output_first`: the ruler is not built until the
rawest artifact has been read.

## Method, and its limits

No graph exists yet, so these briefs were **authored by hand** by reading each
commit's diff *restricted to the subject path*, applying the brief schema
frozen in the FR. They are a test of the schema, not of any model's ability to
fill it. A model-produced brief may be worse; it cannot be better than a
schema that has no room for the fact.

- Subject: `yamlgraph/utils/llm_factory.py` (29 commits under `--follow`,
  inside the 60-commit ceiling).
- Read command per pair:
  `git show <sha> --format="%H%n%ad%n%s%n%b" --date=short -- <path>`
- Selection: three commits chosen for kind-diversity (one fix with a long
  body, one feat, one bundled fix), not sampled at random. A random sample is
  owed at enforcement; this read exists to find schema defects, and it found
  three.

## Pair 1 — 5ee425c2, 2026-07-10

**Brief (hand-authored):**

```yaml
change_kind: fix
what_changed: "google and vertex are excluded from the LLM cache and
  constructed fresh per call; cache lookup/store extracted to _cached_or_create."
why: "FR-712 — loop-affine aiohttp sessions bind to the first event loop, so a
  cached client errored on roughly half of completed calls under the race bridge."
salient_other: "vertex is same-class-inferred, not independently witnessed (F4)."
confidence: high
```

**Retained:** the `_UNCACHED_PROVIDERS` mechanism and its cause — the reason
someone reading this module later must not "optimise" google back into the
cache.

**Dropped:** the entire FR-711 interplay recorded in the commit body — that
the measuring instrument was itself reusing one client across loops, measured
a dead world until it was updated, and that after the fix the fleet latency
arithmetic **inverted** (google collapses to +0.067s while azure carries
+0.628s). A reader asking "why do we believe google is fast" loses the answer
entirely. This is the pattern's substitution hazard in one concrete instance.

## Pair 2 — 88507576, 2026-07-29

**Brief (hand-authored):**

```yaml
change_kind: feat
what_changed: "Adds runpod to ProviderType and a cache fingerprint entry on
  RUNPOD_API_KEY + RUNPOD_ENDPOINT."
why: "FR-766 — runpod provider via an OpenAI-compatible endpoint."
salient_other: "Diff at this path is two list entries; the provider's
  construction lives elsewhere."
confidence: high
```

**Retained:** that runpod exists and what fingerprints its cache key.

**Dropped:** the field finding in the commit body that the endpoint returns
500 on `temperature != 1.0` — an operational trap of the FR-455 class, and the
single most useful sentence in the commit for anyone debugging runpod later.

## Pair 3 — 218ec0ff, 2026-05-24

**Brief (hand-authored):**

```yaml
change_kind: fix
what_changed: "Omits temperature for OpenAI reasoning models via a new
  REASONING_MODEL_PREFIXES = (o1, o3, o4) guard in create_llm."
why: "FR-455 — those models reject the temperature parameter."
salient_other: "Commit also carries FR-456 (structured output JSON fallback),
  which touches other paths."
confidence: high
```

**Retained:** the prefix guard and its reason.

**Dropped:** FR-456 entirely. It is named in the commit subject, and a
path-scoped brief has no honest place to put it.

## What the read changed in the design

Three defects, none of which was visible from the schema on paper:

1. **The commit body is where the expensive knowledge lives, and the schema
   has no room for it.** Pair 1's inverted latency arithmetic and pair 2's
   500-on-temperature finding are both body-only, both operationally
   valuable, and both dropped. `salient_other` capped at 200 characters
   cannot hold them. **Fold:** raise the cap and re-purpose the field for
   the body's non-obvious finding, explicitly prompted for; accept that a
   long body will still lose material and say so in the pattern document.
2. **A path-scoped brief inherits a whole-commit message.** In pair 2 the
   diff at the subject path is two list entries while the commit body
   describes an entire provider integration. A brief that reports the body's
   claims as this path's change is a `plausible_wrong_answer` generator.
   **Fold:** the brief carries `paths_changed_count` from deterministic code,
   and `what_changed` is scoped to the subject path by prompt contract.
3. **`change_kind` is single-valued; commits are not.** Pair 3 carries two
   FRs. **Fold:** `why` accepts multiple references; `change_kind` records
   the kind *of the change at this path*, which is well-defined even when the
   commit is not.

All three folds are in the FR's frozen brief schema. Notably, none of the
three pairs justified `confidence: low` — the abstention shape survives, but
this read produced no evidence about its calibration, and no threshold is
claimed for it.
