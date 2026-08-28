# Judgement: FR-898 Neo-Waterfall Video v2 -- Agent-Generated Extended Edition

**Prior art:** FR-100 (development-pipeline ebook, In Progress) — same subject,
different proclaim channel (text vs video); distinct proclaimable classes per
`docs/research-publication-channels-2026-08-18.md`, no shared deliverables.
Full disposition in the FR's Prior art line.

**Verdict:** APPROVED WITH REVISIONS -- the Proclaim/video direction is sound as a contrib/example, but authority activates only after the FR replaces non-closed/missing implementation evidence with repo-owned contracts and separates human publication from enforceable build work.

**Reviewed against:** `feature-requests/FR-898-neo-waterfall-video-v2.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/doctrine.md`; `feature-requests/TEMPLATE.md`; `docs/feature-request-methodology.md`; `docs/development-process.md`; `docs/diary/diary-2026-08-18-missing-last-leg.md`; `docs/research-publication-channels-2026-08-18.md`; `examples/storyboard/generate_videos.py`; `examples/storyboard/README.md`; `pyproject.toml`.

## What is sound

The first consumer and first event are concrete: the operator uploads `final.mp4` to @voiceresponse and commits the resulting URLs into the methodology documentation (`feature-requests/FR-898-neo-waterfall-video-v2.md:7`). The problem is real: the Proclaim stage is explicitly named in the diary as the missing post-Submit packaging step (`docs/diary/diary-2026-08-18-missing-last-leg.md:53`), and the publication-channel research identifies YouTube/TikTok as a human-facing channel for content-pipeline output (`docs/research-publication-channels-2026-08-18.md:61`) while warning that proclamation exists without harvest/publishing adapters (`docs/research-publication-channels-2026-08-18.md:77`).

The proposal also uses the right strategic class: **Contrib/example**, not framework primitive. It creates a self-contained `examples/demos/process_video/` artifact (`feature-requests/FR-898-neo-waterfall-video-v2.md:93`) and routes graph creation through the graph-authoring sole route (`feature-requests/FR-898-neo-waterfall-video-v2.md:96`), matching the repo rule that every new `graph.yaml`/`prompts/*.yaml` artifact must go through `scripts/author.sh` with lint/smoke evidence (`.github/copilot-instructions.md:15`; `.github/skills/graph-authoring/doctrine.md:97`).

The alternatives table is substantive enough for FR-890's research-evidence gate: it names multiple solution classes and rejects them with reasons rather than shape-only entries (`feature-requests/FR-898-neo-waterfall-video-v2.md:240`, `feature-requests/FR-898-neo-waterfall-video-v2.md:244`, `feature-requests/FR-898-neo-waterfall-video-v2.md:245`, `feature-requests/FR-898-neo-waterfall-video-v2.md:248`, `feature-requests/FR-898-neo-waterfall-video-v2.md:250`). The selected design also has useful precedent: existing storyboard code already performs ffmpeg concatenation (`examples/storyboard/generate_videos.py:136`, `examples/storyboard/generate_videos.py:158`), while the FR correctly rejects extending that Replicate/image-interpolation tool in place because the contract differs (`feature-requests/FR-898-neo-waterfall-video-v2.md:248`).

The redaction boundary is correctly treated as a meaning-level issue, not just a grep: the FR bans customer/project names, private IDs, phone numbers, hostnames, cloud project IDs, and field-deployment measurement constants (`feature-requests/FR-898-neo-waterfall-video-v2.md:149`, `feature-requests/FR-898-neo-waterfall-video-v2.md:226`), and limits beat-4 visuals to generic fixture material (`feature-requests/FR-898-neo-waterfall-video-v2.md:250`).

## Required revisions

### R-1: Replace the missing `voice_runtime` dependency with a repo-owned TTS contract

Rewrite Stage 3, the TTS acceptance criterion, and the Chatterbox alternative so enforcement does not depend on `projects/voice_runtime` or `voice_runtime.create_tts()`. The FR currently cites `projects/voice_runtime` as prior art (`feature-requests/FR-898-neo-waterfall-video-v2.md:28`) and requires `voice_runtime.create_tts()` in both the solution and acceptance criteria (`feature-requests/FR-898-neo-waterfall-video-v2.md:131`, `feature-requests/FR-898-neo-waterfall-video-v2.md:218`), but no `projects/voice_runtime/**` or `**/voice_runtime/**` implementation exists in this repository, and `pyproject.toml` only declares `elevenlabs` under the `telco` extra plus `chatterbox-tts` under the `chatterbox` extra (`pyproject.toml:127`, `pyproject.toml:150`).

