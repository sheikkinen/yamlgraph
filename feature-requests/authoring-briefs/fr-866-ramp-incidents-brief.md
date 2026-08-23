# Task Brief: ramp_incidents — incident repatriation from source corpus (FR-866)

**Prior art:** fr-866-ramp-doctrine-brief.md and
fr-866-ramp-rtm-brief.md are sibling briefs of the same FR-866
contract, not precedent — the three graphs share the runtime contract
but derive disjoint artifacts (doctrine vs RTM vs incidents).

## Task

Author a yamlgraph demo graph that scans THIS repo's FR and diary
corpus for documents mentioning a target repo and classifies each as an
incident record belonging to that target, or `not_an_incident`.
Incidents paid for in the source repo's history are repatriated as a
draft the target's doctrine can cite. Reuses the fr-atlas corpus-map
TOPOLOGY but NOT its prompts or schema (FR-866 AC-14: this decision is
recorded — atlas classifies FR lifecycle, this classifies operational
incidents; the schemas share no fields).

## Target

- Directory: `examples/demos/ramp_incidents/`
- Artifacts: `graph.yaml`, `prompts/classify_incident.yaml`,
  `nodes/incident_tools.py`

## Contract

Graph vars: `target_name` (mention token, e.g. `deviant-daily`,
required); `source` (source repo path, default `.`).

Pipeline shape: python collection node (`collect_corpus`) → **map**
node, one LLM call per document, inline Pydantic schema =
`IncidentClassification` → merge node running `validate_disposition`
and `write_drafts`.

### `nodes/incident_tools.py` module contract (tests import these
exact names — tests/unit/test_ramp_tailoring.py, already committed RED)

- `collect_corpus(source_repo: str, target_name: str) -> list[str]` —
  repo-relative posix paths of files under `feature-requests/` and
  `docs/diary/` whose text contains `target_name`. Mentions only; no
  fuzzy matching.
- `class IncidentClassification(BaseModel)` — fields: `verdict:
  Literal["incident","not_an_incident"]`, and optional-with-default
  `path: str = ""`, `date: str = ""`, `defect: str = ""`,
  `root_cause: str = ""`, `cure: str = ""`, `witness: str = ""`,
  `source_ref: str = ""`. A model validator enforces: when verdict is
  `incident`, ALL of date/defect/root_cause/cure/witness/source_ref
  must be non-empty (raise ValidationError otherwise);
  `not_an_incident` requires nothing further.
- `validate_disposition(classifications: list[dict], corpus:
  list[str], source_repo: str) -> list[str]` — error strings for:
  count-in != count-out (name every corpus path missing a
  classification); any `incident` whose `source_ref` does not resolve
  to an existing file under `source_repo` (quote the ref).
- `EXAMPLE_DRAFT: dict` and
  `write_drafts(draft, base_dir) -> tuple[str, str]` writing EXACTLY
  `<base_dir>/tmp/ramp/incidents-draft.md` and `.json`, nothing else.
  The md groups incidents chronologically with source_ref citations
  and lists not_an_incident paths in a final reconciliation section.

## Precedent

`examples/demos/fr-atlas/graph.yaml` — topology only (corpus map +
merge + count reconciliation). Do NOT copy its prompts or schema.

## Validation

- `yamlgraph graph lint examples/demos/ramp_incidents/graph.yaml`
- `pytest tests/unit/test_ramp_tailoring.py -q --no-cov -k incident`
  (corpus test asserts FR-863 is found for token `deviant-daily`)

## Out of scope

Writing into any target repo; `git commit` / `git push` / `gh` in any
source; fuzzy/semantic corpus matching; classifying documents outside
feature-requests/ and docs/diary/.
