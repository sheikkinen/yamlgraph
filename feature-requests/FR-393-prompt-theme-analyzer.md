# Feature Request: Prompt Theme Analyzer Example

**Priority:** LOW
**Type:** Feature
**Status:** Superseded by FR-402
**Effort:** 1 day
**Requested:** 2026-05-16

## Summary

A YAMLGraph example graph that reads hundreds of image-generation prompt files, classifies each with a concise theme using Inception Mercury (fast/cheap), groups themes into ~10 clusters, and outputs a structured markdown report.

## Value Statement

Graph authors get a real-world demonstration of large-scale map fan-out (900+ items) with a cost-efficient provider, showing YAMLGraph's strength at batch classification and aggregation workflows.

## Problem

The `/Volumes/deviant/image_pipeline/` directory contains 907+ timestamped prompt sets from image generation runs. These are long, richly detailed prompts (avg ~19K chars) with no thematic index. Manual review is impractical. A YAMLGraph pipeline can classify and group them cheaply using Mercury's fast inference.

## Proposed Solution

Four-node pipeline following the diary-index pattern (FR-254), plus a shell helper for local pre-analysis:

```
list_prompts (Python) → classify_themes (map/LLM) → group_themes (LLM) → write_report (Python)
```

### Shell Helper: `examples/prompt_theme_analyzer/analyze.sh`

A standalone shell script (calls embedded Python) for quick keyword-based pre-analysis — no LLM, no API keys required. Scans the source directory for `prompts.txt` files and outputs:

- Total prompt count and date range
- Theme distribution (keyword matching against ~18 theme categories)
- Artist reference frequency
- Prompt length statistics
- Co-occurrence matrix of top theme pairs

This mirrors the ad-hoc analysis performed during research and serves as a fast sanity check before running the full Mercury pipeline.

```bash
# Usage
./examples/prompt_theme_analyzer/analyze.sh /Volumes/deviant/image_pipeline
```

### Graph: `examples/prompt_theme_analyzer/graph.yaml`

```yaml
version: "1.0"
name: prompt-theme-analyzer
description: >
  Read prompt files from image pipeline runs, classify each with a
  concise theme via Inception Mercury, group into ~10 clusters,
  output markdown report. (FR-393)

prompts_relative: true
prompts_dir: prompts

defaults:
  provider: inception
  model: mercury-2
  temperature: 0.3

state:
  source_dir: str
  prompt_entries:
    type: list
  classifications:
    type: list
    reducer: sorted_add
  theme_groups: dict
  report: str
  output_path: str

tools:
  list_prompts:
    type: python
    module: examples.prompt_theme_analyzer.tools
    function: list_prompts
    description: "Scan source_dir for prompts.txt files, return list of {timestamp, text}"
  write_report:
    type: python
    module: examples.prompt_theme_analyzer.tools
    function: write_report
    description: "Write grouped theme report as markdown"

nodes:
  list_prompts:
    type: python
    tool: list_prompts
    state_key: prompt_entries

  classify_themes:
    type: map
    over: "{state.prompt_entries}"
    as: entry
    max_items: 1000
    node:
      type: llm
      prompt: classify_theme
      state_key: classification
      on_error: skip
      variables:
        timestamp: "{state.entry.timestamp}"
        prompt_text: "{state.entry.text}"
    collect: classifications

  group_themes:
    type: llm
    prompt: group_themes
    state_key: theme_groups
    variables:
      classifications_json: "{state.classifications}"

  write_report:
    type: python
    tool: write_report
    state_key: output_path

edges:
  - from: START
    to: list_prompts
  - from: list_prompts
    to: classify_themes
  - from: classify_themes
    to: group_themes
  - from: group_themes
    to: write_report
  - from: write_report
    to: END
```

### Prompt: `classify_theme.yaml`

Classify a single prompt set into a concise 2-4 word theme. Mercury is fast and cheap — no need for heavy reasoning. Input truncated to first 2000 chars to stay within token budget.

```yaml
name: classify_theme
description: Classify an image prompt into a concise theme
system: >
  You are a prompt classifier. Given an image generation prompt,
  return a concise 2-4 word theme label. Examples: "Dark Gothic Romance",
  "Cyberpunk Warrior Portrait", "Underwater Mythology", "Art Nouveau Flora".
  Be specific but not verbose.
template: |
  Classify this image generation prompt from run {timestamp}.

  PROMPT (first 2000 chars):
  {prompt_text:.2000}

  Return a concise 2-4 word theme label.
schema:
  name: ThemeClassification
  fields:
    timestamp: {type: str, description: "Run timestamp"}
    theme: {type: str, description: "Concise 2-4 word theme label"}
```

### Prompt: `group_themes.yaml`

Group the classified themes into ~10 coherent clusters.

```yaml
name: group_themes
description: Group classified themes into ~10 clusters
system: >
  You are an art taxonomy expert. Given a list of theme labels from
  image generation prompts, group them into approximately 10 coherent
  thematic clusters. Each cluster should have a clear name and list
  its member themes with counts.
template: |
  Here are the classified themes from {{classifications_json | length}} image prompt sets:

  {% for c in classifications_json %}
  - {{c.timestamp}}: {{c.theme}}
  {% endfor %}

  Group these into approximately 10 thematic clusters.
  For each cluster, provide: name, description, member themes, and count.
schema:
  name: ThemeGroups
  fields:
    groups:
      type: list
      items:
        name: {type: str, description: "Cluster name"}
        description: {type: str, description: "What unifies this cluster"}
        count: {type: int, description: "Number of prompts in cluster"}
        member_themes:
          type: list
          items: {type: str}
        sample_timestamps:
          type: list
          items: {type: str}
    total_classified: {type: int, description: "Total prompts classified"}
```

