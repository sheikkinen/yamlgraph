# Feature Request: Promote Reference Docs to Copilot Skills

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Completed
**Effort:** 1 day
**Requested:** 2026-05-22

## Judgement

**Rejudged 2026-05-22.** Approved with amendments. Three issues in the original judgement:

### 1. `author-graph` is overloaded — split it

The `author-graph` skill combines `graph-yaml.md` (1,502 lines), `prompt-yaml.md` (616 lines), and `expressions.md` (422 lines) — 2,540 source lines into one skill. The existing `check-langsmith-trace` skill is 136 lines. Graph authoring and prompt authoring are distinct concerns with distinct triggers ("add a node" vs "write a prompt schema"). Split into:

- **`author-graph`**: `graph-yaml.md` + `expressions.md` — node types, edges, routing, conditions, variables
- **`author-prompt`**: `prompt-yaml.md` — prompt templates, Jinja2, inline schemas, few-shot examples

This makes Phase 1 deliver **6 Tier 1 skills**, not 5.

### 2. `run-code-analysis` overlaps with the `code-analysis` agent

A `code-analysis` agent already exists (declared in `.github/agents/`). The skill should focus on **manual usage** — which tools to run, what flags to use, how to interpret output. The agent runs analysis autonomously. Name the skill `code-analysis-manual` to avoid confusion, or keep `run-code-analysis` but document the agent relationship in the skill body.

### 3. Acceptance criteria contradict scope

The scope says "Phase 1 = Tier 1 only" but the AC includes Tier 2 items. Also, `docs/context/fr-424.md` and `fr-444.md` don't exist — that AC item is dead.

### Amended scope

**Phase 1 (this FR):** Create 6 Tier 1 skills: `author-graph`, `author-prompt`, `release-version`, `chaplain-ops`, `run-code-analysis`, `feature-request`.

**Phase 2 (separate FR):** Tier 2 skills deferred.

**Scope freeze:** No changes to `copilot-instructions.md` or `CLAUDE.md`. No auto-generation. Manual curation only. Each skill targets ≤200 lines of curated procedural content.

## Summary

Create Copilot skill files (`.github/skills/*/SKILL.md`) from the highest-value reference docs so they are loaded on-demand when the user's intent matches, instead of being invisible unless manually read.

## Value Statement

Developers and agents get automatic access to the right reference material at the right time, eliminating manual `read_file` calls for the 12,761 lines of reference docs that are currently never auto-loaded.

## Problem

The current knowledge architecture has a gap:

| Layer | Lines | Loading | Content |
|-------|-------|---------|---------|
| `copilot-instructions.md` | 207 | Always | Scripture, Knowledge Graph, conventions |
| `CLAUDE.md` | 443 | Always | Dev commands, architecture, critical rules |
| Skills | ~100 | On-demand (1 skill) | LangSmith traces only |
| Reference docs | 12,761 | Never auto-loaded | 30 files covering all framework topics |

Only 1 skill (`check-langsmith-trace`) exists. The 30 reference docs — including the two largest (`graph-yaml.md` at 1,502 lines, `prompt-yaml.md` at 616 lines) — require the agent to discover and read them manually. This means:

1. Graph authoring questions trigger 2-3 file reads before the agent can answer
2. Release procedures require the agent to find and read `release-checklist.md`
3. Chaplain operations require reading `docs/context/chaplain-system.md`
4. Node type questions require reading 5+ separate reference files

Skills solve this: they declare a description with trigger keywords, and VS Code auto-loads the skill content when the user's intent matches.

## Proposed Solution

Create skill files in `.github/skills/<name>/SKILL.md` for the following tiers.

### Tier 1 — High impact, clear trigger

