# Feature Request: macOS File Hook Example — Folder-Triggered Graphs (DeviantArt MD Generator)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged 2026-08-08 — APPROVED WITH REVISIONS (R-1..R-5 folded below);
see `FR-781-macos-file-hook-example.judgement.md`
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
  rename-then-reprocess bugs (its todo.md is the test plan). No
  persistent processed-files ledger may be introduced (judgement C-7).
- **Confidence gate** (FR-779 pattern): schema includes a confidence
  field; low confidence routes past write/rename — the file stays
  unpaired and is retried on the next event, visibly.
- **Schema at the boundary**: `ImageDescription` extended with optional
  `quote: str | None` and a **constrained** confidence field (default
  None — additive, `matches_prompt`/`notes` set the precedent)
  replacing grep-from-prose.

### Confidence semantics (R-3, frozen)

- `confidence: Literal["high", "medium", "low"] | None = None`.
- **Only `"high"` permits write + rename.** `"medium"`, `"low"`, and
  `None`/missing all block — fail-safe: absence of confidence must not
  publish. The gate is structural (typed field + deterministic
  condition), never prompt-only.

### Filename, collision, and idempotence boundary (R-2, frozen)

- Title → basename normalization is deterministic: reject or transform
  path separators, control characters, empty names, `.`/`..`, and any
  name escaping the watched directory. All writes and renames are
  confined to the watched directory.
- Duplicate-title collision policy: if `<safe-title>.md` or
  `<safe-title>.png` already exists for a DIFFERENT source file, append
  a numeric suffix (`<safe-title>-2`); never overwrite unrelated files.
- A failed safety check leaves the source PNG unmodified with a visible
  error — no fallback to a risky name, no success-shaped output
  (judgement C-3).
- Idempotence contract beyond the happy path, all tested: second-run
  no-op, existing `.md` twin skipped, unsafe title skipped, duplicate
  collision handled, low-confidence no-write/no-rename. The demo runs
  against a disposable copy of `fixture.png` so the witness never
  consumes the committed fixture.

### `describe_image` manifest enhancement (in scope)

```python
def describe_image(image, instruction, *, max_dim: int | None = None, ...):
    # max_dim set: downscale a temp copy so its longest side <= max_dim
    # BEFORE base64 encoding — token/cost engineering at the boundary.
    # max_dim unset: current full-size path, byte-identical behavior.
```

- Downscaling uses Pillow under a **new `vision` optional extra**
  (`Pillow>=10.0.0`) — frozen by judgement R-4. Governance surface:
  entry in `docs/dependency-rationale.yaml`; direct-import scan
  metadata maps `PIL` → `Pillow`; the extra is added to the CI
  unit-test install surface so the positive downscale test runs in CI.
  Requesting `max_dim` without the extra fails fast — before LLM
  invocation — naming `pip install "yamlgraph[vision]"` (FR-759 otel
  precedent: explicit opt-in fails loud, unset is a true no-op); the
  missing-extra path is tested by import simulation, not ambient
  environment.
- URL images: `max_dim` is ignored with a logged warning (no download
  side effect in scope).
- The manifest description and headers updated to name this demo as the
  second committed consumer.

### launchd hook (R-1, frozen contract)

Plist template contains `WatchPaths`, `ThrottleInterval` (30s debounce;
the graph is idempotent anyway), `WorkingDirectory` (repo root),
`StandardOutPath`/`StandardErrorPath`, and an exact executable
`ProgramArguments` — launchd does no shell expansion:

```xml
<key>ProgramArguments</key>
<array>
  <string>/ABS/REPO/.venv/bin/yamlgraph</string>
  <string>graph</string>
  <string>run</string>
  <string>/ABS/REPO/examples/demos/file-hook/graph.yaml</string>
  <string>--var</string>
  <string>dir=/ABS/PATH/TO/watched-folder</string>
</array>
<key>WatchPaths</key>
<array><string>/ABS/PATH/TO/watched-folder</string></array>
<key>ThrottleInterval</key>
<integer>30</integer>
```

- API keys/env reach launchd via the README-documented options
  (`EnvironmentVariables` dict, wrapper script sourcing `.env`, or
  Keychain) — never assumed from an interactive shell.
- `install-hook.sh <watched-dir>` renders the template with absolute
  paths, copies to `~/Library/LaunchAgents/`, and loads it. It has a
  `--render-only` (dry-run) mode so CI tests path substitution and
  load/unload command construction without launchctl; real `launchctl`
  execution is optional/manual, never required in Linux CI
  (judgement C-4).

