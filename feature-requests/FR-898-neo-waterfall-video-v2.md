# Feature Request: FR-898 Neo-Waterfall Video v2 — Agent-Generated Extended Edition

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged — approved with revisions, R-1..R-5 folded 2026-08-28
**Effort:** 5 days
**Requested:** 2026-08-28
**Judgement:** [FR-898-neo-waterfall-video-v2.judgement.md](FR-898-neo-waterfall-video-v2.judgement.md)
**First consumer / first event:** the operator, at the moment of uploading the
rendered `final.mp4` to the @voiceresponse YouTube channel as the successor to
"Neo-waterfall Behind YAMLGraph" (HNZRFub137I) and committing both video URLs
into `docs/feature-request-methodology.md` — the repo's first executed
Proclaim-stage artifact.
**Research:** In-body dispositioned alternatives table (FR-889/FR-896 style;
see `## Alternatives Considered`). `scripts/research.sh` was deliberately not
run: the channel question is already answered by committed research
(`docs/research-publication-channels-2026-08-18.md`), the production
machinery question by committed code (`examples/storyboard/generate_videos.py`
ffmpeg assembly, the declared `elevenlabs` dependency in the `telco` extra), and the content question by the
operator's structured answers recorded below (2026-08-28). Running five
personas would re-derive committed prior art.
**Prior art:** `docs/feature-request-methodology.md` (b06335eb, 2026-07-29 — the
thesis document); `docs/diary/diary-2026-08-18-missing-last-leg.md` (Proclaim
stage named, unbuilt); `docs/research-publication-channels-2026-08-18.md`
(channel map, "two unread instruments plus an empty proclamation calendar");
`examples/storyboard/generate_videos.py` (ffmpeg clip concat); FR-206 demo-gate
(`demo-output.log` as
proclaimable raw material); FR-100 (development-pipeline ebook, In Progress) —
same subject, different proclaim channel: the ebook renders the process as
text for readers already at the repo, this FR renders it as video for an
external channel; the channels research lists them as distinct proclaimable
classes (doctrine/book vs content output), no scope overlap and no shared
deliverables. Background provenance, NOT implementation input
(judgement R-3): session a904c468 turns 82–94 and the local
`docs-planning/plan-interactive-finalize-coordinator.md` R5 (thesis origin —
the R5 text is committed verbatim in `## Thesis` below); production TTS
precedent in the private voice projects. Graveyard checked: FR-070 rejected visual
AUTHORING ("No UI, ever") — a rendered video is visual OBSERVABILITY of the
process, the sanctioned branch of FR-070's own distinction; no FR has
previously scoped video production of the process itself.

## Summary

Produce an updated, extended (~10–15 min) successor to "Neo-waterfall Behind
YAMLGraph" — **agent-generated end to end**: a narration script distilled by
LLM from committed doctrine and diaries, scene visuals captured from *actual
usage* (real terminal runs of the current process), narration synthesized via
the repo's TTS tooling, and final assembly as an ffmpeg slideshow (stills +
narration audio, Ken-Burns-style pacing). The video about the process, made
by the process.

Operator decisions (recorded 2026-08-28, structured question round):
- **Production route:** agent generated — screens, TTS, ffmpeg slideshow.
- **Format:** long-form, ~10–15 minutes.
- **Content:** actual usage, newest additions to the process.

## Value Statement

An outside viewer (developer, prospective adopter, or client evaluating the
methodology) gets a current, evidence-grounded account of the neo-waterfall
process as it actually runs today — while the repo gains its first executed
Proclaim-stage artifact and closes the found gap that v1 is referenced
nowhere in its own repository.

## Problem

1. **v1 is stale.** The original video predates the process's largest recent
   evolutions: the research sole route (FR-890), the main-write guard and
   worktree-only enforcement writes (FR-888/889), the census arc
   (FR-892–897: 1,266 diaries censused for ~$1, synthesize tail, canary
   gates), the situation board (`now.py`, fr-board FR-740/741), and the
   doctrine's export as a forkable template (gitclaw). The published account
   of the process no longer matches the process.
2. **v1 is unreferenced.** The video ID appears nowhere in any repo's history
   or tree (verified 2026-08-28) — the `missing_last_leg` trap in reverse:
   the proclamation exists but the repo doesn't know. The methodology doc has
   no pointer to its own video companion.
3. **Proclaim has never run.** The 2026-08-18 diary named the stage; the
   channels research mapped the channels; nothing has shipped through them.
   This FR is the first concrete instance, using machinery the repo already
   owns.

## Thesis (committed text for beat 1 — judgement R-3)

