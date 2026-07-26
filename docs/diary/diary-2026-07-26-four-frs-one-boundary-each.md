# 2026-07-26 — Four FRs, one boundary each: dependency governance and observability

**Context:** enforced FR-760, FR-761, FR-762, and FR-759 in sequence, all
from the same research doc (`docs/plan-research-dependency-negative-space.md`)
but scoped as four independent, judgement-frozen FRs rather than one large
change. Each required its own isolated worktree since three other sessions
were live in the shared repo (`one_session_one_repo`).

**What happened:** FR-760 (declare `langchain-core` as an explicit
dependency) was the smallest — one line plus rationale. FR-761
(reproducible dependency governance: pip-audit, constraints lockfile,
direct-import AST scanner) was the load-bearing one; FR-762 (example
dependency taxonomy) explicitly branched *from* FR-761's branch to reuse
its scanner internals rather than reimplementing AST resolution — the
judgement's own condition (C-1) named this reuse requirement. FR-759
(OpenTelemetry observability boundary) was set up independently from
`origin/main`, because its judgement (R-4/C-5) explicitly forbade
touching any sibling FR's scope under its own authority, even though all
four came from one research artifact.

**The recurring shape:** every one of the four FRs names its own boundary
precisely and forbids scope bleed into the others — R-4/C-5 in FR-759 is
not boilerplate, it is the judge pre-empting exactly the temptation an
agent has mid-arc: "I'm already touching `pyproject.toml`'s
`optional-dependencies` block for the `otel` extra, may as well tidy the
neighboring entries too." Four frozen scopes, four separate PRs, and a
stacked PR (#464 on #463) where reuse was *required* rather than
convenient — the judgement draws the line between "share code" and
"share scope," and those are not the same thing.

**A concrete trap caught mid-flight:** FR-759's node-execution span
wrapper (`node_otel.py`) was first placed at `yamlgraph/` root, mirroring
the existing `node_timeout.py` sibling. A pre-existing seam-discipline
test (`test_fr717_seams.py::test_root_module_count_bounded`, itself the
product of an earlier FR's split) caught the regression immediately: root
module count 19 > budget 18. The existing module *there* was legacy,
grandfathered; a *new* file at that location is new debt. Moved it to
`yamlgraph/compile/node_otel.py` instead — its only import site — which
also reads better architecturally (it is compile-time wiring, not a
root-level cross-cutting concern like `node_timeout.py` accidentally is).
The module-map line-budget test caught the same growth from a second
angle and needed its bound bumped with a one-line justification, per the
established pattern in that test's own comment trail (FR-677, FR-716/719,
FR-723 all left similar breadcrumbs).

**Design note worth keeping:** OpenTelemetry's global `TracerProvider` can
only be set once per process (`set_tracer_provider` warns and no-ops on a
second call) — this bit the first draft of the in-memory-exporter test
fixture, which tried to install a fresh provider per test. Fixed by
installing one shared provider once and clearing the shared exporter's
captured spans between tests instead. A boundary lesson generalizes here:
process-global singletons force test isolation to happen at the
*data* layer (clear the buffer) when the *object* layer (swap the
provider) is a one-way door.

**Heuristic:** when four FRs share one root cause but the judge splits
them into four authorities, the split is not bureaucratic overhead — it
is the mechanism that keeps a rewrite audit-able later. A single "FR-759
through 762: dependency and observability improvements" commit would have
made it impossible to revert FR-762's taxonomy work without also
reverting FR-759's OTEL boundary, even though they share nothing but a
research doc.

**Seed:** every one of these four FRs adds an `X` extra to
`pyproject.toml` with a rationale entry and a strictness gate
(`dependency_rationale.py`, and now `direct_import_scan.py` for
extra-backed example roots). Is there a point where the number of
independent "optional capability + rationale + strictness gate" triads
justifies a single declarative registry (a `capabilities/extras.yaml`
that generates the `pyproject.toml` block, the rationale stub, and the
CAP file skeleton together) rather than four hand-authored copies of the
same three-file pattern? The pattern has now repeated at least five times
(`otel`, `rag`, `tavily`, `chatterbox`, `a2a`) — is five the graduation
threshold, or does that itself become `framework_costume` — building a
generator for a pattern that is still cheap to hand-author?
