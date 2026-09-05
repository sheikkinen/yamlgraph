# Feature Request: `yamlgraph-outsider` — standalone demo repo; install yamlgraph, copy the skill, get an outsider view before review

**Priority:** MEDIUM
**Type:** Enhancement (public demo repository + one code cap)
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-09-05
**First consumer / first event:** a maintainer of any GitHub repository who has just opened a pull request and wants to know what a reader with no context cannot follow — first event: `pipx install yamlgraph && ./yamlgraph-outsider 123 --repo owner/name`. Second consumer: `sheikkinen/deviant-daily` (the one existing ramp consumer), on its next feature PR. Third: this repo's own PRs, where the Copilot-route wrapper (`scripts/outsider.sh`, FR-995) already runs; the demo is the route for everyone without a Copilot seat.
**Research:** [docs/2026-09-05-research-plan-cap-journey-census.md §12–§13](../docs/2026-09-05-research-plan-cap-journey-census.md) — two spikes, all runs recorded with expectations written first. Spike 1 (Copilot CLI, `gpt-5.6-sol`) is the FR-995 production route; spike 2 (`docs/spikes/outsider-llm-2026-09-05/`, plain `llm` node, provider API, structured output) is the standalone shape this FR ships. Alternatives dispositioned in-body.
**Prior art:** [FR-995](FR-995-outsider-reader.md) — the reader itself; this FR changes nothing in it and reuses its doctrine, rule, fixtures and ledger schema. [FR-865](FR-865-ramp-installer.md) — the ramp installer ships judge/review skills to other repos as doctrine + wrapper without the adapter; this FR is the *standalone* route for one skill and does **not** touch the ramp manifest (ramp inclusion is gated on ≥ 5 external-PR runs — Alternatives #4). FR-998 (anthropic constrained structured output; open on branch `feat/list-type-lie`, not yet on main) — the framework-side fix for `list[str]` arriving as a JSON string (FR-059 class) found by spike 2; this FR keeps spike 2's in-code normalisation until FR-998 lands and does not touch the framework. [docs/node-type-census-2026-08.md] — no overlap. No REJECTED FR in this territory.

## Summary

A small public repository, `sheikkinen/yamlgraph-outsider`, that anyone can clone to run the outsider reader on a pull request: install `yamlgraph`, sign in to `gh`, put one API key in `.env`, run one script. It contains the spike-2 graph and prompt, the typed finalize tool, the entry script, the four fixtures with their expectations, and the `outsider-view` skill files (`SKILL.md`, `doctrine.md`) so a Copilot user in any repository can copy the skill and ask for an outsider view by name before review.

**The script decides nothing about models.** Provider and model come from yamlgraph's own resolution chain — `node.provider > defaults.provider > PROVIDER env > "anthropic"`, model from `{PROVIDER}_MODEL` env with yamlgraph's base default — and the graph declares neither. The only place a model is named is `.env.sample`, which sets `ANTHROPIC_MODEL=claude-haiku-4-5` (yamlgraph's own default for that provider, so the sample is documentation of the default, not a choice made by this repo). Users change the model by editing `.env`, never a flag.

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

1. **Repository** `sheikkinen/yamlgraph-outsider`, MIT (both confirmed by the operator 2026-09-05; not open questions for the judge), created from `docs/spikes/outsider-llm-2026-09-05/` (copy, not reinvention): `graph.yaml`, `prompts/outsider.yaml`, `tools.py`, `yamlgraph-outsider`, `fixtures/{pr-591,plain-591,pr-591-v2,positive}.md` + `EXPECTATIONS.md`, `.github/skills/outsider-view/{SKILL.md,doctrine.md}` copied from this repo with the invocation line pointing at `./yamlgraph-outsider`, `README.md`, `LICENSE`, `.env.sample`, `.gitignore` (`.env`, `out/`).
2. **No model decision in graph or script.** `graph.yaml`: remove `defaults.provider`, `defaults.model`, and the node's `provider:`/`model:` lines; keep `temperature: 0.0`. Entry script: remove `--model`/`--provider` flags and the `MODEL`/`PROVIDER` variables; the report filename uses the model the run actually used, read back from the finalize result, not from a flag. `.env.sample`:
   ```
   # One provider key. yamlgraph picks the provider from PROVIDER (default anthropic)
   # and the model from <PROVIDER>_MODEL (defaults are yamlgraph's own).
   ANTHROPIC_API_KEY=
   ANTHROPIC_MODEL=claude-haiku-4-5
   # PROVIDER=openai   OPENAI_API_KEY=   OPENAI_MODEL=
   ```
3. **Code cap in `finalize` (the one behavioural change):** demote — never drop — a "could not understand" item to a separate `demoted` list when (a) its quote matches a path or identifier pattern (`/`, `.yaml`, `.py`, `.md`, `CAP-\d+`, `FR-\d+`, `REQ-`), or (b) the quote occurs in the body immediately followed by ` (`, ` — `, or `: ` (an inline gloss). Demoted items are still printed under their own heading. The derived rule counts only the remaining items. Unit tests on the committed spike-2 reports: the PR #592 gloss quote demotes; `capabilities/CAP-*.yaml` demotes; "someone writing a graph" does not.
4. **Selftest twice.** `--selftest` runs each fixture twice and requires NO/NO/NO/YES on both passes — the stability claim from spike 2 is the demo's claim, so the demo proves it every time.
5. **README:** what it does (three sentences, no project words) · install · use · read the report · *before review* (two readers, one given everything, one given nothing) · selftest · known limits (over-flagging is capped, not solved; verdict is advisory; one run per PR) · provenance (FR-995, the two spikes). Run the tool on the README before publishing; print its item count in the README.
6. **Ledger** as in FR-995 (attributable rows, real PRs only), written to `out/ledger.jsonl` in the demo repo.
7. **Back-reference in this repo:** one line in `.github/skills/outsider-view/adapters/README.md` pointing at the demo as the non-Copilot route; the spike directory stays as historical evidence and is not edited.

## Acceptance Criteria

- [ ] AC-1: `grep -E 'provider:|model:' graph.yaml` returns nothing except the state declarations; the entry script has no `--model`/`--provider` flags and no model name anywhere; `.env.sample` is the only file naming a model.
- [ ] AC-2: With `.env` = `.env.sample` + a key, `./yamlgraph-outsider --input fixtures/pr-591.md` writes a report whose `<!-- … model: … -->` header shows `claude-haiku-4-5` (yamlgraph's default, not the demo's).
- [ ] AC-3: Changing `ANTHROPIC_MODEL` (or `PROVIDER` + the matching key) in `.env` changes the model in the header; no file other than `.env` is edited.
- [ ] AC-4: The cap demotes path/identifier quotes and glossed quotes; unit tests on the committed spike-2 reports prove the PR #592 gloss quote and `capabilities/CAP-*.yaml` demote, and "someone writing a graph" does not. Demoted items are rendered, never dropped.
- [ ] AC-5: `./yamlgraph-outsider --selftest` runs each fixture twice on the default model and passes NO/NO/NO/YES on both passes; expectations committed before the first run.
- [ ] AC-6: The README's item count line is produced by running the tool on the README; the report is committed under `out/`.
- [ ] AC-7: `.github/skills/outsider-view/SKILL.md` in the demo names `./yamlgraph-outsider` as the invocation; `doctrine.md` is byte-identical to this repo's.
- [ ] AC-8: The ledger has ≥ 1 row from a real PR in a repository other than `sheikkinen/yamlgraph`.
- [ ] AC-9: In this repo: one line in the adapter README; spike directory unchanged; no ramp manifest change; changelog fragment; FR status; diary.

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

- [FR-995](FR-995-outsider-reader.md), FR-998 (branch `feat/list-type-lie`), [FR-865](FR-865-ramp-installer.md)
- [docs/2026-09-05-research-plan-cap-journey-census.md](../docs/2026-09-05-research-plan-cap-journey-census.md) §12 (Copilot spike), §13 (llm spike)
- Diaries 2026-09-05: two-adversaries-one-knows-nothing; what-the-informed-adversary-found; the-same-text-two-verdicts
