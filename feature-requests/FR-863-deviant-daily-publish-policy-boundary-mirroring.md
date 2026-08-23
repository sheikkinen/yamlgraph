# Feature Request: deviant-daily Publish Policy and Boundary Constraint Mirroring

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced ahead of judgement — retrospective, see "Honesty note"
**Effort:** 0.5 day (already spent)
**Requested:** 2026-08-23
**First consumer / first event:** the pipeline itself, on 2026-08-23.
Four production failures inside two hours took the daily publisher from
"green for four days" to "cannot publish at all": a vision payload
rejected at 10.9 MB, a day thrown away on a `medium` verdict, a title
rejected by DeviantArt, and a dedup key about to delete a third of the
corpus. The first event was run 32623570851 failing at the describe
step; the last was run 32624747449 publishing
`Melting-Hours-Saloon-of-Copper-Dreams-1371993166`.

**Prior art:** FR-826 is the **parent** — this FR amends two contracts
it froze (R-5 gate policy, R-2 corpus identity) and must be read as a
supersession, not a duplicate. FR-822 supplies the DeviantArt API
contracts whose title limit was never mirrored inward. FR-862 (same
day) added the dispatch surface that made these failures observable and
recoverable within minutes; it is adjacent, not overlapping — FR-862
changed *when* the pipeline runs, this FR changes *what it accepts*.
FR-769/FR-781 hold the vision precedent whose downscaling
`deviant-daily` failed to inherit. No REJECTED prior art occupies this
territory.

## Summary

Four defects, one root cause: **an external system's constraint was
known at its boundary but never mirrored into our model.** Anthropic's
payload ceiling, DeviantArt's title cap, DeviantArt's mature semantics,
and the corpus extractor's inability to recover generation ids were all
visible facts that our schema either ignored or contradicted.

## Value Statement

The daily publisher survives contact with its own dependencies: no day
is lost to a constraint that was knowable at the boundary, and no
silent data loss accumulates behind a green run.

## Problem

### P-1: vision payload exceeded the provider ceiling

Run 32623570851 died at describe:
`image exceeds 10 MB maximum: 10896644 bytes > 10485760 bytes`.
`tools/vision.py` base64-encoded raw bytes with no size handling, while
the yamlgraph precedent it was modelled on
(`examples/shared/vision_tool.py`) has had `_downscale_png_bytes` and a
`thumbnail` cap all along. The roster rotation to 2K/2MP PNG earlier
the same day pushed payloads over the line — the defect was latent from
the start and my roster change fired it.

### P-2: `confidence: medium` threw the day away

