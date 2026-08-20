# Feature Request: FR-846 GitClaw Executable Control Bundle

**Priority:** CRITICAL
**Type:** Spike / enforcement infrastructure
**Status:** Judged — APPROVED WITH REVISIONS folded; human review pending
**Effort:** 0.5 day
**Requested:** 2026-08-20
**Blocks:** FR-845
**First consumer / first event:** A generic Copilot session in a clean GitClaw
clone loads YAMLGraph-mirrored instructions and skills, then successfully
invokes the independent judge, graph-authoring, and review adapters while the
mirrored hooks enforce their route boundaries.

**Prior art:** FR-844 proved Copilot CLI loads repository instructions but only
restated local contracts. FR-827 vendored skill prose without adapters/hooks,
causing GitClaw to imitate the process. FR-765/806/767 govern graph-authoring
adapter, preflight, and sentinel. NC-412/413/415 govern judge/review adapters and
serialization. FR-839 is unrelated rejected evidence. The prior combined
FR-845 judgement required this independent mirror spike.

## Summary

Build and prove the minimal executable YAMLGraph agent-control bundle required
by GitClaw's generic executor. Pin one YAMLGraph source SHA, mirror exact
instructions/skills/adapters/hooks/wrappers and only their measured transitive
helpers, verify hashes, and run clean-clone witnesses. Do not change GitClaw's
semantic harness under this FR.

## Ideal Result

A manifest can reconstruct the GitClaw agent environment from one YAMLGraph
commit. Copilot loads the same doctrine; judge, author, and review wrappers run
through their canonical YAMLGraph adapters; hooks deny bypasses and
unsentineled graph writes; local differences are explicit and human-reviewed.
No copied file silently drifts.

## Proposed Solution

### Frozen source classes

Mirror these source classes from one full YAMLGraph SHA:

1. `.github/copilot-instructions.md`;
2. `.github/skills/feature-request/**`;
3. `.github/skills/judge-fr/**`;
4. `.github/skills/graph-authoring/**`;
5. `.github/skills/review-pr/**`;
6. adapter wrappers `scripts/judge.sh`, `author.sh`, `review.sh`;
7. wrapper transitive helpers proven by static trace and clean execution;
8. `.github/hooks/` configs/scripts/helpers required for Copilot hook loading,
   authoring sentinel, command guard, and relevant post-edit checks.

Do not copy caches, logs, audit data, unrelated tests, Chaplain runtime,
release/diary scripts, or the complete YAMLGraph scripts tree.

### Manifest and local adaptation

Commit `control-bundle.json` with exact top-level keys: `version`, `source`,
`source_sha`, `bundle_roots`, and `files`. `bundle_roots` is a sorted unique
list containing exactly the GitClaw roots governed by bundle closure:

```text
.github/skills/feature-request
.github/skills/judge-fr
.github/skills/graph-authoring
.github/skills/review-pr
.github/hooks
scripts/control-bundle
```

Repository instructions and root wrapper entrypoints are explicit manifest
targets outside those roots. `files` is sorted by target and every entry has
exactly `{source,target,sha256,mode,disposition}`.
Disposition is `mirror` or `adapt-local`. `mirror` files are byte-identical.
Every `adapt-local` file has a paired Markdown rationale naming changed lines,
the GitClaw path assumption, and preserved guarantee. `omit-with-rationale` is
not allowed in the final bundle: if a required guarantee cannot be ported,
FR-846 fails and FR-845 remains blocked.

A standard-library verifier rejects duplicate/unknown keys, duplicate source or
target entries, malformed paths, targets outside bundle roots/explicit targets,
hash/mode mismatch, missing files, traversal, symlinks, dirty mirrored files,
and every regular file under a bundle root that lacks a manifest entry. Logs,
caches, temporary witness output, and runtime state live outside bundle roots.

### Transitive trace artifact

Commit `control-bundle-trace.md`. For every mirrored wrapper, adapter graph and
prompt, hook config/script, and helper, record every repository-relative path it
references and classify that reference as `mirror`, `adapt-local`, or
`not-runtime` with rationale. The manifest must equal the traced runtime set;
“minimal” is not asserted by intuition. Clean-clone execution may discover a
missing runtime reference, which must first be added to the trace and then to
the manifest.

### Hook guarantee boundary

The GitClaw runtime hook set preserves exactly these named guarantees:

1. deny `--no-verify`, AI co-author trailers, and multiline `git commit -m`;
2. preserve parse-ambiguity fail-closed behavior;
3. enforce authoring-sentinel denial for GitClaw governed graph/prompt paths;
4. allow only the sentineled author adapter execution to write those paths;
5. run applicable Python, YAML, and Markdown post-edit checks; and
6. retain audit/lockdown only if clean-clone tests prove their paths and state
   work in GitClaw.

Every adapted YAMLGraph governed path/checker has a rationale naming the
original guarantee, GitClaw mapping, and preserved test. Project-specific
checks that have no GitClaw consumer are listed `not-runtime` in the trace and
are not copied into the executable hook set.

### Runtime setup

The clean clone uses Python 3.12, Node 22, `npm install -g @github/copilot`, and
`pip install yamlgraph` from GitClaw's existing dependency model. Wrapper
witnesses set `YAMLGRAPH_BIN` to the resolved `yamlgraph` executable when PATH
resolution is not sufficient. Required POSIX shell utilities must be listed in
README. No `uv`, undeclared package manager, or new secret is assumed.

### Clean-clone witnesses

In a disposable clean clone with the same dependency install as GitClaw:

Evidence lives outside bundle roots under `tmp/fr-846-witness/`. Each witness
has a script/command log, expected artifact path, and exact assertion:

1. run a read-only/no-tools non-interactive Copilot probe; captured output must
   name `feature-request`, `judge-fr`, `graph-authoring`, and `review-pr`, and
   quote one distinctive mirrored repository-instruction invariant;
2. run `scripts/judge.sh` on a tiny committed FR and require
   `tmp/draft-judgement.md` with a non-empty `**Verdict:**` line;
3. run `scripts/author.sh` on a tiny task brief and require
   `tmp/draft-authoring-report.md`, all five required headings, at least one
   listed existing authored path, and lint plus smoke/explicit blocked-smoke
   evidence;
4. attempt direct unsentineled writes through file-tool and terminal-write
   shapes for every governed path class; require denial before mutation naming
   `scripts/author.sh`;
5. run `scripts/review.sh` against a real disposable branch/PR and require
   `tmp/draft-review.md` whose first line begins `**Merge verdict:**`, plus the
   actual consumed PR head in evidence;
6. execute named forbidden commit/bypass payloads and capture denial reasons;
   trigger one applicable post-edit failure and capture its surfaced error; and
7. run secret/history/log/artifact scan.

Wrappers/adapters remain advisory: they do not commit, push, comment, merge, or
poll issues. Witness GitHub mechanics are performed outside their processes.

### Exact change surface

Authorized in canonical GitClaw:

- mirrored bundle files and explicit local adaptations;
- `control-bundle.json` and adaptation rationale;
- standard-library parity verifier;
- focused parity/hook/adapter tests;
- disposable witness workflow/scripts and README provenance section.

Not authorized: current GitClaw graph/prompts/policy/workflows/ledger/cron;
feature or fixture migration; YAMLGraph source edits; Oulu work; new secrets;
production generic executor.

## Acceptance Criteria

- [ ] AC-01: Manifest pins one source SHA, exact bundle roots/explicit targets, and the traced required runtime file set
- [ ] AC-02: Trace records every path reference and disposition; included runtime files exactly match the manifest
- [ ] AC-03: Mirror hashes/modes match source; every adaptation records changed lines, mapping, original guarantee, and test
- [ ] AC-04: Verifier fails on schema, duplicate, path, traversal, symlink, hash, mode, missing, unlisted-root, and dirty-mirror violations
- [ ] AC-05: README/setup declares Python/Node/Copilot/YAMLGraph/POSIX requirements and executable resolution
- [ ] AC-06: Clean-clone probe names all four skills and quotes a mirrored instruction invariant
- [ ] AC-07: Judge wrapper produces a valid judgement artifact by artifact contract, not exit status
- [ ] AC-08: Author wrapper proves sentinel-authorized writes, direct-write denial, report headings, path existence, lint, and smoke evidence
- [ ] AC-09: Review wrapper consumes a real PR head and produces a valid line-one merge verdict artifact
- [ ] AC-10: Named hook guarantees and post-edit checks are witnessed under GitClaw paths with fail-closed ambiguity
- [ ] AC-11: Wrappers/adapters perform no Git/GitHub side effect
- [ ] AC-12: No unrelated YAMLGraph/runtime/cache/log/Chaplain or GitClaw semantic harness/cron/Oulu changes are included
- [ ] AC-13: Focused/full tests, clean-clone witnesses, and secret/history/log/artifact scans pass with commands and evidence recorded
- [ ] AC-14: Human reviews mirrored controls, adaptations, hooks, verifier, witnesses, and scans before push

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-844 | Confirms instruction loading; replace local restatement with source-pinned mirror |
| FR-827 vendored skills | Supersede prose-only snapshot with executable bundle |
| FR-765/806/767 | Preserve author adapter, preflight, and sentinel guarantees |
| NC-412/413/415 | Preserve sole judge/review routes, artifact gates, locks, and lineage |
| FR-839 | Rejected evidence only; do not revive generated approve/reject semantics. Preserve only the lesson that enforcement surfaces need executable gates and human review. |
| Prior combined FR-845 judgement | Folded: mirror spike separated from executor replacement |

## Alternatives Considered

- Skills without adapters/hooks: rejected; repeats current failure.
- Copy all YAMLGraph files: rejected; unbounded and imports unrelated doctrine.
- Edit mirrored core in place: rejected; drift becomes invisible.
- Omit a failed hook: rejected; re-judge the required guarantee instead.

## Judgement (2026-08-20)

**Verdict:** APPROVED WITH REVISIONS — R-1 through R-6 folded above; human
review remains required before enforcement.

| # | Finding | Resolution (binding) |
|---|---|---|
| R-1 | Bundle closure undefined | Added exact bundle roots, explicit targets, duplicate and unlisted-file rules |
| R-2 | “Minimal transitive” subjective | Added path-reference trace artifact and exact manifest equality |
| R-3 | Hook relevance ambiguous | Froze six GitClaw hook guarantees and adaptation/not-runtime treatment |
| R-4 | Witnesses prose-only | Added evidence directory, commands/artifacts, and exact assertions |
| R-5 | Runtime dependencies implicit | Froze clean-clone Python/Node/Copilot/YAMLGraph/POSIX setup and executable resolution |
| R-6 | FR-839 omitted from table | Added explicit rejected-precedent disposition |

**Purge list:** Unbounded script copy; caches/logs/audit data; silent hook
weakening; ambient-environment evidence; semantic harness changes; Git/GitHub
side effects inside adapters.

**Scope frozen:** Yes, subject to human review.

### Questions for the human

Human review of the folded judgement is required before enforcement.