Fold this revision mechanically as follows: Stage 3 must require an example-local TTS adapter, e.g. `examples/demos/process_video/nodes/tts.py`, with provider flags for the repo-declared providers it actually imports. If ElevenLabs is primary, the adapter may use the already declared `elevenlabs` package from the `telco` extra; if Azure speech synthesis is retained, the FR must add the exact declared dependency/extra that provides that SDK before authorizing implementation. The capture manifest must continue recording provider and voice id.

### R-2: Demote YouTube upload and v2 URL commit to a post-build human gate

Rewrite Stage 5 and the URL acceptance criterion so the enforceable work ends at a reproducible `final.mp4`, a manifest, and documentation hooks that can accept the URL after the operator supplies it. The current FR makes operator review/upload part of Stage 5 (`feature-requests/FR-898-neo-waterfall-video-v2.md:144`) and requires v1 and v2 YouTube URLs committed as an acceptance criterion (`feature-requests/FR-898-neo-waterfall-video-v2.md:235`). That bundles implementation with an external human/platform action the enforcer cannot complete or test.

Fold this revision mechanically as follows: the implementation may add the v1 URL immediately and add a clearly marked v2 placeholder or "pending upload" note only if the docs convention permits it; committing the actual v2 URL is authorized only after the operator reviews `final.mp4`, uploads it, and supplies the URL in a follow-up commit or separate publication FR.

### R-3: Remove or commit every non-closed evidence dependency

Replace non-committed or inaccessible citations with committed public artifacts, or explicitly state that they are background provenance not consumed by the enforcer. The FR cites session turns and a local planning file as prior art (`feature-requests/FR-898-neo-waterfall-video-v2.md:21`) and cites private beat-4 sources while saying they are deliberately uncited (`feature-requests/FR-898-neo-waterfall-video-v2.md:253`). Judge doctrine permits only the FR, cited evidence files, and repo doctrine; missing essential context is an FR defect (`.github/skills/judge-fr/doctrine.md:16`).

Fold this revision mechanically as follows: keep beat 4's source closed to the committed `## Cross-Project Learnings` section and say that no private repo, session transcript, or local `docs-planning/` file is implementation input. If the R5 quote is mandatory, commit the quoted text inside the FR or cite an existing committed document containing it.

### R-4: Define the capture manifest schema and deterministic checks

Add the manifest file path and required fields to the Proposed Solution. The acceptance criteria require tracing every terminal still to command and exit code (`feature-requests/FR-898-neo-waterfall-video-v2.md:212`) and recording TTS provider/voice id (`feature-requests/FR-898-neo-waterfall-video-v2.md:218`), but the FR never defines the manifest schema or where it is written. Enforcement needs a concrete file contract.

Fold this revision mechanically as follows: require `examples/demos/process_video/output/manifest.json` or another explicit path with typed scene entries containing at minimum `scene_id`, `png_path`, `source_kind`, `command`, `exit_code`, `audio_path`, `tts_provider`, `voice_id`, `duration_seconds`, and `redaction_status`. Add a deterministic validation command that checks all referenced files exist, all command-backed frames have exit codes, total duration is 600-900 seconds, and every mandatory beat is present.

### R-5: Add an explicit graph-authoring task brief deliverable