FR-826 R-5 froze `confidence == "high"` as the only publishable verdict.
But `prompts/describe_post.yaml` defines `confidence` twice and
incompatibly: as **legibility** ("use high only when the image is
clearly legible") and as **policy risk** ("content DeviantArt forbids
outright must be surfaced as confidence=low"). A model looking at
explicit-but-perfectly-legible art has no honest answer and hedges to
`medium` — which the gate read as "unreadable". Three of four describes
skipped, both on `nudity/sexual` content while a `gore` image passed.
The descriptions themselves were detailed and confident.

### P-3: DeviantArt rejected the title

Run 32624528720: `stash/submit failed: HTTP 400 ... 'title has
incorrect length'`. `PostDescription.title` allowed `max_length=120`;
DeviantArt caps at 50. The gate approved what the API refused.

### P-4: the corpus dedup key was degenerate

1,937 of 5,893 corpus rows carry `source_file: "unknown"` — 33% of the
corpus sharing one identity. `used_source_ids()` is the no-repeat
guard, so publishing any one of them would have excluded all 1,937 from
every future draw. Silently: no error, no log line, just a corpus
quietly two-thirds its stated size. Slot `2026-08-23#1` drew one and
reached `submitted` before this was caught.

### P-5: the publisher had been fitted with guards against its owner

Operator finding, same day: "we are working in a sibling repo and have
lost most of the process controls … severe hedging in place —
complicated dry-run and force flags 'protecting' user from executing
the script."

The sibling repo has no pre-commit hooks and no CI running the suite.
With the real controls absent, FR-862 manufactured substitutes at
runtime and aimed them at the wrong party:

| Hedge | Effect |
|---|---|
| `dry_run` default `true` | the publish button published nothing unless argued with |
| `force` default `false` | a second argument was required to publish after any prior run that day, including a skipped one |
| terminal-slot "idempotent exit" | a deliberate dispatch silently did nothing |
| FR-862 AC-18 "operator approval gate" | a permission system gating the repo owner from his own gallery, written into a judged FR as a GATE condition |
| `outputs/dry-run-post.json` + artifact step | infrastructure existing only to serve the dry-run |
| `parse_flag` + 6 tests | boundary parsing for flags that should not exist |

The ceremony generated its own defect: `-f force=true` silently arrived
as `force: false` (runs 32624905387, 32624943253), a bug that could only
exist because the flag existed.

Related, and the deeper finding: **the absence of acceptance criteria is
what lost the downscaling feature.** FR-863's changes were made before
this FR existed, so no AC pinned "every image is downscaled". Under
pressure from an unrelated failing fixture, the invariant was quietly
traded down to "downscale only when bytes exceed the ceiling" — and only
the operator's review caught it. An AC is the thing that survives
refactoring pressure; FR prose is not.

## Ideal Result

Every constraint imposed by an external system — provider payload
limits, API field limits, identity guarantees the upstream extractor
could not make — is represented in our own model at the point the data
enters, so a violation is impossible to construct rather than merely
unlikely. A hedged model verdict routes to a safer publication mode
instead of discarding the day's work. The publisher never loses a day
to a fact that was knowable before the call was made.

## Proposed Solution

*(as implemented — see Honesty note)*

### S-1: unconditional downscale at the vision boundary

`prepare_for_vision()` runs on **every** payload: no "small enough to
skip" branch, because Anthropic bills by pixel, so a full-size
passthrough is money burned. Long edge capped at `MAX_EDGE = 1568`
(the threshold beyond which Anthropic downscales server-side anyway),
re-encoded to JPEG, quality stepped `85 → 70 → 55` until the payload
fits `MAX_B64_BYTES = 9 MB`. Magic bytes remain authoritative for input
validation (FR-826). **DeviantArt still receives the original
full-size artwork** — only the vision copy shrinks, pinned by a test
asserting the source file is byte-identical afterwards.

### S-2: gate blocks `low` only; `medium` publishes escalated

```python
if post.confidence == "low":
    return GateResult(publish=False, reason="confidence: low", post=post)
if post.confidence == "medium":
    return GateResult(publish=True, post=_escalate_to_mature(post))
return GateResult(publish=True, post=post)
```

A hedge publishes behind DeviantArt's mature gate rather than into the
void: `mature=True, mature_level="moderate"`, preserving the model's own
classification when it supplied one. This **supersedes FR-826 R-5's
high-only rule**.

Dependency: the validator required `mature=true` to carry ≥1
classification, which would have rejected every escalated post. The DA
API accepts `is_mature` with only a level, so that requirement was ours,
not theirs — relaxed to `mature=true requires mature_level`.

### S-3: mirror DeviantArt's title cap inward

`DA_TITLE_MAX = 50`, enforced as a `mode="before"` validator that trims
at a word boundary rather than raising — losing a day's post to a
three-character overrun is the worse failure. The describe prompt now
requests ≤50 characters so trimming is rare rather than routine.

### S-4: stable per-row corpus identity

```python
def row_id(row: dict) -> str:
    source = row.get("source_file") or UNKNOWN
    if source != UNKNOWN:
        return source
    return f"{UNKNOWN}-{hashlib.sha1(row['prompt'].encode()).hexdigest()[:12]}"
```

Real generation ids pass through unchanged; unrecoverable ones get a
deterministic content hash. Corpus content is untouched — this is a
code-side normalization, so FR-826 R-2's provenance and redaction record
still holds. The one already-committed `"unknown"` ledger row now
matches no corpus row and excludes nothing.

### S-5: delete the guards; if it runs, it publishes

`dry_run` and `force` are removed from the workflows, the graph state
and args, and every step function. `parse_flag` is deleted with them.
`publish-now` takes `model` and `date` only — capabilities, not guards,
neither having a "safe" default that disables the tool. Every run takes
the next slot for the day and publishes it; a terminal slot is not a
stop sign.

One behaviour is deliberately kept and is **not** hedging: an in-flight
slot (`drawn`/`submitted`) is resumed rather than duplicated, because
its committed row may already guard a DeviantArt call in flight. That is
FR-826 R-3 external-side-effect correctness, not protection of the
operator from himself.

This **supersedes FR-862's** AC-02, AC-06, AC-07, AC-10, AC-13 and
AC-18, and voids its C-6 approval condition.

## Acceptance Criteria

All witnessed before this FR was written (see Honesty note).

- [x] AC-1: every vision payload is downscaled and re-encoded to JPEG;
      no passthrough branch exists.
- [x] AC-2: long edge ≤ 1568px for any input; witnessed live —
      `vision: 3823602 -> 366026 bytes (1568x890, q85)`.
- [x] AC-3: the source image file is byte-identical after
      `prepare_for_vision`.
- [x] AC-4: `confidence: low` blocks; `high` publishes as declared;
      `medium` publishes with `mature=true, mature_level=moderate`.
- [x] AC-5: `medium` preserves a model-supplied `mature_level` and
      classification instead of overwriting them.
- [x] AC-6: schema failures still block regardless of confidence.
- [x] AC-7: titles > 50 chars trim at a word boundary and remain a
      prefix of the original; ≤50 pass untouched.
- [x] AC-8: two corpus rows with `source_file: "unknown"` receive
      distinct, deterministic ids.
- [x] AC-9: publishing one `unknown` row leaves the others drawable.
- [x] AC-10: 145 tests green, `ruff` clean.
- [x] AC-11: live publication witness — run 32624747449,
      `2026-08-23#1 published`, title 39 chars.
- [x] AC-13: no `dry_run` or `force` appears in any workflow, the graph,
      or any step signature; pinned by
      `test_no_guard_flags_survive_anywhere` and signature tests.
- [x] AC-14: a run whose latest slot is `published` or `skipped` takes
      the next slot and publishes; only an in-flight slot is resumed.
- [x] AC-15: `publish-now` exposes exactly `{model, date}`.
- [x] AC-16: `graph.yaml` change authored through the governed route,
      lint clean; report at `tmp/draft-authoring-report.md`.
- [ ] AC-12: **open** — the describe prompt still overloads
      `confidence` with legibility and policy risk (P-2 root cause).
      S-2 treats the symptom; the field should be split into
      `confidence` (legibility) and `publishable` (policy) so the
      ledger records *which* one blocked. Deferred to its own FR.
- [ ] AC-17: **open** — the sibling repo still has no CI running the
      test suite and no pre-commit hooks. This is the real control whose
      absence P-5 describes; inventing runtime guards was the
      substitute. Deferred to its own FR.

## Risks

**The `medium` escalation publishes content the model hedged about.**
That is the operator's explicit ruling (2026-08-23) and the reason the
mature flag is forced rather than merely permitted. If the hedge was
about legibility rather than policy, the result is a mature-flagged post
with a weak description — recoverable, unlike a lost day.

**Title trimming is silent.** It logs nothing today. A title trimmed
mid-phrase reads as intentional. Worth a log line if it proves frequent.

**AC-12 left open means the skip/publish split still rides on an
overloaded field.** The gate is now permissive enough that this is a
quality question, not an availability one.

## Alternatives Considered

- **Raise on an overlong title instead of trimming.** Rejected: a
  three-character overrun would cost the day's post, and the gate has no
  retry path.
- **Rewrite `prompts/corpus.jsonl` to assign real ids.** Rejected: it
  mutates a corpus whose provenance and human approval FR-826 R-2 froze.
  The code-side `row_id()` achieves identity without touching the
  approved artifact.
- **Downscale only when the payload exceeds the byte ceiling.** This was
  shipped first and is wrong: Anthropic bills by pixel, so a large image
  that happens to compress well still costs full price. Corrected in
  `60c15b3` after the operator caught it.
- **Lower `MAX_EDGE` below 1568 for further savings.** Rejected as
  unmeasured: 1568 is the documented no-loss threshold, and going lower
  trades description quality for cost without evidence.

## Honesty note — enforced ahead of judgement

This FR is **retrospective**. All four changes were written, tested, and
pushed to production before it existed, at direct operator instruction,
while the daily publisher was down. That inverts the Scripture's
Plan → Judge → Enforce order.

What was preserved: every change was condemned by a failing test first
(RED and GREEN in separate commits, visible in `git log`), scope stayed
inside the failing surface, and no change was made that the operator did
not explicitly direct.

What was not: no judgement gated the gate-policy amendment, which
alters public publishing behaviour and supersedes a frozen FR-826
clause. That is exactly the class of change the Judge step exists to
catch. This FR should be judged on whether the shipped behaviour is
**retained**, not on whether it may proceed.

**Commits** (`sheikkinen/deviant-daily`):
`8f32c30` RED → `65bba45` downscale; `fa3a512` edge cap restored;
`23785e7` RED → `60c15b3` publish policy + unconditional downscale;
`ada1b0d` RED → `550a123` title cap + corpus keys;
`cbdc81b` guards removed.

## Related

- `feature-requests/FR-826-deviantart-daily-repo.md` — parent; R-5 (gate
  policy) and R-2 (corpus identity) are amended here.
- `feature-requests/FR-822-deviantart-publish-spike.md` — DA API
  contracts; the title limit belonged in this record.
- `feature-requests/FR-862-deviant-daily-on-demand-publish.md` — the
  dispatch surface that made same-day diagnosis and recovery possible.
- `examples/shared/vision_tool.py` — the downscaling precedent
  `deviant-daily` should have inherited at birth.
- Runs: 32623570851 (payload), 32624528720 (title), 32624747449
  (recovery), 32624387009 (policy witness).
