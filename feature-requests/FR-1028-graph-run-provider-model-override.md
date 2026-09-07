# Feature Request: `graph run --provider/--model` Override of Graph Defaults

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS 2026-09-07; R-1..R-5 folded
2026-09-07; see [FR-1028-graph-run-provider-model-override.judgement.md](FR-1028-graph-run-provider-model-override.judgement.md)
**Effort:** 0.5 days
**Requested:** 2026-09-07
**First consumer / first event:** `scripts/research.sh` (FR-890 sole route) on
2026-09-07, blocked by a 401 from the Anthropic key while Azure and OpenAI
credentials in the same `.env` are valid — the operator chose "run on another
provider" over waiting for key rotation (FR-1027 § Decisions, item 4)
**Research:** in-body dispositioned record (§ Research Record) — the research
sole route is the blocked consumer, so it cannot be the research producer
for its own unblock (FR-890 R-6 equivalent record; substance per judgement
R-1)
**Prior art:** FR-119 (lint: provider/model must be declared inside
`defaults:` or per node — this FR keeps that contract; the override is a
runtime input, not a missing declaration); FR-263 (Azure OpenAI provider —
the target provider); FR-071 / FR-230 (graph-level thinking budget as a
`defaults` key — precedent that `defaults` is the graph-wide knob layer);
FR-231 (`graph bench`: authorized provider/model overrides per run via
`configurable.provider_override` / `model_override` set AFTER compilation in
`yamlgraph/cli/bench_commands.py` — but `llm_nodes.py` and `tools/agent.py`
resolve `node pin → defaults` and never read those `configurable` keys, so
the bench override is inert for those node kinds; that defect is RECORDED
here for a separate FR and NOT repaired under this authority — judgement
C-7). No prior FR proposes a load-boundary override of `defaults`;
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

- `yamlgraph/cli/__init__.py` `graph run`: two optional string flags
  `--provider`, `--model` (default `None`); `yamlgraph/cli/graph_commands.py`
  forwards them to the loader.
- `yamlgraph/compile/graph_loader.py` `load_graph_config(...)`: keyword-only
  `provider_override: str | None = None`, `model_override: str | None = None`.
  The loader COPIES the parsed root mapping and its `defaults` mapping,
  replaces only the non-`None` of the two values, and constructs
  `GraphConfig` from the copy — the parsed source mapping is never mutated.
  No `defaults_override: dict`; no other `defaults` key is reachable.
  Resolution order is unchanged: `explicit node field → (overridden) root
  default → existing provider resolution`; provider and model resolve
  independently. Both `type: llm` (`llm_nodes.py` 150–158) and `type: agent`
  (`tools/agent.py` 257–267) already read `defaults`, so both inherit.
- Root graph only: the override applies to the graph `graph run` loads;
  graph-tool child graphs keep their own declarations (not forwarded).
