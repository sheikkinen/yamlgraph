# Reflection: The Smoke Run That Caught What Green Tests Missed

**Date:** 2026-07-28
**FR:** FR-764 — Style-Convert Pipeline (`examples/style_convert/`)
**Trigger:** Enforcing a judged FR. All 30 unit tests were green; the mandated
smoke run (Commandment 2) then failed in two independent ways.

## What happened

The FR was clean, judged APPROVED WITH REVISIONS, folded, and I built the
example TDD-first: RED committed separately (`SKIP=pytest`), then GREEN. Thirty
tests passed. By the letter of the process I could have stopped.

Then I ran the real graph against live Mistral — because "code that has not been
run must not be demoed." It exposed two bugs the entire green suite had missed:

1. **Provider resolved to `deepseek`, not Mistral.** The FR, AC-07, and the
   judgement all said to pin Mistral via `metadata.provider` in the prompt YAML,
   citing `scene_describe.yaml` as precedent. Empirically the executor
   *never reads* `metadata.provider` — `_resolve_provider_and_model` reads a
   top-level `provider` key or the graph node config. The metadata block is
   decorative. The run silently fell through to env `PROVIDER=deepseek`. The
   cited "precedent" was itself relying on an ignored key; nobody had ever
   checked that the pin *did* anything, because the default provider usually
   happened to be fine.

2. **Prompt count doubled: 3 in → 6 saved.** I reused the state key `prompts`
   for both the loader's output and the map node's `collect:` target. The
   ordered append-reducer stacked the 3 converted entries on top of the 3 raw
   loader entries. `save_prompts_node` then serialized all 6 — 3 raw strings and
   3 dicts.

## The traps

**`vendor_default_as_help` / precedent-as-proof.** I trusted a documented
pattern (`metadata.provider`) and a judge who trusted the same pattern, without
ever confirming the mechanism did what its name implied. A metadata key that
looks like configuration but is never read is the config equivalent of dead
code — and it had propagated across examples precisely because no test asserted
the *resolved* provider. The user had to tell me directly: "there is no prompt
provider def. only on graph." One sentence beat my inherited assumption.

**`composition_bug`.** Every unit passed. The loader returned the right list.
The reducer flattened correctly. `save_prompts_node` extracted `prompt_text`
correctly. The defect lived entirely in the *policy connecting correct parts*:
one shared state key across a producer and an append-reducer. My reducer-only
count test even asserted "N in == N out" — but it seeded an *empty* initial
`prompts`, so it could never see the doubling. The test had the shape of the
guarantee without exercising the seam that broke it (`name_the_seam`).

## The cures that worked

- **The smoke run is not ceremony; it is the assertion of last resort.** Both
  bugs were invisible to 30 green tests and visible in the first 10 seconds of a
  real run. `read_raw_output_first`, generalized: for a pipeline, *run the whole
  pipeline and read the file it writes* before believing the units.
- **Assert the resolved fact, not the declared intent.** The fix test now checks
  `convert_styles.node.provider == "mistral"` (where the executor actually reads
  it), not `metadata.provider`. A test that asserts the declaration is worth
  nothing if the declaration is never consulted.
- **End-to-end test that compiles and invokes the real graph** with a mocked
  LLM — it fans out N, collects, saves, and asserts exactly N lines. This is the
  test that would have caught the doubling on the first RED, and it is the one
  the reducer-only test only pretended to be.
- **Record deviations in the FR, not just the code.** D-A (provider on graph
  node) and D-B (`source_prompts` key) both contradict frozen ACs. The FR now
  carries them with rationale, so the next reader sees *why* the shipped shape
  differs from the judged plan.

## Seed

The provider pin propagated as an unread key across at least two examples
(`scene_describe.yaml`, `encounter_summarize.yaml`) because nothing asserts a
node's *resolved* provider. Should the linter grow a check that flags
`metadata.provider` in a prompt YAML as a no-op — and, more generally, warn when
any declared configuration key is never read by the code path that consumes that
file? A config key that looks authoritative but is inert is a lie the same way a
gate that checks shape-not-substance is a lie. Where else in this repo does a
decorative key quietly do nothing?
