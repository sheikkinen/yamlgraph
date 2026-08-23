# Task Brief: ramp_rtm — requirement candidates from test inventory (FR-866)

**Prior art:** fr-866-ramp-doctrine-brief.md and
fr-866-ramp-incidents-brief.md are sibling briefs of the same FR-866
contract, not precedent — the three graphs share the runtime contract
but derive disjoint artifacts (doctrine vs RTM vs incidents).

## Task

Author a yamlgraph demo graph that derives a **proposed** requirement
registry draft for a target repo from its existing test suite. Reverse
traceability: every requirement candidate must cite the witness tests
that motivated it. Low counts are reported honestly, never padded — an
insufficiency finding ("N tests support only M requirement candidates")
is a valid, successful output.

## Target

- Directory: `examples/demos/ramp_rtm/`
- Artifacts: `graph.yaml`, `prompts/derive_reqs.yaml`,
  `nodes/rtm_tools.py`

## Contract

Graph vars: `target` (absolute path, required); `source` (default `.`).

Pipeline shape: python collection node (`collect_tests(target)`) →
**map** node over test files, one LLM call per file, inline Pydantic
schema producing `RtmEntry` items → merge node running
`validate_rtm` + `gap_tests` and `write_drafts`.

### `nodes/rtm_tools.py` module contract (tests import these exact
names — tests/unit/test_ramp_tailoring.py, already committed RED)

- `collect_tests(target_repo: str) -> list[dict]` — walk
  `tests/**/test_*.py` in the target, parse with `ast`, return one dict
  per file: `{"path": <target-relative posix path>,
  "tests": [<function names starting test_>],
  "source": <file text>}`.
- `class RtmEntry(BaseModel)` — fields: `req_id: str`,
  `statement: str`, `witness_tests: list[str]`,
  `confidence: float`, `status: Literal["proposed"]`.
  The Literal makes any other status a ValidationError.
- `validate_rtm(entries: list[dict], inventory: list[dict]) ->
  list[str]` — error strings for: any witness test name not present in
  the inventory (quote the name); empty `witness_tests`; status other
  than `proposed`.
- `gap_tests(entries: list[dict], inventory: list[dict]) -> list[str]`
  — test names in the inventory witnessed by no entry (the honest gap
  list, rendered in the draft).
- `EXAMPLE_DRAFT: dict` and
  `write_drafts(draft, base_dir) -> tuple[str, str]` writing EXACTLY
  `<base_dir>/tmp/ramp/rtm-draft.md` and `.json`, nothing else.
  The md includes the gap list and, when candidate count is low, an
  explicit insufficiency finding instead of padded requirements.

Requirement id namespace in prompts: neutral `REQ-XXX-NNN`
placeholder; FR-867 assigns the real namespace (e.g. REQ-DD) at
landing time — the graph must not hardcode a repo-specific prefix.

## Precedent

`examples/demos/fr-atlas/` (map over corpus, merge with
reconciliation); `scripts/req_coverage.py` (ast-based test-mark
collection pattern).

## Validation

- `yamlgraph graph lint examples/demos/ramp_rtm/graph.yaml`
- `pytest tests/unit/test_ramp_tailoring.py -q --no-cov -k rtm`
  (fixture target: `tests/fixtures/ramp_target/` — 2 test files,
  5 test functions)

## Out of scope

Assigning final REQ ids or status beyond `proposed`; writing into the
target; `git commit` / `git push` / `gh` in any source; padding
requirements to hit a count.
