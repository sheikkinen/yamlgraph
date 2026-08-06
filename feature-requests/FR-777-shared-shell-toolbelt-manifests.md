# Feature Request: Shared Shell Toolbelt Manifests (First Shell-Runtime Manifest Consumers)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5–1 day
**Requested:** 2026-08-06
**Prior art:** FR-768 (tool manifests — shipped shell/python/graph runtimes), FR-770 (first committed python manifest consumer), FR-773/FR-776 (`split_document` / `render_page` python manifests), diary 2026-08-05 "Was the Manifest Worth It?" (census: shell manifest runtime has ZERO committed consumers)

## Summary

Extract the four shell tools duplicated verbatim across the three doctrine
agent demos (planner, enforcer, judge) into shared tool manifests under
`examples/shared/toolbelt/`, and convert all three demos to consume them.
This lands the first committed **shell-runtime** manifest consumers,
closing the unwitnessed-surface gap found in the 2026-08-05 manifest
census — with real, pre-existing duplication (and already-observed
description drift) as the value statement, not a manufactured witness.

## Value Statement

Demo authors and the agents reading these tool descriptions get one
canonical contract per toolbelt tool instead of three drifting copies;
FR-768's shell manifest runtime gets its first honest witness.

## Ideal Result

Every doctrine agent demo declares its common read-only toolbelt with one
line per tool (`manifest: ../../shared/toolbelt/<name>.tool.yaml`); the
agent-facing description of `search` (and each other shared tool) exists
in exactly one file; a change to a toolbelt contract propagates to all
consumers at graph load with zero re-declaration; and the FR-768 shell
runtime is exercised by committed, running graphs rather than only unit
tests.

## Problem

Census (2026-08-06, `grep` over `examples/demos/*/graph.yaml`):

1. **Verbatim ×3 duplication.** Four shell tools are declared identically
   in `examples/demos/planner/graph.yaml`,
   `examples/demos/enforcer/graph.yaml`, and
   `examples/demos/judge/graph.yaml` (lines 10–32 of each):
   - `read_file` — `cat {file}`
   - `search` — `rg -n --glob {glob} {pattern} .`
   - `list_dir` — `ls {dir}`
   - `git_log` — `git log --oneline --all --grep={pattern}`

2. **Drift has already happened.** The `search` description's glob
   examples differ across all three graphs (planner:
   `capabilities/*.yaml`; enforcer: `tests/**/*.py`; judge: both). These
   descriptions are agent-facing contracts — the LLM chooses arguments by
   reading them — so drift silently changes agent behavior per demo.

3. **FR-768's shell manifest runtime is unwitnessed.** The manifest
   feature shipped three runtime types; committed consumers exercise
   python only (FR-770, FR-773, FR-776). `demo_vs_test`: unit tests prove
   the shell translation, but no committed graph proves the abstraction
   is worth having. This FR is the witness — extraction of existing
   duplication, exactly the test the runtime has failed until now.

## Proposed Solution

### 1. Four shell manifests in `examples/shared/toolbelt/`

One manifest per duplicated tool, following the header-comment precedent
of `split_document.tool.yaml` / `render_page.tool.yaml` (contract comment,
first-consumer note, FR references):

```yaml
# examples/shared/toolbelt/search.tool.yaml
# Tool manifest (FR-768) — shared agent toolbelt (FR-777).
# First committed shell-runtime manifest consumers:
#   examples/demos/planner, examples/demos/enforcer, examples/demos/judge.
name: search
description: "Search files matching a glob pattern. Examples: --glob 'ARCHITECTURE.md', --glob 'feature-requests/*.md', --glob 'yamlgraph/**/*.py', --glob 'tests/**/*.py', --glob 'capabilities/*.yaml'."
runtime:
  type: shell
  command: rg -n --glob {glob} {pattern} .
  parse: text
```

Analogous manifests for `read_file` (`cat {file}`), `list_dir`
(`ls {dir}`), and `git_log`
(`git log --oneline --all --grep={pattern}`).

**Drift resolution decision:** the canonical `search` description is the
union of the three drifted glob example lists (judge's copy is already
the superset). Recorded here so the Judge can veto rather than discover
it in the diff.

### 2. Convert all three consumers (no partial remediation)

In each of planner/enforcer/judge `graph.yaml`, replace the four inline
declarations with:

```yaml
tools:
  read_file:
    manifest: ../../shared/toolbelt/read_file.tool.yaml
  search:
    manifest: ../../shared/toolbelt/search.tool.yaml
  list_dir:
    manifest: ../../shared/toolbelt/list_dir.tool.yaml
  git_log:
    manifest: ../../shared/toolbelt/git_log.tool.yaml
```

Demo-specific tools stay inline where they belong (planner's
`write_file`, enforcer's `git_diff`, judge's `run_tests`) — the fit
boundary from the manifest census: manifests only for tools crossing the
directory boundary with ≥2 consumers.

`partial_remediation` applies: converting one demo and leaving two
verbatim copies would preserve the drift channel this FR exists to close.
All three convert in this FR.

