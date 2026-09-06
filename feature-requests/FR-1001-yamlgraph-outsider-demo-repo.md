# Feature Request: `yamlgraph-outsider` — a standalone repo that gives any PR an outsider view before review

**Priority:** MEDIUM
**Type:** Enhancement (public demo repository)
**Status:** Implemented 2026-09-05 with **AC-13 NOT MET**; reviewed 2026-09-06 (`scripts/review.sh` #603 → not approved, P1–P4); P2–P4 fixed; P1 → third [judgement](FR-1001-yamlgraph-outsider-demo-repo.judgement.md) (2026-09-06) restored the frozen `NO/NO/NO/YES` gate and rejected the xfail oracle. Operator merge decision: ship with AC-13 open; a passing sample configuration, or a fixture FR, follows.
**Effort:** 1 day
**Requested:** 2026-09-05
**First consumer / first event:** a maintainer of any GitHub repository who has just opened a pull request — `pipx install yamlgraph && ./yamlgraph-outsider 123 --repo owner/name --comment`. Second: `sheikkinen/deviant-daily` on its next feature PR. Third: this repo's PRs, for anyone without a Copilot seat.
**Research:** [docs/2026-09-05-research-plan-cap-journey-census.md §12–§13](../docs/2026-09-05-research-plan-cap-journey-census.md) — two recorded spikes; spike 2 (`docs/spikes/outsider-llm-2026-09-05/`, plain `llm` node on a provider API) is the shape this FR ships. `is_this_a_graph: Yes` — fetch → `llm` → deterministic finalize is the spiked pipeline, and the graph isolates model inference from side-effect tools. Solution classes dispositioned in Alternatives #1 (Copilot transport), #3 (prompt-only calibration), #5 (plain Python/SDK), #8 (shell-owned side effects); chosen: provider-API graph + deterministic reducer calibration. Recorded disagreement preserved below: the API path is stable but over-flags; the Copilot path discriminates but flickers.
**Prior art:** [FR-995](FR-995-outsider-reader.md) — the reader; this FR reuses its doctrine, rule and fixtures and changes nothing in it. Its run ledger is not reused: the posted comment is the record ([FR-1004](FR-1004-retire-outsider-ledger.md) retires the parent's ledger on the same ground). [FR-865](FR-865-ramp-installer.md) — ships skills to other repos; this FR does not touch the ramp manifest (Alternatives #4). [FR-998](FR-998-anthropic-constrained-structured-output.md) (main, `741aa9821198`) — framework fix for `list[str]` arriving as a JSON string; until it lands the demo keeps its own normalisation. No REJECTED FR in this territory.

## Summary

A small public repository, `sheikkinen/yamlgraph-outsider` (MIT), that anyone can clone to run the outsider reader on a pull request: install `yamlgraph`, sign in to `gh`, put one API key in `.env`, run one script.

The script checks that `yamlgraph`, `gh` and `git` exist and starts the graph. Everything else is the graph's: a python tool reads the PR title and body through `gh`, one `llm` node reads them, a python tool validates, derives the verdict, renders the report and — when asked — posts it as the PR comment through `gh`. The posted comment is the record.

The graph and the script contain no provider or model selection. Copying `.env.sample` selects the tested sample configuration (Anthropic, `claude-haiku-4-5`); users edit or omit those values, and yamlgraph resolves the rest.

## Value Statement

A maintainer outside this project gets, for one API call, the list of phrases in their PR description that only an insider could follow — before a human reviewer's time is spent.

## Problem

FR-995's route needs the GitHub Copilot CLI. Spike 2 showed the reader works as a plain `llm` node on a provider API (structured output, zero parse rejections on five fixtures and one live PR, ~25 s per PR) — installable anywhere `pip` and `gh` work. That code sits under `docs/spikes/` with a model pinned in two places.

Spike 2 also showed the reader over-flags: every path and identifier, and once a quoted *explanation* as a thing it did not understand. Under the ≤ 2 rule no real PR body passes. That is a reducer problem — cap in code, not in the prompt.

## Raw Output Read (measurement / metric-tooling FRs only)

Read: all six committed spike-2 reports ([docs/spikes/outsider-llm-2026-09-05/out/](../docs/spikes/outsider-llm-2026-09-05/out/)). The FR-995 production comments on #591, #592, #595 are context, not evidence (not committed here).

- Same text, two sonnet runs at T=0: 7 → 6 items, 6 shared. Same text, two `gpt-5.6-sol` runs: 5 → 0 items, NO → YES.
- On PR #592 sonnet quoted *"the repository's independent plan-reviewer (a separate model run that reads only the plan…)"* and asked what it was. The text explained the term; the reader flagged the explanation. Code can see the parenthetical; the model cannot be told to.
- On `plain-591` sonnet flagged "capabilities", "compliance evidence", "the process" — ordinary English.
- Every path-like quote (`capabilities/CAP-*.yaml`, `journeys.yaml`, `scripts/author.sh`) was flagged by both models. A path is not vocabulary.
- `list[str]` fields arrived as a JSON-encoded string on sonnet; spike 2 normalises in `tools.py:_lines`.

## Ideal Result

`git clone … && pipx install yamlgraph && cp .env.sample .env` (add one key) `&& ./yamlgraph-outsider 123 --repo owner/name --comment` posts on the PR a report whose first line is a derived YES or NO and whose "could not understand" list contains only phrases a stranger genuinely could not follow — not paths, not things the body already explains. `pytest -m live` passes NO/NO/NO/YES twice in a row on the sample configuration. The README was itself run through the tool and links the report.

## Proposed Solution

1. **Repository.** `sheikkinen/yamlgraph-outsider`, public, MIT, its own Git root (sibling clone, never nested in this repo). Copied from spike 2 through the authoring route: brief `feature-requests/authoring-briefs/fr-1001-yamlgraph-outsider-demo-repo-brief.md`, `scripts/author.sh`, `tmp/draft-authoring-report.md`, `yamlgraph graph lint`, one credentialed smoke. Contents: `graph.yaml`, `prompts/outsider.yaml`, `tools.py`, `yamlgraph-outsider`, `fixtures/{pr-591,plain-591,pr-591-v2,positive}.md` + `EXPECTATIONS.md`, `.github/skills/outsider-view/{SKILL.md,doctrine.md}`, `tests/`, `pyproject.toml` (test manifest; tested minimum `yamlgraph` version), `README.md`, `LICENSE`, `.env.sample`, `.gitignore` (`.env`, `.env.*`, `out/`; not `.env.sample`), `docs/evidence/`.
2. **Script: prerequisites and start, nothing else.** `yamlgraph-outsider <pr> [--repo owner/name] [--comment]` | `--input <file.md>`. Checks `command -v yamlgraph gh git` (each missing tool: distinct non-zero exit, one-line install hint) and that `.env` exists; rejects `--input` with `--comment` at argument parsing; resolves the default `--repo` from `git remote get-url origin` (its only `git` call); then runs exactly one command: `yamlgraph graph run graph.yaml --var pr= --var repo= --var input_path= --var comment=true|false --var report_path=out/<label>-<timestamp>.md`. **Success needs two witnesses:** graph exit 0 **and** a report that validates in full (first line `**Derived verdict:** YES|NO`, four sections). Graph non-zero → failure even if a report exists; graph zero with absent/invalid report → failure. No `gh`, no `--model`/`--provider`, no model name.
3. **Graph: three nodes, owns GitHub.** `fetch_pr` (python: `gh pr view <pr> -R <repo> --json title,body`, argument list, no shell; or reads `input_path`) → `outsider` (`llm`, structured output, `temperature: 0.0`, no `provider`/`model` anywhere) → `finalize` (python: normalise into the typed models below, reduce, derive, render, write `report_path`; then, only when `comment` is strictly `true` and the source was a PR, `gh pr comment <pr> -R <repo> --body-file <report>`). `comment` is normalised strictly from the canonical strings `true`/`false`; anything else is rejected. A failed post raises: the node fails, the graph exits non-zero, no comment is claimed, and the valid local report remains for diagnosis. Any failure before rendering leaves no valid report.
4. **Model from `.env` only.** The report header records provenance in four frozen cases: provider and model configured → both literal values; provider configured, `<PROVIDER>_MODEL` omitted → provider + `framework-default`; provider omitted → `framework-default` / `framework-default`; never an inferred effective model name. Tests prove `finalize` records the same environment values yamlgraph resolves from. `.env.sample`:
   ```
   # Tested sample configuration. yamlgraph resolves PROVIDER, then <PROVIDER>_MODEL;
   # omit either and the framework default applies (recorded as "framework-default").
   PROVIDER=anthropic
   ANTHROPIC_API_KEY=
   ANTHROPIC_MODEL=claude-haiku-4-5
   # PROVIDER=openai
   # OPENAI_API_KEY=
   # OPENAI_MODEL=
   ```
5. **Typed boundary, then reducer.** Pydantic models: `OutsiderReading` (non-empty `restatement`; `opinion: Literal["YES","NO"]`; non-empty `opinion_reason`; ≤ 8 raw unclear items; ≤ 10 non-empty needs items), `UnclearItem` (non-empty `quote`, `question`), `DemotionReason` (`identifier` | `path` | `inline_gloss`), `ReducedReading` (retained + demoted, each demoted item carrying exactly one reason). The two list fields accept only `list[str]`, a JSON-encoded `list[str]`, or newline-delimited strings; non-list JSON, non-string members, other scalars/containers, empty lines and unclear lines that cannot yield both quote and question are rejected. Caps apply before reduction. Reducer, per item, preserving quote, question and order: `identifier` if the whole quote matches `CAP-\d+`, `FR-\d+` or `REQ-[A-Za-z0-9-]+`; else `path` if it contains `/` or ends (case-insensitively) in `.yaml`, `.yml`, `.py`, `.md`; else `inline_gloss` if any exact occurrence of the quote in the source is followed by ` (`, ` — ` or `: `, or the quote itself contains such a gloss and its pre-gloss prefix occurs at that boundary; else retain. Precedence `identifier` → `path` → `inline_gloss`. Verdict derives only from the validated restatement and the retained items. Render exactly four top-level sections; demoted items are a labelled subsection of section 4. Never drop, never duplicate; never render, post or report success from an invalid model. Unit tests on paired source bodies + structured items cover every accepted and rejected form, every rule and near miss, precedence, order, counts, and three named cases: the #592 gloss quote demotes; `capabilities/CAP-*.yaml` demotes; "someone writing a graph" retains.
6. **Evidence before claims; human gate before spend.** Deterministic tests over committed structured outputs derive NO/NO/NO/YES after the reducer. Before any credentialed run or public post, the FR records the human-approved provider/model, spending owner and target PR, and confirms the title/body and report contain no private material. Then `pytest -m live` (skipped without a key) runs every fixture twice through the graph on the `.env.sample` configuration and requires that sequence both times; the eight raw outputs are committed under `docs/evidence/`, expectations written first. **Raw-reading capture** (`OUTSIDER_DUMP_READING`, evidence-only, opt-in): absent in ordinary runs and producing nothing by default; enabled only when the live-test harness sets an explicit destination; writes the exact model payload *before* validation so rejected readings remain inspectable; never changes validation, verdict, report, comment or exit semantics; a capture-write failure raises rather than losing evidence; tested for valid, rejected, disabled and write-failure cases. Not authority for tracing, telemetry or a second ledger.
7. **README.** What it does (three sentences, no project words) · install · use · read the report · *before review* (two readers: one given everything, one given nothing) · the posted comment is the record · live test · known limits (over-flagging is capped, not solved; advisory; one run per PR) · provenance. Run the tool on the README before publishing; commit the report under `docs/evidence/` and link it with input SHA-256, item count, configured provider/model, timestamp and source commit.
8. **This repo.** One line in `.github/skills/outsider-view/adapters/README.md` pointing at the demo as the non-Copilot route. Spike directory untouched.

## Acceptance Criteria

- [ ] AC-01: The revised FR cites `feature-requests/authoring-briefs/fr-1001-yamlgraph-outsider-demo-repo-brief.md`; `scripts/author.sh` produces the declared external graph/prompt/tool artifacts and a valid `tmp/draft-authoring-report.md`; the report records successful `yamlgraph graph lint <external-repo>/graph.yaml` and the narrow smoke, or the exact credential blocker.
- [ ] AC-02: `gh repo view sheikkinen/yamlgraph-outsider --json visibility,licenseInfo` reports public visibility and an MIT license; the local target is a separate Git root outside the yamlgraph repository; `git check-ignore` proves `.env` and `out/` are ignored and `.env.sample` is tracked.
- [ ] AC-03: Parsed `graph.yaml` contains no configured `provider` or `model` at defaults or node level; the entry script accepts no `--provider` or `--model` flag and contains no hard-coded model identifier.
- [ ] AC-04: `.env.sample` contains one active sample provider, empty key, and explicit sample model on separate lines. README calls these the tested sample selection—not “no model choice”—and documents alternatives one variable per line.
- [ ] AC-05: Tests cover all four R-4 provenance cases. Changing `.env` changes the recorded configured values without editing graph, prompt, tool, or wrapper; omitted values are recorded only as `framework-default`.
- [ ] AC-06: The wrapper chooses `out/<label>-<timestamp>.md` before invocation and passes it as `report_path`; no LLM result is needed to construct the path.
- [ ] AC-07: The standalone doctrine and `SKILL.md` contain no Copilot-CLI, pinned-`gpt-5.6-sol`, or ledger claim; they preserve title-and-body-only model input, advisory status, fail-closed handling, three-reader ownership, four top-level sections, one run per PR, and `./yamlgraph-outsider` invocation.
- [ ] AC-08: Pydantic tests exercise every R-2 accepted and rejected normalization form, every required field and cap, quote/question parsing, reducer rule and near miss, reason precedence, stable order, no loss or duplication, retained-only counts, and the three named examples.
- [ ] AC-09: The wrapper contains exactly one `yamlgraph graph run`, no `gh`, and one operational `git` call. With controlled executables on `PATH`, each missing prerequisite and missing `.env` has a distinct non-zero result and one-line hint; the `--var` set is exactly `pr,repo,input_path,comment,report_path`; invalid comment values and `--input --comment` fail before graph invocation.
- [ ] AC-10: Wrapper success requires graph status zero **and** complete report validation. Tests prove graph status non-zero is preserved despite a valid report, and graph status zero with an absent/invalid report also fails.
- [ ] AC-11: With a fake `gh`, `fetch_pr` calls `gh pr view <pr> -R <repo> --json title,body` as an argument list and returns exactly `# <title>

<body>`; `--input` never calls `gh`; `finalize` posts only for strict `comment=true` with a PR source. A failed post returns non-zero and leaves the valid local report but no claimed successful comment.
- [ ] AC-12: Malformed structured output, missing API key, missing `gh`, invalid PR/repository, fetch failure, graph failure, absent report, invalid report, and comment failure each follow the distinct R-1/R-2 artifact semantics and never produce wrapper success.
- [ ] AC-13: After the recorded human spend decision, `pytest -m live` runs the four unchanged fixtures twice on the exact `.env.sample` configuration. Both passes complete without schema rejection and derive `NO/NO/NO/YES`. Expectations predate execution; all eight new raw readings are committed with timestamps and source commit; deterministic replay derives the same sequence. Any rejection or different verdict fails normally—no skip or xfail.
- [ ] AC-14: README's pre-publication report is committed under `docs/evidence/` and linked with input SHA-256, item count, configured provider/model, timestamp, and source commit.
- [ ] AC-15: After the R-5 public-write decision, one explicit `--comment` run on the approved public PR outside `sheikkinen/yamlgraph` leaves the comment on that PR; its URL and evidence report are recorded in the FR; no credential or private PR material is committed.
- [ ] AC-16: `pyproject.toml` declares the exact test command and tested minimum `yamlgraph`; focused tests pass in a clean environment; the README's clone/install/configure/run path succeeds.
- [ ] AC-17: The Research and Prior art fields contain the R-3 `is_this_a_graph` answer, substantive solution-class disposition, and only committed evidentiary dependencies; the dangling FR-1004 claim is removed or replaced by an exact committed path.
- [ ] AC-19: `OUTSIDER_DUMP_READING` behaves as frozen in Proposed Solution 6 — no artifact when unset; exact pre-validation payload when set; rejected readings captured; write failure raises; validation/verdict/report/comment unchanged — with tests for all four cases.
- [ ] AC-18: This repository's diff is limited to the authoring brief, one adapter-README line, FR plus final judgement/status record, changelog fragment, and diary entry; the spike trees, ramp manifest, existing outsider implementation, and ledger are byte-unchanged.

## Implementation status (2026-09-05)

Repository: https://github.com/sheikkinen/yamlgraph-outsider — public, MIT, own Git root at `/Users/sheikki/Documents/src/yamlgraph-outsider`; reviewed at `21a62dfe6e58`, fixes on `main` at `a38f82e4e5a3`. Human decisions (R-5): spend approved by the operator for anthropic / `claude-haiku-4-5` on the operator's key (≈ 11 calls made: 1 authoring smoke, 8 fixture runs, 1 README self-run, 1 live PR); target PR = the first PR of the new repo itself. Route: brief → `scripts/author.sh` (report verified; graph/prompt copied from spike 2; one README line appended here).

| AC | Result | Evidence |
|---|---|---|
| 01 | met | `feature-requests/authoring-briefs/fr-1001-yamlgraph-outsider-demo-repo-brief.md`. Two route runs: the first report recorded lint (0 errors, W026 on the five-field schema) and a smoke that **failed** in `finalize` (`from __future__ import annotations` vs path-loaded pydantic); the defect was fixed and the route re-run 2026-09-06 (review P2) — second `tmp/draft-authoring-report.md`: lint exit 0, smoke exit 0 (`out/authoring-smoke.md` derived NO on `positive`), deterministic tests exit 0; graph, prompt and README line byte-identical across the two runs
| 02 | met | `gh repo view` → PUBLIC; `LICENSE` MIT (GitHub's detector had not yet run at the time); `git check-ignore`: `.env`, `out/` ignored, `.env.sample` tracked |
| 03 | met | `graph.yaml` has `defaults: {temperature: 0.0}` only; launcher has no `--provider`/`--model`, no model name (static test) |
| 04 | met | `.env.sample` three active lines; README: "tested sample configuration", alternatives one per line |
| 05 | met | `test_provenance_four_cases`, `test_finalize_provenance_framework_default_when_omitted`, header `provider: anthropic \| model: claude-haiku-4-5` in every evidence report |
| 06 | met | `out/<label>-<timestamp>.md` chosen by the launcher; `test_report_path_chosen_before_run` |
| 07 | met | `doctrine.md` derived (provider-API route, no Copilot/`gpt-5.6-sol`/ledger claims, four sections, one run per PR); `SKILL.md` invokes `./yamlgraph-outsider` |
| 08 | met | `tests/test_boundary.py` — normalisation accept/reject set (review P3 tightened it: `None`, empty members, whole-text JSON scalars and non-string required fields now raise; an item beginning with an ASCII-quoted phrase is ordinary text — learned from the recorded `plain-591` readings), caps before reduction, every rule and near miss, precedence, order, no loss/duplication, three named cases
| 09 | met | `tests/test_wrapper.py` — one `yamlgraph graph run`, no `gh`, one `git`; exits 70/71/72 per missing tool with install hint, 73 for `.env`; exact var set; `--input --comment` → 64 |
| 10 | met | graph rc≠0 with valid report → fail; rc 0 with absent/invalid report → fail; review P4: the launcher now requires the four canonical headings exactly once and in order plus the exact reducer heading — tests for duplicate, out-of-order, wrong-title and wrong-reducer headings
| 11 | met | `tests/test_gh_tools.py` — exact `gh pr view`/`gh pr comment` argv; `--input` never calls `gh`; failed post raises, report kept |
| 12 | met | rejection paths tested; live: `pr-591` rejected both runs (9 items > 8) with no report written |
| 13 | **NOT MET** | 8 live runs on `.env.sample` (haiku-4-5, T=0), both passes agreeing: `pr-591` REJECTED/REJECTED (9 items > 8), `plain-591` NO/NO, `pr-591-v2` **YES/YES**, `positive` **NO/NO** (4 retained: "someone writing a graph", "mercury-2", "\"retire\" rows", "cross-cutting"; 1 demoted `FR-990`; `does not say` hedge). The frozen gate stands (judgement v3 R-1/R-3: fixtures, threshold, hedges and fail-closed rule may not change); the failed readings are kept unchanged as historical evidence; no xfail oracle; the live test alone asserts the sequence on fresh runs. README calls the sample configuration experimental with a recorded failed calibration. Next: a different human-approved sample configuration under the R-5 spend gate, recorded under new evidence filenames — or a fixture FR. `fixtures/EXPECTATIONS.md` → Results |
| 14 | met | `docs/evidence/README-self-run.md` (derived YES, 1 retained "the reducer" → glossed; 3 set aside); header carries input SHA-256, provider, model, timestamp, commit |
| 15 | met | `./yamlgraph-outsider 1 --comment` with repo from `origin`: derived NO (1 retained "shipped sample configuration" + hedge; "the tool itself" set aside as inline gloss). Comment: https://github.com/sheikkinen/yamlgraph-outsider/pull/1#issuecomment-5552543093 ; report `docs/evidence/pr-1-comment-run.md`; both phrases glossed in the PR body; PR merged |
| 16 | met | `pyproject.toml` `[dependency-groups] test` (`yamlgraph>=0.5.17`; checkout used 0.5.24), `pytest` / `pytest -m live`; 90 deterministic tests pass, 1 strict xfail |
| 17 | met | Research: `is_this_a_graph: Yes` + class disposition; Prior art: FR-1004 by path, production comments labelled non-evidentiary |
| 19 | met | `OUTSIDER_DUMP_READING` tests: disabled → only the report; valid → payload before report; rejected → payload, no report; write failure → `OSError`, no report (`tests/test_gh_tools.py`) |
| 18 | met | this repo's diff: brief, one adapter-README line, FR + judgement, changelog fragment, diary; spike trees, ramp manifest, outsider implementation and ledger untouched |

Deviations: none remaining — the raw-reading capture that the live runs required was folded into the contract by judgement v3 R-4 (Proposed Solution 6, AC-19).

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| 1 | Ship the Copilot-CLI route (FR-995) as the demo | REJECTED — needs a Copilot seat; not installable by a stranger. |
| 2 | Default model in `graph.yaml` or the script | REJECTED — yamlgraph already resolves provider and model from the environment; a second decision point is drift. `.env.sample` only. |
| 3 | Fix over-flagging in the prompt | REJECTED — the signal (a path; a following parenthetical) is visible to code, invisible to the model. |
| 4 | Add the skill to the ramp manifest now | DEFERRED — after the comment has been posted on ≥ 5 external PRs; separate FR. |
| 5 | Standalone Python script without yamlgraph | REJECTED — a different product; the demo is "install yamlgraph, copy the skill". |
| 6 | Fix the `list[str]`-as-string lie here | NOT IN SCOPE — FR-998 owns the boundary. |
| 7 | A run ledger (`outsider-ledger.jsonl`) | REJECTED — the posted comment is already a timestamped, attributable, public record; a second copy must be kept in sync and failed on its first real run in this repo. |
| 8 | Script fetches the PR and posts the comment itself | REJECTED — the graph is the program; `gh` in python tools is testable with a fake `gh` and keeps one owner of the PR shape. |

## Related

- [FR-995](FR-995-outsider-reader.md), [FR-998](FR-998-anthropic-constrained-structured-output.md), [FR-865](FR-865-ramp-installer.md), [FR-1004](FR-1004-retire-outsider-ledger.md)
- [docs/2026-09-05-research-plan-cap-journey-census.md](../docs/2026-09-05-research-plan-cap-journey-census.md) §12–§13