### Python tools: `tools.py`

```python
def list_prompts(state: dict) -> dict:
    """Scan source_dir for prompts.txt files."""
    source_dir = Path(state.get("source_dir", "/Volumes/deviant/image_pipeline"))
    entries = []
    for prompts_file in sorted(source_dir.glob("*/prompts.txt")):
        timestamp = prompts_file.parent.name
        text = prompts_file.read_text(encoding="utf-8", errors="replace")
        # Skip error dumps and refusals
        if text.startswith("{") or len(text.strip()) < 50:
            continue
        entries.append({"timestamp": timestamp, "text": text})
    return {"prompt_entries": entries}

def write_report(state: dict) -> dict:
    """Write grouped theme report as markdown."""
    groups = state["theme_groups"]["groups"]
    output_path = Path(state.get("output_path", "outputs/prompt-theme-report.md"))
    # ... format as markdown table with groups, counts, samples ...
    return {"output_path": str(output_path)}
```

### Usage

```bash
yamlgraph graph run examples/prompt_theme_analyzer/graph.yaml \
  --var source_dir="/Volumes/deviant/image_pipeline" \
  --var output_path="outputs/prompt-theme-report.md" \
  --full
```

## Design Decisions

1. **Mercury for classification**: At ~$0.001/call, classifying 907 prompts costs ~$1. Fast inference means the map fan-out completes in minutes.
2. **Truncate to 2000 chars**: Prompts avg 19K chars but themes are evident from the opening. Saves 90% tokens.
3. **Grouping via stronger model optional**: The `group_themes` node processes ~907 short labels. Mercury handles this fine, but could override to Anthropic for better taxonomy.
4. **Skip filter in list_prompts**: Filters out error dumps (`{_map_index...}`) and LLM refusals (`I'm sorry...`).
5. **max_items: 1000**: Above default 100. The diary-index precedent uses 500. Mercury's speed makes 1000 practical.

## Acceptance Criteria

- [ ] `analyze.sh` runs standalone against source dir, prints theme/artist/stats summary
- [ ] Graph runs end-to-end with `--full` flag
- [ ] `list_prompts` correctly reads 900+ prompt files
- [ ] `classify_themes` fan-out produces theme labels for each prompt
- [ ] `group_themes` produces ~10 coherent clusters
- [ ] `write_report` outputs valid markdown with tables
- [ ] `demo-output.log` captures a successful run
- [ ] Tests added for Python tools (list_prompts, write_report)
- [ ] Graph passes `yamlgraph graph lint`

## Alternatives Considered

1. **Pure Python script** (the ad-hoc analysis above) — works but doesn't demonstrate YAMLGraph patterns or leverage structured LLM output.
2. **Batch API calls without map** — loses parallelism and error isolation per-item.
3. **Two-pass LLM** (classify + group in one) — breaks separation of concerns; 907 prompts too large for single context.

## Judgement

**Verdict: APPROVED with corrections.**

The pattern is sound — it mirrors diary-index (FR-254) faithfully and demonstrates a real use case for large-scale map fan-out. Cost analysis is thoughtful. The following must be corrected before enforcement:

### Corrections Required

1. **`{prompt_text:.2000}` is not supported syntax.** YAMLGraph simple templates don't support Python format specs. Either truncate in the Python tool (`list_prompts` should cap `text` to 2000 chars) or use Jinja2: `{{ prompt_text[:2000] }}`. Recommend truncating in the tool — normalize at the boundary where data enters, not downstream in the prompt.

2. **Context window risk in `group_themes`.** Sending 907 theme labels through a Jinja2 `{% for %}` loop produces a massive prompt. Diary-index uses a deterministic Python `aggregate_index` tool between map and LLM. FR-393 must add the same: a Python node that deduplicates/counts themes before the LLM grouping step. The LLM receives ~50-100 unique themes with counts, not 907 raw labels.

3. **Hardcoded `/Volumes/deviant/` default.** The `list_prompts` tool must not default to a local volume path. Make `source_dir` a required state field (no default). The graph-level `--var source_dir=...` is sufficient.

4. **Missing requirement ID.** Assign REQ-YG-XXX and register in `capabilities/`.

5. **Missing diary entry** in acceptance criteria. Standard per Scripture — add it.

### Approved As-Is

- Shell helper `analyze.sh` — useful secondary artifact, keep it
- Mercury provider choice — cost-effective for classification
- `max_items: 1000` — justified by Mercury's speed and diary-index precedent at 500
- `on_error: skip` — correct for large fan-out resilience
- `sorted_add` reducer — matches diary-index pattern

### Frozen Scope

- 4 nodes + 1 aggregate (corrected: 5 nodes total)
- 2 prompts (classify_theme, group_themes)
- 1 Python tools module
- 1 shell helper script
- Tests for Python tools
- Demo output log

## Related

- FR-254: Diary Index Graph (same list→map→aggregate→write pattern)
- `examples/image_pipeline/` (source of the prompt files)
- `examples/demos/diary_index/` (closest architectural precedent)
