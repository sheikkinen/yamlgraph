# Authoring brief: FR-1027 org_ai_dossier graph (GitHub + Jira census, pinned Azure)

**Governing FR:** feature-requests/FR-1027-org-ai-dossier-census.md (judged APPROVED WITH REVISIONS; R-1..R-8 folded; scope frozen — § Frozen topology is the contract this brief transcribes)
**Prior art:** fr-899-repo-census-brief.md (sibling: preflight-first, Azure-pinned, FR-892 slots) and fr-892-corpus-census-brief.md (base pipeline) — this graph deliberately mirrors both; fr-896-pattern-model-census-brief.md and cap-journey-census-brief.md — sibling censuses with hidden canaries the reducer checks (canary discipline reused). None of them has two sources or a person stage; this is the first.
**Target directory:** examples/demos/org_ai_dossier/
**Artifacts to author:** `graph.yaml`, `prompts/classify_repo_ai.yaml`, `prompts/classify_jira_ai.yaml`, `prompts/summarize_person.yaml`, `prompts/synthesize_findings.yaml`, `prompts/synthesize_onepager.yaml`, `preflight.tool.yaml`, `smoke_preflight.tool.yaml`, `README.md`

## Task

Author the FR-1027 org AI dossier graph: a sibling of
`examples/demos/repo_census/graph.yaml` with a frozen TWO-source topology
(GitHub active repositories, then Jira active projects), hidden canaries
injected between extraction and classification, a typed LLM-free reducer, an
optional (policy-gated) person-summary map, two bounded Azure synthesis
judgements, and one atomic artifact writer.

Python already exists — do NOT author or edit Python. Everything the graph
needs is in `examples/demos/org_ai_dossier/tools.py` (module path
`examples.demos.org_ai_dossier.tools`): `preflight`, `preflight_smoke`,
`coverage_gh`, `inject_repo_canaries`, `inject_jira_canaries`, `reduce`,
`prepare_person_input`, `prepare_findings_input`, `render_artifacts`.
Adapters for the slots live in `examples/demos/corpus_census/adapters/`
(manifests `gh-org-active-discover.tool.yaml`, `gh-repo-ai-extract.tool.yaml`,
`gh-org-code-search.tool.yaml`, `jira-active-discover.tool.yaml`,
`jira-project-extract.tool.yaml`, `jira-coverage.tool.yaml`, and the smoke
fixtures `jira-fixture-discover.tool.yaml`, `jira-fixture-extract.tool.yaml`,
`jira-fixture-coverage.tool.yaml`). Canary bundles
live in `canaries.py`; the model must never see their expected answers.

## Graph contract (exact — FR § Frozen topology)

- `version: "1.0"`, `name: org-ai-dossier`, `prompts_relative: true`,
  `prompts_dir: prompts`.
- `defaults: {provider: azure, temperature: 0.0}`. EVERY `type: llm` node
  ALSO carries `provider: azure` and `temperature: 0` explicitly (judgement
  C-4: no inherited or fallback provider). No `model:` key anywhere — the
  Azure deployment comes from `AZURE_MODEL` env via the factory.
- `config: {max_map_items: 400, max_concurrency: 4, timeout: 5400}`.
- State keys (exact):
  `org: str`, `visibility: str`, `window_days: str`, `top_persons: str`,
  `persons_llm: str`, `persons_llm_ack: str`, `out_dir: str`,
  `preflight_ok: bool`, `coverage_gh: dict`, `api_calls_estimated: int`,
  `llm_calls_estimated: int`, `run_started: str`,
  `repo_items: list`, `repo_bundles: list (reducer sorted_add)`,
  `search_hits: dict`, `repo_findings: list (reducer sorted_add)`,
  `coverage_jira: dict`, `jira_items: list`,
  `jira_bundles: list (reducer sorted_add)`,
  `jira_findings: list (reducer sorted_add)`, `reduced: dict`,
  `person_input: list`, `persons_llm_active: bool`,
  `person_summaries: list (reducer sorted_add)`, `findings_input: dict`,
  `findings_claims: dict`, `onepager_claims: dict`, `artifacts: dict`.
