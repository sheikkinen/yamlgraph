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
