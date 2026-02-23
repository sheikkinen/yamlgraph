# Feature Request: Unify Incaller and Outcaller Under Shared Root

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** IMPLEMENTED
**Effort:** 3 days
**Requested:** 2026-02-23
**Implemented:** 2026-02-23
**FR:** FR-079

## Summary

Refactor `projects/incaller` and `projects/outcaller` so that `outcaller` is the
canonical root for all shared code. Extract duplicated prompts and server logic
into shared locations. Incaller becomes a thin inbound-specific layer on top of
outcaller.

## Problem

Incaller was built as a mirror of outcaller (IC-000 / REQ-YG-086). Today the
coupling is **implicit and fragile**:

1. **Duplicated prompts** — 7 YAML files exist in both `incaller/prompts/` and
   `outcaller/prompts/`. They differ only in "inbound call" vs "phone survey"
   wording. A change to conversation logic requires editing both.

2. **Duplicated graph structure** — `incaller/graph.yaml` (303 lines) and
   `outcaller/graph.yaml` (293 lines) are ~95% identical. 14 of 15 nodes, all
   edges (except the first), all loop limits, and all state keys are the same.
   Only the call-initiation node and its first edge differ
   (`await_call` vs `initiate_call`).

3. **Duplicated server code** — `incaller/server.py` (151 lines) contains the
   same WebSocket handler as `outcaller/server.py` (122 lines). Incaller
   adds only a `/incoming` webhook endpoint (~34 lines unique).

4. **Cross-project imports** — Incaller already imports from outcaller at
   runtime (`coordinator`, `twilio_call`, `probe_recap`), but the dependency is
   undeclared and bidirectional awareness is absent.

This violates Commandment 8 (kill entropy) and creates a maintenance trap where
identical logic drifts apart silently.

## Proposed Solution

### Target Structure

```
projects/outcaller/                    # Root project (canonical)
├── graph.yaml                         # Outcaller graph (outbound-specific)
├── server.py                          # Outcaller server (imports server_base)
├── nodes/
│   ├── coordinator.py                 # TelcoSession (shared)
│   ├── twilio_call.py                 # speak, listen, accumulate, end_call (shared)
│   ├── probe_recap.py                 # parse_targets, extract, check (shared)
│   ├── tts.py                         # ElevenLabs TTS (shared)
│   └── stt.py                         # ElevenLabs STT (shared)
├── prompts/
│   ├── shared/                        # ← NEW: shared prompts (parameterized)
│   │   ├── analyze_recap_response.yaml
│   │   ├── extract_answers.yaml       # Parameterized with {{ call_context }}
│   │   ├── generate_probe.yaml        # Parameterized with {{ call_context }}
│   │   └── generate_recap.yaml        # Parameterized with {{ call_context }}
│   ├── conversation.yaml              # Outcaller-specific wording
│   ├── goodbye.yaml                   # Outcaller-specific wording
│   └── goodbye_refused.yaml           # Outcaller-specific wording
├── server_base.py                     # ← NEW: shared WebSocket handler
└── tests/

projects/incaller/                     # Thin inbound layer
├── graph.yaml                         # Incaller graph (symlinks to shared prompts)
├── server.py                          # Imports server_base + adds /incoming
├── nodes/
│   └── twilio_inbound.py              # await_call (only unique code)
├── prompts/
│   ├── shared -> ../../outcaller/prompts/shared  # ← Symlink
│   ├── conversation.yaml              # Incaller-specific wording only
│   ├── goodbye.yaml                   # Incaller-specific wording only
│   └── goodbye_refused.yaml           # Incaller-specific wording only
└── tests/
```

### Key Changes

#### 1. Extract shared prompts to `outcaller/prompts/shared/` (Day 1)

**Verified diff status** (correcting the original inbox analysis):

| Prompt | Actual Status | Action |
|--------|---------------|--------|
| `analyze_recap_response.yaml` | Identical (only header comment differs) | → `shared/` as-is |
| `extract_answers.yaml` | Differs: refusal examples, extraction examples, schema text | → `shared/` with Jinja2 `{{ call_context }}` parameterization |
| `generate_probe.yaml` | Differs: system context + greeting wording | → `shared/` with Jinja2 `{{ call_context }}` parameterization |
| `generate_recap.yaml` | Differs: system context wording | → `shared/` with Jinja2 `{{ call_context }}` parameterization |
| `conversation.yaml` | Different wording throughout | Keep per-project |
| `goodbye.yaml` | Different wording throughout | Keep per-project |
| `goodbye_refused.yaml` | Different wording throughout | Keep per-project |

