# Diary — 2026-06-26 — The gold we never validated

## What happened

After FR-609 closed the goal-anchoring line as REFUTED, the user pushed past the
aggregate and asked the question the whole arc had skirted: *are the prompts/tasks too
complicated or vague?* Reading the actual LangSmith traces and running a minimal-prompt
ablation on haiku turned a tidy "capability gap" into something more uncomfortable — and
then the user named the thing directly: **a suspicion that the GT emotion scores are
arbitrary, so any score built on them is theatre.**

This entry is about taking that suspicion seriously, because the day's evidence largely
earns it.

## The suspicion, stated precisely

Not "all emotion scoring is meaningless." The sharp version, the one the evidence
supports:

> We scored the model against a **single-author gold** whose own reliability we never
> measured. When several readings of a beat are text-valid, the gold is one sample from a
> distribution of valid answers, not the truth. A recall number against such a gold is
> interpretable **only up to the inter-annotator-agreement ceiling** — and we never
> established that ceiling. So we cannot tell whether recall 0.214 means "the model is
> weak" or "the gold itself would only agree with a second annotator 0.3 of the time."
> The number isn't false. It's **uncalibrated**, and an uncalibrated number presented as
> capability is theatre.

## The root the suspicion points at: there is no emotion in the input

The user's rationale cuts below the label. The fixtures are *synopsis spread over
chapters* — and a synopsis has had the emotion boiled off. I measured it: the scifi
fixture is 13 beats, mean **35.8 words** each, and **0 of 13 glosses contain a single
emotion or interiority word** (felt, ashamed, grief, trembling, heart…). They are pure
third-person event summary — "ARIA pushes a firmware update to 200 implanted lab rats";
"Mara reviews the overnight lab footage and sees the rats." The affect lives only in the
authored `eff_affect` annotation and the `affect_policy`; it was written *alongside* the
events and never *into* them.

So the L7 task is not "find the emotion in the story." It is "guess which event in a plot
outline a reader might choose to attach an emotion to." When the text supplies no
affective signal, the reader supplies all of it — and two readers (the model and the
annotator, or any two annotators) project differently because **the input gives them
nothing to converge on.** This is why the suspicion is right at its strongest: it is not
merely that the gold is one of several valid labels; it is that the source
under-determines *every* label. There is no fact of the matter the gold could be right
about. `0/13` is the measurement of "any interpretation is right."

This subsumes the inter-annotator argument below. Perfect IAA tooling would not save the
score: two careful humans projecting guilt onto thirteen emotion-free event summaries
would disagree not because either is careless but because **there is nothing in the text
to be careful about.** The missing control (a second annotation) would not just reveal
low agreement — it would reveal that agreement is *impossible by construction*.

## What today's evidence shows (the downstream symptoms)

Three independent probes, all pointing the same way:

1. **The referent is drivable to anywhere on the goal chain by prompt wording.** Same
   model, same beats pulled byte-identical from the trace: a rule worded "the goal whose
   pursuit caused the harm" sends scifi guilt to the crusade cluster (`trace_anomaly`); a
   rule worded "the ultimate aim" sends salt-road hope to the most abstract goal
   (`protect_traders`). I moved the answer at will. If the prompt's emphasis selects the
   referent, the referent was never a fact about the story — it was a fact about the
   question.

2. **The metric relaxation that should have rescued the signal recovered nothing.**
   Chain-adjacent scoring (credit a pick within k hops of GT on the goal graph) held flat
   at 0.059 for k=0,1,2, because the full-prompt picks are 5+ hops away or in
   *disconnected* components — `expose_ARIA` vs `save_Jonas`, `reach_surface` vs
   `protect_crew`. The "ground-truth" disambiguating graph is itself fragmented and partly
   backwards (`derive_goal_graph` produced `expose_ARIA enables trace_anomaly` and
   `protect_traders enabled_by` the *antagonist's* goal). The scaffold we used to defend
   the gold is broken.

3. **Two text-valid readings were documented long ago and scored as one error.** The
   research note already recorded that horror `loss` can be losing Fen *or* the
   entrapment, and quest `hope` the kingdom saved *or* the crown retrieved — both grounded
   in the beats. The gate counted the model's choice of the other valid reading as a
   `wrong_beat` miss. That is the suspicion, already sitting in our own prose, unlabeled.

So the referent layer of the gold is arbitrary in the strong sense (I can drive it), and
the placement layer is arbitrary in the weaker but real sense (multiple text-valid
endpoints, one picked). Neither layer's reliability was ever measured.

## The trap: gold_validated_by_authorship

I spent five FRs and two model scales doing metric archaeology on a ruler I never
calibrated. The gold *felt* like truth because we wrote it carefully — but care in
authorship is not the same as reliability across authors. Every recall number in the arc
silently assumed inter-annotator agreement ≈ 1.0, and we never collected the second
annotation that would test it. The whole arc optimized **agreement with one annotator's
choices among valid alternatives** and reported it as **capability**. The model's failure
mode and our measurement's failure mode are the same shape (an identifier standing in for
a referent), one level apart — and the deepest version of that shape is this: *we treated
our own labels as the referent when they were only our identifier for it.*

And one level deeper still: the labels pointed at a referent the **input never contained.**
Calibrating the gold (the heuristic I first reached for) is necessary but not sufficient —
you cannot calibrate your way to reliability on a text that holds no signal. The trap has
two floors: *(1)* trusting a gold you never validated, and beneath it *(2)* scoring for a
signal the input was never written to carry. Floor 2 is the user's rationale, and it is the
load-bearing one.

## Heuristic

> **check_the_input_carries_the_signal_before_scoring_for_it.** Before scoring a model's
> ability to locate X in a text, verify the text actually contains X. For affect: count
> interiority/emotion words in the source. If a thirteen-beat fixture has zero, the
> emotion is reader-projected, the construct is not measurable at beat resolution, and
> *no* annotation quality or metric sophistication can rescue the score — the task is
> ill-posed at the input. The cheap probe (grep the source for affective language)
> precedes the expensive one (inter-annotator agreement), and usually settles it: a
> synopsis is a story with the emotion boiled off, so asking where the emotion is
> located in a synopsis is asking a question the input cannot answer.

## Seed

The cheap experiment we never ran is the one that settles the suspicion — and it is
cheaper than a second annotation. **First, grep the fixtures for affective language.** If
the glosses carry ~0 interiority words (the scifi fixture: 0/13), the emotion is
reader-projected and the L7 gate has been scoring a projection against a projection over a
text that licenses neither. **Second, if the input *did* carry emotion, then** re-annotate
the fixtures independently and report an agreement band, not a recall. **Seed:** if affect
is to be evaluated at all, the fixtures must be rewritten from synopsis into *scene* — beats
with interiority the text actually commits to ("her hand stopped over the keyboard") — so
there is a signal to detect and two readers can converge. Otherwise the honest move is to
delete the L7 gate and record the finding that **emotion is not locatable in a plot
outline** — a truth about the construct worth more than every recall number the FR-578→609
arc produced. The whole arc may have been measuring the resolution of the input, not the
capability of the model: you cannot photograph a texture that was sanded off before the
camera arrived.
