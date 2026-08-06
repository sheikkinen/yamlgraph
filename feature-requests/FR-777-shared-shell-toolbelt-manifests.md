# Feature Request: Shared Shell Toolbelt Manifests (First Shell-Runtime Manifest Consumers)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced 2026-08-06 — all 10 ACs met; see Implementation Status
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

## Assumption: Research Graph as a Toolbelt Tool (Direction, Not Scope)

The toolbelt is designed on the assumption that its next resident is a
**graph-runtime manifest**: the research graph published as
`examples/shared/toolbelt/research.tool.yaml` (`runtime.type: graph`).

- **Assumed first consumer:** the judge_fr adapter graph
  (`.github/skills/judge-fr/adapters/graph.yaml`), invoking research as
  an optional branch — e.g. fired when the FR's Prior-art section is
  empty or the judge's confidence in precedent coverage is low.
- **Rationale:** Commandment 1 requires research before coding, but in
  practice research is seldom done and never automatically. Every other
  Sermon step has mechanical enforcement (Judge → adapter graph,
  Enforce → hooks/CI, Distill → diary-gate); Research has none. A
  manifest tool makes research mechanically invocable from the graphs
  that need it, closing the only unenforced Sermon step.
- **Consequence for this FR:** the directory contract is
  `examples/shared/toolbelt/` = shared *agent tools of any runtime
  type*, not "shell manifests" — naming, README wording, and tests must
  not assume shell-only. The research manifest itself, and any judge_fr
  branch, are a separate FR (it also witnesses the graph runtime,
  completing FR-768's runtime coverage).

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
- **research-agent / code-analysis / meta demos are OUT of scope** for
  shell-tool conversion. Their shell tools are variants, not verbatim
  copies; converting them would require the same semantic unification.
  The research *graph itself* is the assumed next toolbelt resident — as
  a graph-runtime manifest, per the Assumption section — in a follow-up
  FR.

## Constraints

- C-1: No files under `yamlgraph/` change (translation layer exists;
  REQ-YG-574 path semantics already cover
  manifest-relative resolution).
- C-2: Governed artifacts (`examples/**/graph.yaml`) are authored solely
  via `scripts/author.sh <task-brief.md>` (FR-767); manifests themselves
  are not governed paths but follow the same brief for coherence if the
  adapter run covers them, else are written directly with header-comment
  precedent.
- C-3: Effective shell-tool equivalence (R-2): the regression test
  compares the effective parsed shell config — `command`, canonical
  `description`, `parse`, and `timeout` — for each shared tool against
  the manifest contract, proving `timeout == 30` unless a manifest
  intentionally sets another value. Raw expanded-dict byte equality is
  NOT required (manifest translation adds the explicit default
  `timeout: 30` that inline parsing also defaults to); effective runtime
  equivalence is the contract. Only documented delta: the canonical
  `search` description union.
- C-4: Demo-specific tools remain inline; the toolbelt contains only the
  four ×3-duplicated tools. No speculative additions.
- C-5: `demo-gate` compliance: each converted demo ships a regenerated
  successful `demo-output.log` in the same commit; intentional-failure
  sections, if any, go to `demo-witness.log` (demo-proof-check rejects
  fatal markers — hook lesson 2026-08-05).
- C-6: `capabilities/CAP-220-shared-shell-toolbelt.yaml` with
  `REQ-YG-579` (R-3: exact next-free IDs, verified free 2026-08-06;
  if another merge consumes them before enforcement, revise to the
  actual next-free pair first). All new tests carry
  `@pytest.mark.req("REQ-YG-579")`.
- C-7: Human-review gate (R-1): planner, enforcer, and judge participate
  in the plan/judge/enforce workflow — the migrated graph/toolbelt diff
  requires human review before merge, per judge doctrine on
  enforcement-infrastructure changes and the FR-768 judgement's
  condition for these exact graphs. Advisory output is not merge
  authority.
- C-8: If enforcement discovers a shell manifest translation gap
  requiring `yamlgraph/` changes, stop and file a separate bug FR; this
  FR may not repair the runtime (judgement C-5).

## Acceptance Criteria

(Revised per judgement 2026-08-06 — this set supersedes the proposal's.)

- [ ] AC-01: `examples/shared/toolbelt/{read_file,search,list_dir,git_log}.tool.yaml`
      exist, validate against `ToolManifest` with unknown fields
      rejected, and each declares `runtime.type: shell`.
- [ ] AC-02: planner, enforcer, and judge `graph.yaml` reference all four
      shared tools via `manifest:` keys; zero inline copies of
      `cat {file}`, `rg -n --glob {glob} {pattern} .`, `ls {dir}`, and
      `git log --oneline --all --grep={pattern}` remain in those three
      graph files.
- [ ] AC-03: A committed test loads each converted graph and proves the
      effective shell config for each shared tool matches the canonical
      manifest contract: `command`, canonical `description`, `parse`,
      and `timeout == 30`.
- [ ] AC-04: The canonical `search` description contains the union of
      the three previously drifted glob example lists.
- [ ] AC-05: Demo-specific tools remain inline: planner `write_file`,
      enforcer `git_diff`/`lint`/`run_tests`/edit-write helpers, and
      judge `run_tests` are not moved into the toolbelt.
- [ ] AC-06: `yamlgraph graph lint` passes for planner, enforcer, and
      judge; the governed graph edits are authored via
      `scripts/author.sh` and the validation artifact records lint and
      smoke evidence.
- [ ] AC-07: Each converted demo has a regenerated successful
      `demo-output.log` committed with the graph change and no
      fatal-marker-only witness substituted for success.
- [ ] AC-08: `capabilities/CAP-220-shared-shell-toolbelt.yaml` with
      `REQ-YG-579` is added (or the exact next-free pair if revised
      before enforcement); every new or changed test has an exact
      `@pytest.mark.req(...)` marker and
      `python scripts/req_coverage.py --strict` passes.
- [ ] AC-09: `examples/shared/README.md` documents
      `examples/shared/toolbelt/` as shared agent tools of any manifest
      runtime type, with the fit boundary "verbatim two-plus-consumer
      contracts earn manifests; demo-local variants stay inline."
- [ ] AC-10: No files under `yamlgraph/` change; no research graph
      manifest or judge adapter branch is added; changelog fragment, FR
      implementation status, and diary reflection are included.

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

## Implementation Status (2026-08-06)

**Commits:** RED `bd61e66f` (21-test suite `tests/unit/test_fr777_shell_toolbelt.py` + CAP-220/REQ-YG-579); GREEN follows in the same push (manifests, converted graphs, witnesses, docs).

**Route (C-2):** conversion executed via `scripts/author.sh`; `tmp/draft-authoring-report.md` recorded lint 0 errors (3 pre-existing W026 warnings), per-graph validate passed, 21/21 FR-777 tests green.

**AC checklist:**
- AC-01 ✅ four manifests in `examples/shared/toolbelt/`, all validate under `ToolManifest` (extra=forbid).
- AC-02 ✅ planner/enforcer/judge reference the four tools purely by `manifest:`; zero inline copies remain (test-asserted).
- AC-03 ✅ effective-config equivalence test: command, description, `parse: text`, `timeout == 30` via `load_graph_config` + `parse_tools`.
- AC-04 ✅ `search` description is the canonical union of the three drifted copies; union-extension comment in the manifest.
- AC-05 ✅ demo-specific tools (planner `write_file`; enforcer `git_diff`/`lint`/`run_tests`/`write_file`/`edit_file`; judge `run_tests`) stay inline (test-asserted).
- AC-06 ✅ lint + author.sh evidence per report above.
- AC-07 ✅ all three `demo-output.log` regenerated from live successful runs (PROVIDER=google, gemini-3.5-flash), zero fatal markers, success marker present; no witness substitution. Note: `.env` pins `PROVIDER=deepseek`, which — like anthropic — timed out on the planner's large context (ARCHITECTURE.md grew ~263KB since the 2026-05-29 witness); google completed all runs. A wrapper heredoc bug (stdin hijack → broken pipe) produced one false failure before the provider was exonerated.
- AC-08 ✅ CAP-220 + REQ-YG-579 registered; `scripts/req_coverage.py --strict` green; ARCHITECTURE.md regenerated via `aggregate_capabilities.py`.
- AC-09 ✅ `examples/shared/README.md` toolbelt section (runtime-neutral wording, fit boundary, union rule).
- AC-10 ✅ no `yamlgraph/` changes; no research manifest; changelog fragment `changelog/unreleased/fr-777-shell-toolbelt.md`; diary entry included.

**C-7 (human-review gate):** planner/enforcer/judge are enforcement-adjacent demos; the conversion diff is presented for human review at merge — advisory note honored, no self-merge.

**C-8:** no manifest→shell-config translation gap was found; `manifest.py` untouched.

**Deviations (in-scope test updates, no production change):**
- Four legacy demo-structure tests (FR-447/452/462/463) asserted the raw inline `type: shell` shape the conversion intentionally replaced; updated to accept toolbelt `manifest:` refs while keeping tool counts/names exact.
- `test_changelog_req_cross_wiring._build_fr_to_reqs` treated a comma-list `fr:` field (CAP-218: `FR-773, FR-774, FR-775`) as a single key, so those FRs mapped to no capability once this FR's fragment made the REQ multiply-claimed; fixed at the parse boundary by splitting the list. Test-infrastructure fix, not a `yamlgraph/` change.

## Related

- feature-requests/FR-777-shared-shell-toolbelt-manifests.judgement.md — verdict APPROVED WITH REVISIONS (2026-08-06); scope table and conditions govern enforcement
- FR-768 — tool manifests (shipped the shell runtime this FR witnesses)
- FR-770 — first python manifest consumer (precedent for "first consumer" framing)
- FR-773 / FR-776 — `split_document` / `render_page` manifest precedents
- docs/diary/diary-2026-08-05-was-the-manifest-worth-it.md — census that found the gap; its Seed (zero-consumer surface sweep) is partially answered by this FR
- examples/demos/{planner,enforcer,judge}/graph.yaml lines 10–32 — the duplicated blocks
- .github/skills/judge-fr/adapters/graph.yaml — assumed first consumer of the follow-up research graph-tool manifest
- examples/demos/research-agent/ — the graph assumed to be published as a toolbelt tool
- yamlgraph/tools/manifest.py — translation layer (unchanged by this FR)
