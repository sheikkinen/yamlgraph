# Judgement: FR-875 Memory-Corpus Curation Graph

**Verdict:** APPROVED WITH REVISIONS — the selective-amnesia graph is the right prerequisite to FR-874-style transport, but authority activates only after the FR pins provider/data-egress limits, live-apply hash gates, exact graph artifacts, and repo-scope-only input boundaries.

**Reviewed against:** `feature-requests/FR-875-memory-corpus-curation-graph.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/doctrine.md`; `feature-requests/TEMPLATE.md`; `reference/getting-started.md`; `ARCHITECTURE.md`; `feature-requests/FR-874-cross-device-agent-memory-sync.md`; `feature-requests/FR-874-cross-device-agent-memory-sync.judgement.md`; `feature-requests/FR-868-scripture-dev-salvage.md`; `feature-requests/FR-868-scripture-dev-salvage.judgement.md`; `feature-requests/FR-617-memory-note-taking-primitive.md`; `docs/diary/diary-2026-08-24-the-note-that-judged-its-own-transport.md`. The cited `.chaplain/inbox/memory-corpus-judgement-graph.md` was not consumed because no committed artifact exists at that path.

**Prior art:** FR-874 (REJECTED), FR-868, FR-617 dispositioned throughout
this judgement. FR-854 (WITHDRAWN subagent-call classification graph) —
same map-over-corpus *shape*, different subject (session transcripts, not
memory notes) and withdrawn for reasons not implicated here; no rationale
transfers. FR-814 (FR knowledge-graph extraction) — noun collision
(corpus/curation) only; extracts structure from FR files, no overlap with
memory-note disposition.

## What is sound

The problem is real and is direct REJECTED-prior-art fallout, not speculative growth. FR-874 records that its transport implementation was rejected because the repo is public and the seed corpus contained customer-critical facts, including customer-confidential operational/security details intentionally omitted here (`feature-requests/FR-874-cross-device-agent-memory-sync.md:3-24`). It binds successor proposals to classify notes before any export and to treat `public / peer / customer-private / machine-local` as a boundary requirement (`feature-requests/FR-874-cross-device-agent-memory-sync.md:26-32`). FR-875 explicitly answers that precedent by moving no data beyond `tmp/` and the live memory root (`feature-requests/FR-875-memory-corpus-curation-graph.md:15-18`, `146-158`).

The task shape fits YAMLGraph. The FR proposes deterministic collection, a per-note map-node LLM judgement, then deterministic reconciliation/rendering (`feature-requests/FR-875-memory-corpus-curation-graph.md:68-95`). YAMLGraph documents `map` as the parallel execution node type (`reference/getting-started.md:84-101`), and repo doctrine says per-item LLM judgement should name the matching graph shape before falling back to scripts or subagents (`.github/copilot-instructions.md:119-133`). The deterministic code / YAML graph / side-effect separation also aligns with the documented three-layer pattern (`ARCHITECTURE.md:36-70`).

The review-surface design is a strong reuse of precedent. FR-875 adopts FR-868's frozen-manifest, count-in == count-out, zero-unknown, draft-disposition pattern (`feature-requests/FR-875-memory-corpus-curation-graph.md:70-89`; `feature-requests/FR-868-scripture-dev-salvage.judgement.md:72-90`) and preserves human sign-off before destructive changes (`feature-requests/FR-875-memory-corpus-curation-graph.md:91-95`). Strategic classification: **contrib/example repo-operations graph plus gated local apply tool**, not a YAMLGraph framework primitive.

## Required revisions

### R-1: Add a provider/data-egress gate before any real corpus run

Fold a hard privacy boundary into the FR: the graph must not send the operator's real memory corpus to a cloud LLM provider unless the FR records explicit human approval for that provider and audience. The FR's blast-radius section says the worst-case reader is the local operator and that notes only move to `tmp/` (`feature-requests/FR-875-memory-corpus-curation-graph.md:15-18`), but the proposed map node sends every note body to an LLM (`feature-requests/FR-875-memory-corpus-curation-graph.md:75-85`). That is a data boundary outside `tmp/`, and FR-874's rejection proves the corpus may contain customer-critical facts (`feature-requests/FR-874-cross-device-agent-memory-sync.md:9-24`; `docs/diary/diary-2026-08-24-the-note-that-judged-its-own-transport.md:52-76`).

Fold this by requiring one of two modes before a real run: local provider only, or a recorded human approval line naming the external provider/model and data-handling premise. Fixture smoke runs may use any test-safe provider because fixture notes contain no private facts. The run command and README must make the provider boundary visible.

### R-2: Bind destructive apply to the frozen manifest, disposition, and live file hashes

