# Task Brief: GitHub-native daily digest graph (FR-819)

## Target

Author into the EXTERNAL sibling repository directory
`/Users/sheikki/Documents/src/yamlgraph-daily-digest/` (absolute paths;
this is a separate git repo — FR-819 C-4 forbids vendoring it into
yamlgraph):

- `/Users/sheikki/Documents/src/yamlgraph-daily-digest/graph.yaml`
- `/Users/sheikki/Documents/src/yamlgraph-daily-digest/prompts/analyze_article.yaml`
- `/Users/sheikki/Documents/src/yamlgraph-daily-digest/prompts/rank_stories.yaml`

## Task

Adapt `examples/daily_digest/graph.yaml` and its two prompts
(`examples/daily_digest/prompts/analyze_article.yaml`,
`examples/daily_digest/prompts/rank_stories.yaml`) into a GitHub-native
variant that renders a markdown bulletin instead of sending email.

Precedent: `examples/daily_digest/` is THE precedent — copy its
structure faithfully. This is a subtraction adaptation, not a redesign.

### graph.yaml changes vs the example

1. `name: daily_digest_github`, description mentions markdown bulletin,
   no email.
2. **Remove the sqlite checkpointer block entirely** — the runner is
   ephemeral and never resumes; the committed `digest.db` serves only
   the `filter_recent` node's seen-URL dedup (via `DATABASE_PATH`).
   No checkpointer noise in committed state.
3. State: drop `recipient_email`, `digest_html`, `email_sent`; add
   `digest_markdown: str`. Keep the rest unchanged.
4. Tools: drop `format_email` and `send_email`. Add:
   ```yaml
   format_markdown:
     type: python
     module: nodes.formatting
     function: format_markdown
     description: "Render markdown bulletin from ranked stories"
   ```
   Keep `fetch_sources`, `filter_recent`, `fetch_article_content`
   verbatim.
5. Nodes: drop `format_email` and `send_email`; add node
   `format_markdown` (type python, tool format_markdown,
   state_key digest_markdown). Keep `fetch_sources`, `filter_recent`,
   `fetch_content`, `analyze_all` (map), `rank_stories` verbatim —
   including the map node's `on_error: skip`.
6. Edges: same chain, ending `rank_stories → format_markdown`. The
   example's edge list ends at `format_email` with implicit END; keep
   the same idiom for `format_markdown`.
7. Keep `defaults` (provider anthropic, temperature 0.5,
   prompts_relative true, prompts_dir prompts) unchanged.

### Prompts

Copy both prompts verbatim from the example — schemas included. The
`rank_stories.yaml` prompt references
`item._map_analyze_all_sub.*` fields; the map node name is unchanged so
these references remain correct. Do not rename fields, do not "improve"
wording.

## Validation

- `yamlgraph graph lint /Users/sheikki/Documents/src/yamlgraph-daily-digest/graph.yaml`
  must pass.
- Smoke: from `/Users/sheikki/Documents/src/yamlgraph-daily-digest/`,
  the graph must load and compile:
  `python -c "import sys; sys.path.insert(0,'.'); from yamlgraph.compile.graph_loader import load_and_compile; load_and_compile('graph.yaml').compile(); print('compiles')"`
  (Python tool imports resolve against the PoC dir; a full LLM run is
  NOT required for this brief — the operator runs the end-to-end smoke
  separately with API keys.)

## Constraints

- Do not modify anything under `examples/daily_digest/`.
- Do not create any files in the yamlgraph repo other than
  `tmp/draft-authoring-report.md`.
- Supporting Python nodes (`nodes/formatting.py` etc.) already exist in
  the target directory — do not rewrite them.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
