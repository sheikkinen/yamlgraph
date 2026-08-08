# Feature Request: FR-782 — User Self-Portrait Example (PersonalizationPortrait → Agent Context)

**Priority:** MEDIUM
**Type:** Feature (example)
**Status:** ENFORCED 2026-08-08 — all AC met; see Implementation Status below.
Judged 2026-08-08 — APPROVED WITH REVISIONS (R-1..R-6 folded below);
see FR-782-user-self-portrait-example.judgement.md
**Effort:** 1–2 days
**Requested:** 2026-08-08

**Prior art:** FR-781 (file-hook: launchd trigger + typed-graph pattern, Pattern B
deploy outside `~/Documents`); `~/Documents/src/control-plane/docs/plan-self-portrait.md`
(source plan: data-source inventory, entity categories, Wikidata resolution);
`examples/demos/diary-index` and `diary_digest` (scheduled synthesis precedent);
operator-calibration user-memory file (the hand-curated artifact this mechanizes).

## Summary

New example `examples/demos/self-portrait/`: extract the user's people,
topics, locations, and rhythms from Apple's PersonalizationPortrait
database (plus supplementary local DBs), enrich (Wikidata topic labels,
cross-referenced communication frequency), and synthesize a structured
**self-portrait whose primary consumer is an AI agent** — a
machine-loadable "who is this user" context artifact, with a
human-readable narrative as the secondary rendering.

## Ideal Result

Any agent session — Copilot, an NPC, a voice bot — begins already
knowing the user: inner circle, expertise, languages, home base, daily
rhythm, current interests and their drift. The knowledge comes from the
device's own behavioral record, not from what the user remembered to
write down. The hand-curated operator-calibration file becomes one
*section* (explicit corrections/preferences) layered on a generated
foundation that refreshes weekly and reports its own diff.

## Value Statement

The operator's thesis made concrete: software's primary consumers are
agents — and an agent that doesn't know its user re-asks questions the
device answered years ago.

**First consumer / first event (R-1):** a Copilot/agent session in this
workspace loading `~/.yamlgraph/self-portrait/self-portrait.json` (or
its `agent_briefing` section) as system context at session start —
first event is the first manual `yamlgraph graph run` after merge,
producing the portrait that replaces the hand-curated
operator-calibration foundation.

**Frozen agent JSON contract (R-1):** `self-portrait.json` top-level
fields, schema-stable: `schema_version`, `portrait_date`,
`generated_at`, `source_summary`, `identity`, `social_graph`,
`expertise`, `geography`, `rhythms`, `evolution`, `agent_briefing`,
`provenance`.

## Intent Boundary (explicit)

**Personal data is the core intent, not something to filter out.**
This is the user reading their own device's record of themselves and
handing it to their own agents. No redaction gates, no "public
version", no anonymization — those would delete the product. The
honest boundaries instead:

- Everything stays local: outputs land in a local folder, never
  committed (the repo ships the *pipeline*, a schema, and a synthetic
  fixture — never a real portrait).
- **Exact-payload consent gate before egress (R-2)**: a deterministic
  `build_synthesis_payload` step produces the exact JSON payload that
  `synthesize` will send, plus byte count and SHA-256 content hash.
  The `type: interrupt` node renders a compact human summary AND the
  path to a local file containing the full outbound payload; the
  resumed synthesis consumes that same payload byte-for-byte (tested
  by hash comparison). A consent gate that summarizes different data
  is not authorized — summary-only preview is compliance theatre
  (substance_over_presence).
- Provider selection is the standard `PROVIDER` mechanism — not a
  feature of this FR; the README merely notes that local providers
  exist for zero-egress preferences (documentation only, no recipe,
  no testing surface).
- The committed demo witness runs on the synthetic fixture DB, not on
  the author's real databases.

## Problem

1. Agent context about the user is hand-curated, stale, and partial
   (operator-calibration is ~40 lines written from memory; the device
   holds 14,993 named entities, 1,117 scored topics, 241 locations,
   communication frequency, and app rhythms).