Add the committed authoring brief path to the deliverables and acceptance criteria. The FR correctly says the graph must be authored via `scripts/author.sh` (`feature-requests/FR-898-neo-waterfall-video-v2.md:96`, `feature-requests/FR-898-neo-waterfall-video-v2.md:237`), but graph-authoring doctrine requires an artifact-closed task brief whose target directory and desired artifact are stated inside the brief (`.github/skills/graph-authoring/doctrine.md:18`). Without the brief path, the enforcer can satisfy the shape of the route while losing the input-closure record.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/authoring-briefs/fr-898-process-video-brief.md` |
| D-2 | `examples/demos/process_video/graph.yaml` and `examples/demos/process_video/prompts/*.yaml`, authored only through `scripts/author.sh` |
| D-3 | `examples/demos/process_video/nodes/` or equivalent example-local Python helpers for screen capture, manifest validation, TTS, and ffmpeg assembly |
| D-4 | `examples/demos/process_video/fixtures/` sanitized beat-4 fixture material only |
| D-5 | `examples/demos/process_video/output/script.json`, `manifest.json`, generated stills/audio, and `final.mp4` when the repo's artifact-size policy permits; otherwise a documented generated-output path plus committed manifest/demo log |
| D-6 | `examples/demos/process_video/demo-output.log` proving the end-to-end build command ran |
| D-7 | `docs/feature-request-methodology.md` and `docs/development-process.md` documentation references, limited by R-2 |
| D-8 | `changelog/unreleased/*.md`, the FR implementation-status update, and a diary reflection |

Not authorized: framework node-type changes; judge/review/graph-authoring doctrine changes; hook or CI changes except those already triggered by the demo gate; private-repo screenshots, private issue/PR references, customer identifiers, phone numbers, hostnames, cloud project IDs, or field-deployment measurement constants; direct publication/upload automation; generic Harvest ledger implementation; shorts/cut-down generation; extending `examples/storyboard/generate_videos.py` in place; dependency additions not named in the revised FR.

## Revised acceptance criteria

- [ ] AC-01: `feature-requests/authoring-briefs/fr-898-process-video-brief.md` is committed and names `examples/demos/process_video/` as the artifact boundary.
- [ ] AC-02: `scripts/author.sh feature-requests/authoring-briefs/fr-898-process-video-brief.md` produces `tmp/draft-authoring-report.md` with `Artifacts`, `Precedent`, `Validation`, `Repairs`, and `Blocked validation` sections, and the report lists the created/modified process-video paths.
- [ ] AC-03: `yamlgraph graph lint examples/demos/process_video/graph.yaml` passes, and the narrow smoke/build command is recorded in `examples/demos/process_video/demo-output.log`.
- [ ] AC-04: The graph generates typed `script.json` from committed inputs only, and a deterministic validator proves all five mandatory beats are present.
- [ ] AC-05: `script.json` contains scene entries with narration, visual spec, and duration hint; total planned/runtime duration validates within 600-900 seconds.
- [ ] AC-06: Every command-backed terminal still in `manifest.json` maps PNG path to command and exit code from the build run; no mocked terminal output is accepted.
- [ ] AC-07: Narration audio is synthesized per scene by the revised repo-owned TTS adapter; `manifest.json` records provider and voice id for every audio file.
- [ ] AC-08: The ffmpeg assembler creates `final.mp4`; the validator confirms referenced audio/still files exist and the final duration is 600-900 seconds.
- [ ] AC-09: Redaction validation over `script.json`, `manifest.json`, generated text surfaces, and frame-source metadata finds no sibling-repo names, customer identifiers, absolute home paths, private PR/issue IDs, phone numbers, hostnames, cloud project IDs, or field-deployment measurement constants.
- [ ] AC-10: Beat-4 visuals are generated only from fixtures committed under `examples/demos/process_video/fixtures/`, and the authoring report records a human meaning-level redaction review before any upload.
- [ ] AC-11: `docs/feature-request-methodology.md` includes the v1 URL and either the operator-supplied v2 URL or an explicit pending-upload marker allowed by R-2; `docs/development-process.md` receives the matching process-video pointer.
- [ ] AC-12: A changelog fragment and diary reflection are committed, and the FR records implementation status, decisions, and any deviations.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-5 are folded into `feature-requests/FR-898-neo-waterfall-video-v2.md`. | GATE |
| C-2 | Graph and prompt artifacts must be authored only through `scripts/author.sh`; unsentineled direct edits to governed graph artifacts remain forbidden. | GATE |
| C-3 | The enforcer must not read or render private repositories, session transcripts, uncommitted local planning files, customer dashboards, phone-call artifacts, or private deployment reports; beat-4 implementation input is limited to the committed aliased digest and sanitized fixtures. | GATE |
| C-4 | If the revised TTS provider requires a dependency not already declared in `pyproject.toml`, the dependency addition must be explicit in the FR before implementation and covered by the narrow build/smoke command. | GATE |
| C-5 | Publication is a human gate: no upload automation and no actual v2 URL commit unless the operator has reviewed `final.mp4` and supplied the URL. | GATE |
| C-6 | Any generated media too large or unstable for git must stay out of tracked source; the repo must commit the command, manifest, and demo log that reproduce it instead. | GATE |

Authority granted: after the revisions are folded into the FR, build the self-contained `examples/demos/process_video/` contrib/example and its reproducible local video artifact; external publication remains gated on operator review and supplied URL.
