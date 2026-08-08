# Judgement: FR-781 macOS File Hook Example - Folder-Triggered Graphs

**Verdict:** APPROVED WITH REVISIONS - the event-driven local automation example is a real contrib/example, but authority activates only after the FR freezes the filename/write boundary, launchd runner contract, confidence semantics, and Pillow dependency/test surfaces.

**Reviewed against:** `feature-requests/FR-781-macos-file-hook-example.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `reference/scheduling-agents.md`; `examples/shared/describe_image.tool.yaml`; `examples/shared/vision_tool.py`; `examples/demos/shared-vision-tool/graph.yaml`; `capabilities/CAP-217-shared-vision-tool.yaml`; `tests/unit/test_shared_vision_tool.py`; `tests/unit/test_fr770_demo_manifest.py`; `tests/unit/test_fr771_demo_invocation.py`; `feature-requests/FR-117-enforce-worktree-watch-integration.md`; `feature-requests/046-diary-world-digest.md`; `feature-requests/FR-759-otel-observability-boundary.md`; `feature-requests/FR-767-graph-authoring-sole-route.md`; `feature-requests/FR-779-research-agent-demo-rot.md`; `feature-requests/FR-779-research-agent-demo-rot.judgement.md`; `feature-requests/FR-780-research-agent-toolbelt-conversion.md`; `docs/diary/diary-2026-08-08-the-ancestor-in-the-deployed-folder.md`; `docs/diary-2026-02-21.md`; `pyproject.toml`; `docs/dependency-rationale.yaml`; `scripts/direct_import_scan.py`; `.github/workflows/workflow.yml`; `.github/workflows/commitlint.yml`.

**Prior art:** dispositioned — `reference/scheduling-agents.md` teaches calendar/interval scheduling only, no `WatchPaths` (gap confirmed, not a duplicate); FR-117 rejected fswatch (rationale supports native launchd here); CAP-217/FR-769/FR-770 shared vision boundary is reused and extended additively, not reinvented; FR-046 is the calendar-scheduled sibling; FR-759 supplies the missing-extra fail-fast contract; no rejected FR occupies this territory.

## What is sound

The first consumer is concrete, not invented. FR-781 names the 15 orphaned PNGs and the next folder-drop event (`feature-requests/FR-781-macos-file-hook-example.md:8-11`), and the diary evidence independently records the failed invariant: 15 titled PNGs, zero descriptions, newest from Aug 5, last successful run 2025-10-30 (`docs/diary/diary-2026-08-08-the-ancestor-in-the-deployed-folder.md:39-43`). The same diary entry identifies the old shell system as a ready requirements document and test plan for a YAMLGraph conversion (`docs/diary/diary-2026-08-08-the-ancestor-in-the-deployed-folder.md:55-63`).

The event-driven documentation gap is real enough for an example. Current scheduling docs teach `StartCalendarInterval` and `StartInterval` (`reference/scheduling-agents.md:29-35`, `reference/scheduling-agents.md:98-119`) but do not provide a `WatchPaths` recipe; FR-781's proposed sibling file-hook section is therefore pattern documentation, not a duplicate of the scheduled-agent guide (`feature-requests/FR-781-macos-file-hook-example.md:13-15`, `feature-requests/FR-781-macos-file-hook-example.md:173-174`). FR-117's rejected `fswatch` alternative objected to adding a dependency and second daemon (`feature-requests/FR-117-enforce-worktree-watch-integration.md:97-100`), which supports a native launchd `WatchPaths` example rather than undermining it.

The vision boundary reuse is architecturally aligned. The shared manifest already points to `examples.shared.vision_tool.describe_image` (`examples/shared/describe_image.tool.yaml:3-8`), the committed demo consumes it through `manifest:` (`examples/demos/shared-vision-tool/graph.yaml:9-22`), and CAP-217 defines the reusable contract as image plus instruction through `create_llm()` into a validated `ImageDescription` (`capabilities/CAP-217-shared-vision-tool.yaml:4-8`). Extending that boundary with optional fields and opt-in downscaling is more coherent than adding a demo-local shell shrink step, provided the dependency and schema contracts are frozen.

The FR already respects the governed graph-authoring boundary by requiring `scripts/author.sh` for the new graph (`feature-requests/FR-781-macos-file-hook-example.md:83`, `feature-requests/FR-781-macos-file-hook-example.md:178-180`), matching repo doctrine that graph and prompt artifacts must be authored through the sole route (`.github/copilot-instructions.md:15`). Its strategic classification is **Contrib/example with a bounded shared example-utility enhancement**, not a framework primitive: the reusable product is a documented macOS hook pattern plus one concrete graph, not new YAMLGraph runtime semantics.

## Required revisions

### R-1: Freeze the launchd runner, environment, and test contract

Replace the ambiguous runner text with an exact `ProgramArguments` contract. The current phrase "absolute venv python -> `yamlgraph graph run`" (`feature-requests/FR-781-macos-file-hook-example.md:152-154`) is not mechanically executable as written: launchd `ProgramArguments` does no shell expansion, and the existing scheduling guide emphasizes full paths (`reference/scheduling-agents.md:20-27`, `reference/scheduling-agents.md:76-80`). Choose one executable form and state it explicitly, such as absolute `.venv/bin/yamlgraph` plus `graph run ...`, or absolute Python plus a valid module/script invocation.

Fold these details into the FR: the plist template contains `WorkingDirectory`, `StandardOutPath`, and `StandardErrorPath`; the README documents how API keys/env vars reach launchd using a wrapper, `.env`, or Keychain rather than assuming an interactive shell (`reference/scheduling-agents.md:82-96`); the Full Disk Access/TCC warning cites the sandbox diary evidence (`docs/diary-2026-02-21.md:139-163`, `docs/diary-2026-02-21.md:348-350`); and `install-hook.sh` has a render-only or dry-run mode so CI can test absolute-path substitution without requiring macOS launchctl. Actual `launchctl` load/unload may be documented and optionally exercised on Darwin, but must not be required for Linux CI.

### R-2: Define the safe filename, collision, and idempotence boundary

The FR currently writes `<Title>.md` and renames the PNG from LLM output (`feature-requests/FR-781-macos-file-hook-example.md:31-33`, `feature-requests/FR-781-macos-file-hook-example.md:106-107`) but does not define how an arbitrary title becomes a safe basename. Fold a deterministic contract into the FR: title normalization must reject or transform path separators, control characters, empty names, `.`/`..`, and names that escape the watched directory; duplicate titles must have a stated collision policy; writes and renames must be confined to the watched directory; and a failed safety check must leave the source PNG unmodified with a visible error, not fall back to a risky name.

Extend pairing idempotence beyond the happy path. The existing ancestor's bugs were duplicate ledgers and rename-then-reprocess behavior (`docs/diary/diary-2026-08-08-the-ancestor-in-the-deployed-folder.md:31-43`), so the FR must require tests for second-run no-op, existing `.md` twin skip, unsafe title skip, duplicate-title collision handling, and low-confidence no-write/no-rename. The committed demo must run against a disposable copy of `fixture.png` or a generated demo workspace so the source fixture is not consumed by its own witness run.

### R-3: Freeze confidence semantics at the schema boundary

The FR adds `confidence: str | None` and gates low confidence (`feature-requests/FR-781-macos-file-hook-example.md:117-123`), but a free string is not a mechanical gate. Fold in an exact domain and routing rule. Use a constrained enum/Literal such as `high | medium | low` unless the FR chooses a stricter alternative. For this demo, state exactly which values permit write/rename and which values block it; `None` or missing confidence must be fail-safe and must not publish.

This preserves the repo's boundary doctrine: all LLM outputs pass through typed schema (`.github/copilot-instructions.md:216`), and a plausible wrong answer is worse than a crash (`.github/copilot-instructions.md:218`). FR-779 is the right precedent only when the gate is structural and deterministic, not prompt-only (`feature-requests/FR-779-research-agent-demo-rot.md:70-72`; `feature-requests/FR-779-research-agent-demo-rot.judgement.md:67-69`).

### R-4: Choose the Pillow dependency surface and make it CI-measurable

The FR currently leaves the dependency placement open - "new optional extra (or added to an existing one - judge decides)" (`feature-requests/FR-781-macos-file-hook-example.md:134-137`). Fold the decision into the FR before enforcement. The authorized default is a new `vision` optional extra containing `Pillow>=10.0.0`, with an entry in `docs/dependency-rationale.yaml` because every pyproject dependency requires rationale (`docs/dependency-rationale.yaml:1-4`). If the implementation imports `PIL`, update dependency scanning metadata so `PIL` resolves to the `Pillow` distribution rather than appearing as an undeclared report-only import (`scripts/direct_import_scan.py:81-98`).

The test plan must also say how the positive downscale test runs in CI. Current workflow installs explicit extras in the unit-test jobs (`.github/workflows/workflow.yml:30-40`, `.github/workflows/workflow.yml:56-62`), and `pyproject.toml` has no Pillow-bearing extra in the consumed optional-dependencies block (`pyproject.toml:39-159`). Add the chosen extra to the relevant test install surface, or otherwise provide an equivalent committed test mechanism. The fail-fast path for `max_dim` with the extra absent must be tested by import simulation, mirroring FR-759's missing-extra contract (`feature-requests/FR-759-otel-observability-boundary.md:64-67`), not by relying on the developer's ambient environment.

### R-5: Tighten the demo witness and documentation boundaries

The `demo-output.log` acceptance criterion must prove the example, not just satisfy the demo gate. The existing CI demo gate requires a changed demo to include `examples/demos/<name>/demo-output.log` and validates it semantically (`.github/workflows/commitlint.yml:239-288`); FR-781 should additionally require the log to show the temp input path, the typed schema result, the confidence route taken, the markdown write, the image rename, and the second-run no-op. The receipt-renamer remains a README recipe only (`feature-requests/FR-781-macos-file-hook-example.md:166-172`, `feature-requests/FR-781-macos-file-hook-example.md:218-220`); do not implement a second graph or PDF tooling under this FR.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revisions to `feature-requests/FR-781-macos-file-hook-example.md` folding R-1 through R-5 |
| D-2 | New governed example artifacts under `examples/demos/file-hook/`: `graph.yaml`, `prompts/describe_artwork.yaml`, hook template, install script, README, fixture, and `demo-output.log` |
| D-3 | Shared vision-tool enhancement in `examples/shared/vision_tool.py` and `examples/shared/describe_image.tool.yaml` for optional `max_dim`, `quote`, and constrained `confidence` |
| D-4 | Dependency governance updates for the chosen Pillow extra: `pyproject.toml`, `docs/dependency-rationale.yaml`, direct-import scan metadata if `PIL` is imported, and CI install surface if needed for tests |
| D-5 | Tests for pairing/idempotence, filename safety, confidence gating, `describe_image(max_dim=...)`, missing-extra fail-fast, plist rendering, and install-script dry-run/fake-launch behavior |
| D-6 | `reference/scheduling-agents.md` WatchPaths pointer, changelog fragment, requirement/capability traceability, FR implementation status, and diary reflection |

Not authorized: new YAMLGraph runtime/node types; changes under `yamlgraph/`; a generic file-watcher framework; `fswatch`, polling daemons, or Folder Actions implementation; a receipt-renamer graph or PDF tool implementation; unbounded changes to shared vision provider support; live launchctl requirements in Linux CI; prompt-only confidence enforcement; writing outside the watched directory; manual edits to governed graph/prompt artifacts outside `scripts/author.sh`.

## Revised acceptance criteria

- [ ] AC-01: The FR is revised to include the exact launchd runner/env/test contract, filename/collision/idempotence contract, constrained confidence semantics, chosen Pillow extra/dependency-governance surface, and demo-witness requirements from R-1 through R-5.
- [ ] AC-02: `examples/demos/file-hook/graph.yaml` and `prompts/describe_artwork.yaml` are authored through `scripts/author.sh`; `tmp/draft-authoring-report.md` records lint, compile/validate, smoke, and relevant test evidence for the governed artifacts.
- [ ] AC-03: Pairing idempotence is proven by tests that run the scan/process semantics on a temporary folder: first run processes a PNG with no `.md` twin, second run processes zero files, and an existing `.md` twin is skipped without a ledger.
- [ ] AC-04: Filename-safety tests prove title normalization confines outputs to the watched directory, handles path separators/control characters/empty or dot names, and applies the frozen duplicate-title collision policy without overwriting unrelated files.
- [ ] AC-05: Confidence-gate tests prove low, missing, or otherwise blocked confidence writes no markdown and performs no rename, while the explicitly allowed confidence value(s) write `<safe-title>.md` and rename the PNG.
- [ ] AC-06: `ImageDescription` gains optional `quote` and constrained optional `confidence` fields with defaults that preserve existing shared-vision consumers; existing shared-vision tests remain green without edits that weaken their assertions.
- [ ] AC-07: `describe_image(max_dim=...)` on a local image downscales before base64 encoding so the longest side is `<= max_dim` and payload bytes shrink; `max_dim=None` preserves current full-size behavior; URL inputs are not downloaded and emit the documented warning when `max_dim` is requested.
- [ ] AC-08: Requesting `max_dim` without the Pillow extra fails before LLM invocation with an error naming the exact install command for the chosen extra; tests simulate the missing-extra path independent of ambient installation state.
- [ ] AC-09: `pyproject.toml`, `docs/dependency-rationale.yaml`, dependency-scan metadata, and CI/test install surfaces are updated consistently for the chosen Pillow extra; `python scripts/dependency_rationale.py --strict` and `python scripts/direct_import_scan.py --strict` pass.
- [ ] AC-10: The plist template contains `WatchPaths`, `ThrottleInterval`, `WorkingDirectory`, `StandardOutPath`, `StandardErrorPath`, and the exact executable `ProgramArguments`; install-script tests verify absolute-path rendering and load/unload command construction through dry-run or fake `launchctl` without requiring macOS in CI.
- [ ] AC-11: README documents install, uninstall, status, manual test, logs, environment/API-key setup, `WatchPaths` versus `StartCalendarInterval`, the Full Disk Access/TCC trap, this DeviantArt example, and the receipt-renamer as documentation-only recipe; `reference/scheduling-agents.md` links to the example as the canonical WatchPaths demo.
- [ ] AC-12: `demo-output.log` is regenerated from a grounded `PROVIDER=google` run on a disposable copy of `fixture.png`; it shows typed schema output, confidence routing, write/rename effects, and second-run no-op, contains no fatal markers, and does not consume or rename the committed fixture.
- [ ] AC-13: Every new or changed test has an exact `@pytest.mark.req("REQ-YG-...")` marker; the capability registry is updated or extended for the new file-hook example and vision downscale behavior; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-14: A changelog fragment, FR implementation-status update, and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-5 are folded into `feature-requests/FR-781-macos-file-hook-example.md`. | GATE |
| C-2 | Governed graph and prompt artifacts must be created or changed only through `scripts/author.sh`; manual edits to `graph.yaml` or `prompts/*.yaml` are not authorized. | GATE |
| C-3 | The file-writing boundary must fail safe: unsafe titles, duplicate collisions, low/missing confidence, or write/rename errors must leave the source PNG unmodified and must not create success-shaped output. | GATE |
| C-4 | The hook installer must be mechanically testable without a real launchd session; actual `launchctl` execution is optional/manual unless running on Darwin with an explicit test harness. | GATE |
| C-5 | If implementing `max_dim` requires changes under `yamlgraph/` or promotes Pillow to a core dependency, stop for re-judgement; this FR authorizes an examples/shared vision extra, not a framework primitive. | GATE |
| C-6 | The receipt-renamer remains documentation only. Implementing PDF extraction, a second graph, or a second live demo is out of scope. | GATE |
| C-7 | No `fswatch`, polling daemon, Folder Actions, or persistent processed-files ledger may be introduced. The `.md` twin is the ledger. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may build the macOS `WatchPaths` file-hook demo, the directly necessary shared vision-tool enhancements, and the tests/docs/dependency-governance artifacts listed in the frozen scope.
