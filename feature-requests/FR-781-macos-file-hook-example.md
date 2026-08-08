# Feature Request: macOS File Hook Example — Folder-Triggered Graphs (DeviantArt MD Generator)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 3 days
**Requested:** 2026-08-08
**First consumer / first event:** the 15 orphaned PNGs in
`~/Documents/deviant-working/deployed/` (newest 2026-08-05), which have
waited for post descriptions since the shell ancestor died 2025-10-30;
first event is the next image the operator drops into that folder.

**Prior art:** `reference/scheduling-agents.md` covers launchd
`StartCalendarInterval` only — no `WatchPaths`/event-driven pattern
exists in the repo (this FR adds the sibling, not a duplicate).
FR-117 rejected fswatch for the enforce watcher; that rationale (extra
daemon, extra dependency) argues FOR `WatchPaths` here, which is
zero-daemon. `examples/demos/shared-vision-tool/` +
`examples/shared/describe_image.tool.yaml` solve the vision boundary
and are reused, not reinvented. FR-046 shipped a launchd-scheduled
graph (calendar, not file-triggered). No rejected FR occupies this
territory.

## Summary

A demo example (`examples/demos/file-hook/`) showing how to run a
yamlgraph graph as a **macOS file hook**: a launchd `WatchPaths` agent
fires the graph whenever a watched folder changes. The shipped graph is
a yamlgraph reimplementation of the deviant-working ancestor
(diary-2026-08-08): scan for PNGs lacking an `.md` twin → vision-analyze
via the shared `describe_image` manifest → typed schema (title,
description, tags, quote) → confidence gate → write `<Title>.md` and
rename the PNG. The README doubles as the canonical guide for
installing ANY yamlgraph graph as a system hook, with recipes for other
use cases (receipt PDF renaming — prefixing sender name).

**In scope — shared manifest enhancement:** `describe_image`
(`examples/shared/vision_tool.py`, CAP-217) is the reusable boundary
this demo consumes; it gains (a) an optional `max_dim` downscale
parameter — the ancestor's 10%-shrink cost trick generalized — and
(b) optional `quote` and `confidence` schema fields the gate needs.
Both additive; existing consumers unchanged.

## Value Statement

Operators get event-driven local automation (drop file → typed LLM
pipeline runs) with one plist and zero daemons, replacing hand-rolled
polling shell scripts that rot silently.

## Problem

1. The deviant-working automation (loop.sh + claude-deployed.sh) is the
   proven use case but embodies every pre-yamlgraph trap: grep-based
   title extraction (no schema boundary), a `.processed_files` ledger
   with duplicate-entry bugs, a 15s polling daemon, and a pairing
   invariant that rotted invisibly when the watcher died — 15 orphaned
   PNGs today.
2. yamlgraph documents **scheduled** execution
   (`reference/scheduling-agents.md`, `StartCalendarInterval`) but has
   no documented pattern for **event-driven** execution. `WatchPaths`
   is one plist key away and nothing in the repo shows it.
3. The pattern generalizes (receipts, downloads triage, inbox sorting)
   but there is no install guide an operator can follow without
   re-deriving the launchd sandbox trap (diary-2026-02-21: launchd
   agents are denied `~/Documents` without Full Disk Access).

## Ideal Result

The operator drops a PNG into the watched folder; seconds later a
`<Poetic Title>.md` post description in the julkaisuohje style sits
beside the renamed PNG — or, when the vision analysis is low-confidence,
nothing is written and the log says why (never publish a hallucinated
myth). Installing this behavior — or the same hook wired to any other
graph — is a copy-paste sequence from one README. Re-running the graph
on an already-processed folder is a no-op: the `.md` twin IS the ledger.

## Proposed Solution

New example `examples/demos/file-hook/`:

