# Feature Request: `yamlgraph-outsider` — standalone demo repo; install yamlgraph, copy the skill, get an outsider view before review

**Priority:** MEDIUM
**Type:** Enhancement (public demo repository + one code cap)
**Status:** Judged — APPROVED WITH REVISIONS (2026-09-05, [judgement](FR-1001-yamlgraph-outsider-demo-repo.judgement.md)). R-1…R-6 folded below; authority active for D-1…D-8 only.
**Effort:** 1 day
**Requested:** 2026-09-05
**First consumer / first event:** a maintainer of any GitHub repository who has just opened a pull request and wants to know what a reader with no context cannot follow — first event: `pipx install yamlgraph && ./yamlgraph-outsider 123 --repo owner/name`. Second consumer: `sheikkinen/deviant-daily` (the one existing ramp consumer), on its next feature PR. Third: this repo's own PRs, where the Copilot-route wrapper (`scripts/outsider.sh`, FR-995) already runs; the demo is the route for everyone without a Copilot seat.
**Research:** [docs/2026-09-05-research-plan-cap-journey-census.md §12–§13](../docs/2026-09-05-research-plan-cap-journey-census.md) — two spikes, all runs recorded with expectations written first. Spike 1 (Copilot CLI, `gpt-5.6-sol`) is the FR-995 production route; spike 2 (`docs/spikes/outsider-llm-2026-09-05/`, plain `llm` node, provider API, structured output) is the standalone shape this FR ships. Alternatives dispositioned in-body.
**Prior art:** [FR-995](FR-995-outsider-reader.md) — the reader itself; this FR changes nothing in it and reuses its doctrine, rule, fixtures and ledger schema. [FR-865](FR-865-ramp-installer.md) — the ramp installer ships judge/review skills to other repos as doctrine + wrapper without the adapter; this FR is the *standalone* route for one skill and does **not** touch the ramp manifest (ramp inclusion is gated on ≥ 5 external-PR runs — Alternatives #4). FR-998 (`feature-requests/FR-998-anthropic-constrained-structured-output.md` on main since `741aa9821198` (judged, not yet enforced)) — the framework-side fix for `list[str]` arriving as a JSON string (FR-059 class) found by spike 2; this FR keeps spike 2's in-code normalisation until FR-998 lands and does not touch the framework. [docs/node-type-census-2026-08.md] — no overlap. No REJECTED FR in this territory.

## Summary

A small public repository, `sheikkinen/yamlgraph-outsider`, that anyone can clone to run the outsider reader on a pull request: install `yamlgraph`, sign in to `gh`, put one API key in `.env`, run one script. It contains the spike-2 graph and prompt, the typed finalize tool, the entry script, the four fixtures with their expectations, and the `outsider-view` skill files (`SKILL.md`, `doctrine.md`) so a Copilot user in any repository can copy the skill and ask for an outsider view by name before review.

**The script decides nothing about models.** Provider and model come from yamlgraph's own resolution chain — `node.provider > defaults.provider > PROVIDER env > "anthropic"`, model from `{PROVIDER}_MODEL` env with yamlgraph's base default — and the graph declares neither. The *active* configuration lives only in `.env`. `.env.sample` ships the **demo's tested sample configuration** (`PROVIDER=anthropic`, `ANTHROPIC_MODEL=claude-haiku-4-5`) — honestly a default the demo distributes, even though it coincides with the framework's own; historical evidence and documentation may name other tested models. Users change the model by editing `.env`, never a flag. (R-2)

## Value Statement

A maintainer outside this project gets, for one API call, the list of phrases in their PR description that only an insider could follow — before a human reviewer's time is spent.

## Problem

FR-995's production route requires the GitHub Copilot CLI with access to `gpt-5.6-sol`. Spike 2 showed the reader works as a plain `llm` node on a provider API (structured output; zero parse rejections on five fixtures plus one live PR; ~25 s per PR), which makes it installable anywhere `pip` and `gh` work. Today that code sits under `docs/spikes/` in this repo, with a model pinned in `graph.yaml` and again in the entry script — two places a demo user would have to edit, and two places that assert a model decision the framework already makes better.

Spike 2 also found the reader **over-flags on sonnet**: it lists every path and identifier, and quoted an inline *explanation* as a thing it did not understand. Under the ≤ 2 rule no real PR body passes. That is a reducer problem (FR-725 idiom: cap in code), not a prompt problem, and the demo is not honest without it.

## Raw Output Read (measurement / metric-tooling FRs only)

- **Samples read:** all spike-2 reports under [docs/spikes/outsider-llm-2026-09-05/out/](../docs/spikes/outsider-llm-2026-09-05/out/) (fixtures ×4, positive ×2, PR #592 live), plus the three FR-995 production reports (#591, #592, #595).
- **What I saw:**
  - Same text, two sonnet runs at T=0: 7 → 6 items, 6 shared. Same text, two `gpt-5.6-sol` runs: 5 → 0 items, NO → YES. The API path has a temperature; the Copilot route does not expose one.
  - Sonnet on PR #592 quoted the gloss *"the repository's independent plan-reviewer (a separate model run that reads only the plan…)"* and asked what it was. The text explained the term; the reader flagged the explanation. A reducer can see this — the quote is immediately followed by a parenthetical in the source — the model cannot be told to.
  - Sonnet on `plain-591` flagged "capabilities", "compliance evidence", "the process": ordinary English. Same over-flagging class.
  - Every path-like quote (`capabilities/CAP-*.yaml`, `journeys.yaml`, `scripts/author.sh`) was flagged by sonnet and by `gpt-5.6-sol` alike; a path is by definition not vocabulary.
  - Structured output returned `list[str]` fields as a JSON-encoded string on sonnet (FR-059 class); spike 2 normalises in `tools.py:_lines`. FR-998 is the framework fix; not this FR.

## Ideal Result

`git clone sheikkinen/yamlgraph-outsider && cd yamlgraph-outsider && pipx install yamlgraph && cp .env.sample .env` (add one key) `&& ./yamlgraph-outsider 123 --repo owner/name` prints a report whose first line is a derived YES or NO, and whose "could not understand" list contains only phrases a stranger genuinely could not follow — not paths, not things the body already explains. `./yamlgraph-outsider --selftest` passes NO/NO/NO/YES twice in a row on the default model. The README was itself run through the tool and says how many items it drew.

## Proposed Solution

1. **Repository** `sheikkinen/yamlgraph-outsider`, MIT (both confirmed by the operator 2026-09-05), a **separate sibling clone with its own Git root** — never nested in or vendored into this worktree (R-5). Created from `docs/spikes/outsider-llm-2026-09-05/` (copy, not reinvention) **through the authoring route**: brief `feature-requests/authoring-briefs/fr-1001-yamlgraph-outsider-demo-repo-brief.md` names the external repo as target and every artifact; `scripts/author.sh` produces graph/prompt, verified by `tmp/draft-authoring-report.md`, `yamlgraph graph lint`, and the narrow credentialed smoke. Contents: `graph.yaml`, `prompts/outsider.yaml`, `tools.py`, executable `yamlgraph-outsider`, `fixtures/{pr-591,plain-591,pr-591-v2,positive}.md` + `EXPECTATIONS.md`, `.github/skills/outsider-view/{SKILL.md,doctrine.md}`, `tests/`, `pyproject.toml` (test/dependency manifest; tested minimum `yamlgraph` version recorded; end users still `pipx install yamlgraph`), `README.md`, `LICENSE`, `.env.sample`, `.gitignore` (`.env`, `out/`), `docs/evidence/`, `docs/census/outsider-ledger.jsonl`.
   **Standalone doctrine (R-1):** `doctrine.md` is *derived from* this repo's, not byte-identical — it keeps title-and-body-only input, advisory status, fail-closed output, the three readers, four top-level sections and one run per PR, but names the provider-API `llm` route and environment-based model configuration; the Copilot-CLI / `gpt-5.6-sol` / "cwd outside the repo" claims do not apply and are absent. `SKILL.md` invokes `./yamlgraph-outsider` and carries no `scripts/outsider.sh` or Copilot claims.
2. **No model decision in graph or script (R-2).** `graph.yaml`: no `provider`/`model` at `defaults` or node level; `temperature: 0.0` stays. Entry script: no `--model`/`--provider` flags, no model identifier anywhere. **Report filename is model-neutral and pre-run**: `out/<label>-<timestamp>.md`. The report header and ledger record the **configured** provider/model as loaded from `.env` (tests prove those exact values reach both the `llm` node's resolution environment and the finalizer); when a variable is omitted the record says `framework-default`, never a guessed identifier. `.env.sample`, one variable per line:
   ```
   # Tested sample configuration. yamlgraph resolves PROVIDER then <PROVIDER>_MODEL;
   # omit either and the framework default applies (recorded as "framework-default").
   PROVIDER=anthropic
   ANTHROPIC_API_KEY=
   ANTHROPIC_MODEL=claude-haiku-4-5
   # PROVIDER=openai
   # OPENAI_API_KEY=
   # OPENAI_MODEL=
   ```
3. **Reducer as a deterministic typed boundary (R-3).** Input: `(source_body, validated_unclear_items)` after the inherited Pydantic/fail-closed checks (malformed structured output → no report, no comment, no ledger row). For each item, preserving quote and question and original order: (i) demote if the quote is a full identifier token matching `CAP-\d+`, `FR-\d+` or `REQ-[A-Za-z0-9-]+`; (ii) demote if path-like — contains `/` or ends in `.yaml`, `.yml`, `.py`, `.md`; (iii) demote as an inline gloss if the exact quote is followed in the source by ` (`, ` — ` or `: `, **or** the quote itself contains such a gloss and its pre-gloss prefix occurs at that source boundary (the #592 case: the parenthetical was inside the model's quote); (iv) retain everything else in `unclear`. Demoted items carry a machine-readable reason and are rendered as a labelled subsection of section 4 — not a fifth top-level section — and are excluded from the derived-verdict count. Never drop, never duplicate. Typed unit tests use paired source bodies + structured items (not rendered text): every rule, near misses, case, punctuation, order, counts, and the three named examples (the #592 gloss quote demotes; `capabilities/CAP-*.yaml` demotes; "someone writing a graph" retains).
4. **Selftest twice, evidence first (R-3).** Deterministic tests over committed structured outputs derive NO/NO/NO/YES after the reducer. Separately, the credentialed `--selftest` runs every fixture twice with the exact `.env.sample` configuration and requires that sequence on both passes; all eight raw outputs committed under `docs/evidence/` with expectations written before execution. The existing spike evidence (sonnet, no reducer, `positive` = NO twice) does **not** establish the haiku result; it must be produced.
5. **README:** what it does (three sentences, no project words) · install · use · read the report · *before review* (two readers, one given everything, one given nothing) · selftest · known limits (over-flagging is capped, not solved; verdict is advisory; one run per PR) · provenance. The README is run through the tool before publishing; the report is committed under `docs/evidence/` and the README **links** it with input SHA-256, item count, configured provider/model, timestamp and source commit — it does not embed a count derived from its own final bytes (R-4).
6. **Ledger (R-4):** `docs/census/outsider-ledger.jsonl` (committed; `out/` stays ignored for transient runs). Row schema: UTC timestamp, repository, PR number, PR head SHA, exact title+body SHA-256, configured provider/model, graph/prompt digest, demo-repo commit SHA, derived verdict, retained-unclear count, demoted count, needs count, report path. Appended only after successful validation for a real PR; fixture, `--input`, self-test, failed and comment-failed runs write no row. The five-run ramp prerequisite = five distinct external PRs, latest successful row per (repo, PR).
7. **Back-reference in this repo:** one line in `.github/skills/outsider-view/adapters/README.md` pointing at the demo as the non-Copilot route; the spike directory stays as historical evidence and is not edited.

## Acceptance Criteria (revised by the judgement; originals superseded)

- [ ] AC-01: The FR cites `feature-requests/authoring-briefs/fr-1001-yamlgraph-outsider-demo-repo-brief.md`; `scripts/author.sh` produces the declared external graph/prompt/tool artifacts and a valid `tmp/draft-authoring-report.md`; the report records successful `yamlgraph graph lint <external-repo>/graph.yaml` and the narrow smoke, or the exact credential blocker.
- [ ] AC-02: `gh repo view sheikkinen/yamlgraph-outsider --json visibility,licenseInfo` reports public visibility and an MIT license, and the local target is a separate Git root outside the yamlgraph repository.
- [ ] AC-03: Parsed `graph.yaml` contains no configured `provider` or `model` at defaults or node level; the entry script accepts no `--provider` or `--model` flag and contains no hard-coded model identifier.
- [ ] AC-04: `.env.sample` contains one active sample provider, empty key, and explicit sample model on separate lines; README labels that model as the demo's tested sample default and documents one-variable-per-line alternatives.
- [ ] AC-05: With `cp .env.sample .env` and the key value filled in, a fixture run records the configured provider/model in the validated report header and ledger metadata. Changing those `.env` values changes the recorded configured values without editing graph, prompt, tool, or script. Omitted values are recorded as `framework-default`, not as a guessed identifier.
- [ ] AC-06: Reports use a model-neutral pre-run filename. No code needs an LLM result in order to construct the path passed into that same run.
- [ ] AC-07: The standalone doctrine and `SKILL.md` contain no Copilot-CLI or pinned-`gpt-5.6-sol` execution claim; they preserve title-and-body-only model input, advisory status, fail-closed handling, three-reader ownership, four top-level sections, one run per PR, and `./yamlgraph-outsider` invocation.
- [ ] AC-08: Typed unit tests prove every R-3 reducer rule and near miss using paired source bodies and structured unclear items. They prove stable ordering, no loss or duplication, machine-readable demotion reasons, retained-only verdict counts, and the three named cases.
- [ ] AC-09: Missing/invalid structured fields, excessive item counts, malformed unclear items, missing API key, missing `gh`, invalid PR/repository input, graph failure, comment failure, and absent/invalid report all fail non-zero and create no success-shaped report or ledger row.
- [ ] AC-10: Deterministic tests over committed structured outputs derive `NO/NO/NO/YES` after the reducer. A credentialed `./yamlgraph-outsider --selftest` runs every fixture twice with the exact `.env.sample` configuration and requires that sequence on both passes; all eight raw outputs are committed under `docs/evidence/` with expectations written before execution.
- [ ] AC-11: `out/` is ignored and contains only transient runtime reports/logs. The README pre-publication report is committed under `docs/evidence/`, and README links it with input SHA-256, item count, configured provider/model, timestamp, and source commit; README does not claim to contain a count derived from its own final bytes.
- [ ] AC-12: `docs/census/outsider-ledger.jsonl` uses the complete R-4 schema. Tests prove one row per successful real-PR run, no rows for excluded/failed modes, and distinct external-PR counting for the five-run ramp prerequisite.
- [ ] AC-13: At least one validated run against a real PR outside `sheikkinen/yamlgraph` produces a committed evidence report and attributable ledger row without committing credentials or PR-private data.
- [ ] AC-14: The external repository includes the declared test/dependency manifest and exact test command; its focused tests pass in a clean environment using the documented setup, and the README's clone/install/run path succeeds.
- [ ] AC-15: In this repository, the diff is limited to the authoring brief, one adapter-README link, FR/judgement/status record, changelog fragment, and diary entry; the spike tree and ramp manifest are byte-unchanged.
- [ ] AC-16: The FR's prior-art line cites FR-998 by committed path and SHA (done in the Problem section) and states that local normalisation is wholly owned by this demo until that framework work lands.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| 1 | Ship the Copilot-CLI route (FR-995 adapter) as the demo | REJECTED — needs a Copilot seat with `gpt-5.6-sol`; not installable by a stranger. It stays this repo's production route. |
| 2 | Keep a default model in `graph.yaml` or the script | REJECTED (operator, 2026-09-05) — yamlgraph already resolves provider and model from the environment with sane defaults; a second decision point is drift waiting to happen. Documented in `.env.sample` only. |
| 3 | Fix over-flagging in the prompt | REJECTED — two-strike rule; the signal (a path; a following parenthetical) is visible to code and invisible to the model. |
| 4 | Add the skill to the ramp manifest now | DEFERRED — condition set 2026-09-05: ≥ 5 external-PR ledger rows first; then a separate FR against `ramp/manifest.yaml`. |
| 5 | Standalone Python script without yamlgraph | REJECTED for this FR — the point of the demo is "install yamlgraph, copy the skill"; a yamlgraph-free script is a different product. |
| 6 | Fix the `list[str]`-as-string type lie here | NOT IN SCOPE — FR-998 owns the framework boundary; the demo keeps spike 2's normalisation until then. |

## Related

- [FR-995](FR-995-outsider-reader.md), [FR-998](FR-998-anthropic-constrained-structured-output.md), [FR-865](FR-865-ramp-installer.md)
- [docs/2026-09-05-research-plan-cap-journey-census.md](../docs/2026-09-05-research-plan-cap-journey-census.md) §12 (Copilot spike), §13 (llm spike)
- Diaries 2026-09-05: two-adversaries-one-knows-nothing; what-the-informed-adversary-found; the-same-text-two-verdicts
