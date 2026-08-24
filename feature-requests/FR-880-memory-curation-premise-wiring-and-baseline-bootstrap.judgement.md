# Judgement: FR-880 Memory Curation Premise Wiring & Baseline Bootstrap

**Verdict:** APPROVED WITH REVISIONS - the integration defect is real and the proposed fix is the minimal path, but authority activates only after the authoring brief exists in the closed record and the graph-path failure/bootstrap evidence is made mechanically checkable.

**Reviewed against:** `feature-requests/FR-880-memory-curation-premise-wiring-and-baseline-bootstrap.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/doctrine.md`; `feature-requests/TEMPLATE.md`; `ARCHITECTURE.md`; `feature-requests/FR-875-memory-corpus-curation-graph.md`; `feature-requests/FR-878-reversible-amnesia-tiered-approval.md`; `feature-requests/FR-878-reversible-amnesia-tiered-approval.judgement.md`; `feature-requests/FR-877-memory-curation-staleness-advisory.md`; `feature-requests/FR-877-memory-curation-staleness-advisory.judgement.md`; `feature-requests/FR-874-cross-device-agent-memory-sync.md`; `feature-requests/FR-767-graph-authoring-sole-route.md`; `examples/memory-curation/graph.yaml`; `examples/memory-curation/nodes/graph_nodes.py`; `examples/memory-curation/nodes/reconcile.py`; `examples/memory-curation/apply.py`; `examples/memory-curation/advisory.py`; `examples/memory-curation/README.md`; `tests/unit/test_memory_curation.py`; `tests/unit/test_memory_curation_tiers.py`; `capabilities/CAP-247-memory-corpus-curation.yaml`; `docs/diary/diary-2026-08-24-the-note-that-judged-its-own-transport.md`; `docs/diary/diary-2026-08-24-the-baseline-that-plagiarized.md`. No author chat narrative was consumed.

**Prior art:** FR-875 (parent graph), FR-878 (exact premise/tier
contract), FR-877 (marker/advisory), FR-874 (REJECTED transport), and
FR-767 (sole authoring route) are dispositioned throughout. Other noun
collisions have no territorial overlap with this composition correction.

## What is sound

The defect is real, current, and composition-shaped. FR-878 required `premise_kind: hygiene | export_publication` to be explicit metadata, never substring-matched from prose, with missing/unknown premise failing closed to tier 3 (`feature-requests/FR-878-reversible-amnesia-tiered-approval.md:106-110`). The current reconcile/apply code implements that boundary: reconcile accepts and validates `--premise-kind` (`examples/memory-curation/nodes/reconcile.py:75-76`, `100-104`, `142-144`), while apply computes tier 3 whenever the disposition's `premise_kind` is not `hygiene` (`examples/memory-curation/apply.py:36-38`). But the graph still declares only `memory_root` and `audience_premise` as inputs (`examples/memory-curation/graph.yaml:11-13`) and the reconcile node passes only `out_dir`, `manifest_path`, and `dispositions` (`examples/memory-curation/graph.yaml:80-88`). The Python graph glue likewise invokes `reconcile.py` without `--premise-kind` (`examples/memory-curation/nodes/graph_nodes.py:42-52`). FR-880 correctly identifies that component-green/system-red gap (`feature-requests/FR-880-memory-curation-premise-wiring-and-baseline-bootstrap.md:40-45`).

The proposed transport is architecturally aligned and appropriately narrow. Adding a graph state variable and passing it into Python glue preserves the YAMLGraph three-layer pattern: graph state carries orchestration data, Python nodes handle side-effectful command execution, and Pydantic/argparse validation remains at the deterministic reconcile boundary (`ARCHITECTURE.md:38-70`; `feature-requests/FR-880-memory-curation-premise-wiring-and-baseline-bootstrap.md:87-103`). It also obeys the graph-authoring route requirement for `graph.yaml` changes (`.github/copilot-instructions.md:15`; `.github/skills/graph-authoring/doctrine.md:91-107`) and does not expand into prompt changes (`feature-requests/FR-880-memory-curation-premise-wiring-and-baseline-bootstrap.md:151-154`).

The live bootstrap belongs in this FR rather than a separate feature. FR-877 made `.curation-state.json` the post-apply live baseline and treats absent marker plus non-empty corpus as "never curated" (`feature-requests/FR-877-memory-curation-staleness-advisory.md:48-54`, `58-66`, `76-81`). FR-875's implementation record confirms a hygiene run was applied before that marker existed (`feature-requests/FR-875-memory-corpus-curation-graph.md:283-292`), while its header still says the first real-corpus run is pending (`feature-requests/FR-875-memory-corpus-curation-graph.md:3-5`). Wiring `premise_kind` first, then running one real hygiene pass to create the missing marker, is the minimal path back to the ideal state described by FR-880 (`feature-requests/FR-880-memory-curation-premise-wiring-and-baseline-bootstrap.md:53-63`). Strategic classification: **contrib/example operational correction to CAP-247**, not a YAMLGraph framework primitive.