### 3. Scope discipline

- **No new runtime code.** FR-768's translation layer
  (`yamlgraph/tools/manifest.py`) already supports shell runtimes
  (`command`, `parse`, `timeout`); this FR is manifests + graph edits +
  tests + docs only. If translation gaps surface, that is a separate
  bug FR.
- **`pytest` variants are OUT of scope.** The two `run_tests` variants
  (judge `--tb=short` vs code-analysis `--tb=no | tail`) differ
  deliberately per purpose; unifying them is a semantic decision, not an
  extraction, and dies here by `junk_drawer_cap` reasoning.
- **research-agent / code-analysis / meta demos are OUT of scope.** Their
  shell tools are variants, not verbatim copies; converting them would
  require the same semantic unification. A follow-up may extend the
  toolbelt if genuine reuse appears.

## Constraints

- C-1: No files under `yamlgraph/` change (translation layer exists;
  REQ-YG-574 path semantics already cover
  manifest-relative resolution).
- C-2: Governed artifacts (`examples/**/graph.yaml`) are authored solely
  via `scripts/author.sh <task-brief.md>` (FR-767); manifests themselves
  are not governed paths but follow the same brief for coherence if the
  adapter run covers them, else are written directly with header-comment
  precedent.
- C-3: Byte-for-byte behavior: each converted graph's translated tool
  declarations must equal the prior inline declarations (modulo the
  documented `search` description unification) — verified by test, not
  eyeballed.
- C-4: Demo-specific tools remain inline; the toolbelt contains only the
  four ×3-duplicated tools. No speculative additions.
- C-5: `demo-gate` compliance: each converted demo ships a regenerated
  successful `demo-output.log` in the same commit; intentional-failure
  sections, if any, go to `demo-witness.log` (demo-proof-check rejects
  fatal markers — hook lesson 2026-08-05).
- C-6: New CAP file + REQ-YG-XXX; all new tests carry
  `@pytest.mark.req`.

## Acceptance Criteria

- [ ] AC-01: `examples/shared/toolbelt/{read_file,search,list_dir,git_log}.tool.yaml`
      exist, validate against the `ToolManifest` schema
      (`extra=forbid`), and each declares `runtime.type: shell`.
- [ ] AC-02: planner, enforcer, and judge `graph.yaml` reference all four
      via `manifest:` keys; zero inline copies of the four commands
      remain in any of the three graphs (grep-witnessed in a test).
- [ ] AC-03: A unit test loads each converted graph and asserts the
      translated tool declarations (command, parse, description) match
      the canonical manifest contract — proving translation, not just
      file presence (substance_over_presence).
- [ ] AC-04: The canonical `search` description contains the union of
      the three previously drifted glob example lists.
- [ ] AC-05: Each converted demo runs successfully end-to-end;
      regenerated `demo-output.log` (success markers only) committed with
      the graph change.
- [ ] AC-06: `yamlgraph graph lint` passes on all three converted graphs.
- [ ] AC-07: New `capabilities/CAP-XXX-shared-shell-toolbelt.yaml` with
      REQ-YG-XXX; tests tagged; `req_coverage --strict` green.
- [ ] AC-08: `examples/shared/README.md` documents the toolbelt directory
      and the fit boundary (verbatim ×2+ duplication earns a manifest;
      demo-local variants stay inline).
- [ ] AC-09: No changes under `yamlgraph/`; changelog fragment in
      `changelog/unreleased/`; diary entry committed.

## Alternatives Considered

- **Convert only one demo (original brainstorm shape, "e.g.
  research-agent").** Rejected twice over: research-agent's shell tools
  are variants, not copies (weaker witness), and single-demo conversion
  leaves the ×3 drift channel open (`partial_remediation`).
- **Unify the pytest `run_tests` variants into the toolbelt.** Rejected:
  the variants differ semantically per demo purpose; unification is a
  design decision beyond extraction and would manufacture a fifth
  manifest to hit "4–5" — `growth_as_default`.
- **Do nothing / retire the shell manifest runtime (FR-465-style).**
  Considered honestly per the census diary: retirement would be correct
  if no real duplication existed. It does — ×3 verbatim with live drift —
  so extraction beats amputation here.
- **Python wrapper tools instead of shell manifests.** Rejected: wrapping
  `cat`/`rg`/`ls` in Python adds indirection without value; the shell
  runtime exists precisely for this shape.

## Related

- FR-768 — tool manifests (shipped the shell runtime this FR witnesses)
- FR-770 — first python manifest consumer (precedent for "first consumer" framing)
- FR-773 / FR-776 — `split_document` / `render_page` manifest precedents
- docs/diary/diary-2026-08-05-was-the-manifest-worth-it.md — census that found the gap; its Seed (zero-consumer surface sweep) is partially answered by this FR
- examples/demos/{planner,enforcer,judge}/graph.yaml lines 10–32 — the duplicated blocks
- yamlgraph/tools/manifest.py — translation layer (unchanged by this FR)
