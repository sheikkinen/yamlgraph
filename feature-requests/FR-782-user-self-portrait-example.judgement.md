# Judgement: FR-782 User Self-Portrait Example

**Prior art:** FR-781 (launchd/TCC precedent, Pattern B deploy); `examples/demos/diary_index` + `examples/diary_digest` (synthesis-pattern predecessors); control-plane `plan-self-portrait.md` (data inventory); `reference/interrupt-nodes.md` + CLI resume loop (consent-gate primitive). No rejected FR found occupying this territory — not a resurrection.

**Verdict:** APPROVED WITH REVISIONS - the self-portrait is a sound contrib/example, but authority activates only after the FR freezes the first consumer, exact egress-consent boundary, supplementary-source phase boundary, synthetic-fixture proof, and HTTP/cache dependency contract.

**Reviewed against:** `feature-requests/FR-782-user-self-portrait-example.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `feature-requests/FR-781-macos-file-hook-example.md`; `feature-requests/FR-781-macos-file-hook-example.judgement.md`; `examples/demos/file-hook/README.md`; `docs/diary/diary-2026-08-08-the-control-plane-is-the-trigger-inventory.md`; `/Users/sheikki/Documents/src/control-plane/docs/plan-self-portrait.md`; `examples/demos/diary_index/README.md`; `examples/demos/diary_index/graph.yaml`; `examples/demos/diary_index/tools.py`; `examples/diary_digest/README.md`; `examples/diary_digest/graph.yaml`; `examples/diary_digest/nodes/sources.py`; `reference/interrupt-nodes.md`; `reference/graph-yaml.md`; `examples/demos/interrupt/README.md`; `examples/demos/interrupt/interrupt-parent.yaml`; `examples/demos/interrupt/subgraphs/interrupt-child.yaml`; `tests/integration/test_subgraph_interrupt.py`; `yamlgraph/cli/graph_run_helpers.py`; `reference/scheduling-agents.md`; `pyproject.toml`.

## What is sound

The problem is real and repo-fit. The FR names a concrete data source with scale - 14,993 named entities, 1,117 topics, 241 locations, significant contacts, and provenance tables (`feature-requests/FR-782-user-self-portrait-example.md:67-77`, `/Users/sheikki/Documents/src/control-plane/docs/plan-self-portrait.md:18-27`). Its proposed shape - SQLite extraction, Wikidata enrichment, LLM synthesis, and rendered JSON/Markdown - matches the source plan's own architecture (`/Users/sheikki/Documents/src/control-plane/docs/plan-self-portrait.md:53-147`) and the repo's three-layer doctrine: keep config and orchestration declarative, validate outputs with types, and demonstrate with examples (`.github/copilot-instructions.md:208-218`).

The strategic classification is **Contrib/example**, not a framework primitive. Existing abstractions are sufficient: Python tools already feed map/LLM/persistence examples (`examples/demos/diary_index/graph.yaml:40-80`, `examples/demos/diary_index/tools.py:19-32`, `examples/diary_digest/graph.yaml:61-145`), scheduled synthesis exists as `diary_digest` (`examples/diary_digest/README.md:1-17`), and interrupt nodes already pause and resume with checkpointers (`reference/interrupt-nodes.md:52-58`, `reference/graph-yaml.md:645-671`, `yamlgraph/cli/graph_run_helpers.py:203-223`). The FR's C-7 "no changes under `yamlgraph/`" boundary is therefore correct (`feature-requests/FR-782-user-self-portrait-example.md:166-167`).

The privacy stance is unusually honest: personal data is the product, not noise to anonymize, while the repo commits only the pipeline/schema/synthetic fixture and keeps real outputs local (`feature-requests/FR-782-user-self-portrait-example.md:41-63`). That aligns with the file-hook/trigger precedent: FR-781 documented the macOS TCC trap and Pattern B deploy outside protected locations (`examples/demos/file-hook/README.md:61-103`, `examples/demos/file-hook/README.md:125-139`), and the control-plane diary distilled the general rule that every trigger/actuator surface must name its TCC gate and re-fire semantics before implementation (`docs/diary/diary-2026-08-08-the-control-plane-is-the-trigger-inventory.md:68-83`).

Prior art is sufficiently identified but not yet sufficiently folded. FR-781 is the right launchd/TCC precedent (`feature-requests/FR-782-user-self-portrait-example.md:9-13`), `diary_index` and `diary_digest` are valid synthesis-pattern predecessors (`examples/demos/diary_index/README.md:5-18`, `examples/diary_digest/README.md:1-17`), and the control-plane plan supplies raw data inventory (`/Users/sheikki/Documents/src/control-plane/docs/plan-self-portrait.md:16-50`). No rejected FR was found in the consumed evidence occupying this territory; the proposal is not a resurrection of a rejected plan.

## Required revisions

### R-1: Add the first consumer and freeze the agent JSON contract

Fold an explicit `**First consumer / first event:**` line into the FR. The repo template says an FR that cannot name who uses this first and at what concrete moment is `growth_as_default` (`feature-requests/TEMPLATE.md:8-10`). FR-782 gestures at "Any agent session" and "Copilot, an NPC, a voice bot" (`feature-requests/FR-782-user-self-portrait-example.md:25-33`) but does not name the first consumer or event.

State the first consumer as a concrete agent-context load of `self-portrait.json` or `agent_briefing`, including the path the agent reads and the first run moment. Freeze the machine-readable JSON contract with at least: `schema_version`, `portrait_date`, `generated_at`, `source_summary`, `identity`, `social_graph`, `expertise`, `geography`, `rhythms`, `evolution`, `agent_briefing`, and `provenance`. The FR currently says JSON is "for agents" and `agent_briefing` is "loadable as system context" (`feature-requests/FR-782-user-self-portrait-example.md:131-141`), but that is not yet a mechanically stable consumer contract.

### R-2: Make consent prove exact outbound-payload identity

Replace the current "compact summary" consent design with an exact payload-preview contract. The FR promises an interrupt showing exactly what will be sent to the LLM (`feature-requests/FR-782-user-self-portrait-example.md:52-57`), but the proposed node shows only counts, top-N, and byte estimate (`feature-requests/FR-782-user-self-portrait-example.md:119-123`). That contradiction matters because personal data egress is the central boundary, and repo doctrine rejects presence-only gates as compliance theatre (`.github/copilot-instructions.md:87-90`, `.github/copilot-instructions.md:110`).

Fold in a deterministic `build_synthesis_payload` step that produces the exact JSON payload later passed to `synthesize`, plus byte count and content hash. The interrupt may render a compact human summary, but it must also expose the full outbound payload or a local file path containing it; the resumed synthesis path must consume that same payload byte-for-byte. Add tests that compare the previewed payload/hash to the payload passed into synthesis; a consent gate that summarizes different data is not authorized.

### R-3: Freeze supplementary DBs as deferred, absent-source descriptors

Narrow this FR to the primary `PPSQLDatabase.db` extraction plus Wikidata topic resolution. The FR lists `knowledgeC.db`, Safari History, Calendar, and WhatsApp as supplementary phase-2 enrichment (`feature-requests/FR-782-user-self-portrait-example.md:86-89`) and proposes cross-reference enrichment (`feature-requests/FR-782-user-self-portrait-example.md:116-118`), but the acceptance criteria only test absence handling (`feature-requests/FR-782-user-self-portrait-example.md:186-188`). There is no committed schema, synthetic fixture, or measurable parser contract for those four additional databases.

Fold the phase boundary into the FR: under FR-782, supplementary sources may be probed for availability and rendered as "absent/not configured" sections only. Implementing parsers for `knowledgeC.db`, Safari, Calendar, WhatsApp, or message-volume cross-reference is not authorized unless the FR is revised again with exact synthetic fixtures, schema assertions, and tests for each source. The primary DB already includes significant contacts and provenance (`feature-requests/FR-782-user-self-portrait-example.md:81-84`), so the example can prove the local-DB -> typed rows -> LLM synthesis pattern without bundling four orthogonal Apple/private-app schemas.

### R-4: Define the synthetic fixture generator and no-real-data guard

Add a deterministic fixture contract. The FR says the repo ships a synthetic `fixture/PPSQLDatabase.db` (`feature-requests/FR-782-user-self-portrait-example.md:99-107`) and real portraits never enter git (`feature-requests/FR-782-user-self-portrait-example.md:49-63`, `feature-requests/FR-782-user-self-portrait-example.md:154-156`), but it does not say how the fixture is generated, what rows it must contain, or how enforcement prevents accidental real-data commits.

Fold in either a committed fixture-builder script or a test-local generator that creates the same schema deterministically. Require minimum synthetic rows for person, organization, location, product/topic coverage, topic Q-IDs, locations, significant contacts, and provenance, using obviously fake names and paths. Add a test that the committed fixture and demo witness contain no `~/Library` paths, no real PersonalizationPortrait path, and no non-synthetic marker. The demo witness must run on a disposable copy so the committed fixture is unconsumed, preserving the FR's stated boundary (`feature-requests/FR-782-user-self-portrait-example.md:203-206`).

### R-5: Freeze the Wikidata HTTP, cache, and dependency surface

Specify the resolver implementation boundary before enforcement. The source plan sketches `requests.get` for Wikidata (`/Users/sheikki/Documents/src/control-plane/docs/plan-self-portrait.md:191-205`), but `requests` is not a core dependency in the current project dependency list (`pyproject.toml:24-37`). FR-782 correctly requires batch size, disk cache, and offline degradation (`feature-requests/FR-782-user-self-portrait-example.md:157-158`, `feature-requests/FR-782-user-self-portrait-example.md:180-182`), but it does not name the HTTP client, cache path, TTL/invalidation policy, or dependency-governance surface.

Fold in one of two choices: use only the Python standard library for Wikidata HTTP, or declare the exact optional dependency/extra and governance updates required for any third-party HTTP client. The cache must live under the output directory, be keyed by Q-ID plus language, avoid network on cache hits, and preserve Q-IDs when offline. Tests must cover batches of 50 and 51 IDs, cache hit with network forbidden, HTTP failure degradation, and labels missing in the requested language.

### R-6: Make schema drift and typed extraction testable at the boundary

Tighten "assert-and-adapt at the extraction boundary" into concrete row models and failure tests. FR-782 names schema drift as expected (`feature-requests/FR-782-user-self-portrait-example.md:159-163`) and asks for typed rows (`feature-requests/FR-782-user-self-portrait-example.md:177-179`), but it does not name the Pydantic models, category mapping behavior, or the exact failures for missing columns/tables. The repo doctrine requires typed outputs and loud errors rather than silent fallbacks (`.github/copilot-instructions.md:216-220`).

Fold in Pydantic models for extracted people/entities, topics, locations, significant contacts, provenance, source summaries, consent payload, synthesis output, and portrait diff. Tests must cover unknown entity categories, missing optional columns, missing required primary tables, unreadable primary DB/FDA remediation, supplementary absence, and output-dir confinement. If implementation discovers the real macOS schema differs from the source plan enough to require new framework behavior, stop and re-enter planning; do not hide it behind broad `except` or empty-section fallbacks.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revisions to `feature-requests/FR-782-user-self-portrait-example.md` folding R-1 through R-6 |
| D-2 | New governed example artifacts under `examples/demos/self-portrait/`: `graph.yaml`, `prompts/synthesize_portrait.yaml`, `tools.py`, README, synthetic fixture or fixture builder, and `demo-output.log` |
| D-3 | Tests for primary SQLite extraction, read-only URI access, row models, Wikidata batch/cache/offline behavior, consent interrupt/resume payload identity, rendering, diff mode, missing DB/FDA errors, supplementary absent descriptors, and no-real-data guard |
| D-4 | Capability registry entry, requirement-tagged tests, changelog fragment, FR implementation-status update, and diary reflection |
| D-5 | README documentation for FDA/TCC grant path, consent semantics, output locations, synthetic fixture witness, weekly launchd Pattern B reference, and local-provider note via standard `PROVIDER` |

Not authorized: changes under `yamlgraph/`; new node types, new CLI flags, or framework-level privacy/consent machinery; real PersonalizationPortrait databases or real portrait outputs in git; public/redacted portrait mode; a live personal-context MCP server; visualization/social-graph UI; launchd installer scripts beyond README Pattern B documentation; supplementary DB parsers for `knowledgeC.db`, Safari, Calendar, WhatsApp, or message-volume enrichment; undeclared third-party HTTP dependencies; egress of real personal data during tests or demo witness; manual edits to governed `graph.yaml` or `prompts/*.yaml` outside `scripts/author.sh`.

## Revised acceptance criteria

- [ ] AC-01: The FR is revised to include a concrete first consumer/first event, the stable agent JSON contract, exact outbound-payload consent semantics, the primary-only supplementary-source phase boundary, fixture/no-real-data guard, Wikidata dependency/cache contract, and schema-drift row-model tests from R-1 through R-6.
- [ ] AC-02: `examples/demos/self-portrait/graph.yaml` and `prompts/synthesize_portrait.yaml` are authored through `scripts/author.sh`; `tmp/draft-authoring-report.md` records graph lint, compile/validate, fixture smoke, and relevant test evidence.
- [ ] AC-03: A deterministic synthetic `PPSQLDatabase.db` fixture or fixture-builder exists with fake people, organizations, locations, products/events/concepts, topic Q-IDs, location rows, significant contacts, and provenance rows; tests assert it contains no real PersonalizationPortrait path, `~/Library` source path, or non-synthetic marker.
- [ ] AC-04: Extraction opens SQLite via read-only URI mode and returns Pydantic-validated row models for entities, topics, locations, significant contacts, provenance, and source summary; tests cover category mapping, unknown categories, missing optional columns, missing required primary tables, unreadable/missing primary DB with named FDA remediation, and output-dir confinement.
- [ ] AC-05: Supplementary DBs are limited to availability probes and absent-source rendering under this FR; absent `knowledgeC.db`, Safari, Calendar, and WhatsApp sources do not fail the portrait and are represented as absent/not configured in the JSON and narrative.
- [ ] AC-06: Wikidata resolution batches at no more than 50 Q-IDs per request, caches labels under the output directory, avoids network on cache hit, keeps Q-IDs when offline or labels are missing, and uses either standard-library HTTP or a declared/governed optional dependency.
- [ ] AC-07: Consent gate defaults to interactive interrupt with checkpointer; it exposes the exact outbound synthesis payload or a local file containing it, plus byte count and content hash; resume `"yes"` proceeds using the same payload byte-for-byte, any other answer routes to extraction-only render and clean exit, and `auto_approve=true` is the only opt-in bypass.
- [ ] AC-08: Synthesis uses an inline Pydantic schema with stable `self-portrait.json` fields: `schema_version`, `portrait_date`, `generated_at`, `source_summary`, `identity`, `social_graph`, `expertise`, `geography`, `rhythms`, `evolution`, `agent_briefing`, and `provenance`; narrative Markdown and JSON both render from the validated model.
- [ ] AC-09: Diff mode is tested by a second run against a modified synthetic fixture and reports a new person, shifted topic score, and dropped location without reading prior real outputs.
- [ ] AC-10: README documents the FDA/TCC gate with exact grant path and Pattern B deploy note, consent-gate semantics including exact payload preview and `auto_approve`, output directory default outside the repo, weekly launchd `StartCalendarInterval` reference to FR-781 Pattern B, local-provider note via standard `PROVIDER`, and the intent boundary that personal data is the product while real portraits are not committed.
- [ ] AC-11: `demo-output.log` is regenerated from a grounded fixture run using a real LLM and synthetic data; it shows the auto-approved fixture witness plus one recorded interactive consent exchange, includes the output paths, and proves the committed fixture was run through a disposable copy.
- [ ] AC-12: Every new or changed test carries an exact `@pytest.mark.req("REQ-YG-...")`; the capability registry is updated for the self-portrait example; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-13: Changelog fragment, FR implementation-status update, and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-6 are folded into `feature-requests/FR-782-user-self-portrait-example.md`. | GATE |
| C-2 | Governed graph and prompt artifacts must be created or changed only through `scripts/author.sh`; manual edits to `graph.yaml` or `prompts/*.yaml` are not authorized. | GATE |
| C-3 | Real personal databases, real extracted payloads, real portrait JSON/Markdown, and real output diffs must not enter git; tests and demo witness must use only synthetic fixtures and disposable copies. | GATE |
| C-4 | The consent boundary must prove exact outbound-payload identity; a summary-only interrupt or an `auto_approve` default is not authorized. | GATE |
| C-5 | No changes under `yamlgraph/` are authorized. If framework changes are needed, stop and split a new FR. | GATE |
| C-6 | Supplementary DB parsers and cross-reference enrichment beyond absent-source descriptors are out of scope unless the FR is re-judged with exact fixtures and tests for those sources. | GATE |
| C-7 | Any new third-party dependency for Wikidata or fixture/render tooling must be declared in the appropriate optional extra with dependency-rationale/direct-import governance; undeclared imports are not authorized. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may build the primary PersonalizationPortrait self-portrait example, its exact consent gate, synthetic fixture, Wikidata resolver, render/diff outputs, and the tests/docs/governance artifacts listed in the frozen scope.
