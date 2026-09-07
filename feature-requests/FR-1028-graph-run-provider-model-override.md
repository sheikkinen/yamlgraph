# Feature Request: `graph run --provider/--model` Override of Graph Defaults

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-09-07
**First consumer / first event:** `scripts/research.sh` (FR-890 sole route) on
2026-09-07, blocked by a 401 from the Anthropic key while Azure and OpenAI
credentials in the same `.env` are valid — the operator chose "run on another
provider" over waiting for key rotation (FR-1027 § Decisions, item 4)
**Research:** in-body dispositioned alternatives table (§ Alternatives
Considered) — the research sole route is the blocked consumer, so it cannot
be the research producer for its own unblock (FR-890 R-6 equivalent record)
**Prior art:** FR-119 (lint: provider/model must be declared at top level or
per node — this FR keeps that contract; the override is a runtime input, not
a missing declaration); FR-263 (Azure OpenAI provider — the target provider);
FR-071 / FR-230 (graph-level thinking budget as a `defaults` key — precedent
that `defaults` is the graph-wide knob layer); FR-231 (provider/model timing
comparison — ran the same graph on several providers by editing YAML, the
pain this FR removes). No prior FR proposes a CLI/env override of `defaults`;
`feature-requests/` grep for "provider override" returns only the above.

## Summary

Add `--provider` and `--model` to `yamlgraph graph run`. They override the
graph's `defaults.provider` / `defaults.model` at the load boundary. Explicit
per-node `provider:` / `model:` pins are untouched — a governance pin such as
`repo_census`'s `provider: azure` on every LLM node cannot be redirected by a
CLI flag. `scripts/research.sh` forwards `RESEARCH_PROVIDER` /
`RESEARCH_MODEL` when set.

## Value Statement

An operator whose one provider key is dead runs any defaults-only graph on a
working provider from the command line, without editing committed YAML.

## Problem

`examples/demos/research-route/graph.yaml` declares `defaults: provider:
anthropic, model: claude-haiku-4-5` and pins nothing per node. On 2026-09-07
the `.env` Anthropic key returned 401 on `GET /v1/models`; Azure and OpenAI
keys in the same file were valid. There is no runtime override: `graph run`
offers `--var`, `--var-file`, `--tool` but no provider/model flag, and no
environment variable is consulted by `compile/graph_loader.py` (line 67:
`config.get("provider") or self.defaults.get("provider")`). The only routes
were editing the committed graph or waiting on key rotation. FR-1027's
research record was blocked by this.

## Ideal Result

```bash
RESEARCH_PROVIDER=azure RESEARCH_MODEL="$AZURE_MODEL" \
  scripts/research.sh feature-requests/research-briefs/org-ai-dossier.md
# ≡ yamlgraph graph run <graph> --provider azure --model <deployment> --var ...
```

runs the five personas on Azure; `tmp/draft-alternatives.md` records the
provider/model actually used; a graph with per-node `provider: azure` pins
ignores `--provider anthropic` entirely.

## Proposed Solution

- `yamlgraph/cli` `graph run`: two optional flags `--provider`, `--model`;
  values pass to the loader as `defaults_override: dict`.
- `compile/graph_loader.py`: apply `defaults_override` onto the graph's
  `defaults` mapping once, before node construction. Resolution order is
  unchanged: node pin → defaults (now overridden). Nothing else reads the
  flags.
- `scripts/research.sh`: append `--provider "$RESEARCH_PROVIDER"` /
  `--model "$RESEARCH_MODEL"` when the variables are non-empty; the artifact
  header gains a `- provider/model:` line so the promoted
  `FR-XXX.research.md` states what ran (FR-890 R-6 provenance).
- Lint (FR-119) is unaffected: the graph still declares its defaults.

## Acceptance Criteria

- [ ] RED: `graph run --provider azure` on a defaults-only fixture graph
      constructs LLM nodes with `provider == "azure"` (unit, factory mocked).
- [ ] Per-node pin wins: fixture with `provider: azure` on a node and
      `--provider anthropic` → node stays `azure` (unit — RED first).
- [ ] `--model` without `--provider` overrides only the model; vice versa.
- [ ] `scripts/research.sh` with `RESEARCH_PROVIDER` unset produces an
      identical argv to today (shell test); with it set, appends the flags and
      the artifact header carries `- provider/model:`.
- [ ] `research_preflight.py --verify-artifact` accepts the new header line.
- [ ] Live witness: `scripts/research.sh` on the FR-1027 brief completes on
      Azure; `FR-1027.research.md` promoted.
- [ ] Tests tagged `@pytest.mark.req("REQ-YG-XXX")`, CAP yaml, ARCHITECTURE
      row, changelog fragment; `req_coverage.py --strict` green.

## Alternatives Considered (probed 2026-09-07)

| Alternative | Probe / evidence | Verdict |
| --- | --- | --- |
| Rotate the Anthropic key | operator decision: run on another provider instead | Not chosen — remains the zero-code route; this FR does not preclude it |
| Edit `research-route/graph.yaml` defaults to `azure` | one-line change; but the committed route would then depend on `AZURE_*` env for every operator, and FR-890 baselines were produced on haiku | Rejected — moves the problem to the next operator |
| Environment variable read by the loader (`YAMLGRAPH_PROVIDER`) | `grep -rn 'DEFAULT_PROVIDER\|YAMLGRAPH_PROVIDER' yamlgraph/` → none exist; env is ambient and invisible in artifacts | Rejected in favour of explicit CLI flags that scripts forward and record |
| Convert research-route LLM nodes to `type: copilot` like judge/author/review routes | those routes pin `gpt-5.6-sol` / `claude-opus-5` via Copilot CLI, no API key; research-route has 5 `type: llm` + 1 `type: agent` (librarian with tools) — agent node has no copilot equivalent | Rejected — larger change, alters the FR-890 route contract |
| `--var provider=…` with Jinja in `defaults` | `defaults` is not templated; would need loader support anyway | Rejected — same code surface, worse contract |

## Related

- [FR-1027](FR-1027-org-ai-dossier-census.md) — blocked consumer
- [FR-890](FR-890-research-sole-route-closed-input-alternatives.md) research sole route;
  [scripts/research.sh](../scripts/research.sh);
  [examples/demos/research-route/graph.yaml](../examples/demos/research-route/graph.yaml)
- [yamlgraph/compile/graph_loader.py](../yamlgraph/compile/graph_loader.py)
