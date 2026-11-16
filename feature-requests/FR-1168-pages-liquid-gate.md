# Feature Request: Gate docs against Liquid syntax that breaks the GitHub Pages build

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Requested:** 2026-11-16
**First consumer / first event:** the author of the next PR that touches `docs/**` — at the moment pre-commit or the PR's CI run reports a Liquid break that today only surfaces, after merge, as a failed `pages build and deployment` run nobody reads.
**Research:** in-body dispositioned alternatives table — [Alternatives Considered](#alternatives-considered) (FR-890 equivalent committed record)
**Prior art:** commit `1c5061aa` (2026-02-26, `fix(docs): add Jekyll config to disable Liquid processing`) — set `render_with_liquid: false`, which Jekyll 3.10 (the github-pages gem) silently ignores, as `docs/_config.yml` itself now records. Commit `013ff5ae` (2026-07-14, `fix(docs): exclude diary from Pages build`) — excluded `docs/diary` after quoted Jinja2 broke the build; the config comment calls this "the enforcement that actually works". Both were per-incident patches with no gate; this is the third occurrence of the same failure class, which is the Scripture's graduation threshold (`process.graduation`, `detection_without_enforcement`). No FR covers the Pages build.

## Summary

GitHub Pages has failed on every push to main since 2026-09-25 (60 of 60 recent `pages build and deployment` runs; last success `011317a8`, 2026-09-25T14:35Z). The cause is one line: `docs/investigations/fr1065-resumable-map.md:108`, added by `5ecbc2dc` (#696), quotes `` `{{ <key>` `` in inline code. Jekyll 3.10 runs Liquid over every Markdown page before Markdown rendering, and Liquid 4 raises `Variable '{{' was not properly terminated`. Fix the line, and add a stdlib scanner that reproduces Liquid 4's tokenizer-level errors over the files Jekyll actually renders, wired into pre-commit and into a CI job that runs on every PR including docs-only ones.

## Value Statement

Docs authors learn of a Pages-breaking edit before merge instead of the public docs site silently freezing at an eight-week-old snapshot.

## Problem

Witnessed 2026-11-16 (`gh run view --log-failed` on the latest Pages run):

```
Liquid Exception: Liquid syntax error (line 108): Variable '{{' was not properly
terminated with regexp: /\}\}/ in investigations/fr1065-resumable-map.md
```

1. **Nothing gates it.** `pages-build-deployment` is GitHub's own workflow; it runs after merge, on main, and is not a required check. `workflow.yml`'s `test` job no-ops on docs-only diffs (`changes.code` filter `'!**/*.md'`), so no CI step ever parses docs as Liquid.
2. **The failure is silent.** 60 consecutive failures over seven weeks went unnoticed until a manual `status` read on 2026-11-16.
3. **The class recurs.** Third occurrence (see Prior art). Each previous fix patched the instance; the config comment documents why the one config-level cure (`render_with_liquid: false`) is ineffective on Jekyll 3.
4. **Jekyll stops at the first error**, so the build log cannot tell us whether `fr1065` is the only break.

## Ideal Result

A docs edit that would make Jekyll 3.10 raise a Liquid syntax error fails locally at commit and fails the PR, with `path:line` and the Liquid error class, before merge. The Pages build on main is green.

## Planned Operations

```yaml
probes:
  - "scan the docs tree at 011317a8 (last green Pages build) — must report zero findings; any finding there is a false positive and the rule is wrong"
  - "scan the docs tree at 5ecbc2dc (first red build) — must report exactly docs/investigations/fr1065-resumable-map.md:108"
  - "scan the current docs tree — decides whether fr1065:108 is the only break (Jekyll stops at the first)"
  - "read docs/_config.yml exclude list — decides which paths the scanner skips"
branches:
  - "calibration at 011317a8 reports any finding → narrow the rule to what Liquid 4 actually raises, re-run both calibration points"
  - "current tree has breaks beyond fr1065:108 → fix each in the same GREEN commit and list them in Implementation Status"
  - "a finding is inside text that Jekyll does not render (excluded path, no-front-matter static file) → fix the file-selection rule, not the finding"
delegations:
  - "judge.sh: 1 run"
waits:
  - "judge"
  - "PR CI including the new docs-liquid job"
  - "post-merge pages build and deployment run on main"
commands:
  - scripts/judge.sh
  - python scripts/check_docs_liquid.py
  - pytest tests/unit/test_fr1168_docs_liquid_gate.py
  - python scripts/req_coverage.py --strict
  - python scripts/aggregate_capabilities.py
  - gh run list --workflow pages-build-deployment
```

## Proposed Solution

1. **Fix the instance.** Wrap the quoted Jinja fragment on `fr1065-resumable-map.md:108` in `{% raw %}…{% endraw %}`, following the repo's existing pattern (`docs/2026-07-18-fr-atlas.md`, `docs/ebook/v3/07-yamlgraph-core.md`). The rendered site shows `` `{{ <key>` `` unchanged.
2. **`scripts/check_docs_liquid.py`** (stdlib + PyYAML; PyYAML is already a core dependency):
   - **File selection** mirrors Jekyll 3.10 on this site: `*.md` / `*.markdown` under `docs/` (jekyll-optional-front-matter renders them without front matter) and any other file starting with a `---` front-matter line; skip paths matched by `docs/_config.yml` `exclude` (fnmatch on the relative path and each leading directory) and any path component starting with `_` or `.` (Jekyll defaults, covers `_site`).
   - **Tokenizer** is a port of Liquid 4.0.4's `TemplateParser` regex: `(\{%.*?%\}|\{\{.*?\}\}?|\{%|\{\{)` with DOTALL. Rules, each a Liquid 4 parse error:
     - `L001` a `{{` token that does not end with `}}` — *Variable was not properly terminated* (the incident class);
     - `L002` a `{%` token that does not match `{%-?\s*\w+.*?-?%}` — *Tag was not properly terminated*;
     - `L003` a `{% raw %}` / `{% comment %}` with no matching end tag before EOF.
   - Content between `{% raw %}` and `{% endraw %}` (and `comment`/`endcomment`) is not tokenized, as in Liquid.
   - Output: one `path:line: Lxxx message` per finding; exit 1 on any finding, 0 otherwise. Optional positional paths restrict the scan (pre-commit passes changed files); the selection and exclude rules still apply.
3. **Wiring.**
   - `.pre-commit-config.yaml`: local hook `docs-liquid`, `files: ^docs/`, `pass_filenames: true`.
   - `.github/workflows/commitlint.yml`: job `docs-liquid` ("Docs Liquid syntax (Pages build)") with no title or path condition, so it runs on docs-only PRs and on `merge_group`; installs PyYAML and runs the full scan.
4. **Traceability.** `capabilities/CAP-306-docs-liquid-gate.yaml` with `REQ-YG-731`; tests tagged `REQ-YG-731`; `ARCHITECTURE.md` regenerated.

Out of scope: unknown-tag and unclosed-block detection (`{% for %}` without `endfor`, `{% set %}`). Those are real Liquid errors but the calibration probe decides whether today's tree contains any; adding them without a witness is speculative. Making the gate a required status check is a branch-protection change for the human operator.

## Acceptance Criteria

- [ ] `docs/investigations/fr1065-resumable-map.md:108` renders the same text and no longer contains an unterminated `{{` outside `raw`.
- [ ] `python scripts/check_docs_liquid.py` exits 0 on the fixed tree and exits 1 naming `fr1065-resumable-map.md:108 L001` on the tree at `5ecbc2dc`.
- [ ] The same command reports zero findings on the docs tree at `011317a8` (last green Pages build).
- [ ] Unit tests (REQ-YG-731) cover L001, L002, L003, content inside `raw`, a balanced `{{ x }}` that is not flagged, an `exclude`d path that is not scanned, a `_`-prefixed path that is not scanned, and a non-Markdown file without front matter that is not scanned.
- [ ] Pre-commit hook `docs-liquid` and CI job `docs-liquid` exist; the CI job has no path or title condition.
- [ ] After merge, the `pages build and deployment` run on main succeeds (post-cutoff; recorded on the PR).
- [ ] CAP-306 / REQ-YG-731 registered; `python scripts/req_coverage.py --strict` passes.
- [ ] Changelog fragment and diary entry.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Fix line 108 only | Rejected: third occurrence of the class; `detection_without_enforcement`. |
| A2 | Exclude `docs/investigations` from the build (the `013ff5ae` cure) | Rejected: hides investigations from the site and moves the next break to whichever directory is not excluded. |
| A3 | `render_with_liquid: false` | Rejected: already present, ignored by Jekyll 3.10 (`1c5061aa`). |
| A4 | Run real Jekyll (`github-pages` gem) in CI | Rejected for now: adds a Ruby toolchain and minutes to every PR; the incident class is tokenizer-level and a port of one regex reproduces it. Revisit if a non-tokenizer Liquid error reaches main. |
| A5 | `python-liquid` package as the parser | Rejected: new dev dependency under FR-761 governance, and it implements Liquid 5 / Shopify semantics rather than Jekyll 3.10's Liquid 4.0.4. |
| A6 | Switch Pages to an Actions-built Jekyll 4 site where `render_with_liquid` works | Rejected: larger migration, and Jekyll 4 still parses Liquid in pages that do not opt out. |
| A7 | Port Liquid 4's tokenizer regex in a stdlib script (chosen) | Accepted: proper parser for the boundary (not an ad-hoc regex list), no new dependency, calibrated against the last green and first red builds. |

## Related

- `docs/_config.yml` — exclude list and the Jekyll 3 note
- `.github/workflows/commitlint.yml` — always-run hygiene jobs
- `docs/investigations/fr1065-resumable-map.md` — the break
- FR-1065 — the investigation that added the line
