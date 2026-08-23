# Task Brief: ramp_doctrine — target-tailored doctrine draft (FR-866)

**Prior art:** fr-866-ramp-rtm-brief.md and
fr-866-ramp-incidents-brief.md are sibling briefs of the same FR-866
contract, not precedent — the three graphs share the runtime contract
but derive disjoint artifacts (doctrine vs RTM vs incidents).

## Task

Author a yamlgraph demo graph that derives a target-repo `AGENTS.md`
**draft** by tailoring this repo's Scripture (traps, cures, questions)
to what the target actually does. Drafts only; landing in a target is a
human act (FR-867), never this graph's.

## Target

- Directory: `examples/demos/ramp_doctrine/`
- Artifacts: `graph.yaml`, `prompts/judge_entry.yaml`,
  `nodes/doctrine_tools.py`

## Contract

Graph vars: `target` (absolute path to target repo, required);
`source` (source repo path, default `.`).

Pipeline shape (shared FR-866 runtime contract):

1. Python collection node — deterministic, no LLM sees a directory
   listing it did not get from here. Calls
   `collect_doctrine(source)` and `collect_inventory(target)` from
   `nodes/doctrine_tools.py`.
2. **map** node — one LLM call per doctrine entry (~40 items), inline
   Pydantic schema = `DoctrineVerdict`. The prompt gives the entry
   (family, id, text) plus the target inventory and asks: does this
   entry apply to that repo? Verdicts: `applies` | `not` | `tailor`.
   `applies`/`tailor` require `target_evidence` citing target files;
   `not` requires a `reason`. The model must NEVER invent a new id.
3. Merge node — reconcile count-in == count-out, run
   `validate_draft(verdicts, source_items)`, render via
   `write_drafts(draft, base_dir=".")`.

### `nodes/doctrine_tools.py` module contract (tests import these
exact names — tests/unit/test_ramp_tailoring.py, already committed RED)

- `collect_doctrine(source_repo: str) -> list[dict]` — parse the
  Scripture knowledge-graph YAML block inside
  `.github/copilot-instructions.md` (the fenced ```yaml block with
  `traps:`, `cures:`, `questions:` keys). Return one dict per entry:
  `{"family": "trap"|"cure"|"question", "id": <yaml key>,
  "text": <yaml value>}`. Families exactly those three.
- `collect_inventory(target_repo: str) -> dict` with keys
  `languages`, `entry_points`, `effect_sites`, `gates`,
  `workflow_triggers` — each `list[str]` of repo-relative paths or
  names. `effect_sites`: files whose source contains network/API write
  markers (`urllib`, `requests`, `httpx`, `socket`, `subprocess`).
  `gates`: pre-commit config / CI test jobs found (empty list when
  none). `workflow_triggers`: workflow files with their trigger line
  (e.g. `.github/workflows/publish.yml: schedule`).
- `class DoctrineVerdict(BaseModel)` — fields: `family:
  Literal["trap","cure","question"]`, `id: str`, `verdict:
  Literal["applies","not","tailor"]`, `reason: str`,
  `target_evidence: str`.
- `validate_draft(verdicts: list[dict], source_items: list[dict]) ->
  list[str]` — returns error strings (empty = valid): any verdict id
  not present in source_items for its family ("invented id" —
  quote the id in the error); `applies`/`tailor` with empty
  `target_evidence`; `not` with empty `reason`.
- `EXAMPLE_DRAFT: dict` — a small representative draft payload used by
  tests to exercise `write_drafts`.
- `write_drafts(draft: dict, base_dir: str | Path) -> tuple[str, str]`
  — writes EXACTLY `<base_dir>/tmp/ramp/doctrine-draft.md` and
  `<base_dir>/tmp/ramp/doctrine-draft.json` (creating dirs), returns
  `(md_path, json_path)` as strings. No other file writes anywhere.
  The md renders one section per family, kept entries as strict
  subsets, witness citations emptied, and an explicitly blank
  "Local incidents" section for ramp_incidents to fill.

## Precedent

`examples/demos/fr-atlas/graph.yaml` (corpus map + merge +
count reconciliation; nodes/ module layout).

## Validation

- `yamlgraph graph lint examples/demos/ramp_doctrine/graph.yaml`
- `pytest tests/unit/test_ramp_tailoring.py -q --no-cov -k doctrine`
  (committed RED tests; fixture target at
  `tests/fixtures/ramp_target/`)

## Out of scope

Writing into any target repo; `git commit` / `git push` / `gh`
anywhere in graph, prompts, or nodes; new doctrine ids; smoke runs
against live siblings (operator-run, recorded in FR-866).
