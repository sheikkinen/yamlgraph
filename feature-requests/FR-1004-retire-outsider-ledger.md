# Feature Request: Retire the outsider ledger — the posted comment is the record

**Priority:** HIGH
**Type:** Removal
**Status:** Judged 2026-09-05 — APPROVED WITH REVISIONS ([judgement](FR-1004-retire-outsider-ledger.judgement.md)); R-1…R-4 folded below
**Effort:** 0.5 day
**Requested:** 2026-09-05
**First consumer / first event:** the author of the next PR that runs `scripts/outsider.sh <pr> --comment`, at the moment a second open PR has also run it — today that author is me, three times (PRs #594, #595, #596 each carry one appended row to the same file and conflict pairwise as they merge). Second consumer: whoever counts distinct outsider-read PRs toward FR-995's "twenty before any gate" threshold — they run one `gh search` instead of reading a committed file.
**Research:** in-body — the *Problem* section is the witnessed record (three concurrent PRs, one shared append-only file, 2026-09-05), and the *Alternatives* table is the dispositioned design space. `is_this_a_graph`: **no new LLM decision** is introduced — this is deletion of committed derived state plus relocation of provenance fields into the report the graph already renders — **but an existing graph artifact (`.github/skills/outsider-view/adapters/graph.yaml`) is materially modified** (its typed state grows by the observation fields), so that change goes through `scripts/author.sh` (R-3).
**Prior art:** [FR-995](FR-995-outsider-reader.md) and its [judgement R-3](FR-995-outsider-reader.judgement.md) — created the ledger as D-7 with the attributability contract (timestamp, repo, PR, head SHA, input SHA-256, model, prompt digest, tool SHA, derived verdict, s3/s4 counts, report path; rows for every validated real-PR run; distinct-PR dedup). This FR **changes two things** in that contract and keeps the rest: (a) the *storage* moves from a committed JSONL file every PR mutates to the HTML marker of the posted comment; (b) the *counted population* narrows from "every validated real-PR run" to "every validated real-PR run whose comment was successfully posted" — a `pr` run without `--comment` was a ledger row before and is not an observation after (see R-1 fold in *Ideal Result*). `report_path` is retired: the posted comment *is* the durable report location. [FR-858](FR-858-retire-committed-fr-board.md) retired the committed FR board for the same reason — a derived artifact every PR mutated — the highest-ranked cure in the shared-tree hazard ladder (diary [2026-08-23 the-worktree-is-the-airlock](../docs/diary/2026-08-23-the-worktree-is-the-airlock.md)). Operator calibration (*additive default*): a composing artifact shipped; the subtraction proposal follows. Scripture `seeds.artifact_carries_code_identity` — satisfied by marker fields on the artifact, not by a file. No REJECTED FR in this territory (`grep -l ledger feature-requests/*.md` → FR-995 only; FR-873's "ledger" is deviant-daily's publication ledger, a different artifact in a different repo).

## Summary

`docs/census/outsider-ledger.jsonl` is an append-only file that every outsider run against a real PR writes one line to, and that line is committed in that PR. Two PRs open at the same time both append → the second to merge conflicts on a one-line JSONL file and needs a rebase. Today three PRs are in that state at once. The file records nothing that the PR comment the same run posts could not carry, so: delete the file, move its fields into the comment's existing HTML marker, and count distinct PRs with one `gh search` when the count is wanted.

## Value Statement

The person who runs the outsider on their PR does not inherit a merge conflict from whoever ran it on theirs; the measurement FR-995 wanted (twenty distinct PRs before any gate) is still answerable in one command, from the place the observation actually happened.

## Problem

### Witnessed today (2026-09-05)

| PR | adds a ledger row | state |
|---|---|---|
| #594 (FR-995 exec-bit fix; row for #593) | yes | rebased once already; conflicts with #595 or #596 when the other lands |
| #595 (FR-995 Scripture entry; row from its own dogfood run) | yes | same |
| #596 (FR-998 docs; row for #596) | yes | merged first; the other two now conflict on rebase |

Three authors (all the same operator's sessions), one file, pairwise conflicts on a line that is *derived* — it repeats what the posted comment says. The judge that created the ledger asked for attributable, non-gameable observations (FR-995 R-3); it did not ask for them to live in a file that every PR mutates. The mutation is the defect. The cure ladder for shared-tree hazards is already written down (diary 2026-08-23): *retire the contended artifact > worktree airlock > per-shape choreography*. This is rung one.

### What the file holds vs. what the comment carries today

Comparing a row (`docs/census/outsider-ledger.jsonl`) with the marker the same run posts (`render_report` in [outsider_tools.py L146-150](../.github/skills/outsider-view/adapters/outsider_tools.py#L146)):

| field | ledger row | comment marker today | after this FR |
|---|---|---|---|
| UTC timestamp | ✓ | ✓ | ✓ |
| model | ✓ | ✓ | ✓ |
| repo, PR number | ✓ | implicit | ✓ explicit |
| derived verdict | ✓ | ✓ (first body line) | ✓ also in marker |
| s3 / s4 counts | ✓ | derivable | ✓ in marker |
| PR head SHA (full) | ✓ | ✗ | ✓ |
| input SHA-256 (full 64 hex) | ✓ | ✗ | ✓ |
| prompt digest | ✓ | ✗ | ✓ |
| tool git SHA | ✓ | ✗ | ✓ |
| report path | ✓ (repo-relative `tmp/…`, never committed — dangling) | — | **retired** — the comment is the report location |
| `source:` | — | ✓ (a `mktemp` path under `/var/folders/…`) | **dropped** — exposes only the disposable child path |

The wrapper already computes head SHA, prompt digest and tool SHA ([outsider.sh L67-68, L123](../scripts/outsider.sh#L67)) — it hands them to the ledger instead of the report.

## Ideal Result

A run of `scripts/outsider.sh <pr> --comment` leaves exactly one **durable measurement record**: the comment on that PR, whose first line is the derived verdict and whose HTML marker carries the typed observation (R-2 fields). Outsider execution changes **no tracked repository state**; validated local reports and logs under git-ignored `tmp/` remain diagnostic artifacts, as FR-995 intended. "How many distinct PRs has the outsider read?" is one `gh search` returning a number.

**Counted population (R-1):** one observation is countable **only when a validated real-PR report is successfully posted as a PR comment.** `--input`, `--selftest`, graph failures, parse failures, comment failures, and `pr` mode without `--comment` produce no observation. The last item is a narrowing relative to FR-995 (whose ledger recorded non-comment PR runs; #591 was such a row with no comment) and is deliberate: a measurement that lives only on one workstation's `tmp/` is not a measurement.

## Proposed Solution

### S-1: delete the committed ledger

- `git rm docs/census/outsider-ledger.jsonl` (rows for #591, #592, #596 on main; #593/#595 rows on the two open branches — those PRs drop the file on rebase, or the deletion wins the conflict).
- `scripts/outsider.sh`: remove `LEDGER`, `OUTSIDER_LEDGER`, the post-comment ledger append block (L132-140) and the `ledger:` echo; the `--input` usage note "no ledger row" becomes "no observation".
- `outsider_tools.py`: delete `ledger_row`, `append_ledger`, `distinct_pr_count`; module docstring updated.
- Tests: the ledger tests in `tests/unit/test_fr995_outsider_reader.py` and `tests/unit/test_fr995_outsider_wrapper.py` are rewritten to the marker/observation assertions in S-5.

### S-2: the typed observation marker (R-2)

New Pydantic model `Observation` in `outsider_tools.py` with exactly: `ts` (UTC ISO-8601, `Z`), `repo`, `pr` (int or `-`), `head_sha` (full 40-hex or `-`), `input_sha256` (full 64-hex), `model`, `prompt_digest`, `tool_sha`, `derived_verdict` (`YES`/`NO`), `s3` (int), `s4` (int). `render_report` takes an `Observation` and emits one marker line:

```
<!-- outsider reader | ts: 2026-09-05T12:11:22Z | repo: sheikkinen/yamlgraph | pr: 596 | head: 1edb9e82…(40) | input: acb34bfc…(64) | model: gpt-5.6-sol | prompt: 3f9c2a1b… | tool: 2e67a32a… | verdict: NO | s3: 4 | s4: 6 -->
```

`parse_observation(report_text) -> Observation` round-trips it. `source:` is gone. `--input` / `--selftest` reports render with `-` for `repo`/`pr`/`head_sha` and are **not countable** (they are never posted). The `**Derived verdict:**` first line, the parser, the verdict rule, the model and the prompt are unchanged (C-7).

### S-3: provenance flows through the graph (R-3)

Today `finalize_report` renders inside the graph and the graph state carries only `input_path`, `report_path`, `model`. Change:

- `graph.yaml` state gains `repo: str`, `pr: str`, `head_sha: str`, `prompt_digest: str`, `tool_sha: str` (the *base* observation fields; verdict and counts come from the validated report inside `finalize_report`, where the `Observation` is constructed). The wrapper passes them as `--var`s; `-` placeholders for non-PR modes.
- This is a material `graph.yaml` change → an FR-1004 **authoring brief** (`feature-requests/authoring-briefs/fr-1004-outsider-observation.md`) routed through `scripts/author.sh`; `tmp/draft-authoring-report.md`, `yamlgraph graph lint` and the `--selftest` smoke are retained as evidence (C-6). No prompt change.
- The wrapper test fakes: the fake `yamlgraph` consumes the new `--var`s; the fake `gh pr comment` preserves the `--body-file` content so the posted body can be asserted byte-for-byte.

### S-4: the count is a query, not a file (R-1)

Documented in `SKILL.md` and `doctrine.md` (doctrine stays ≤ 60 lines). The search marker is **transition-safe** — it matches the pre-FR-1004 comments already posted (`<!-- outsider reader | source: …`) and the new marker:

```bash
gh search prs --repo sheikkinen/yamlgraph 'in:comments "<!-- outsider reader |"' --limit 1000 --json number
gh search prs --repo sheikkinen/yamlgraph 'in:comments "<!-- outsider reader |"' --limit 1000 --json number --jq length
```

GitHub returns each PR once regardless of how many matching comments it has — the distinct-PR dedup FR-995 R-3 asked for, without code. Historical comments are **not** rewritten to make the query pass. The FR-995 sentence "twenty distinct PRs before any gate FR" stays; its instrument changes from a file to this line and its population to posted comments.

### S-5: tests (RED first, `SKIP=pytest`; then GREEN) — in the two existing FR-995 test modules

1. `Observation` / `render_report` / `parse_observation`: every field present exactly once; full 40/64-hex lengths; UTC `Z` timestamp; no `source:`; round-trip equality; placeholder rendering for `--input`.
2. Wrapper `pr --comment` success: the fake `gh pr comment` body equals the validated report file byte-for-byte; its marker's `head`/`input` equal what the fake `gh pr view` returned and the SHA-256 of the fetched text; no path under `docs/` created or modified; `git status --porcelain` of the lane unchanged by the run; `OUTSIDER_LEDGER` set in the environment has no effect.
3. Wrapper comment failure: non-zero exit; no `docs/` write; no tracked-file mutation.
4. Wrapper `pr` without `--comment`: validated report written under `tmp/`; no comment; nothing under `docs/`.
5. `--input`, `--selftest`, graph-failure, parse-failure: no comment, nothing under `docs/` (existing tests, re-asserted).
6. Static: `ledger` absent from `scripts/outsider.sh` and `outsider_tools.py`; `doctrine.md` ≤ 60 lines.

### S-6: traceability and the active contract

- `capabilities/CAP-263-outsider-reader.yaml`: REQ-YG-662 rewritten — the S-2 marker schema, the R-1 inclusion rule, `report_path` retired; `fr: FR-995, FR-1004`; regenerate `ARCHITECTURE.md`.
- FR-995 *active contract* annotated in three places: Proposed Solution 7 ("Measurement"), AC-11, and the implementation record — each with one sentence "superseded by FR-1004: storage = posted comment marker; population = successfully posted comments; `report_path` retired". Its judgement and spike artifacts are not touched.

### S-7: credentialed witness (AC-07)

On the enforcing PR: `scripts/outsider.sh <pr> --comment`; then the S-4 query. Record in the implementation record: the posted marker verbatim, the **returned PR-number set** verbatim, and that the enforcing PR appears **exactly once**. No predicted minimum. If the search does not return the enforcing PR, the replacement is not demonstrated and enforcement stops (C-5).

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: `docs/census/outsider-ledger.jsonl` is deleted; `git grep -n ledger -- scripts/outsider.sh .github/skills/outsider-view` returns no active ledger implementation or instruction.
- [ ] AC-02: Every rendered report carries one typed marker with exactly one UTC timestamp, repo, PR, full head SHA, full input SHA-256, model, prompt digest, tool SHA, derived verdict, s3, s4 — and no `source:` or temp path. Non-PR reports use `-` placeholders and are not countable.
- [ ] AC-03: `report_path` is recorded as retired (superseded by the comment location) in FR-1004 and FR-995; no text claims the old fields or inclusion rules are unchanged.
- [ ] AC-04: No mode of `scripts/outsider.sh` creates or modifies a path under `docs/` or any tracked file; validated local reports/logs may remain under git-ignored `tmp/`; `OUTSIDER_LEDGER` is absent from active code and has no effect.
- [ ] AC-05: `pr --comment` posts exactly the enriched validated report; the fake captures `--body-file` and its head/input values match the fake `gh pr view` result and the fetched text's SHA-256. Comment failure exits non-zero and creates no durable record.
- [ ] AC-06: A non-comment PR run writes its validated report under `tmp/` and is excluded from the count; `--input`, `--selftest`, graph, parse and comment failures are excluded too.
- [ ] AC-07: `SKILL.md` and `doctrine.md` document the transition-safe search and the comment-only population; the credentialed enforcing-PR run records the returned PR-number set, shows the enforcing PR exactly once, and quotes the actual count with no speculative minimum.
- [ ] AC-08: `graph.yaml` typed state carries the base observation fields into `finalize_report`; the change has a committed authoring brief, a valid `tmp/draft-authoring-report.md`, lint and smoke evidence.
- [ ] AC-09: Direct tests cover marker completeness/uniqueness, digest lengths, UTC shape, placeholders, round-trip, posted-body identity, no `docs/` writes, no tracked-file mutation, ignored `OUTSIDER_LEDGER`, non-comment exclusion, comment-failure exclusion.
- [ ] AC-10: REQ-YG-662 / CAP-263 describe the marker schema and comment-only rule with `fr: FR-995, FR-1004`; `ARCHITECTURE.md` regenerated; every changed test carries a REQ marker; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-11: FR-995 Proposed Solution 7, AC-11 and implementation record carry the superseding sentence; its judgement and spike artifacts are unchanged.
- [ ] AC-12: RED commit precedes GREEN; `changelog/unreleased/fr-1004-retire-outsider-ledger.md` (`type: removal`, `scope: outsider`, `req: REQ-YG-662`); the implementation record cites both commits and the witness.
- [ ] AC-13: The diff touches none of the unauthorised surfaces (automation, CI/hooks, blocking verdict, model/prompt/parser/verdict rule, historical comments or spike outputs, other census artifacts, new subcommand, judge/review doctrine).
- [ ] AC-14: `docs/diary/2026-09-05-reflection-fr-1004-*.md` with `**Seed:**`.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A | Delete the file; observation into the comment marker; count via `gh search` | **Chosen.** Zero committed state; eleven typed fields kept, `report_path` retired, `source:` dropped; zero new subcommands. |
| B | Keep the file, write rows only on `main` (a post-merge job) | Rejected: a job that commits to `main` on every merge is the chaplain's shape (FR-889 lock, post-merge finalization) for a one-line derived fact; the comment already exists at that moment. |
| C | Keep the file, move it out of the PR path (`.gitignore` + local only) | Rejected: a measurement that lives on one workstation is not a measurement (`artifact_carries_code_identity` wants provenance *with* the artifact, and the artifact here is the comment). |
| D | Keep the file, resolve conflicts with a merge driver (`merge=union`) | Rejected: works mechanically but keeps every PR touching one file and every author learning why; the cure ladder says retire first. |
| E | Store rows as check-run annotations or a gist | Rejected: a second write target with its own auth and failure mode, when the comment is already the write. |
| F | Do nothing; rebase as needed | Rejected: three conflicts on day one of the instrument; the cost compounds with adoption, which is the goal. |
| G | Keep non-comment PR runs countable by posting a hidden marker-only comment | Rejected: a comment nobody asked for on someone's PR to satisfy a counter; the count is not worth the noise. Population narrows instead (R-1). |

## Related

- [FR-995](FR-995-outsider-reader.md), [judgement](FR-995-outsider-reader.judgement.md) R-3, D-7, AC-11 — what this retires and what it keeps.
- [FR-998](FR-998-anthropic-constrained-structured-output.md) — PR #596, one of the three conflicting rows.
- [FR-858](FR-858-retire-committed-fr-board.md), [docs/diary/2026-08-23-the-worktree-is-the-airlock.md](../docs/diary/2026-08-23-the-worktree-is-the-airlock.md) — the cure ladder.
- PRs #594, #595, #596 — the witnessed conflict set.
