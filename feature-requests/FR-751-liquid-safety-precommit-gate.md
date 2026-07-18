# Feature Request: FR-751 Liquid-Safety Pre-Commit Gate for the Pages Jurisdiction

**Priority:** HIGH (third incident of the same class; the last one held the Pages build red for 6 consecutive runs)
**Type:** Enhancement (enforcement infrastructure — pre-commit + merge-boundary gate)
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-07-19
**Spawned by:** 2026-07-18 Pages incident (FR-748 atlas: literal `{% set %}` in an FR title → `Liquid::SyntaxError`, 6 failed deployments, fixed per-generator with a raw-wrap); FR-425 precedent (diary tree excluded for the identical class, 2026-05-20); `docs/_config.yml`'s `render_with_liquid: false` default that Jekyll 3 **silently ignores** — a config that looks like enforcement and enforces nothing (`gate_checks_shape_not_substance`)
**Related:** `scripts/check_demo_proof.sh` (two-ring gate pattern), `tests/unit/test_concurrency_safety_doc.py` (repo-tree assertion pattern), FR-714 (gate-truth discipline), Scripture `detection_without_enforcement`, `the_one_law`
**Prior art:** FR-441 (pre-commit `files:` pattern hygiene — infrastructure this hook conforms to, not overlap), FR-310/FR-294/FR-380 (pre-commit plumbing for watcher/venv/diary — unrelated domains, keyword-only hits), FR-183 (pipeline simplification — no content overlap). None guards rendered-docs content; the closest true precedent is FR-425 (diary exclusion), dispositioned in Problem as incident #1 of the class this FR closes.

## Summary

A pre-commit hook plus a merge-boundary witness that reject any **active
Liquid token outside a `{% raw %}` region** in Jekyll-rendered files
under `docs/`. The class "Jinja2-quoting project meets Liquid-rendering
site" has now caused three incidents; every fix so far guarded one
producer or excluded one tree. This gate guards the jurisdiction.

## Value Statement

Any file — human-written, generator-written, or pasted — that would break
the Pages build is rejected at commit time with file:line and a fix hint,
instead of being discovered as a red deployment N runs later that nobody
owns.

## Problem

`docs/` is Liquid jurisdiction: GitHub Pages runs Jekyll 3.10, which
parses `{% … %}` / `{{ … }}` in **all** rendered content — including
fenced code blocks — and cannot disable Liquid per-file
(`render_with_liquid` is Jekyll ≥ 4). This project's documentation
constantly quotes Jinja2, which shares the delimiter syntax. Incident
record:

1. **2026-05-20 (FR-425):** diary prose broke the build → whole tree
   excluded in `_config.yml`.
2. **Ebook chapters:** hand-wrapped inline `{% raw %}` — correct but
   maintained by vigilance.
3. **2026-07-18 (FR-748):** generated atlas carried a literal
   `{% set %}` inside an FR title → 6 consecutive deployment failures;
   fixed by wrapping *that generator's* output.

Three incidents, three point fixes, zero structural guards. The next
producer (a new generator, a pasted research doc, a diary graduated into
docs/) re-breaks the build — and the failing workflow blocks nothing, so
it decays into background noise (it took 3 days and a triage request to
notice the atlas failure).

## Proposed Solution

### Checker: `scripts/check_liquid_safety.py` (~120 lines, stdlib only)

- **Scope:** files under `docs/` ending `.md`/`.html`, **minus** the
  exclusion list parsed from `docs/_config.yml` (`exclude:` entries) —
  one source of truth for what Jekyll renders; the checker must never
  drift from the config (it reads it, not copies it).
- **Rule:** outside `{% raw %}…{% endraw %}` regions, any occurrence of
  `{%` or `{{` is a violation. Code fences do NOT protect (Jekyll 3
  fact, verified in the 07-18 incident). Report file:line:token with the
  fix hint: wrap in `{% raw %}`, or add the file to `_config.yml`
  exclude with a reason.
