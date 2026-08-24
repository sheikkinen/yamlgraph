# Feature Request: Memory-Corpus Curation Graph (Selective Amnesia)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced (2026-08-24) — fixture-validated; first real-corpus run pending operator scheduling
**Effort:** 1–2 days
**Requested:** 2026-08-24
**First consumer / first event:** the operator, running the graph over this
workspace's repo-scope memory corpus (~56 notes) before any future
cross-device/sharing proposal is entertained — FR-874's rejection made an
audited, curated corpus the precondition for that entire direction. Second
consumer: periodic memory hygiene (notes rot — "voice_runtime now v0.1.13"
class facts are stale within weeks).

**Blast radius:** notes move from the machine-local memory-tool root to
`tmp/` (gitignored) — AND, during the judge stage, note bodies transit to
the configured LLM provider (R-1: that is egress, not a tmp-local move).
Real-corpus runs therefore require either a local-only provider or a
recorded human approval line naming the external provider/model and the
data-handling premise; fixture runs may use any test-safe provider.

> **R-1 provider approval (operator, 2026-08-24):** `vertex` (Gemini via
> GCP) and `azure` (Azure AI Foundry) are APPROVED for real-corpus runs —
> both run in operator-controlled enterprise tenants. All other external
> providers remain blocked for real-corpus content without a new recorded
> approval.

Nothing is committed; verdict *execution* (deletion/redaction of live
memory files) happens only after written, hash-bound human sign-off.

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

1. **Collect (code):** enumerate the memory root's **repo scope only**
   (R-4: user/session scope is a separate FR after repo-scope curation
   exists) into a frozen manifest under
   `tmp/memory-curation/manifest.json` — path, sha256, size, mtime —
   and copy note bodies alongside. The memory root is passed explicitly
   (`--var memory_root=…` / env var) in all tests and smoke runs (R-6);
   the operator convenience default to the real local root must print
   the resolved root. Every relative path is sanitized. The run judges
   the frozen snapshot, never the live root.