```
examples/demos/file-hook/
  graph.yaml                    # authored via scripts/author.sh (FR-767)
  prompts/describe_artwork.yaml # julkaisuohje-derived instruction + inline schema
  hooks/com.yamlgraph.file-hook.plist.template  # WatchPaths agent, path placeholders
  hooks/install-hook.sh         # substitutes absolute paths, cp + launchctl load
  README.md                     # the system-hook install guide + recipes
  fixture.png                   # demo witness input
  demo-output.log
```

### Graph flow

```yaml
# sketch — final artifact produced by the governed authoring route
state:
  dir: str            # watched folder, passed by the hook runner
  unpaired: list      # PNGs without an .md twin
  results: list

tools:
  find_unpaired:      # shell: find "$dir" pngs lacking "<base>.md"
    command: ...      # pairing check replaces the ancestor's ledger
  describe_image:
    manifest: ../../shared/describe_image.tool.yaml   # args: max_dim: 512
  write_post: ...     # shell: write <Title>.md
  rename_image: ...   # shell: mv original -> <Title>.png (idempotent)

nodes:
  scan:      {type: tool_call, tool: find_unpaired, state_key: unpaired}
  process:   {type: map, over: unpaired, ...}   # describe -> gate -> write -> rename
```

- **Idempotence by pairing, not ledger**: a file is "new" iff it has no
  `.md` twin. Cures the ancestor's duplicate-ledger and
  rename-then-reprocess bugs (its todo.md is the test plan).
- **Confidence gate** (FR-779 pattern): schema includes a confidence
  field; low confidence routes past write/rename — the file stays
  unpaired and is retried on the next event, visibly.
- **Schema at the boundary**: `ImageDescription` extended with optional
  `quote: str | None` and `confidence: str | None` (default None —
  additive, `matches_prompt`/`notes` set the precedent) replaces
  grep-from-prose.

### `describe_image` manifest enhancement (in scope)

```python
def describe_image(image, instruction, *, max_dim: int | None = None, ...):
    # max_dim set: downscale a temp copy so its longest side <= max_dim
    # BEFORE base64 encoding — token/cost engineering at the boundary.
    # max_dim unset: current full-size path, byte-identical behavior.
```

- Downscaling uses Pillow, declared as a new optional extra (or added
  to an existing one — judge decides); requesting `max_dim` without the
  extra fails fast naming the install command (FR-759 otel precedent:
  explicit opt-in fails loud, unset is a true no-op).
- URL images: `max_dim` is ignored with a logged warning (no download
  side effect in scope).
- The manifest description and headers updated to name this demo as the
  second committed consumer.

### launchd hook

```xml
<key>WatchPaths</key>
<array><string>/ABS/PATH/TO/watched-folder</string></array>
<key>ThrottleInterval</key>
<integer>30</integer>   <!-- debounce bursts; graph is idempotent anyway -->
```

`ProgramArguments` = absolute venv python → `yamlgraph graph run
examples/demos/file-hook/graph.yaml --var dir=<watched>`.
`install-hook.sh <watched-dir>` renders the template (launchd does no
shell expansion), copies to `~/Library/LaunchAgents/`, and loads it.

### README contract (the actual deliverable for "system hooks")

1. **Install a yamlgraph graph as a macOS file hook** — plist anatomy
   (`WatchPaths` vs `StartCalendarInterval`), install/uninstall/test/
   logs commands, and the **sandbox trap callout**: launchd agents need
   Full Disk Access (or a watch dir outside `~/Documents`/`~/Desktop`)
   — cite diary-2026-02-21 so nobody re-derives it.
2. **This example**: the DeviantArt post generator, run manually or via
   the hook.
3. **Other use cases (recipes, documented not enforced)**:
   - **Receipt renamer**: watch `~/Downloads`, graph extracts sender
     name from PDF text (`pdftotext` shell tool → LLM schema
     `{sender, date, total, confidence}`) → rename to
     `<Sender> - <date> - receipt.pdf`. Graph sketch in README only.
   - Pointer back to `reference/scheduling-agents.md` for scheduled
     (non-event) variants.