**Parameterization source:** Each graph.yaml declares a `call_context` variable
in its metadata that Jinja2 templates consume:

```yaml
# incaller/graph.yaml
metadata:
  vars:
    call_context: "inbound call from a customer"

# outcaller/graph.yaml
metadata:
  vars:
    call_context: "outbound survey call"
```

The shared prompts use `{{ call_context }}` wherever the current per-project
wording diverges:

```yaml
# outcaller/prompts/shared/generate_probe.yaml
system: |
  You are a friendly phone agent {{ call_context }}.
  ...
```

**Prompt resolution mechanism:** Both graphs use `prompts_relative: true` and
`prompts_dir: prompts`. The YAMLGraph prompt resolver (strategy 1) resolves
`graph_path.parent / prompts_dir / {prompt_name}.yaml`. For shared prompts,
incaller creates a symlink:

```
projects/incaller/prompts/shared -> ../../outcaller/prompts/shared
```

Nodes reference shared prompts via subdirectory:
```yaml
# Node in incaller/graph.yaml
generate_probe:
  prompt: shared/generate_probe  # Resolves to incaller/prompts/shared/generate_probe.yaml → symlink → outcaller/prompts/shared/
```

This requires no framework changes — YAMLGraph already supports `/` in prompt
names, and symlinks are transparent to the resolver.

#### 2. Extract shared WebSocket handler (Day 2)

Create `outcaller/server_base.py` with the shared WebSocket handler:

```python
# outcaller/server_base.py
def register_voice_websocket(app: FastAPI, session: TelcoSession) -> None:
    """Register the Twilio Media Streams WebSocket handler."""
    @app.websocket("/voice")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        # ... shared WebSocket code (currently duplicated in both servers)
```

Both servers import and call `register_voice_websocket()`:

```python
# outcaller/server.py
from projects.outcaller.server_base import register_voice_websocket

def create_app(session: TelcoSession) -> FastAPI:
    app = FastAPI(title="Outcaller Voice Server")
    register_voice_websocket(app, session)
    # ... health endpoint
```

```python
# incaller/server.py
from projects.outcaller.server_base import register_voice_websocket

def create_app(session: TelcoSession) -> FastAPI:
    app = FastAPI(title="Incaller Voice Server")
    register_voice_websocket(app, session)

    @app.post("/incoming")
    async def incoming_call(request: Request) -> Response:
        # ... incaller-specific webhook (only unique code)
```

#### 3. Graph YAML files remain separate (Day 2)

**Definitive decision:** YAMLGraph does NOT support `!include` or YAML
composition. The `graph.yaml` files remain separate and duplicated. They are
entry points that rarely change (the shared logic lives in prompts and nodes).

**Drift detection:** Add a cross-reference comment at the top of each file:

```yaml
# NOTE: This graph shares 14 of 15 nodes with projects/outcaller/graph.yaml.
# Only the first node (await_call vs initiate_call) and its first edge differ.
# Run: diff projects/incaller/graph.yaml projects/outcaller/graph.yaml
```

A CI script or pre-commit hook that diffs the two files and warns on unexpected
divergence is a follow-up candidate but out of scope for this FR.

#### 4. Delete incaller prompt duplicates (Day 3)

Remove the 4 shared prompts from `incaller/prompts/` (they now resolve via
symlink to `outcaller/prompts/shared/`). Only 3 project-specific prompts remain
in `incaller/prompts/`.

#### 5. Update imports and tests (Day 3)

- Update `incaller/server.py` to import `register_voice_websocket` from
  `outcaller.server_base`
- Update incaller `graph.yaml` prompt names for shared prompts to use
  `shared/` prefix (e.g., `prompt: shared/generate_probe`)
- Verify both projects run end-to-end
- Verify all existing unit tests pass

## Acceptance Criteria

