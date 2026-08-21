# Judgement: FR-848 GitClaw Obsolete Artifact Purge

**Verdict:** APPROVED WITH REVISIONS - authority is active after R-1 through R-4 were folded into the FR.

**Prior art:** FR-845's generic executor and FR-847's one-task cron/haiku runtime remain current. FR-848 explicitly supersedes FR-847's temporary decision to retain the embedded pre-FR-847 haiku FR, judgement, and review. YAMLGraph FR-847 and Git history remain the authority trail.

## What Is Sound

The purge is real, bounded, and subtractive. It names exactly 13 tracked files whose runtime, examples, tests, or architecture were deleted by FR-845/847. No live runtime, test, control manifest, or README consumes them. Git history already preserves the records.

The retained boundary is explicit: generic executor/intake/control bundle, canonical skills/adapters/hooks, cron, README, and the haiku graph/prompt/current authoring report remain unchanged. The one-time spike workflow is enforcement infrastructure, so its removal requires human review before push.

## Required Revisions

| # | Finding | Binding resolution |
|---|---|---|
| R-1 | FR-847 explicitly retained three haiku governance files | State that FR-848 supersedes that boundary and identify FR-847 plus Git history as continuing authority |
| R-2 | “No tracked references” mixed historical evidence with consumers | Define all 13 paths in `OBSOLETE_PATHS` and scan only live consumer surfaces, excluding authority/history and the test constant |
| R-3 | Local cleanup could remove tracked files without durable evidence | Require a pre-clean tracked-file guard and post-clean ignored/untracked status witness |
| R-4 | Dead-code AC named no existing command | Delete it; use the focused consumer scan instead |

All revisions are folded into FR-848.

## Frozen Scope

Authorized:

- delete exactly the 13 paths listed in FR-848;
- add exact `.gitignore` entries `tmp/` and `logs/*.log`;
- add one dependency-free repository-hygiene test;
- update FR-848, this judgement, generated board, and one diary reflection;
- safely remove local residue after the tracked-file guard.

Not authorized: graph/prompt, README, cron/intake/executor/control-bundle, skill/adapter/hook, dependency, secret, permission, schedule, or output-contract changes; broad `outputs/` ignore; deletion of `tools/__init__.py`; deletion of the current haiku graph, prompt, or authoring report; replacement archive/index/migration artifacts.

## Conditions for Enforcement

1. Delete exactly the 13 named tracked files and no others.
2. Prove the RED test before deleting them.
3. Preserve all frozen live surfaces byte-for-byte.
4. Guard local cleanup against tracked files and record the post-clean status witness.
5. Obtain human review of the destructive deletion and spike-workflow removal before push.

Authority granted for the folded FR-848 scope only.
