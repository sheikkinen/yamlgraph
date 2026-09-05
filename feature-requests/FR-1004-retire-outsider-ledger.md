# Feature Request: Retire the outsider ledger — the posted comment is the record

**Priority:** HIGH
**Type:** Removal
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-09-05
**First consumer / first event:** the author of the next PR that runs `scripts/outsider.sh <pr> --comment`, at the moment a second open PR has also run it — today that author is me, three times (PRs #594, #595, #596 each carry one appended row to the same file and will conflict pairwise as they merge). Second consumer: whoever counts distinct outsider-read PRs toward FR-995's "twenty before any gate" threshold — they run one `gh search` instead of reading a committed file.
**Research:** in-body — the *Problem* section is the witnessed record (three concurrent PRs, one shared append-only file, 2026-09-05), and the *Alternatives* table is the dispositioned design space. `is_this_a_graph: No` — deletion of committed derived state plus relocation of six provenance fields into an existing HTML marker; no LLM decision.
**Prior art:** [FR-995](FR-995-outsider-reader.md) and its [judgement R-3](FR-995-outsider-reader.judgement.md) — created the ledger as D-7 with the attributability contract (timestamp, repo, PR, head SHA, input SHA-256, model, prompt digest, tool SHA, verdict, counts, report path; rows only for validated real-PR runs; distinct-PR dedup). This FR keeps every one of those *fields* and *inclusion rules* and retires only the *storage*: a committed JSONL file appended by every PR. [FR-858](FR-858-retire-committed-fr-board.md) (retire the contended artifact — the highest-ranked cure in the shared-tree hazard ladder, diary [2026-08-23 the-worktree-is-the-airlock](../docs/diary/2026-08-23-the-worktree-is-the-airlock.md)): same move, different artifact. `growth_as_default` / operator calibration (*additive default*): a composing artifact shipped; the subtraction proposal follows. Scripture `seeds.artifact_carries_code_identity` — satisfied by the marker fields, not by a file. No REJECTED FR in this territory (`grep -l "ledger" feature-requests/*.md` → FR-995 only; FR-873's "ledger" is deviant-daily's publication ledger, a different artifact in a different repo). [FR-858](FR-858-retire-committed-fr-board.md) retired the committed FR board for the same reason — a derived artifact every PR mutated.

## Summary

`docs/census/outsider-ledger.jsonl` is an append-only file that every outsider run against a real PR writes one line to, and that line is committed in that PR. Two PRs open at the same time both append → the second to merge conflicts on a one-line JSONL file and needs a rebase. Today three PRs are in that state at once. The file records nothing that the PR comment the same run posts could not carry, so: delete the file, move its provenance fields into the comment's existing HTML marker, and count distinct PRs with one `gh search` when the count is wanted.

## Value Statement

The person who runs the outsider on their PR does not inherit a merge conflict from whoever ran it on theirs; the measurement FR-995 wanted (twenty distinct PRs before any gate) is still answerable in one command, from the place the observation actually happened.

## Problem

### Witnessed today (2026-09-05)

| PR | adds a ledger row | state |
|---|---|---|
| #594 (FR-995 exec-bit fix; row for #593) | yes | rebased once already; will conflict with whichever of #595/#596 lands first |
| #595 (FR-995 Scripture entry; row from its own dogfood run) | yes | same |
| #596 (FR-998 docs; row for #596) | yes | same |

Three authors (all the same operator's sessions), one file, pairwise conflicts on a line that is *derived* — it repeats what the posted comment says. The judge that created the ledger asked for attributable, non-gameable observations (FR-995 R-3); it did not ask for them to live in a file that every PR mutates. The mutation is the defect. The cure ladder for shared-tree hazards is already written down (diary 2026-08-23): *retire the contended artifact > worktree airlock > per-shape choreography*. This is rung one.

### What the file actually holds that the comment does not

Comparing a row (`docs/census/outsider-ledger.jsonl`) with the marker the same run posts (`render_report` in [outsider_tools.py L146-150](../.github/skills/outsider-view/adapters/outsider_tools.py#L146)):

| field | ledger row | comment marker today |
|---|---|---|
| UTC timestamp | ✓ | ✓ |
| model | ✓ | ✓ |
| repo, PR number | ✓ | implicit — the comment is on that PR |
| derived verdict | ✓ | ✓ (first line of the body) |
| s3/s4 counts | ✓ | derivable from the body |
| PR head SHA | ✓ | ✗ |
| input SHA-256 | ✓ | ✗ |
| prompt digest | ✓ | ✗ |
| tool git SHA | ✓ | ✗ |
| report path | ✓ (repo-relative `tmp/…`, never committed — dangling) | — |
| `source:` | — | ✓ (a `mktemp` path in `/var/folders/…` — meaningless to any reader) |

Four provenance fields are missing from the comment; one comment field is noise; one ledger field points at a file that never exists after the run. The wrapper already computes all four missing values ([outsider.sh L67-68, L123](../scripts/outsider.sh#L67)) — it just hands them to the ledger instead of the marker.

## Ideal Result

A run of `scripts/outsider.sh <pr> --comment` leaves exactly one durable trace: the comment on that PR, whose first line is the derived verdict and whose HTML marker carries every FR-995 R-3 provenance field. Nothing in the repository changes because the outsider ran. "How many distinct PRs has the outsider read?" is one `gh search` returning a number. Runs that do not post (fixtures, `--input`, `--selftest`, failures, `pr` mode without `--comment`) leave no trace anywhere, and the doctrine says so in one sentence.

## Proposed Solution

### S-1: delete the committed ledger

- `git rm docs/census/outsider-ledger.jsonl` (rows for #591, #592 on main; #593/#595/#596 rows on the three open branches — those PRs drop the file on rebase, or the deletion wins the conflict).
- `scripts/outsider.sh`: remove `LEDGER`, `OUTSIDER_LEDGER`, the post-comment ledger append block (L132-140) and the `ledger:` echo; the `--input` usage note "no ledger row" becomes "no record".
- `outsider_tools.py`: delete `ledger_row`, `append_ledger`, `distinct_pr_count` (L172-end of section); module docstring updated.
- Tests: delete the ledger tests in `tests/unit/test_fr995_outsider_reader.py` and `tests/unit/test_fr995_outsider_wrapper.py` (21 references; the wrapper tests `test_pr_mode_success_writes_one_attributable_row`, `test_comment_failure_writes_no_ledger_row`, `test_input_mode_success_writes_report_and_no_ledger` are rewritten to assert the marker, per S-2).

### S-2: relocate the R-3 provenance into the comment marker

`render_report(report, verdict, *, model, source)` becomes `render_report(report, verdict, *, provenance: Provenance)` where `Provenance` is a small Pydantic model with the FR-995 R-3 fields: `repo`, `pr`, `head_sha`, `input_sha256`, `model`, `prompt_digest`, `tool_sha`, `ts` (UTC). The marker line becomes:

```
<!-- outsider reader | repo: sheikkinen/yamlgraph | pr: 596 | head: 1edb9e82 | input: acb34bfc… | model: gpt-5.6-sol | prompt: 3f9c2a1b… | tool: 2e67a32a | 2026-09-05T12:11:22Z -->
```

`source:` (the temp path) is dropped. For `--input`/`--selftest` runs `repo`/`pr`/`head_sha` are `-` and the marker still renders — so a report's provenance is complete wherever it is read. The wrapper passes the values it already computes; it computes nothing new. The `**Derived verdict:**` first line is unchanged, so the FR-995 non-gameability property (verdict computed in code, front-loaded) is untouched.

### S-3: the count is a query, not a file

Document in `SKILL.md` and `doctrine.md` (keeping doctrine ≤ 60 lines):

```bash
gh search prs --repo sheikkinen/yamlgraph 'in:comments "<!-- outsider reader | repo:"' --json number --jq 'length'
```

Distinct PRs are distinct search hits (GitHub search returns each PR once regardless of comment count) — the dedup rule FR-995 R-3 wanted, for free. The FR-995 sentence "twenty distinct PRs before any gate FR" stays; its measurement instrument changes from a file to this line. No new subcommand.

### S-4: traceability

`capabilities/CAP-263-outsider-reader.yaml`: rewrite REQ-YG-662's description — same fields, "carried in the posted comment's HTML marker; runs that do not post leave no record; distinct-PR count is the documented `gh search`" — and add `fr: FR-995, FR-1004`. Regenerate `ARCHITECTURE.md`. FR-995: one *Implementation record* sentence ("ledger retired by FR-1004; provenance lives in the comment marker") and D-7/AC-11 annotated, not rewritten.

### S-5: tests (RED first, `SKIP=pytest`; then GREEN)

1. `render_report` output's marker contains all eight provenance fields and no `source:`; `--input` provenance renders with `-` placeholders.
2. Wrapper (fakes on PATH, as today): `pr --comment` success → the fake `gh pr comment` body file's marker carries the head SHA and input SHA-256 the fake `gh pr view` returned; no file under `docs/census/` is created or modified; `OUTSIDER_LEDGER` in the environment has no effect.
3. Wrapper: comment failure → non-zero exit, no `docs/census/` write (the old P2 property, restated without the ledger).
4. AST/grep: `ledger` does not appear in `scripts/outsider.sh` or `outsider_tools.py`.
5. `doctrine.md` ≤ 60 lines (existing test, must stay green after the S-3 sentence).

## Acceptance Criteria

- [ ] AC-01: `docs/census/outsider-ledger.jsonl` is deleted; `git grep -n ledger -- scripts/outsider.sh .github/skills/outsider-view` returns nothing.
- [ ] AC-02: A `pr --comment` run's posted body carries a marker with repo, PR, head SHA, input SHA-256, model, prompt digest, tool SHA, UTC timestamp, and no temp path (S-2, test 1-2).
- [ ] AC-03: No mode of `scripts/outsider.sh` writes under `docs/` (test 2-3); `OUTSIDER_LEDGER` is gone.
- [ ] AC-04: `SKILL.md` and `doctrine.md` document the `gh search` count (S-3); doctrine ≤ 60 lines; the FR-995 threshold sentence is unchanged in meaning.
- [ ] AC-05: REQ-YG-662 rewritten in CAP-263 with `fr: FR-995, FR-1004`; `ARCHITECTURE.md` regenerated; every changed test carries its REQ marker; `python scripts/req_coverage.py --strict` green.
- [ ] AC-06: RED commit precedes GREEN; changelog fragment `changelog/unreleased/fr-1004-retire-outsider-ledger.md` (`type: removal`, `scope: outsider`, `req: REQ-YG-662`).
- [ ] AC-07: One credentialed run of `scripts/outsider.sh <this PR> --comment` on the enforcing PR; the posted marker is quoted in the FR implementation record; `gh search` count quoted alongside (expected ≥ 4: #591, #592, #593, #596, plus this PR).
- [ ] AC-08: FR-995 implementation record gets the one sentence in S-4; diary `docs/diary/2026-09-05-reflection-fr-1004-*.md` with `**Seed:**`.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A | Delete the file; provenance into the comment marker; count via `gh search` | **Chosen.** Zero committed state; every R-3 field kept; zero new subcommands. |
| B | Keep the file, write rows only on `main` (a post-merge job) | Rejected: a job that commits to `main` on every merge is the chaplain's shape (FR-889 lock, post-merge finalization) for a one-line derived fact; the comment already exists at that moment. |
| C | Keep the file, move it out of the PR path (`.gitignore` + local only) | Rejected: a measurement that lives on one workstation is not a measurement (`artifact_carries_code_identity` wants provenance *with* the artifact, and the artifact here is the comment). |
| D | Keep the file, resolve conflicts with a merge driver (`union`) | Rejected: `.gitattributes merge=union` on JSONL works mechanically but keeps every PR touching one file and every author learning why; the judge's cure ladder says retire first. |
| E | Store rows as GitHub check-run annotations or a gist | Rejected: a second write target with its own auth and failure mode, when the comment is already the write. |
| F | Do nothing; rebase as needed | Rejected: three conflicts on day one of the instrument; the cost compounds with adoption, which is the goal. |

## Related

- [FR-995](FR-995-outsider-reader.md), [judgement](FR-995-outsider-reader.judgement.md) R-3, D-7, AC-11 — what this retires and what it keeps.
- [FR-998](FR-998-anthropic-constrained-structured-output.md) — PR #596, one of the three conflicting rows.
- [docs/diary/2026-08-23-the-worktree-is-the-airlock.md](../docs/diary/2026-08-23-the-worktree-is-the-airlock.md) — the cure ladder.
- PRs #594, #595, #596 — the witnessed conflict set.