> Waterfall is the design: inspection lives entirely at plan/judge; a judged
> FR *is* the approval; "come hell or high water" is the enforce contract.
> The PR carries no review semantics — no approver, no PR-level inspection,
> auto-merge on green. It exists to serialize parallel sessions' writes to
> main. Escalation target is always the judgement: enforcement surprises
> amend the FR and re-judge the delta; PR comments are a channel this
> process deliberately doesn't have.

## Ideal Result

A viewer presses play and, in 10–15 minutes, sees the neo-waterfall thesis
stated (inspection lives at plan/judge; a judged FR is the approval; the PR
is a git-concurrency workaround, not a review gate) and then **watches it
run**: real terminal footage of an FR being researched, filed, judged,
enforced against bouncing gates, and merged — narrated by a synthesized
voice reading a script the pipeline distilled from the repo's own committed
record. The closing frames show the newest organs (census, situation board,
gitclaw) with their measured numbers, then widen to the field: the same
process operating a production platform, told entirely in aliased mechanisms
and identity-free numbers. Every asset in the video is
reproducible by a command committed in this repo; both video URLs are
committed historical references in the methodology doc. The Proposed
Solution below is the minimal path back from this.

## Proposed Solution

New example under `examples/demos/process_video/` (authored via the sole
graph-authoring route, `scripts/author.sh`, per FR-767).

**Stage 0 — Authoring brief (judgement R-5).** A committed artifact-closed
task brief at `feature-requests/authoring-briefs/fr-898-process-video-brief.md`
naming `examples/demos/process_video/` as the artifact boundary; it is the
input-closure record for the sole-route run.

**Stage 1 — Script (LLM graph).** Distill a scene-by-scene narration script
(~1,400–2,100 words for 10–15 min at ~140 wpm) from closed inputs:
`docs/feature-request-methodology.md`, `docs/development-process.md`, the
Scripture, a curated newest-additions digest (FR-888–897 one-liners), and
the aliased `## Cross-Project Learnings` digest in this FR (beat 4's sole
narration source — the input closure for field material is this committed
text, never the private repos).
Output: typed `script.json` — scenes with `narration`, `visual_spec`
(command to run or file to frame), `duration_hint`. One judgement per scene
(prompt-as-subagent-contract); deterministic assembler validates total
length and coverage of the mandatory beats:
1. Thesis recap (neo-waterfall, R5 verbatim quote)
2. Actual usage arc: research.sh → FR filing → judge.sh → enforcement with
   real pre-commit bounces → RED/GREEN commits → merge-on-green
3. Newest additions: main-write guard, census arc + synthesize tail,
   `now.py` situation board, gitclaw export
4. Field deployment arc (aliased — see `## Cross-Project Learnings`): the
   same process operating a production voice-AI platform — infra-as-code
   witness tests, evidence-based capacity sizing, GitOps rollout with
   post-deploy evidence artifacts, browser-controlled enterprise surfaces,
   and black-box verification by real phone calls
5. Evidence close: measured numbers only, and only from THIS public repo
   (census cost, diary count, gate counts) — no aspirational claims, no
   field-deployment constants (see beat-4 abstraction rule below).

**Stage 2 — Screens (deterministic Python tool).** For each scene, capture
stills from actual usage: terminal captures of the real commands running
(freeze-rendered via `termshot`-style rendering or screenshot of executed
output written to PNG), plus framed renders of committed artifacts (FR
excerpts, judgement verdicts, the Scripture). No mocked output: every
terminal frame comes from a command actually executed during the build run
(`mock_escape_hatch` applies to footage too).

**Stage 3 — Narration (TTS, judgement R-1).** Per-scene WAVs synthesized by
an example-local adapter `examples/demos/process_video/nodes/tts.py` with a
provider flag; the primary provider is ElevenLabs via the already declared
`elevenlabs` package (`telco` extra) — the published artifact carries a
production-grade voice. No dependency on any private `voice_runtime`
package. Additional providers (e.g. Azure speech) are authorized only after
this FR is amended with the exact declared dependency/extra (judgement C-4).
The capture manifest records provider and voice id for every WAV so the
audio is regenerable. Chatterbox (CAP-100) rejected for this use: local demo
quality, not the narration voice a published artifact should carry.

**Stage 4 — Assembly (ffmpeg, deterministic).** Slideshow assembler pairs
each scene's stills with its narration audio (image duration = audio
duration), concatenates with crossfades into `final.mp4` — direct descendant
of `generate_videos.py`'s concat stage, no Replicate dependency.

**Manifest contract (judgement R-4).** The build writes
`examples/demos/process_video/output/manifest.json`: typed scene entries
with at minimum `scene_id`, `png_path`, `source_kind`, `command`,
`exit_code`, `audio_path`, `tts_provider`, `voice_id`, `duration_seconds`,
`redaction_status`. A deterministic validation command checks: all
referenced files exist, every command-backed frame has an exit code, total
duration is 600–900 seconds, and every mandatory beat is present. Generated
media too large for git stays untracked (judgement C-6): the committed
record is the command, the manifest, and `demo-output.log`.

