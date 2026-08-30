# Problem brief: research route failure names the symptom, discards the recorded cause

<!-- Closed input for the research route (FR-890). Incident record only;
     no solution content. -->

**Prior art:** filename-noun hits on other briefs sharing "problem, brief" are unrelated subject matter — not applicable. `fr-925-lane-delivery-problem-brief.md` is the sibling incident (same day, same session): it documents the delivery seam this brief's diagnosis cost was paid on; distinguished — this brief concerns pipeline failure diagnostics, not hook delivery.

## Problem statement

When a persona node in the research-route graph exhausts its retries,
the framework records a complete failure record — node name, exception
type, and the full validation message — into the graph state's error
channel. The downstream gather step then fails the run with only
"missing persona findings: <state key>", naming the absent key and
discarding the recorded cause sitting in the same state one key away.
The operator-facing failure output (CLI, log tail, run summary) carries
the symptom only. Recovering the actual cause required drilling into
the tracing backend with a throwaway script to read information the
graph already possessed at raise time. The fault was hidden, not borne
witness to; a failure record that exists but is never surfaced is
equivalent to no record at the moment of diagnosis.

## Classification

measurement

## Constraints

- The persona output schema's hard caps (reject over-length, never
  truncate) are deliberate boundary design and must not be weakened.
- Node-level retry semantics and the error-channel state shape are
  framework-level contracts shared by other graphs; the research route
  is one consumer.
- The route's failure must remain a hard failure (no partial artifact,
  no fail-soft) — the draft artifact is the proof of research.
- Diagnosis must be possible from the run's own output without tracing
  backend access.

## Witnessed incidents

- 2026-08-30, three consecutive research-route runs for the FR-925
  brief failed with "missing persona findings: yamlgraph_native_finding"
  in CLI output and log. The recorded cause — a Pydantic
  string_too_long validation failure on the rationale field, retried
  and re-failed identically — was present in graph state's error
  channel each time but appeared nowhere in the failure output.
- Same incident: root-cause recovery required a custom LangSmith drill
  script traversing 47 child runs to read the error record, converting
  a one-read diagnosis into a multi-step trace investigation.
- The route's own contract message ("tmp/draft-alternatives.md is the
  proof of research") repeated the symptom framing; no surface in the
  failure path cited the recorded validation error.
