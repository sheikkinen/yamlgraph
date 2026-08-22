# Feature Request: Make the Existing Implementation-Traceability Report Trustworthy and Usable

**Priority:** MEDIUM
**Type:** Tooling
**Status:** Proposed
**Effort:** 0.5–1 day
**Requested:** 2026-08-22
**First consumer / first event:** the operator, reading the first
trustworthy `--implementation` run to decide whether the planned
claims-drift machinery (snapshot + weekly diff, plan step 2) is worth
building at all. First event: a manual
`python scripts/req_coverage.py --implementation` run in the working
tree — no new script, no cron, no CI.

**Prior art:** FR-851-requirement-witness-audit (enforced 2026-08-22, now
**partially covers this FR**: its `scripts/req_audit_questions.py`
`derive_resolution` ships the 5-class split — coverage/ast/doc-witness/
no-link-ran/no-link-unrecorded — answering this FR's original split,
cause-partition, and doc-witness questions; its report is the anomaly-first
view. This FR is rescoped to the residue: instrument tripwire, shared-loader
normalization, module reconciliation, and disposition of the now-duplicated
weaker derivation in `req_coverage.py`); FR-450-judge-demo-hardening,
FR-269-cli-inter-run-state-chaining, FR-490-dm-v2-chapter-outline-ui,
FR-364-copilot-instrumentation-gap-closure (noun-level matches only — none
touches `req_coverage.py` output or coverage-context integrity; no scope
intersection).

## Summary

Polish `scripts/req_coverage.py --implementation` into a usable,
trustworthy form before any new reporting tool exists: print the full
resolution split (its main denominator is currently omitted), refuse
sysmon-poisoned coverage DBs, normalize parametrized context ids, and
add an anomaly-first summary mode. The planned sibling
`claims_report.py` (snapshot + drift, plan step 2) is **explicitly
deferred**: it must earn its filing from the value added / issues
learned by actually using the polished report — the existing report
earns its place in the task list first.

## Value Statement

The operator gets numbers that can be believed and read in one screen
from a tool that already exists; the drift-report decision gets made on
evidence from use instead of on design enthusiasm.

## Problem

The existing report is unusable in exactly the ways today's three-run
session exposed (see Raw Output Read):

