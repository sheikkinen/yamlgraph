# Key findings of the applied arc, and sixty entries without a source

**Date:** 2026-09-10
**Series:** metamodelling, part 14 (closing the applied arc, parts 11–13)
**Trigger:** operator: "reflect — key findings, diary, docs pr, merge".
**Context:** parts 1–10 built a framework and read it against seven
fields. Parts 11–13 tried to *use* it: a Roman-history source ledger, a
claim-graph schema, and the schema read back across every field
including this repository. This entry states what the arc found, runs
the one query it kept promising, and records the number.

## The check, run before the reflection

Part 13 said the first Scripture-provenance query is a grep. Run against
the Knowledge Graph block of `.github/copilot-instructions.md`:

```
entries=83  cited=23  uncited=60
```

Cited means an inline `FR-nnn`, `NC-nnn`, or date on the entry's own
line. Of the 60 uncited: 4 are seeds (forward-looking, no incident
expected) and 9 are the interrogative canon, cited once as a block in
its section header. That leaves roughly 47 entries — well over half —
whose provenance is not on the line that states the rule. The oldest
traps are among them: `continuation_bias`, `quick_confidence`,
`spec_kill`, `three_reads`, `callsite_fix`. They predate the citation
habit.

This is not proof of no origin. Most are recoverable from diaries by
search. It is proof that the record does not carry the edge where the
rule is, which is what `legend` means in the model: a claim whose
`derives_from` must be reconstructed rather than read. First strike, by
the two-strike rule for tooling. The field earns a second look the next
time a Scripture entry is added or pruned.

## Key findings

1. **For fields without compilers, the oracle is a graph query.** It
   does not return true/false; it returns a rung computed from latency,
   origins, and transmission (part 11). GRADE, citators, and source
   criticism are the same function under three names.
2. **Generator recall of citations drifts at a measurable rate.** One
   anchor in three, one minute to check (part 11). The cheapest oracle in
   the whole series, and the one most often skipped, including by the
   author of the series.
3. **The claim graph is an RTM plus two edges.** `contradicts` and
   `derives_from` are what the repository's traceability matrix lacks and
   what history, law, and medicine cannot do without (part 12). Store
   follows query: the metrics are paths, so the record is a typed edge
   table and any vector index is a retrieval cache.
4. **Liability draws the edges; propagation is the query.** The graph is
   mature where wrong claims cost — law's red flag, medicine's systematic
   reviews, formal proof — and absent where claims are cheap: strategy,
   republished news, SE doctrine, agent output (part 13). Every field's
   first payoff is the same walk: a node is refuted, flag what rests on
   it.
5. **The leaf is the oracle.** Witchcraft had the graph; its leaves were
   uninspectable. A schema constraint — every `attests` edge terminates
   in a Passage a third party can inspect, every rung has a recorded
   fail — is the difference between a citator and a *Malleus*.
6. **For this repository the payoff is on doctrine, not code.** Code has
   tests. Scripture has parentheticals. The grep above is the first
   number the doctrine layer has ever had about itself.
7. **Prompt-level heuristics decay within a turn.** Part 10 wrote "run
   the artifact through its own rules once"; part 11 found it had not
   been done for three turns. Parts 11, 13, and 14 each opened with a
   check because the pattern was made a *step*, not a *rule*. The route
   held where the doctrine did not.

## What the arc did not do

It did not verify its own non-Polybius anchors (Shepard's date, the
MMR retraction, the seventeen-year estimate, Mather 1692, Spee 1631).
By finding 2 they are drafts. It did not run the propagation query for
superseded FRs (part 13's seed). It did not build anything. Fourteen
entries by one generator in two days remain one witness; the grep above
is the first observation that did not come from the generator's own
reflection.

## Traps

**`rule_without_its_line`.** The provenance exists somewhere in the
record but not where the rule is read. Every reader of the rule inherits
it as legend regardless of how well it was once witnessed.

## Heuristic

When a framework has been described for more than two entries, stop and
run its cheapest query against the thing that produced it. The number is
worth more than the next entry.

**Seed:** 47 uncited Knowledge Graph entries. Which have a diary entry
that could be linked in one edit, which have an FR, and which have
neither? The third set is the candidate list for the Red Hat — and the
first real input to the census.
