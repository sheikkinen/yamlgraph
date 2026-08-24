# Diary: we installed twenty gates and a human found the fire

**Date:** 2026-08-24
**Produced by:** Claude Opus 5 (Copilot CLI session).

## The morning

Two things happened in `deviant-daily` overnight. The ramp installed
twenty governance assets (FR-867, Tier 3). And a stale-tree commit
silently reverted every source fix from 2026-08-23, after which the
publisher ran all night on the previous morning's code.

The second was found by the operator reading a log line.

## What the machinery actually is

Install verified against `docs/ramp-manifest.md` — 20 assets, every row
hash-matched, rollback documented:

| Asset | State |
|---|---|
| `.pre-commit-config.yaml`, 12 hooks | **live** — fired on my salvage commit, reformatted 10 files |
| `.git/hooks/pre-commit` | installed |
| Copilot guard set | installed |
| `judge.sh`, `review.sh`, skills, templates | installed |
| `req_coverage.py`, `capabilities/` | installed, **0 entries**, **0 req tags** |
| `AGENTS.md` | the 9-line **stub** |
| `docs/incidents.md` | **absent** |
| `.github/workflows/tests.yml` | **inert stub**, `on: workflow_dispatch` |
| `reviewed_source_sha` | `pending-human-review` |

So the skeleton is in and the process is not yet running. Everything
mechanical landed; everything requiring judgement — the doctrine, the
requirement registry, the incident record — is still a placeholder,
because FR-866's graphs have not been run against this target and their
drafts landed by a human.

## The finding I did not want

Ask the only question that matters: **would any installed gate have
caught the revert?**

The twelve hooks are ruff, ruff-format, whitespace, EOF, check-yaml,
large-files, merge-conflict, check-ast, check-toml, debug-statements,
private-key, forbidden-phrases. Not one runs the test suite. None of
them can see that a file went *backwards*: stale content is
syntactically perfect, formats cleanly, and contains no forbidden
phrase. `ruff-format` would have happily reformatted the reverted file
and waved it through.

The gate that would have caught it is a CI job running the 145 tests on
push — because four test modules fail at **import** against the reverted
code. That is a two-second, unambiguous, machine-readable signal.

That gate shipped as an inert stub.

And it shipped as a stub for a defensible reason. FR-865 R-3 forced the
choice: a generic installer cannot know a target's test command, so
either prove the exact command path with fixtures or ship a stub that
**declares itself inert and is not called a gate**. I chose honesty over
a claim I could not back. Correct in the generic FR. The target-specific
FR-867 was supposed to activate it against this repo's real command —
and that step has not happened.

**We shipped the honest version of the one gate that mattered, and left
it switched off.**

## The one thing that did work, and it is not nothing

Yesterday's entry named `silent_absence_of_enforcement`: a missing gate
emits nothing, and nothing is the shape of success. Today the missing
CI gate is a **committed file that says, in its first line, that it is
inert**. The gap did not close, but it stopped being silent — I found it
by reading a file rather than by suffering an incident.

That is the proposed cure working on its first outing, one rung lower
than intended. Not detection at the boundary; documentation of the
absence *at the site of the absence*. Cheaper than I expected and worth
keeping.

## The second finding: the provider lied about a type again

The 04:06 run failed on its own:

```
1 validation error for PostDescription
paragraphs
  Input should be a valid list [type=list_type,
   input_value='["A figure stands alone ...nt. Be Art. Be Unique."', input_type=str]
```

The vision model returned `paragraphs` as a **JSON-encoded string**
rather than a list. Structured output is not a guarantee; it is a
request. This is `schema` / `provider` boundary — the Scripture's
"provider's type lie" (FR-059), and yamlgraph already carries a cure for
exactly this shape in the race node's JSON content normalization
(CAP-117).

Two defects in one, and the second is worse than the first:

1. **No normalization** at the vision boundary — a JSON-string list is
   not repaired into a list.
2. **The failure mode is red, not skip.** `describe_step` raises inside
   `structured.invoke` *before* `gate_step` can classify it. The gate
   was built to turn a bad description into a recorded `skipped` row;
   a malformed *shape* bypasses that entirely and kills the run. The
   day is lost to a formatting quirk, and the ledger records nothing.

Unrelated to the revert. It will recur.

## What today actually cost

The revert was detected by a human noticing an impossible string in a
log — the `impossible_result` tripwire, which works, but only if someone
is reading. Recovery took minutes because `cbdc81b` was intact and the
condemning tests survived: four import failures proved the regression
before any argument about it.

That is the honest ledger for the day: **twenty assets installed, zero
of them involved in finding the incident.** The tests found it once
asked. Nobody was asking automatically.

## Proposed graduation

```yaml
inert_by_honesty_is_still_inert: "Declining to claim a gate you cannot
  prove is correct — and produces a file that looks like coverage.
  A stub that names its own inertness is strictly better than silence,
  but the gap is identical in effect: on 2026-08-24 the one gate that
  would have caught a total source revert (CI running the suite; four
  modules fail at import) had shipped as an inert stub the previous
  evening, correctly labelled, switched off. Ship the honest stub AND
  record the activation as a blocking obligation on the target-specific
  FR, not as an optional later step."
```

## Seed

The tests detected the revert instantly *when asked*, and nothing asked
them. Every gate we install is a question somebody scheduled. So which
questions in this estate are currently asked only by a human who happens
to be reading — and of those, which would cost the least to schedule?
The candidate list from today is short and unpleasant: does the code
still contain yesterday's fixes; does the deployed SHA match the
reviewed one; did the last run publish anything at all.
