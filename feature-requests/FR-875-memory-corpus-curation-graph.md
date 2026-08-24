# Feature Request: Memory-Corpus Curation Graph (Selective Amnesia)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1–2 days
**Requested:** 2026-08-24
**First consumer / first event:** the operator, running the graph over this
workspace's repo-scope memory corpus (~56 notes) before any future
cross-device/sharing proposal is entertained — FR-874's rejection made an
audited, curated corpus the precondition for that entire direction. Second
consumer: periodic memory hygiene (notes rot — "voice_runtime now v0.1.13"
class facts are stale within weeks).

**Blast radius:** notes move from the machine-local memory-tool root to
`tmp/` (gitignored) only. Nothing is committed; worst-case reader is the
local operator. Verdict *execution* (deletion/redaction of live memory
files) happens only after written human sign-off.

## Summary

A yamlgraph map-node graph that judges every note in the Copilot memory
tool's repo scope and renders a per-note disposition draft — **keep /
redact / forget** plus an audience classification (**public / peer /
customer-private / machine-local**) — for human review. The corpus today
is an uncurated accumulation of "memory glimpses": no note has ever passed
a gate for accuracy, staleness, audience, or sensitivity. FR-874 built a
transport for this corpus and was rejected for exactly that; this FR is
the prerequisite mechanism it skipped.

## Value Statement

The operator gets a reviewed, classified memory corpus — stale and
one-off notes forgotten, sensitive facts flagged by audience — making
future sharing decisions (and daily recall quality) trustworthy.

## Problem

1. **No curation gate has ever run.** Notes accumulate at write time with
   zero review; the corpus mixes durable boundary facts with expired
   version pins, one-off incident glimpses, and customer-critical
   material (FR-874's security review found customer-confidential
   operational findings sitting in "repo" notes; details intentionally omitted).
2. **Pattern scanning cannot classify meaning.** The FR-874 seed scan
   grepped for secret *values* and passed; the actual leak class was
   *facts* (details intentionally omitted from this public record).
   Only meaning-level judgement classifies that — an LLM job, per note.
3. **Stale notes are actively harmful.** A wrong note is worse than no
   note (the memory is trusted at recall time); several notes carry
   version/deployment facts with built-in expiry and no freshness marker.
4. **The task shape is a graph.** Per-note LLM judgement over a manifest
   is the map-node's native shape (`is_this_a_graph`; the trap fired late
   in FR-874 — the operator named the graph route, not the agent).

## Ideal Result

The operator runs one command; minutes later `tmp/memory-curation/` holds
a disposition draft covering every note (count-in == count-out, zero
unknown verdicts), each row carrying verdict, audience, one-line
rationale, and for `redact` a concrete redacted draft. The operator edits
or signs off the draft; a small apply step then executes the amnesia —
deleting `forget` notes and replacing `redact` notes — against the live
memory root. Re-running on an already-curated corpus yields near-empty
deltas. Nothing sensitive ever touches a committed path.

## Proposed Solution

Three stages; only the middle one is an LLM.

1. **Collect (code):** enumerate the memory root's repo scope (and
   optionally user scope) into a frozen manifest under
   `tmp/memory-curation/manifest.json` — path, sha256, size, mtime —
   and copy note bodies alongside. The run judges the frozen snapshot,
   never the live root.
