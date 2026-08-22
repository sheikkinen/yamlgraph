# 2026-08-22 — FR-850: The Instrument Confesses Before It Testifies

## What happened

Enforced FR-850 (coverage-context boundary) RED→GREEN in one session:
one shared loader (`scripts/coverage_contexts.py`) replaced two
divergent `.coverage` readers, warning-and-continue became
`CoverageContextError` hard refusal with a 0.25 poisoning tripwire, the
implementation report gained a five-class witness split whose summary
raises `ValueError` when the counts don't sum to the denominator, and
module reconciliation was partitioned into measured never-hit vs
unmeasured.

## Cognitive traps encountered

1. **Benchmark artifact resolves its own root.** The first AC-02
   byte-identity check ran the HEAD version of `req_coverage.py` from
   `tmp/ac02/` — where `Path(__file__).parent.parent` silently became
   `tmp/`, producing a 239-line diff that looked like a regression. The
   old code wasn't wrong; the *harness* moved the boundary. Same law as
   ever: normalize at the boundary — a script copied for comparison must
   be run from the directory contract it was written for. One `git show
   > scripts/_ac02_old.py` later: SUMMARY-IDENTICAL, DETAIL-IDENTICAL.

2. **read_raw_output_first paid again, immediately.** The reconciliation
   section passed all its unit tests, but reading the raw Q3 output
   showed `yamlgraph/edge_compiler` and `yamlgraph/models/__init__`
   flagged never-hit — extensionless *file* declarations matched only as
   directory prefixes. The unit tests couldn't see this because the
   fixtures used well-formed declarations; the registry's actual data
   had a shape the spec never named. One read of the prose, one
   two-line matcher fix. The remaining never-hits (dotted function-level
   declarations like `edge_compiler._add_conditional_edges`) are genuine
   registry data-quality signals, left visible rather than laundered.

3. **Line-number-addressed confessions are a refactoring tax.** The
   noqa-confession gate matches `file#Lline` exactly, so moving an
   import block invalidates confessions that were true a minute ago
   (CONF-019, CONF-410 both needed line-shift updates). The gate checks
   presence at a coordinate, not identity of the sin. Cheap to pay,
   easy to forget; grep for `noqa` in every edited file before commit.

## Heuristic

**A gate that warns is a gate that lies twice**: once when it lets the
poisoned instrument through, and again when downstream numbers inherit
false authority. FR-850's whole shape is converting one ⚠️-and-continue
into a refusal that *names its remedy* — the error message carries
`COVERAGE_CORE=ctrace`, `--cov-context=test`, no `-n auto`, so the
refusal is also the documentation.

**Seed:** the never-hit list now honestly exposes dotted function-level
`modules:` declarations in the capability registry
(`yamlgraph/edge_compiler._add_conditional_edges`) that no file matcher
can resolve. Should the registry schema forbid sub-file declarations, or
should reconciliation learn to resolve them via AST? Which side of the
boundary owns that normalization?

## Demo run (post-merge, real `.coverage`)

`python scripts/req_coverage.py --implementation` — exit 0, 12,400 lines.

Stored reports:
- [2026-08-22-fr850-implementation-report.txt.gz](2026-08-22-fr850-implementation-report.txt.gz)
  — full `--implementation` output, gzipped (12,400 lines / 888 KB raw
  exceeds the 500 KB hook; `gunzip -k` to read) (Q1/Q2/Q3)
- [2026-08-22-fr850-summary-report.txt](2026-08-22-fr850-summary-report.txt)
  — default summary report (230 lines)

- **Header:** 413/413 requirements covered; 6,190 unique tagged tests,
  6,593 test-req pairs.
- **Q1** (linkage census): per-CAP, per-REQ witness classification for
  every requirement — each test named under its resolution class.
- **Q2** (trust): `Instrument: 3052 recorded test contexts for 6190
  tagged tests (.coverage accepted)` — above the 0.25 tripwire, so the
  report runs; the gap (fast suite skips slow/process tests) is stated,
  not hidden. Witness split sums exactly:
  `coverage: 3376 | ast: 475 | no-link-ran: 0 | no-link-unrecorded:
  1279 | doc-witness: 1463` = 6,593.
- **Q3** (reconciliation): 18 capabilities flagged with declared-but-
  never-hit yamlgraph modules (e.g. CAP-171 `llm_factory_async.py`,
  CAP-209 root-package seams); 623 declarations outside `yamlgraph/`
  correctly reported as unmeasured rather than falsely never-hit.

What the demo proves: the report now answers its three questions with
an honest denominator — half the tagged suite has no recorded context
and *says so* (no-link-unrecorded: 1279) instead of counting those
pairs as covered. The 18 Q3 flags are actionable registry-hygiene
leads, not noise: each is either a stale declaration or a genuinely
untested seam.

## Key findings from reading the stored reports

Read the raw census (not just the headline) per
`read_raw_output_first`. The headline and the census *disagree*, and
the disagreement is the product working:

