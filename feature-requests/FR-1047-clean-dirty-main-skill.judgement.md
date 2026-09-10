# Judgement: FR-1047 A `clean-dirty-main` skill — classify main's dirt by provenance before touching it

**Route:** `scripts/judge.sh feature-requests/FR-1047-clean-dirty-main-skill.md`, round 1, 2026-09-10, backend `copilot` (model `gpt-5.6-sol`). Promoted from the draft retained locally as `tmp/draft-judgement-copilot-FR-1047-clean-dirty-main-skill.md`. **Advisory until human-reviewed** (C-1, C-6).
**Prior art:** see FR-1047's own Prior art field (FR-889, FR-698, FR-241, FR-312) — this judgement reviews and dispositions those same citations; no additional precedent is introduced here.

**Verdict:** APPROVED WITH REVISIONS — the recurring diagnostic deserves a read-only route, but authority activates only after the FR replaces unprovable causal labels and broad cleanup with a conservative, fail-closed evidence contract.

**Reviewed against:** `feature-requests/FR-1047-clean-dirty-main-skill.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-889-os-enforced-main-write-lock.md`; `feature-requests/FR-698-executor-neutral-worktree-tooling.md`; `feature-requests/FR-241-complete-worktree-teardown-self-heal.md`; `feature-requests/FR-312-watcher2-post-merge-main-sync.md`; `docs/diary/diary-2026-09-03-the-lock-writes-half-a-pull.md`; `scripts/worktree.sh`; `.github/hooks/scripts/checks/main_write.py`; `capabilities/CAP-270-markdown-corpus-census.yaml`; `capabilities/CAP-271-pre-commit-gate-hygiene.yaml`. The `/memories/repo/hook-lessons.md` reference was not consumed because it is not a committed artifact in this repository.

## What is sound

The problem is real and recurrent: the first consumer and two witnessed invocations are named (`FR-1047`, lines 7–10), while the committed incident record confirms that every dirty file in the 2026-09-03 event matched `origin/main` and resulted from a partial pull (`diary-2026-09-03-the-lock-writes-half-a-pull.md`, lines 13–15). The record also confirms that `sync` alone cannot recover such residue and gives a proven recovery sequence (`diary-2026-09-03-the-lock-writes-half-a-pull.md`, lines 33–46).

The proposed boundary is appropriately small: one read-only classifier and one routing skill, with no new lock mutator, git wrapper, or automation (`FR-1047`, lines 112–115). That aligns with the existing audited `unlock-main`, `lock-main`, and always-relocking `sync` primitives (`FR-889`, lines 79–109; `scripts/worktree.sh`, lines 524–562). The classifier, skill, and prompt route form one operator-triage responsibility rather than a bundle.

The research field is substantive enough to pass the prospective research gate: prior art is dispositioned (`FR-1047`, lines 15–29), and six genuine solution classes are compared (`FR-1047`, lines 187–196). The text also answers `is_this_a_graph`: the decision is deterministic git plumbing over fixed inputs, not an LLM pipeline (`FR-1047`, lines 11–14). Strategic classification is **contrib/operator tooling**: one recurring operator use case has a gap in the existing `sync` abstraction (`FR-1047`, lines 7–10 and 62–65); this is not a YAMLGraph framework primitive.

The fixture-repository approach makes the core behavior directly testable (`FR-1047`, lines 158–174). Once the revisions below define unsupported states and safe action semantics, failing tests can be written for missing behavior rather than for missing fixtures or ambiguous expectations.

## Required revisions

### R-1: Classify evidence, not historical cause

Replace the claimed four-way causal classifier with three evidence classes:

1. `TARGET_IDENTICAL`: the working-tree bytes at path `p` equal the blob at the same path in `origin/main`; this is the only `SAFE` class.
2. `KNOWN_BLOB`: the bytes occur in another reachable commit but do not equal `origin/main:p`; report a source revision, but classify the path `PRESERVE/REVIEW`.
3. `UNSEEN_BLOB`: no examined reachable ref contains the bytes; classify the path `PRESERVE`.

Keep A–D only as incident explanations in the skill. Do not claim that the classifier proves them. A and D have the same specified signature (`FR-1047`, lines 53 and 56) and are already merged into one probe verdict (`FR-1047`, line 124); an older-blob match does not prove that a sibling editor wrote the file rather than that somebody intentionally restored old content (`FR-1047`, lines 54–55 and 125). Replace AC-02/AC-03's cause-A expectation with `TARGET_IDENTICAL`, and replace AC-05's cause-C expectation with `KNOWN_BLOB` plus `PRESERVE`.

Delete or qualify the claim that all four causes are witnessed. The committed diary proves A (`diary-2026-09-03-the-lock-writes-half-a-pull.md`, lines 13–15 and 65–70), but the FR delegates the C/D causal evidence to `/memories/repo/hook-lessons.md` (`FR-1047`, lines 66–70 and 93–98), which is outside the committed input closure. This revision preserves the useful provenance facts without presenting hypotheses as proof.

