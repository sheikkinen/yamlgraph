# Judgement: FR-777 Shared Shell Toolbelt Manifests

**Prior art:** FR-768 (manifest feature + judgement's human-review condition for these graphs — honored as R-1/C-3), FR-770/FR-773/FR-776 (python manifest consumer precedents — first-consumer framing reused), diary 2026-08-05 manifest census (the negative-space finding this FR answers); no rejected FR occupies this territory.

**Verdict:** APPROVED WITH REVISIONS — the extraction is real, minimal, and architecture-aligned, but authority activates only after the FR adds the missing human-review gate, clarifies shell equivalence at the effective config boundary, and freezes traceability IDs.

**Reviewed against:** `feature-requests/FR-777-shared-shell-toolbelt-manifests.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; repo doctrine in `.github/copilot-instructions.md` as provided to this execution; `feature-requests/FR-768-tool-manifest-declaration-reuse.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.judgement.md`; `feature-requests/FR-770-vision-demo-consumes-manifest.md`; `feature-requests/FR-773-shared-document-splitter-manifest.md`; `feature-requests/FR-773-shared-document-splitter-manifest.judgement.md`; `feature-requests/FR-776-vision-fallback-scanned-pdf.md`; `feature-requests/FR-776-vision-fallback-scanned-pdf.judgement.md`; `docs/diary/diary-2026-08-05-was-the-manifest-worth-it.md`; `examples/demos/planner/graph.yaml`; `examples/demos/enforcer/graph.yaml`; `examples/demos/judge/graph.yaml`; `examples/shared/README.md`; `examples/shared/describe_image.tool.yaml`; `examples/shared/split_document.tool.yaml`; `examples/shared/render_page.tool.yaml`; `yamlgraph/tools/manifest.py`; `yamlgraph/tools/shell.py`; `yamlgraph/compile/graph_loader.py`; `tests/unit/test_tool_manifest.py`; `tests/unit/test_fr770_demo_manifest.py`; capability registry scan of `capabilities/CAP-*.yaml` for the current high-water mark (`CAP-219` / `REQ-YG-578`).

## What is sound

The problem is concrete. FR-777 identifies four shell tools duplicated across planner, enforcer, and judge (`feature-requests/FR-777-shared-shell-toolbelt-manifests.md:12-18`, `feature-requests/FR-777-shared-shell-toolbelt-manifests.md:63-70`), and the cited graphs confirm those inline declarations: planner has `read_file`, `search`, `list_dir`, and `git_log` at `examples/demos/planner/graph.yaml:11-34`; enforcer repeats them at `examples/demos/enforcer/graph.yaml:11-34`; judge repeats them at `examples/demos/judge/graph.yaml:11-34`. The drift claim is also real: the `search` description differs across planner, enforcer, and judge (`examples/demos/planner/graph.yaml:18-22`; `examples/demos/enforcer/graph.yaml:18-22`; `examples/demos/judge/graph.yaml:18-22`), so one canonical manifest removes an actual agent-facing contract split.

The scope is minimal and correctly uses an existing abstraction. FR-768 already defines `manifest:` as declaration reuse over existing runtimes, not a new execution engine (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:16-20`, `feature-requests/FR-768-tool-manifest-declaration-reuse.md:84-107`), and the implementation expands manifests at graph load (`yamlgraph/compile/graph_loader.py:63-64`) through typed Pydantic models with `extra="forbid"` (`yamlgraph/tools/manifest.py:22-70`). Shell manifest translation already maps to the inline shell shape (`yamlgraph/tools/manifest.py:79-89`), and shell parsing uses the same default `parse` and `timeout` values for inline tools (`yamlgraph/tools/shell.py:195-200`). No `yamlgraph/` change is needed for this FR.

