# Authoring brief: cap_journey_census graph (per-CAP journey / blast / disposition / value census)

**Governing document:** docs/2026-09-05-research-plan-cap-journey-census.md (research plan, operator-reviewed 2026-09-05; pre-FR — the measurement FR follows the pilot)
**Prior art:** fr-899-repo-census-brief.md and fr-892-corpus-census-brief.md (sibling census graphs this one deliberately mirrors); fr-940-census-labels-model-brief.md (label/model discipline). `examples/demos/person_profile_census/` is the reducer precedent (multi-field verdict, `row_failed` containment).
**Target directory:** examples/demos/cap_journey_census/
**Artifacts to author:** `graph.yaml`, `prompts/judge_cap.yaml`, `README.md`

## Task

Author a sibling of `examples/demos/corpus_census/graph.yaml` that censuses
the capability registry (`capabilities/CAP-*.yaml`): one cheap per-CAP
judgement adding the columns the traceability chain cannot carry — customer
journey (closed catalog), blast kind, keep/retire/extend disposition, value
proposition — followed by an LLM-free reduce. No synthesis tail: the reduced
ledger IS the artifact.

Python already exists — do NOT author Python. `examples/demos/cap_journey_census/tools.py`
provides `cap_discover`, `cap_extract`, `reduce_cap_ledger`. The journey
catalog is `examples/demos/cap_journey_census/journeys.yaml`; hidden
canaries are `examples/demos/cap_journey_census/canaries.yaml` (the model
must never see either file's contents — the reducer reads them).

## Graph contract

- `version: "1.0"`, `name: cap-journey-census`, `prompts_relative: true`,
  `prompts_dir: prompts`.
- `defaults: {provider: anthropic, model: claude-haiku-4-5, temperature: 0.0}`.
  The LLM node takes `provider: "{state.provider}"` and
  `model: "{state.model}"` so the pilot (haiku) and a later mercury run of
  the enum columns are invocation choices, not edits.
- `config: {max_map_items: 250}`.
- State keys: `source: str`, `provider: str`, `model: str`,
  `output_path: str`, `journeys_path: str`, `canaries_path: str`,
  `items: list`, `contents: list (reducer sorted_add)`,
  `findings: list (reducer sorted_add)`, `ledger: dict`.
- Tools (all `type: python`, `path: tools.py`): `discover` → `cap_discover`,
  `extract` → `cap_extract`, `reduce_cap_ledger` → `reduce_cap_ledger`.
  Plain tools, not FR-892 slots — this graph has one corpus.
- Nodes and edge order (exact):
  `START → discover → extract_items → judge_items → reduce_cap_ledger → END`
- `discover`: python, tool `discover`, variables `source: "{state.source}"`,
  state_key `items`, `on_error: fail`.
- `extract_items`: `type: map`, `over: "{state.items}"`, `as: item`,
  `max_items: 250`, sub-node python tool `extract`, state_key `content`,
  `on_error: fail`, `collect: contents`.
- `judge_items`: `type: map`, `over: "{state.contents}"`,
  `as: judged_content`, `max_items: 250`, sub-node `type: llm`,
  `prompt: judge_cap`, `provider: "{state.provider}"`,
  `model: "{state.model}"`, `temperature: 0.0`, `on_error: skip`,
  state_key `finding`, `collect: findings`, variables
  `journey_ids: "{state.journey_ids}"`,
  `content: "{state.judged_content.value}"`,
  `source_index: "{state.judged_content._map_index}"`.
- State key `journey_ids: str` — the caller passes the catalog ids as a
  comma-separated string (`--var journey_ids=...`). The model sees only the
  ids, never the catalog's `who` text or the canaries.
- `reduce_cap_ledger`: python, tool `reduce_cap_ledger`, state_key `ledger`.
  It reads `items`, `contents`, `findings`, `output_path`, `model`,
  `journeys_path`, `canaries_path` from state.

## Prompt contract — `judge_cap.yaml` (one CAP per call, input-closed)

- System: the model classifies ONE capability from a JSON evidence bundle
  (CAP yaml, the creating FR's head, and MECHANICAL facts: consumer paths
  found by grep, doc mentions, incident-file count, diary mentions, tagged
  test files). It must use only the bundle; it must not guess consumers
  that are not in the mechanical lists; it abstains rather than invents.
- User: `Journey ids (closed catalog): {journey_ids}`, `Evidence bundle:
  {content}`, `Source index: {source_index}`, then field instructions.
- Schema name `CapJourneyFinding`, fields (all required):
  - `source_index: int ge 0` — echo of the supplied index.
  - `journeys: list[str]` — 1..3 values; each MUST be one of the journey
    ids, or `off_catalog:<snake_case_label>` when none fits. Use
    `none_internal` for capabilities that serve only this repo's developer
    velocity.
  - `blast_kind: str` — exactly one of `core_runtime`, `node_type`,
    `cli_surface`, `tooling_integration`, `process_infra`, `example_only`.
  - `disposition: str` — exactly one of `keep`, `retire`, `extend`,
    `already_retired`. `already_retired` only when bundle `status` is
    `retired`. `keep` requires citing a consumer path from the bundle's
    mechanical consumer lists in `consumer_cited`. `retire` only when the
    mechanical consumer lists are empty. `extend` requires `extend_to`.
  - `extend_to: str` — a journey id when disposition is `extend`, else "".
  - `consumer_cited: str` — one path copied verbatim from
    `mechanical.consumers_by_id` or `mechanical.consumers_by_module`, else "".
  - `value_for_whom: str` — a journey id (who benefits), else "".
  - `value_pain: str` — one sentence: what pain is removed, else "".
  - `value_versus: str` — the real alternative (raw LangGraph, a script, a
    vendor feature, "nothing"), else "".
  - `evidence_span: str` — a short EXACT substring of the CAP yaml text or
    the FR head that supports `journeys`; empty only when abstained.
  - `abstained: bool`, `abstain_reason: str` — abstain when the bundle
    cannot support a journey judgement; then set journeys to
    `["none_internal"]`, evidence_span "", confidence irrelevant.
- FORBIDDEN in the prompt: any mention of the canary file, expected
  answers, other CAPs, the prior node-type census verdict, or aggregate
  questions (counts, rankings). One CAP, one judgement.

## README contract

State purpose (one paragraph citing the research plan path), the
invocation below, the four census columns, the fail-closed anchors the
reducer applies (catalog, consumer citation, evidence substring, canary
gate after artifacts are written), and that `retire` rows are claims that
still go through the FR-466 lifecycle. No verdict vocabulary.

## Validation the authoring run must perform

- `yamlgraph graph lint examples/demos/cap_journey_census/graph.yaml`
- Smoke (3 CAPs, canaries omitted so the gate does not fire on a partial
  set):

```bash
PYTHONPATH=$PWD yamlgraph graph run examples/demos/cap_journey_census/graph.yaml \
  --var source="capabilities:ids=CAP-131,CAP-81,CAP-126" \
  --var provider=anthropic --var model=claude-haiku-4-5 \
  --var journey_ids="author_graph,run_operate,debug_observe,integrate,serve_embed,census_classify,govern_process,audit_comply,conversational_app,none_internal" \
  --var journeys_path=examples/demos/cap_journey_census/journeys.yaml \
  --var canaries_path="" \
  --var output_path=tmp/cap-census/smoke.md --json > tmp/cap-census/smoke.json
```

Verify by artifact: `tmp/cap-census/smoke.md` exists with a
"Journey × CAP matrix" heading and `tmp/cap-census/smoke.jsonl` has 3 rows.
Record the smoke in the authoring report; if the run is blocked (no API
key), record the blocked command honestly.
