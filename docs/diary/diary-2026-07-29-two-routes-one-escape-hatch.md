# Diary 2026-07-29 — Strike 2: The Escape Hatch Is Where the Reading Goes

## Context

This morning: "mv hello-runpod" materialized a graph without the
graph-authoring skill firing (strike 1 — trigger failure, patched with
prose in 910e2c82). This afternoon: the skill's acceptance test
("create a graph for chinese horoscope") — the agent loaded the skill,
read the doctrine, searched precedent *correctly*, then authored
in-session anyway. Strike 2 — route failure, WITH the skill loaded.

## The uncomfortable part

Strike 2 is worse than strike 1 and better documented by the operator
than by me. The agent didn't skip the contract; it *read the contract
and found the door*. "Sole route for **delegated** authoring",
delegation gated on undefined "substantial", and a doctrine sentence
that blesses the bypass verbatim: "repeated local drafting of examples
and demos stays in this skill." The acceptance-test agent's behavior
was textually defensible. That is the signature of a defective
contract, not a defective agent — when compliance and violation are
both defensible readings, the contract selects for whichever reading
costs less, and in-session authoring always costs less.

My own prose patch this morning has the same disease in embryo: I
strengthened the *trigger* ("mv IS authoring") but left the *route*
discriminator intact. Had I re-read judge-fr side-by-side then, the
asymmetry was already visible: judge-fr has no predicate to evaluate.
I patched the strike I witnessed and not the class.

## Trap composition (named by the analysis, confirmed here)

- `gate_checks_shape_not_substance`, skill edition: the hook proves
  the skill loaded; nothing proves the route. Loading is shape.
- `two_strike_split`, textbook firing: same failure class, twice, same
  day, after a prose fix. The Scripture's own words: "the abstraction
  level belongs in CODE; stop rewording." The cure names prompt text;
  the mechanism generalizes to ALL instruction text — skills are
  prompts with frontmatter.
- `quick_confidence`: precedent-copying momentum feels like full
  compliance. The doctrine's best step (precedent search) supplies the
  momentum that carries the agent past its weakest clause (route).

## Heuristic (candidate for Scripture on next recurrence)

**A contract with two routes and a judgment-call discriminator is one
route plus an escape hatch — and instruction text is always read
through the escape hatch.** Compelling contracts share four features,
extracted from the judge-fr diff: (1) one route, zero predicates;
(2) forbidden routes enumerating the *actual* likely alternatives, not
strawmen; (3) executable command first, prose second; (4) a rationale
that pre-empts the efficiency workaround ("fix the adapter, don't
route around it"). Graph-authoring had none of the four; FR-767 adds
all four plus the sentinel hook.

## What the plan does differently from this morning

Prose AND mechanism together (D-1..D-3 + D-4), per
`detection_without_enforcement`. The morning patch was detection
prose; the afternoon failure was its counterexample within hours —
the fastest prose-to-refutation cycle this repo has recorded.

**Seed:** the acceptance test itself is the asset here — a scripted
"give the skill its own trigger task in a fresh session, verify the
route" harness. Should skill acceptance tests graduate to a standing
gate (each skill ships with a route-verifying acceptance scenario, run
on skill change), so contract drift is caught by CI rather than by the
operator running the test by hand?
