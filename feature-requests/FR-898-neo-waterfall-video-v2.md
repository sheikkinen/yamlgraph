# Feature Request: FR-898 Neo-Waterfall Video v2 — Agent-Generated Extended Edition

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 5 days (extended 2026-08-28 with cross-project beat 4 + alias audit)
**Requested:** 2026-08-28
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
ffmpeg assembly, chatterbox TTS CAP-100), and the content question by the
operator's structured answers recorded below (2026-08-28). Running five
personas would re-derive committed prior art.
**Prior art:** Session a904c468 turns 82–94 (Neo-waterfall thesis born at the
operator's R5 correction, 2026-07-18); `docs-planning/plan-interactive-finalize-coordinator.md`
R5 (local); `docs/feature-request-methodology.md` (b06335eb, 2026-07-29 — the
thesis document); `docs/diary/diary-2026-08-18-missing-last-leg.md` (Proclaim
stage named, unbuilt); `docs/research-publication-channels-2026-08-18.md`
(channel map, "two unread instruments plus an empty proclamation calendar");
`examples/storyboard/generate_videos.py` (ffmpeg clip concat); CAP-100
chatterbox multilingual TTS CLI; FR-206 demo-gate (`demo-output.log` as
proclaimable raw material). Graveyard checked: FR-070 rejected visual
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
graph-authoring route, `scripts/author.sh`, per FR-767):

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
5. Evidence close: measured numbers only (census cost, diary count, gate
   counts, load-test ceilings) — no aspirational claims.

**Stage 2 — Screens (deterministic Python tool).** For each scene, capture
stills from actual usage: terminal captures of the real commands running
(freeze-rendered via `termshot`-style rendering or screenshot of executed
output written to PNG), plus framed renders of committed artifacts (FR
excerpts, judgement verdicts, the Scripture). No mocked output: every
terminal frame comes from a command actually executed during the build run
(`mock_escape_hatch` applies to footage too).

**Stage 3 — Narration (TTS).** Chatterbox CLI (CAP-100) synthesizes per-scene
WAVs from `script.json` narration fields.

**Stage 4 — Assembly (ffmpeg, deterministic).** Slideshow assembler pairs
each scene's stills with its narration audio (image duration = audio
duration), concatenates with crossfades into `final.mp4` — direct descendant
of `generate_videos.py`'s concat stage, no Replicate dependency.

**Stage 5 — Proclaim + historical refs (manual gate).** Operator reviews
`final.mp4`, uploads to @voiceresponse, then a one-commit docs change adds
both v1 (HNZRFub137I) and v2 URLs to `docs/feature-request-methodology.md`
and the video pointer to `docs/development-process.md`.

State/redaction boundary: script inputs are committed public docs only; the
screens tool must run in a sanitized demo checkout state (no customer repo
names, no sibling-project paths in framed terminal output) — alias at first
capture, not at review (FR-896 R-4 lesson). Beat 4 is the highest-risk beat:
its source material lives in private customer repositories and enters this
public repo as narration text only, pre-aliased per the rules in
`## Cross-Project Learnings` — no source doc links, no customer or project
names, no PR/issue numbers from private trackers, no phone numbers,
hostnames, or GCP project ids. Numbers and mechanisms are the payload;
identities are not (FR-874 rejection precedent: meaning-level leaks survive
secret-value grepping, so the alias pass is judged, not grepped).

## Cross-Project Learnings (2026-08-28 extension)

The operator ran the neo-waterfall process for months on a production
voice-AI customer platform (referred to here and in all video assets only as
"the field deployment"). Four learnings graduate into beat 4 — each is a
*process* claim demonstrable with aliased numbers, not a customer story:

1. **Infra is enforceable like code.** Kubernetes overlays (kustomize) got
   the full RED/GREEN treatment: rendered-manifest witness tests assert
   worker counts, resource limits, ConfigMap fields, and protected
   invariants of sibling environments (33 witnesses on the latest change).
   The video shows a rendered-manifest test bouncing RED against the live
   overlay, then GREEN after a three-file change — infrastructure inside the
   same judged-FR pipeline as Python.