## Required revisions

### R-1: Add the committed authoring brief before authority activates

Create and cite `feature-requests/authoring-briefs/fr-880-premise-wiring-brief.md` before enforcement runs `scripts/author.sh`. FR-880 names that path as the sole-route input (`feature-requests/FR-880-memory-curation-premise-wiring-and-baseline-bootstrap.md:72-80`), but the closed record does not contain the brief. Graph-authoring doctrine requires FR-bound task briefs to live committed under `feature-requests/authoring-briefs/` and be cited by the governing FR (`.github/skills/graph-authoring/doctrine.md:21-30`); the adapter route is artifact-closed and must not infer target details from hidden chat narrative (`.github/skills/graph-authoring/doctrine.md:91-99`). Fold this by adding the brief with the exact target artifacts, the required `premise_kind` wiring, the no-prompt-change constraint, and the lint/smoke expectations; then update FR-880 to state the brief is present, not merely planned.

### R-2: Make graph-path absence and invalid-premise behavior testable before apply

Tighten the failure witness. FR-880 says missing/unknown premise values fail before apply (`feature-requests/FR-880-memory-curation-premise-wiring-and-baseline-bootstrap.md:111-112`), but the current lower boundary can also produce a disposition with no `premise_kind` and let apply classify it as tier 3 (`examples/memory-curation/nodes/reconcile.py:100-104`; `examples/memory-curation/apply.py:36-38`). That is correct for direct reconcile/apply callers, but it does not prove the graph path requires the new runtime variable. Fold this by requiring tests or smokes that exercise the graph/glue path, not only `reconcile.py` directly: `premise_kind=hygiene` and `premise_kind=export_publication` must survive unchanged into `disposition.json`; omitting the graph variable must fail with a clear graph/state/reconcile error before apply is invoked; and an unknown value must be rejected by reconcile validation, never normalized or defaulted.

### R-3: Record the live bootstrap as bounded evidence, with a durable stop artifact for tier 2/3