2. **Judge (map node):** per note, one judgement with closed inputs
   (note body + the declared audience premise + today's date). Output
   schema per note (Pydantic-validated, exact enums — R-5):
   - `verdict: keep | redact | forget`
   - `audience: public | peer | customer_private | machine_local`
   - `rationale: str` (one line)
   - `redacted_draft: str | null` — non-empty iff verdict=redact
   - `staleness: fresh | dated | expired`
   - `staleness_evidence: str | null` — non-empty iff staleness is
     dated/expired; cites the expiring fact
   Prompt bounded per the prompt-contract discipline: one judgement, no
   serialization jobs, validator-covered shape.
3. **Reconcile + render (code):** count-in == count-out over the frozen
   manifest; every manifest path appears exactly once; zero unknown
   verdicts; every `redact` has a non-empty draft. Render
   `tmp/memory-curation/disposition.md` (human review surface) +
   `disposition.json` (apply input), both stamped with the manifest
   hash.

**Apply step (code, gated — R-2 hash-bound contract):** `apply` refuses
unless (a) the signed review artifact names the manifest hash and
disposition hash and the JSON input matches both; (b) every live target
still has its manifest sha256 before `forget`/`redact` executes — a note
edited after collection is drift and fails with a clear summary requiring
re-collect/re-judge; (c) idempotent re-run succeeds only for rows whose
current bytes equal the expected post-apply state (or whose forgotten
file is already absent). `forget` deletes, `redact` replaces, `keep`
untouched; prints a summary.

**Artifact boundary (R-3):** committed task brief
`feature-requests/authoring-briefs/fr-875-memory-curation-brief.md`;
graph `examples/memory-curation/graph.yaml`; prompts under
`examples/memory-curation/prompts/`; tools/nodes under
`examples/memory-curation/nodes/` if needed; `examples/memory-curation/README.md`;
apply tool `examples/memory-curation/apply.py`; fixture corpus
`examples/memory-curation/fixtures/`; authoring report retained as FR
evidence. Run outputs: `tmp/memory-curation/{manifest.json,notes/,disposition.md,disposition.json}`.
Graph authoring itself follows the sole authoring route
(`scripts/author.sh`, FR-767) at enforce time; no hand-authored
graph/prompt YAML outside it.

```bash
# run (draft only, everything under tmp/)
yamlgraph graph run examples/memory-curation/graph.yaml \
  --var audience_premise="public repo workspace; worst-case reader: internet" --full

# after human sign-off inside disposition.md
python examples/memory-curation/apply.py tmp/memory-curation/disposition.json
```

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: FR revised with provider/egress policy, repo-scope-only
      input, memory-root discovery, exact artifact paths, retained
      authoring evidence, signed apply contract, and exact schemas
      (R-1…R-6) — this document.
- [ ] AC-02: Collect reads only the configured repo-scope memory root,
      writes manifest + note bodies under `tmp/memory-curation/`
      (path, sha256, size, mtime), sanitizes every relative path.
- [ ] AC-03: Automated tests and smoke runs use fixture/temp memory
      roots only — never the operator's real memory directories.
- [ ] AC-04: Graph authored via the governed route with committed task
      brief and retained authoring report (artifacts, precedent, lint,
      smoke, repairs).
- [ ] AC-05: `graph.yaml` lints clean; fixture smoke run recorded as FR
      or example evidence.
- [ ] AC-06: Per-note output Pydantic-validated, exact enums;
      `redacted_draft` non-empty iff redact; `staleness_evidence`
      non-empty iff dated/expired.
- [ ] AC-07: Reconciliation proves count-in == count-out, each manifest
      path exactly once, zero unknown verdicts, every redact has a
      non-empty draft.
- [ ] AC-08: No run stage writes outside `tmp/memory-curation/`; tests
      assert out-of-tree writes are refused.
- [ ] AC-09: Real-corpus execution blocked unless provider is local-only
      or the FR records human approval naming provider/model and data
      premise.
- [ ] AC-10: Apply refuses unless the signed review artifact binds
      manifest hash + disposition hash and the JSON matches both.
- [ ] AC-11: Apply refuses destructive changes on live-hash drift
      (except documented already-applied idempotent states); drift
      requires re-collect/re-judge.
- [ ] AC-12: With a valid signed disposition on a fixture root: forget
      deletes, redact replaces, keep untouched, summary printed,
      idempotent re-run.
- [ ] AC-13: Tests tagged with a new `REQ-YG-XXX`; capability file added.
- [ ] AC-14: First real run records only aggregates in the FR (note
      count, kept/redacted/forgotten, audience counts, provider
      decision, sign-off status); raw bodies and drafts stay under
      `tmp/` or the live root.

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

## Judgement (2026-08-24)

**Verdict: APPROVED WITH REVISIONS** — rendered via the sole judge route
(`scripts/judge.sh`, copilot graph, gpt-5.5); full artifact:
`feature-requests/FR-875-memory-corpus-curation-graph.judgement.md`.

| # | Revision (folded above) |
|---|---|
| R-1 | Provider/data-egress gate: the judge stage IS egress; local-only provider or recorded human approval for real-corpus runs |
| R-2 | Apply is hash-bound: signed artifact names manifest+disposition hashes; live-hash drift refuses destructive change |
| R-3 | Graph-authoring artifact boundary frozen (task brief, graph/prompt/tool/fixture/README paths, retained report) |
| R-4 | v1 is repo-scope only; user/session scope needs its own FR |
| R-5 | Exact schema: `staleness_evidence` field, exact enums, Pydantic cross-field invariants |
| R-6 | Memory-root discovery explicit in all tests/smoke; fixtures only; convenience default prints resolved root |

**Not authorized:** committing note contents; rebuilding FR-874 transport;
cross-device sync; user/session-scope curation; automatic apply; applying
on hash drift; real-corpus egress without recorded approval; framework
primitives; CI/hook/doctrine changes.

## Implementation (2026-08-24)

RED `91293e93` (17 condemning tests, SKIP=pytest) → GREEN this change.

| Deliverable | Artifact |
|---|---|
| D-2 | `feature-requests/authoring-briefs/fr-875-memory-curation-brief.md` |
| D-3 | `examples/memory-curation/graph.yaml`, `prompts/judge_note.yaml`, `nodes/graph_nodes.py` — authored via the SOLE route (`scripts/author.sh`), report retained below |
| D-4 | `examples/memory-curation/apply.py` (hash-bound sign-off, validate-all-then-apply-all drift refusal, idempotent) |
| D-5 | `examples/memory-curation/nodes/{collect,reconcile}.py`; 3-note fixture corpus; `tests/unit/test_memory_curation.py` (17 tests, temp roots only per C-5) |
| D-7 | `capabilities/CAP-247-memory-corpus-curation.yaml` / REQ-YG-620 |

**Authoring record (C-3, from `tmp/draft-authoring-report.md`):** precedent
`examples/demos/salvage_classify` (+ python-map, research-agent shell-tool
conventions); `yamlgraph graph lint` clean first pass; fixture smoke
`--var memory_root=examples/memory-curation/fixtures/memories` completed —
3/3 notes covered, zero unknown verdicts; no repairs; no blocked
validation. Independently cross-checked post-run: lint re-run clean; raw
disposition read (`read_raw_output_first`) — the judge correctly rendered
keep (durable fact), forget/expired (version pin, evidence cited), and
redact (planted endpoint + credential-workaround note): the exact FR-874
leak classes.

**AC-14 (first real run, 2026-08-24, provider=vertex):** 57 notes judged,
zero validation errors; verdicts 51 keep / 6 redact / 0 forget; audience
43 public / 14 peer / 0 customer_private / 0 machine_local; staleness
56 fresh / 1 dated. **Disposition NOT signed off** — two findings:
(1) *premise determines verdict semantics*: the run used the
publication premise ("public repo workspace"), so redacted drafts strip
locally-useful facts from local working notes — applying it would degrade
local memory; local-hygiene runs need a machine-local premise, and the
README should document the two run modes. (2) *witness disagreement*: the
judge caught 4/8 notes from the operator-session manual security review
plus 2 the manual review missed, but passed 4 customer-identifier notes
(fly-log-census, nc383, persona-suite, voice-runtime-test-env) and rated
56/57 fresh despite version-pin content — single-judge recall is real but
incomplete; the FR-874-era manual review and this graph disagree exactly
where the witness-disagreement cross-checker pattern predicts. Follow-up
candidates: premise-pair runs (hygiene + export) and a
disagreement-diff over their dispositions.

### Questions for the human

None open — the judgement resolved provider policy (R-1 mechanism) and
scope (R-4). Advisory until human-reviewed.
