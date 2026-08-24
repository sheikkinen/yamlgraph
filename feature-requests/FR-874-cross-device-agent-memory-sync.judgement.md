# Judgement: FR-874 Cross-Device Agent Memory Sync via Git-Tracked Note Store

**Verdict:** APPROVED WITH REVISIONS — the portability defect is real and the git-transport shape is minimal, but authority activates only after the FR pins opt-in privacy, conflict metadata, subrepo discovery, and observable fail-open behavior.

**Reviewed against:** `feature-requests/FR-874-cross-device-agent-memory-sync.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `feature-requests/TEMPLATE.md`; `.github/copilot-instructions.md`; `docs/diary/diary-2026-07-16-a-map-for-the-amnesiac.md`; `scripts/vscode/README.md`; `scripts/vscode/MAP.md`; `feature-requests/FR-617-memory-note-taking-primitive.md`; `feature-requests/FR-743-sessionstart-briefing-hook.md`. The cited `/memories/repo/where-repo-notes-live.md` was not consumed because it is not a committed artifact found in this repo.

**Prior art:** FR-617 and FR-743 dispositioned in "What is sound" below;
FR-243 is proposal transport, not note sync; FR-782/FR-824/FR-831 are noun
collisions with no territorial overlap (see the FR's Prior art section).

## What is sound

The problem is evidenced, not speculative: the FR states that repo and user memory live under local VS Code storage rather than git (`feature-requests/FR-874-cross-device-agent-memory-sync.md:15-23`), and the diary records the same filesystem fact: one repo on two machines has two disjoint repo memories (`docs/diary/diary-2026-07-16-a-map-for-the-amnesiac.md:10-19`). The storage map corroborates the exact memory-tool locations under `globalStorage` and `workspaceStorage` (`scripts/vscode/README.md:95-111`).

The first consumer is concrete: an agent starting on another device at SessionStart (`feature-requests/FR-874-cross-device-agent-memory-sync.md:8-11`). The ideal result is appropriately boring: git is the transport, the memory tool remains the local cache, and no service or daemon is introduced (`feature-requests/FR-874-cross-device-agent-memory-sync.md:49-55`). Strategic classification: **pattern/tooling for repo operations**, not a framework primitive; it serves this repo's agent practice and subrepo hub workflow, while FR-617 remains the separate graph-level memory primitive (`feature-requests/FR-874-cross-device-agent-memory-sync.md:121-124`; `feature-requests/FR-617-memory-note-taking-primitive.md:11-20`).

The prior-art disposition is mostly adequate: FR-617 supplies the no-traversal, explicit miss, and concurrent-clobber warnings (`feature-requests/FR-617-memory-note-taking-primitive.md:44-54`), and FR-743 supplies the SessionStart fail-open seam (`feature-requests/FR-743-sessionstart-briefing-hook.md:55-62`). The FR also correctly rejects symlinking into VS Code-managed stores (`feature-requests/FR-874-cross-device-agent-memory-sync.md:104-107`), aligning with the mapped seam that VS Code storage should be treated carefully (`scripts/vscode/MAP.md:52-60`).

## Required revisions

### R-1: Freeze `shared/` as explicit opt-in promotion only

Replace the open human question about `shared/` export policy with a binding rule: user-scope notes are exported only when explicitly named/promoted, never by export-all with denylist. The FR already hints at designated shareability (`feature-requests/FR-874-cross-device-agent-memory-sync.md:61-64`) but then reopens the decision (`feature-requests/FR-874-cross-device-agent-memory-sync.md:142-146`). A git-tracked peer-shared store makes privacy and leak prevention part of scope, not implementation taste.

### R-2: Define the conflict contract without relying on filesystem mtime

Replace "locally-newer" with a mechanical manifest contract: each imported note records the repo content hash it last imported; import refuses overwrite when the local file content differs from that base and the repo file also changed, unless `--force` is supplied. Filesystem mtimes are not stable across git checkout, devices, or editor writes. The FR's "content-hash aware" export (`feature-requests/FR-874-cross-device-agent-memory-sync.md:65-68`) should be extended into the import conflict rule and tested.

### R-3: Specify the subrepo master-clone discovery mechanism

Replace "path discovered via a small config or convention" (`feature-requests/FR-874-cross-device-agent-memory-sync.md:74-76`) with one exact mechanism. Use a committed config file or environment variable name, define the failure mode when absent, and test that subrepo mode is read-only in v1. As written, this acceptance surface is not mechanically enforceable.

### R-4: Make fail-open import observable

Keep SessionStart import fail-open, but require it to emit a bounded audit record or warning when import fails. FR-743 permits a briefing hook to exit 0 on failure (`feature-requests/FR-743-sessionstart-briefing-hook.md:55-62`), but repo doctrine forbids silent success-shaped failures (`.github/copilot-instructions.md:217-221`). A broken sync must not block a session, but it also must not masquerade as successful sync.

### R-5: Gate the initial seeded corpus with a manifest and human review

Change "seeded with the current exportable corpus" (`feature-requests/FR-874-cross-device-agent-memory-sync.md:88-90`) to require a committed manifest listing seeded note paths, scopes, hashes, and promotion source. The seed must exclude session-scoped notes and any note containing secrets, credentials, customer-private data, or local-only machine paths unless manually redacted. The judge cannot inspect the local memory corpus under input closure; the enforcement gate must make the exported corpus reviewable before commit.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `docs/agent-memory/README.md` documenting canonical repo store, local cache semantics, explicit `shared/` promotion, seed review, and subrepo read-only contract |
| D-2 | `docs/agent-memory/repo/` and `docs/agent-memory/shared/` seeded only after manifest-backed review |
| D-3 | `docs/agent-memory/manifest.json` or equivalent deterministic manifest with path, scope, content hash, and last-import base hash |
| D-4 | `scripts/memory_sync.py` implementing `export`, `import`, `--quiet`, `--force`, path sanitization, manifest-based conflict detection, and subrepo read-only import |
| D-5 | FR-743 SessionStart hook integration that runs import fail-open and records bounded failure evidence |
| D-6 | Capability/requirement artifact and pytest coverage for the sync behavior |
| D-7 | `feature-requests/FR-874-cross-device-agent-memory-sync.md` updated with implementation status, decisions, and deviations |
| D-8 | `docs/diary/` reflection for the enforcement session |

Not authorized: bidirectional subrepo write-back; automatic export at SessionStart; export-all user-scope behavior; background daemon/service/watch mode; symlinking VS Code memory-tool directories into the repo; writing outside memory-tool note roots; graph-level memory primitive changes under FR-617; changes to judge/review doctrine, CI, or hook policy beyond the FR-743 SessionStart integration.

## Revised acceptance criteria

- [ ] AC-01: `docs/agent-memory/{repo,shared}/` and README exist; README states git-tracked store vs local cache, explicit opt-in `shared/` promotion, excluded content classes, and subrepo read-only behavior.
- [ ] AC-02: Initial seed includes a manifest with every committed note path, scope, content hash, and promotion source; no session-scoped notes are seeded.
- [ ] AC-03: `scripts/memory_sync.py export` copies repo-scope notes and explicitly promoted shared notes into `docs/agent-memory/`, updates the manifest, reports adds/updates, and never exports unpromoted user-scope notes.
- [ ] AC-04: Export -> wipe test -> import reproduces exported note bytes and manifest base hashes for a temporary memory-tool root.
- [ ] AC-05: Import refuses overwrite when local content diverged from the recorded base hash and repo content changed; `--force` overwrites and records the new base hash.
- [ ] AC-06: Import sanitizes all note paths and rejects traversal, absolute paths, symlinks escaping the target root, and non-`.md` note payloads.
- [ ] AC-07: Subrepo import discovers the yamlgraph master store through the specified config/env mechanism, imports read-only, and errors observably when the master path is absent or invalid.
- [ ] AC-08: FR-743 SessionStart integration runs `memory_sync.py import --quiet` fail-open and emits a bounded audit/warning record on failure.
- [ ] AC-09: Tests are tagged with a new `REQ-YG-XXX`; matching capability file is added.
- [ ] AC-10: The FR records implementation status and any deviations; a diary reflection is included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 into the FR before implementation authority activates. | GATE |
| C-2 | Treat the seed corpus as human-reviewed content; do not commit generated exports until the manifest and exclusions make the diff auditable. | GATE |
| C-3 | Use temporary memory-tool roots in tests; tests must not read or write the operator's real VS Code memory directories. | GATE |
| C-4 | Any failure in SessionStart import must fail open but leave bounded evidence; no silent pass, no session block. | GATE |
| C-5 | Keep subrepo behavior read-only in v1. | GATE |

Authority granted: after revisions are folded into the FR, implement a manifest-backed git note store and explicit sync script for repo/shared agent memory, wired into SessionStart import fail-open with observable failure reporting.
