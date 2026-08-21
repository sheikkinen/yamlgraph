# Feature Request: FR-848 GitClaw Obsolete Artifact Purge

**Priority:** MEDIUM
**Type:** Removal / repository hygiene
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-08-21
**Depends on:** FR-847
**First consumer / first event:** A template user opens GitClaw after FR-847
and sees only the current executor, one scheduled haiku task, and evidence that
describes those live contracts.

**Prior art:** FR-845 retired the custom semantic harness; FR-847 retired the
generic cron runtime, output publisher, composition examples, and old cron
tests. Both intentionally kept their immediate change surfaces narrow. The
post-FR-847 audit found files whose only consumer or subject is now deleted.
Git history already preserves those implementation and acceptance records.

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-845 | Retain the generic executor/control bundle; delete reports for the superseded custom harness |
| FR-847 | Retain cron and the haiku runtime; intentionally supersede FR-847's retained `features/haiku/FR.md`, `judgement.md`, and `review.md` boundary because they govern the scheduler-completed predecessor |
| Git history | Remains the archive and authority trail for deleted issue-era GitClaw artifacts |
| YAMLGraph FR-847 | Remains current authority for the self-sufficient haiku and one-task scheduler |

## Summary

Delete obsolete GitClaw spike, generated output, test-log, authoring-report, and
superseded embedded haiku governance artifacts. Ignore local `tmp/` and test-log
evidence so adapter runs and acceptance work do not repeatedly dirty the tree.

Retain the live haiku graph, prompt, and current authoring report; retain the
generic executor, intake workflow, control bundle, canonical skills/adapters,
tests, and current README.

## Value Statement

GitClaw remains a truthful public template instead of presenting historical
experiments, deleted-runtime output, and superseded specifications as current
product surfaces.

## Problem

FR-847 removed 1,617 lines but left 538 tracked lines in 13 files that no live
runtime, test, control manifest, or README consumes:

- one manual Copilot CLI spike workflow created only for FR-827 AC-01;
- three generated outputs from the deleted generic output publisher, including
  two outputs for examples that no longer exist;
- RED/GREEN logs for tests and cron behavior that FR-847 deleted;
- four standalone authoring reports describing the deleted monolithic harness,
  verdict gates, push-race handling, and horoscope bootstrap; and
- `features/haiku/FR.md`, `judgement.md`, and `review.md`, which describe the old
  scheduler-provided date, fixed-city prompt, and horoscope precedent rather
  than the self-sufficient graph enforced by FR-847.

The stale governance files are not the authority for FR-847; the judged FR and
implementation record live in YAMLGraph, while Git history preserves the
original issue-era artifacts. Keeping contradictory prose in the active feature
directory increases the chance that an agent restores the retired design.

Local adapter and acceptance evidence also remains visible after every run:
`tmp/` currently holds FR-845/846/847 briefs, reports, logs, and witness data;
untracked `logs/green2.log` and `logs/red2.log` duplicate obsolete acceptance
evidence. Empty `policy/` and `state/` directories are filesystem residue.

## Ideal Result

The tracked GitClaw tree contains no one-time spike workflow, generated cron
output, historical test logs, reports for deleted architecture, or contradictory
haiku governance. `features/haiku/` contains only:

- `graph.yaml`;
- `prompts/haiku.yaml`; and
- `authoring-report.md`.

Adapter scratch files and local test logs do not appear in `git status`. Empty
residue directories and current local evidence are removed. All tests, graph
lint, and control-bundle verification remain green.

## Proposed Solution

### 1. Delete obsolete tracked artifacts

Delete exactly:

- `.github/workflows/spike-copilot-cli.yml`;
- `outputs/2026-08-20-daily-aphorism-about-software-craft.md`;
- `outputs/2026-08-20-haiku.md`;
- `outputs/2026-08-20-horoscope.md`;
- `logs/red.log` and `logs/green.log`;
- all four `docs/authoring-report-2026-08-20-*.md` files;
- `features/haiku/FR.md`;
- `features/haiku/judgement.md`; and
- `features/haiku/review.md`.

This is 13 files / 538 tracked lines. Do not replace them with archive,
supersession, index, or migration files; Git history is the archive.

### 2. Prevent recurring local residue

Add to `.gitignore`:

```gitignore
tmp/
logs/*.log
```

Keep `outputs/routes/` ignored. Do not ignore all `outputs/`; a future task may
explicitly own and version an output artifact under separately judged scope.

After tracked changes are committed, first run a tracked-file guard over
`tmp/`, `logs/`, `outputs/routes/`, `policy/`, and `state/`. The guard must show
that the only tracked files under those targets are the two authorized log
deletions; after their commit, it must show no tracked files. Only then remove
local untracked/ignored evidence and empty directories.

Record a post-clean
`git status --porcelain --untracked-files=all --ignored` witness proving no
entry remains under `tmp/`, `logs/*.log`, `outputs/routes/`, `policy/`, or
`state/`.

### 3. Add a repository-hygiene witness

Add one dependency-free test that asserts:

1. all 13 obsolete paths are absent;
2. `features/haiku/` contains exactly graph, prompt directory, and current
   authoring report;