| Skill | Source files | Trigger keywords |
|-------|-------------|------------------|
| `author-graph` | `reference/graph-yaml.md`, `reference/expressions.md` | graph YAML, add node, edge, routing, conditions, variables, state_key |
| `author-prompt` | `reference/prompt-yaml.md` | prompt YAML, prompt schema, Jinja2 template, few-shot, inline schema |
| `release-version` | `reference/release-checklist.md` | release, bump version, tag, push release, changelog freeze |
| `chaplain-ops` | `docs/context/chaplain-system.md` | chaplain, dispatcher, pipeline FSM, inbox, watcher |
| `run-code-analysis` | `reference/code-analysis.md` | code analysis, ruff, bandit, radon, vulture, quality |
| `feature-request` | `feature-requests/TEMPLATE.md`, copilot-instructions Sermon section | feature request, FR-, plan judge enforce, submit proposal |

### Tier 2 — Specialized, less frequent

| Skill | Source files | Trigger keywords |
|-------|-------------|------------------|
| `node-types` | `reference/map-nodes.md`, `reference/subgraph-nodes.md`, `reference/interrupt-nodes.md`, `reference/passthrough-nodes.md`, `reference/tool-call-nodes.md` | map node, subgraph, interrupt, passthrough, tool_call, race node |
| `setup-streaming` | `reference/streaming.md`, `reference/async-usage.md` | streaming, async, token-by-token, SSE |
| `configure-mcp` | `reference/mcp-server.md` | MCP, copilot tools, expose graph as tool |
| `setup-a2a` | `reference/a2a-server.md` | A2A, agent-to-agent, agent card |
| `develop-hooks` | `.github/hooks/README.md` | copilot hook, pre-tool, post-edit, hook script |

### Skill file format

Each skill follows the VS Code Copilot skill format:

```yaml
---
name: author-graph
description: "Author YAMLGraph graphs and prompts. Use when: creating or editing graph YAML, adding nodes/edges, writing prompt templates, configuring schemas, using expressions or Jinja2 in prompts."
argument-hint: "node type, field name, or 'prompt schema'"
---
```

Followed by a curated subset of the source reference docs — not a raw copy, but a focused procedural guide optimized for agent consumption.

### Design decisions

1. **Curated, not copied.** Each skill distills the source reference into the most actionable content. Raw reference docs remain the canonical source.
2. **Composite skills preferred.** `node-types` combines 5 files into one skill rather than creating 5 micro-skills, because intent overlap is high ("how do I use a map node?" and "how do subgraphs work?" come from the same mental context).
3. **No changes to copilot-instructions.md.** The always-loaded instructions stay lean. Skills add breadth without adding weight.
4. **`docs/context/` cleanup.** Stale Chaplain context plans (`fr-424.md`, `fr-444.md`) are deleted. Remaining context files that become skills can be kept as canonical source or removed if fully absorbed.

## Acceptance Criteria

- [x] Tier 1 skills created (6 skills: `author-graph`, `author-prompt`, `release-version`, `chaplain-ops`, `run-code-analysis`, `feature-request`)
- [x] Each skill has proper YAML frontmatter (`name`, `description`, `argument-hint`)
- [x] Each skill contains curated procedural content (~200 lines, not raw doc copy)
- [x] Existing `check-langsmith-trace` skill unchanged
- [x] Skills auto-discovered by VS Code from `.github/skills/*/SKILL.md` (no manual registration needed)
- [x] Smoke test: open new chat, ask "how do I add a node to a graph?" — verify `author-graph` skill loads

## Alternatives Considered

1. **Inline everything into copilot-instructions.md** — Rejected. Already 207 lines; adding 12K+ lines would bloat every conversation's context window.
2. **Use `docs/context/` files only** — Rejected. Loading semantics are unclear and editor-dependent. Skills have a defined contract.
3. **One skill per reference file** — Rejected. Too many micro-skills with overlapping triggers. Composite skills reduce noise.
4. **Auto-generate skills from reference docs** — Deferred. Could use `yamlgraph skill export` (CAP-142) in the future, but manual curation produces better agent-optimized content for now.

## Related

- CAP-142: `yamlgraph skill export` (portable graph packaging — different scope)
- CAP-143: agent-md export format
- `.github/skills/check-langsmith-trace/SKILL.md` (existing skill, pattern to follow)
- `reference/skills-export.md` (CLI reference for graph-to-skill export)