2. **Judge (map node):** per note, one judgement with closed inputs
   (note body + the declared audience premise + today's date). Output
   schema per note:
   - `verdict: keep | redact | forget`
   - `audience: public | peer | customer_private | machine_local`
   - `rationale: str` (one line)
   - `redacted_draft: str | null` (required iff verdict=redact)
   - `staleness: fresh | dated | expired` (dated/expired must cite the
     expiring fact)
   Prompt bounded per the prompt-contract discipline: one judgement, no
   serialization jobs, validator-covered shape.
3. **Reconcile + render (code):** count-in == count-out over the frozen
   manifest; zero unknown verdicts; every `redact` has a draft. Render
   `tmp/memory-curation/disposition.md` (human review surface) +
   `disposition.json` (apply input).

**Apply step (code, gated):** `apply` refuses to run unless the
disposition file carries an explicit human sign-off marker (edited-in
line, same pattern as FR-868's written-approval hard gate). Executes
against the live memory root: `forget` deletes, `redact` replaces,
`keep` untouched. Prints a summary; idempotent.

Graph authoring itself follows the sole authoring route
(`scripts/author.sh`, FR-767) at enforce time.

```bash
# run (draft only, everything under tmp/)
yamlgraph graph run examples/memory-curation/graph.yaml \
  --var audience_premise="public repo workspace; worst-case reader: internet" --full

# after human sign-off inside disposition.md
python examples/memory-curation/apply.py tmp/memory-curation/disposition.json
```

## Acceptance Criteria

- [ ] AC-01: Collect stage freezes the corpus (manifest + bodies) under
      `tmp/memory-curation/`; live memory root is read-only to the graph.
- [ ] AC-02: Disposition covers every manifest note — count-in ==
      count-out, zero unknown verdicts (validation error otherwise).
- [ ] AC-03: Every `redact` verdict carries a non-empty redacted draft;
      every `dated`/`expired` staleness cites the expiring fact.
- [ ] AC-04: Apply refuses without the human sign-off marker; with it,
      `forget` deletes and `redact` replaces in the live root; idempotent
      on re-run.
- [ ] AC-05: No stage writes outside `tmp/memory-curation/` and the live
      memory root (apply only); nothing under a committed path.
- [ ] AC-06: Graph lints clean; smoke run on a fixture corpus (temp
      memory root — never the operator's real one in tests) with
      `demo-output.log` if under `examples/demos/`.
- [ ] AC-07: Tests tagged with a new `REQ-YG-XXX`; capability file added.
- [ ] AC-08: First real run's disposition reviewed by the operator; the
      FR records the aggregate outcome (kept/redacted/forgotten counts).

## Alternatives Considered

- **Manual sweep by the agent in-session:** does not scale (56 notes ×
  meaning-level judgement burns interactive context), leaves no artifact,
  and repeats the FR-874 error of trusting one session's unaudited
  reading. The map graph is cheaper, parallel, and leaves a reviewable
  draft.
- **Subagent fan-out / shell script over the copilot CLI:** the fallback
  shapes; the map node is the framework-native form of exactly this task
  (`is_this_a_graph` — naming the graph is the point).
- **Curate only at export time (rebuild FR-874 with a filter):** rejected
  by FR-874's precedent rules — curation is the prerequisite mechanism,
  transport a possible successor. Also hygiene has standalone value with
  no transport at all.
- **Regex/denylist classifier:** proven insufficient — the leak class is
  facts, not tokens (FR-874 rejection, finding 2).

## Prior art

**Prior art:** FR-874 (REJECTED 2026-08-24) — the transport this FR is
the prerequisite for; its rejection section binds this design (visibility
as written precondition, curation before transport, classification as
boundary requirement) and this FR deliberately moves no data beyond
`tmp/`. FR-868 salvage_classify — the disposition-draft shape this FR
mirrors (frozen manifest, count-in == count-out, zero unknown verdicts,
written-approval hard gate before destructive action). FR-617 (memory
node) — graph-level memory primitive for graphs, not the authoring
agent's memory tool; no overlap. `.chaplain/inbox/memory-corpus-judgement-graph.md`
(2026-08-24) — the freeform proposal this FR formalizes; superseded by
this document.

## Related

- `docs/diary/diary-2026-08-24-the-note-that-judged-its-own-transport.md`
  — the rejection arc and the `threat_model_inherited_unverified` trap
- Scripture traps this mechanizes against: `plausible_wrong_answer`
  (stale note at recall time), `workspace_is_not_boundary` (audience
  classification names it per note)
- Graph authoring doctrine: `.github/skills/graph-authoring/doctrine.md`
  (sole route at enforce time)

## Judgement (pending)

Not judged in the author's session; route:
`.github/skills/judge-fr/adapters/README.md`.