### README contract (the actual deliverable for "system hooks")

1. **Install a yamlgraph graph as a macOS file hook** — plist anatomy
   (`WatchPaths` vs `StartCalendarInterval`), install/uninstall/status/
   manual-test/logs commands, environment/API-key setup for launchd,
   and the **sandbox trap callout**: launchd agents need
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

Frozen by the judgement (AC-01 satisfied by this revision):

- [x] AC-01: FR revised to include the exact launchd runner/env/test
      contract, filename/collision/idempotence contract, constrained
      confidence semantics, chosen Pillow extra/dependency-governance
      surface, and demo-witness requirements (R-1..R-5).
- [ ] AC-02: `examples/demos/file-hook/graph.yaml` and
      `prompts/describe_artwork.yaml` authored through
      `scripts/author.sh`; `tmp/draft-authoring-report.md` records
      lint, compile/validate, smoke, and test evidence.
- [ ] AC-03: Pairing idempotence proven by tests on a temporary folder:
      first run processes a PNG with no `.md` twin, second run
      processes zero files, existing `.md` twin skipped without a
      ledger.
- [ ] AC-04: Filename-safety tests prove title normalization confines
      outputs to the watched directory, handles path separators/
      control characters/empty or dot names, and applies the frozen
      duplicate-title collision policy without overwriting unrelated
      files.
- [ ] AC-05: Confidence-gate tests prove low, missing, or otherwise
      blocked confidence writes no markdown and performs no rename,
      while `"high"` writes `<safe-title>.md` and renames the PNG.
- [ ] AC-06: `ImageDescription` gains optional `quote` and constrained
      optional `confidence` fields with defaults preserving existing
      shared-vision consumers; existing shared-vision tests remain
      green without weakened assertions.
- [ ] AC-07: `describe_image(max_dim=...)` downscales before base64
      encoding (longest side ≤ `max_dim`, payload bytes shrink);
      `max_dim=None` preserves current full-size behavior; URL inputs
      not downloaded, documented warning when `max_dim` requested.
- [ ] AC-08: `max_dim` without the Pillow extra fails before LLM
      invocation naming `pip install "yamlgraph[vision]"`; tests
      simulate the missing-extra path independent of ambient state.
- [ ] AC-09: `pyproject.toml`, `docs/dependency-rationale.yaml`,
      dependency-scan metadata, and CI install surfaces updated
      consistently for the `vision` extra;
      `python scripts/dependency_rationale.py --strict` and
      `python scripts/direct_import_scan.py --strict` pass.
- [ ] AC-10: Plist template contains `WatchPaths`, `ThrottleInterval`,
      `WorkingDirectory`, `StandardOutPath`, `StandardErrorPath`, and
      exact executable `ProgramArguments`; install-script tests verify
      absolute-path rendering and load/unload command construction via
      dry-run/fake launchctl without requiring macOS in CI.
- [ ] AC-11: README documents install, uninstall, status, manual test,
      logs, environment/API-key setup, `WatchPaths` vs
      `StartCalendarInterval`, the Full Disk Access/TCC trap, this
      example, and the receipt-renamer as documentation-only recipe;
      `reference/scheduling-agents.md` links the example as the
      canonical WatchPaths demo.
- [ ] AC-12: `demo-output.log` regenerated from a grounded
      `PROVIDER=google` run on a disposable copy of `fixture.png`:
      shows typed schema output, confidence routing, write/rename
      effects, second-run no-op; no fatal markers; committed fixture
      not consumed or renamed.
- [ ] AC-13: Every new/changed test has exact
      `@pytest.mark.req("REQ-YG-...")`; capability registry updated for
      the file-hook example and vision downscale;
      `python scripts/req_coverage.py --strict` passes.
- [ ] AC-14: Changelog fragment, FR implementation-status update, and
      diary reflection included.

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

## Judgement (2026-08-08)

**Verdict:** APPROVED WITH REVISIONS — see
`FR-781-macos-file-hook-example.judgement.md` for the full rubric.
R-1..R-5 folded into this FR above (C-1 satisfied). Enforcement gates
C-2..C-7: governed authoring only; fail-safe write boundary; installer
testable without launchd; `max_dim` requiring `yamlgraph/` changes or
core-Pillow promotion stops for re-judgement; receipt-renamer stays
documentation-only; no fswatch/polling/ledger — the `.md` twin is the
ledger.