The strategic classification is **Contrib/example**. The framework primitive is already shipped by FR-768; this FR supplies the first committed shell-runtime consumers and documents an examples-level shared toolbelt. That directly answers the diary's negative-space finding that shell and graph manifest runtimes had zero committed consumers (`docs/diary/diary-2026-08-05-was-the-manifest-worth-it.md:36-45`) while staying inside manifests, graph edits, tests, docs, changelog, and diary (`feature-requests/FR-777-shared-shell-toolbelt-manifests.md:141-181`).

The future graph-runtime direction is bounded well enough not to force a SPLIT. FR-777 explicitly treats the research graph as direction, not scope, and excludes the research manifest and judge branch from this FR (`feature-requests/FR-777-shared-shell-toolbelt-manifests.md:36-57`). Keeping `examples/shared/toolbelt/` runtime-neutral in naming and README wording is a useful design constraint, not an additional deliverable.

## Required revisions

### R-1: Add the human-review gate for planner/enforcer/judge migration

Fold a hard enforcement condition into the FR: because the planner, enforcer, and judge demos participate in the plan/judge/enforce workflow, the migrated graph/toolbelt diff requires human review before merge. FR-777 already requires governed graph edits to go through `scripts/author.sh` (`feature-requests/FR-777-shared-shell-toolbelt-manifests.md:164-168`), but it omits the separate human-review gate. That gate is required by judge doctrine for enforcement-infrastructure changes (`.github/skills/judge-fr/doctrine.md:96-103`) and by the governing FR-768 judgement for these exact graphs (`feature-requests/FR-768-tool-manifest-declaration-reuse.judgement.md:35-37`, `feature-requests/FR-768-tool-manifest-declaration-reuse.judgement.md:73-77`).

### R-2: Test effective shell-tool equivalence, including default timeout

Replace the ambiguous "byte-for-byte behavior" wording with an effective-config contract. FR-777 C-3 currently says each converted graph's translated tool declarations must equal the prior inline declarations byte-for-byte except for the search description (`feature-requests/FR-777-shared-shell-toolbelt-manifests.md:169-172`), while shell manifests translate with an explicit default `timeout: 30` (`yamlgraph/tools/manifest.py:82-89`) and inline shell parsing also defaults missing timeout to `30` (`yamlgraph/tools/shell.py:195-200`). A raw-dict byte comparison can therefore fail while runtime behavior is identical.

Fold this exact rule into the FR: the regression test must compare the effective `ShellToolConfig` or equivalent parsed fields for `command`, `description`, `parse`, and `timeout`, proving `timeout == 30` for these four tools unless a manifest intentionally sets another value. Raw expanded dict equality is not required; effective runtime equivalence is.

### R-3: Replace traceability placeholders with exact next IDs

