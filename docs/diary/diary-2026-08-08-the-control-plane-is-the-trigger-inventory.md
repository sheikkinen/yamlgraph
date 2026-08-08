# Diary 2026-08-08 — The Control Plane Is the Trigger Inventory

**Context:** After FR-781 shipped and the file hook went live in
`~/scheduled-yamlgraphs/`, a survey of the sibling repo
`~/Documents/src/control-plane/` — a macOS automation-surface
inventory (AppleScript, URL schemes, Spotlight, FSEvents, AX,
EventKit, launchd, Shortcuts, distributed notifications) built around
WhatsApp AX automation.

## The realization: two repos, one architecture, neither knew it

FR-781 wired exactly ONE trigger surface (launchd `WatchPaths`) to one
graph and treated the wiring as demo-specific. The control-plane repo
has already enumerated the *whole space* of trigger surfaces — and its
own integration decision tree is the missing general statement:

```
observe changes?  → FSEvents / notifications / AXObserver   = graph TRIGGERS
read data?        → Spotlight / plists / AppleScript        = graph TOOLS (input)
trigger action?   → URL scheme / AppleScript / Shortcuts    = graph TOOLS (actuation)
```

yamlgraph sits precisely in the middle: **trigger → typed graph →
actuator**. The file-hook demo is one instantiation; the control-plane
inventory is the catalog of the other instantiations. Neither repo
states this because each was built inside its own task horizon —
`research_as_inventory` in repo form. The inventory existed; the
analysis (what it means for yamlgraph) is this entry.

## What FR-781 contributed that the control-plane repo lacks

The control-plane scripts are imperative Swift/shell with timing
windows and retry heuristics (the WhatsApp image extractor needs a
10-second modification-time window and a re-download dialog handler).
What the file-hook demo adds is the *governance layer* those scripts
never had:

1. **Output-artifact-as-ledger idempotence** — the `.md` twin, the
   renamed file, the created reminder IS the processed-marker. Any
   trigger surface that re-fires (launchd rename echo, FSEvents
   coalescing, notification replays) becomes harmless.
2. **Confidence gate before actuation** — the LLM stakes
   `high|medium|low`; only `high` acts. Generalizes to every
   act-on-my-behalf automation: blocked items stay visible and retry.
3. **Fail-safe naming/normalization at the boundary** — `safe_basename`
   is the_one_law applied to filesystem actuation.

The control-plane repo's own lesson list converges from the other
side: "prefer passive over UI", "event-driven > polling", "AX is last
resort" — those are trigger-selection heuristics; the yamlgraph side
supplies act-decision heuristics. Together they compose.

## Use cases now cheap (trigger × graph × actuator)

| Trigger | Graph work | Actuator | Notes |
|---------|-----------|----------|-------|
| WatchPaths on `~/Downloads` | pdftotext → `{sender,date,total,confidence}` | rename | Receipt renamer (FR-781 README recipe) |
| FSEvents on WhatsApp `Group Containers/*/Media/` | describe_image manifest | file copy + md | Passive — beats the whole AX extraction pipeline |
| StartCalendarInterval | diary_digest (already live) | md report | Existing pattern, now with a healthy venv |
| `shortcuts run` → wrapper | any graph | Shortcuts chain | Siri/Focus-mode entry into typed pipelines |
| Spotlight query as scan tool | map over results | tags/rename | `mdfind` is find_unpaired generalized |
| Darwin/distributed notification | classify → route | URL scheme `open` | Needs the hooks-probe's name map first |

The composition rule from FR-781 holds everywhere: the scan tool
defines "unprocessed" via the actuator's own artifact, and the gate
decides act/skip. Only the two endpoints change.

## Trap confirmed: permission model is per-surface, not per-machine

Today's TCC failure (`pyvenv.cfg` under `~/Documents`) and the
control-plane's permission notes (Accessibility for AX, Full Disk for
TCC db, Calendar for EventKit) are the same boundary fact: **each
trigger/actuator surface carries its own TCC gate, attributed to the
responsible binary**. Pattern B (deploy outside protected paths) cures
the filesystem case; AX and EventKit cases need per-binary grants that
no installer can script. An install pattern that doesn't name its TCC
gate is incomplete — `workspace_is_not_boundary`'s sibling: *the
filesystem is not the permission boundary; the surface is*.

**Heuristic:** When wiring a new trigger or actuator surface, state
its TCC gate and its re-fire semantics (echo, coalescing, replay)
before writing the graph — those two facts determine the ledger design
and the deploy location, which are the only hard parts. The graph in
the middle is the easy, regenerable 60%.

**Seed:** Tool manifests (FR-768) typed the *tool* boundary; triggers
are still artisanal plists and wrapper scripts. Could a graph declare
`trigger: {type: watchpaths, path: ..., throttle: 30}` in metadata,
with one installer rendering the plist/wrapper/deploy-copy (Pattern B
mechanized) — `yamlgraph hook install <graph.yaml>`? The control-plane
inventory would then be a menu of `trigger.type` values, and the
per-surface TCC gate + re-fire semantics could live in the trigger
manifest schema as required declarations.
