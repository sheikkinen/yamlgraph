# Authoring brief: FR-1121 standalone digest — ranker schema and error policy

Governing FR: feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md
(judgement D-4; this brief closes the standalone-digest authoring run).

Repository boundary: the **external** repository
`sheikkinen/yamlgraph-daily-digest`, checked out beside this one; on
this host the checkout is `C:/src/yamlgraph-daily-digest`. The
authoring route runs from this YAMLGraph checkout with
`AUTHOR_WORKDIR` set to that checkout, every edit happens there and
not in the YAMLGraph checkout, and every path below is relative to the
digest checkout. Nothing from that checkout is committed here
(judgement C-3): no nested repository, no bulletin, no database.

## Task

Modify **exactly two files** in the digest checkout:

1. `prompts/rank_stories.yaml` — in `schema.fields.stories`, change
   `type: list[Any]` to `type: list[dict]`. Templates, description and
   every other field stay byte-identical.
2. `graph.yaml` — in the `rank_stories` node, add `on_error: fail` (one
   line). No other node, edge, `defaults`, `tools`, `state` or `config`
   entry changes. `analyze_all` is not touched by this brief; its
   migration is FR-1122's brief.

Related artifacts edited by the FR's enforcement in the digest
repository, not by this run: `run_digest.py` (the post-invoke error
guard that exits 2 before any no-op line) and the focused FR-1121 tests
under `tests/`, including the replacement for FR-905's schema-pin test.

## Validation

- Before the edit, record the complete output of
  `yamlgraph graph lint graph.yaml` (run in the digest checkout) in the
  report; after the edit, run the identical command and record it
  again. The after set must be unchanged or reduced, and no diagnostic
  may point at `rank_stories` or its prompt schema (judgement R-3). The
  pre-existing E601 on `gate` and the W013/W017/W022 on `analyze_all`
  are expected in both sets; they belong to FR-1122.
- `python -m pytest tests -q` in the digest checkout — the FR-1121 tests
  and every remaining FR-905 test must pass after the edit.
- No live smoke in this run: there is no dry mode in the digest
  (README), and a run archives and emails. The production witness is
  the first scheduled run after merge, recorded per judgement AC-11.

**Prior art:** FR-1121 (governing FR; this brief executes its D-4
surface); FR-903, FR-904, FR-905 (the digest's own lineage, all
authored under briefs in this directory's convention); FR-1122 (the
sibling brief for the same graph's map node, applied after this one).
