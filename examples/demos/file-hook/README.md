# File Hook Demo — Run a YAMLGraph Graph as a macOS File Hook

Drop a PNG into a watched folder; seconds later a `<Poetic Title>.md`
post description sits beside the renamed image — or nothing is written
and the log says why. This demo (FR-781) shows the general pattern:
**installing any yamlgraph graph as a macOS system hook** using a
launchd `WatchPaths` agent — zero daemons, zero polling, survives
reboots.

The shipped graph reimplements a real pre-yamlgraph shell automation
(a DeviantArt publishing watcher) with typed boundaries:

```
scan (find PNGs lacking an .md twin)          ← pairing IS the ledger
  → map over unpaired
      → describe_image (shared vision manifest, max_dim downscale)
      → confidence gate: only "high" publishes  ← never publish a hallucinated myth
      → write <safe-title>.md + rename PNG      ← fail-safe, confined to the folder
```

## Run it manually

```bash
# Process every unpaired PNG in a folder (copy the fixture somewhere first —
# the graph renames what it processes):
mkdir -p /tmp/file-hook-demo && cp examples/demos/file-hook/fixture.png /tmp/file-hook-demo/
PROVIDER=google yamlgraph graph run examples/demos/file-hook/graph.yaml \
  --var dir=/tmp/file-hook-demo --full

# Second run is a no-op: every PNG now has its .md twin
PROVIDER=google yamlgraph graph run examples/demos/file-hook/graph.yaml \
  --var dir=/tmp/file-hook-demo --full
```

Requires `GOOGLE_API_KEY` (or `ANTHROPIC_API_KEY` with
`PROVIDER=anthropic`) and the vision extra:

```bash
pip install -e ".[vision]"   # Pillow, for the max_dim downscale
```

## Install as a system hook (launchd WatchPaths)

```bash
cd examples/demos/file-hook/hooks

# Dry run — prints the rendered plist to stdout, commands to stderr:
./install-hook.sh --render-only ~/Pictures/deployed

# Real install: renders, copies to ~/Library/LaunchAgents, loads:
./install-hook.sh ~/Pictures/deployed
```

### Managing the hook

```bash
launchctl list | grep yamlgraph                                    # status
launchctl start com.yamlgraph.file-hook                            # fire now (test)
tail -f /tmp/com.yamlgraph.file-hook.log                           # logs
launchctl unload ~/Library/LaunchAgents/com.yamlgraph.file-hook.plist  # uninstall
```

### Plist anatomy — WatchPaths vs StartCalendarInterval

| Key | Purpose |
|-----|---------|
| `WatchPaths` | Fire when anything in the folder changes (event-driven — this demo) |
| `StartCalendarInterval` | Fire on a schedule (see [scheduling-agents.md](../../../reference/scheduling-agents.md)) |
| `ThrottleInterval` | Debounce bursts (30s here); safe because the graph is idempotent |
| `ProgramArguments` | Absolute paths only — launchd does **no** shell expansion |
| `WorkingDirectory` | Repo root, so relative graph paths resolve |
| `EnvironmentVariables` | API keys — launchd agents do NOT inherit your shell env |

### ⚠️ The macOS sandbox trap (Full Disk Access)

launchd agents are **denied access to `~/Documents`, `~/Desktop`, and
`~/Downloads`** by macOS privacy protection (TCC) — the graph will fail
with `Operation not permitted` while working perfectly in your
terminal. Documented the hard way in
[docs/diary-2026-02-21.md](../../../docs/diary-2026-02-21.md). Either:

- watch a folder outside protected locations (e.g. `~/Pictures/...`), or
- grant Full Disk Access to the executing binary
  (System Settings → Privacy & Security → Full Disk Access).

### Getting API keys into launchd

Pick one (in the plist template or a wrapper):

1. `EnvironmentVariables` dict in the plist (simplest; plist is
   user-readable — keep it out of git).
2. Wrapper script as `ProgramArguments[0]` that sources your `.env`
   then execs `yamlgraph`.
3. `security find-generic-password` (Keychain) inside a wrapper.

## Design notes

- **The `.md` twin is the ledger.** No `.processed_files` file, no
  database: a PNG is unprocessed iff `<base>.md` does not exist. Rerun
  anytime; already-published files are skipped. This cures the
  ancestor's duplicate-ledger and rename-then-reprocess bugs.
- **Only `confidence: high` publishes.** The schema
  (`ImageDescription` in [examples/shared/vision_tool.py](../../shared/vision_tool.py))
  constrains confidence to `high | medium | low`; medium, low, and
  missing all block — the file stays unpaired, visible, and is retried
  on the next event.
- **Fail-safe writes.** Titles are normalized (no path separators,
  control chars, dot names); collisions get a numeric suffix; a failed
  safety check leaves the source PNG untouched.
- **`max_dim=512` downscale** before base64 encoding cuts vision-token
  cost — the ancestor shrank images to 10% for the same reason.

## Other use cases (recipes)

The hook mechanics are identical for any graph — only the plist's
`ProgramArguments` graph path and `--var` change.

### Receipt renamer (sketch — not implemented)

Watch `~/Downloads`; when a PDF arrives, extract the sender and date,
rename to `<Sender> - <date> - receipt.pdf`:

```yaml
# graph sketch only — author via scripts/author.sh if you build it
state: {dir: str, unpaired: list, results: list}
tools:
  find_new_pdfs: ...      # same pairing trick: rename IS the ledger
                          # (processed files match the target pattern)
  pdf_text:
    type: shell
    command: pdftotext -l 1 {file} -   # first page to stdout
nodes:
  extract:                # llm node with inline schema:
    ...                   # {sender: str, date: str, total: str,
                          #  confidence: Literal[high|medium|low]}
  rename:                 # only confidence high renames; same
    ...                   # safe_basename + collision discipline
```

Same doctrine applies: schema at the boundary, only `high` acts,
pairing-style idempotence, fail-safe rename.

### Scheduled variants

For time-based (not event-based) triggers, use
`StartCalendarInterval` — full guide in
[reference/scheduling-agents.md](../../../reference/scheduling-agents.md).

## Files

| File | Purpose |
|------|---------|
| [graph.yaml](graph.yaml) | scan → map(process) pipeline (authored via `scripts/author.sh`) |
| [prompts/describe_artwork.yaml](prompts/describe_artwork.yaml) | Publishing-voice instruction (title/prose/tags/quote/confidence) |
| [tools.py](tools.py) | `find_unpaired`, `safe_basename`, `process_artwork` (gate + fail-safe publish) |
| [hooks/com.yamlgraph.file-hook.plist.template](hooks/com.yamlgraph.file-hook.plist.template) | launchd WatchPaths agent template |
| [hooks/install-hook.sh](hooks/install-hook.sh) | Renders absolute paths; `--render-only` for CI |
| [fixture.png](fixture.png) | Demo witness input (downscaled real artwork) |
| [demo-output.log](demo-output.log) | Grounded witness: publish + second-run no-op |

Tests: `tests/unit/test_fr781_file_hook.py` (REQ-YG-582, REQ-YG-583).
