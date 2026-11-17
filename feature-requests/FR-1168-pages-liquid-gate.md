# Feature Request: Pages docs gate — no active Liquid outside `{% raw %}`

**Priority:** HIGH
**Type:** Bug
**Status:** Completed — merged in #783 (a4c88861); Pages green on the merge SHA. `Docs Liquid (Pages build)` is advisory until the operator adds it as a required check (C-3). Round 2 [judgement](FR-1168-pages-liquid-gate.judgement.md) APPROVED WITH REVISIONS; R-1..R-4 folded below
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
- `lib/liquid/tags/raw.rb:3-4,12-22` — `Syntax = /\A\s*\z/` (raw takes no arguments); the block ends at the first token matching `FullTokenPossiblyInvalid = /\A(.*)#{TagStart}\s*(\w+)\s*(.*)?#{TagEnd}\z/om` with `$2 == "endraw"`; tokens before it are emitted as literal text; no end → `tag_never_closed`. **Parser behaviour:** the trailing `(.*)?` means *any* `{%` + optional whitespace + `endraw` + anything + `%}` closes raw — `{% endraw ignored %}` and `{% endraw -%}` close it; `{%- endraw %}` does **not** (`\s*(\w+)` cannot match `-`) and stays raw content. **Project policy (stricter):** only the canonical `{% raw %}` / `{% endraw %}` (whitespace only inside) are permitted; every other `endraw`-named tag is a violation (R-1).
- Jekyll 3.10 renders Liquid only when the body contains `{%` or `{{` (`lib/jekyll/utils.rb:153-156` `has_liquid_construct?`), after stripping front matter (`lib/jekyll/document.rb:13` `YAML_FRONT_MATTER_REGEXP`).

Rendered-file selection, pinned to `jekyll/jekyll@v3.10.0` and `benbalter/jekyll-optional-front-matter@v0.3.2` (R-2):

| Path class | Jekyll 3.10 behaviour | Source | Scanner |
|---|---|---|---|
| Markdown file (`markdown,mkdown,mkdn,mkd,md`) without front matter | static file promoted to a page by optional-front-matter, except basenames `README`/`LICENSE`/`LICENCE`… (readme-index then promotes `README`) | `configuration.rb:27`; ofm `generator.rb:43-45,57-60`, `jekyll-optional-front-matter.rb:10-13` | scanned, blacklist ignored (over-scan is the fail-safe direction) |
| Any file whose first line is `---` | page, Liquid-rendered | `reader.rb:45-46`, `utils.rb:145-146` `has_yaml_header?` (`\A---\s*\r?\n`) | scanned |
| Other files without front matter | static, copied verbatim | `reader.rb:48,103-104` | not scanned |
| Name starting with `.`, `_`, `#`, `~` (any path component) | filtered | `entry_filter.rb:6-8,48-50` | not scanned, except `_posts` |
| `_posts/**` matching `DATE_FILENAME_MATCHER` | posts, rendered | `reader.rb:50,62-64`, `post_reader.rb:26-27`, `document.rb:15` | scanned |
| `exclude:` entries | filtered | `entry_filter.rb:57` | not scanned; list read from `docs/_config.yml` at run time |