2. The control-plane plan (`plan-self-portrait.md`) fully inventoried
   the data sources but stayed imperative-script-shaped; it is the
   inventory, this FR is the yamlgraph analysis: typed extraction →
   enrichment → LLM synthesis is exactly the three-layer pattern.
3. No existing example demonstrates SQLite extraction tools feeding an
   LLM synthesis node — a common real-world shape (local DB → typed
   rows → narrative + structured output).

## Data Sources

Primary: `PPSQLDatabase.db` (PersonalizationPortrait) —
`ne_records` (people/orgs/places/products/events with scores),
`tp_records` (Wikidata Q-ID topics with relevance), `loc_records`
(GPS + locality), `significant_contacts`, `sources` (provenance).

Supplementary (R-3 — **deferred, availability probes only under this
FR**): `knowledgeC.db` (app usage rhythms), Safari `History.db`,
`Calendar.sqlitedb`, WhatsApp `ChatStorage.sqlite`. FR-782 may probe
these for availability and render them as "absent/not configured"
sections only; implementing their parsers or message-volume
cross-reference requires a re-judged FR revision with exact synthetic
fixtures, schema assertions, and per-source tests. The primary DB
already includes significant contacts and provenance, so the
local-DB → typed rows → LLM synthesis pattern is provable without
bundling four orthogonal private-app schemas.

**TCC gate (named per the FR-781 heuristic):** these DBs live under
`~/Library` — the *executing binary* needs Full Disk Access; graph
fails fast with a named remediation when the DB is unreadable.
Re-fire semantics: none (pull-based); scheduled refresh is idempotent
by portrait-date.

## Proposed Solution

```
examples/demos/self-portrait/
  graph.yaml                    # authored via scripts/author.sh (C-2)
  prompts/synthesize_portrait.yaml
  tools.py                      # extract_* (typed rows), resolve_wikidata,
                                # build_synthesis_payload, render_outputs
  fixture_builder.py            # deterministic synthetic DB generator (R-4)
  fixture/PPSQLDatabase.db      # committed synthetic fixture (built by it)
  README.md                     # FDA gate, consent gate, weekly
                                # launchd recipe (FR-781 Pattern B)
```

Pipeline:

```
extract (SQLite, read-only URI mode)
  → Pydantic row models (R-6): EntityRow, TopicRow, LocationRow,
    ContactRow, ProvenanceRow, SourceSummary
    → enrich: Wikidata batch label resolution (Q-ID → label, cached
      to disk; offline = keep Q-IDs, degrade gracefully)
    → supplementary sources: availability probe → absent/not-configured
      descriptors only (R-3; no parsers under this FR)
  → build_synthesis_payload (R-2): deterministic exact JSON payload for
    synthesis + byte count + SHA-256 hash, written to the output dir
  → confirm_egress (type: interrupt, requires checkpointer):
      shows compact summary (counts per category, top-N, byte count,
      hash) AND the path to the full payload file; resume answer
      routed: yes → synthesize consuming that same payload
      byte-for-byte (hash-verified), anything else → abort node that
      renders extraction-only outputs and exits cleanly.
      Scheduled/headless runs pass --var auto_approve=true to route
      around the interrupt (explicit opt-in; interactive default asks)
  → synthesize (LLM, inline schema):
      identity, social_graph (inner circle w/ evidence), expertise,
      geography (home base, travel), rhythms, evolution (score decay =
      fading relevance), agent_briefing (the section written TO an
      agent: how to work with this user)
  → render:
      self-portrait.md        # narrative, for the human
      self-portrait.json      # typed, for agents (the primary output;
                              # frozen contract fields per R-1)
      portrait-diff.md        # vs previous run: new people, shifted
                              # interests, dropped locations
```

The `agent_briefing` section is the point: written in second person to
a future agent ("the user is…, prefers…, is currently deep in…"),
loadable as system context — the generated sibling of
operator-calibration.

