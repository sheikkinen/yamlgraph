# Scheduling YAMLGraph Agents

How to run YAMLGraph graphs on a schedule — locally or in CI.

## macOS: launchd

`launchd` is macOS's native scheduler (preferred over cron). Agents run in user context with access to env vars, keychain, and file system.

### Plist template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.yamlgraph.diary-digest</string>

    <key>ProgramArguments</key>
    <array>
        <string>/path/to/yamlgraph/.venv/bin/python</string>
        <string>/path/to/yamlgraph/scripts/diary_digest.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/path/to/yamlgraph</string>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/tmp/diary-digest.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/diary-digest.err</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>ANTHROPIC_API_KEY</key>
        <string>FROM_KEYCHAIN_OR_DOTENV</string>
    </dict>
</dict>
</plist>
```

### Commands

```bash
# Install (load agent)
cp com.yamlgraph.diary-digest.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.yamlgraph.diary-digest.plist

# Uninstall
launchctl unload ~/Library/LaunchAgents/com.yamlgraph.diary-digest.plist

# Run immediately (test)
launchctl start com.yamlgraph.diary-digest

# Check status
launchctl list | grep yamlgraph

# View logs
tail -f /tmp/diary-digest.log
```

### Key launchd concepts

| Key | Purpose |
|-----|---------|
| `Label` | Unique identifier for the agent |
| `ProgramArguments` | Full path to python + script (no shell expansion) |
| `WorkingDirectory` | Set to repo root so relative paths work |
| `StartCalendarInterval` | Cron-like schedule (Hour/Minute/Day/Month/Weekday) |
| `RunAtLoad` | Set `true` to also run when first loaded |
| `KeepAlive` | Set `true` for long-running daemons (not needed for one-shot) |

### Environment variables

launchd agents don't inherit shell environment. Options:

1. **Inline in plist** — `EnvironmentVariables` dict (shown above). Simple but secrets in plaintext.
2. **dotenv in script** — Script loads `.env` file at startup (daily_digest pattern). Preferred.
3. **macOS Keychain** — Use `security find-generic-password` in a wrapper script. Most secure.

```bash
# Option 3: Wrapper script that loads from Keychain
#!/bin/bash
export ANTHROPIC_API_KEY=$(security find-generic-password -s "anthropic-api-key" -w)
cd /path/to/yamlgraph
.venv/bin/python scripts/diary_digest.py
```

### Scheduling patterns

```xml
<!-- Every day at 06:00 -->
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key><integer>6</integer>
    <key>Minute</key><integer>0</integer>
</dict>

<!-- Every Monday at 09:00 -->
<key>StartCalendarInterval</key>
<dict>
    <key>Weekday</key><integer>1</integer>
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>0</integer>
</dict>

<!-- Every 4 hours -->
<key>StartInterval</key>
<integer>14400</integer>
```

### File hooks (WatchPaths) — event-driven, not scheduled

To fire a graph when a **folder changes** instead of on a schedule,
replace `StartCalendarInterval` with `WatchPaths`:

```xml
<key>WatchPaths</key>
<array><string>/ABS/PATH/TO/watched-folder</string></array>
<key>ThrottleInterval</key>
<integer>30</integer>  <!-- debounce bursts; pair with an idempotent graph -->
```

Canonical demo with installer, sandbox-trap notes, and an idempotent
graph: [examples/demos/file-hook/](../examples/demos/file-hook/README.md)
(FR-781). Beware the TCC trap: launchd agents are denied
`~/Documents`/`~/Desktop`/`~/Downloads` without Full Disk Access.

## GitHub Actions: Cron

For CI-based scheduling, use GitHub Actions with `workflow_dispatch` for manual triggers.

```yaml
name: Diary Digest
on:
  schedule:
    - cron: '0 6 * * *'  # 6 AM UTC daily
  workflow_dispatch:       # Manual trigger

jobs:
  digest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[digest]"
      - run: python scripts/diary_digest.py --commit
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: daily diary digest"
          file_pattern: docs/diary.md
```

### Tradeoffs

| Aspect | launchd (local) | GitHub Actions (CI) |
|--------|----------------|-------------------|
| Runs when | Machine is on | Always (cloud) |
| Latency | Immediate file access | Commit → push → pull |
| Secrets | Keychain / .env | GitHub Secrets |
| Cost | Free | Free (public repos) |
| Dependencies | Local Python env | CI setup each run |
| Best for | Development workflow | Team/production |

## Existing examples

- `examples/daily_digest/` — Fly.io deployment with GitHub Action trigger
- `scripts/diary_rotate.py` — Pre-commit hook (event-driven, not scheduled)
