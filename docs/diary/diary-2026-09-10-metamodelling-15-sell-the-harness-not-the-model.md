# Sell the harness, not the model: three pitches and the observation that kills each

**Date:** 2026-09-10
**Series:** metamodelling, part 15 (applied)
**Trigger:** operator: "across the fields are there tools / product ideas
that raise. what would you pitch".
**Context:** fourteen entries described and applied a framework. This one
asks what, if anything, a buyer would pay for — with the series' own
discipline applied: value proposition in one sentence, first consumer
named, prior art checked, and a fail state stated before the pitch.

## Candidates

| # | Tool | For whom / pain | Versus what exists | Source fields |
|---|---|---|---|---|
| 1 | Rulebook linter — provenance, contradiction, never-fired, staleness for AGENTS.md / copilot-instructions / CLAUDE.md / Cursor rules | every team with an agent rulebook that grows by default and is never pruned | nothing; the artifact class is about two years old | witchcraft (`legend`), clinical (override rate), SE (60/83, part 14) |
| 2 | Anchor-check at the generation boundary — claim-typer, citation resolver, page-level match, drift rate stamped on the output | anyone shipping LLM-written reports, briefs, lessons; the *Mata* fear | RAG attaches sources; legal AI checks citations in-domain; none report drift generically | law, history (1 in 3), journalism, clinical |
| 3 | CI harness census — fire count, override count, last fail per gate; lists ordeals | platform / DevEx teams with forty checks and a flaky-skip culture | dashboards show pass rates, not "has this ever failed" or "how often bypassed" | clinical alert fatigue, witchcraft, part 1 seed |
| 4 | Propagation engine — typed `derives_from` / `contradicts`; refute a node, flag downstream | strategy (assumptions → decisions), doctrine maintainers, informal-math citation graphs | Shepard's / KeyCite in law; scite.ai in science; nothing cross-domain | law, clinical (MMR), strategy |
| 5 | Input-closed reader as a docs test — "a model given only this text can do X?" | docs and API teams; PR bodies (the outsider, FR-995, exists here) | doc linters check style, not comprehension | journalism, part 5 |
| 6 | Source-anchored courseware — backward design, typed claims, student- and historian-model readers | teachers who will not use generated material they cannot trust | crowded; none verify anchors | history, the Rome case |
| 7 | Decision journal with edges and scheduled reread | leadership teams | many journals; no propagation; adoption historically poor | strategy |

## The three I would pitch

**1. The rulebook linter.** The only candidate whose artifact class did
not exist three years ago and now sits in every repository. The rulebook
*is* the harness and nobody audits it. Every feature is mechanical or one
input-closed judge call: rule → cited incident or `legend`; rule pairs
that contradict; rules with no corresponding gate
(`detection_without_enforcement`); rules never triggered in hook logs;
override rate per gate. **Wedge:** a corpus-map-reduce census over a few
hundred public rulebooks — legend rate, contradiction count, growth over
git history — at cheap-model pricing; a research result and a launch
artifact in one. **Kill observation:** legend rates low and rulebooks
small and stable across the corpus. Then the pain is only ours.

**2. The anchor-check hook.** Model-independent, domain-generic, and the
demo already exists: one minute, one in three. A PreToolUse-shaped step
in any writing pipeline: type each claim, resolve each anchor, match the
quote, stamp the drift rate on the document. Sells against fear, the
strongest buyer motive in law and medicine. **Kill observation:**
frontier models reach near-zero citation drift natively; the layer
becomes a receipt, not a check, and its price collapses. That is the
pre-mortem, stated.

**3. The CI harness census.** Smallest and most immediate; it also
sharpens the other two, because an ordeal in CI and a legend in a
rulebook are the same object. **Kill observation:** a repository where
every gate has failed within ninety days — the census finds nothing,
cheaply.

Not pitched alone: 4 is the *feature* that makes 1 and 3 valuable, not a
product; 6 is crowded and its differentiator is 2, so it ships as 2's
vertical; 7's obstacle is human, not technical.

## The principle

**Sell the harness, not the model.** Every field's durable verification
product outlived its practitioners and its methods: citators since the
1870s, GRADE across generations of trials. A model-independent
verification layer survives model churn; a model-dependent product is
repriced every release. *Liability draws the edges* (part 13) is also
the go-to-market: the first buyers are wherever a wrong claim already
costs money.

## The caveat the series requires

The generator is pitching tools derived from its own reflection — one
witness, fifteen entries. Each pitch carries the observation that would
kill it; the rulebook census is the cheapest of those and would decide
pitch 1 in an afternoon. Until it runs, these are drafts with a
value-proposition sentence attached.

## Trap

**`pitch_without_kill_observation`.** A product idea stated without the
data that would end it. Indistinguishable from an ordeal: it can only be
confirmed.

## Heuristic

For every tool idea, write the one sentence for-whom / what-pain /
versus-what, name the first consumer and first event, then write the
observation that kills it and estimate its cost. Pitch only the ideas
whose kill observation is cheap to obtain, and obtain it first.

**Seed:** the rulebook census. `gh search code` for AGENTS.md,
copilot-instructions.md, CLAUDE.md, `.cursorrules`; sample two hundred;
map each with a cheap model to (rule count, cited-rule count,
contradiction pairs, gate-backed count); reduce to distributions. One
afternoon, and it answers whether part 14's 60/83 is a local defect or
the shape of the artifact class.
