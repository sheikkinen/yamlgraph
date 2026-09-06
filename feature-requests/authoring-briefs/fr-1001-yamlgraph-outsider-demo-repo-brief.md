# Authoring brief: FR-1001 `yamlgraph-outsider` standalone graph (copy of spike 2)

**Governing FR:** feature-requests/FR-1001-yamlgraph-outsider-demo-repo.md (judged APPROVED WITH REVISIONS 2026-09-05; scope frozen D-1…D-8)
**Prior art:** docs/spikes/outsider-llm-2026-09-05/graph.yaml and docs/spikes/outsider-llm-2026-09-05/prompts/outsider.yaml — the spike this graph COPIES (judgement C-2: copy via the route, do not reinvent). .github/skills/outsider-view/adapters/graph.yaml — the Copilot-route sibling; NOT the source here (different node type, pinned model).
**Target directory:** /Users/sheikki/Documents/src/yamlgraph-outsider/ — a SEPARATE Git repository (sibling of this one, its own Git root). Write there with absolute paths. Do not create anything under this repository except the one README line below.
**Artifacts to author:** `/Users/sheikki/Documents/src/yamlgraph-outsider/graph.yaml`, `/Users/sheikki/Documents/src/yamlgraph-outsider/prompts/outsider.yaml`, and ONE appended line in `.github/skills/outsider-view/adapters/README.md` (this repository).

## Task

Author the standalone graph and prompt by copying spike 2 and removing every
provider/model decision. Python already exists and is tested — do NOT author
or edit Python: `/Users/sheikki/Documents/src/yamlgraph-outsider/tools.py`
provides `fetch_pr` and `finalize` (validate → reduce → derive → render →
write → optionally post via `gh`). Do not edit `tests/`, `fixtures/`,
`yamlgraph-outsider`, `.env.sample`, or anything else there.

## Graph contract — `graph.yaml` (frozen by the FR-1001 judgement)

- `version: "1.0"`, `name: yamlgraph-outsider`, `prompts_relative: true`,
  `prompts_dir: prompts`. Header comment (3–5 lines): the reader gets the PR
  title and body and nothing else; the `llm` node has no tools; the graph
  names NO provider and NO model — both come from `.env` through yamlgraph's
  own resolution (`PROVIDER`, `<PROVIDER>_MODEL`).
- **No `defaults.provider`, no `defaults.model`, no `provider:`/`model:` on
  any node.** `defaults:` may carry only `temperature: 0.0`.
- State: `pr: str`, `repo: str`, `input_path: str`, `comment: str`,
  `report_path: str`, `pr_text: str`, `reading: dict`, `result: dict`.
  (No `provider`/`model`/`post` state keys — the spike had them; remove.)
- Tools (`type: python`, `path: tools.py`): `fetch_pr` → function `fetch_pr`;
  `finalize` → function `finalize`.
- Nodes and edge order (exact): `START → fetch_pr → outsider → finalize → END`.
- `fetch_pr`: python, tool `fetch_pr`, state_key `pr_text`, `on_error: fail`.
- `outsider`: `type: llm`, `prompt: outsider`, `temperature: 0.0`, variables
  `pr_text: "{state.pr_text}"`, state_key `reading`, `on_error: fail`.
- `finalize`: python, tool `finalize`, state_key `result`, `on_error: fail`.
  It reads `reading`, `pr_text`, `pr`, `repo`, `input_path`, `comment`,
  `report_path` from state.

## Prompt contract — `prompts/outsider.yaml`

Copy `docs/spikes/outsider-llm-2026-09-05/prompts/outsider.yaml` VERBATIM
except: replace the two header comment lines with two lines naming FR-1001
and the spike source. Keep the `schema:` block exactly (`OutsiderReading`;
`unclear` and `needs` are `type: str`, newline-delimited — `tools.py`
normalises them). Do not add project vocabulary, doctrine references, or any
instruction that tells the reader about any repository.

## README line — `.github/skills/outsider-view/adapters/README.md` (this repo)

Append exactly one line at the end of the file:

`Non-Copilot route (provider API, any model from .env): https://github.com/sheikkinen/yamlgraph-outsider (FR-1001).`

Change nothing else in that file.

## Validation the authoring run must perform

```bash
yamlgraph graph lint /Users/sheikki/Documents/src/yamlgraph-outsider/graph.yaml
```

```bash
cd /Users/sheikki/Documents/src/yamlgraph-outsider && test -f .env && yamlgraph graph run graph.yaml --var pr= --var repo= --var input_path=fixtures/positive.md --var comment=false --var report_path=out/authoring-smoke.md --full
```

The smoke needs `/Users/sheikki/Documents/src/yamlgraph-outsider/.env` with a
provider key (the human creates it; never write one). If `.env` is absent the
`test -f .env` guard fails: record the exact blocked command under "Blocked
validation" and stop — do not substitute a key, a provider, or a model. If it
runs, `out/authoring-smoke.md` must start with `**Derived verdict:**` and
contain the four `## N.` headings and the `### Set aside by the reducer` line.

Then confirm the deterministic tests still pass without touching them:

```bash
cd /Users/sheikki/Documents/src/yamlgraph-outsider && python -m pytest tests/test_boundary.py tests/test_gh_tools.py tests/test_wrapper.py -q
```
