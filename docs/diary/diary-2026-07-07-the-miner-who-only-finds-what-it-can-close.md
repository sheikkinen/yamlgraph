# The Miner Who Only Finds What It Can Close

**Date:** 2026-07-07
**Context:** FR-691 enforce — story_extract pipeline run on the Floodmark canon; 1a/1b diff read for the FR review.

## What happened

The plot-thread extractor worked. Eight threads, four gates green, five throughlines, 36/36 tests. Then the mandated raw read of the artifacts — the AC we put in precisely because gates check shape — found the defect the gates cannot see:

**All eight threads are `status: released`. Zero latent. Zero open.**

The reconcile prompt's design document — the plan itself — contains the worked example: `young_men_grievance`, mined from aschenwulf `internal_tensions` ("see her relationship with Gunnar as a betrayal of the dead"), a loaded gun no event fires. The miner did not find it. It found three *other* latent threads (`gunnar_peacetime_identity`, `heidrun_legacy`, `reinmar_departure`) — and gave every one of them raises, releases, and a closed status. The deficit list that steps 1.5 and 2 were designed to consume is empty.

## The trap

`conflict_dissolution_bias` was diagnosed two days ago as a property of the *story generator*: every conflict the synopsis raises, the synopsis resolves. Today it reproduced inside the *analysis tool built to detect it*. The extractor, asked to find unresolved tension, resolved the tension in the act of finding it. `heidrun_legacy` releases on `heidrun_dies` — the miner read "the old songs will die with her" and concluded the thread *closes* when she dies, which is precisely the reading that de-escalates: her death is the thread's *escalation*, unless someone learned the songs, and nobody did.

This is one level up from `plausible_wrong_answer`. Each thread individually passes shape and reads plausibly. The wrongness is a *distribution*: a canon with three named unfired guns yielding a thread set with zero open threads is statistically damning, but no per-item gate can see it. Gate 3 checks each opposition is non-empty; nothing checks that *the set* contains what the canon's tension inventory predicts it should.

Second, smaller instance of shape-over-substance in the same run: all five grounded threads carry `sources: []` and `justification: ''`. Gate 1 (citation integrity) passes vacuously — an empty list cites nothing false. The gate validates every id that *is* cited; it does not require that anything *be* cited.

## Why the raw read caught it and nothing else could

The Judgement had examined the measurement-FR clause and ruled the gates exempt (validators, not scorers) — but kept AC 4, the 1a/1b diff read, as non-negotiable. That read took minutes: `cat threads_1a.yaml`, `cat thread/*.yaml`, one `grep -h "^status:"`. The `uniq -c` line — `8 status: released` — is the entire investigation. `read_raw_output_first` held again, in a new position: not after a bad score, but after a *green* run. Green gates plus unread artifacts is exactly the compliance theatre the doctrine warns about, wearing a passing test suite as its costume.

## The heuristic

**A detector built from the same model that has the bias will exhibit the bias.** The extractor is an LLM asked to enumerate tensions; the story generator is an LLM asked to invent tensions; both prefer closure because closure is the shape of a satisfying completion. Asking the model to *find* unresolved conflict is still asking it to complete a document about conflict, and its completions resolve. The cure is structural, not exhortative: the prompt must make `status: latent` with empty `raises`/`releases` an *expected, first-class output*, and the gate layer needs a set-level check — zero latents from a canon whose `internal_tensions`/`fears` inventory is non-empty is a suspect result, the same way a filter returning everything is (Commandment 6's inverse: a filter returning *nothing anomalous* deserves the same suspicion).

Candidate trap name for the Scripture, if it recurs: `detector_shares_the_bias` — an LLM stage built to detect a generation bias reproduces that bias in its detections; validate the detector's output *distribution* against an independent inventory, not just its items.

## Consequences recorded

- FR-696 verdict: **Go** — 1b mined three threads the synopsis could not see, each justified by a verbatim canon field quote. The reconcile pass earns its place.
- FR-692/693 are blocked on a prompt-only amendment: latent-mining hardening + `sources` population. Gates and schemas are correct as shipped.
- The second run (post prompt fix) will be the id-stability gate's first non-vacuous exercise — the gate whose first-run vacuity the Judgement named in advance.

**Seed:** Gate 3 checks each thread has opposition; nothing checks the *set* against the canon's tension inventory. Could a set-level gate be mechanical — count entities with non-empty `fears`/`internal_tensions`, require either a citing thread or a waiver per entity? That would make "the miner found only what it could close" a red CI check instead of a diary entry.