### R-2: Define the status domain and fail closed

Specify `git status --porcelain=v1 -z --untracked-files=all` so paths are NUL-delimited. Before classification, verify that the target is the shared main checkout, that `HEAD` is on `main`, and that `origin/main` resolves. Support only unstaged tracked regular-file modifications and untracked regular files in the first implementation.

Classify staged entries, deletions, renames/copies, unmerged entries, type changes, symlinks, submodules, non-regular files, and malformed status records as `UNSUPPORTED/PRESERVE`. Classify every git, filesystem, decode, or lookup failure as `ERROR/PRESERVE`; a failed probe must never become “no match.” Any `PRESERVE`, `UNSUPPORTED`, or `ERROR` count makes the process exit non-zero. Escape displayed paths unambiguously and test spaces, leading dashes, and control characters. This closes the gap between “every dirty path” (`FR-1047`, lines 33–35 and 106–107) and an algorithm that currently assumes every status entry has readable working-file bytes (`FR-1047`, lines 119–126).

### R-3: Remove repository-wide cleanup from the skill

Delete `git clean -fd` from the recovery contract (`FR-1047`, lines 139–142). If any path is `PRESERVE`, `UNSUPPORTED`, or `ERROR`, the skill must stop before unlocking or mutating anything, including paths marked safe. On an all-safe snapshot, cleanup may address only the exact classified paths, with an explicit `--` path separator; no repository-wide `checkout`, `restore`, `clean`, or deletion is authorized.

The skill must use the existing audited verbs and must restore the lock on every success and failure path. It may invoke `scripts/worktree.sh sync` only after the explicit residue paths have been restored/removed; `sync` already owns pull and relock behavior (`scripts/worktree.sh`, lines 554–562). Cause-B/`PRESERVE` handling must stop, report path and content hash, and hand control to the operator. Remove the instruction to “move the path into a worktree”: `scripts/worktree.sh new` creates a lane but does not transport dirty content (`FR-698`, lines 94–109), so the current text does not define a lossless operation.

### R-4: Make the safety claim honest and snapshot-bound

Replace “structurally impossible” (`FR-1047`, lines 104–110) with an advisory, fail-closed contract. A read-only report cannot prevent a later independent git command from discarding a path (`FR-1047`, lines 128–132). Each report must identify the repository root, `HEAD` OID, `origin/main` OID, status code, path, and working-content hash. The skill must rerun triage after any tree/ref change and immediately before cleanup; a changed snapshot aborts the procedure.

Define the summary as `safe=<n> preserve=<n> unsupported=<n> errors=<n>`. A clean tree exits 0 with all counts zero; an all-`TARGET_IDENTICAL` tree exits 0; every other result exits non-zero.

### R-5: Pin RED tests and requirement traceability

Add an enforcement sequence that creates and commits `tests/unit/test_dirty_main_triage.py` RED before production edits. Every test must carry `@pytest.mark.req("REQ-YG-678")`. Pin `capabilities/CAP-272-clean-dirty-main-triage.yaml` to `REQ-YG-678`, include the classifier, skill, instruction route, and test module in its witness surfaces, and regenerate `ARCHITECTURE.md` with `python scripts/aggregate_capabilities.py`. This folds the repo's requirement rule (`.github/copilot-instructions.md`, lines 168–170) into the FR instead of leaving “Capability YAML” unspecified (`FR-1047`, lines 181–184).

Pin the release record to `changelog/unreleased/fr1047-clean-dirty-main-skill.md`. Replace `pre-commit run --files <changed paths>` with the exact expected changed-path list, and add the required Distill artifact under `docs/diary/` with a `Seed:` (`.github/copilot-instructions.md`, lines 26 and 213).

### R-6: Test the safety contract, not document keywords

Replace the presence-only AC-07–AC-09 checks (`FR-1047`, lines 175–180) with behavioral assertions that the skill:

- invokes triage before any mutation;
- stops on non-zero status or any preserve/unsupported/error count;
- never contains `git clean -fd`, a repository-wide discard, or automatic preservation transport;
- uses only explicit `-- <path>` cleanup after an all-safe result;
- restores the main lock on every documented failure path;
- routes the literal phrase `check dirty main` from `.github/copilot-instructions.md`.

Retain valid frontmatter checks, but do not accept keyword presence as evidence that the destructive workflow is safe. Because `.github/copilot-instructions.md` is enforcement infrastructure, its exact routing change requires human review before merge (`judge-fr/doctrine.md`, lines 94–100).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised plan and implementation record in `feature-requests/FR-1047-clean-dirty-main-skill.md` |
| D-2 | Read-only classifier in `scripts/dirty_main_triage.py` |
| D-3 | Operator route in `.github/skills/clean-dirty-main/SKILL.md` |
| D-4 | One literal route entry in `.github/copilot-instructions.md` |
| D-5 | RED/GREEN acceptance tests in `tests/unit/test_dirty_main_triage.py` |
| D-6 | `capabilities/CAP-272-clean-dirty-main-triage.yaml` and generated `ARCHITECTURE.md` |
| D-7 | `changelog/unreleased/fr1047-clean-dirty-main-skill.md` |
| D-8 | One FR-1047 Distill entry under `docs/diary/` with a `Seed:` |

