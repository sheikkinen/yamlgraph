# Feature Request: Pages docs gate — no active Liquid outside `{% raw %}`

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed (round 2: rescoped to the strict rule after round-1 judgement)
**Requested:** 2026-11-16
**First consumer / first event:** the author of the next PR that touches `docs/**` — at the moment pre-commit or the PR's `docs-liquid` CI job names a `{{`/`{%` that would either break the Pages build or silently render as empty text on the site.
**Research:** in-body dispositioned alternatives table — [Alternatives Considered](#alternatives-considered), with pinned parser evidence in [Evidence](#evidence) (FR-890 equivalent committed record). Classification: `enforcement/latency-critical`; `is_this_a_graph: no` — a deterministic delimiter check at a commit/merge boundary has no model judgement in it (FR-890 classification rule).
**Prior art:** [FR-751-liquid-safety-precommit-gate.md](FR-751-liquid-safety-precommit-gate.md) — **Proposed**, never judged, no judgement sibling; same jurisdiction and the same strict rule. This FR **supersedes** it for implementation (FR-751 is not edited). Differences: FR-751's merge ring was a unit test, but `workflow.yml`'s `test` job no-ops on Markdown-only diffs (`changes.code` filter `'!**/*.md'`), so that ring would not bite on docs-only PRs; this FR uses an always-run CI job instead, and adds a real Jekyll build. Commit `1c5061aa` (2026-02-26) set `render_with_liquid: false`, which Jekyll 3.10 ignores. Commit `013ff5ae` (2026-07-14, FR-425 incident) excluded `docs/diary`. FR-748 (2026-07-18) raw-wrapped one generator's output after `{% set %}` broke 6 deployments. Each was a point fix; this is the fourth incident of the class.

## Summary

GitHub Pages has failed on every push to main since 2026-09-25 (60 of 60 recent `pages build and deployment` runs; last success `011317a8`). Cause: `docs/investigations/fr1065-resumable-map.md:108` (added by `5ecbc2dc`, #696) quotes `` `{{ <key>` `` and Liquid 4 raises *Variable '{{' was not properly terminated*. A scan of the rendered tree finds 23 further active Liquid tokens that do not break the build but render as **empty text** — e.g. `docs/sheikkinen-process.md:201-206` publishes a workflow snippet whose `{{ secrets.AZURE_SPEECH_KEY }}` lines are blank on the site.

Rule (from FR-751): in every file Jekyll renders with Liquid, any `{{` or `{%` outside a `{% raw %}…{% endraw %}` region is a violation. Wrap all 24 current tokens; add `scripts/check_docs_liquid.py`; run it in pre-commit and in an always-run CI job that also performs a real `actions/jekyll-build-pages` build of `docs/`.

## Value Statement

Docs authors learn before merge that a Jinja2 quote will break the site or vanish from it, instead of the public docs freezing for weeks or silently dropping text.

## Problem

1. **Build break, unseen for seven weeks.** `pages-build-deployment` runs after merge on main and is not a required check; 60 consecutive failures went unnoticed until a manual status read on 2026-11-16.
2. **Silent content loss.** 23 balanced `{{ … }}` tokens in 9 files render as empty strings. Not an error, so neither Jekyll nor any check reports it — a `plausible_wrong_answer` on the published site.
3. **No gate on docs-only changes.** `workflow.yml`'s `test` job skips its steps when only `*.md` changed.
4. **Recurrence.** Fourth incident (Prior art). This project documents Jinja2, which shares Liquid's delimiters, so every new doc is a candidate.
5. **Jekyll stops at the first error**, so a build log never lists all breaks.

## Ideal Result

No published docs page contains active Liquid. A commit or PR introducing `{{`/`{%` outside `raw` in a rendered docs file fails with `path:line`; the PR also proves the site builds with the real Pages action. The Pages build on main is green, and the 24 current tokens display literally.

## Evidence

Pinned Liquid 4.0.4 (the github-pages gem's Liquid; the failing log names `liquid-4.0.4` and `jekyll-3.10.0`), `https://github.com/Shopify/liquid/blob/v4.0.4/`:

- `lib/liquid.rb:28-40` — `TagStart = /\{\%/`, `VariableStart = /\{\{/`, `TemplateParser = /(#{PartialTemplateParser}|#{AnyStartingTag})/om`: every `{{` and `{%` in the page body is a Liquid token, including inside Markdown code fences (Liquid runs before Markdown in Jekyll 3).
- `lib/liquid/tags/raw.rb:3-4,12-22` — `Syntax = /\A\s*\z/` (raw takes no arguments); the block ends at the first token matching `FullTokenPossiblyInvalid = /\A(.*)#{TagStart}\s*(\w+)\s*(.*)?#{TagEnd}\z/om` with `$2 == "endraw"`; tokens before it are emitted as literal text; no end → `tag_never_closed`. Consequence: `{%- endraw %}` (whitespace control) does **not** close raw in 4.0.4 (`\s*(\w+)` cannot match `-`), so only `{% raw %}` / `{% endraw %}` without `-` are accepted markers.
- Jekyll 3.10 renders Liquid in a page only when the body contains a Liquid construct, and strips YAML front matter (`\A---\s*\r?\n … ^---`) before rendering. `jekyll-optional-front-matter` (enabled by github-pages, visible in the failing log's `Requiring:` list) makes every `.md`/`.markdown` a page without front matter.

Current-tree inventory (2026-11-16, `docs/_config.yml` excludes applied): 24 active tokens in 10 files — `sheikkinen-process.md` 6; `memento/feature-requests/019-questionnaire-generator.md` 3, `011-yamlgraph-web-ui.md` 3, `017-mermaid-improvements.md` 3, `brainstorming-fsm-yamlgraph.md` 2; `issues-2026-09-24.md` 2; `issues-2026-09-27-fr1124-census.md` 2; `plan-dm.md` 1; `research-wiki-format.md` 1; `investigations/fr1065-resumable-map.md` 1. Non-Markdown files under `docs/` (html, json, jsonl, txt, yaml, py, sh, mermaid, webp): none starts with front matter, so none is Liquid-rendered; no file uses `{%-`/`-%}`.

## Planned Operations

```yaml
probes:
  - "isolated scratch tree (git archive) of docs/ at 011317a8 — record findings; balanced tokens there are expected (they render empty), so this calibrates file selection, not zero findings"
  - "isolated scratch tree at 5ecbc2dc — findings must include docs/investigations/fr1065-resumable-map.md:108"
  - "full scan of the worktree before wrapping — must equal the 24-token inventory in Evidence; a difference means selection or raw handling is wrong"
  - "after wrapping, render check: the wrapped text appears literally in the jekyll-build-pages output (_site) for sheikkinen-process.md and fr1065-resumable-map.md"
branches:
  - "scan count differs from the 24-token inventory → fix the selection/raw rule before wrapping anything"
  - "jekyll-build-pages fails on the wrapped tree with an error the scanner does not flag → stop; record it; scope decision (C-6)"
  - "a token sits in a file that should be excluded rather than published → raise it to the operator; do not add excludes inside this FR"
delegations:
  - "judge.sh: 1 run (round 2)"
waits:
  - "judge"
  - "PR CI including docs-liquid job"
  - "post-merge pages build and deployment run on main"
commands:
  - scripts/judge.sh
  - python scripts/check_docs_liquid.py
  - pytest tests/unit/test_fr1168_docs_liquid_gate.py
  - pre-commit run docs-liquid --files
  - python scripts/req_coverage.py --strict
  - python scripts/aggregate_capabilities.py
  - gh run list --workflow pages-build-deployment
```

## Proposed Solution

1. **`scripts/check_docs_liquid.py`** — stdlib + PyYAML (core dependency), read-only.
   - **Selection** (mirrors Jekyll 3.10 + github-pages plugins): files under `docs/` that are `.md`/`.markdown`, or any other file whose first line matches `^---\s*$`; skip any path whose relative path or a leading directory matches a `docs/_config.yml` `exclude` entry (fnmatch), and any path component starting with `_` or `.`. The exclude list is read at run time, never copied. Missing/unparseable `_config.yml`, an `exclude` that is not a list, or a selected file that is not valid UTF-8 → exit 2 with the reason (never an empty pass).
   - **Body**: strip leading YAML front matter (`---` … `---`) but keep original line numbers for diagnostics.
   - **Rule**: scan the body left to right. `{% raw %}` (regex `\{%\s*raw\s*%\}`) opens a raw region; the first `{% endraw %}` (`\{%\s*endraw\s*%\}`) closes it; text inside is ignored. Outside raw, any other `{{` or `{%` — including `{% comment %}` and whitespace-control forms — is a violation `L001` (`{{`) or `L002` (`{%`). An unclosed raw is `L003` at its opening line.
   - **Output**: `docs/<path>:<line>: Lxxx <message> — wrap in {% raw %}…{% endraw %}` per finding; exit 1 if any, 0 if none.
   - **Arguments**: optional file paths restrict the scan (pre-commit fast path); selection and excludes still apply. If `docs/_config.yml` is among the arguments, scan the full selected tree (a changed exclude list can expose files not in the changed set).
2. **Fix the tree**: wrap each of the 24 tokens in `{% raw %}…{% endraw %}` (inline around the token's span, or around the whole fenced block where a block holds several), matching existing usage in `docs/ebook/v3/07-yamlgraph-core.md`. No other text changes; no new excludes.
3. **Ring 1 — pre-commit**: local hook `docs-liquid`, `entry: python scripts/check_docs_liquid.py`, `files: ^docs/`, `pass_filenames: true`.
4. **Ring 2 — CI**: job `docs-liquid` in `.github/workflows/commitlint.yml` ("Docs Liquid (Pages build)"), no title/path/`changes` condition, runs on `pull_request` and `merge_group`: checkout the candidate, `pip install pyyaml`, `python scripts/check_docs_liquid.py` (full tree), then `actions/jekyll-build-pages@v1` with `source: ./docs`, `destination: ./_site` (the action GitHub's own Pages workflow uses) — the real-build witness on every PR.
5. **Traceability**: `capabilities/CAP-306-docs-liquid-gate.yaml`, `REQ-YG-731` — "rendered docs contain no active Liquid outside raw; PRs build the site with the Pages action". Tests tagged `REQ-YG-731`; `ARCHITECTURE.md` regenerated.

The scanner claims only the delimiter rule; it does not claim a full Liquid parse. Build safety is witnessed by the `jekyll-build-pages` step, not by the scanner.

Out of scope: making `docs-liquid` a required status check (operator decision, C-3); Pages migration to Jekyll 4; auto-wrapping; editing FR-751; adding excludes.

## Acceptance Criteria

- [ ] AC-01: FR folds round-1 R-1..R-4 (see [Round-1 judgement disposition](#round-1-judgement-disposition)) and is re-judged.
- [ ] AC-02: Full scan of the unwrapped worktree reports exactly the 24 tokens in Evidence (count and paths); after wrapping it exits 0.
- [ ] AC-03: Isolated scratch-tree scan at `5ecbc2dc` includes `docs/investigations/fr1065-resumable-map.md:108: L001`; scan at `011317a8` recorded (command, SHA, exit, findings) in Implementation Status.
- [ ] AC-04: Unit tests (REQ-YG-731) in isolated `tmp_path` trees: L001, L002 (incl. `{% comment %}` and `{%- raw %}`), L003; inline and block raw pass; `{%- endraw %}` does not close raw; tokens inside fenced code are flagged; front matter is stripped with correct line numbers; excluded dir and glob not scanned; `_`-prefixed path not scanned; `.markdown` scanned; `.yaml` with front matter scanned, without front matter not; invalid UTF-8 and missing config exit 2; `_config.yml` argument triggers full scan.
- [ ] AC-05: Gate-bite: recorded `pre-commit run docs-liquid --files <scratch incident>` fails, passes once wrapped.
- [ ] AC-06: CI job `docs-liquid` has no `if:` and runs both the scanner and `actions/jekyll-build-pages`; it succeeds on the PR.
- [ ] AC-07: Rendered text preserved: in the PR's `jekyll-build-pages` output (or a local run), `{{ secrets.AZURE_SPEECH_KEY }}` and `` `{{ <key>` `` appear literally.
- [ ] AC-08: Post-merge (recorded on the PR, not a merge prerequisite): the `pages build and deployment` run on the merge SHA succeeds.
- [ ] AC-09: CAP-306 / REQ-YG-731 registered; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-10: Changelog fragment and diary entry with **Seed:**.

## Round-1 judgement disposition

Round 1 (narrow L001–L003 subset, APPROVED WITH REVISIONS, kept as `tmp/judgement-round1.md`, not promoted) required:

- **R-1** disposition FR-751, classification, pinned evidence → Prior art, Research and Evidence above. FR-751's strict rule was **adopted** (operator decision 2026-11-16) rather than distinguished.
- **R-2** freeze a subset, no full-parser claim, raw/comment semantics, real build before merge → the strict rule needs no parser-equivalence claim; raw/comment/whitespace-control semantics are fixed from `raw.rb`; the real build runs on every PR via `jekyll-build-pages`.
- **R-3** front matter, selection matrix, explicit errors, config-change full scan → Proposed Solution §1 and AC-04.
- **R-4** gate-bite witnesses, isolated calibration, pre-/post-merge separation → AC-03, AC-05, AC-06, AC-08.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Fix `fr1065:108` only | Rejected: fourth incident; leaves 23 silent blanks; `detection_without_enforcement`. |
| A2 | Narrow tokenizer-error subset (round-1 draft) | Rejected by operator: does not catch silent empty renders or `{% set %}` (the FR-748 incident); needs a parser-equivalence claim the strict rule does not. |
| A3 | Exclude more directories (FR-425 cure) | Rejected: hides published content; moves the next break elsewhere. |
| A4 | `render_with_liquid: false` | Rejected: present already, ignored by Jekyll 3.10 (`1c5061aa`). |
| A5 | Real Jekyll build only, no scanner | Rejected: a build passes while balanced tokens vanish; the scanner gives edit-time `path:line`. Kept as the CI second step. |
| A6 | Unit test over the tree (FR-751 ring 2) | Rejected: the `test` job no-ops on Markdown-only diffs. |
| A7 | `python-liquid` dependency | Rejected: new dependency under FR-761; Liquid 5 semantics; unnecessary for a delimiter rule. |
| A8 | Migrate Pages to an Actions-built Jekyll 4 | Rejected: separate migration; Jekyll 4 still renders Liquid unless every page opts out. |
| A9 | Strict delimiter rule + always-run CI job with real build (chosen) | Accepted. |

## Related

- `docs/_config.yml`, `.github/workflows/commitlint.yml`, `.pre-commit-config.yaml`
- FR-751 (superseded proposal), FR-748, FR-425, FR-1065