Replace the loose "sign-off marker in disposition.md, apply disposition.json" contract with a mechanically bound apply contract. The FR freezes manifest sha256 values before judging (`feature-requests/FR-875-memory-corpus-curation-graph.md:70-74`) but apply later mutates the live memory root (`feature-requests/FR-875-memory-corpus-curation-graph.md:91-95`) without saying what happens if a note changed after collection. That can delete or redact newer human/agent content the graph never judged.

Fold this by requiring `apply` to verify: the signed review artifact names the manifest hash and disposition hash; the JSON input matches those hashes; every live target still has the manifest sha256 before `forget` or `redact`; and idempotent re-run succeeds only for already-applied rows whose current bytes equal the expected post-apply state or whose forgotten file is already absent. Any other drift must fail with a clear summary and require re-collection/re-judgement.

### R-3: Freeze the graph-authoring artifact boundary and retained records

Add exact artifact paths before enforcement starts. FR-875 names `examples/memory-curation/graph.yaml` and `examples/memory-curation/apply.py` only in examples (`feature-requests/FR-875-memory-corpus-curation-graph.md:97-107`), while graph-authoring doctrine requires an artifact boundary, committed task brief, lint/smoke evidence, and parseable authoring report (`.github/skills/graph-authoring/doctrine.md:52-74`, `91-107`).

Fold this by naming the committed task brief path, graph path, prompt path(s), optional node/tool paths, README path if any, fixture path, retained authoring-report path or FR evidence section, and exact `tmp/memory-curation/` output filenames. Authority covers running the governed authoring route at enforce time; it does not authorize hand-authoring graph or prompt YAML outside that route.

### R-4: Remove optional user-scope collection from v1

Narrow collection to the memory tool's repo scope for this FR. The first consumer and problem cite the workspace repo-scope corpus of about 56 notes (`feature-requests/FR-875-memory-corpus-curation-graph.md:8-13`, `39-43`), but the proposed collect stage adds "optionally user scope" (`feature-requests/FR-875-memory-corpus-curation-graph.md:70-71`). User-scope notes expand the privacy and audience surface while not being required for the stated first event.

Fold this by making v1 repo-scope only. User-scope, session-scope, shared-scope, cross-device sync, or git-tracked transport requires a separate FR after repo-scope curation exists.

### R-5: Make the output schema and invariants exact enough to test

Add the missing evidence fields and validator rules. The FR requires `dated`/`expired` staleness to cite the expiring fact (`feature-requests/FR-875-memory-corpus-curation-graph.md:82-83`, `115-116`), but the proposed schema has no dedicated staleness-evidence field (`feature-requests/FR-875-memory-corpus-curation-graph.md:77-83`). A one-line rationale can become overloaded and hard to validate.

Fold this by adding `staleness_evidence: str | null` required for `dated` and `expired`, defining allowed enum spellings exactly, and requiring Pydantic validation for all cross-field invariants: `redacted_draft` non-empty iff `verdict=redact`; `staleness_evidence` non-empty iff `staleness in {dated, expired}`; count-in == count-out; zero unknown verdicts; and every manifest path appears exactly once.

### R-6: Pin memory-root discovery and fixture-only automated tests

Specify how collection finds the memory root and how tests avoid the operator's real store. FR-875 says the graph reads the "memory root's repo scope" (`feature-requests/FR-875-memory-corpus-curation-graph.md:70-74`) and AC-06 mentions a temp memory root for smoke tests (`feature-requests/FR-875-memory-corpus-curation-graph.md:122-124`), but the runtime discovery contract is not frozen. FR-617's memory primitive warns that durable note stores need explicit miss and concurrency/path contracts (`feature-requests/FR-617-memory-note-taking-primitive.md:44-63`), and repo doctrine treats workspace boundaries as a recurring source of defects (`.github/copilot-instructions.md:87-88`, `109-110`).

