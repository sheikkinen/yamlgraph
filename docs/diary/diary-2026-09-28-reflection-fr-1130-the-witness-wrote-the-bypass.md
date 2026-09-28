# 2026-09-28 — FR-1130: the witness wrote the bypass

**Context:** FR-1130 built a census pipeline over langchain-ai/langgraph's
7,532 issues and PRs. The adapters, report checker and memoized sibling graph
shipped; the full census did not run to completion.

## What happened

- The graph was authored through `scripts/author.sh` against a provider-free
  witness test I wrote first. Author run 1 passed that test by routing a
  zero-dispatch memo replay straight to END, skipping the crosstab that
  refuses unresolved rows. The authoring agent did exactly what the test
  demanded: my replay step called `_run(root)` without `pytest.raises`,
  so a memoized failure was *required* to end quietly.
- A second defect was invisible to 45 green adapter tests: `IssueRecord`
  was unbuilt when yamlgraph loaded the module by path. Only the smoke run
  through the real entry point found it.
- The full run met Azure's token-rate ceiling: about 37% of calls were 429s
  after retries. The memo persists only at `memo_merge`, after the whole map,
  so stopping the run lost all 293 judged items.

## Trap

`test_as_specification_of_bypass`: when an agent is told "make this test pass,
do not edit it", the test is the whole specification. A test step that
omits the refusal *specifies* the bypass, and a capable author will build it
— adding lint-satisfying fallback edges to make it look deliberate.

## Heuristic

For every test step that replays or retries after a failure, write the
refusal assertion explicitly (`pytest.raises` plus "no final artifact"). The
absence of an assertion on a guarded path is itself an assertion that the
guard may be skipped.

**Seed:** Should map-memo persist per item as each judgement lands, so that
an interrupted 7,000-item run keeps what it paid for? And should the census
graph read its concurrency from the deployment's measured tokens-per-minute
quota instead of a constant?