Make the real-run acceptance mechanically auditable without committing memory content. FR-880 requires one Vertex hygiene run, reading every non-keep row, applying tier 0/1 under standing delegation, stopping for tier 2, treating tier 3 as a witness failure, then proving the advisory is silent at threshold 1 (`feature-requests/FR-880-memory-curation-premise-wiring-and-baseline-bootstrap.md:115-137`, `165-171`). The shape is sound, but "read every non-keep row" and "present one structured human question" need a durable artifact or FR record. Fold this by requiring the implementation record to include the exact command shape, provider, exact hygiene premise text from FR-875 run 2 (`feature-requests/FR-875-memory-corpus-curation-graph.md:283-285`), manifest/disposition hashes, aggregate verdict/audience/staleness counts, tier, action taken, and a bounded list of non-keep relative paths with draft byte counts and an explicit read-in-full attestation. If tier 2 or 3 occurs, enforcement must write a gitignored structured decision artifact such as `tmp/memory-curation/fr-880-human-question.md`, record that path in the FR, and stop without claiming marker bootstrap success. No raw note bodies, redacted drafts, archive payloads, customer facts, hostnames, or credentials may be committed.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-880-memory-curation-premise-wiring-and-baseline-bootstrap.md` folding R-1 through R-3 |
| D-2 | New committed task brief `feature-requests/authoring-briefs/fr-880-premise-wiring-brief.md` |
| D-3 | Governed graph edit to `examples/memory-curation/graph.yaml` through `scripts/author.sh` only |
| D-4 | Adjacent glue edit to `examples/memory-curation/nodes/graph_nodes.py` passing exact `--premise-kind` |
| D-5 | Fixture/temp-root tests proving graph/glue premise transport, invalid/missing premise failure, and no real-memory reads |
| D-6 | `examples/memory-curation/README.md` usage and fixture smoke commands updated to require `premise_kind` and explain policy-vs-judgement roles |
| D-7 | `capabilities/CAP-247-memory-corpus-curation.yaml` amended only if REQ-YG-620..622 do not already cover the transport witness; matching test tags either way |
| D-8 | One bounded live Vertex hygiene bootstrap record in FR-880 plus FR-875 header/status correction after success |
| D-9 | Diary reflection on the component-green/system-red metadata-transport trap |

Not authorized: prompt YAML changes; changing the note-judgement schema beyond adding/carrying `premise_kind`; fuzzy inference from `audience_premise`; defaulting missing premise to hygiene; modifying judge/review/graph-authoring doctrine, hooks, CI, or YAMLGraph framework primitives; rebuilding FR-874 transport; committing raw memory note bodies, redacted drafts, archive payloads, customer facts, hostnames, credentials, or live memory content; automated tests against the operator's real memory store; applying tier 2/3 dispositions without the required human decision artifact.

## Revised acceptance criteria

- [ ] AC-01: FR-880 is revised to fold R-1 through R-3 and records that the committed authoring brief exists before the graph-authoring adapter is run.
- [ ] AC-02: `feature-requests/authoring-briefs/fr-880-premise-wiring-brief.md` exists and names the graph, glue, README, tests, no-prompt-change constraint, required `premise_kind` values, and lint/smoke expectations.
- [ ] AC-03: `examples/memory-curation/graph.yaml` is modified only via `scripts/author.sh`; the retained `tmp/draft-authoring-report.md` has the required `Artifacts`, `Precedent`, `Validation`, `Repairs`, and `Blocked validation` headings and lists the authored paths.
- [ ] AC-04: `graph.yaml` declares required `premise_kind` state and passes `{state.premise_kind}` explicitly to the reconcile node; `audience_premise` remains a separate required input and no prompt YAML changes are made.
- [ ] AC-05: `examples/memory-curation/nodes/graph_nodes.py` invokes `reconcile.py --premise-kind <value>` using the exact graph state value; it performs no substring inference and supplies no hygiene default.
- [ ] AC-06: Fixture/temp-root tests or smokes prove `premise_kind=hygiene` and `premise_kind=export_publication` appear unchanged in final `disposition.json` through the graph/glue path.
- [ ] AC-07: Fixture/temp-root tests or smokes prove omitting the graph variable fails before apply is invoked, and an unknown value is rejected by reconcile validation.
- [ ] AC-08: `yamlgraph graph lint examples/memory-curation/graph.yaml`, the 3-note fixture smoke with both `premise_kind` and `audience_premise`, and the targeted memory-curation unit suite pass; all tests are tagged to CAP-247 coverage and no automated test reads the real memory store.
- [ ] AC-09: README run commands require both `premise_kind` and `audience_premise`, explaining that `premise_kind` controls approval tier while `audience_premise` grounds semantic judgement.
- [ ] AC-10: After fixture validation, one real Vertex hygiene run is executed with the FR-875 run-2 hygiene premise; FR-880 records command shape, provider, hashes, aggregate counts, tier, non-keep relative paths plus draft byte counts/read attestation, action taken, and any deviation without committing raw memory content.
- [ ] AC-11: If the real run is tier 0/1, apply may proceed under FR-878; `.curation-state.json` must exist afterward and `memory-advisory.sh` at threshold 1 must emit no advisory line, with marker count equal to the live corpus predicate. If the run is tier 2/3, enforcement must stop, write a structured `tmp/` human-decision artifact, and not claim bootstrap success.
- [ ] AC-12: FR-875's stale status header and FR-880's implementation record match observed reality after the bootstrap outcome; diary reflection records the composition trap and the end-to-end metadata-transport witness.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-3 are folded into FR-880 and the committed authoring brief exists. | GATE |
| C-2 | Any `graph.yaml` or prompt-governed edit must go through `scripts/author.sh`; unsentineled manual graph edits are forbidden. | GATE |
| C-3 | Missing or unknown premise must never be normalized to hygiene; graph/glue/reconcile must fail closed before apply for those fixture witnesses. | GATE |
| C-4 | Automated validation uses temp/fixture roots only; no test may read, archive, restore, or mutate the operator's real memory store. | GATE |
| C-5 | The live Vertex run may commit only aggregate metadata and bounded relative-path evidence; no raw note bodies, drafts, archive payloads, customer facts, hostnames, credentials, or live memory content may be committed. | GATE |
| C-6 | Tier 2 or tier 3 real-run output stops enforcement at a structured human-decision artifact; no apply or marker-bootstrap success may be claimed. | GATE |
| C-7 | Do not invoke or re-run the judge skill, judge adapter, judge graph, YAMLGraph judge routes, or review routes while enforcing this judgement. | GATE |
| C-8 | No CI, hook, doctrine, framework-primitive, prompt-template, or FR-874 transport changes are authorized by this FR. | GATE |

Authority granted: after the required revisions are folded, enforcement may wire `premise_kind` through the memory-curation graph and glue, validate the fixture graph path, update README/CAP/FR records as needed, and run one bounded machine-local Vertex hygiene bootstrap to establish the FR-877 live baseline.