**Stage 5 — Docs hooks + human publication gate (judgement R-2).**
Enforceable work ends at a reproducible `final.mp4`, the manifest, and the
docs hooks: the implementation commits the v1 URL (HNZRFub137I) into
`docs/feature-request-methodology.md` immediately, plus an explicit
pending-upload marker for v2 and the video pointer in
`docs/development-process.md`. Upload is a human gate: the operator reviews
`final.mp4`, uploads to @voiceresponse, and supplies the v2 URL, which lands
as a follow-up docs commit. No upload automation (judgement C-5).

State/redaction boundary: script inputs are committed public docs only; the
screens tool must run in a sanitized demo checkout state (no customer repo
names, no sibling-project paths in framed terminal output) — alias at first
capture, not at review (FR-896 R-4 lesson). Beat 4 is the highest-risk beat:
its source material lives in private customer repositories and enters this
public repo as narration text only, pre-aliased per the rules in
`## Cross-Project Learnings` — no source doc links, no customer or project
names, no PR/issue numbers from private trackers, no phone numbers,
hostnames, or GCP project ids, and **no
field-deployment measurement constants**: capacity figures are a
fingerprint even when identity is aliased. Mechanisms are the payload;
identities and constants are not (FR-874 rejection precedent, which listed
capacity disclosure as a leak category: meaning-level leaks survive
secret-value grepping, so the alias pass is judged, not grepped).

## Cross-Project Learnings

The operator ran the neo-waterfall process for months on a production
voice-AI customer platform (referred to here and in all video assets only as
"the field deployment"). Four learnings graduate into beat 4 — each is a
*process* claim demonstrated by mechanism, not by the deployment's own
measurements:

1. **Infra is enforceable like code.** Kubernetes overlays (kustomize) got
   the full RED/GREEN treatment: rendered-manifest witness tests assert
   worker counts, resource limits, ConfigMap fields, and protected
   invariants of sibling environments.
   The video shows a rendered-manifest test bouncing RED against a fixture
   overlay, then GREEN after a minimal change — infrastructure inside the
   same judged-FR pipeline as Python.
2. **Sizing rules come from live falsification, not local probes.** A local
   memory probe was falsified by a live load-test series run against the
   real environment, which crashed the predicted ceiling from both sides.
   The graduated rule is a *coherence inequality* (`limit ≥ baseline +
   pool_size × per-call + headroom`) encoded as a witness test, so the
   defect class is unrepresentable, not just fixed. The video states the
   inequality with illustrative placeholder values, never the deployment's
   measured constants. Strongest available demonstration of Commandment 9
   (operational truth) on real money.
3. **GitOps closes the loop with evidence, not hope.** Merges deploy via
   ArgoCD; the FR is not closable until a post-rollout evidence artifact
   records read-only observations (worker readiness, deployed limits,
   OOM/restart status) from the live environment. Plan → judge → enforce →
   **observe** — the R-1 evidence stage is the process's answer to "it
   merged, ship it."
4. **The boundary extends to browsers and phone lines.** Enterprise web
   surfaces were driven by agent browser control (Playwright-instrumented
   integrated browser, per-frame UA normalization to defeat embedded-client
   detection), and the platform itself is verified black-box by a sibling
   harness that places *real phone calls*: LLM persona callers (elderly,
   intoxicated, Swedish-speaking, jailbreak probes), live TTS/STT over
   Twilio, diarised offline transcription, and LLM judges scoring
   data-capture and safety — behaviour assertions, not string matches.
   `mock_escape_hatch` at system scale: the test exercises the physical
   phenomenon (a phone call), and parallel-call stress batches surfaced
   limits that unit tests never could.

Scene sourcing for beat 4: narration distilled from the aliased digest above
(committed in this FR); visuals are freshly rendered *generic* frames — a
kustomize witness test run against a sanitized fixture overlay committed
under the example, an inequality graphic, and a redrawn call-harness
diagram — never screenshots of customer repos, dashboards, or reports.

## Acceptance Criteria (revised by judgement, R-1..R-5 folded)

- [ ] AC-01: `feature-requests/authoring-briefs/fr-898-process-video-brief.md`
      committed; names `examples/demos/process_video/` as the artifact boundary
- [ ] AC-02: `scripts/author.sh` run on the brief produces
      `tmp/draft-authoring-report.md` with Artifacts / Precedent / Validation /
      Repairs / Blocked validation sections listing the process-video paths
- [ ] AC-03: `yamlgraph graph lint examples/demos/process_video/graph.yaml`
      passes; smoke/build command recorded in
      `examples/demos/process_video/demo-output.log`