Scheduled refresh: README documents the weekly
`StartCalendarInterval` install using the FR-781 Pattern B deploy
(this FR ships no installer — the file-hook README is the canonical
install guide; trigger-manifest mechanization stays in its seed).

## Constraints

- C-1: Graph + prompts authored solely via `scripts/author.sh`
  (governed route; FR-767 sentinel).
- C-2: All DB access read-only (`file:...?mode=ro` URI); tools never
  write outside the output directory.
- C-3: Real portrait outputs and real DBs never enter git; tests and
  demo witness run against the synthetic fixture only. Output dir
  default `~/.yamlgraph/self-portrait/` (outside repo).
- C-4: Wikidata resolution (R-5): batch ≤50 IDs/call, disk cache under
  the output directory keyed by Q-ID + language, no network on cache
  hit, offline/HTTP-failure degradation keeps Q-IDs, never fails the
  run. HTTP client is either Python standard library ONLY, or an
  exactly declared optional extra with full dependency governance
  (rationale, direct-import scan, CI surfaces) — no undeclared
  `requests`.
- C-5: Missing/unreadable DB (no FDA, different macOS version, absent
  schema) → fail fast with named remediation for primary; skip with
  logged notice for supplementary. Schema drift across macOS versions
  is expected: assert-and-adapt at the extraction boundary
  (the_one_law), not downstream — typed row models (R-6) with explicit
  failure tests for unknown categories, missing optional columns, and
  missing required tables; no broad `except`, no empty-section
  fallbacks. If the real schema demands framework behavior, stop and
  re-enter planning.
- C-6: Synthesis output is a Pydantic-validated inline schema; the
  JSON rendering is schema-stable (frozen R-1 contract) so agents can
  depend on it.
- C-7: No changes under `yamlgraph/` — pure example; if the framework
  needs a change, stop and split the FR.
- C-8: The consent interrupt is the default path; `auto_approve` is an
  explicit opt-in variable for headless/scheduled runs, never the
  default. The gate must prove exact outbound-payload identity (R-2):
  preview exposes the full payload (file path) + byte count + SHA-256;
  synthesis consumes the previewed payload byte-for-byte. Summary-only
  preview is compliance theatre (substance_over_presence).
- C-9: Synthetic fixture (R-4): built deterministically by a committed
  `fixture_builder.py` with obviously fake names/paths and minimum row
  coverage (person, org, location, product/topic, event/concept
  categories; topic Q-IDs; locations; significant contacts;
  provenance). A guard test asserts the committed fixture and demo
  witness contain no `~/Library` path, no real PersonalizationPortrait
  path, and no non-synthetic marker.

## Acceptance Criteria

Frozen by the judgement (AC-01 satisfied by this revision):

- [x] AC-01: The FR is revised to include a concrete first
      consumer/first event, the stable agent JSON contract, exact
      outbound-payload consent semantics, the primary-only
      supplementary-source phase boundary, fixture/no-real-data guard,
      Wikidata dependency/cache contract, and schema-drift row-model
      tests from R-1 through R-6.
- [x] AC-02: `examples/demos/self-portrait/graph.yaml` and
      `prompts/synthesize_portrait.yaml` are authored through
      `scripts/author.sh`; `tmp/draft-authoring-report.md` records
      graph lint, compile/validate, fixture smoke, and relevant test
      evidence.
- [x] AC-03: A deterministic synthetic `PPSQLDatabase.db` fixture or
      fixture-builder exists with fake people, organizations,
      locations, products/events/concepts, topic Q-IDs, location rows,
      significant contacts, and provenance rows; tests assert it
      contains no real PersonalizationPortrait path, `~/Library`
      source path, or non-synthetic marker.
