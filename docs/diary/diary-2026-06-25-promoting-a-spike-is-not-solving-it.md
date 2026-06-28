# Diary — Promoting a spike is not the same as solving its problem

**2026-06-25 · FR-591 enforcement**

## What happened

I enforced FR-591, which promoted the FR-590 per-character L5 decomposition from
a throwaway Python harness (`spike_perspective.py`) into two real graphs: an
outer map-over-agents driver and an inner per-agent subgraph (summarize → encode
→ assemble). The conversion now lives in YAMLGraph; scoring stays a separate
post-operation; the driver is a shell script.

The Judge had GRANTED authority but on a **re-scoped contract** with four binding
corrections. The most important one (J1) was a trap I had walked straight into
when *writing* the FR: I had argued to "freeze the direct `pre_world`+`eff_world`
encoding" because that run held recall ~0.53. The Judge caught that this is the
same run whose `pre_world` was 81% garbage (precision 0.21) — I had conflated
"this contract held recall" with "this contract is clean." The honest shape is a
trilemma (direct = recall-but-junk-pre; eff-only+diff = lossy 0.25; per-agent
precise pre = unsolved), and the consistent move — since the FR defers the metric
anyway — is to carry the contract as **provisional / precision-open**, not frozen.

## The cognitive trap

**`metric_held_means_contract_clean`.** A number surviving a threshold is not the
same as the mechanism behind it being sound. Recall 0.53 was real; it was also
produced by flooding `pre_world` with low-precision guesses. The recall passed
*because of* the precision wound, not despite it. When I wrote the FR I let the
one green number license a "freeze" decision, hiding the 81%-garbage cost in a
different slice of the same output.

The smoke run made this concrete and honest: fresh detective recall 0.50 (≈
run-1), predicate precision 0.15. The recall is preserved; the precision wound is
exactly where the label says it is. The graph is a *diagnosable pipeline*, not a
solved L5 — and the README/AC/prompt-header now say so in three places.

## What made the enforcement boring (good)

Three corrections were mechanical once named: move `_parse_beats` into
`tools.py` (it lived only in the file being deleted), remove the rejected
eff-only+diff helper and its four tests, and smoke-run one fixture instead of
trusting lint. The fourth — the contract re-scope — was the only one that
required reconciling my *own prior words*: the FR still carried a "Judgement
Notes #1: freeze direct" line contradicting the granted judgement. I struck it
through with a provenance note rather than deleting it, so the record shows the
correction happened.

## A design honesty I almost skipped

The FR's literal YAML used `input_mapping: auto`. The proven reference
(`image_pipeline`) uses *explicit* mappings, and explicit makes the forwarded
fields self-documenting. I deviated — and recorded the deviation in the
enforcement-result section rather than silently "implementing the FR." Same for
`state_key: perspective` on the subgraph sub-node (so the collected shape is a
clean record) and the dual-mode `combine_perspectives`. Deviations that aren't
written down are how a plan and its code drift apart.

## Heuristic

When a metric is cited to justify freezing a contract, ask which *other* slice of
the same output paid for that number. A recall that rides on a precision flood is
a provisional contract wearing a settled one's clothes. Label the open seam in
the artifact itself (prompt header, AC, README), not only in the FR.

**Seed:** The smoke run scored only the one freshly-converted fixture while
`evaluate.main_l5` reported all five (four stale). Should the `perspective` mode
refuse to evaluate genres it did not just write — or is mixing fresh and stale
L5 a feature for incremental runs? When is "score whatever is on disk" a
convenience and when is it a contaminated number?