- **Raw-region tracking:** line-scan state machine (inline and block
  `{% raw %}` both occur in the ebook today); unterminated `{% raw %}`
  is itself a violation (it swallows the rest of the page).
- **No allowlist.** The site's pages use no active Liquid (theme handles
  layout). If a page ever legitimately needs Liquid, that is a judged
  exception added to the checker explicitly — not a bypass comment.

### Ring 1 — pre-commit (edit-time feedback)

Hook in `.pre-commit-config.yaml` (`files: ^docs/.*\.(md|html)$`,
pass_filenames true so only staged files scan — fast path).

### Ring 2 — merge boundary (FR-149 lesson: local hooks are bypassable)

Unit test `tests/unit/test_liquid_safety.py` runs the checker over the
committed `docs/` tree — rides the required `test` status check, so a
server-side squash merge cannot land a violation either. (Pattern:
`test_concurrency_safety_doc.py`.)

### Out of scope (purge list)

- Migrating Pages to an Actions-built Jekyll 4 (`render_with_liquid`
  would then actually work) — the platform-level fix, listed as an
  alternative; bigger change, separate FR if ever wanted.
- Auto-wrapping violations (write access to prose from a gate — no).
- Non-docs trees (diary etc. are excluded from rendering; the checker
  honors the exclude list rather than duplicating the decision).
- Retiring the no-op `render_with_liquid` default from `_config.yml` —
  it documents intent and activates for free if Pages ever moves to
  Jekyll 4; the comment already confesses its impotence.

## Acceptance Criteria

- [ ] AC-01 RED: fixture with an unwrapped `{% set %}` under docs/ fails
      the checker naming file:line; the same content inside
      `{% raw %}…{% endraw %}` passes; unterminated `{% raw %}` fails
- [ ] AC-02 Exclusion fidelity: a violation in `docs/diary/` (excluded
      tree) passes; the exclusion list is READ from `_config.yml` at
      check time — a test mutates a copy of the config and observes the
      scope change (no copied list to drift)
- [ ] AC-03 Repo reality: the committed `docs/` tree passes — both
      dated atlases (raw-wrapped), ebook chapters (inline raw), and the
      68 root docs pages, with zero code changes beyond FR-748's
- [ ] AC-04 Gate-bite witness: a deliberate violation in a scratch file
      fails the pre-commit hook (recorded run, FR-714 AC-02 pattern)
- [ ] AC-05 Ring 2: `tests/unit/test_liquid_safety.py` runs the checker
      over `docs/` in the unit suite (merge-boundary enforcement); a
      tmp-tree violation case proves the test can fail
- [ ] AC-06 The FR-748 incident replayed: the pre-fix
      2026-07-18 atlas content (unwrapped title with `{% set %}`) fails
      the checker — the gate would have caught the incident
- [ ] Changelog fragment; CAP + REQ (new enforcement capability); diary
      entry

## Alternatives Considered

- **Keep fixing producers one at a time** — rejected:
  `partial_remediation` verbatim; FR-748 fixed the atlas, the next
  generator re-breaks the site; three incidents already.
- **Exclude all of docs/ from Pages** — rejected: kills the site the
  ebook and research docs exist to serve.
- **Actions-based Pages build on Jekyll ≥ 4 with
  `render_with_liquid: false`** — the true platform fix
  (`does_the_platform_already_do_this`); deferred: deployment migration
  with its own risk surface, and the gate is still wanted afterward as
  defense-in-depth for the day someone re-enables Liquid for one page.
  If this FR's checker grows painful, that migration is the escape
  hatch, as its own FR.
- **CI-only check (no pre-commit ring)** — rejected: the feedback loop
  is the point; a red CI on push costs a round-trip the editor hook
  prevents for free.

## Related Files

- `docs/_config.yml` (exclusion list — the scope oracle)
- `examples/demos/fr-atlas/nodes/render.py` (FR-748 producer-side wrap,
  stays as belt to this FR's suspenders)
- `.pre-commit-config.yaml`, `.github/workflows/workflow.yml` (rings)
- `docs/diary/` 2026-05-20 FR-425 entry (first incident of the class)
