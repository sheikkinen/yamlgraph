# Feature Request: FR-782 — User Self-Portrait Example (PersonalizationPortrait → Agent Context)

**Priority:** MEDIUM
**Type:** Feature (example)
**Status:** Proposed
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

## Intent Boundary (explicit)

**Personal data is the core intent, not something to filter out.**
This is the user reading their own device's record of themselves and
handing it to their own agents. No redaction gates, no "public
version", no anonymization — those would delete the product. The
honest boundaries instead:

- Everything stays local: outputs land in a local folder, never
  committed (the repo ships the *pipeline*, a schema, and a synthetic
  fixture — never a real portrait).
- Synthesis sends extracted data to the configured LLM provider like
  every other graph; `provider: lmstudio` documented as the fully
  local option for those who want zero egress.
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

Supplementary (phase-2 enrichment, behind availability checks):
`knowledgeC.db` (app usage rhythms), Safari `History.db`,
`Calendar.sqlitedb`, WhatsApp `ChatStorage.sqlite` (message volume per
contact).

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
  tools.py                      # extract_entities, extract_topics,
                                # extract_locations, resolve_wikidata,
                                # cross_reference, render_outputs
  fixture/PPSQLDatabase.db      # small synthetic fixture (generated)
  README.md                     # FDA gate, local-provider option,
                                # weekly launchd recipe (FR-781 Pattern B)
```

Pipeline:

```
extract (SQLite, read-only URI mode)
  → {people[], topics[], locations[], contacts[], provenance{}}
    → enrich: Wikidata batch label resolution (Q-ID → label, cached
      to disk; offline = keep Q-IDs, degrade gracefully)
    → cross-reference where supplementary DBs are readable
  → synthesize (LLM, inline schema):
      identity, social_graph (inner circle w/ evidence), expertise,
      geography (home base, travel), rhythms, evolution (score decay =
      fading relevance), agent_briefing (the section written TO an
      agent: how to work with this user)
  → render:
      self-portrait.md        # narrative, for the human
      self-portrait.json      # typed, for agents (the primary output)
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
- C-4: Wikidata resolution is batch (≤50 IDs/call), disk-cached, and
  optional — offline runs degrade to Q-IDs, never fail.
- C-5: Missing/unreadable DB (no FDA, different macOS version, absent
  schema) → fail fast with named remediation for primary; skip with
  logged notice for supplementary. Schema drift across macOS versions
  is expected: assert-and-adapt at the extraction boundary
  (the_one_law), not downstream.
- C-6: Synthesis output is a Pydantic-validated inline schema; the
  JSON rendering is schema-stable so agents can depend on it.
- C-7: No changes under `yamlgraph/` — pure example; if the framework
  needs a change, stop and split the FR.

## Acceptance Criteria

- [ ] AC-01: `tools.py` extraction functions return typed rows from a
      fixture `PPSQLDatabase.db`; tests cover entity categories,
      topic scores, location clustering (REQ tag per registry).
- [ ] AC-02: Wikidata resolver: batch ≤50, disk cache hit avoids
      network (tested with mocked HTTP), offline degradation keeps
      Q-IDs.
- [ ] AC-03: Read-only enforcement tested: extraction against a
      read-only fixture copy succeeds; no write side effects outside
      the output dir.
- [ ] AC-04: Missing-DB path: primary DB absent → fails fast naming
      the FDA remediation; supplementary absent → portrait still
      renders with the section marked absent.
- [ ] AC-05: Synthesis schema includes `agent_briefing`; JSON output
      validates against the schema; narrative + JSON + diff all
      rendered.
- [ ] AC-06: Diff mode: second run against modified fixture reports
      new person / shifted topic / dropped location.
- [ ] AC-07: graph.yaml + prompt authored via `scripts/author.sh`,
      lint clean, smoke on fixture; `tmp/draft-authoring-report.md`
      retained as evidence.
- [ ] AC-08: `demo-output.log` from a grounded fixture run (real LLM,
      synthetic data); committed fixture unconsumed.
- [ ] AC-09: README: FDA gate with exact grant path, lmstudio
      local-provider recipe, weekly launchd install referencing
      FR-781 Pattern B, and the intent boundary stated (personal data
      is the product; pipeline is shared, portraits are not).
- [ ] AC-10: Capability registry entry + REQ tags;
      `req_coverage.py --strict` passes; changelog fragment + diary
      reflection included.

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
