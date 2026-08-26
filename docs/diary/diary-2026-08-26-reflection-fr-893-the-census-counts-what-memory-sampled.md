# Diary — Reflection FR-893: The Census Counts What Memory Sampled

**Date:** 2026-08-26
**Context:** FR-893 enforced: 1266 diary entries censused through the
FR-892 pipeline (24 batches, 26 min, ~$1, haiku), LLM-free recurrence
aggregation, canary-gated. The diary_graduation_pipeline Scripture seed —
unbuilt for months — now runs as one shell command.

## The canary earned its keep, on its first real run

The first full-corpus aggregation FAILED: exact-label canaries found ZERO
entries for a trap witnessed four times. Not because the census missed
the entries — because the vocabulary drift the raw-read had predicted was
total: `tmp_msg_txt`, `stale_tmp_msg_file`, `tmp_msg_file_loss`, never
once the literal label I'd frozen. Without the canary gate this would
have shipped as a plausible census quietly undercounting everything by
the drift factor. The mechanism validated itself by failing correctly:
`plausible_wrong_answer` caught by design, not by luck. Family-substring
matching (the judgement's own word "family" was load-bearing) fixed it.

## The headline finding nobody asked for

The corpus's loudest signal is not an ungraduated trap — it is that the
top "novel" recurrences are ALIASES of graduated doctrine: the
silent_fallback family recurs 34+ times under four names;
boundary_normalization is the_one_law wearing prose. The diary keeps
re-learning what the Scripture already knows, under new names. The
graduation pipeline's real successor problem is VOCABULARY CONSOLIDATION:
a canonicalization layer (FR-593's lesson at doctrine scale) that maps
drifted trap names onto Scripture keys, so recurrence energy accrues to
the canonical entry instead of fragmenting. Also: both genuinely novel
candidates (protocol_archaeology, invisible_decisions, 12 entries each)
come entirely from world-digest entries — genre matters; digests recur
themes, reflections recur traps.

## Trap witnessed (own)

Threshold-3 emission produced 82, then 33 inbox drafts — a flood into a
consumed-on-pickup directory. The spec said "drafts at the bar"; the
operational reality said the bar and the emission bar are different
numbers. `threshold_encodes_forecast`'s cousin: a threshold correct for
CLASSIFICATION can be wrong for ACTUATION when the sink has side effects.

## Seed

**Seed:** The census found ~1700 distinct labels for what is probably
<200 real concepts. Is the next mechanism a label-canonicalization census
(map: cluster labels against Scripture keys + each other; reduce: alias
table) — turning the 4-name silent_fallback family into one row with 34
entries? That table would also make the canary gates self-maintaining:
families defined by measured aliases instead of hand-written alternations.