- `scripts/research.sh`: `RESEARCH_PROVIDER` and `RESEARCH_MODEL` are a PAIR
  — both unset ⇒ today's argv byte-for-byte; both set ⇒ append `--provider
  "$RESEARCH_PROVIDER" --model "$RESEARCH_MODEL"` in that order; exactly one
  set ⇒ exit 64 with an actionable message BEFORE the executor is invoked.
  On an override run the wrapper — not the graph — atomically inserts
  exactly one `- provider/model: <provider>/<model>` line into the artifact
  header (write temp + `mv`) BEFORE `research_preflight.py --verify-artifact`
  runs. (Today the artifact is authored inside `reduce_findings()`,
  `examples/demos/research-route/nodes/research_tools.py` 755–783, with
  brief/date/persona headers only; the graph and its prompts are not
  modified.)
- `scripts/research_preflight.py --verify-artifact`: the `- provider/model:`
  line is OPTIONAL (legacy artifacts pass); when present it must be exactly
  one line matching `^- provider/model: [a-z0-9_-]+/[A-Za-z0-9._:-]+$`; empty,
  duplicate, or malformed ⇒ exit 65.
- Lint (FR-119) is unaffected: `graph lint` validates the committed YAML and
  never sees runtime flags.

## Acceptance Criteria (judgement AC-01..AC-12, frozen)

- [ ] AC-01: parser tests — `graph run` accepts optional `--provider` /
      `--model`; both `None` when omitted.
- [ ] AC-02 (RED first): loader test — root graph with declared defaults
      resolves an explicit pair; the parsed source mapping and a second
      unoverridden load retain the YAML values.
- [ ] AC-03: provider-only and model-only each replace only the named root
      default.
- [ ] AC-04: factory-mocked — defaults-only `type: llm` AND `type: agent`
      nodes both receive the overridden pair.
- [ ] AC-05: explicit provider/model pins win independently on both node
      kinds; a mixed-pin fixture (one field pinned) proves the unpinned field
      inherits its overridden default.
- [ ] AC-06: graph-tool child fixture — root override is not forwarded to
      the child graph.
- [ ] AC-07: no-flag `graph run` unchanged; `graph lint` ignores runtime flags.
- [ ] AC-08: shell tests — `research.sh` forwards nothing when both vars
      unset, both flags in stable order when both set, exits 64 before the
      executor when exactly one is set.
- [ ] AC-09: wrapper inserts exactly one `- provider/model:` line before
      verification; verifier accepts one valid line and legacy artifacts,
      rejects empty / duplicate / malformed.
- [ ] AC-10: live — `RESEARCH_PROVIDER=azure RESEARCH_MODEL=<deployment>
      scripts/research.sh feature-requests/research-briefs/org-ai-dossier.md`
      completes all personas, header carries the exact pair, verification
      passes, promoted to `feature-requests/FR-1027.research.md`; no
      credential or private org identifier in the artifact (C-6).
- [ ] AC-11: tests tagged `@pytest.mark.req("REQ-YG-671")`;
      `capabilities/CAP-267-graph-run-provider-model-override.yaml`;
      `ARCHITECTURE.md` row; `python scripts/req_coverage.py --strict` green.
      (IDs checked free on main and all remote branches 2026-09-07; FR-1027
      holds REQ-YG-670 / CAP-266.)
- [ ] AC-12: changelog fragment; § Implementation Record below filled; diary
      Distill entry with `Seed:`.

Test files: `tests/unit/test_fr1028_provider_model_override.py` (AC-01..07),
`tests/unit/test_fr890_research_wrapper.py` or its sibling (AC-08, AC-09).

## Research Record (FR-890 R-6 equivalent; judgement R-1)

`is_this_a_graph`: **No.** Provider/model selection must happen BEFORE the
graph's LLM and agent nodes are constructed; a graph cannot choose the
provider of its own nodes. The change is a load-boundary primitive.

| candidate | source/position | class | verdict | precedent | is_this_a_graph | effort/risk |
| --- | --- | --- | --- | --- | --- | --- |
| CLI `--provider/--model` overriding root `defaults` at load; node pins win | author; judge concurs (frozen) | framework primitive / config boundary | **pursue** | FR-071/FR-230 (`defaults` is the graph-wide knob layer); FR-119 (declaration stays in YAML) | no | 0.5 d; risk: widening to arbitrary `defaults` keys — closed by keyword-only API |
| Reuse FR-231's `configurable.provider_override` after compilation | FR-231 / `bench_commands.py` 195–220 | runtime-config injection | **dissent recorded, not pursued** — the keys exist but `llm_nodes.py`/`agent.py` never read them (inert for these node kinds); repairing bench is out of scope (C-7) | FR-231 | no | 0 d to reuse, but does not work; repair = separate FR |
| Loader reads `YAMLGRAPH_PROVIDER` / `YAMLGRAPH_MODEL` env | os_infra position | ambient environment | reject — invisible in artifacts; `grep -rn 'DEFAULT_PROVIDER\|YAMLGRAPH_PROVIDER' yamlgraph/` → none exist today, and the judge forbids loader env reads | FR-890 R-6 (provenance must be recorded) | no | 0.2 d; risk: silent provider drift |
| Edit `research-route/graph.yaml` defaults to `azure` | subtractionist position | one-line config change | reject — moves the dependency to every future operator; FR-890 baselines ran on haiku; governed artifact (C-4) | FR-890, FR-767 | n/a | 0.1 d; risk: route contract change |
| Convert research-route `type: llm` nodes to `type: copilot` (as judge/author/review routes) | yamlgraph_native position | route re-platform | reject — 5 llm + 1 agent (librarian with tools) node; no copilot equivalent for the agent; alters the FR-890 route | FR-959/FR-960 (copilot backends) | yes (route graph) but out of scope | 2 d; risk: research quality shift |
| Rotate the Anthropic key | operator | zero-code | not chosen 2026-09-07 (operator decision); remains available and unaffected by this FR | — | no | 0 d; risk: recurs on next outage |

Disagreement preserved: the FR-231 row is a genuine conflict — the repo
already "has" an override that does not reach the nodes this FR needs.

## Implementation Record

- **RED** `6f40af69` — `tests/unit/test_fr1028_provider_model_override.py`,
  11 failed / 2 passed (the two no-flag paths pass by construction, AC-07 and
  the pair-unset half of AC-08). CAP-267 / REQ-YG-671, ARCHITECTURE row,
  fragment.
- **GREEN** — see the commit following RED. Deviations from the plan:
  - The override helper lives in a new `yamlgraph/compile/default_overrides.py`
    (`apply_default_overrides`) rather than inside `graph_loader.py`: the
    loader was at 434 lines and the addition crossed the 450-line gate.
  - `verify_artifact` in `research_preflight.py` was already CC 22 (grade D)
    on main; touching the file made the radon gate bite, so the per-row loop
    was extracted into `_check_row` (behaviour-preserving; the FR-890/1005/938
    suites are the witnesses).
  - Provenance stamp: `head -1 / echo / tail -n +2` into `$ARTIFACT.tmp` then
    `mv` — the line lands directly under the title, before the persona
    accounting lines.
- Observed, not fixed (out of scope): `tests/unit/test_ramp_installer.py::
  test_wrapper_delegates` shells `scripts/ramp.sh` → bare `python3`, so it
  fails in any shell where `.venv` is not on `PATH` (`ModuleNotFoundError:
  yaml`). Passes with the venv activated. Test-isolation defect to file
  separately; not caused by this change.
- Live witness (AC-10): pending — next step in this arc.

## Alternatives Considered

Superseded by § Research Record (judgement R-1) — the table there carries the
solution classes, positions, precedent, and the preserved FR-231 conflict.

## Related

- [FR-1027](FR-1027-org-ai-dossier-census.md) — blocked consumer
- [FR-890](FR-890-research-sole-route-closed-input-alternatives.md) research sole route;
  [scripts/research.sh](../scripts/research.sh);
  [examples/demos/research-route/graph.yaml](../examples/demos/research-route/graph.yaml)
- [yamlgraph/compile/graph_loader.py](../yamlgraph/compile/graph_loader.py)
