# Diary 2026-09-26 — The census found the docs, not the typo

**Context:** FR-1084 enforcement: `graph run` refuses `--var`/`--var-file`
keys that the compiled input schema would drop.

The fix was twelve lines. The first full-suite run after it failed eight
tests. Seven were CLI tests that pass `--var topic=...` to a `MagicMock`
app. A mock has no input schema, so the check had nothing to compare
against. Those tests had asserted for months that the CLI passes variables
through. They never asserted that the graph keeps them. A mock app accepts
any key, so the mocks were built around the same dropped-input defect the
FR removes. The repair was to declare, in each test, the schema its
variables need. That turned each test's unstated premise into a stated one.

The census was meant to find key typos in documented invocations. It found
none. It found seven invocations that cannot run at all:

- a `--tool` path that only resolves from the example directory;
- an illustrative manifest that does not exist;
- two graphs that fail `GraphConfigSchema` yet pass `graph validate`;
- a `--var` that feeds a map from `data_files`, not state;
- the two known ones: innovation-matrix `domain` (FR-1088) and
  safety-guards (FR-1087).

These rows would have stayed hidden until someone ran a documented command
and read a stack trace. The frozen scope allowed only typo repairs, so
every other finding went to an FR (FR-1101) rather than into this diff.
The census shows the gap without widening the change.

## Heuristic and seed

**Heuristic:** when a boundary check breaks mocked tests, read the break as
evidence that the mocks encoded the defect. Do not weaken the check to fit
the mocks. Give each mock the contract the real object has. Tests that no
longer compile under a stated premise were leaning on an unstated one.

**Seed:** `graph validate` passed two graphs that the loader rejects. Should
`validate` load through the same `GraphConfigSchema` path as `graph run`, so
that "valid" means "loads"? If it did, the census's FINDING column would
shrink to what only running can reveal.
