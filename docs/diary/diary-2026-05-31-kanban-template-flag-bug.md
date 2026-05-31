# Diary: Kanban View Template Flag Bug

**Date:** 2026-05-31
**Context:** Investigating why Kanban view is not activated for ninchat_voice

## The Bug

The WebSocket monitor's Kanban view is not activated for `voice_coordinator` machines. The view routing in `app-modular.js` checks `metadata?.template === true` from the config metadata served by the diagram server.

### Root Cause (two issues)

**Issue 1: Template flag at wrong YAML level**

`voice_coordinator.yaml` has `template: true` nested under `metadata:`:

```yaml
metadata:
  name: "Voice Coordinator"
  machine_name: voice_coordinator
  template: true       # ← nested under metadata
```

But `diagrams.py:generate_metadata()` reads it from the top level:

```python
"template": config.get("template", False)  # line 815 — reads top level only
```

The working config (`patient-records.yaml`) has it at top level:

```yaml
template: true  # ← top level
name: "patient-records"
```

**Issue 2: No diagrams generated**

`docs/fsm-diagrams/voice_coordinator/` does not exist. The diagram server (`server.cjs`) serves metadata from `docs/fsm-diagrams/<config_type>/metadata.json`. Without this directory, the `/api/diagram/voice_coordinator/metadata` endpoint returns 404 → `isKanbanMachine()` returns false → diagram view shown instead.

### Fix Required (not applied)

Coordinated changes across two repos:

1. **statemachine-engine** (`diagrams.py`): `generate_metadata()` should check both `config.get("template")` and `config.get("metadata", {}).get("template")` — normalize at the boundary.
2. **yamlgraph** (`voice_coordinator.yaml`): Move `template: true` to top level to match `patient-records.yaml` convention.
3. **Generate diagrams**: Run `generate_diagram_files()` for voice_coordinator to create `docs/fsm-diagrams/voice_coordinator/metadata.json`.

### Why Not Fixed Now

- ninchat_voice is not currently deployed or in active use
- Fix requires coordinated changes in statemachine-engine (diagrams.py) and yamlgraph (voice_coordinator.yaml)
- Diagram generation needs to run from statemachine-engine context

## Trap

`downstream_fix` — the symptom is "Kanban not showing" but the root cause is a boundary normalization failure in `generate_metadata()`. The YAML config uses a reasonable nesting (`metadata.template`), but the code only reads the top level. Normalize at the boundary.

## Heuristic

When a config flag works for one machine but not another, diff the working config against the broken one before reading any code. The structural difference (top-level vs nested) would have been visible in 10 seconds.

## Seed

Should statemachine-engine's YAML schema be validated with a JSON Schema or Pydantic model, the way yamlgraph validates `GraphConfig`? That would catch placement mismatches at load time rather than at view-routing time.
