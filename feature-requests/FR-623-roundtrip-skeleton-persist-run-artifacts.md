# Feature Request: Persist round-trip skeleton run artifacts (P1-P3 outputs)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged (2026-06-30) — Authority GRANTED after folding 4 corrections (Corr 1 manifest model/provider sourced from env, not state; Corr 2 `artifacts` declared in `state:` block; Corr 3 microsecond run_id + disambiguator; Corr 4 redundant gitignore AC reworded). Scope frozen.
**Effort:** 0.5 day
**Requested:** 2026-06-30

## Summary

The round-trip skeleton (FR-610..613) produces four authored/derived artifacts in
state — `cast`, `briefs`, `book`, `coherence` — but persists **none** of them. Capturing a
run today means ad-hoc `--export-state` JSON dumps or scraping `--full` stdout (the P3 K=6
read had to redirect terminal output into `logs/p3-raw/*.log` by hand, and `briefs`
truncated in the console). Add a single deterministic persistence leaf tool to the tail of
the spine that writes each stage's result to a run-stamped artifact directory, so every run
is durable, inspectable, and demo-able without CLI gymnastics.

## Value Statement

Anyone running the skeleton (demos, the P3/P5 raw-output reads, regression diffs) gets a
durable, named, per-run artifact set on disk — `cast.json`, `briefs.json`, `book.md`,
`coherence.json`, `manifest.json` — instead of reconstructing results from scrollback.

## Problem

- The four state keys are computed and then discarded at process exit; only stdout (and
  optional `--export-state`, which dumps the *whole* state into one JSON blob) survives.
- The P3 Raw Output Read (FR-613) had to manually `> logs/p3-raw/<fixture>.log` each run and
  parse the console — and `briefs` truncated in `--full` output, so the richest authored
  artifact was the hardest to read.
- There is no record of *which premise / model / timestamp* produced a given result, so two
  draws of one premise (the Loom 0.40 vs 0.00 non-reproducibility) cannot be told apart
  after the fact.
- The skeleton's value is as an **instrument**; an instrument that does not record its
  readings cannot support reproducibility, diffing, or the variance check FR-622 now needs.

## Proposed Solution

Add one **deterministic leaf tool** `persist_run` (Python, side-effect layer — no LLM) and
wire it as the final node after `coherence_gate`. All flow stays in the graph YAML; the only
new Python is the leaf tool, consistent with the skeleton's three-layer discipline.

The tool writes a run-stamped directory under `outputs/roundtrip/<run_id>/`, where
`run_id = <UTC timestamp>-<8-char hash of premise>` (stable per premise+time, so reruns are
distinguishable and the Loom-style two-draw case is separable):

```
outputs/roundtrip/20260630T141205-832194Z-3f9ab210/
  manifest.json     # {premise, genre, provider, model, run_id, created_utc, chapter_count}
  cast.json         # state.cast (pretty-printed, stable key order)
  briefs.json       # state.briefs  -- the full authored arc, never truncated
  book.md           # state.book    -- assembled prose, as Markdown
  coherence.json    # state.coherence report
```

**Corr 3 (run_id precision):** the timestamp uses **microsecond** precision
(`%Y%m%dT%H%M%S-%f`) so two draws of one premise within the same second do not
collide; the 8-char premise hash disambiguates premises, the microsecond stamp
disambiguates draws. Do **not** use second granularity (the Loom 0.40-vs-0.00
two-draw case must be separable).