- Tools:
  - Slots (`slot: true`, FR-892): `preflight` (contract args: none),
    `gh_discover` (args `[source, visibility]`), `gh_extract` (args `[item]`),
    `gh_search` (args `[org]`), `jira_coverage` (args `[source]`),
    `jira_discover` (args `[source]`), `jira_extract` (args `[item]`).
  - Local python tools, all `type: python`,
    `module: examples.demos.org_ai_dossier.tools`: `coverage_gh`,
    `inject_repo_canaries`, `inject_jira_canaries`, `reduce`,
    `prepare_person_input`, `prepare_findings_input`, `render_artifacts`
    (function name == tool name). One-line `description:` each.
- Nodes and edge order (exact; every python node `on_error: fail`):
  `START → preflight → coverage_gh → gh_discover → gh_extract_items →
  inject_repo_canaries → gh_search → classify_repos → coverage_jira →
  jira_discover → jira_extract_items → inject_jira_canaries → classify_jira →
  reduce → prepare_person_input → [conditional] → summarize_persons |
  prepare_findings_input → synthesize_findings → synthesize_onepager →
  render_artifacts → END`
  - `preflight`: python, tool `preflight`, state_key `preflight_ok`.
  - `coverage_gh`: python, tool `coverage_gh` (returns a dict merged into
    state: `coverage_gh`, `api_calls_estimated`, `llm_calls_estimated`,
    `run_started`) — no state_key.
  - `gh_discover`: python, tool `gh_discover`, variables
    `source: "{state.org}:{state.window_days}"`,
    `visibility: "{state.visibility}"`, state_key `repo_items`.
  - `gh_extract_items`: `type: map`, `over: "{state.repo_items}"`,
    `as: item`, `max_items: 400`, sub-node python tool `gh_extract`,
    state_key `content`, `on_error: fail`, `collect: repo_bundles`.
  - `inject_repo_canaries`: python, tool `inject_repo_canaries` (returns
    `{repo_bundles: [...]}` which the `sorted_add` reducer appends) — no
    state_key.
  - `gh_search`: python, tool `gh_search`, variables `org: "{state.org}"`
    (returns `{search_hits: ...}`) — no state_key.
  - `classify_repos`: `type: map`, `over: "{state.repo_bundles}"`,
    `as: judged`, `max_items: 405` (400 + 3 canaries + margin), sub-node
    `type: llm`, `prompt: classify_repo_ai`, `provider: azure`,
    `temperature: 0`, `on_error: skip`, state_key `finding`,
    variables `content: "{state.judged.value}"`,
    `source_index: "{state.judged._map_index}"`, `collect: repo_findings`.
  - `coverage_jira`: python, tool `jira_coverage`, variables
    `source: "{state.window_days}"` (returns `{coverage_jira: ...}`) — no
    state_key.
  - `jira_discover`: python, tool `jira_discover`, variables
    `source: "{state.window_days}"`, state_key `jira_items`.
  - `jira_extract_items`: `type: map`, `over: "{state.jira_items}"`,
    `as: item`, `max_items: 150`, sub-node python tool `jira_extract`,
    state_key `content`, `on_error: fail`, `collect: jira_bundles`.
  - `inject_jira_canaries`: python, tool `inject_jira_canaries` — no
    state_key.
  - `classify_jira`: `type: map`, `over: "{state.jira_bundles}"`,
    `as: judged`, `max_items: 155`, sub-node `type: llm`,
    `prompt: classify_jira_ai`, `provider: azure`, `temperature: 0`,
    `on_error: skip`, state_key `finding`, variables
    `content: "{state.judged.value}"`,
    `source_index: "{state.judged._map_index}"`, `collect: jira_findings`.
  - `reduce`: python, tool `reduce` (returns `{reduced: ...}`) — no
    state_key.
  - `prepare_person_input`: python, tool `prepare_person_input` (returns
    `{person_input, persons_llm_active}`) — no state_key.
  - Conditional edges from `prepare_person_input`:
    `condition: "persons_llm_active == true"` → `summarize_persons`;
    `condition: "persons_llm_active != true"` → `prepare_findings_input`.
  - `summarize_persons`: `type: map`, `over: "{state.person_input}"`,
    `as: person`, `max_items: 60`, sub-node `type: llm`,
    `prompt: summarize_person`, `provider: azure`, `temperature: 0`,
    `on_error: fail`, state_key `summary_out`, variables
    `person: "{state.person.value}"`,
    `source_index: "{state.person._map_index}"`,
    `collect: person_summaries`. Edge `summarize_persons →
    prepare_findings_input`.
  - `prepare_findings_input`: python, tool `prepare_findings_input`
    (returns `{reduced, findings_input}`) — no state_key.
  - `synthesize_findings`: `type: llm`, `prompt: synthesize_findings`,
    `provider: azure`, `temperature: 0`, state_key `findings_claims`,
    variables `rows: "{state.findings_input.rows}"`,
    `coverage: "{state.findings_input.coverage}"`,
    `tools: "{state.findings_input.ai_tools}"`.
  - `synthesize_onepager`: `type: llm`, `prompt: synthesize_onepager`,
    `provider: azure`, `temperature: 0`, state_key `onepager_claims`,
    same variables.
  - `render_artifacts`: python, tool `render_artifacts` (returns
    `{artifacts: ...}`) — no state_key. Edge `render_artifacts → END`.

