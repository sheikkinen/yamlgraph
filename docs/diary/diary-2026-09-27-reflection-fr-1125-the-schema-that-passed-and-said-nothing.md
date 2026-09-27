# Reflection: FR-1125 — the schema that passed and said nothing

**Date:** 2026-09-27
**FR:** FR-1125 (refuse unconstrained objects on Anthropic-bound nodes)

## What happened

Three FRs in one day used the same witness for "this schema is safe":
build the model, hand its JSON schema to the Anthropic SDK's transform,
assert it does not raise. FR-1121 chose `list[dict]` on that witness;
FR-1123 built a gate and a parity test on it and migrated nine prompts
into `list[dict]`; the FR-1121 judge froze `list[dict]` as "the full
schema change authorized". Then the digest ran on 0.6.1, the ranker call
succeeded, and the answer was `{"stories": []}`.

The transform had not lied. It cannot send an object with unknown keys,
because the API refuses `additionalProperties: true`, so it does the one
thing it can: `properties: {}`, `additionalProperties: false`. A grammar
whose only object is `{}`. Every check we had asked "did it raise?" and
none asked "what did it produce?" The spike's raw API call closed the
question in one line: this is the provider's rule, not a library bug,
and no client change can keep `dict` semantics under constrained
decoding.

The correct form had existed since FR-1054: `output_schema` with
declared item properties. It survived the transform intact and returned
three full stories on the first try. Nobody had reached for it because
the `fields` grammar cannot express it and the refusal message we shipped
this afternoon recommended `list[dict]`.

## Trap

`plausible_wrong_answer`, third instance today, now with a sharper
shape: **a boundary oracle that reports acceptance, not fidelity.** A
transform that "does not raise" is a shape check on the input; the
question that mattered was whether the output still carries the
author's intent. The same trap sat one level up in the judge's C-7 and
in my own AC: freezing the wrong cure because the witness was a
raise-or-not.

## Heuristic

For any boundary that transforms a declaration before sending it, the
witness must compare what comes out against what went in, at the
canonical path, and name what was lost. "Accepted" is never the
assertion; "preserved" is. And when a live run contradicts a passing
witness, the spike comes before the FR: one probe with raw outputs
committed answered in fifteen minutes what four judged documents had
assumed.

**Seed:** The `fields` grammar can still write `dict` and `list[dict]`,
and they remain right on providers that accept open objects. Should the
prompt reference stop teaching `list[dict]` as a first choice and lead
with `output_schema` item properties, so the next author's default is
the form every provider can fill? And is there a second transform in the
stack, langchain's OpenAI strict mode, with its own "accepted but
hollowed" class that the same content-parity oracle should be pointed
at?