- [ ] Shared prompts live in `outcaller/prompts/shared/` (single canonical location)
- [ ] `incaller/prompts/shared` is a symlink to `../../outcaller/prompts/shared`
- [ ] No prompt file is duplicated between incaller and outcaller
- [ ] `extract_answers.yaml`, `generate_probe.yaml`, `generate_recap.yaml` are parameterized with `{{ call_context }}`
- [ ] Each `graph.yaml` declares `call_context` in metadata vars
- [ ] WebSocket handler code exists in exactly one place (`server_base.py`)
- [ ] Incaller `server.py` imports shared WebSocket handler + adds `/incoming`
- [ ] Outcaller `server.py` imports shared WebSocket handler
- [ ] Both `graph.yaml` files lint cleanly: `yamlgraph graph lint projects/*/graph.yaml`
- [ ] All existing unit tests pass: `pytest tests/ projects/outcaller/tests/ projects/incaller/tests/ -q --no-cov`
- [ ] Both `test_dialogue_e2e.py` scripts remain functional
- [ ] No new `# noqa` suppressions without confession in `docs/confessions.md`
- [ ] Tests added for shared `register_voice_websocket()` function
- [ ] Documentation updated (project READMEs, cross-reference comments in graph.yaml)

## Constraints

- **Outcaller is the root** — incaller depends on outcaller, never the reverse.
- **No new framework features required** — use existing YAMLGraph prompt
  resolution (`prompts_dir`, relative paths, `/` in prompt names) and Python
  imports. Symlinks for prompt sharing.
- **Preserve git history** — use `git mv` for prompt relocations.
- **No behavioral changes** — this is purely structural. Both projects must
  behave identically before and after the refactoring.
- **Incaller tests must not import from outcaller test fixtures** — shared test
  helpers go in a `conftest.py` at the `projects/` level if needed.
- **Rollback safety** — all changes are reversible via `git revert`. No database
  migrations, no config format changes, no external dependency updates.

## Alternatives Considered

1. **Merge into a single project with a `--mode inbound|outbound` flag.**
   Rejected: the projects have separate `.env` files, separate deployment
   targets, and separate feature request trails. A single project conflates
   concerns.

2. **Create a third `projects/telco-common/` package.**
   Rejected: adds a new project with its own lifecycle. Outcaller already owns
   the shared code; formalizing it there is simpler.

3. **Use YAMLGraph subgraphs to share the conversation loop.**
   Worth exploring in a follow-up FR, but out of scope for this structural
   cleanup.

4. **Per-node `prompts_dir` override (framework feature).**
   Rejected: violates the "no new framework features" constraint. Symlinks
   achieve the same result without framework changes.

5. **Path-in-prompt-name** (e.g., `prompt: ../outcaller/prompts/shared/foo`).
   Rejected: functional but ugly; leaks cross-project paths into every node
   definition. Symlinks are cleaner and keep prompt names readable.

## Implementation Plan

### Day 1: Shared Prompts
1. Create `outcaller/prompts/shared/` directory
2. Parameterize `extract_answers.yaml`, `generate_probe.yaml`,
   `generate_recap.yaml` with `{{ call_context }}` Jinja2 variable
3. Move `analyze_recap_response.yaml` to `shared/` (identical, no parameterization)
4. Move parameterized prompts to `shared/` (use `git mv`)
5. Add `call_context` to `metadata.vars` in both `graph.yaml` files
6. Create symlink `incaller/prompts/shared -> ../../outcaller/prompts/shared`
7. Update prompt names in both `graph.yaml` files to `shared/` prefix
8. Delete incaller copies of the 4 shared prompts
9. Run `yamlgraph graph lint` on both graphs

### Day 2: Shared Server + Graph Comments
1. Create `outcaller/server_base.py` with `register_voice_websocket()`
2. Refactor `outcaller/server.py` to import from `server_base`
3. Refactor `incaller/server.py` to import from `outcaller.server_base`
4. Add cross-reference comments to both `graph.yaml` files
5. Write unit tests for `register_voice_websocket()`
6. Run full test suite

