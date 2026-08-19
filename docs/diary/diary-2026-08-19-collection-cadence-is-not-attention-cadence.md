# 2026-08-19 — Collection Cadence Is Not Attention Cadence

## Context

Planning FR-824 began with the phrase "weekly bulletin." The easy translation
was one Monday workflow that scrapes HVA governance, Hilma/TED, and MAO and then
summarizes whatever it sees.

## Trap: schedule_name_becomes_system_architecture

The consumer wants to spend attention weekly. That does not mean the world
should be observed weekly. Agendas, amendments, procurement deadlines, and
appeals have their own publication cadence. Treating the report schedule as the
collection schedule silently discards lead time and turns source disappearance
between runs into unknowable history.

The same conflation hides the runner's real missing capability. More probes do
not solve an ephemeral runner's amnesia. Without a prior-state ledger, every
Monday is a first Monday and the whole corpus can look new.

## Insight

Separate three clocks:

1. **Source clock:** collect event feeds often enough to preserve changes.
2. **State clock:** emit only deterministic substantive deltas across runs.
3. **Attention clock:** synthesize those deltas when the consumer reads them.

For FR-824 the clocks become daily collection, event-time persistence, and
weekly publication. The first baseline emits no news; that one rule prevents the
system's birth from being narrated as a historic week.

A second boundary emerged during contract review: Hilma and TED can describe the
same procurement. A normalized item with one `url` could not satisfy the plan's
promise to preserve both witnesses. Changing the boundary to `source_urls`
removed the contradiction before implementation. The model should represent the
world's plurality instead of forcing one source to win.

## Heuristic

When a product is named after a cadence, ask whose clock the name describes.
Never infer acquisition cadence from publication cadence. Before adding
synthesis, prove baseline, delta, retry/no-op, and multi-witness identity with
deterministic fixtures.

**Seed:** Once daily collection preserves every transition, should urgency
(deadline before next bulletin) create a separate alert product, or can the
weekly consumer contract remain honest while knowingly holding time-sensitive
events until Monday?