Not authorized: changes to `scripts/worktree.sh`; FR-889 lock roots, permissions, marker, audit, or relock behavior; `.github/hooks/scripts/checks/main_write.py`; hook/CI/branch-protection policy; watcher teardown or post-merge flows; automatic cleanup in `sync`; a new git wrapper or mutating classifier mode; graph, prompt, provider, or YAMLGraph runtime changes; classification of unsupported git states as safe.

## Revised acceptance criteria

- [ ] AC-01: On a clean shared `main` checkout with resolvable `origin/main`, `scripts/dirty_main_triage.py` exits 0 and prints `safe=0 preserve=0 unsupported=0 errors=0`.
- [ ] AC-02: A tracked regular file whose working bytes equal `origin/main` at the same path is `TARGET_IDENTICAL`; an all-safe fixture exits 0 with `safe=1`.
- [ ] AC-03: An untracked regular file whose bytes equal `origin/main` at the same path is `TARGET_IDENTICAL`, covering the committed 2026-09-03 incident shape.
- [ ] AC-04: Bytes found only in another reachable commit are `KNOWN_BLOB`, name a source revision, count as `preserve=1`, and produce a non-zero exit.
- [ ] AC-05: Bytes absent from examined reachable refs are `UNSEEN_BLOB`, count as `preserve=1`, and produce a non-zero exit.
- [ ] AC-06: `git status --porcelain=v1 -z --untracked-files=all` is parsed without path ambiguity; fixtures cover spaces, a leading dash, a newline/control character, and binary content.
- [ ] AC-07: A non-main branch, linked worktree, missing `origin/main`, staged entry, deletion, rename/copy, conflict, type change, symlink, submodule, non-regular file, or failed git/filesystem probe is never safe and produces a non-zero exit with an `unsupported` or `errors` count.
- [ ] AC-08: A mixed fixture containing one `TARGET_IDENTICAL` path and one preserve/unsupported/error path exits non-zero; the skill performs no cleanup for that result.
- [ ] AC-09: Before and after every classifier run, `HEAD`, refs, index, working-tree bytes, untracked-path set, and lock state are identical; output records root, `HEAD`, `origin/main`, status, escaped path, and content hash.
- [ ] AC-10: The skill has valid YAML frontmatter, contains the literal trigger `dirty main`, invokes triage first, reruns it after tree/ref changes, and stops before mutation on any non-zero or non-safe result.
- [ ] AC-11: The skill contains no `git clean -fd`, repository-wide discard, or automatic cause-B transport; the all-safe recipe uses explicit `-- <path>` pathspecs and restores the FR-889 lock on every documented exit.
- [ ] AC-12: `.github/copilot-instructions.md` routes the literal phrase `check dirty main` to `.github/skills/clean-dirty-main/SKILL.md`, with no unrelated doctrine edits.
- [ ] AC-13: `tests/unit/test_dirty_main_triage.py` is committed RED before production changes and every test is marked `REQ-YG-678`; `capabilities/CAP-272-clean-dirty-main-triage.yaml` registers that requirement and `python scripts/req_coverage.py --strict` passes after capability aggregation.
- [ ] AC-14: `changelog/unreleased/fr1047-clean-dirty-main-skill.md` records the operator-facing route and cites `REQ-YG-678`.
- [ ] AC-15: `pre-commit run --files` over the exact D-1–D-8 changed paths exits zero.
- [ ] AC-16: The FR records implementation status, RED/GREEN evidence, decisions, and deviations, and a Distill entry under `docs/diary/` contains a concrete heuristic and `Seed:`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1–R-6 into the FR and promote this judgement only after human review; no implementation authority exists before both actions. | GATE |
| C-2 | Commit the `REQ-YG-678` RED tests before editing production, skill, instruction, capability, changelog, or diary surfaces. | GATE |
| C-3 | Only `TARGET_IDENTICAL` may be marked safe; every ambiguity and every probe failure must preserve and exit non-zero. | GATE |
| C-4 | Any non-safe path blocks all cleanup, and no broad discard command may appear in code, tests, or the skill. | GATE |
| C-5 | Do not modify the existing lock, sync, hook, CI, watcher, or branch-protection implementations. | GATE |
| C-6 | A human must review the exact `.github/copilot-instructions.md` diff before merge because it changes enforcement infrastructure. | GATE |

Authority granted: after R-1–R-6 are folded and this advisory draft is human-reviewed and promoted, enforcement may build only the frozen read-only triage route and its traceability artifacts.