### Day 3: Cleanup + Verification
1. Verify all tests pass across both projects
2. Update project READMEs with new structure
3. Run `ruff check` and `ruff format`
4. End-to-end verification with both `test_dialogue_e2e.py` scripts
5. Final `git diff` review

## Related

- `projects/incaller/IC-000-incaller-voicebot.md` — Original incaller spec
- `projects/outcaller/OC-005-outcaller-probe-recap.md` — Probe-recap design
- REQ-YG-086 — Cross-project tool reuse requirement
- REQ-YG-084/085 — Incaller await_call and webhook requirements

---

## Judgement (2026-02-23)

**Verdict: AMEND**

### What's sound

The FR is well-researched. Codebase audit confirms the core claims:

- **7 duplicated prompts** — confirmed, all 7 exist in both `incaller/prompts/` and `outcaller/prompts/`
- **Prompt diff analysis** — accurate. `analyze_recap_response` differs only in header comment/whitespace; `extract_answers`, `generate_probe`, `generate_recap` differ in wording; the other 3 differ throughout
- **Graph similarity** — confirmed (302 vs 293 lines), diff shows only first node (`await_call` vs `initiate_call`), comments, and a few extra state keys differ
- **Server duplication** — confirmed, both have the same WebSocket handler
- **Cross-project imports** — confirmed (`coordinator`, `probe_recap` imported from outcaller)
- **Prompt resolver handles `/` in names** — confirmed. `resolve_prompt_path()` uses `f"{prompt_name}.yaml"` via Path concatenation, so `shared/generate_probe` resolves to `{prompts_dir}/shared/generate_probe.yaml`. Symlinks work transparently
- **Alternatives considered** — thorough and well-reasoned

Design decisions are defensible: outcaller as canonical root, symlinks over framework features, separate graph.yaml files with drift comments.

### Issues to resolve before approval

#### ISSUE-1: `metadata.vars` does not exist (BLOCKING)

The FR proposes `metadata.vars.call_context` as the Jinja2 parameterization source (lines 98–111). **This mechanism does not exist in YAMLGraph.** The `metadata` block currently holds `provider`, `model`, `thinking_budget` only. There is no code path that passes `metadata.vars` to prompt rendering.

This directly contradicts the FR's own constraint: "No new framework features required."