2. **Sizing rules come from live falsification, not local probes.** A local
   N=15 memory probe was falsified by a live 8-batch load-test series
   (idle baseline 975 MiB, ~157 MiB per processing call, hard ceiling 6
   concurrent at a 2 GiB limit — crashed from both sides as predicted).
   The graduated rule is a *coherence inequality* (`limit ≥ baseline +
   pool_size × per-call + headroom`) encoded as a witness test, so the
   defect class is unrepresentable, not just fixed. Strongest available
   demonstration of Commandment 9 (operational truth) on real money.
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
   phenomenon (a phone call), and parallel-call stress batches found the
   capacity ceiling that unit tests never could.

Scene sourcing for beat 4: narration distilled from the aliased digest above
(committed in this FR); visuals are freshly rendered *generic* frames — a
kustomize witness test run against a sanitized fixture overlay committed
under the example, an inequality graphic, and a redrawn call-harness
diagram — never screenshots of customer repos, dashboards, or reports.

## Acceptance Criteria

- [ ] `script.json` generated by the graph from committed inputs only; all
      five mandatory beats covered (deterministic beat-coverage check)
- [ ] Every terminal still traceable to a command actually executed during
      the build run (capture manifest maps PNG → command → exit code)
- [ ] Narration audio synthesized per scene via chatterbox; no human
      recording
- [ ] `final.mp4` assembled by ffmpeg, duration within 10–15 min, plays with
      synchronized audio
- [ ] Redaction check: no sibling-repo names, customer identifiers, or
      absolute home paths visible in any frame (mechanical grep of capture
      manifest + script text)
- [ ] Beat-4 alias audit: script text and all beat-4 frames contain no
      customer/project names, private PR/issue ids, phone numbers,
      hostnames, or cloud project ids; beat-4 visuals rendered only from
      fixtures committed under the example (meaning-level review recorded
      in the authoring report — grep alone is insufficient per FR-874)
- [ ] `demo-output.log` committed proving the pipeline ran end to end
      (FR-206 demo gate)
- [ ] v1 and v2 YouTube URLs committed in `docs/feature-request-methodology.md`;
      pointer added to `docs/development-process.md`
- [ ] Graph authored via sole route; lint + smoke recorded in authoring report
- [ ] Changelog fragment in `changelog/unreleased/`; diary reflection

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| NotebookLM / external AI video generator | REJECTED by operator (2026-08-28): route is agent-generated in-repo. Also fails reproducibility — assets not regenerable by committed command. |
| Manual recording (screen capture + human narration) | REJECTED by operator: defeats the self-demonstration value; the video about the agentic process should be producible by the process. |
| Storyboard pipeline with generated imagery (z-image/wan-2.2 as v1-style visuals) | REJECTED for the usage arc: generated imagery cannot show *actual usage*; real terminal frames are the point. Retained only as optional title-card garnish — not in scope. |
| Shorts-first (2–3 cut-downs, no long-form) | DEFERRED: operator chose long-form. Shorts are a natural follow-up FR once `script.json` scene structure exists to cut from. |
| Extend `generate_videos.py` in place | REJECTED: that tool is image-pair interpolation via Replicate; this is stills+audio slideshow. Shared ffmpeg concat idea, different contract — new example, honest precedent citation. |
| Show field-deployment material directly (real load-test reports, ArgoCD UI, call-harness recordings) | REJECTED: source repos are private and the artifacts carry customer identity at the meaning level; beat 4 ships aliased narration + generic fixture visuals only (FR-874 precedent). |
| Do nothing (docs are enough) | REJECTED: `missing_last_leg` — the methodology doc reaches only people already reading the repo; the channels research shows the proclamation calendar is empty and the thesis of external signal requires an artifact in an external channel. |

## Related

- Session a904c468-ac1f-4f63-8fd5-84a3bc239b61 turns 82–94 (thesis origin)
- [docs/feature-request-methodology.md](../docs/feature-request-methodology.md)
- [docs/diary/diary-2026-08-18-missing-last-leg.md](../docs/diary/diary-2026-08-18-missing-last-leg.md)
- [docs/research-publication-channels-2026-08-18.md](../docs/research-publication-channels-2026-08-18.md)
- [examples/storyboard/generate_videos.py](../examples/storyboard/generate_videos.py)
- v1: https://www.youtube.com/watch?v=HNZRFub137I ("Neo-waterfall Behind YAMLGraph")
- Beat-4 sources are deliberately uncited: they live in private customer
  repositories; the aliased digest in `## Cross-Project Learnings` is the
  complete public-side record (this repo is public — FR-874).

## Judgement (pending)

To be rendered via the sole judge route (`scripts/judge.sh`) — never in this
authoring session.