Freeze the traceability surface before enforcement. FR-777 currently says "New CAP file + REQ-YG-XXX" (`feature-requests/FR-777-shared-shell-toolbelt-manifests.md:179-180`) and AC-07 repeats `CAP-XXX` / `REQ-YG-XXX` placeholders (`feature-requests/FR-777-shared-shell-toolbelt-manifests.md:200-201`). Repo doctrine requires concrete requirement markers on every test and a capability file for new capability work. The current registry high-water mark is `CAP-219` / `REQ-YG-578`, so this FR should reserve `capabilities/CAP-220-shared-shell-toolbelt.yaml` with `REQ-YG-579`, unless another merge consumes those IDs before enforcement; in that case the FR must be revised to the actual next-free exact IDs before implementation.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/shared/toolbelt/read_file.tool.yaml`, `search.tool.yaml`, `list_dir.tool.yaml`, and `git_log.tool.yaml` as shell-runtime `ToolManifest` files |
| D-2 | `examples/demos/planner/graph.yaml`, `examples/demos/enforcer/graph.yaml`, and `examples/demos/judge/graph.yaml` converted to manifest references for only those four shared tools |
| D-3 | Unit/artifact tests proving manifest schema validation, manifest-only graph entries, no remaining inline copies in the three target graphs, and effective shell-tool equivalence including timeout |
| D-4 | `examples/shared/README.md` documenting the runtime-neutral toolbelt boundary |
| D-5 | `capabilities/CAP-220-shared-shell-toolbelt.yaml` / `REQ-YG-579`, or exact next-free IDs if revised before enforcement |
| D-6 | Regenerated successful `demo-output.log` for planner, enforcer, and judge, plus graph lint evidence from the authoring route |
| D-7 | Changelog fragment, FR implementation status update, and diary reflection |

Not authorized: changes under `yamlgraph/`; changes to manifest schema or runtime translation; adding graph-runtime research manifests; modifying `.github/skills/judge-fr/adapters/graph.yaml`; converting research-agent, code-analysis, meta, or other demos; unifying `run_tests` variants; adding speculative tools to the toolbelt; changing hooks, CI, judge/review/authoring doctrine, provider behavior, shell execution semantics, or graph lint behavior.

## Revised acceptance criteria

- [ ] AC-01: `examples/shared/toolbelt/{read_file,search,list_dir,git_log}.tool.yaml` exist, validate against `ToolManifest` with unknown fields rejected, and each declares `runtime.type: shell`.
- [ ] AC-02: planner, enforcer, and judge `graph.yaml` reference all four shared tools via `manifest:` keys; zero inline copies of `cat {file}`, `rg -n --glob {glob} {pattern} .`, `ls {dir}`, and `git log --oneline --all --grep={pattern}` remain in those three graph files.
- [ ] AC-03: A committed test loads each converted graph and proves the effective shell config for each shared tool matches the canonical manifest contract: `command`, canonical `description`, `parse`, and `timeout == 30`.
- [ ] AC-04: The canonical `search` description contains the union of the three previously drifted glob example lists.
- [ ] AC-05: Demo-specific tools remain inline: planner `write_file`, enforcer `git_diff`/`lint`/`run_tests`/edit-write helpers, and judge `run_tests` are not moved into the toolbelt.
- [ ] AC-06: `yamlgraph graph lint` passes for planner, enforcer, and judge; the governed graph edits are authored via `scripts/author.sh` and the validation artifact records lint and smoke evidence.
- [ ] AC-07: Each converted demo has a regenerated successful `demo-output.log` committed with the graph change and no fatal-marker-only witness substituted for success.
- [ ] AC-08: `capabilities/CAP-220-shared-shell-toolbelt.yaml` with `REQ-YG-579` is added, unless the FR is revised before enforcement to another exact next-free pair; every new or changed test has an exact `@pytest.mark.req(...)` marker and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-09: `examples/shared/README.md` documents `examples/shared/toolbelt/` as shared agent tools of any manifest runtime type, with the fit boundary "verbatim two-plus-consumer contracts earn manifests; demo-local variants stay inline."
- [ ] AC-10: No files under `yamlgraph/` change; no research graph manifest or judge adapter branch is added; changelog fragment, FR implementation status, and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-3 are folded into `feature-requests/FR-777-shared-shell-toolbelt-manifests.md`. | GATE |
| C-2 | Governed graph edits to planner, enforcer, and judge must be authored through `scripts/author.sh` and retain its validation record. | GATE |
| C-3 | The migrated planner/enforcer/judge graph and toolbelt diff requires human review before merge. | GATE |
| C-4 | Effective shell behavior must remain unchanged except for the documented canonical `search` description union; timeout/default semantics must be tested, not assumed. | GATE |
| C-5 | If enforcement discovers a shell manifest translation gap that requires `yamlgraph/` changes, stop and file a separate bug FR; this FR may not repair the runtime. | GATE |
| C-6 | The toolbelt directory must remain runtime-neutral in wording and scope; adding the research graph manifest or any graph-runtime consumer belongs to a separate judged FR. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may add the four shared shell toolbelt manifests, migrate only the planner/enforcer/judge copies to manifest references through the authoring route, and add the directly related tests, docs, capability, changelog, demo logs, implementation-status note, and diary.