`docs/` has no `_posts`, `_layouts` or `_includes` today; underscore directories other than `_posts` (layouts/includes legitimately hold Liquid) stay unscanned.

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
   - **Selection**: the [selection table](#evidence) — Markdown extensions `markdown,mkdown,mkdn,mkd,md`, plus any file whose first line matches `\A---\s*\r?\n`; skip paths with a component starting with `.`, `_`, `#`, `~` except dated files under `_posts/`; skip paths whose relative path or a leading directory matches a `docs/_config.yml` `exclude` entry (fnmatch). The exclude list is read at run time, never copied.
   - **Errors → exit 2 with reason, never an empty pass**: `_config.yml` missing, unparseable, or not a mapping; `exclude` present but not a list; a non-string `exclude` member; a selected file that is not valid UTF-8.
   - **Body**: strip leading front matter (`YAML_FRONT_MATTER_REGEXP`) but keep original line numbers for diagnostics.
   - **Rule** (left-to-right scan):
     - Outside raw, the canonical opener `{% raw %}` (`\{%\s*raw\s*%\}`) enters raw. Any other `{{` is `L001`; any other `{%` (including `{% comment %}`, `{%- raw %}`, `{% raw x %}`) is `L002`.
     - Inside raw, find the next `{%`…`%}` tag. Canonical `{% endraw %}` (`\{%\s*endraw\s*%\}`) leaves raw. A tag Liquid treats as a closer (`\{%\s*endraw(?!\w).*?%\}`) but which is not canonical is `L004` **and** leaves raw, as Liquid does — so `{% raw %}x{% endraw ignored %}{{ secret }}` reports `L004` and `L001`. `{%-\s*endraw…%}` (not a closer in Liquid) is `L004` and the region stays raw.
     - A raw region still open at end of body is `L003` at its opening line.
   - **Output**: `docs/<path>:<line>: Lxxx <message> — wrap in {% raw %}…{% endraw %}` per finding; exit 1 if any, 0 if none.
   - **Arguments**: optional file paths restrict the scan (pre-commit fast path); selection and excludes still apply. If `docs/_config.yml` is among the arguments, scan the full selected tree (a changed exclude list can expose files not in the changed set).
2. **Fix the tree**: wrap each of the 24 tokens in `{% raw %}…{% endraw %}` (inline around the token's span, or around the whole fenced block where a block holds several), matching existing usage in `docs/ebook/v3/07-yamlgraph-core.md`. No other text changes; no new excludes.
3. **Ring 1 — pre-commit**: local hook `docs-liquid`, `entry: python scripts/check_docs_liquid.py`, `files: ^docs/`, `pass_filenames: true`.
4. **Ring 2 — CI**: job `docs-liquid` in `.github/workflows/commitlint.yml`, named `Docs Liquid (Pages build)`, with no title/path/`changes` condition and job-level `permissions: contents: read` (workflow-level permissions unchanged). It runs on every trigger of that workflow — `pull_request`, `merge_group` and the existing `v*` tag push (operator-approved, see Conditions). Steps:
   1. checkout the candidate;
   2. `pip install pyyaml`; `python scripts/check_docs_liquid.py` (full tree);
   3. `actions/jekyll-build-pages@v1` with `source: ./docs`, `destination: ./_site` (the action GitHub's own Pages workflow uses);
   4. a Python step that reads `_site/sheikkinen-process.html` and `_site/investigations/fr1065-resumable-map.html`, HTML-unescapes them, and asserts `{{ secrets.AZURE_SPEECH_KEY }}` and `{{ <key>` occur literally (AC-07).
5. **Traceability**: `capabilities/CAP-306-docs-liquid-gate.yaml`, `REQ-YG-731` — "rendered docs contain no active Liquid outside raw; PRs build the site with the Pages action". Tests tagged `REQ-YG-731`; `ARCHITECTURE.md` regenerated.

The scanner claims only the delimiter rule; it does not claim a full Liquid parse. Build safety is witnessed by the `jekyll-build-pages` step, not by the scanner.

Out of scope: changing branch protection from automation (the operator adds the required context, C-3); Pages migration to Jekyll 4; auto-wrapping; editing FR-751; adding excludes; collections support.

## Acceptance Criteria

- [x] AC-01: FR folds round-1 R-1..R-4 (see [Round-1 judgement disposition](#round-1-judgement-disposition)) and is re-judged.
- [x] AC-02: Full scan of the unwrapped worktree reports exactly the 24 tokens in Evidence (count and paths); after wrapping it exits 0.
- [x] AC-03: Isolated scratch-tree scan at `5ecbc2dc` includes `docs/investigations/fr1065-resumable-map.md:108: L001`; scan at `011317a8` recorded (command, SHA, exit, findings) in Implementation Status.
- [x] AC-04: Unit tests (REQ-YG-731) in isolated `tmp_path` trees:
  - rules: L001, L002 (incl. `{% comment %}`, `{%- raw %}`, `{% raw x %}`), L003; inline and block raw pass; tokens inside fenced code flagged;
  - raw closers (R-1): `{% raw %}literal{% endraw ignored %}{{ secret }}{% raw %}tail{% endraw %}` fails with L004 and L001; `{% endraw -%}` → L004 and leaves raw; `{%- endraw %}` → L004 and stays raw (L003 if nothing closes it);
  - selection (R-2): front matter stripped with correct line numbers; `.markdown` and `.mkd` scanned; `.yaml` with front matter scanned, without not; excluded dir and glob not scanned; `_drafts/` and `.hidden/` not scanned; dated `_posts/2026-01-01-x.md` scanned;
  - errors: missing, malformed and non-mapping config; non-list `exclude`; non-string `exclude` member; invalid UTF-8 — each exit 2;
  - a `_config.yml` argument triggers a full-tree scan.
- [x] AC-05: Gate-bite (R-3): in a throwaway `git init` tree holding the candidate checker, hook config and `docs/_config.yml`, a tracked `docs/liquid-gate-witness.md` containing `{{ x }}` makes `pre-commit run docs-liquid --files docs/liquid-gate-witness.md` fail naming the file; after raw-wrapping it passes. Command, exit codes and output recorded.
- [x] AC-06: CI job `docs-liquid` has no `if:`, job-level `permissions: contents: read`, and runs the scanner, `actions/jekyll-build-pages` and the literal-output step; it succeeds on the PR.
- [x] AC-07: The CI literal-output step passes: HTML-unescaped `_site` pages contain `{{ secrets.AZURE_SPEECH_KEY }}` and `{{ <key>`.
- [x] AC-08: Post-merge (recorded on the PR, not a merge prerequisite): the `pages build and deployment` run on the merge SHA succeeds.
- [x] AC-09: CAP-306 / REQ-YG-731 registered; `python scripts/req_coverage.py --strict` passes.
- [x] AC-10: Changelog fragment and diary entry with **Seed:**.

## Implementation Status

Enforced on `fix/fr-1168-pages-liquid-gate`: FR fold and judgement e4ad7504; RED a1f06742 (28 tests: 25 setup errors from the missing scanner, 3 wiring/bite failures); GREEN `fix(docs): FR-1168 …` (scanner, 24 wraps, hook, CI job, CAP-306, changelog, diary).

**Probe records (AC-02, AC-03)** — `python scripts/check_docs_liquid.py [--root <scratch>/docs]`, scratch trees from `git archive <sha> docs`:

| Tree | Exit | Findings |
|---|---|---|
| worktree at a1f06742, before wrapping | 1 | 24 × L001 in the 10 Evidence files, counts per file identical to Evidence |
| `5ecbc2dc` (first failing Pages SHA) | 1 | 22 × L001, including `docs/investigations/fr1065-resumable-map.md:108` |
| `011317a8` (last green Pages SHA) | 1 | 21 × L001 — all balanced; Jekyll built them and rendered them as empty text |
| worktree after wrapping | 0 | none |

**Wrapping:** inline tokens wrapped in place (fr1065:108, issues-2026-09-24:460/764, fr1124-census:35/36, 017:214, brainstorming:124, research-wiki-format:24); tokens inside fenced blocks wrapped by `{% raw %}`/`{% endraw %}` lines around the whole fence (011, 017 ×2, 019, brainstorming, plan-dm, sheikkinen-process), so the tags never appear inside rendered code.

**Gate bite (AC-05):** `test_precommit_hook_bites_in_throwaway_repo` runs `pre-commit run docs-liquid --files docs/liquid-gate-witness.md` in a `git init` tmp tree: exit 1 naming `liquid-gate-witness.md:1: L001`, exit 0 after wrapping. Also run against the real `.pre-commit-config.yaml` in the worktree: Passed on the 10 wrapped files + `_config.yml`; Failed (exit 1, `docs/liquid-gate-witness.md:1: L001`) on a staged witness, then removed.

**Decisions / deviations:**
- `Finding` is a `NamedTuple`, not a dataclass: `spec_from_file_location` loading (the test pattern) leaves the module out of `sys.modules`, which breaks dataclass annotation resolution under `from __future__ import annotations`.
- REQ markers: `scripts/req_coverage.py` reads only per-test decorators, so GREEN moves `REQ-YG-731` from the RED module-level `pytestmark` onto each of the 24 tests (marker-only change); the module keeps `pytest.mark.process` (FR-756 boundary guard).
- The local `_site` render probe did not run: the Docker daemon is not running on this host. The literal-output assertion runs in the PR's `docs-liquid` job (AC-07).

| Planned operation | Outcome (ran / did not run / changed) | Witness |
|---|---|---|
| probe: scratch tree at 011317a8 | ran | table above; audit.jsonl `git archive 011317a8` |
| probe: scratch tree at 5ecbc2dc | ran | table above; audit.jsonl `git archive 5ecbc2dc` |
| probe: full worktree scan before wrapping = 24 | ran | table above; audit.jsonl `check_docs_liquid.py` |
| probe: `_site` render check | changed | moved to the PR CI literal-output step (Docker not running locally) |
| branch: count differs from 24 | did not run | count matched (table above) |
| branch: build fails unflagged | did not run | no local build; PR CI decides |
| branch: token in should-be-excluded file | did not run | no such file found in the 24 |
| delegation: judge.sh round 2 | ran | e4ad7504 judgement file |
| command: `pytest tests/unit/test_fr1168_docs_liquid_gate.py` | ran | a1f06742 (RED), GREEN commit (28 passed) |
| command: `pre-commit run docs-liquid --files` | ran | audit.jsonl; Implementation Status gate-bite paragraph |
| command: `python scripts/req_coverage.py --strict` | ran | exit 0 at GREEN |
| command: `python scripts/aggregate_capabilities.py` | ran | ARCHITECTURE.md in GREEN commit |

**Unplanned operations:** an inline Python wrap script applied the 24 wraps (diff in GREEN commit); `ruff format` on the scanner and test.

**Post-merge record (C-3, C-5, AC-06..AC-08):**
- AC-06/07: PR #783 head b7e9f6a7: job `Docs Liquid (Pages build)` passed (run 43880266326). The real `jekyll-build-pages` build ran, and the literal step printed `✅ Wrapped Liquid renders literally`.
- C-4: operator reviewed and merged #783 (squash, a4c88861).
- AC-08: `pages build and deployment` run 43881368501 on a4c88861 succeeded, the first green Pages build since 011317a8. The live pages `sheikkinen-process.html` and `investigations/fr1065-resumable-map.html` show `{{ secrets.AZURE_SPEECH_KEY }}` and `{{ <key>` literally.
- C-3: as of 2026-11-17 the required contexts are `commitlint`, `test (3.11)` and `test (3.14)`. The docs-liquid job runs on every PR but does **not** block merge until the operator adds `Docs Liquid (Pages build)` to branch protection.

## Conditions for enforcement

Operator answers (R-4, recorded verbatim, 2026-11-16):

- *Does the operator authorize making the emitted Docs Liquid check required?* — **Yes** (`required_check=true`). The operator adds `Docs Liquid (Pages build)` to branch protection after merge; automation does not.
- *Does the operator approve a real Pages build on every PR, merge-group candidate, and existing tag push?* — **Yes** (`build_every_pr=true`).

| # | Condition |
|---|---|
| C-1 | R-1..R-4 folded and committed before implementation. |
| C-2 | RED witnesses committed (SKIP=pytest) before GREEN; isolated fixture trees only. |
| C-3 | Merge enforcement is claimed only after the operator adds the required context; until then the job is reported as advisory. |
| C-4 | Human review of the checker, hook and workflow diff before merge. |
| C-5 | The candidate's scanner, build and literal-output steps pass before merge; post-merge deployment evidence recorded separately on the PR. |
| C-6 | Inventory disagreement, or a real-build failure the scanner does not flag → stop, record, ask for a scope decision; no new excludes, parser features or migration. |

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
