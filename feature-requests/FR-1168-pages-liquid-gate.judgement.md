# Judgement: FR-1168 Pages docs gate - no active Liquid outside raw

**Verdict:** APPROVED WITH REVISIONS — the strict rule addresses both build failure and silent text loss, but raw termination, rendered-file selection, executable witnesses, and merge-boundary authority need correction; implementation authority activates only after R-1 through R-4 are folded into the FR and the applicable gates are satisfied.

**Prior art:** [FR-751-liquid-safety-precommit-gate.md](FR-751-liquid-safety-precommit-gate.md) — Proposed, unjudged; superseded by FR-1168 for implementation. Round 1 (narrow subset) judgement retained outside the repo; its R-1..R-4 are dispositioned in the FR.

**Reviewed against:** Committed `feature-requests/FR-1168-pages-liquid-gate.md` at `266f2cca` (working copy verified unchanged); `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md` (supplied doctrine and targeted committed passages); `feature-requests/FR-751-liquid-safety-precommit-gate.md`; targeted passages of `feature-requests/FR-748-fr-atlas-onboarding-summary.md` and `feature-requests/FR-425-hook-classification-daemon.md`; `docs/_config.yml`; `.github/workflows/commitlint.yml`; `.github/workflows/workflow.yml:1-160`; `.pre-commit-config.yaml:1-180`; `docs/investigations/fr1065-resumable-map.md:95-115`; `docs/sheikkinen-process.md:184-214`; raw-marker passages of `docs/ebook/v3/07-yamlgraph-core.md`; metadata/file lists for cited commits `1c5061aa`, `013ff5ae`, `5ecbc2dc`, and `011317a8`. The Liquid source quotations in FR-1168:35-39 were evaluated as committed evidence; the external source and deployment logs were not independently retrieved. No author transcript, scratch round-1 judgement, or uncommitted notes were consumed.

## What is sound

The strongest case against this proposal is that a green delimiter approximation could become another false assurance. Nevertheless, fixing only the unterminated variable would leave balanced expressions exposed: the committed incident contains the incomplete delimiter (`docs/investigations/fr1065-resumable-map.md:108`), while the workflow example contains six balanced expressions (`docs/sheikkinen-process.md:201-206`). A strict publication policy plus a real build is a justified response, provided its raw exemptions cannot hide active expressions.

The alternatives table contains genuine alternatives, not cosmetic variants: producer repair, publication exclusions, per-page configuration, build-only validation, parser dependency, and platform migration are dispositioned; the rejected narrower approach and deterministic/non-graph classification are explicit (FR-1168:8-9,114-122). This satisfies the research-substance requirement without requiring another research graph. FR-751 is expressly superseded rather than silently duplicated.

| Criterion | Finding and evidence |
|---|---|
| Scope | Sound: one publication defect class, a read-only checker, literal-preserving repairs, and two execution rings; migration, automatic wrapping, and new excludes are excluded (FR-1168:73-86). |
| Consistency | Needs revision: the quoted Liquid endraw recognizer is broader than the exemption scanner (FR-1168:38,76); an always-run check is not automatically a merge gate (FR-1168:81,86). |
| Measurability | Mostly sound: counts, exit codes, historical SHAs, rendered text, and post-merge outcomes are specified (FR-1168:91-99). The scratch-hook command can skip its fixture unless its repository and path are fixed (R-3). |
| Feasibility | Sound direction: no new Liquid parser is needed; Markdown-only test skipping is confirmed by `workflow.yml:23-45`. Job permissions and reproducible render inspection need explicit instructions (R-3). |
| Architecture alignment | Reuses the raw-marker pattern (`docs/ebook/v3/07-yamlgraph-core.md:194-199`) and runtime config (`docs/_config.yml:22-29`). Selection fidelity and actual blocking must match those claims (R-2, R-4). |
| Single responsibility | Sound: scanner, raw wrapping, and build witness jointly protect published literal text; no independent feature needs splitting (FR-1168:15,73-84). |
| Strategic classification | **Contrib/example**, specifically repository-local publishing enforcement, not a framework primitive: one Pages publishing use case using existing Python/pre-commit/Actions mechanisms (FR-1168:7-8,73-82). No YAMLGraph runtime extension is authorized. |
| Testability | Strong isolated-fixture matrix (FR-1168:93), but missing adversarial raw-termination and rendered-special-path cases allow green tests with a false exemption (R-1, R-2). |

## Required revisions

### R-1: Reject noncanonical Liquid raw terminators instead of hiding them

