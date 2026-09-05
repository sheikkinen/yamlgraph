# Authoring brief: FR-1004 outsider-view adapter — base observation fields in graph state

**Governing FR:** feature-requests/FR-1004-retire-outsider-ledger.md (judged APPROVED WITH REVISIONS 2026-09-05; deliverable D-4, revision R-3)
**Prior art:** .github/skills/outsider-view/adapters/graph.yaml — the committed artifact being modified in place (authored for FR-995 via feature-requests/authoring-briefs/fr-995-outsider-reader-brief.md). Sibling thin adapters: .github/skills/judge-fr/adapters/graph.yaml, .github/skills/review-pr/adapters/graph.yaml.
**Target directory:** .github/skills/outsider-view/adapters/
**Artifacts to author:** `graph.yaml` — modify in place; this is the ONLY file to change.

## Task

Extend the typed state of the outsider-view adapter graph with five string
fields so the wrapper (`scripts/outsider.sh`) can pass the *base observation*
of a run into the graph, where the Python tool `finalize_report` builds the
typed observation marker (FR-1004 S-3). The Python already consumes the new
state — `.github/skills/outsider-view/adapters/outsider_tools.py` reads
`repo`, `pr`, `head_sha`, `prompt_digest`, `tool_sha` and `model` from state.

Do NOT edit `outsider_tools.py`, `prompts/outsider.yaml`, `README.md`,
`scripts/outsider.sh`, or any test. Do not author any new file.

## Graph contract (frozen)

Everything in `graph.yaml` stays byte-identical except the `state:` block:
header comment, `version`, `name`, `prompts_relative`, `prompts_dir`, the
`tools:` block, every node (types, `cli_flags: {model: gpt-5.6-sol}` pinned
literally, `timeout: 600`, `on_error: fail`), and the edge list
`START → read_input → outsider → finalize_report → END`. There must still be
NO `allow_all_paths` and NO `allow_all_tools` anywhere in the file.

The `state:` block becomes exactly (order matters — existing inputs, then the
five new base observation fields, then the derived keys):

```yaml
state:
  input_path: str
  report_path: str
  model: str
  # FR-1004: base observation fields; finalize_report builds the typed marker from them.
  repo: str
  pr: str
  head_sha: str
  prompt_digest: str
  tool_sha: str
  pr_text: str
  outsider_result: dict
  report: dict
```

## Validation the authoring run must perform

- `yamlgraph graph lint .github/skills/outsider-view/adapters/graph.yaml`
- One smoke with the placeholder values a non-PR run passes (the wrapper itself
  additionally runs from a clean directory outside the repo; the wrapper's own
  `--selftest` is the operator's evidence for that property):

```bash
OUTSIDER_EXECUTION=1 yamlgraph graph run .github/skills/outsider-view/adapters/graph.yaml --var input_path=.github/skills/outsider-view/fixtures/pr-591-v2.md --var report_path=tmp/outsider-fr1004-smoke.md --var model=gpt-5.6-sol --var repo=- --var pr=- --var head_sha=- --var prompt_digest=0000000000000000 --var tool_sha=smoke --full  # writes the smoke output report
```

The smoke must write the output `tmp/outsider-fr1004-smoke.md`; its first line
begins `**Derived verdict:**`; its second line begins `<!-- outsider reader | ts: `
and contains `| repo: - | pr: - | head: - |`; all four section headings are
present. If the model call is blocked, record the exact blocked command and
the reason honestly — never claim the smoke passed.
