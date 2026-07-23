# 2026-07-21 — FR-754 to FR-756 Boundary Enforcement

Today enforced a three-step boundary chain in strict order: package boundary (FR-754), ownership boundary (FR-755), then test/CI boundary (FR-756). The key trap was trying to mechanize process marker insertion quickly: the first pass produced syntactic breakage (`__future__` ordering, marker overwrite patterns), which proved the same doctrine point these FRs encode — boundary automation must preserve grammar contracts, not just token presence.

What worked:
- Enforcing FR-754 first simplified FR-756 classification semantics: ID-registry tests no longer had to carry an unresolved package leak.
- Adding collection-time source-scan enforcement turned process classification from checklist theatre into a hard gate.
- Import-linter contract for FSM ownership converted ruling-C from documentation into executable architecture.

What failed initially:
- Bulk marker insertion ignored multi-line imports and existing `pytestmark = ...` overrides.
- Boundary test fixture for FR-756 originally wrote outside `tests/unit`, so the hook correctly did not fire; the witness had to exercise the same path rules as production collection.

Heuristic extracted:
- When adding mechanical classifications to Python tests, normalize structure first (docstring, `__future__`, imports, marker merge), then classify; never mutate marker lines without checking existing `pytestmark` assignment semantics.

Seed: Can we add a tiny structural safety pass (AST-based marker insertion + marker-merge rewrite) as a reusable script so future classification FRs stop using ad-hoc text mutation?