FR-1168:38 quotes a recognizer whose trailing `(.*)?` permits text after the `endraw` name; FR-1168:76 recognizes only whitespace before `%}`. Those are not equivalent. The no-full-parser disclaimer at line 84 does not excuse an exemption that conceals active Liquid.

Add a fail-closed rule: while inside raw, a tag recognized as an `endraw` candidate by the cited Liquid 4.0.4 rule but not accepted as the canonical marker must produce a diagnostic and a nonzero exit, not be ignored as ordinary raw content. Keep exact canonical markers as the sole permitted exemptions. Correct line 38's assertion that only its whitespace-only closers are recognized by Liquid; distinguish project policy from parser behavior.

Add a regression containing:

```text
{% raw %}literal{% endraw ignored %}{{ secret }}{% raw %}tail{% endraw %}
```

The proposed scanner would accept this by ignoring the first closer and the second opener; the quoted Liquid recognizer closes the first raw block early, exposing `{{ secret }}`. Require this fixture to fail. Include `{% endraw -%}` and retain the specified `{%- endraw %}` case, with expected behavior grounded in the pinned recognizer. This is correction of the raw exemption, not authority to implement a full Liquid parser.

### R-2: Evidence and test the rendered-file boundary

The statement that selection "mirrors Jekyll 3.10 + github-pages plugins" (FR-1168:74) is not established by the front-matter observations at lines 39-41. In particular, blanket skipping of every underscore-prefixed component is unsafe for a claim covering every rendered file: Jekyll's `_posts` is a rendered-content namespace, not simply an ignored directory.

Fold a compact, committed selection table into Evidence with pinned Jekyll/plugin source paths and line references for ordinary Markdown pages, front-matter pages, excludes, hidden paths, and `_posts`. Amend the blanket underscore exclusion so rendered posts are scanned; explicitly distinguish ignored directories from Jekyll's special rendered namespaces. Add isolated tests for a valid dated Markdown post under `docs/_posts/`, an ignored underscore directory, and a hidden directory. No collections feature or deployment migration is authorized.

Complete the existing error contract: missing, malformed, or non-mapping config, non-list `exclude`, and non-string exclude members must exit 2 with an explicit reason. Add tests for these cases rather than allowing incidental type errors. Keep config runtime-driven and config-change full scans as already planned (FR-1168:74,78).

### R-3: Make the hook and build witnesses reproducible

Replace AC-05's `<scratch incident>` (FR-1168:94) with a throwaway Git tree containing the candidate hook/checker/config and a tracked `docs/liquid-gate-witness.md`. Run `pre-commit run docs-liquid --files docs/liquid-gate-witness.md` from that tree. Assert the checker actually runs, names the fixture, and fails before wrapping, then passes after wrapping. A file under `tmp/` or outside the selected docs root would be skipped by `files: ^docs/` (FR-1168:80), proving nothing.

Specify the job-level minimum `permissions: contents: read` for checkout, without expanding workflow-wide permissions (`commitlint.yml:18-19` currently declares only `pull-requests: read`). State that the unconditional job also runs on this workflow's existing tag-push trigger (`commitlint.yml:10-12`); do not change unrelated triggers or jobs to hide that consequence.

For AC-07, name how the actual `_site` output is inspected: assertions in a subsequent CI step against the generated HTML, or a recorded local build with command, build identity, output paths, and assertions. Match the literal text after HTML entity decoding; a literal `<key>` need not occur byte-for-byte in HTML. Assert both cited examples, not merely action success. No permanent artifact-upload or deployment feature is required.

### R-4: Separate check execution from human-authorized merge enforcement

FR-1168:86 excludes required-status configuration while the proposal claims a commit/merge-boundary gate (lines 8,15,31). An unconditional optional job cannot prevent merge. This conflicts with `.github/copilot-instructions.md:154-155`.

Add explicit Conditions for Enforcement to the FR and replace dangling references to C-3/C-6 (FR-1168:53,86) with defined conditions. Keep automated branch-protection changes out of scope, but make operator confirmation that the exact emitted check context is required on PR/merge-queue candidates an external prerequisite to claiming merge enforcement.

Surface these human decisions verbatim as questions to be answered in the implementation record: **Does the operator authorize making the emitted Docs Liquid check required? Does the operator approve a real Pages build on every PR, merge-group candidate, and existing tag push?** Until answered affirmatively, describe the proposed CI job as advisory and do not mark the merge-gate objective complete.

