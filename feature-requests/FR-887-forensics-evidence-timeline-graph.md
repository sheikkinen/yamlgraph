# Feature Request: Forensics Evidence-and-Timeline Graph

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-08-25
**First consumer / first event:** the next production-incident session — the
moment it would otherwise assemble a SID-keyed timeline by hand at premium
prices.

**Prior art:** FR-884 raw read (docs/FR-884-raw-read-log.md S-H1) records the
organic precedent: during the window the operator scripted two evidence
gatherers *mid-incident* in a customer project because interactive evidence
assembly was untenable — the gather half of this shape is proven
extractable by field practice; this FR extracts the remaining join+narrate
half. The recap demo (examples/demos/recap, FR-700..704 arc) is the
committed in-repo pattern precedent: deterministic collection in tool
nodes, exactly one LLM judgement, code-assembled residue — this FR is that
architecture applied to incident evidence. No graveyard hit proposes a
timeline-assembly graph.

## Summary

A yamlgraph pipeline that takes an incident key (call/trace/session id) plus
gathered source artifacts, joins them by key in code, and renders a
citation-checked forensic timeline with one pinned cheap-model judgement.

## Value Statement

Incident responders (human or agent, especially at 3 AM) get a verified
timeline in one graph run instead of a multi-hour premium session; every
timeline row is mechanically traceable to a source artifact.

## Problem

FR-884 measured incident-forensics at ~32M tokens (4.9%, 4 primary
sessions). The shape is closed-input and one-judgement — the definition of
graph-extractable — yet each incident re-derives the join and narrative
interactively. The gather step already escaped to scripts under incident
pressure; the join+timeline step has not.

## Ideal Result

`yamlgraph graph run examples/demos/forensic-timeline/graph.yaml
--var key=<id> --var sources_dir=<dir>` emits a timeline document where
every row carries a source citation, plus a gap report (expected artifacts
missing for the key) — and the validator rejects any timeline row that
cites nothing. The manual runbook's assembly steps reduce to one command.

## Proposed Solution

Three stages, recap-demo architecture:

1. **Gather/parse (tool nodes, code):** read the artifacts in
   `sources_dir` (logs, records, transcripts, API evidence dumps —
   format adapters as small parsers), normalize to keyed events
   `{ts, source_file, kind, summary_fields}`.
2. **Join (code):** filter by key, sort by ts, compute gaps
   (expected-artifact checklist vs present) — deterministic, testable.
3. **Narrate (ONE llm node, pinned cheap model per FR-884 R-4 precedent):**
   render the ordered events as a prose timeline; inline schema forces
   per-row `source_ref`; a post-validator (code) rejects rows whose
   `source_ref` is not among the inputs (plausible-wrong-answer guard).

Authored via the sole authoring route (`scripts/author.sh`), like the
FR-884 classifier. Synthetic fixtures only in tests; the example ships with
a sanitized fixture incident.

## Acceptance Criteria

- [ ] Graph authored via sole route: lint clean, smoke on committed
      synthetic fixture, demo-output.log in the diff
- [ ] Model pinned explicitly on the narrate node; no unpinned LLM nodes
- [ ] Post-validator rejects uncited timeline rows — witnessed by a
      fixture with a hallucinated citation
- [ ] Gap report lists expected-but-missing artifact kinds for the key
- [ ] No customer-identifying content in committed fixtures (FR-884 R-3
      rules apply)
- [ ] Runbook/cookbook manual-assembly section replaced by the graph
      invocation (adoption trigger)
- [ ] Changelog fragment; diary reflection

## Alternatives Considered

- **Pure script (no LLM)** — the join is code, but the narrative timeline
  with human-readable causality is a genuine single judgement; scripts
  produced tables people re-narrated interactively anyway.
- **Keep interactive** — 4.9% and climbing as pilots go to production;
  3 AM is the wrong time to pay context-resend prices.
- **General-purpose "analyze anything" graph** — fit over affordance
  (`does_the_tool_fit_or_merely_exist`); this is scoped to keyed incident
  evidence.

## Related

- FR-884 census + raw-read log (evidence); FR-884 classifier example
  (sole-route + pin precedent)
- examples/demos/recap (architecture precedent)
- Scripture: `read_raw_output_first`, `plausible_wrong_answer`,
  `substance_over_presence`
