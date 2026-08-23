# Task Brief: salvage_classify — scripture-dev disposition (FR-868)

**Prior art:** fr-866-ramp-{doctrine,rtm,incidents}-brief.md are
sibling ramp-family briefs, not precedent — they tailor governance
INTO a target; this graph classifies a stale source repo's assets FOR
retirement. FR-858 (fr-board retirement) is the nearest retirement
precedent but authored no graph. No REJECTED prior art occupies this
territory.

## Task

Author a yamlgraph demo graph that classifies every tracked file of a
frozen `scripture-dev` checkout against this repo's current
equivalents, emitting a human-review disposition draft. Verdicts:
`duplicate` (this repo already covers it — name the equivalent path),
`lift` (genuinely missing here and still correct — name a destination
under `ramp/salvage/<original-path>`), `obsolete` (dead by design). No
`unknown` verdicts; count-in == count-out over the manifest.

## Target

- Directory: `examples/demos/salvage_classify/`
- Artifacts: `graph.yaml`, `prompts/classify_asset.yaml`,
  `nodes/salvage_tools.py`

## Contract

Graph vars: `source_repo` (path to the scripture-dev checkout,
required); `source_sha` (frozen ref, required).

Pipeline shape: python collection node (`collect_manifest`) → **map**
node, one LLM call per file (file content + candidate equivalents from
this repo), inline Pydantic schema = `AssetClassification` → merge node
running `validate_disposition` and `write_drafts`.

### `nodes/salvage_tools.py` module contract (tests import these exact
names — tests/unit/test_salvage_classify.py, already committed RED)

- `collect_manifest(source_repo: str) -> list[str]` — `git -C
  <source_repo> ls-files` posix paths; read-only.
- `class AssetClassification(BaseModel)` — fields: `path: str`,
  `category: str`, `verdict:
  Literal["duplicate","lift","obsolete"]`, `rationale: str`
  (min_length=1), `yamlgraph_equivalent: str | None = None`,
  `target_path: str | None = None`.
- `class SalvageDisposition(BaseModel)` — fields: `source_repo: str`,
  `source_sha: str` (min_length=7), `manifest_count: int`, `items:
  list[AssetClassification]`.
- `validate_disposition(disposition: dict, manifest: list[str],
  repo_root) -> list[str]` — error strings for: count-in != count-out
  (name every manifest path missing a verdict); any `duplicate` whose
  `yamlgraph_equivalent` is None or does not exist under `repo_root`
  (quote the path); any `lift` whose `target_path` is None or does not
  start with `ramp/salvage/`.
- `write_drafts(disposition: dict, base_dir=".") -> dict` writing
  EXACTLY `<base_dir>/tmp/ramp/salvage-disposition.md` and `.json`,
  nothing else; returns `{"markdown": ..., "json": ...}`. The md
  groups items by verdict with rationales and ends with a
  reconciliation section (manifest count vs classified count).

## Precedent

`examples/demos/ramp_incidents/graph.yaml` — collection → map → merge
topology with count reconciliation. Do NOT copy its prompts or schema.

## Validation

- `yamlgraph graph lint examples/demos/salvage_classify/graph.yaml`
- `pytest tests/unit/test_salvage_classify.py -q --no-cov`

## Out of scope

Any write outside `tmp/ramp/`; `git commit` / `git push` / `gh` in any
source; actually lifting files (a human act after raw-output read);
archiving the source repo (hard-gated on written human approval,
FR-868 AC-16).