## Prompt contracts (one judgement per call; input-closed; schema-validated)

All five prompts: system + user + `schema:`; Jinja templating; NO mention of
canaries, expected answers, other units, aggregates, or rankings.

- `classify_repo_ai.yaml` — system: classify ONE repository's AI usage from
  a JSON evidence bundle (metadata, README head, contributor logins,
  instruction-file presence, manifest/workflow lines that matched an AI
  vocabulary, PR authors). Use ONLY the bundle. `product` = the shipped
  software calls an AI/LLM provider or framework; `dev_tooling` = the team
  uses AI coding tools (instruction files, Copilot/AI workflows, bot PR
  authors); `both`; `none`; `unclear` when the bundle hints at AI (e.g. a
  README phrase) without a citable manifest/instruction/workflow line.
  Every tool MUST cite `evidence_path` copied verbatim from a bundle
  `manifest_hits[].path`, `workflow_hits[].path`, or `instruction_files[]`
  entry — a tool without such a path must be omitted. User: `Evidence
  bundle: {{ content }}`, `Source index: {{ source_index }}`. Schema
  `RepoAIClassification` fields (all required): `source_index: int`,
  `purpose: str` (one sentence, what it does and for whom),
  `ai_usage: str` (exactly one of none|product|dev_tooling|both|unclear),
  `ai_tools: list[dict]` (each `{name, kind, evidence_path}`; `kind` one of
  provider|framework|coding_agent|model), `rationale: str` (one sentence).
- `classify_jira_ai.yaml` — same shape for ONE Jira project bundle (project
  meta, counts, ≤30 recent issues with summaries/status/short description,
  `ai_term_count`). Evidence is `evidence_issue`, an issue `key` copied
  verbatim from the bundle's `issues[]`. Schema `JiraAIClassification`:
  `source_index`, `purpose`, `ai_usage`, `ai_tools: list[dict]`
  (`{name, kind, evidence_issue}`), `rationale`.
- `summarize_person.yaml` — system: write a 2–3 sentence professional
  contribution summary for ONE person from ONE source-qualified footprint
  (`id`, `label`, `source`, `score`, `footprint: [{id, purpose}]`). Mention
  only units in the footprint. FORBIDDEN (state explicitly): seniority,
  performance, workload, sentiment, intent, comparisons with other people,
  any other person's name or id, any claim about who this person is on the
  other system. User: `Footprint: {{ person }}`, `Source index:
  {{ source_index }}`. Schema `PersonSummary`: `source_index: int`,
  `summary: str`.
