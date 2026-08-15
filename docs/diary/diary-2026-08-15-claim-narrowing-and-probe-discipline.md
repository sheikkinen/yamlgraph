# Diary — 2026-08-15: Claim narrowing and probe discipline (market-research session, part 2)

**Session arc:** eval of the sister session's position paper → self-hosting
null-hypothesis probe → Haystack correction → checking FR-802/803 enforcement
results → empirical lint probe of the core "LLM-friendly" claim.

## Trap: feature-name match as competitive evidence

I published a table row claiming Haystack was the "closest artifact-class
competitor" because it "has YAML pipelines." One primary-source fetch
overturned it: Haystack's YAML is round-trip *serialization* of Python objects
(class paths + init-param mirrors, allowlist-gated instantiation), not an
authoring surface. This is `gate_checks_shape_not_substance` operating on
market research: "supports YAML" is a shape check; whether the YAML is an
*authorable, lintable artifact* is the substance. A competitor feature list is
an LLM-output-shaped claim — apply `read_raw_output_first` to it: the raw
artifact is the competitor's own docs/source, and one read beats any number of
recalled comparisons. The correction *strengthened* our position — being too
generous to a competitor is still being wrong.

## Cure applied: probe the claim, don't assert it

"yamlgraph artifacts are LLM-friendly (lint, local execution)" was tested by
injecting four defect classes into a real demo graph and reading the lint
output — Commandment 2 (`demo_vs_test`) applied to a *marketing claim*. Bonus:
the accidental E004 (copying the graph to tmp broke relative prompt
resolution) was itself unplanned evidence of cross-artifact checking. An
accident during a probe is data, not noise.

## Insight: claims survive only in narrowed form

Every claim this session lived only after narrowing:
"open source, self-hosted" → *vendor incentive alignment* (everyone is OSS);
"has YAML" → *declarative-first, lintable without executing Python*;
"LLM-friendly tooling" → *closed error surface: enumerable failure modes with
canned remediations* (Python+ruff/mypy is richer but open). The broad form of
a claim is where competitors tie; the narrow form is where the differentiator
binds. Narrowing is not concession — it is the same move as `spec_kill`:
the cheapest refutation is the one you perform on your own claim first.

## Interleave discipline held

Held the addendum append while the research doc carried the sister session's
uncommitted KR-3 edit; appended only after the tree cleaned. Session-unique
msg files (`tmp/msg-lintprobe.txt`) used throughout; one transient DNS push
failure retried without incident. The 854136c8 lesson is now habit.

**Seed:** "Closed error surface" is measurable — remediation coverage (% of
lint error codes with a `Fix:` line, % with machine-applicable fixes) could be
a CAP with a gate. More radically: should every README claim be required to
cite a reproducible probe transcript, the way every fix must cite a condemning
test? Marketing under TDD.