- [x] AC-04: Extraction opens SQLite via read-only URI mode and
      returns Pydantic-validated row models for entities, topics,
      locations, significant contacts, provenance, and source summary;
      tests cover category mapping, unknown categories, missing
      optional columns, missing required primary tables,
      unreadable/missing primary DB with named FDA remediation, and
      output-dir confinement.
- [x] AC-05: Supplementary DBs are limited to availability probes and
      absent-source rendering under this FR; absent `knowledgeC.db`,
      Safari, Calendar, and WhatsApp sources do not fail the portrait
      and are represented as absent/not configured in the JSON and
      narrative.
- [x] AC-06: Wikidata resolution batches at no more than 50 Q-IDs per
      request, caches labels under the output directory, avoids
      network on cache hit, keeps Q-IDs when offline or labels are
      missing, and uses either standard-library HTTP or a
      declared/governed optional dependency.
- [x] AC-07: Consent gate defaults to interactive interrupt with
      checkpointer; it exposes the exact outbound synthesis payload or
      a local file containing it, plus byte count and content hash;
      resume "yes" proceeds using the same payload byte-for-byte, any
      other answer routes to extraction-only render and clean exit,
      and `auto_approve=true` is the only opt-in bypass.
- [x] AC-08: Synthesis uses an inline Pydantic schema with stable
      `self-portrait.json` fields: `schema_version`, `portrait_date`,
      `generated_at`, `source_summary`, `identity`, `social_graph`,
      `expertise`, `geography`, `rhythms`, `evolution`,
      `agent_briefing`, and `provenance`; narrative Markdown and JSON
      both render from the validated model.
- [x] AC-09: Diff mode is tested by a second run against a modified
      synthetic fixture and reports a new person, shifted topic score,
      and dropped location without reading prior real outputs.
- [x] AC-10: README documents the FDA/TCC gate with exact grant path
      and Pattern B deploy note, consent-gate semantics including
      exact payload preview and `auto_approve`, output directory
      default outside the repo, weekly launchd `StartCalendarInterval`
      reference to FR-781 Pattern B, local-provider note via standard
      `PROVIDER`, and the intent boundary that personal data is the
      product while real portraits are not committed.
- [x] AC-11: `demo-output.log` is regenerated from a grounded fixture
      run using a real LLM and synthetic data; it shows the
      auto-approved fixture witness plus one recorded interactive
      consent exchange, includes the output paths, and proves the
      committed fixture was run through a disposable copy.
- [x] AC-12: Every new or changed test carries an exact
      `@pytest.mark.req("REQ-YG-...")`; the capability registry is
      updated for the self-portrait example;
      `python scripts/req_coverage.py --strict` passes.
- [x] AC-13: Changelog fragment, FR implementation-status update, and
      diary reflection are included.

## Judgement (2026-08-08)

APPROVED WITH REVISIONS — R-1..R-6 folded above; full verdict in
`FR-782-user-self-portrait-example.judgement.md`. Enforcement gates:

- C-1 (GATE): authority active only now that R-1..R-6 are folded.
- C-2 (GATE): governed artifacts only via `scripts/author.sh`.
- C-3 (GATE): no real DBs/payloads/portraits/diffs in git; synthetic
  fixtures + disposable copies only.
- C-4 (GATE): consent must prove exact outbound-payload identity;
  summary-only interrupt or `auto_approve` default not authorized.
- C-5 (GATE): no changes under `yamlgraph/`; split a new FR if needed.
- C-6 (GATE): supplementary DB parsers/cross-reference out of scope
  without re-judgement.
- C-7 (GATE): any third-party dependency must be declared with full
  governance; undeclared imports not authorized.

Not authorized (from frozen scope): framework privacy/consent
machinery, new node types or CLI flags, public/redacted portrait mode,
personal-context MCP server, visualization UI, launchd installer
scripts beyond README Pattern B documentation, supplementary parsers,
egress of real personal data during tests or witness.

## Implementation Status (2026-08-08)

ENFORCED. Capability **CAP-223** / requirement **REQ-YG-584**;
31 tests in `tests/unit/test_fr782_self_portrait.py`.

