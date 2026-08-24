# Feature Request: Cross-Device Agent Memory Sync via Git-Tracked Note Store

## Rejection (2026-08-24, human verdict — overrides the judgement)

Enforced and rolled back the same day (RED `7aa7ac3d`, GREEN `78119e46`,
both reverted before push). Two independent fatal findings from the
post-enforcement security review of the seed corpus:

1. **The target repo is PUBLIC** (`gh repo view`: visibility PUBLIC). The
   FR's entire privacy model — and the judgement's R-1/R-5 — assumed a
   peer-shared repo; neither author, judge, nor enforcer checked
   visibility. The seed corpus contained customer-critical material with
   zero prior public baseline: customer-confidential material.
   Details are intentionally omitted from this
   public record. The controlling
   root cause
   is `workspace_is_not_boundary`: the memory tool's "repo" scope is
   actually workspace scope, and this workspace spans customer projects.
2. **The corpus is unjudged.** The notes are accumulated glimpses — no
   note ever passed a curation gate. Building the transport before the
   curation pipeline published randomness at scale. The correct order is
   a yamlgraph judgement graph over the corpus first (verdict per note:
   keep / redact / forget — selective amnesia), transport second, if
   ever. The pipeline-before-pipe lesson: FR-874 shipped the pipe.

**Precedent value (why this file survives):** any future proposal to
commit memory-tool contents to a git-tracked store must (a) verify repo
visibility as a written precondition, (b) route the corpus through a
judgement/selective-amnesia graph before any export exists, and (c)
treat note classification (public / peer / customer-private /
machine-local) as a boundary requirement, not an implementation detail.
Successor proposal: FR-875 (memory-corpus curation graph).

---

**Priority:** MEDIUM
**Type:** Feature
**Status:** REJECTED (2026-08-24) — enforced same day, then rolled back on post-enforcement security review; see Rejection below
**Effort:** 1–2 days
**Requested:** 2026-08-24
**First consumer / first event:** the Copilot agent starting a session on the
operator's *other* device (or a peer's clone), at SessionStart — it currently
re-derives repo facts that a sibling session already paid to learn, because
memory-tool notes never leave the machine they were written on.

## Summary

The memory tool's "repo" and "user" scopes are machine-local despite their
names: both live under the local VS Code user directory
(`workspaceStorage/<hash>/…/memory-tool/` and
`globalStorage/github.copilot-chat/memory-tool/`), keyed to one machine.
The same repo cloned on two devices has two disjoint "repo memories"; peers
share nothing. This FR adds a git-tracked note store in yamlgraph plus a
small sync mechanism, making yamlgraph — a shared repo that acts as master
for subrepos (customer-service-agent-platform, fsm, questionnaire-api,
tt-bot-v2) — the propagation hub for agent intel across devices and peers.

## Value Statement

Every agent session on every device/peer clone inherits the boundary facts,
root-causes, and working practices that any sibling session already paid an
incident to learn — instead of silently re-deriving them, wrongly, at cost.

## Problem

1. **Name-implies-portability defect (second occurrence).** The diary entry
   `docs/diary/diary-2026-07-16-a-map-for-the-amnesiac.md` established by
   filesystem proof that "repo memory does not live in the repo." On
   2026-08-24 the operator independently hit the consequence: multiple
   devices in use, best-practice intel visibly accumulating in memory notes,
   none of it reaching peers. Two occurrences → graduation threshold met
   (Scripture `graduation` rule); the observation must become a mechanism.
2. **No existing channel carries it.** Git-committed diaries carry
   *narrative*; Scripture carries *graduated doctrine*; memory-tool notes —
   the terse, high-frequency working layer (~60 files in this workspace's
   repo scope alone) — ride no committed artifact. VS Code Settings Sync
   does not cover extension `globalStorage`/`workspaceStorage` blobs.
3. **Subrepos are also cut off.** Notes about the voice projects, fsm, etc.
   live in yamlgraph's workspace-hash store; a session opened directly in a
   subrepo clone sees none of them.

## Ideal Result

An agent opening any clone of yamlgraph — any device, any peer, or a nested
subrepo workspace — finds the accumulated note corpus already present in the
working tree after an ordinary `git pull`, and notes it writes flow back
through an ordinary commit. The memory tool remains the fast local cache;
git is the transport; no new infrastructure, no daemon, no service.

## Proposed Solution