- Its Summary line reports only the fallbacks ("2591 via AST, 2861
  unresolvable") — the coverage-resolved count, the mode's entire
  point, is printed nowhere.
- It silently accepts a first-test-wins-poisoned `.coverage` DB and
  produces a plausible wrong report.
- Parametrized context ids never match marker keys, so those pairs are
  misfiled as no-link.
- It is a census: 6555 pairs at equal emphasis, thousands of lines,
  no anomaly-first view a human would actually read.

Building a new reporting script on top of an untrustworthy census would
inherit every one of these defects (`detection_without_enforcement`
inside the flagship spine, now at the instrument layer).

## Raw Output Read (measurement / metric-tooling FRs only)

- **Samples read:** three full `python scripts/req_coverage.py
  --implementation` runs at working tree 6f05d33d, 2026-08-22: (1)
  against the stale no-context `.coverage`, (2) against a fresh
  `pytest --cov-context=test` run under the default coverage core, (3)
  against a `COVERAGE_CORE=ctrace` run. Coverage DB inspected directly
  via SQLite between runs.
- **What I saw:**
  - **The default coverage core silently breaks per-test contexts on
    Python 3.14**: coverage 7.15's `sys.monitoring` core disables
    line events after first execution, so only the first test to hit a
    line gets context credit — 1017 contexts for 5957 passing tests,
    1356 `line_bits` rows, resolution split 1103 coverage / 2591 AST /
    2861 unresolved. No warning is emitted. Forcing
    `COVERAGE_CORE=ctrace` yields 3446 contexts, 12013 rows, and the
    split becomes **3339 coverage / 509 AST / 2707 no-link**. The
    snapshot generator MUST set `COVERAGE_CORE=ctrace` (and run
    sequentially — no `-n auto`) or the whole evidence layer is a
    first-test-wins artifact.
  - **~2700 test-req pairs execute no `yamlgraph/` source at all** even
    with correct recording — the honest residual class (doc-contract
    witnesses, subprocess-driven CLI tests, hook/registry tests, plus
    integration and `slow` tests not in the recording run). The
    snapshot must record `resolution: coverage|ast|unresolved` per
    pair, or the report's denominators lie.
  - **Zero-file tests are a legitimate class, not an anomaly:**
    `test_race_pipeline_docs::TestGraphYamlRaceSection::*` (16 tests,
    "0 files") witness documentation contracts — they assert headings
    and examples exist in reference docs. A naive
    "test-hits-no-module" rule would flag every doc-contract witness;
    the report needs a `doc-witness` classification.
  - Parametrized tests are a small residual mismatch: coverage context
    ids carry `[param]` suffixes, marker keys don't (26 such contexts);
    the snapshot loader should strip the suffix before matching.

## Ideal Result

One existing command, run against a correctly recorded `.coverage` DB,
produces numbers the operator can believe (full
coverage/AST/no-link split with denominators), refuses to lie when the
instrument is broken, and offers a one-screen anomaly view. After 2–3
real uses, the "value added / issues learned" record in this FR either
justifies the drift-report follow-up or kills it.

## Proposed Solution

Rescoped 2026-08-22 after FR-851 enforcement: the resolution split,
no-link cause partition, doc-witness class, and anomaly-first report
now exist in `scripts/req_audit_questions.py` / `req_audit_report.py`.
What remains is the residue FR-851 did not answer, plus the duplication
it created. The gated `--strict` path untouched:

1. **Poisoning tripwire (binding, R-1).** For `--implementation` and
   `req_audit_questions.py`, missing `.coverage`, zero non-empty
   contexts, or a poisoned coverage-context DB is a **hard refusal** —
   one explicit exception type whose message names
   `COVERAGE_CORE=ctrace`, `--cov-context=test`, and sequential
   recording (no `-n auto`). Non-implementation `req_coverage.py`
   modes, including `--strict`, must not read this loader. Mechanical
   poisoning predicate: distinct non-empty context test-ids
   < 0.25 × distinct req-tagged test ids supplied by the caller
   (observed: sysmon-poisoned ratio 1017/5957 ≈ 0.17, healthy ctrace
   3446/5957 ≈ 0.58) — testable from a synthetic SQLite fixture plus a
   marker set.
2. **Shared context-loader boundary (R-1).** One shared helper under
   `scripts/`, consumed by both `req_coverage.py --implementation` and
   `req_audit_questions.py` (removing `_load_recorded_contexts`):
   returns normalized `test_id -> source files` and normalized recorded
   context ids, strips `[param]` suffixes from the final test-id
   component, and raises the R-1 exception on invalid DBs. Probe
   evidence: ~26 parametrized contexts are misfiled in **both** scripts
   today, including the enforced FR-851 run.
3. **Derivation merge (R-3 — retirement not authorized).** Keep
   `req_coverage.py --implementation`; make it consume the shared
   5-class `derive_resolution` and remove the weaker local 3-class
   truth. No second resolution truth remains.
4. **Module reconciliation (R-2, measured scope only).** CAPs whose
   declared `modules:` were never hit by any of their tagged tests'
   resolved files — limited to declared modules that normalize to
   measured `yamlgraph/` paths. Non-`yamlgraph/` declarations are
   reported, if at all, as "unmeasured by this coverage run", never as
   never-hit anomalies. Expanding the coverage source set is not
   authorized here.
5. **Question-first sections.** Every remaining report section is
   headed by the question it answers — e.g. "Which declared modules
   does no tagged test exercise?" (reconciliation), "Can these numbers
   be trusted?" (instrument status). A datum answering no section
   question is cut, not printed.
6. **Traceability registration (R-4).** Add or update a
   capability/requirement entry for the implementation-traceability
   report behavior (shared loader, poisoning refusal, param
   normalization, 5-class split, module reconciliation); all new tests
   tagged with that REQ id. CAP-243 (audit constructor) and CAP-18
   (marker enforcement) do not cover this surface.

```bash
# Correct recording (documented in the script's --help and CLAUDE.md)
COVERAGE_CORE=ctrace pytest tests/unit tests/integration -q \
  --cov=yamlgraph --cov-context=test
python scripts/req_coverage.py --implementation --anomalies
```

### Value-added / issues-learned record (fills in during use)

The decision input for the deferred drift FR. Seeded from today's runs:

| Date | Run | Learned | Action taken |
|------|-----|---------|--------------|
| 2026-08-22 | 3 manual runs | sysmon core silently poisons contexts on Py3.14 | this FR (tripwire) |
| 2026-08-22 | ctrace run | summary omits its own primary-path count | this FR (honest summary) |
| 2026-08-22 | ctrace run | ~2707 no-link pairs; doc-witness is a legitimate class | this FR (anomaly partition) |

## Acceptance Criteria

Revised per judgement (R-1…R-5 folded 2026-08-22):

- [ ] AC-01: A single shared coverage-context loader under `scripts/`
  is used by both `req_coverage.py --implementation` and
  `req_audit_questions.py`; the duplicated `_load_recorded_contexts`
  DB read is removed.
- [ ] AC-02: `req_coverage.py` summary, `--detail`, and `--strict`
  behavior are byte-identical when `--implementation` is not requested.
- [ ] AC-03: Missing `.coverage`, zero non-empty contexts, and the
  poisoned-context predicate hard-fail both consumers, with an error
  naming `COVERAGE_CORE=ctrace`, `--cov-context=test`, and
  sequential/no-`-n auto` recording.
- [ ] AC-04: Synthetic SQLite coverage fixtures cover missing DB,
  context-free DB, poisoned DB, and healthy DB cases for both
  consumers.
- [ ] AC-05: Parametrized coverage context ids with `[param]` suffixes
  normalize to the same marker keys in both consumers, covered by a
  parametrized test fixture.
- [ ] AC-06: `req_coverage.py --implementation` reports the full
  five-class split `coverage|ast|doc-witness|no-link-ran|
  no-link-unrecorded` with totals whose sum equals the
  implementation-mode test-REQ pair denominator.
- [ ] AC-07: The local three-class derivation is removed or reduced to
  a thin call into the shared five-class derivation; no second
  resolution truth remains.
- [ ] AC-08: Declared-module reconciliation is emitted in exactly one
  question-headed output section and applies only to measured
  `yamlgraph/` module declarations; unmeasured non-`yamlgraph/`
  declarations are not reported as never-hit anomalies.
- [ ] AC-09: Every implementation report section is headed by the
  human question it answers; no unheaded data block remains in the
  `--implementation` output.
- [ ] AC-10: FR-851 constructor output is unchanged except where
  parametrized contexts normalize or the shared loader correctly
  refuses an invalid coverage DB.
- [ ] AC-11: Capability/ARCHITECTURE registry entries describe the new
  implementation-traceability behavior, and all new/changed tests are
  tagged with the corresponding REQ id.
- [ ] AC-12: The script help or adjacent documented command shows the
  correct recording command with `COVERAGE_CORE=ctrace`,
  `--cov-context=test`, and sequential execution; a changelog fragment
  is included.

### Deferred follow-up gate (not an implementation AC, per R-5)

The value/issues table above must have ≥2 post-implementation entries
before any drift-report FR is filed — usage evidence, not design
enthusiasm, decides the follow-up.

## Alternatives Considered

- **Build `claims_report.py` first (this FR's original scope):**
  rejected by the operator's `would_you_use_this` — a new ledger on top
  of an untrustworthy census inherits its defects, and the drift
  machinery's value is a forecast until the polished census has been
  used. Deferred; decision input is the deferred follow-up gate's table.
- **Per-PR advisory check (csap VBOT-101-B shape):** no trigger surface —
  yamlgraph's human flow is direct pushes to main.
- **Gate `--implementation` in pre-commit:** full coverage-with-contexts
  is minutes-slow; would violate the fast-hook budget and reintroduce
  the exact cost that made the edge advisory.

## Related

- Plan: `docs/2026-08-21-plan-architecture-claims-pipeline.md` (Current
  status — 2026-08-22; steps 2–3; sample report; FR breakdown item 2)
- Reflection: `docs/diary/diary-2026-08-22-the-spine-is-a-claim-store.md`
- Precedents: `scripts/req_coverage.py` (ADR-001), csap VBOT-101-A spike
  (PASS), `weekly-recap.yml` FR-821 (future consumer via cookbook FR)
- Deferred follow-ups, gated on the follow-up gate's evidence: claims
  snapshot + drift report script, cron cookbook FR, instantiation FR,
  `fr: legacy` disposition FR

## Judgement

**Verdict:** APPROVED WITH REVISIONS (2026-08-22, judge adapter route,
gpt-5.5) — revisions R-1…R-5 folded above. Full judgement:
`feature-requests/FR-850-req-coverage-usable-form.judgement.md`.
Authority active within the frozen scope (D-1…D-7); not authorized:
`claims_report.py`, snapshot/drift/cron machinery, CI/pre-commit gates,
doctrine edits, coverage-source expansion, `--strict` changes.