**Delivered** (`examples/demos/self-portrait/`):

| File | Role |
|---|---|
| `graph.yaml`, `prompts/synthesize_portrait.yaml` | governed artifacts, authored via `scripts/author.sh` (two runs; report `tmp/draft-authoring-report.md`) |
| `models.py` | typed boundary — row models, `SchemaDriftError`, `DatabaseUnreadableError`, `ConsentPayloadMismatchError` |
| `extract.py` | read-only URI SQLite extraction, category mapping, supplementary probes |
| `wikidata.py` | stdlib `urllib`, ≤50-ID batches, disk cache, offline degradation |
| `portrait_io.py` | payload build/hash, identity verification, render, deterministic diff |
| `tools.py` | graph state adapters |
| `fixture_builder.py`, `fixture/PPSQLDatabase.db` | deterministic synthetic fixture (+ drifted variant for diff mode) |
| `README.md`, `demo-output.log` | FDA/consent/launchd docs; three-run grounded witness |

**Decisions taken during enforcement:**

1. **Tool loading via `module:`, not `path:`** — the graph-relative
   `path:` form loads the file without a parent package, so the tool
   module's relative imports fail in strict mode. Converted through a
   second `scripts/author.sh` run (never a manual edit), following the
   `examples/demos/file-hook/graph.yaml` precedent for hyphenated demo
   directories.
2. **Supplementary probe paths are home-relative (`~/Library/…`).**
   The first grounded run leaked the account name into the outbound
   payload through absolute probe paths — and the model duly inferred
   an identity from it. The probe list rides inside the consent payload,
   so the leak was cured at that boundary and pinned by
   `test_supplementary_probe_paths_never_carry_the_account_name`.
3. **Unknown `ne_records.category` raises** rather than being bucketed
   as "other" (C-5: no empty-section fallbacks). Missing *optional*
   columns degrade to `None`; missing *required* tables raise.
4. **Wikidata labels are whatever Wikidata says.** The source plan's
   guessed mappings (Q7913 = "artificial intelligence") did not survive
   contact with the API (it returns "Romanian"); the resolver reports
   the real label and never a curated one — unresolved topics keep bare
   Q-IDs.
5. **Diff is deterministic**, computed from a `payload-snapshot.json`
   written each run — the LLM never authors the drift report.
6. **W026 lint warning accepted**: the synthesis prompt declares seven
   top-level fields because R-1 froze that contract; splitting the call
   would break the agent-facing schema.

**Scope observed:** no changes under `yamlgraph/`; no new dependency; no
supplementary parsers; no real database, payload, or portrait committed.

## Alternatives Considered

1. **Imperative script in control-plane repo** (the source plan's
   default) — works once, but no typed boundary, no scheduled refresh
   discipline, no diff artifact; and the synthesis step is exactly
   what yamlgraph exists for.
2. **Hand-maintained operator file only** (status quo) — 40 lines vs
   15k entities; goes stale; misses drift (the portrait's evolution
   section is unwritable by hand).
3. **Full personal-context MCP server** — the portrait JSON as a live
   queryable surface; deferred — the artifact must exist and prove
   useful before it grows a server (would_you_use_this: the first
   consumer is a system-context load, which a file already serves).

## Related

- `~/Documents/src/control-plane/docs/plan-self-portrait.md` (source
  inventory; Wikidata mappings; SQL sketches)
- FR-781 + `docs/diary/diary-2026-08-08-the-control-plane-is-the-trigger-inventory.md`
  (trigger × graph × actuator frame; TCC-gate-first heuristic)
- `examples/demos/file-hook/README.md` (Pattern B deploy — canonical
  launchd install guide)
- `reference/interrupt-nodes.md` + `examples/demos/interrupt` (the
  consent-gate primitive: interrupt node, checkpointer, CLI resume
  loop in `yamlgraph/cli/graph_run_helpers.py`)