Require human review of the checker, pre-commit wiring, and workflow diff before merge, as mandated by judge doctrine:98-101. For a real-build failure after the delimiter policy passes, stop, record the actual failure, and obtain a separate scope decision; do not widen exclusions or migrate Pages.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/check_docs_liquid.py`: read-only strict delimiter policy, safe raw exemptions, runtime selection/config, explicit exit codes |
| D-2 | The ten docs files enumerated in FR-1168:41: raw wrapping only |
| D-3 | `.pre-commit-config.yaml`: the `docs-liquid` local hook only |
| D-4 | `.github/workflows/commitlint.yml`: unconditional docs job, scanner, real Pages build, minimum job permissions, literal-output witness if implemented there |
| D-5 | `tests/unit/test_fr1168_docs_liquid_gate.py`: isolated checker/config/selection regressions and wiring assertions |
| D-6 | `capabilities/CAP-306-docs-liquid-gate.yaml`, `REQ-YG-731`, regenerated `ARCHITECTURE.md` |
| D-7 | FR implementation record, changelog fragment, and FR-1168 diary reflection with **Seed:** |

Not authorized: a full Liquid parser, additional parser dependencies, framework/runtime changes, automatic rewriting, additional excludes, collections support, Pages migration/deployment changes, editing FR-751, automated branch-protection changes, or unrelated workflow cleanup.

## Revised acceptance criteria

- [ ] AC-01: R-1 through R-4 are folded into the committed FR; the selection evidence and human-decision conditions are explicit. No uncommitted round-1 notes are needed to interpret the contract.
- [ ] AC-02: Before wrapping, the full scan reports the committed 24-token inventory with paths and original lines; afterward it exits 0. An inventory discrepancy is recorded and resolved against actual selection evidence, never by tuning the checker to the expected count.
- [ ] AC-03: Isolated scans at `5ecbc2dc` and `011317a8` record commands, SHAs, exits, and findings; the former names `docs/investigations/fr1065-resumable-map.md:108: L001`.
- [ ] AC-04: REQ-YG-731 tests cover the complete original AC-04 matrix plus R-1's noncanonical-closer escape, R-2's rendered post/ignored/hidden path distinctions, and malformed config shapes. Failures exercise the policy, not missing fixtures or imports; diagnostics preserve original line numbers.
- [ ] AC-05: The R-3 isolated Git-tree pre-commit witness runs rather than skips, fails on its tracked docs fixture, and passes after raw wrapping; commands and outputs are recorded.
- [ ] AC-06: Structural assertions establish no title/path/changes condition or dependency that skips the docs job; it runs the full scanner followed by `actions/jekyll-build-pages@v1` on the candidate with `source: ./docs` and `destination: ./_site`, using job-level read-only contents permission. The PR's actual job succeeds.
- [ ] AC-07: Recorded assertions against the real generated HTML, after entity decoding, show `{{ secrets.AZURE_SPEECH_KEY }}` in the process page and the quoted incomplete delimiter in the investigation page. A green build alone does not satisfy this criterion.
- [ ] AC-08: The operator's required-check decision and review of enforcement changes are recorded. If the check is not required, merge enforcement remains explicitly incomplete.
- [ ] AC-09: After merge, the Pages deployment on the merge SHA succeeds and is recorded on the PR; this observation is not a circular pre-merge prerequisite.
- [ ] AC-10: CAP-306/REQ-YG-731 are registered, generated architecture is synchronized, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-11: The changelog fragment and FR-1168 reflection with **Seed:** exist; the FR records implementation status, calibration, rendering evidence, and any authorized deviations.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold all required revisions into the committed FR before implementation; this draft does not independently authorize edits. | GATE |
| C-2 | Commit/run focused RED witnesses before the fix, then GREEN, following `.github/copilot-instructions.md:198`; use isolated fixture trees, not the shared index. | GATE |
| C-3 | Obtain affirmative operator decisions on required-check configuration and always-run build cost before claiming merge enforcement; automation must not change protection settings. | GATE |
| C-4 | A human reviews the checker and hook/workflow diffs before merge; model judgement cannot satisfy adversarial enforcement review. | GATE |
| C-5 | Require the actual candidate's scanner/build and literal-render witnesses to pass before merge; keep post-merge deployment evidence separate. | GATE |
| C-6 | On inventory disagreement or an uncovered build failure, stop and record evidence; obtain a scope decision rather than adding excludes, parser features, or migration work. | GATE |

Authority granted: conditional authority for D-1 through D-7 only after the revisions are folded and C-1/C-2 are met; completion and merge-enforcement claims additionally require C-3 through C-6.
