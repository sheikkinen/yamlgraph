# Feature Request: Meta Self-Reflective Demo

**Priority:** LOW
**Type:** Feature
**Status:** Enforced (2026-06-02)
**Effort:** 1 day
**Requested:** 2026-06-02

## Enforcement (2026-06-02)

Implemented via TDD (RED commit `811a80e5`, GREEN to follow). Files:
`examples/demos/meta/{graph.yaml,prompts/meta_transform.yaml,demo.sh,README.md}`,
`tests/unit/test_fr464_meta_demo.py` (16 tests, REQ-YG-467), `capabilities/CAP-166`.

**Deviation from plan:** the `read_file` shell-tool placeholder was named `{target}`
rather than `{file}`. The E001 linter requires shell-tool command placeholders to be
declared in state and only exempts *agent* tools, not tool-node `variables:` mappings.
Renaming to `{target}` (already a state field) satisfies the linter without inventing
a phantom `file: str` state field. Logged as a seed in the diary (linter could learn
that `type: tool` nodes resolve their own command placeholders).

Self-referential headline verified: `./examples/demos/meta/demo.sh` runs the demo
against its own `graph.yaml` and returns a typed `MetaResult` (see `demo-output.log`).

## Summary

A small `examples/demos/meta/` demo that applies a natural-language verb to a code
artifact — including the demo's own graph YAML. It is a typed, traced homage to the
2023 `meta.js` trick (`node meta 'explain structure' ./meta.js`), closing the loop
from trust-by-default Unix pipe to a verified YAMLGraph pipeline.

## Value Statement

Demo users learn the canonical "LLM as a code transformer" pattern — explain,
improve, document, test — expressed as a single reusable graph whose verb and target
are variables, proving the framework can reason about its own configuration.

## Problem

The "apply a verb to some code" pattern (explain / improve / restyle / simplify /
test / document / debug) is the most common first contact developers have with LLMs,
yet there is no minimal demo showing it done the YAMLGraph way: verb-as-variable,
prompt-in-YAML, typed output, traceable run. The historical reference implementation
(`meta.js`, 2023) piped raw model output straight to the filesystem with no boundary,
no verification, and no type — exactly the naïveté our doctrine exists to correct.

## Proposed Solution

A single graph parameterized by `verb` (the instruction) and `target` (a file path).
The graph reads the target file via a tool, runs one LLM node with a YAML prompt, and
returns structured output.

```bash
yamlgraph graph run examples/demos/meta/graph.yaml \
  --var verb="explain structure" \
  --var target=examples/demos/meta/graph.yaml \
  --full
```

```yaml
# examples/demos/meta/graph.yaml (sketch)
prompts_relative: true
prompts_dir: prompts
variables:
  verb: { type: str, description: "Natural-language instruction" }
  target: { type: str, description: "Path to the code artifact" }
tools:
  read_file:
    type: shell
    command: cat {file}
    description: "Read a project file in full."
    parse: text
nodes:
  load:
    type: tool
    tool: read_file
    args: { file: "{target}" }
    state_key: source
  transform:
    type: llm
    prompt: meta_transform
    state_key: result
```

The `read_file` tool follows the established `judge`/`enforcer` demo convention
(`type: shell, command: cat {file}`); runtime vars are escaped via `shlex.quote`.
The `meta_transform` prompt carries an inline schema (e.g. `summary`, `findings`,
`suggested_code`) so the output is typed rather than free text. The self-referential
case — pointing `target` at the graph's own YAML — is the headline demo.

## Acceptance Criteria

- [x] `examples/demos/meta/graph.yaml` runs `verb` × `target` and returns typed output
- [x] `prompts/` (or demo-local) `meta_transform.yaml` with inline schema, no hardcoded prompt
- [x] `read_file` defined as a shell tool (`cat {target}`) per `judge`/`enforcer` convention; runtime vars escaped via `shlex.quote` (filesystem traversal hardening deferred to framework per FR-463)
- [x] Self-referential run (`target` = the graph's own YAML) succeeds and is the documented example
- [x] `demo-output.log` committed proving the demo was executed (demo-gate)
- [x] `README.md` in the demo folder explains the `meta.js` lineage and the typed/traced upgrade
- [x] Tests added with `@pytest.mark.req` linking to the demo's REQ-YG-467
- [x] Capability file `capabilities/CAP-166-meta-demo.yaml` created
- [x] Diary reflection added (diary-gate)

## Alternatives Considered

- **Shell-script port of `meta.js`**: faithful to the original but reproduces its
  trust-by-default flaws and teaches nothing about YAMLGraph. Rejected.
- **Multi-node verb router** (one node per verb): over-engineered; a single
  parameterized prompt covers all verbs. Rejected per implementation discipline.
- **Write transformed output back to disk** (`| tee`): reintroduces the unbounded
  filesystem boundary the original suffered from. Output stays in structured state;
  the caller decides what to persist.

## Judgement (2026-06-02)

**Verdict: Accepted with refinements. Scope frozen.**

Verified against codebase. One defect corrected: the original sketch declared a
project-root-bounded `read_file` Python tool that does not exist. Sibling demos use
an inline shell tool (`cat {file}`), and FR-463 explicitly deferred path-traversal
hardening of that tool as out-of-scope framework work. The solution and acceptance
criteria were amended to match the established shell-tool convention; the boundary
statement now reflects what is actually achievable (shlex escaping; traversal deferred).
Node type `type: tool` confirmed valid via `node_factory/tool_nodes.py`. Demo-local
prompts pinned (`prompts_relative: true`). Remaining scope is minimal and internally
consistent. Authority granted to Enforce.

## Related

- Confluence: "OpenAI Prompts for Developers" (2023-01-30), `meta.js` by Santiago Valdarrama
- `examples/demos/judge/`, `examples/demos/enforcer/` — typed-output shell-tool demos to mirror
- `feature-requests/FR-463-enforcer-demo-safety-hardening.md` — `cat {file}` traversal deferral
- `yamlgraph/node_factory/tool_nodes.py` — `type: tool` node contract
- `reference/getting-started.md` — demo conventions