1. **Presence says 100%, substance says 66%.** The header reports
   413/413 requirements covered — the presence gate. The Q1 census
   shows **141 of 413 REQs (34%) have zero code-linked witnesses** in
   this coverage DB. Split by cause:
   - **73 doc-witness only** — every tagged test reads repo docs,
     never executes yamlgraph code. Structural for docs/process CAPs;
     a defect signal elsewhere.
   - **64 unrecorded only** — witnesses exist but were skipped by the
     fast recording run (slow/process/integration). A full
     `COVERAGE_CORE=ctrace` recording would resolve these; the honest
     ceiling is therefore ~82% code-linked, not 66%.
   - 4 mixed.

2. **Doc-witness-only clusters name their own explanations — and one
   anomaly.** Top owners: CAP-145 Copilot Instrumentation (7 — scripts
   outside `yamlgraph/`, structurally unmeasurable), CAP-71/74/79/82/99
   (docs/gate CAPs — doc-witness is their correct class). The anomaly:
   **CAP-131 Anthropic Prompt Caching has 4 doc-witness-only REQs** —
   a core code capability whose witnesses for those REQs never touch
   the code they certify. Registry-hygiene lead, same class as the Q3
   never-hits.

3. **The five-class split converts a boolean into a distribution, and
   the distribution is the finding.** Before FR-850 the report could
   only say "covered". Now `coverage: 3376 | ast: 475 | no-link-ran: 0
   | no-link-unrecorded: 1279 | doc-witness: 1463` — and no-link-ran
   at exactly **0** is the strongest line: every tagged test that
   actually ran under recording touched linkable code or a repo doc.
   No witness ran and touched *nothing*. The instrument's confession
   (3052/6190 contexts) bounds every claim above.

**Reflection:** the trap this report retires is
`gate_checks_shape_not_substance` — but the report itself demonstrates
the trap's successor: a *substance* census still inherits its
instrument's blind spots (the 64 unrecorded REQs look identical to
missing witnesses until Q2 is read alongside Q1). The cure is the
pairing itself: never publish a linkage number without its instrument
line. **Seed:** should the fast-suite recording gap be closed by a
scheduled full-suite `ctrace` run whose `.coverage` artifact is the
one the report consumes — making no-link-unrecorded structurally zero?

## CAP-131 investigated: the anomaly dissolves, and a phantom surfaces

Reading the CAP-131 census closed the anomaly and opened a better one:

- **The 4 doc-witness-only REQs are correctly classified.** REQ-YG-302/
  304/305/306 are FR-219 *demo-artifact* contracts (demo dir exists,
  prompts share cached segments, README explains benefits,
  demo-output.log proves execution). Their witnesses inspect artifacts,
  not code — doc-witness is their honest class. CAP-131 is simply a
  mixed capability: 8 code REQs (all coverage-linked) + 4 artifact REQs.
  Not a defect; the census separating them IS the feature.

- **The real find was one line up.** REQ-YG-287's witness list includes
  `test_sim117_auto_fix` — ruff SIM117 auto-fix tests tagged to "System
  segments schema validation". Provenance: FR-281 (watcher2 ruff
  --unsafe-fixes, 127d5077) reused REQ-YG-287 without registering its
  own requirement; FR-465 (caf6c034) deleted the retired watcher2 tests
  and "fixed REQ traceability" — but missed this sibling integration
  test. Textbook `partial_remediation`. Liveness: zero consumers of
  SIM117/unsafe-fixes remain in yamlgraph/, scripts/, or .github/; the
  test exercises *ruff's* behavior against temp files. Subtraction
  proposal filed: `.chaplain/inbox/delete-orphaned-sim117-test-phantom-req-tag.md`.

The pattern worth keeping: the census's first-order flag (doc-witness
cluster) was a false lead that dissolved under inspection, while the
true defect (phantom tag) sat unclassified inside a *green*
coverage-linked section — visible only because the report prints every
witness name under its REQ. Aggregates flag; rosters convict.

## Reflection: is stale-REQ analysis needed?

No — it already ran; what's owed is **disposition**. FR-851's Stage-1
audit (haiku, 412/412 reconciled, `tmp/req-audit/report.md`) rendered
10 `[no]` + 235 `[partial]` verdicts, and it caught the SIM117 phantom
independently of my read (REQ-YG-287 `[partial]`: "two unrelated tests
(SIM117) appear misclassified"). Two instruments converging on the same
defect from different directions — roster reading and LLM audit — is
the traceability spine working.

But most flagged verdicts cite `no-link-unrecorded ... resolved_files
empty`: they are the FR-850 recording gap (64 unrecorded-only REQs)
wearing an audit-verdict costume, not semantic staleness. Triaging 235
partials by hand before closing the instrument gap would be
`metric_archaeology_before_reading_output` in reverse — human effort
spent on what a mechanical re-recording clears. The disposition order
is: (1) full-suite `ctrace` recording, (2) re-run the FR-851 audit
against the honest DB, (3) triage the residue — those are the genuine
SIM117-class phantoms. FR-859 takes the one proven phantom now;
the residue triage waits for the deflated report.
