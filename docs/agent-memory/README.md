# Agent Memory Store (FR-874)

Git-tracked mirror of the Copilot memory tool's machine-local scopes. The
memory tool remains the fast local cache; **this store is the canonical,
portable copy** — git is the transport across devices, peers, and subrepos.

## Layout

- `repo/` — yamlgraph-scoped facts, mirrored from the local memory-tool
  repo scope automatically on `export`.
- `shared/` — user-scope practices exported **only after explicit per-note
  promotion** (`memory_sync.py promote <note>.md`). No export-all mode
  exists; an unpromoted user note never leaves the machine.
- `manifest.json` — deterministic record per note: path, scope, sha256,
  promotion source. Makes every seed/export diff auditable.

## Excluded content classes

Never commit notes containing secrets or credentials, customer-private
data, or session-scoped notes. Machine-local paths are acceptable only
when they are the documented fact itself. Every export diff is
human-reviewed before commit.

## Usage

```bash
# publish (at Distill time, in the master clone)
python scripts/memory_sync.py export
git add docs/agent-memory && git commit

# receive (automatic: SessionStart hook runs this fail-open)
python scripts/memory_sync.py import

# share a user-scope practice note
python scripts/memory_sync.py promote precommit-dry-run.md
```

## Conflict contract

Import records the store hash it last applied per note
(`<memory-root>/.import-base.json`, machine-local). A local note is
overwritten only when it still matches that base; divergence on both
sides is a reported conflict requiring `--force`. Filesystem mtimes are
never consulted.

## Subrepo access (read-only in v1)

Sessions outside the master clone set `YAMLGRAPH_AGENT_MEMORY_ROOT` to the
master clone's `docs/agent-memory/`. Import works; export and promote are
refused. An unset or invalid variable is an observable error, not a
silent skip.