- `synthesize_findings.yaml` — system: from a bounded table of rows
  (`item_ref`, `judgement`, `label`, `entries`), a coverage record, and an
  AI-tool table, return 3–8 findings about the organisation's AI use. Every
  claim cites only `row:<item_ref>` or `label:<label>` values present in
  the rows. Never invent units, tools, or people. User: `Rows: {{ rows }}`,
  `Coverage: {{ coverage }}`, `AI tools: {{ tools }}`. Schema
  `DossierFindings`: `claims: list[dict]` — each `{claim_id: str, text: str,
  citations: list[str], confidence: float}`.
- `synthesize_onepager.yaml` — same inputs; return EXACTLY three claims —
  the three findings a manager must know (activity, AI adoption, tools /
  where the work is) — each ≤ 40 words, cited the same way. Schema
  `OnepagerFindings`: `claims: list[dict]` (same element shape). State in
  the system prompt that exactly three claims are required.

## Tool manifests

- `preflight.tool.yaml`: `name: preflight`, `runtime: {type: python,
  path: tools.py, function: preflight}`.
- `smoke_preflight.tool.yaml`: `name: preflight`, `runtime: {type: python,
  path: tools.py, function: preflight_smoke}`, description says smoke-only
  (public visibility, no Jira env, `persons_llm=false`, `tmp/` output root)
  and that the committed graph binds nothing.

## README contract

1. Purpose paragraph citing FR-1027 and the sibling precedents (FR-892,
   FR-899, FR-962).
2. Reproduce this warning block VERBATIM (from FR-962's README):

   > **Use only on your own footprint or with the subject's explicit written
   > permission.** Profiling another person's authored PRs — even from public
   > repositories — may implicate labour law, data-protection law (GDPR
   > Art. 4, 6, 22 in the EU), platform terms of service, and employer
   > policies. Public availability of the source PR does not by itself
   > license aggregated behavioural analysis of the author. The corp-run
   > path additionally requires that the subject's employer has authorised
   > the LLM analysis under the applicable data-processing agreement. This
   > tool ships no consent mechanism; the operator is the accountable
   > controller.

   followed by one sentence: the operator running this graph is the
   accountable controller; `persons_llm` is required with no default and
   `true` requires `persons_llm_ack`.
3. Structure table (graph, prompts, tools/models/reduce/render/docs/canaries
   modules, manifests, adapter fixtures under
   `examples/demos/corpus_census/adapters/fixtures/jira/`).
4. The smoke command (below) and the live command shape (from the FR § Ideal
   Result, with `<org>` placeholder — never a real customer org name).
5. Outputs list: `onepager.md` (≤800 words), `dossier.md`, `repos.md`,
   `jira.md`, `ledgers/*.jsonl|csv`, `run.json`; the live output root is
   gitignored `research/org-ai-dossier/` and preflight rejects anything
   else; every share prints `n of <denominator>=<value>`.
6. Persons: two source-local rankings (`github:<login>`, `jira:<accountId>`),
   never joined.
No verdict vocabulary.

## Validation (required)

- `yamlgraph graph lint examples/demos/org_ai_dossier/graph.yaml`
- Smoke (real run: public GitHub owner `sheikkinen`, Jira fixtures, Azure
  keys + gh auth from `.env`; `persons_llm=false`):

```bash
yamlgraph graph run examples/demos/org_ai_dossier/graph.yaml --tool preflight=examples/demos/org_ai_dossier/smoke_preflight.tool.yaml --tool gh_discover=examples/demos/corpus_census/adapters/gh-org-active-discover.tool.yaml --tool gh_extract=examples/demos/corpus_census/adapters/gh-repo-ai-extract.tool.yaml --tool gh_search=examples/demos/corpus_census/adapters/gh-org-code-search.tool.yaml --tool jira_coverage=examples/demos/corpus_census/adapters/jira-fixture-coverage.tool.yaml --tool jira_discover=examples/demos/corpus_census/adapters/jira-fixture-discover.tool.yaml --tool jira_extract=examples/demos/corpus_census/adapters/jira-fixture-extract.tool.yaml --var org=sheikkinen --var visibility=public --var window_days=90 --var top_persons=5 --var persons_llm=false --var persons_llm_ack= --var out_dir=tmp/org-ai-dossier-smoke/authoring --full
```

Record the lint result and the smoke result (or the blocked reason) in
`tmp/draft-authoring-report.md`.
