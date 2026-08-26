# Task Brief: research-route — closed-input alternatives graph (FR-890)

**Prior art:** `examples/demos/session-shapes` (FR-884 pinned-model
classifier + deterministic reduce) is the architecture precedent;
`examples/demos/web-research` (FR-780) supplies the reused `search_web`
tool; `examples/demos/innovation_matrix` is the never-fired ideation
sibling this route operationalizes; `examples/demos/fan-out` shows
parallel node fan-out. No REJECTED prior art occupies this territory
(FR-890 judgement dispositions).

## Task

Author a yamlgraph demo graph that fans a CLOSED problem brief out to
five planner personas with orthogonal priors — each receiving ONLY the
brief's fields, never any draft solution (FR-890 C-3) — and reduces
their findings into a dispositioned alternatives table via LLM-free
code. The reduce fails closed; disagreement between personas is
preserved as separate rows, never voted away.

## Target

- Directory: `examples/demos/research-route/`
- Artifacts: `graph.yaml`, `prompts/*.yaml` (one per persona plus a
  librarian structuring step), `nodes/research_tools.py`

## Contract

Graph var: `brief_path` (path to a preflighted problem brief, required).

All LLM nodes pin a cheap model: `defaults: provider: anthropic, model:
claude-haiku-4-5, temperature: 0.0` (FR-890 AC-01).

Pipeline shape: python node `load_brief` → python node
`collect_graph_shapes` → parallel fan-out of five persona nodes → glue
→ python reduce node writing `tmp/draft-alternatives.md`.

### Personas (one finding each, orthogonal priors)

1. **os-infra-primitivist** (llm): what does the platform/OS/kernel
   already enforce? Prefers permissions, filesystem, process boundaries.
2. **data-process-planner** (llm): what schema or process change
   dissolves the problem instead of guarding it?
3. **yamlgraph-native-planner** (llm): receives the collected graph
   shape descriptions as a variable and MUST record an `is_this_a_graph`
   answer naming the matching graph shape or saying none (FR-890 AC-04).
4. **subtractionist** (llm): can the requirement be deleted? The
   growth_as_default check.
5. **librarian** (agent with `search_web` from
   `examples.shared.websearch`, max_iterations 4): how has the world
   solved this problem class? Followed by an llm structuring node that
   MUST copy a real result URL into the `precedent` field — an
   `Error:`/`No results` string is a failure, not a citation (AC-05).

Each persona prompt receives only: `problem_statement`,
`classification`, `constraints`, `witnessed_incidents` (the
yamlgraph-native planner additionally receives `graph_shapes`). Inline
Pydantic schema per persona output with exactly these fields: `persona`,
`candidate`, `solution_class`, `verdict`, `precedent`,
`is_this_a_graph`, `effort_risk` — all non-empty strings.

### `nodes/research_tools.py` module contract (tests import these exact
names — tests/unit/test_fr890_research_route.py, already committed RED)

- `load_brief(brief_path: str) -> dict` — parses the brief's four
  sections into keys `problem_statement`, `classification`,
  `constraints`, `witnessed_incidents` (non-empty strings).
- `collect_graph_shapes(demos_dir: str = "examples/demos") -> str` —
  one line per demo graph: name plus description read from each
  `graph.yaml`; must include the map demo.
- `class PersonaFinding(BaseModel)` — fields `persona`, `candidate`,
  `solution_class`, `verdict`, `precedent`, `is_this_a_graph`,
  `effort_risk`: all `str` with `min_length=1`.
- `reduce_findings(findings: list[dict], brief_path: str, base_dir:
  str = ".") -> dict` — LLM-free. Validates every finding through
  `PersonaFinding`; raises `ValueError` naming the defect when: any
  required cell is empty; a `librarian` persona's `precedent` contains
  `Error:` or `No results` (message must contain "librarian") or lacks
  an `http(s)://` URL (message must contain "URL"); the count of
  distinct `solution_class` values is outside 4-6 (message must contain
  "class"). Never merges or dedupes rows: the artifact row count equals
  `len(findings)`. Writes EXACTLY `<base_dir>/tmp/draft-alternatives.md`
  with a metadata header (brief filename, run date, personas executed)
  and a markdown table with columns, in order: `candidate`, `persona`,
  `class`, `verdict`, `precedent`, `is_this_a_graph`, `effort-risk`.
  Returns `{"artifact": <path>, "rows": <int>, "classes": <int>}`.
- A glue function gathering the five persona state outputs into the
  findings list may be added to the same module if the wiring needs it.

## Precedent

`examples/demos/session-shapes/graph.yaml` — pinned haiku classifier +
deterministic aggregate tool. `examples/demos/web-research/graph.yaml`
— agent node with `search_web`. Do NOT copy their prompts.

## Validation

```bash
yamlgraph graph lint examples/demos/research-route/graph.yaml
python -m pytest tests/unit/test_fr890_research_route.py -q --no-cov
yamlgraph graph run examples/demos/research-route/graph.yaml --var brief_path=tests/fixtures/fr890/clean-brief.md  # writes tmp/draft-alternatives.md
```

The smoke run's artifact must pass
`python scripts/research_preflight.py --verify-artifact tmp/draft-alternatives.md`.

## Out of scope

Any write outside `tmp/`; `scripts/research.sh` and
`scripts/research_preflight.py` (wrapper code, exists already); judge
doctrine or template edits; `git commit`/`git push` in any form; passing
any draft solution or candidate list into persona prompts (FR-890 C-3).
