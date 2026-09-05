# Feature Request: Outsider reader — an adversarial third reader for PR (and FR) descriptions

**Priority:** HIGH
**Type:** Enhancement (process instrument, advisory)
**Status:** Enforced 2026-09-05 (PR #592) — D-1…D-10 delivered under the [judgement](FR-995-outsider-reader.judgement.md); reviewed via `scripts/review.sh` (six blocking findings, all fixed — see *Review record*). Positive fixture derives YES on one run and NO on another; recorded as the instrument's nature, not a defect.
**Effort:** 1 day (spike exists; skill layout + wrapper + canary fixtures)
**Requested:** 2026-09-05
**First consumer / first event:** the author of any `feat`/`fix` PR, at the moment the PR is opened and before `scripts/review.sh` runs — the outsider's report tells them what a reader with no project context cannot understand from the title and body. Second consumer: the reviewer, who receives the "what a merge decision would still need" list and partitions it into *exists-but-unlinked* and *absent*. Third: this FR itself (dogfood — see Acceptance Criteria).
**Research:** [docs/2026-09-05-research-plan-cap-journey-census.md §12](../docs/2026-09-05-research-plan-cap-journey-census.md) — the spike record inside the plan for the *capability census* (a survey of the 242 capability records in `capabilities/`, which is where the unreadable PR description came from); (setup, two prompt versions, three canaries with expectations written before each run, results, conclusions), and the committed spike copy at [docs/spikes/outsider-reader-2026-09-05/](../docs/spikes/outsider-reader-2026-09-05/) (graph, prompt v1 and v2, tools, wrapper, inputs, six reports, `EXPECTATIONS.md`). Alternatives dispositioned in-body.
**Prior art:** [.github/skills/judge-fr/doctrine.md](../.github/skills/judge-fr/doctrine.md) — reads an FR *with* doctrine; this reader reads *without* anything (inverted input closure). [.github/skills/review-pr/doctrine.md](../.github/skills/review-pr/doctrine.md) — reads a PR against its FR and judgement with file access; this reader has no file access and no FR; it runs *before* review and hands review its checklist. [scripts/review.sh](../scripts/review.sh) — wrapper shape copied (lock, artifact check, exit code not trusted). [FR-742](FR-742-undelivered-diary-detection.md) — successor briefing; same "addressed to whoever is addressed to no one" problem, different artifact. Diary [2026-07-16-the-human-skims](../docs/diary/diary-2026-07-16-the-human-skims.md) — documents optimise for the next agent, not the human; this FR makes that measurable per PR. No REJECTED FR found in this territory (grep of `feature-requests/` for "outsider", "plain language", "readability", "comprehension": none).

## Summary

**Scope of this PR: the feature request and the committed spike copy only.** Nothing is implemented here; implementation follows judgement.

A reader that knows nothing about this project reads a pull request's title and body — and nothing else — and reports, in four fixed sections, what it understood, what it could not understand, and what a merge decision would still need. It runs on `gpt-5.6-sol` (the model the repo's FR judge uses) from a directory outside the repository (so the Copilot CLI cannot load the project's instructions), has no file access and no tools, and its output is advisory. It runs when a PR is opened, before the repo's PR review step (`scripts/review.sh`). In this FR the author invokes it by hand; automatic invocation on PR open is deferred together with the gate decision (Alternatives #6). Reading FR bodies is not in scope (Alternatives #7).

## Value Statement

Authors learn, before a reviewer's time is spent, which parts of their description only make sense to someone who already knows the project; reviewers receive a checklist of what the description did not tell them.

## Problem

On 2026-09-05 the operator judged four consecutive recaps and PR #591's description unreadable to an outsider ("even I have hard time understanding what's being said"). The description was a pasted commit message in project shorthand. The rulebook already says *who reads this when* and *substance over presence*; neither fired, because the only reader in the loop was the author, whose vocabulary is the problem. An author-side "write plainly" rule was considered and rejected: it asks the writer to judge their own clarity — same session, same priors, same blind spot (the recap failures happened while the author held the rule in mind).

The spike (plan §12) ran a context-free reader on three inputs. Against the original #591 body it produced 33 things it could not understand and could not say who the change was for. Against the operator-approved plain rewrite it restated the change correctly but still found six phrases that assumed team context ("the business plan", "the fast, cheap one we had agreed to try"). Against the final body it said YES and listed five project-specific terms, which were then glossed. It also found a real defect the humans missed: the plain rewrite's title claimed a census of 242 while the text reported 30. Its "what is missing" section listed sixteen items of which ten existed in the PR but were not pointed to, and six were genuinely absent — including automated tests on a `feat` PR, a rule violation found by a reader who has never seen the rule.

## Raw Output Read (measurement / metric-tooling FRs only)

- **Samples read:** six reports, all read end-to-end, committed under [docs/spikes/outsider-reader-2026-09-05/out/](../docs/spikes/outsider-reader-2026-09-05/out/): `pr-591-*` (original body, prompt v1 and v2), `plain-591-*` (approved plain account, v1 and v2), `pr-591-v2-*` (rewritten body, v2).
- **What I saw:**
  - v1 on the plain account: 41 items, 16 typed "undefined term" — for *plain English* ("what counts as use", "what does valid mean", "someone running a pipeline"). Told to "be exhaustive", the model interrogated ordinary words as if they were jargon. The item count did not separate a bad description (33) from a good one (41); it scaled with text length and diligence.
  - v1 restatement of the original body: "instruments and pilots *something called* the FR-990 CAP journey census … the intended users are not stated." The hedge is the signal. The restatement of the plain account was correct in one read. Restatement separates; count does not.
  - v2 (comprehension-only, cap 8): counts became informative — 8 (original body, all real shorthand) / 6 (plain account) / 5 (rewritten body). The six on the plain account were all self-referential team context; the operator-approved text was plain but not self-contained.
  - v2's YES/NO produced a **false YES** on the original body: "30/30" and a wildcard path satisfied "what was found" and "where to look". The verdict cannot be asked of the model.
  - Report B's chapter 4 (v1), checked line by line against the PR: 10 of 16 "missing" items existed but were unlinked; 6 were absent (tests, runs 1–2, indirect-use evidence, cost, locality, model comparison). The reader cannot partition these — only someone with the files can. That is the reviewer handoff.
  - `cli_flags.model: "{state.model}"` is not templated; the CLI failed with *Model "{state.model}" is not available* and exit 0 / empty output. The artifact check caught it; the exit code would not have.

## Ideal Result

An author who has just opened a `feat`/`fix` PR runs one command and gets, in about a minute, a report from a reader with zero project context: one paragraph restating the change, at most eight phrases it could not understand, and a short list of what a merge decision would still need. The author fixes the text; the reviewer partitions the list. A verdict derived in code (not the model's) says whether the description stands alone. Every real-PR run appends one attributable ledger row; after twenty distinct PRs the rows say whether "could not understand" items per PR fell. Automatic invocation on PR open and any blocking gate are **separate future FRs**, each needing its own judgement (R-4).

## Proposed Solution

Copy the spike; do not reinvent it.

1. **Skill layout** — `.github/skills/outsider-view/`: `doctrine.md` (what it is; inverted input closure — title + body only, no files, no tools, no doctrine, run from a clean directory; what it is not — not a reviewer, not a rewriter, not a gate; output advisory), `adapters/graph.yaml` and `adapters/prompts/outsider.yaml` copied from `docs/spikes/outsider-reader-2026-09-05/` via the repo's required process for graph files (`scripts/author.sh`: an agent writes the YAML from a committed brief; direct edits to graph files are blocked by a hook), the brief citing the spike files as the source; `adapters/README.md` in the judge/review style.
2. **Wrapper** — `scripts/outsider.sh <pr-number>`, copied from the spike's `outsider.sh` (itself copied from `review.sh`): fetches title + body with `gh pr view`, writes the PR text to a **clean temporary directory outside the repo**, runs the graph from there with `yamlgraph graph run` (the repo's own CLI, from its virtualenv), verifies the report by artifact (heading `## 1. In my own words` present), never trusts the exit code. The temporary directory is deleted after the run; the report is kept under `tmp/` (git-ignored). A directory lock serialises runs (so two runs cannot collide, including on the ledger), and an environment marker stops the reader from launching another copy of itself — both copied from `review.sh`.
3. **Typed report boundary and derived verdict** (R-2) — a Python tool node after the model normalises the model text into a Pydantic model: non-empty section-1 restatement; model opinion `YES|NO` + one reason; 0–8 section-3 items (quote, question); 0–10 section-4 items. All four numbered headings exactly once, in order; the literal `nothing` is an empty list; missing, duplicate, reordered, over-cap or malformed sections **fail closed**: non-zero wrapper result, no comment, no ledger row. Only from that validated model is the verdict derived: **YES iff section-3 count ≤ 2 and section 1 contains none of** `does not say`, `something called`, `not stated`, `cannot tell` (case-insensitive). The report front-loads `**Derived verdict:** YES|NO`; the model's section-2 answer is kept and labelled as its non-authoritative opinion. Direct tests for every failure class.
4. **Model** — `gpt-5.6-sol`, pinned literally in `cli_flags` (operator decision: PR-level text is read by the same model the FR judge uses). No `allow_all_paths`, no `allow_all_tools`. Cost: one model call per PR, about a minute, drawn from the Copilot subscription — no per-token bill.
5. **Fixtures and self-test** (R-1) — the spike inputs and `EXPECTATIONS.md` move to `.github/skills/outsider-view/fixtures/`. `--selftest` runs the fixture set and requires derived **NO / NO / NO / YES** for: original #591 body (`pr-591.md`), plain account (`plain-591.md`), pre-gloss rewritten body (`pr-591-v2.md`), and a **final-glossed positive** whose expectation is written before its output is produced. All six historical reports derive NO under the rule (the rewritten-body report has 5 items and the hedge "the text does not say"; the dogfood report has 8 items). The threshold is not loosened to fit observed counts. See *Fixtures — the search for a positive* below for the three passes already recorded.
6. **Posting** — the wrapper prints the report path; posting it as a PR comment is a separate explicit `--comment` flag, off by default, and the only code path that calls `gh pr comment`. Nothing auto-merges, auto-approves, or blocks. No workflow, hook, scheduled service, or automatic PR-open invocation (R-4).
7. **Measurement** (R-3) — one JSONL row per *successfully parsed, artifact-validated invocation against a real GitHub PR*, appended to `docs/census/outsider-ledger.jsonl` while the wrapper lock is held and only after report validation. Fields: UTC timestamp, repository, PR number, PR head SHA, SHA-256 of the exact title+body input, pinned model, prompt/adapter version or digest, local tool git SHA, derived verdict, section-3 count, section-4 count, report path. Self-tests, dry runs, parse failures, graph failures and comment failures write **no** row. "Twenty rows before a gate" means twenty **distinct PRs**, latest successful observation per PR.
8. **Artifact surface** (R-5) — `.github/skills/outsider-view/{SKILL.md (discovery frontmatter + manual command), doctrine.md (≤ 60 lines), adapters/README.md, adapters/graph.yaml, adapters/prompts/outsider.yaml, adapters/<typed tool module>, fixtures/}`; `feature-requests/authoring-briefs/fr-995-outsider-reader-brief.md` naming every graph artifact; `scripts/outsider.sh`; focused unit and wrapper tests under `tests/`; one new `capabilities/CAP-*.yaml` + `ARCHITECTURE.md` REQ; changelog fragment; FR implementation record; one diary entry. The adapter README must state: the sole manual command, input closure, artifact path, derived-vs-model verdict distinction, advisory status, forbidden actions.

## Acceptance Criteria (revised by the judgement; originals superseded)

- [x] AC-01: The FR cites `feature-requests/authoring-briefs/fr-995-outsider-reader-brief.md`; `scripts/author.sh` produces the named graph/prompt/tool artifacts and a valid `tmp/draft-authoring-report.md`; the authored graph passes `yamlgraph graph lint` and a recorded smoke attempt. *(brief committed; report's smoke was blocked by the Pydantic forward-ref defect, fixed; post-repair smoke = the wrapper runs recorded below)*
- [x] AC-02: The skill bundle contains `SKILL.md`, doctrine of at most 60 lines, adapter README, graph, prompt, and typed tool module. The docs state the manual command, title-plus-body-only input closure, three-reader division, derived/model verdict distinction, advisory boundary, artifact path, and forbidden actions.
- [x] AC-03: The adapter pins `gpt-5.6-sol` literally and contains neither `allow_all_paths` nor `allow_all_tools`. A wrapper test proves the child cwd is outside the repository and contains no `.github/`, while absolute graph/tool/report paths still resolve.
- [x] AC-04: The wrapper fetches title, body, and PR head SHA; holds one repo-scoped directory lock; rejects recursive execution; removes temporary input on success, graph failure, and parse failure; preserves the validated report under repo `tmp/`; and validates the complete report contract rather than only the section-1 heading. *(P1/P4 fixed after review; behavioural tests)*
- [x] AC-05: Model text is normalized into the R-2 Pydantic model. Missing, duplicate, reordered, malformed, and over-cap sections fail closed; no failed run comments or writes a ledger row. *(P3 fixed after review)*
- [x] AC-06: The derived verdict is case-insensitively computed as section-3 count `<= 2` and absence of all four hedge markers. The report front-loads that verdict and clearly labels the model's section-2 answer as opinion.
- [x] AC-07: Tests classify all historical reports (nine committed) as NO under the derived rule and one newly committed final-glossed model report as YES. The FR dogfood record says the eight-item pre-fix report derived NO and links the actual PR comment plus each item's disposition. *(the same fixture also has a committed NO report; both asserted)*
- [x] AC-08: `scripts/outsider.sh --selftest` runs original, plain-account, pre-gloss rewritten, and final-glossed fixtures and requires derived `NO/NO/NO/YES`; expectations for the new positive are committed before its output. *(passed once at 06:25–06:26Z; the positive is known to flicker)*
- [x] AC-09: A credentialed `scripts/outsider.sh 591` smoke writes a structurally valid report from the current GitHub title/body. Its observed counts and verdict are recorded without changing the fixed unit expectations if the model drifts. *(07:34Z: derived NO, 6 items / 6 needs; report under the spike directory; ledger row 2)*
- [x] AC-10: `--comment` is off by default. Mocked wrapper tests prove only explicit `--comment` posts exactly the validated report to the requested PR and that no self-test, dry run, or failed run posts.
- [x] AC-11: Each successful real-PR run appends exactly one locked JSONL row with every R-3 field. Tests prove excluded modes/failures write none and repeated PR runs cannot satisfy the twenty-distinct-PR prerequisite.
- [x] AC-12: A new capability record and `ARCHITECTURE.md` requirement cover the feature; every test has the matching `@pytest.mark.req`; `python scripts/req_coverage.py --strict` passes.
- [x] AC-13: The spike directory remains unchanged as historical evidence and is cited from the skill README; a changelog fragment, FR implementation/status record, and metacognitive diary entry are added. *(new reports were appended to the spike `out/`; no historical output edited)*
- [x] AC-14: The diff contains none of the explicitly unauthorized surfaces (see judgement — no automation, CI/hook changes, gate, auto-comment, FR-body input, judge/review/guard changes, model selection logic, PR rewriting, merge/approval actions, edits to historical spike outputs).

## Dogfood record (AC-05 of the original list; AC-07 now)

The spike reader was run on this FR's first-pushed text: report at
[docs/spikes/outsider-reader-2026-09-05/out/fr-995-gpt-5.6-sol-20260905T054043Z.md](../docs/spikes/outsider-reader-2026-09-05/out/fr-995-gpt-5.6-sol-20260905T054043Z.md),
posted as [PR #592 comment](https://github.com/sheikkinen/yamlgraph/pull/592#issuecomment-5549746082).
**Derived verdict on the pre-fix text: NO** (8 section-3 items > 2; restatement unhedged; the model's own section 2 said YES — a further instance of the false-YES class). Dispositions: all eight phrases glossed inline ("CAP journey census", "Submit step", "authoring route", "lock and lineage sentinel", "judge-class model", "pointer reasons", "new CAP", "guard-by-content"). Section 4: scope stated (FR only, nothing implemented); the `--fr` flag contradiction with Alternatives #7 was real and is removed; cost, concurrency (lock), cleanup, and runtime are now stated; self-test, regression and automatic-invocation items are implementation-time and remain open by design.

## Implementation record (2026-09-05)

**Delivered (PR #592):** `.github/skills/outsider-view/{SKILL.md, doctrine.md (60 lines), adapters/{README.md, graph.yaml, prompts/outsider.yaml, outsider_tools.py}, fixtures/}`; `scripts/outsider.sh`; `tests/unit/test_fr995_outsider_reader.py` + `test_fr995_outsider_wrapper.py` (29 tests); `capabilities/CAP-263-outsider-reader.yaml` (REQ-YG-660…663), `ARCHITECTURE.md` regenerated; `docs/census/outsider-ledger.jsonl` (empty); changelog fragment; brief `feature-requests/authoring-briefs/fr-995-outsider-reader-brief.md`. Graph, prompt and README authored via `scripts/author.sh` (report in `tmp/draft-authoring-report.md`): prompt body byte-identical to the spike's after a two-line header; graph = spike graph with the write step replaced by the typed `finalize_report`; Python untouched by the route.

**RED → GREEN:** tests committed first (`7e95a82c`), module second. One defect found by the wrapper smoke, not by unit tests: the rendered report did not round-trip through its own parser (opinion and label on one line). Fixed in the renderer; a round-trip test added.

**Deviations and decisions:**
- `--dry-run` was designed and then **removed** (operator: dry-runs are banned). Wrapper tests assert the cwd inversion, grants, cleanup and comment gating on the script text and exercise the recursion sentinel for real (it exits before any run).
- `chmod` on `scripts/` is blocked by the main-lock guard in worktrees; the executable bit is set through `git update-index --chmod=+x`.
- Pydantic under yamlgraph's path-based tool loading needs `model_rebuild()` after the classes (CONF-443 idiom); the authoring smoke found it, the unit tests (which import by spec) did not.
- `test_fr995_outsider_wrapper.py` carries `pytestmark = pytest.mark.process` (FR-756 boundary: it reads `scripts/`).

**AC-07 / AC-08 — the positive fixture, honestly:** attempt 4 (`fixtures/positive.md` = v5 + who decides + where the ten types are defined) derived **NO** (5 items: "catalog", "retire rows", "the business plan", "novel_fandom", "fi_domain_crawl") at 06:24Z and **YES** (0 items, "nothing") at 06:26Z in the production `--selftest`, which therefore passed NO/NO/NO/YES. Same text, two minutes apart, opposite verdicts. Both reports are committed under the spike directory and both are asserted in tests. The item set differs on every run (attempts 1–4 named 4 + 3 + 2 + 5 distinct phrases with little overlap); glossing chases a moving target. Rule unchanged, per R-1.

**Operator calibration (2026-09-05):** *gpt-5.6-sol is a nagger — almost impossible to please. That is why the results are advisory and the number of runs is limited.* Recorded in `doctrine.md`. Consequence for anyone proposing a gate later: measure repeat-run variance on the twenty PRs, not single verdicts; a flickering positive is the instrument's nature, not a bug to loop on.

**Not done, by scope:** nothing outstanding after the review round. AC-09 was run after the review (below). No automation, no gate.

## Review record (2026-09-05, `scripts/review.sh 592`)

Verdict on the first head: **Not approved**, six blocking findings — every one real, none visible to the author or to the outsider:

| # | finding | fix |
|---|---|---|
| P1 | the cleanup trap was installed before lock acquisition, so a *losing* invocation deleted the winner's lock (probe: exit 73 and the lock gone) | trap only the child dir until `mkdir $LOCK` succeeds, then trap both; behavioural test: losing process leaves `holder` intact |
| P2 | ledger row appended before the optional comment; a failed comment left a measurement row; ledger write unchecked under `set -u` | comment first, then a checked ledger append; mocked tests for success, comment failure, graph failure, parse failure |
| P3 | parser accepted an empty opinion reason, an item without a question, an empty section-4 item; headings matched as prefixes | required fields `min_length=1`, section-4 items non-empty, headings matched as complete lines; four new fail-closed cases |
| P4 | fetched PR text was written under repo `tmp/` and never removed | fetched text lives only in the trapped child directory; test asserts nothing survives |
| P5 | doctrine 61 lines against a 60-line AC | 60 lines; test asserts ≤ 60 |
| P6 | AC-09 not run; implementation record said "ledger empty, no comment" while the head had a #592 row and a posted comment | AC-09 run on #591 (derived NO, 6 items, row 2); record reconciled below |

Non-blocking: ledger `report_path` now repo-relative (both rows). The reviewer read the same files the outsider could not, and found what the outsider could not: the two adversaries caught disjoint defect classes on the same PR.

**Ledger after the review round:** two rows, two distinct PRs — #592 (06:44Z, NO, 6/8, comment posted) and #591 (07:34Z, NO, 6/6, no comment). The wrapper that wrote row 1 had the P1/P2/P4 defects; the row itself is valid (validated report, real PR).

## Fixtures — the search for a positive (R-1 evidence)

All under [docs/spikes/outsider-reader-2026-09-05/](../docs/spikes/outsider-reader-2026-09-05/); every expectation in `EXPECTATIONS.md` was written before its run. Rule unchanged throughout: YES iff ≤ 2 section-3 items and no hedge marker in section 1.

| input | what it is | section-3 items | hedge in §1 | derived | model's own §2 |
|---|---|---:|---|---|---|
| `pr-591.md` | original #591 body (pasted commit message) | 8 (v2 prompt) | yes | NO | YES (false) |
| `plain-591.md` | operator-approved plain account | 6 | no | NO | NO |
| `pr-591-v2.md` | rewritten body: account + pointers + stated omissions | 5 | yes ("does not say who will operate it") | NO | YES |
| `fr-995.md` | this FR, first push | 8 | no | NO | YES |
| `pr-591-v3.md` | #591 body as merged (v2 + five glosses) | 4 ("FR-990", "yamlgraph", the ten ids, "mercury-2") | no | NO | YES |
| `pr-591-v4.md` | v3 + project name explained, FR defined, ids pointed to `journeys.yaml`, mercury-2 vendor | 3 (the ten ids, "FR-990 AC-7", "plan §12") | no | NO | YES |
| `pr-591-v5.md` | v4 + raw id list removed, AC-7 spelled out, "plan §12" explained | 2 | **yes** ("does not say who has final responsibility for acting on its recommendations") | NO | YES |

Stopped after three passes, per the stop rule written before pass 1. What the chain says: the count clause was met only once the raw enum list left the body; the hedge clause then carried the verdict and pointed at a genuine omission (who decides on retirements). The model's own YES/NO said YES on six of seven — the derived rule is doing real work. Candidate fourth pass for implementation time, expectation first: state who acts on the recommendations. If a fourth pass still derives NO, that is evidence about the rule for a *separate* revision, not a reason to loosen it in this FR.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| 1 | Author-side skill: "write PR descriptions plainly" | REJECTED — the writer judges its own clarity; the failures this FR closes happened while the author held that rule. |
| 2 | Extend `review-pr` with a readability section | REJECTED — the reviewer has file access and the FR; once it has read them it is no longer an outsider. Separate reader, handoff list to review instead. |
| 3 | GitHub Copilot PR summary (vendor feature) | REJECTED for this purpose — it *writes* a description from the diff (author side); it does not read the author's text as a stranger. |
| 4 | Cheap model (haiku / mercury-2) | DEFERRED — operator decision is `gpt-5.6-sol` for PR-level text; the restatement paragraph is judgement, not a label. Revisit if the ledger shows cost matters. |
| 5 | Ask the model for the YES/NO | REJECTED by evidence — false YES on the original #591 body (spike v2). Derived in code. |
| 6 | Blocking gate on the derived verdict | DEFERRED to a separate FR — twenty distinct attributable PR observations first (Proposed Solution 7). A gate calibrated on a handful of inputs is a guess with a hook. |
| 6b | Automatic invocation on PR open (workflow/hook) | DEFERRED to a separate FR (R-4) — this FR is manual-only; automation is not carried by the gate deferral. |
| 7 | Point the reader at FR bodies as a second target | NOT IN SCOPE (operator, 2026-09-05) — dogfood on this FR's PR instead (AC-5). |

## Related

- [docs/2026-09-05-research-plan-cap-journey-census.md](../docs/2026-09-05-research-plan-cap-journey-census.md) §11 (the approved plain account), §12.1–12.7 (the spike)
- [docs/spikes/outsider-reader-2026-09-05/](../docs/spikes/outsider-reader-2026-09-05/) — committed spike copy
- [FR-990](FR-990-cap-journey-census.md) — the PR whose description was the first input
- Diaries: [the-recap-nobody-outside-could-read](../docs/diary/diary-2026-09-05-the-recap-nobody-outside-could-read.md), [the-junk-drawer-moved-when-i-reworded-it](../docs/diary/2026-09-05-reflection-fr-990-the-junk-drawer-moved-when-i-reworded-it.md)
- Separate FR candidate, not bundled: detecting graph files under `examples/` by their contents (a file with `nodes:` and `edges:`) instead of by filename, so a graph cannot dodge the authoring hook by being named something other than `graph.yaml` (the `gh-profiler.yaml` case, plan §12.5)