1. **Committed store:** `docs/agent-memory/` with two subdirectories:
   - `repo/` — mirror of `/memories/repo/*.md` (yamlgraph-scoped facts).
   - `shared/` — user-scope notes exported **only when explicitly promoted
     by name** (R-1, binding): no export-all, no denylist mode. A note is
     shareable solely by a deliberate promotion act; everything else stays
     machine-local.
2. **Manifest:** `docs/agent-memory/manifest.json` — deterministic record
   per note: path, scope, content hash, promotion source, and last-import
   base hash (R-2, R-5). The manifest makes the seed diff auditable and
   carries the conflict-detection base.
3. **Sync script:** `scripts/memory_sync.py` with `export` (memory-tool →
   repo; repo-scope notes plus explicitly promoted shared notes only;
   updates the manifest, reports adds/updates) and `import` (repo →
   memory-tool). **Conflict contract (R-2, binding — no mtime):** import
   records the repo content hash it last imported as the note's base hash;
   overwrite is refused when local content diverged from that base AND the
   repo content also changed; `--force` overwrites and records the new
   base. Conflicts are reported, never merged silently.
4. **SessionStart integration:** the FR-743 briefing hook additionally runs
   `memory_sync.py import --quiet` — fail-open, but a failure **emits a
   bounded audit/warning record** (R-4): never blocks a session, never
   masquerades as successful sync. Export remains a deliberate act at
   reflection time (Distill step), not automatic — commits stay curated.
5. **Subrepo access (R-3):** subrepo sessions discover the master store via
   the `YAMLGRAPH_AGENT_MEMORY_ROOT` environment variable pointing at the
   yamlgraph clone's `docs/agent-memory/`; when unset or invalid, import
   errors observably (no silent skip). Read-only from the subrepo side in
   v1.

```bash
# device A, at Distill time
python scripts/memory_sync.py export && git add docs/agent-memory && git commit -m "chore(memory): note sync"

# device B, at SessionStart (automated via FR-743 hook)
python scripts/memory_sync.py import
```

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: `docs/agent-memory/{repo,shared}/` and README exist; README
      states git-tracked store vs local cache, explicit opt-in `shared/`
      promotion, excluded content classes, and subrepo read-only behavior.
- [ ] AC-02: Initial seed includes a manifest with every committed note
      path, scope, content hash, and promotion source; no session-scoped
      notes are seeded; seed diff human-reviewed before commit (R-5).
- [ ] AC-03: `export` copies repo-scope notes and explicitly promoted
      shared notes only, updates the manifest, reports adds/updates, and
      never exports unpromoted user-scope notes.
- [ ] AC-04: Export → wipe (temporary memory-tool root) → import reproduces
      exported note bytes and manifest base hashes (test).
- [ ] AC-05: Import refuses overwrite when local content diverged from the
      recorded base hash and repo content changed; `--force` overwrites and
      records the new base hash (test).
- [ ] AC-06: Import sanitizes all note paths — rejects traversal, absolute
      paths, symlinks escaping the target root, and non-`.md` payloads.
- [ ] AC-07: Subrepo import discovers the master store via
      `YAMLGRAPH_AGENT_MEMORY_ROOT`, imports read-only, errors observably
      when the path is absent or invalid.
- [ ] AC-08: FR-743 SessionStart integration runs import fail-open and
      emits a bounded audit/warning record on failure.
- [ ] AC-09: Tests tagged with a new `REQ-YG-XXX`; capability file added;
      tests use temporary memory-tool roots, never the operator's real
      VS Code memory directories (C-3).
- [ ] AC-10: FR updated with implementation status/deviations; `docs/diary/`
      reflection included.

## Alternatives Considered

- **Symlink memory-tool dirs into the repo:** fragile — the store is keyed
  by workspace hash, VS Code owns the tree (MAP.md seam 2: never write to
  live stores), and a symlinked git dir inside `Application Support` invites
  the nested-repo blast-radius trap.
- **VS Code Settings Sync:** does not cover extension storage; not
  peer-shareable regardless.
- **Rely on diaries + Scripture only:** these carry narrative and graduated
  doctrine; the terse working layer (60+ notes) is a different register with
  a different write frequency — forcing it through diary format would kill
  the habit that produces it.
- **GitHub issues / chaplain inbox as transport:** built for proposals with
  lifecycle, not for a synced corpus; wrong shape.

## Prior art