Fold this by requiring an explicit CLI variable or environment variable for the memory root in all tests and smoke runs, path sanitization for every manifest entry, and fixture corpora under tests/examples. A convenience operator command may default to the real local root only if it prints the resolved root and refuses to apply without the R-2 signed review gate.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-875-memory-corpus-curation-graph.md` folding R-1 through R-6 |
| D-2 | Committed graph-authoring task brief, e.g. `feature-requests/authoring-briefs/fr-875-memory-curation-brief.md` |
| D-3 | `examples/memory-curation/graph.yaml`, prompt YAML, optional nodes/tools, and README named by the revised FR |
| D-4 | `examples/memory-curation/apply.py` or equivalent apply tool with signed-disposition/hash-bound gates |
| D-5 | Fixture corpus and pytest coverage for collect, schema validation, reconciliation, no-write-outside paths, and apply idempotence/drift refusal |
| D-6 | `tmp/memory-curation/manifest.json`, copied fixture/real note bodies, `disposition.md`, and `disposition.json` as ignored draft outputs only |
| D-7 | Capability/requirement artifact and `@pytest.mark.req("REQ-YG-XXX")` coverage |
| D-8 | FR implementation record with authoring report, validation evidence, provider-boundary decision, first-real-run aggregate counts, and diary reflection |

Not authorized: committing memory-tool note contents; rebuilding FR-874 transport; cross-device sync/import/export; user-scope or session-scope curation; automatic apply without written human sign-off; applying redactions/deletions to files whose live hash differs from the manifest; sending real corpus content to an external LLM provider without recorded approval; adding a YAMLGraph framework primitive; changing CI, hooks, judge/review doctrine, graph-authoring doctrine, or memory-node runtime behavior.

## Revised acceptance criteria

- [ ] AC-01: FR-875 is revised to define provider/data-egress policy, repo-scope-only input, memory-root discovery, exact graph/prompt/tool/task-brief paths, retained authoring evidence, signed apply contract, and output schemas from R-1 through R-6.
- [ ] AC-02: Collect reads only the configured repo-scope memory root, writes manifest plus copied note bodies under `tmp/memory-curation/`, records path, sha256, size, and mtime, and sanitizes every relative path.
- [ ] AC-03: Automated tests and smoke runs use fixture/temp memory roots only and never read or write the operator's real memory directories.
- [ ] AC-04: The graph is authored through the governed graph-authoring route with a committed task brief and retained report naming artifacts, precedent, lint command, smoke command, repairs, and blocked validation if any.
- [ ] AC-05: The final `graph.yaml` passes `yamlgraph graph lint`; the narrow smoke command runs on a fixture corpus and records its output in the FR or example evidence.
- [ ] AC-06: Per-note output is Pydantic-validated with exact enums for `verdict`, `audience`, and `staleness`; `redacted_draft` is non-empty iff `verdict=redact`; `staleness_evidence` is non-empty iff `staleness` is `dated` or `expired`.
- [ ] AC-07: Reconciliation proves count-in == count-out, every manifest path appears exactly once, zero unknown verdicts are emitted, and every `redact` row has a non-empty replacement draft.
- [ ] AC-08: No run stage writes outside `tmp/memory-curation/`; tests assert writes outside that directory are refused or impossible.
- [ ] AC-09: Real-corpus execution is blocked unless the provider boundary is local-only or the FR records explicit human approval naming the external provider/model and data premise.
- [ ] AC-10: Apply refuses unless the signed review artifact binds the manifest hash and disposition hash; the JSON input must match those hashes.
- [ ] AC-11: Apply refuses destructive changes when a live file's sha256 differs from the manifest, except for documented idempotent already-applied states; drift requires re-collection/re-judgement.
- [ ] AC-12: With a valid signed disposition on a fixture root, apply deletes `forget`, replaces `redact`, leaves `keep` untouched, prints a summary, and is idempotent on re-run.
- [ ] AC-13: Tests are tagged with a new `REQ-YG-XXX`; a matching capability file is added.
- [ ] AC-14: The first real run records only aggregate counts and non-sensitive validation metadata in the FR: manifest note count, kept/redacted/forgotten counts, audience counts, provider-boundary decision, and whether human sign-off was granted. Raw note bodies and redacted drafts remain under `tmp/` or the live memory root only.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-6 are folded into `feature-requests/FR-875-memory-corpus-curation-graph.md`. | GATE |
| C-2 | Do not invoke or re-run the judge while enforcing this FR. | GATE |
| C-3 | Any graph or prompt authoring must use the governed graph-authoring route and retain the FR-875 authoring record. | GATE |
| C-4 | The real memory corpus must not leave the machine via an external LLM provider without recorded human approval naming the provider/model and data premise. | GATE |
| C-5 | Tests and fixture smoke runs must use temp memory roots only; no automated validation may touch the operator's real memory store. | GATE |
| C-6 | Apply may mutate the live memory root only after signed, hash-bound human review and live-hash verification. | GATE |
| C-7 | No committed artifact may contain copied note bodies, redacted drafts, customer facts, hostnames, credentials, or raw memory-corpus content. | GATE |

Authority granted: after the required revisions are folded, enforcement may author and validate a repo-scope memory-curation YAMLGraph artifact through the governed route, render review-only dispositions under `tmp/memory-curation/`, and implement a hash-bound apply tool that performs human-approved local amnesia only against the live memory root.
