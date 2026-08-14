# Judgement: FR-794 Shared Python Tool Manifest Root Confinement Fix

**Verdict:** APPROVED - the FR identifies a real composition bug between manifest-relative Python paths and graph-root confinement, keeps the security boundary intact, and defines mechanically testable acceptance criteria.

**Reviewed against:** `feature-requests/FR-794-python-tool-manifest-root-confinement-fix.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; repo doctrine supplied in the execution context; HEAD versions of `yamlgraph/tools/manifest.py`, `yamlgraph/tools/python_tool.py`, `yamlgraph/compile/graph_loader.py`, `tests/unit/test_fr445_python_tool_graph_root_confinement_red.py`, `examples/api-discovery/steps/endpoint-probe/graph.yaml`, `examples/api-discovery/tools/curl_probe.tool.yaml`, `feature-requests/FR-445-python-tool-path-root-confinement.md`, and `feature-requests/FR-768-tool-manifest-declaration-reuse.md`. Uncommitted implementation diffs were not used as authority.

## What is sound

The failure is concrete and scoped. FR-794 documents a runtime failure where `curl_probe` resolves to `examples/api-discovery/tools/curl_probe.py` and is rejected as escaping the consuming graph root `examples/api-discovery/steps/endpoint-probe` (`feature-requests/FR-794-python-tool-manifest-root-confinement-fix.md:35-47`). The cited graph really consumes a shared manifest (`examples/api-discovery/steps/endpoint-probe/graph.yaml:20-22`), and that manifest really declares a Python file-path runtime (`examples/api-discovery/tools/curl_probe.tool.yaml:7-10`).

The root cause is correctly localized. FR-768 established that manifest runtime paths resolve relative to the manifest file (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:94-101`), and the manifest translator in HEAD implements that by converting `runtime.path` to an absolute path from `manifest_dir` (`yamlgraph/tools/manifest.py:79-100`). FR-445 established graph-root confinement for inline Python file-path tools (`feature-requests/FR-445-python-tool-path-root-confinement.md:50-63`), and HEAD `python_tool.py` enforces every file path against the `graph_root` passed by the consuming graph (`yamlgraph/tools/python_tool.py:110-183`). Those contracts are individually coherent but incompatible for cross-directory shared Python manifests.

The proposed fix is minimal and preserves the prior security objective. It moves manifest-sourced Python path confinement to the manifest declaration root while leaving inline, non-manifest `type: python` paths confined to the consuming graph root (`feature-requests/FR-794-python-tool-manifest-root-confinement-fix.md:73-104`). It also closes the currently unguarded manifest-path escape gap by requiring `resolved.relative_to(manifest_dir)` in `_translate()` (`feature-requests/FR-794-python-tool-manifest-root-confinement-fix.md:61-66`, `feature-requests/FR-794-python-tool-manifest-root-confinement-fix.md:83-90`).

The FR is single-responsibility after the split. It explicitly excludes the independent prompt/schema dialect problem and tracks that as FR-795 (`feature-requests/FR-794-python-tool-manifest-root-confinement-fix.md:54-58`, `feature-requests/FR-794-python-tool-manifest-root-confinement-fix.md:160-165`). That keeps this judgement on framework tool-loading semantics, not graph-authoring repair.

Strategic classification: **Framework primitive bug fix**. This repairs the interaction between two existing framework primitives, with multiple named consumers already blocked or exposed: FR-785, FR-788, FR-790, and FR-791 (`feature-requests/FR-794-python-tool-manifest-root-confinement-fix.md:49-52`).

## Required revisions

None.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/tools/manifest.py::_translate()` validates `PythonRuntime.path` against the manifest directory and carries the manifest declaration root forward for path-based Python tools. |
| D-2 | `yamlgraph/tools/python_tool.py` accepts that manifest declaration root for manifest-sourced Python file-path tools and confines against it instead of the consuming graph root. |
| D-3 | Regression tests for cross-directory Python path manifest success, manifest-path escape rejection, unchanged FR-445 inline confinement, and the endpoint-probe tool-loading seam. |
| D-4 | Changelog fragment and diary reflection. |

Not authorized: graph or prompt artifact edits; shell-runtime or graph-runtime manifest semantic changes; Python module manifest semantic changes; weakening or skipping path confinement; using `tool_load_mode: warn` as the fix; adding a public callable-registry API for tests; changing agent invocation semantics; changing hooks, CI, judge/review doctrine, or other enforcement infrastructure.

## Revised acceptance criteria

- [ ] AC-01: A RED test using `yamlgraph.compile.graph_loader.load_and_compile` reproduces the current failure on a temp fixture where graph directory B consumes a `runtime.type: python` manifest from directory A and the manifest path is rejected as escaping graph root.
- [ ] AC-02: After the fix, the same fixture loads and compiles successfully, and invoking the compiled graph returns the manifest-backed Python tool's actual output. The test must use existing public graph execution behavior and must not introduce a public callable-registry API.
- [ ] AC-03: A manifest whose own `runtime.path` escapes its manifest directory is rejected during graph load/compile with an explicit error naming the escaped path, the manifest/declaration root, and the resolved path.
- [ ] AC-04: Existing FR-445 tests in `tests/unit/test_fr445_python_tool_graph_root_confinement_red.py` pass unmodified; inline non-manifest Python file-path tools remain confined to the consuming graph root.
- [ ] AC-05: `examples/api-discovery/steps/endpoint-probe/graph.yaml` no longer raises the `curl_probe` "escapes graph root" error at the `_parse_all_tools`/tool-loading seam. Full `load_and_compile` success for that graph is not required by this FR if still blocked solely by FR-795's prompt-schema repair.
- [ ] AC-06: Existing FR-768 manifest behavior remains unchanged for shell manifests, graph manifests, Python module manifests, and inline declarations.
- [ ] AC-07: Changelog fragment and diary reflection are added.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Manifest-sourced Python file paths must be confined to the manifest directory; inline Python file paths must remain confined to the consuming graph directory. | GATE |
| C-2 | The implementation must not skip validation for manifest-sourced Python paths or rely on `tool_load_mode: warn` to avoid failure. | GATE |
| C-3 | No graph or prompt artifacts may be edited under this FR; any material graph/prompt repair must use the graph-authoring route under a separate FR. | GATE |
| C-4 | No shell-runtime, graph-runtime, or Python-module manifest semantics may change under this FR. | GATE |
| C-5 | No public callable-registry API may be introduced to satisfy testing; prove execution through graph invocation or an existing internal seam. | GATE |

Authority granted: upon human acceptance of this draft judgement, the enforcer may implement only the shared Python file-path manifest root-confinement fix and the regression/documentation artifacts listed above.

**Prior art:** FR-445 (python-tool-path-root-confinement) is the confinement mechanism being relocated, not duplicated or removed — cited throughout as the invariant this fix preserves. FR-782/FR-699/FR-768 hits are false positives from generic noun overlap ("python", "tool", "confinement"); none address the manifest-vs-graph-root boundary conflict this FR fixes. No overlap requiring disposition beyond FR-445, which is explicitly the repaired predecessor.
