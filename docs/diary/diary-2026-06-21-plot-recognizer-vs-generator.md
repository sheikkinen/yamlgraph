# We built a plot recognizer; plot wants a generator

**Date:** 2026-06-21
**Context:** DM v2 continuity program (FR-474 -> FR-558), reflecting on the
10037-BC floodmark-saga run and the v3-rewrite-guidance doctrine.

## The trap, named

For thirty-odd feature requests we modeled plot the same way: let the LLM write a
chapter, then try to **parse a plot model back out of the prose** and gate the
parse. The ledger, the witnesses, the reversal/unplayable/composition gates --
all of it is **plot recognition**. The user said it plainly: "there are always
more plot elements to capture." That sentence is not a to-do list with a few
items left. It is the signature of recognition over an **open set**.

Prose can express unboundedly many plot-relevant facts -- lifecycle, position,
prop possession, who-believes-what, unpaid emotional debts, off-screen elapsed
time, promises made and owed. Any extract-and-gate vocabulary over that set is
provably incomplete; each gate we ship closes the gap by measure zero. We were
enumerating a set with no boundary and reading our fatigue as "almost done."

## The thing I missed for thirty FRs

The 10037-BC run was an accidental, clean falsification test, and it pointed at
the real omission. The floodmark engine is **"Arnulf is alive but believed
dead."** v2's lifecycle ledger has *one bit per character*: `alive | dead`. That
schema **cannot represent the premise.** "Presumed dead" is not ontology (what is
true); it is **epistemics** (what the clan believes). The whole saga lives in the
divergence between truth and belief -- and we modeled a global truth flag.

Seen from there, three "different" defect classes collapse into one omission:

- the **early reveal** (Arnulf alive in Ch3 with no Ch2 setup) -- a missing
  `believes(observer, fact, t)` lane;
- the **phantom reversal / double return** (FR-525/555) -- a missing
  `because(event, event)` causal link and partial order;
- the **unresolved confrontation** (Ch6->Ch7, accuser flips to silent observer)
  -- a missing `affect_debt(char, unpaid)` fluent (Lehnert's unterminated plot
  unit, 1981).

We kept adding gates because we modeled **ontology** when plot lives in
**epistemics + causality + affect**. Each of those is a *finite* lane. Ontology
alone is the wrong -- and unboundedly leaky -- projection of them.

## The heuristic

When a quality program feels like whack-a-mole with no end ("always more X to
capture"), check whether you are **recognizing** an open set or **generating** a
closed one. If the constraints are *detected after the fact*, the vocabulary is
open and you will chase it forever. Invert the direction of truth: define a
small, closed, **generative** vocabulary, author the artifact from it, and demote
the LLM to its realizer. Then there is nothing to recapture, because nothing
load-bearing originated in the output. (This is the same `the_one_law` move --
normalize at the boundary where data is born -- applied to *structure* instead of
*types*: author plot at the boundary where it is born, do not reconstruct it
where it manifests.)

## What this costs to admit

v2's gates are not wasted -- they are the **incident record** that told us which
lanes matter (incident_density_ranking: the breaks cluster on belief, causality,
affect, exactly the three lanes a generative model would carry). But the doctrine
doc's §2 ("project, don't reconstruct") stops one step short: it proposes to
project a *richer ledger* and keep extracting the rest. The run says the ledger's
**schema** is the bug, not its direction. A richer ontology ledger is still
ontology.

**Seed:** What is the *minimal closed generative vocabulary* of plot for a
capped-scene engine -- the smallest set of lanes (belief, causal link, affect
debt, function/role, world fluent) from which prose can be realized with nothing
left to recapture? Propp gives a finite alphabet, planning (IPOCL) gives the
causal partial order and parallel-safety, plot units give the affect lane,
epistemic logic gives the belief lane. Is the DM-sized synthesis a partial-order
plan of Propp-like functions whose preconditions range over a typed world-state
**and** a per-observer belief-state, with affect-debt as a tracked fluent? And
which single lane, added first, retires the most v2 gates -- is it belief, the
one the floodmark premise proves we never had?