4. `reference/scheduling-agents.md` gains a short "File hooks
   (WatchPaths)" section linking to this example as the canonical demo.

## Acceptance Criteria

- [ ] `examples/demos/file-hook/graph.yaml` lints
      (`yamlgraph graph lint`) and compiles; authored via
      `scripts/author.sh` (FR-767 governed route)
- [ ] Pairing idempotence: running the graph twice on the same folder
      processes zero files the second run (unit test on the
      `find_unpaired` tool semantics + witnessed in demo-output.log)
- [ ] Low-confidence gate: condition strings verified by unit test
      (FR-779 pattern); low-confidence file is neither written nor
      renamed
- [ ] `describe_image(max_dim=...)`: unit test proves the encoded image's
      longest side ≤ `max_dim` and payload bytes shrink vs full-size;
      `max_dim=None` leaves the current path untouched (existing
      shared-vision-tool tests stay green unmodified)
- [ ] `max_dim` without the Pillow extra raises a fail-fast error naming
      the extra; `ImageDescription.quote`/`.confidence` optional fields
      added with defaults
- [ ] `hooks/com.yamlgraph.file-hook.plist.template` contains
      `WatchPaths` + `ThrottleInterval`; `install-hook.sh` renders
      absolute paths and loads the agent
- [ ] README documents install/uninstall/status/log commands, the
      Full-Disk-Access sandbox trap, and the receipt-renamer recipe
- [ ] `reference/scheduling-agents.md` extended with a WatchPaths
      section referencing the example
- [ ] Grounded `demo-output.log` witness on `fixture.png`
      (PROVIDER=google): shows schema output and the write/rename
      effects
- [ ] Tests tagged with new REQ-YG-XXX; new `capabilities/CAP-XXX`
      file; `python scripts/req_coverage.py --strict` green
- [ ] Changelog fragment in `changelog/unreleased/`
- [ ] Diary entry

## Alternatives Considered

1. **Revive the shell ancestor** — keeps grep-parsing and the ledger
   bugs; rejected per diary-2026-08-08 (the seed this FR grows from).
2. **fswatch/polling daemon** — a second process to manage; FR-117
   already rejected fswatch for the enforce watcher. `WatchPaths` is
   OS-native, zero-daemon, and survives reboots via launchd.
3. **macOS Folder Actions (Automator/AppleScript)** — native but
   unversionable and undebuggable; a plist in git is doctrine-shaped.
4. **Implement the receipt renamer as a second enforced graph** —
   doubles witness/test surface for a recipe whose hook mechanics are
   identical; documented sketch suffices until it has a first consumer.
5. **In-graph shrink via shell tool (`sips`)** — keeps the manifest
   untouched but couples the pattern to macOS and leaves every future
   vision consumer to re-derive the trick; rejected in favor of the
   in-scope `max_dim` parameter on the shared manifest, where the
   optimization is reusable and portable (Pillow).
6. **Deferring the manifest enhancement to its own FR** — original
   draft's position; overturned: the demo is the concrete second
   consumer that justifies the parameter now, and shipping the demo
   full-size would embed the cost bug the ancestor had already solved.

## Related

- diary-2026-08-08-the-ancestor-in-the-deployed-folder.md (seed origin;
  `~/Documents/deviant-working/` is the requirements doc, its todo.md
  the test plan)
- `examples/shared/describe_image.tool.yaml` +
  `examples/demos/shared-vision-tool/` (vision boundary already solved)
- `examples/shared/toolbelt/` (CAP-220, FR-780 — shell manifest pattern)
- `reference/scheduling-agents.md` (launchd calendar scheduling; this FR
  adds the event-driven sibling)
- docs/diary-2026-02-21.md (launchd sandbox trap — must be in README)
- FR-117 (fswatch rejection precedent)
- FR-779 (confidence-gate pattern reused here)