3. `.gitignore` contains exact `tmp/` and `logs/*.log` entries;
4. `.github/workflows/cron.yml`, `.github/workflows/intake.yml`, `gitclaw.yaml`,
   control-bundle files, canonical skills/adapters, and retained haiku artifacts
   remain present; and
5. an `OBSOLETE_PATHS` constant contains all 13 deleted paths and no live
  consumer surface references any entry.

The consumer scan includes retained workflows, README, control manifests,
retained feature runtime files, scripts/tools, and existing tests. It excludes
authority/history artifacts (FRs, judgements, reviews, diary entries, Git
history) and the hygiene test's own `OBSOLETE_PATHS` constant. Historical
mentions are evidence, not live consumers.

The RED commit must fail against the current tracked residue. The GREEN commit
performs only the authorized purge and ignore changes.

## Exact Change Surface

Authorized:

- deletion of the 13 files listed above;
- `.gitignore`;
- one focused repository-hygiene test;
- updates to this FR, its judgement, generated FR board, and diary reflection;
- local cleanup of `tmp/`, `logs/`, `outputs/routes/`, `policy/`, and `state/`.

Not authorized:

- modification of any graph or prompt artifact;
- cron, intake, executor, publisher, containment, request/reference, or control-
  bundle implementation changes;
- skill, adapter, hook, README, dependency, secret, permission, schedule, or
  output-contract changes;
- deletion of `tools/__init__.py`, which remains the explicit package marker;
- deletion of the current haiku authoring report; or
- creation of replacement archive/documentation artifacts.

## Acceptance Criteria

- [ ] AC-01: RED commit adds `tests/test_repository_hygiene.py` and fails because the 13 obsolete tracked paths exist and exact `.gitignore` entries `tmp/` and `logs/*.log` are absent
- [ ] AC-02: GREEN deletes exactly the 13 named obsolete tracked paths / 538 lines, with no replacement archive, supersession, index, or migration artifact
- [ ] AC-03: `features/haiku/` contains exactly `graph.yaml`, `prompts/haiku.yaml`, and `authoring-report.md`; its old FR, judgement, and review are absent
- [ ] AC-04: `.gitignore` contains exact standalone entries `tmp/` and `logs/*.log`; `outputs/routes/` remains ignored; no bare `outputs/` or equivalent broad output ignore is introduced
- [ ] AC-05: The hygiene test defines all 13 paths in `OBSOLETE_PATHS` and proves no live consumer surface references any entry, excluding only authority/history artifacts and the test constant itself
- [ ] AC-06: Generic executor, intake workflow, control-bundle files, canonical skills/adapters/hooks, cron workflow, README, retained haiku graph/prompt/authoring report, and `tools/__init__.py` are byte-unchanged
- [ ] AC-07: Local cleanup is preceded by a tracked-file guard and followed by `git status --porcelain --untracked-files=all --ignored` evidence showing no residue matching `tmp/`, `logs/*.log`, `outputs/routes/`, `policy/`, or `state/`
- [ ] AC-08: `python -m pytest tests/test_repository_hygiene.py -q`, `python -m pytest tests/ -q`, `yamlgraph graph lint features/haiku/graph.yaml`, and `python -m tools.control_bundle` pass
- [ ] AC-09: Human review approves the destructive 13-file deletion and workflow removal before push
- [ ] AC-10: FR-848 records implementation status, decisions/deviations, validation evidence, and the required diary reflection

## Alternatives Considered

- **Keep historical evidence in the live tree:** rejected; Git history already
  preserves it, while current-tree presence implies current authority.
- **Move files to `archive/`:** rejected; relocation preserves clutter and
  creates a new documentation surface with no reader.
- **Update the old haiku FR/judgement/review:** rejected; they governed a
  superseded implementation and rewriting historical authority falsifies the
  record.
- **Ignore all outputs:** rejected; task-owned versioned outputs remain a valid
  future contract even though cron no longer owns them.
- **Delete `tools/__init__.py`:** rejected; zero-byte package markers are not
  evidence of obsolescence.

## Related

- `feature-requests/FR-845-gitclaw-generic-skill-executor.md`
- `feature-requests/FR-847-cron-schedules-one-yamlgraph-task.md`
- `docs/diary/2026-08-20-cron-schedules-the-task.md`

## Judgement

**Verdict:** APPROVED WITH REVISIONS - all revisions folded below; enforcement
authority is active.

| # | Finding | Folded resolution |
|---|---|---|
| R-1 | FR-847 explicitly retained three haiku governance files | Prior Art Disposition now explicitly supersedes that boundary while preserving FR-847 and Git history as authority |
| R-2 | “No tracked references” confused historical evidence with live consumers | Focused test now scans named live consumer surfaces using all 13 `OBSOLETE_PATHS` |
| R-3 | Local cleanup evidence was aspirational and could remove tracked files | Require pre-clean tracked-file guard and post-clean ignored/untracked status witness |
| R-4 | Dead-code scan had no named existing command | Removed; consumer-orphan protection belongs in the focused hygiene test |

**Purge list:** Exactly the 13 named tracked files plus guarded local residue.
No replacement archive or documentation is permitted.

**Scope frozen:** Yes. No graph, prompt, README, cron, intake, executor,
control-bundle, skill, adapter, hook, dependency, permission, schedule, secret,
or output-contract change is authorized. Human review is mandatory before push.

### Questions for the human

None.
