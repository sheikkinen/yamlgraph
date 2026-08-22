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

1. **Poisoning tripwire.** When the `.coverage` DB shows
   first-test-wins symptoms (distinct contexts ≪ tagged tests), refuse
   with the exact remedy line
   (`COVERAGE_CORE=ctrace pytest ... --cov-context=test`, sequential).
   Same for missing/context-free DBs — today's ⚠️-and-continue becomes
   a hard refusal or visible degraded-mode banner. Applies at the
   **shared loader** so the FR-851 audit constructor is protected too —
   it currently accepts a poisoned DB silently.
2. **Shared context-loader boundary.** `req_audit_questions.py`
   `_load_recorded_contexts` duplicates `req_coverage.py`'s DB read.
   Extract one loader (normalize at the boundary): context read +
   `[param]` suffix stripping + poisoning tripwire, consumed by both.
   Probe evidence: ~26 parametrized contexts are misfiled in **both**
   scripts today, including the enforced FR-851 run.
3. **Derivation disposition (subtraction).** `req_coverage.py
   --implementation` now carries a weaker 3-class derivation beside the
   enforced 5-class `derive_resolution`. Disposition: make
   `req_coverage.py` consume the shared 5-class derivation, or retire
   the `--implementation` census path in favor of the constructor's
   questions output. Keeping both is `false_duplicate` in reverse —
   one boundary, two truths.
4. **Module reconciliation.** CAPs whose declared `modules:` were never
   hit by any of their tagged tests' resolved files — the one
   mechanical anomaly question no existing output answers.
5. **Question-first sections.** Every remaining report section is
   headed by the question it answers — e.g. "Which declared modules
   does no tagged test exercise?" (reconciliation), "Can these numbers
   be trusted?" (instrument status). A datum answering no section
   question is cut, not printed.

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

- [ ] AC-01: One shared context-loader used by both `req_coverage.py`
  and `req_audit_questions.py`; `_load_recorded_contexts` duplication
  removed.
- [ ] AC-02: First-test-wins-poisoned DB (contexts ≪ tagged tests) →
  hard refusal in the shared loader naming `COVERAGE_CORE=ctrace`;
  missing/context-free DB → hard refusal or explicit degraded-mode
  banner, not a scroll-away warning. Witnessed for both consumers.
- [ ] AC-03: `[param]`-suffixed contexts match their marker keys in
  both consumers; witnessed with parametrized contexts.
- [ ] AC-04: Declared-module-never-hit CAP reconciliation exists in
  exactly one output, headed by its question.
- [ ] AC-05: `--strict` behavior byte-identical (gate untouched);
  FR-851 constructor output byte-identical except for param-normalized
  and tripwire-refused cases.
- [ ] AC-06: Tests tagged with the ADR-001 REQ covering these scripts;
  changelog fragment included.
- [ ] AC-06b: Every report section is headed by the question it
  answers; no unheaded data blocks.
- [ ] AC-07: The value/issues table above has ≥2 post-implementation
  entries before any drift-report FR is filed — usage evidence, not
  design enthusiasm, decides the follow-up.
- [ ] AC-08: The 3-class vs 5-class derivation duplication is
  dispositioned (merge or retire) with the decision recorded in this
  FR — keeping both untouched fails this AC.

## Alternatives Considered

- **Build `claims_report.py` first (this FR's original scope):**
  rejected by the operator's `would_you_use_this` — a new ledger on top
  of an untrustworthy census inherits its defects, and the drift
  machinery's value is a forecast until the polished census has been
  used. Deferred; decision input is AC-07's table.
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
- Deferred follow-ups, gated on AC-07 evidence: claims snapshot + drift
  report script, cron cookbook FR, instantiation FR, `fr: legacy`
  disposition FR

## Judgement (pending)

**Verdict:** —

Not judged in the author's session; submit via the judge adapter route.