- [ ] AC-04: typed `script.json` generated from committed inputs only; a
      deterministic validator proves all five mandatory beats present
- [ ] AC-05: scene entries carry narration, visual spec, duration hint; total
      duration validates within 600–900 seconds
- [ ] AC-06: every command-backed terminal still in `manifest.json` maps PNG
      → command → exit code from the build run; no mocked terminal output
- [ ] AC-07: narration synthesized per scene by the example-local TTS adapter
      (declared `elevenlabs` dependency); provider + voice id recorded per
      audio file; no human recording
- [ ] AC-08: ffmpeg assembler produces `final.mp4`; validator confirms
      referenced audio/stills exist and final duration is 600–900 s
- [ ] AC-09: redaction validation over `script.json`, `manifest.json`,
      generated text surfaces, and frame-source metadata finds no
      sibling-repo names, customer identifiers, absolute home paths, private
      PR/issue ids, phone numbers, hostnames, cloud project ids, or
      field-deployment measurement constants
- [ ] AC-10: beat-4 visuals rendered only from fixtures committed under
      `examples/demos/process_video/fixtures/`; human meaning-level redaction
      review recorded in the authoring report before any upload
- [ ] AC-11: `docs/feature-request-methodology.md` gains the v1 URL and an
      explicit v2 pending-upload marker (actual v2 URL only after operator
      upload, follow-up commit); `docs/development-process.md` gains the
      matching pointer
- [ ] AC-12: changelog fragment + diary reflection committed; FR updated with
      implementation status, decisions, deviations

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| NotebookLM / external AI video generator | REJECTED by operator (2026-08-28): route is agent-generated in-repo. Also fails reproducibility — assets not regenerable by committed command. |
| Manual recording (screen capture + human narration) | REJECTED by operator: defeats the self-demonstration value; the video about the agentic process should be producible by the process. |
| Storyboard pipeline with generated imagery (z-image/wan-2.2 as v1-style visuals) | REJECTED for the usage arc: generated imagery cannot show *actual usage*; real terminal frames are the point. Retained only as optional title-card garnish — not in scope. |
| Shorts-first (2–3 cut-downs, no long-form) | DEFERRED: operator chose long-form. Shorts are a natural follow-up FR once `script.json` scene structure exists to cut from. |
| Extend `generate_videos.py` in place | REJECTED: that tool is image-pair interpolation via Replicate; this is stills+audio slideshow. Shared ffmpeg concat idea, different contract — new example, honest precedent citation. |
| Chatterbox TTS (CAP-100) for narration | REJECTED (operator, 2026-08-28): local demo-grade voice; a published artifact carries a production-grade voice — example-local adapter over the declared `elevenlabs` dependency (judgement R-1). |
| Show field-deployment material directly (real load-test reports, ArgoCD UI, call-harness recordings) | REJECTED: source repos are private and the artifacts carry customer identity at the meaning level; beat 4 ships aliased narration + generic fixture visuals only (FR-874 precedent). |
| Do nothing (docs are enough) | REJECTED: `missing_last_leg` — the methodology doc reaches only people already reading the repo; the channels research shows the proclamation calendar is empty and the thesis of external signal requires an artifact in an external channel. |

## Related

- Session a904c468-ac1f-4f63-8fd5-84a3bc239b61 turns 82–94 (thesis origin)
- [docs/feature-request-methodology.md](../docs/feature-request-methodology.md)
- [docs/diary/diary-2026-08-18-missing-last-leg.md](../docs/diary/diary-2026-08-18-missing-last-leg.md)
- [docs/research-publication-channels-2026-08-18.md](../docs/research-publication-channels-2026-08-18.md)
- [examples/storyboard/generate_videos.py](../examples/storyboard/generate_videos.py)
- v1: https://www.youtube.com/watch?v=HNZRFub137I ("Neo-waterfall Behind YAMLGraph")

## Judgement (2026-08-28)

APPROVED WITH REVISIONS — R-1 (repo-owned TTS contract, no `voice_runtime`
dependency), R-2 (publication demoted to human gate), R-3 (evidence closure:
private/session sources are background provenance; R5 thesis committed
in-FR), R-4 (manifest schema + deterministic validator), R-5 (committed
authoring brief). Gates C-1..C-6; scope frozen per D-1..D-8. Full text:
[FR-898-neo-waterfall-video-v2.judgement.md](FR-898-neo-waterfall-video-v2.judgement.md).
- Beat-4 sources are deliberately uncited: they live in private customer
  repositories; the aliased digest in `## Cross-Project Learnings` is the
  complete public-side record (this repo is public — FR-874).

## Judgement (pending)

To be rendered via the sole judge route (`scripts/judge.sh`) — never in this
authoring session.
