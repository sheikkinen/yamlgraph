# Diary — 2026-08-24 — The baseline that plagiarized

**Arc:** FR-876 (minimal LLM training demo on the deviant-daily
corpus): reflect → FR → graph-judge → clone → RED → GREEN → 13-minute
training witness → temperature sheets → rejection table → push.
One day, one governed loop, all evidence committed.

## The trap: author's intuition as evaluation forecast

I wrote into the FR, with full confidence: "Markov fails novelty rarely
and coherence always." The measured result: **167/200 Markov samples
rejected for novelty** — the trigram baseline is a corpus-mosaic
machine, the opposite of my claim. A trigram chain can only walk
observed transitions, so long spans of its output ARE the corpus; I had
mentally filed "dumb model" under "can't reproduce anything" when
mechanically it can *only* reproduce. This is `threshold_encodes_forecast`
wearing a new coat: the FR's prose encoded a forecast about a defect
distribution I had never measured. The judge had already (R-5) forced
the unmeasured *coherence* half of that sentence out of the gates —
but the *novelty* half survived as narrative and was falsified within
the hour by the table it predicted. Neither of us flagged it, because
it wasn't a gate — only a story. Stories in FRs are forecasts too.

## What worked

- **Judge R-2 was the catch of the day:** I designed a boundary for
  *generation* but required committed *training logs with periodic
  samples* — an unfiltered side channel around my own gate. The graph
  judge saw the composition bug (each part correct, the policy
  connecting them leaky) that the author could not.
- **The boundary earned its keep live:** step-4250 training sample
  rejected `novelty:shared_8gram` — memorization onset caught in the
  training log itself, mid-run, by the mechanism under test.
- **`read_raw_output_first` as eval:** the temperature sheets read
  end-to-end produced the sharpest finding — at t1.2 the words die but
  the SYNTAX SKELETON survives (commas, parens, underscores,
  score-blocks). No metric would have said that; one read did.
- **Interleave ritual finally held:** after the tmp/msg.txt strike
  (FR-876 files swept into a parallel session's FR-878 commit), the
  unique-msg-file + staged-check-in-same-command ritual produced clean
  single-concern commits for the rest of the day.

## Heuristic

An FR's *narrative predictions* about measurement outcomes are
forecasts with no gate attached — either delete them, or mark them as
hypotheses the evaluation is allowed to kill. The falsification is not
failure; it IS the demonstration (here: the table taught the opposite
lesson, an 11× pass gain whose mechanism — memorization vs form — was
invisible to intuition).

**Seed:** the boundary rejected 0/800 samples for redaction — the
corpus's extraction-time redaction held through model recombination at
3M params. At what model scale (or corpus contamination rate) does the
first redaction hit appear in generated output? A scaling probe of the
leak rate would put an empirical floor under the "extraction-time
filtering does not transfer" doctrine instead of the current
worst-case assumption.
