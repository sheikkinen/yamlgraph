# The Beat That Could Not Be Played

**Date:** 2026-06-18
**FR:** FR-528 (re-scoped from a falsified FR-527)

## What happened

FR-527 tried to cut the DM v2 no-progress tail at the PLAY boundary with a beat-stall
guard and was falsified by its own corpus check: a beat-count plateau is indistinguishable
from a routine mid-scene pause (up to 9 turns in the recorded corpus). The signal carried
no new information because it was a transform of the one it tried to beat
(`scene_complete = k == n` vs "k flat for K turns").

FR-528 moved the cure to the OUTLINE boundary — where the bad beat is actually authored —
and the proposal arrived wearing a schema change: tag the offending beat `playable: false`
so it drops out of `n`. The judgement rejected that mechanism before a line was written:
`beats` is a hardened `list[str]` contract that the director selects *by number*. A beat
the director can never select is a category error, and promoting `str` beats to
`{text, playable}` objects would ripple through ~8 call sites AND the recorded `*-BC`
corpus. The same goal — `scene_complete` fires when the scene resolves, the epilogue
survives as narration — is reachable by keeping the epilogue OUT of the beat list and
folding it into the existing `summary`, with a detector that catches it being mis-authored
into a beat. Zero contract blast radius.

## The trap

**`schema_change_as_default`** — when a proposed feature is "add a field/flag to the data
model," check first whether the same outcome is reachable by *relocating* the offending
content to a channel that already exists. The `playable` flag and the `summary` fold both
preserve the epilogue as narration and both fix `n`; only one of them migrates a corpus.
The cheaper design was invisible until I read the actual type of `beats` (Commandment 4:
honor existing patterns; the contract is the pattern).

**`leading_anchor_over_co_occurrence`** — the first detector instinct was "fire if the
final beat mentions 'settlement'/'feud' after a time word." That is the `plausible_wrong_
answer` shape: it over-fires on a present-tense in-scene resolution that legitimately names
the settlement. The discriminator that actually separates the 10025-BC CH8 epilogue from
the clean 10020/10022/10023/10024-BC resolutions is positional, not lexical: an epilogue
*opens* with the time jump ("By autumn, …"). Anchoring on the LEADING token — not
co-occurrence anywhere in the beat — is what made the witness precise. I pinned this with
an explicit negative-control test (a present-tense "settlement/feud" final beat must stay
clean) rather than trusting the happy path.

## The insight

When FR-527's downstream guard was falsified, the falsification itself named the boundary:
"a count plateau is mid-scene noise" is the same sentence as "the defect is upstream of
play." The corpus that condemned the play-loop fix was the map to the outline-loop fix. The
RED won twice — once to kill the wrong cure, once to locate the right one.

## Seed

The DM now has TWO outline-time gates (FR-525 reversal-pack, FR-528 unplayable-epilogue)
that share a loop, a retry budget, and a raise discipline but each carries its own
detector + feedback pair. At what point does a third gate justify a generic
"outline-witness → feedback → bounded re-roll → raise" combinator, and would extracting it
make the *next* gate cheaper than copy-pasting the pair — or would it just hide the one
line of per-gate logic that actually matters (which token the feedback names)?
