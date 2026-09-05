# Authoring brief: FR-995 outsider-view adapter graph (copy of the spike)

**Governing FR:** feature-requests/FR-995-outsider-reader.md (judged APPROVED WITH REVISIONS 2026-09-05; scope frozen D-1…D-10)
**Prior art:** docs/spikes/outsider-reader-2026-09-05/graph.yaml and prompts/outsider.yaml — the spike this graph COPIES (judgement C-2: copy via the route, do not reinvent); .github/skills/judge-fr/adapters/graph.yaml and .github/skills/review-pr/adapters/graph.yaml — sibling thin adapters (copilot node, literal model pin); their prompts are pointer prompts to a doctrine file, which this one is NOT (the reader must see no doctrine).
**Target directory:** .github/skills/outsider-view/adapters/
**Artifacts to author:** `graph.yaml`, `prompts/outsider.yaml`, `README.md`

## Task

Author the production adapter for the outsider reader by copying the spike
graph and prompt, then adding the typed finalize step. Python already exists
— do NOT author or edit Python: `.github/skills/outsider-view/adapters/outsider_tools.py`
provides `read_input` and `finalize_report` (parse → derive verdict → write
report; fails closed on malformed model output).

## Graph contract (frozen by the FR-995 judgement)

- `version: "1.0"`, `name: outsider-view-adapter`, `prompts_relative: true`,
  `prompts_dir: prompts`. Header comment: the reader runs from a directory
  OUTSIDE the repo (the wrapper does this) and must have no file or tool
  access; a reader who can open the files is not an outsider.
- State: `input_path: str`, `report_path: str`, `model: str`, `pr_text: str`,
  `outsider_result: dict`, `report: dict`.
- Tools (`type: python`, `path: outsider_tools.py`): `read_input` →
  `read_input`; `finalize_report` → `finalize_report`.
- Nodes and edge order (exact): `START → read_input → outsider → finalize_report → END`.
- `read_input`: python, tool `read_input`, state_key `pr_text`, `on_error: fail`.
- `outsider`: `type: copilot`, `backend: cli`, `cli_flags: {model: gpt-5.6-sol}`
  — the model is pinned LITERALLY (cli_flags are not templated; the spike
  proved `{state.model}` fails) and there must be NO `allow_all_paths` and NO
  `allow_all_tools` anywhere in the file. `prompt: outsider`, variables
  `pr_text: "{state.pr_text}"`, state_key `outsider_result`, `timeout: 600`,
  `on_error: fail`.
- `finalize_report`: python, tool `finalize_report`, state_key `report`,
  `on_error: fail`. It reads `outsider_result`, `report_path`, `model`,
  `input_path` from state.

## Prompt contract — `prompts/outsider.yaml`

Copy `docs/spikes/outsider-reader-2026-09-05/prompts/outsider.yaml` (the v2
prompt) VERBATIM except for adding a two-line header comment naming FR-995 and
the spike source. Do not add project vocabulary, doctrine references, or any
instruction that tells the reader about this repository. The four section
headings must stay byte-identical to the spike's — the typed parser matches
them exactly:

```
## 1. In my own words
## 2. Could I decide whether to merge this from the description alone?
## 3. Words and references I could not understand
## 4. What a merge decision would still need
```

## README contract — `adapters/README.md`

Operational, doctrine-free, in the shape of `.github/skills/review-pr/adapters/README.md`.
Must state: the sole manual command (`scripts/outsider.sh <pr-number>
[--comment]`, plus `--input`, `--selftest`, `--dry-run`); input closure (PR
title + body only; child cwd outside the repo; no path/tool grants); the
artifact path (`tmp/outsider-<label>-<stamp>.md`, verified by content, never
exit code); the distinction between the **derived verdict** (first line,
computed in code) and the model's section-2 opinion (non-authoritative);
advisory status; forbidden actions (no auto-invocation, no gate, no comment
without `--comment`, no FR-body input, no edits to the spike outputs); and a
pointer to `docs/spikes/outsider-reader-2026-09-05/` as the source copy.

## Validation the authoring run must perform

- `yamlgraph graph lint .github/skills/outsider-view/adapters/graph.yaml`
- Smoke, run from a clean directory exactly as the wrapper does:

```bash
cd "$(mktemp -d)" && OUTSIDER_EXECUTION=1 yamlgraph graph run /Users/sheikki/Documents/src/yamlgraph/tmp/worktrees/feat/outsider-reader/.github/skills/outsider-view/adapters/graph.yaml --var input_path=/Users/sheikki/Documents/src/yamlgraph/tmp/worktrees/feat/outsider-reader/docs/spikes/outsider-reader-2026-09-05/inputs/pr-591-v2.md --var report_path=/Users/sheikki/Documents/src/yamlgraph/tmp/worktrees/feat/outsider-reader/tmp/outsider-smoke.md --var model=gpt-5.6-sol --full
```

The smoke creates the output `tmp/outsider-smoke.md`; its first line must
begin `**Derived verdict:**` and it must contain all four headings. If the
model call is blocked, record the blocked command honestly.
