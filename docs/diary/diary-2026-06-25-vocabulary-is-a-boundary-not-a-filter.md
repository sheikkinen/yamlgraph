# The Vocabulary Was a Boundary, Not a Filter

*2026-06-25 — FR-592 rejected, FR-593 born; the day an oracle's convenience lied about architecture.*

## What happened

Yesterday I proved, with an oracle, that a controlled vocabulary lifts L5 recall
(scifi 0.13→0.30 atop the transition rule). Today I shipped that proven ingredient and
the corpus got *worse*: scifi **0.04**, below the 0.09 no-vocab run and the 0.17
baseline. I rolled the whole FR back, marked it REJECTED, and re-planned it as FR-593.

The proximate bug was mechanical — the extracted vocab arrived as a markdown *string*,
not a dict, so the encoder's `{{ state.vocab.locations }}` rendered empty and the anchor
was inert (the at-flood stayed at 97 FPs, unchanged from 100). But the mechanical bug is
not the lesson. Even with a perfect dict, the architecture was wrong.

## The trap: the oracle's injection site is not an architectural endorsement

The oracle injected perfect vocabulary **at encode time**, as a "use ONLY these tokens,
omit if nothing fits" filter, and scored 0.30. I read that as *"vocabulary at encode
time works."* It does not. It worked **only because the tokens were ground-truth-exact**
— a perfect filter is lossless. The moment a real, LLM-extracted vocabulary sits at that
same site, the filter is *lossy*: every imperfect token silently omits a true fluent.
The oracle chose encode-time because it was the cheapest place to *measure* the
ingredient, not because it was the right place to *deploy* it. I mistook a measurement
convenience for a design.

Name it: **`oracle_injection_site_as_architecture`** — an oracle proves an ingredient at
whatever site is cheapest to inject; promoting that ingredient to production is a
separate decision about *where it enters*, and the oracle is silent on it.

## The deeper law this is an instance of

This is not new doctrine — it is `the_one_law` wearing a costume:

> *Normalize at the boundary where external data enters, not downstream where it
> manifests.*

Vocabulary **is** a naming normalization. The at-flood **manifests** at `encode`, so I
put the cure at `encode` — the `downstream_fix` trap, exactly. The drift's *source* is
that five characters independently re-name the same places; that source is upstream, at
the story level, before any per-character work begins. FR-593 moves the cure to the
boundary: extract the canon once, **rewrite the beats into it**, and let every
downstream stage read already-normalized names — no filter at the tail, because there is
nothing left to filter.

## Reflection: how the whole pipeline fits — nouns before verbs

The session forced me to see the plot pipeline as two phases, not a flat list of nodes:

1. **Cast & Set (story-level entity resolution).** *Identify the agents* (the cast) and
   *the canonical vocabulary* of locations and objects (the set). These are the **nouns**
   — the stable entities — and they are one shared coordinate system the whole story is
   written in. Agents are themselves part of the vocabulary; identifying the cast and
   fixing the names are the same act of resolving *what exists*.
2. **Per-character trajectory (detail-level analysis).** For each agent, retell their arc
   (`summarize`) and encode the **transitions** — `at[X, place]` flipping false→true as
   they move, `holds` flipping as they gain and lose. These are the **verbs**: change
   over the fixed nouns. Then `combine` unions the trajectories into one world model.

The dependency is strict and was the thing I violated: **you cannot derive the verbs
until the nouns are fixed and shared.** Encoding a transition is naming a *from* and a
*to*; if each character invents their own nouns, the transitions can't agree — the
at-flood is precisely the sound of verbs derived before nouns were resolved. Vocabulary
and agent-identification are not two more tunable knobs alongside the encoder (the OFAT
view I was punished for yesterday); they are the **phase that must complete before the
detail phase begins**. Story-level before character-level. Nouns before verbs.

FR-592 tried to smuggle the noun-fixing *into* the verb step as a filter. FR-593 puts it
where it belongs: a prologue that establishes the coordinate system, so the detailed
analysis has somewhere consistent to land.

## Heuristic

When you promote an oracle-proven ingredient to production, **re-decide where it enters
the pipeline** — the oracle picked the cheapest injection site for *measurement*, which
is often the worst site for an *imperfect* real implementation. Ask: is this ingredient a
**normalization**? If so, it belongs at the input boundary, not at the stage where its
absence manifests.

## Seed

If "cast & set" is genuinely one phase, should *identifying the agents* and *extracting
the vocabulary* be one node, not two — a single story-level entity-resolution step whose
output (the cast list + the canonical set) is the typed contract every downstream
perspective is required to speak? And if so, does the gloss-absent ceiling
(`Vantari Labs`, `Surface` — names the synopsis knows but the beats never say) become a
*detectable* defect: an entity in the cast/set that no beat references is either dead
vocabulary or an upstream classification miss?