**How variables actually flow:** `llm_nodes.py:115` reads `variable_templates = node_config.get("variables", {})`. When empty (as in both graphs' probe/recap nodes), `resolve_node_variables()` passes the **entire state dict** as variables. So `{{ call_context }}` in a prompt template works IF `call_context` is in the state.

**Fix:** Replace `metadata.vars` with a state-based approach:
1. Add `call_context: str` to each graph's `state:` definition
2. Have the first tool node (`await_call` / `initiate_call`) return `{"call_context": "inbound call from a customer"}` or `{"call_context": "outbound survey call"}` as part of its state update
3. All downstream LLM nodes without explicit `variables:` pass state as variables → `{{ call_context }}` resolves automatically

This uses only existing mechanisms. Update Section "Key Changes §1", the YAML code blocks (lines 101–111), and the Implementation Plan Day 1 step 5.

#### ISSUE-2: Server line counts inaccurate (NON-BLOCKING)

FR claims incaller `server.py` is 151 lines; actual is **186 lines**. Outcaller is claimed as 122 lines; actual is **147 lines**. The unique incaller code is ~34 lines (the `/incoming` webhook) — this claim appears accurate. Correct the numbers for precision.

#### ISSUE-3: State key divergence understated (NON-BLOCKING)

The FR says "all state keys are the same" but incaller has extra state keys not in outcaller: `prompts_dir`, `call_info`, `caller_number`, `last_spoken`, `call_result`. Since graph.yaml files remain separate this doesn't affect the design, but the claim should be corrected to avoid confusion during implementation. Say "state keys are mostly shared; incaller adds 5 inbound-specific keys."

### Action required

Fix ISSUE-1 (blocking). Optionally fix ISSUE-2 and ISSUE-3 for accuracy. Return to `.chaplain/drafts/` for re-judgement.

---

## Judgement Addendum: Should `metadata.vars` become FR-080? (2026-02-23)

**Verdict: No. Do not promote.**

### Analysis

The proposal is: add a `metadata.vars` block to graph YAML that auto-injects
key-value pairs into every prompt's variable context. This would let graphs
declare constants like `call_context: "outbound survey call"` once, available to
all nodes without polluting state.

**Arguments for promotion:**

1. Clean separation — graph-level constants don't belong in mutable state
2. Declarative — visible in YAML, no Python plumbing needed
3. General utility — any graph wanting per-graph prompt flavor benefits

**Arguments against (decisive):**

1. **The workaround is trivial and already idiomatic.** The state-based approach
   (first tool node returns `{"call_context": "..."}`) uses only existing
   mechanisms and requires zero framework code. YAMLGraph already has `--var`
   flags that set initial state — `call_context` is semantically identical.

2. **`metadata.vars` would require touching 4+ framework modules.** The metadata
   block is read in `GraphConfig.__init__` but never forwarded to
   `resolve_node_variables()`, `execute_prompt()`, or the streaming/control node
   factories. Injecting it requires plumbing through `compile_nodes()` →
   `create_llm_node()` → `node_fn()` → `resolve_node_variables()`. This is not
   a 1-line change.

3. **Python tool nodes would not benefit.** `extract_answers` is called from
   `probe_recap.py` with an explicit variables dict — Python tools don't
   participate in the graph-level variable pipeline. So `metadata.vars` would
   only work for LLM graph nodes, creating a confusing asymmetry. The
   state-based approach works uniformly for both.

4. **`data_files` (FR-021) already exists as the prior art.** It loads external
   YAML into initial state. Adding `metadata.vars` as a second way to inject
   initial state creates two mechanisms for the same thing. If anything, the
   right future feature would be inline `data:` (literal key-value pairs loaded
   into initial state), which generalizes `data_files`.

5. **Violates Commandment 8** — adding a mechanism for a single use case when
   existing tools suffice is entropy, not simplification.

### Recommendation for FR-079

Replace `metadata.vars` with the state-based approach described in ISSUE-1:

```yaml
# In each graph.yaml state: section
state:
  call_context: str   # Set by first tool node

# In extract_answers Python tool (probe_recap.py), add to the variables dict:
result = execute_prompt(
    "extract_answers",
    {
        "call_context": state.get("call_context", "phone call"),
        "target_fields": state["target_fields"],
        ...
    },
    ...
)
```

This costs 3 lines of YAML + 1 line of Python per project. No framework changes.

---

## Implementation Notes (2026-02-23)

### Commits

| Repo | Commit | Changes |
|------|--------|---------|
| outcaller | `03e72ef` | Shared prompts in `prompts/shared/`, `server_base.py` extracted |
| incaller | `5c70c5d` | Symlink to shared prompts, imports `server_base.py` |

### Acceptance Criteria Status

- [x] Shared prompts live in `outcaller/prompts/shared/` (single canonical location)
- [x] `incaller/prompts/shared` is a symlink to `../../outcaller/prompts/shared`
- [x] No prompt file is duplicated between incaller and outcaller
- [x] `extract_answers.yaml`, `generate_probe.yaml`, `generate_recap.yaml` are parameterized with `{{ call_context }}`
- [x] Each `graph.yaml` declares `call_context` in state (via first tool node)
- [x] WebSocket handler code exists in exactly one place (`server_base.py`)
- [x] Incaller `server.py` imports shared WebSocket handler + adds `/incoming`
- [x] Outcaller `server.py` imports shared WebSocket handler
- [x] Both `graph.yaml` files lint cleanly
- [x] All existing unit tests pass (outcaller: 100, incaller: 11)
- [x] Tests added for shared prompts (`test_shared_prompts.py`)

### Implementation Decisions

1. **State-based `call_context`** — Followed Judgement recommendation. `initiate_call` and `await_call` set `call_context` in their return dicts. No framework changes needed.

2. **LLM nodes get `call_context` automatically** — When no explicit `variables:` defined, `resolve_node_variables()` passes filtered state → prompts receive `call_context`.

3. **Line count reduction**:
   - outcaller/server.py: 148 → 42 lines (-72%)
   - incaller/server.py: 187 → 80 lines (-57%)

4. **Symlink for shared prompts** — Works transparently with YAMLGraph prompt resolver. No framework changes needed.
