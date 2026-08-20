# Feature Request: FR-845 Oulu Brief Phased Delivery

**Priority:** HIGH
**Type:** Process / GitClaw phased issue queue
**Status:** Proposed
**Effort:** 1 day elapsed (five pipeline runs plus gates)
**Requested:** 2026-08-20
**Parent:** FR-831
**Depends on:** FR-835, FR-836, FR-840, FR-841, FR-843, FR-844
**Blocks:** The Oulu daily civic brief reaching production
**Prior art:** FR-828's monolithic issue timed out at enforce (900s). FR-831
decomposed the work and its source tasks were proven one-per-issue in the old
consumer (issues #2-#4 all closed pushed). Today's controlled replication in
the fresh repo — hardened FR-840/843 pipeline *plus* FR-841 reference probes —
timed out at enforce 900s with the identical signature (issue #1, run
`32368978213`): references fix discovery, not construction volume. A phase is
the pipeline's unit of commit; a phased plan is a sequence of bounded issues.
FR-835/836 composition and candidate contracts are inherited by the fresh repo
from the template; FR-837 supplies the judged composer shape. Chaining
automation (auto-filing phase N+1) is explicitly out of scope — it needs its
own judged FR because bot-filed issues interact with the intake trust gate.
**First consumer / first event:** A reader of
`sheikkinen/gitclaw-oulu-civic-intelligence`, when the daily cron commits a
complete civic brief composed from three independently owned source snapshots.

## Ideal Result

Five bounded owner issues, filed one at a time, each closing pushed within a
single enforcement session, culminating in a daily Markdown civic brief whose
three sections come from independently tested source features, whose health
table is deterministic, and whose prose is LLM-condensed from verified records
only — with issue #1 preserved untouched as the monolith-ceiling evidence.

## Decision

- One phase = one owner issue = one generated feature = one enforcement
  session. Never more than one phase in flight.
- Phases 1-3 adapt one reference probe each (`Reference-set: oulu-civic-brief`);
  phase 4 is a deterministic composer (no reference, no LLM); phase 5 is the
  LLM condenser composing phase 4's output.
- The operator files phase N+1 only after phase N's issue closes `pushed` and
  one cron (or dispatch) run commits its output without failure artifacts.
- A `reject_final` or timeout at any phase stops the queue for replanning; no
  retry of the same body without a recorded change.
- Timeout stays 900s; raising it is rejected (moves the cliff, triples failed
  cost).

## Frozen Phase Queue

Titles are frozen because `tools/slug.py` derives the feature slug from them.

### Phase 1 — Title: `Oulu harbour source snapshot`

> Reference-set: oulu-civic-brief
>
> Adapt probes/digitraffic-marine-probe.sh from this feature's reference/
> directory into one contained deterministic Python tool. Fetch upcoming port
> calls for Oulu (FIOUL) from the public Digitraffic Marine Port Call API with
> one unauthenticated GET, finite connect/read timeouts, and the smallest
> result window the output needs. Select the next upcoming vessel call and
> report vessel name, ETA, previous port, next port, berth when available, and
> vessel-type hint. Never state an inferred cargo commodity as fact.
>
> Emit exactly one non-empty Markdown candidate under state_key: candidate,
> beginning with the requested date, containing the harbour records with
> clickable source URLs and one line `Source health: ok|unavailable|invalid`.
> A valid empty result (no upcoming call) is ok, stated explicitly. Network or
> HTTP failure is unavailable; schema or parse failure is invalid; in both
> cases emit the health line and an explicit no-data statement — never
> invented records. No LLM node: retrieval, selection, and rendering are
> deterministic code. Tests use synthetic fixtures covering ok, empty,
> unavailable, and invalid paths; one bounded live smoke records health only.
> Follow policy/generated-features.md; everything stays inside this feature
> directory.

### Phase 2 — Title: `Oulu procurement source snapshot`

> Reference-set: oulu-civic-brief
>
> Adapt probes/hilma-probe.sh from this feature's reference/ directory into
> one contained deterministic Python tool. Fetch recent public procurement
> notices relevant to Oulu from Hilma's public notice data with one
> unauthenticated request, finite timeouts, and a result window capped at the
> five newest qualifying notices. Report title, contracting authority,
> publication date, deadline when available, and source URL for each.
>
> Same output contract as the harbour snapshot: one Markdown candidate under
> state_key: candidate beginning with the requested date, clickable source
> URLs, one `Source health: ok|unavailable|invalid` line, explicit no-data
> statements, no invented records, no LLM node, synthetic-fixture tests for
> ok/empty/unavailable/invalid plus one bounded live smoke recording health
> only. Follow policy/generated-features.md; stay inside this feature
> directory.

### Phase 3 — Title: `Oulu municipal notice source snapshot`

> Reference-set: oulu-civic-brief
>
> Adapt probes/ktweb-probe.sh from this feature's reference/ directory into
> one contained deterministic Python tool. Fetch recent Oulu public notices
> from the official City of Oulu KTweb listing with one unauthenticated GET,
> finite timeouts, and a bounded response size. Decode losslessly using
> declared HTTP/meta charsets — never an unconditional Latin-1 fallback — and
> parse the notice table structurally, never with primary regex. Report up to
> five newest notices: title, notice type when available, date, and clickable
> official source URL.
>
> Same output contract as the other snapshots: one Markdown candidate under
> state_key: candidate beginning with the requested date, one
> `Source health: ok|unavailable|invalid` line, explicit no-data statements,
> no invented records, no LLM node, synthetic-fixture tests for
> ok/empty/unavailable/invalid plus one bounded live smoke recording health
> only. Follow policy/generated-features.md; stay inside this feature
> directory.

### Phase 4 — Title: `Oulu source health assembly`

> Compose the three committed source features. Commit composition.json with
> version 1 and dependencies exactly: oulu-harbour-source-snapshot,
> oulu-procurement-source-snapshot, oulu-municipal-notice-source-snapshot.
>
> The graph accepts date and the source_snapshots JSON envelope supplied by
> the runner. Deterministic code only, no LLM node: validate the envelope
> structurally, then emit one Markdown candidate under state_key: candidate
> beginning with the requested date, containing each source's candidate text
> unchanged in a fixed order (Harbour, Procurement, Municipal decisions) and
> ending with a Source health table showing ok, unavailable, or invalid per
> source — failed dependencies appear as unavailable with their bounded
> reason, never as invented content. The composer runs on partial and
> all-source failure; tests use synthetic envelopes covering all-success,
> each single-failure, and all-failure. Do not read sibling feature files or
> prior outputs, re-fetch sources, or parse source facts beyond the health
> annotations. Follow policy/generated-features.md.

### Phase 5 — Title: `Oulu civic brief condenser`

> Compose the assembly feature. Commit composition.json with version 1 and
> dependencies exactly: oulu-source-health-assembly.
>
> Each day, publish one concise Markdown civic-intelligence brief for Oulu,
> Finland. Deterministic code validates the source_snapshots envelope; if the
> assembly succeeded, one LLM node condenses its verified records into three
> sections (Harbour, Procurement, Municipal decisions), preserving every
> source URL as a clickable link, labeling any inference, inventing nothing,
> and reproducing the assembly's Source health table unchanged at the end.
> Begin with the UTC generation date. If the assembly's health table shows all
> three sources failed, or the assembly itself failed, fail the feature
> rather than publish a plausible empty brief. Emit exactly one non-empty
> Markdown candidate under state_key: candidate. Tests use synthetic
> envelopes proving: verified-records-only condensation input, all-failed
> means feature failure, and one-failed still yields a brief with that source
> marked. Follow policy/generated-features.md.

## Gates and Stop Conditions

1. Human approves the FR-845 judgement before phase 1 is filed.
2. Each phase issue is filed by the operator with the exact frozen title and
   body; any wording change requires a recorded FR amendment first.
3. Phase N+1 is filed only after phase N closes `pushed` and one cron or
   dispatched run commits its output with no `.failed.json` for it.
4. `reject_final`, timeout, or containment failure at any phase halts the
   queue; the failure is recorded here and the phase replanned before any
   retry.
5. Issue #1 (monolith replication) stays open, untouched, as evidence.

## Acceptance Criteria

- [ ] AC-01: Each phase issue matches its frozen title/body exactly
- [ ] AC-02: Phases run strictly one at a time; each reaches a visible
      terminal outcome (pushed or reject_final) — no silent END, no timeout
      retry without amendment
- [ ] AC-03: Phases 1-3 adapt their reference probes (staged `reference/`
      present in each generated feature) and emit health-annotated snapshots
      under `state_key: candidate` with no LLM node
- [ ] AC-04: Phase 4 composes exactly the three source slugs
      deterministically, runs on partial/all failure, and renders the health
      table without invented content
- [ ] AC-05: Phase 5 condenses verified records only, preserves URLs and the
      health table, and fails rather than publishing when all sources failed
- [ ] AC-06: After phase 5, one scheduled or dispatched cron run commits a
      complete daily brief
- [ ] AC-07: Per-phase evidence (issue, run id, commit, cron witness) is
      recorded in this FR before the next phase is filed
- [ ] AC-08: Issue #1 remains untouched; no timeout increase, no chaining
      automation, no manual feature edits

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-828 / issue #1 (both repos) | Immutable monolith-ceiling evidence; never retried as-is |
| FR-831 | Its staged queue is re-executed here in the fresh repo with references replacing prose-only transfer |
| FR-832/833/834 | Their proven one-source-per-issue scale calibrates phases 1-3; their generated artifacts died with the old repo and are not copied |
| FR-835 / FR-836 | Composition and candidate contracts inherited via template; phases 4-5 consume them as-is |
| FR-837 | Composer contract shape reused in phase 4's body; its slug freeze died with the old repo |
| FR-841 | Reference channel supplies phases 1-3; `reference/` staging already live-verified today |
| FR-843 | Guarantees every phase ends visibly (one remediation lap, then reject_final) |

## Alternatives Rejected

- **Raise the enforce timeout:** replication showed the cliff just moves;
  each failure would cost 3x more.
- **Retry the monolithic issue with a trimmed body:** the volume is in
  construction, not prose; trimming words does not shrink three adapters.
- **Auto-chaining workflow now:** bot-filed issues interact with the intake
  trust gate (`author_association`); security-sensitive, separately judged.
- **Skip phase 4 and let phase 5 compose three sources directly:** merges
  deterministic health semantics with LLM condensation in one judgement —
  the FR-837 lesson.

## Scope Fence

FR-845 authorizes filing the five frozen issues, one at a time, in
`sheikkinen/gitclaw-oulu-civic-intelligence`, plus per-phase evidence
recording. It authorizes no platform change, no timeout change, no chaining
automation, no issue #1 action, no manual edits to generated features, and no
reference-set content change.