**Prior art:** FR-243 (GitHub-issues remote inbox) — proposal transport
with lifecycle, not a synced note corpus; dispositioned under Alternatives.
FR-782 (user self-portrait example) — renders a portrait from session
stores, read-only analytics; no note transport, no overlap. FR-824 /
FR-831 (HVA/Oulu bulletin repos) — noun collisions (cross/device/memory)
only; bulletin generation is unrelated territory. FR-617 and FR-743 are
dispositioned below.

- `docs/diary/diary-2026-07-16-a-map-for-the-amnesiac.md` — first
  occurrence, filesystem proof, no mechanism built.
- FR-617 (memory node) — graph-level memory primitive for *graphs*, not the
  authoring agent's memory-tool scopes; complementary, not overlapping. Its
  Correction 1 (concurrent-write clobber) and Correction 2 (explicit miss)
  inform the import conflict contract here.
- FR-743 (SessionStart briefing hook) — the delivery seam this FR rides.
- `/memories/repo/where-repo-notes-live.md` doctrine: diaries durable,
  memory notes fast working layer — this FR makes the working layer durable
  without changing its register.

## Related

- Scripture: `one_session_one_repo` — the sync commit must follow the
  shared-index ritual (explicit file list, immediate commit).
- Scripture trap candidate: *name-implies-portability* (named in the
  2026-07-16 diary; this FR is its cure).

## Judgement (2026-08-24)

**Verdict: APPROVED WITH REVISIONS** — rendered via the sole judge route
(`scripts/judge.sh`, copilot graph, model gpt-5.5); full artifact:
`feature-requests/FR-874-cross-device-agent-memory-sync.judgement.md`.

| # | Revision (folded above) |
|---|---|
| R-1 | `shared/` is explicit opt-in promotion only — no export-all/denylist |
| R-2 | Conflict contract is manifest base-hash based, never filesystem mtime |
| R-3 | Subrepo discovery pinned to `YAMLGRAPH_AGENT_MEMORY_ROOT`; observable failure when absent |
| R-4 | SessionStart import fail-open but emits bounded audit/warning evidence |
| R-5 | Seed corpus gated by committed manifest + human review; no session-scope notes, no secrets/local paths |

**Not authorized:** bidirectional subrepo write-back; automatic export at
SessionStart; export-all user-scope; daemon/watch mode; symlinking VS Code
memory-tool dirs; FR-617 primitive changes; hook/CI policy changes beyond
the FR-743 integration.

## Implementation (2026-08-24)

RED `7aa7ac3d` (17 condemning tests, SKIP=pytest) → GREEN this change.

| Deliverable | Artifact |
|---|---|
| D-1 | `docs/agent-memory/README.md` |
| D-2 | `docs/agent-memory/repo/` seeded (56 notes); `shared/` empty — zero user notes promoted in the seed (R-1 strictest reading) |
| D-3 | `docs/agent-memory/manifest.json` (path, scope, sha256, promotion source) |
| D-4 | `scripts/memory_sync.py` (export/import/promote, `--force`, `--quiet`, sanitization, base-hash conflicts, env-var read-only mode) |
| D-5 | `.github/hooks/scripts/memory-import.sh` wired into SessionStart (`session-probe.json`); fail-open, bounded JSONL audit at `.github/hooks/logs/memory-sync.jsonl` (200-line cap) |
| D-6 | `capabilities/CAP-247-cross-device-agent-memory-sync.yaml` / REQ-YG-620; `tests/unit/test_memory_sync.py` (17 tests, `process`-marked, temp roots only per C-3) |

**Deviation (recorded):** the judgement's D-3 lists "last-import base hash"
as a manifest field; base hashes are machine-local by nature (each device
imports at different times), so committing them would reintroduce the
cross-device clobber the manifest exists to prevent. They live in
`<memory-root>/.import-base.json` per machine; the manifest carries the
shareable fields only. AC-05 semantics are unchanged.

**Seed secret-scan (R-5):** grep over the 56-note corpus for
key/token/password/secret/bearer patterns — all hits are NLP-domain
"token" prose; one flagged-for-review item: `repo/voice-projects-architecture.md`
contains a credential-recovery procedure (no credential
value). Session-scope notes excluded by construction (export reads repo
scope + promoted list only).

### Questions for the human

None open — the judgement resolved both drafted questions (R-1: opt-in
promotion; scope freeze: subrepo read-only in v1). The judgement is
advisory until human-reviewed.