**Corr 1 (manifest provenance):** `provider`/`model` are **not in graph state** —
they come from the run environment (`PROVIDER`, `ANTHROPIC_MODEL`/`*_MODEL`). The
manifest sources them from `os.environ` at write time (recording `"(unset)"` when
absent), and notes that per-node model overrides (FR-622's strong-model authoring)
are not captured by a single field.

```yaml
# graphs/roundtrip_skeleton.yaml  (additions only -- spine unchanged)
tools:
  persist_run:
    type: python
    module: examples.plot_modeller.nodes.roundtrip_tools
    function: persist_run

# Corr 2: every explicit python state_key in this skeleton is declared in the
# `state:` block (cast/briefs/book/coherence). `artifacts` MUST be too, or the
# dynamic state builder will not allocate the key.
state:
  artifacts:
    type: dict
    description: "persist_run witness {run_dir, run_id, files: [...]}"

nodes:
  persist_run:
    type: python
    tool: persist_run
    state_key: artifacts        # {run_dir, run_id, files: [...]} witness

edges:
  - from: coherence_gate
    to: persist_run
  - from: persist_run
    to: END
```

```python
# examples/plot_modeller/nodes/roundtrip_tools.py  (new leaf)
def persist_run(state: dict[str, Any]) -> dict[str, Any]:
    """Deterministically write cast/briefs/book/coherence to a run-stamped dir.

    Side-effect leaf (no LLM). run_id = <UTC ts>-<premise hash>. Raises if a
    required artifact key is absent, so a broken upstream stage cannot silently
    produce an empty run dir.
    """
    # required keys present -> write manifest + 4 artifacts -> return {"artifacts": ...}
```

The output base honours an optional `YAMLGRAPH_ROUNDTRIP_OUT` env var (default
`outputs/roundtrip/`), so demos and CI can redirect without editing YAML.

## Acceptance Criteria

- [ ] `persist_run` leaf tool writes `manifest.json`, `cast.json`, `briefs.json`, `book.md`,
      `coherence.json` under `outputs/roundtrip/<run_id>/`.
- [ ] `briefs.json` contains the **full** authored arc (no truncation), pretty-printed with
      stable key order.
- [ ] `run_id` uses **microsecond** precision so two runs of the same premise in the same
      second do not collide; `manifest` records premise, genre, `provider`, `model` (from
      env, `"(unset)"` when absent), `run_id`, `created_utc`, and `chapter_count`.
- [ ] The tool **raises** if any of `cast`/`briefs`/`book`/`coherence` is missing (a broken
      upstream stage cannot yield a silent/empty run dir), mirroring `assemble_book`.
- [ ] `artifacts` is declared in the graph `state:` block (Corr 2); the dynamic state builder
      allocates it.
- [ ] Output base overridable via `YAMLGRAPH_ROUNDTRIP_OUT`; default `outputs/roundtrip/`.
- [ ] Graph lints clean and runs end-to-end on at least one fixture; the spine before
      `coherence_gate` is unchanged (additive only).
- [ ] Unit test covers: artifact files written, missing-key raise, and **distinct run_ids for
      two `persist_run` calls with the same premise** (microsecond stamp differs).
- [ ] No new gitignore rule needed — `outputs/` is already ignored (`.gitignore:38`); confirm
      `outputs/roundtrip/` is covered by that rule (do not add a redundant entry).

## Alternatives Considered

- **Keep using `--export-state`.** Rejected: it dumps one undifferentiated state blob, has no
  per-stage files, no manifest, no run stamping, and still requires the operator to remember
  the flag and a path each run. The demo/read pain (truncated `briefs`, manual log redirects)
  is exactly what this removes.
- **Per-stage persistence (write after each of P1/P2/P3).** Rejected for now: more nodes on
  the critical path for no extra value — a single tail tool reads all four finished state keys
  at once. Revisit only if mid-run crash recovery is needed.
- **Write artifacts from inside each LLM node.** Rejected: violates the three-layer split
  (side effects belong in a leaf tool, not in an `llm`/`map` node).

## Related

- Modifies: [roundtrip_skeleton.yaml](../examples/plot_modeller/graphs/roundtrip_skeleton.yaml),
  [roundtrip_tools.py](../examples/plot_modeller/nodes/roundtrip_tools.py)
- Skeleton spine: FR-610 (P0), FR-611 (P1 cast/briefs), FR-612 (P2 prose), FR-613 (P3 gate).
- Unblocks the FR-622 reproducibility/variance check (durable runs to diff across draws).
- Prior capture pain: `logs/p3-raw/*.log` (manual redirects);
  [plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md).
