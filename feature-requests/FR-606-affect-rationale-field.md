# Feature Request: Optional affect rationale field (default-off legibility)

**Priority:** LOW
**Type:** Enhancement
**Status:** CLOSED — DELIVERED (2026-06-26)
**Effort:** 0.5 day
**Requested:** 2026-06-26

## Summary

Add an **optional, default-off** `rationale` output field to the affect-detection
prompts so each emitted `(op, kind, beat)` delta can carry a one-clause, beat-quoted
justification. The field is a **diagnostic instrument**, not a scored output: it lets a
human (or the next spike's autopsy) read *why* the model placed an emotion on a beat
without hand-archaeology of the prose. It is OFF by default so production runs and the
frozen gate are byte-for-byte unaffected.

## Value Statement

The FR-605 referent mismatch took manual prose archaeology to find; an optional
beat-quoted rationale would have surfaced it automatically, turning the next affect
autopsy from hours of reading into a `grep`.

## Judgement (2026-06-26)

**Verdict: Authority GRANTED, with two corrections.** This is a cheap, clean, low-risk
legibility instrument that pays a real cost the arc keeps re-paying — FR-605's referent
diagnosis took manual prose archaeology, and I myself had to reconstruct the localization
autopsy by hand to verify it. Default-off keeps the frozen gate and production path
byte-identical; the hard ≥3-word beat-quote constraint correctly defends the FR-598 "novel"
trap; and putting the quote check in the **harness** (code), not the model, is the right
prompt-contract discipline (don't ask a stateless worker to self-validate the one job it
can't be trusted on). Two corrections bind the grant.

1. **(secondary) The rationale field is a PROBE that perturbs — it explains the explain-mode
   run, not the default-off production emission.** Adding a "justify yourself" field changes
   the model's output distribution (the rationalization/observer effect): the placement it
   emits *with* a rationale demand may differ from the placement it emits without one. So a
   rationale read during autopsy explains the explain-mode draw, and must not be cited as
   proof about a scored (default-off) draw. The design already gates `rationale` off the
   scored path — state explicitly that explain-mode draws are kept separate from scored
   draws and never mixed in a recall number.

2. **(secondary) Sequence it before/with FR-607 so the autopsy is actually free.** This
   field's value is realized only if a future autopsy consumes it; standing alone it is
   latent tooling. Land it as part of (or immediately before) the FR-607 goal spike, whose
   Value Statement already names it as the instrument that makes the referent autopsy a
   `grep`. Otherwise it risks being a default-off field nothing ever turns on.

**Endorsed:** default-off schema parity (diff-proven), hard quote constraint with a
code-side checker, frozen gate untouched, lives only in gitignored draw dumps. A small,
honest instrument.

**Frozen scope:** an optional `{% if state.explain %}` `rationale` on `affect_locate.yaml` /
`affect_set.yaml` (≤1 sentence, ≥3 contiguous words quoted from the cited beat, harness-
checked), off the scored path, `evaluate.py` byte-identical, one `--explain` demo logged,
a schema-parity test for explain-off. No scored field, no gate path.

## Problem

FR-605 REFUTED two-pass affect localization and the *real* diagnosis only emerged after
manually reading the beat prose at both the predicted and the gold beat for each miss
(the model attached the right kind to a different but text-valid event — bereavement-loss
F4 vs entrapment-loss F1/F6). The model's reasoning was opaque: the output is bare
`{open, close}` beat ids, so every post-mortem must reconstruct the model's intent by
re-reading the glosses by hand. The detector knows *why* it chose a beat; we throw that
signal away.

This is a legibility gap, not a recall gap. Adding a constrained rationale makes the
model's referent choice **inspectable at the point of emission**, which is exactly the
signal the FR-605 autopsy spent hours reconstructing.

## Proposed Solution

Add an optional `rationale` field to `affect_locate.yaml` (and `affect_set.yaml`),
emitted only when a `state.explain` flag is set (default false). The field is
**hard-constrained** to defeat the FR-598 "novel" trap (haiku returned a 658-token essay
when asked to analyze): one sentence, and it MUST quote the beat text it grounds in.

```yaml
# affect_locate.yaml — added only under {% if state.explain %}
# out (explain mode):
#   open: <beat id or null>
#   close: <beat id or null>
#   rationale: "<=1 sentence; MUST quote >=3 words from the cited beat"
```

- **Default OFF.** With `explain` unset the prompt output schema is byte-identical to
  today; no gate path, no scored field, no cost on production runs.
- **Constrained HARD.** One sentence, max ~30 words, must contain a verbatim >=3-word
  quote from the beat it cites. A rationale that does not quote the beat is a lint
  failure in the spike harness (not the gate).
- **Off the scored path.** `evaluate.py` never reads `rationale`; the frozen gate is
  untouched. The field lives only in the gitignored draw dumps and is summarized by the
  spike's autopsy.
- The spike harness gains an `--explain` flag that turns it on and prints, per miss, the
  model's own one-line reason next to the gold beat's prose — the FR-605 autopsy, for
  free.

## Acceptance Criteria

- [ ] `affect_locate.yaml` / `affect_set.yaml` emit `rationale` ONLY under
      `{% if state.explain %}`; with the flag unset the rendered prompt and output schema
      are byte-identical to the current version (diff proof in the FR).
- [ ] Rationale is constrained: <=1 sentence, must quote >=3 contiguous words from the
      cited beat; the spike harness flags any rationale that fails the quote check.
- [ ] Frozen gate untouched: `evaluate.py` never references `rationale`;
      `git diff --stat examples/plot_modeller/evaluate.py` empty.
- [ ] Spike harness `--explain` flag prints model rationale next to gold prose per miss;
      one demo run logged to `logs/`.
- [ ] No production behavior change: default-off verified by a test asserting schema
      parity between explain-off and the pre-change prompt.
- [ ] Diary reflection added.

## Alternatives Considered

- **Always-on rationale.** Rejected: cost/latency on every production delta for a field
  nothing downstream consumes, and it risks the FR-598 verbose-noise failure on the hot
  path. Default-off confines it to autopsy runs.
- **Free-form rationale (no quote constraint).** Rejected: FR-598 proved an unconstrained
  "explain yourself" prompt yields confident-sounding prose detached from the text. The
  >=3-word beat quote forces grounding and makes the rationale checkable.
- **Do nothing (keep manual autopsy).** Viable but pays the FR-605 archaeology cost again
  on every future affect spike.

## Related

- `feature-requests/FR-605-l7-two-pass-affect-what-then-where.md` — the autopsy this
  field would have automated.
- `docs/diary/diary-2026-06-26-the-emotion-had-the-wrong-referent.md` — referent finding.
- FR-596 -> FR-598 — the "novel" trap that motivates the hard quote constraint.
- `examples/plot_modeller/prompts/affect_locate.yaml`,
  `examples/plot_modeller/prompts/affect_set.yaml`,
  `examples/plot_modeller/spike_affect_twopass.py`.

## Enforcement Outcome (2026-06-26) — DELIVERED

**Status: CLOSED — DELIVERED.** All ACs met; the field is live, default-off, and the
frozen gate is byte-identical.

### What landed

- **`affect_locate.yaml` / `affect_set.yaml`** gained a `{%- if state.explain %}` block
  (`rationale` on locate; a per-kind `reasons:` mapping on set). Whitespace-trimmed so the
  explain-OFF render is **byte-identical** to the pre-change template.
- **`spike_affect_twopass.py`** threads `explain` into both passes, adds the code-side
  `_rationale_quotes_beat(rationale, beat_text, min_words=3)` lint (J: don't trust the model
  to self-validate), and an `--explain` run that prints each delta's reason + quote-verdict
  and **returns before the scored verdict** (J: correction 1 — the rationale demand perturbs
  the distribution; explain draws are never folded into a recall number). Dumps go to a
  separate `results/l7_twopass_explain/`.
- **`tests/test_affect_explain.py`** (9 tests, all green): byte-parity vs golden snapshots
  captured from the pre-change templates (`tests/fixtures/affect_prompts/*.txt`), explain-on
  adds the field, and the quote-check accepts a grounded rationale / rejects an FR-598 novel
  / requires >=3 consecutive words.

### AC verdict

- [x] **AC1 explain-gated + byte-identical off.** Goldens captured pre-edit; parity test
      green for all 3 cases (set, locate-nonrel, locate-rel). `rationale`/`reasons` absent
      when off.
- [x] **AC2 hard quote constraint, harness-checked.** `_rationale_quotes_beat` in code, not
      the model; tests cover positive/novel/two-word cases.
- [x] **AC3 frozen gate untouched.** `evaluate.py` not referenced and not modified
      (`git diff --stat examples/plot_modeller/evaluate.py` empty).
- [x] **AC4 `--explain` demo logged.** `logs/fr606-explain-demo.log` — live haiku draw,
      **9/9 rationales quoted >=3 consecutive words** from a cited beat (zero novels).
- [x] **AC5 no production change.** Schema-parity test asserts explain-off == pre-change.
- [x] **AC6 diary.** `docs/diary/diary-2026-06-26-the-rationale-that-quotes.md`.

### What the demo showed (free FR-605 autopsy)

The quote-lint passed 9/9 and the reasons were beat-grounded — the FR-598 "novel" did not
recur under the >=3-word constraint. More: the **referent mismatch is now visible at
emission** without prose archaeology. Quest `hope` closed at F8 with the reason quoting
*"the lack is liquidated"* (the kingdom goal) — exactly the proximate-vs-terminal goal split
FR-605 spent hours reconstructing, here readable in one line. This is the instrument
FR-607's autopsy will consume (J: correction 2 — sequenced before/with FR-607).
