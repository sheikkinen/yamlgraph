# The knob that was already there

**Date:** 2026-09-04
**FR:** FR-984 (map fan-out `max_concurrency`), closing an arc that ran
FR-966 → FR-967 → FR-982 → FR-983 → FR-984/985 in one day.

## What happened

A corp census run dropped 100 of 259 rows to Azure 429s and wrote a
fluent brief about the survivors. I diagnosed it as "the map fans out
all 259 rows at once" and started sketching a yamlgraph-side throttle.
Then I asked the Scripture's question — *does the platform already do
this?* — and ran 40 `Send` tasks through LangGraph with
`config={"max_concurrency": 4}`. Peak parallelism: 12 unthrottled, 4
configured. The primitive existed; yamlgraph had simply never passed it.
The fix became three files of plumbing mirroring `recursion_limit`, and
the FR-030 graveyard entry that rejected this exact feature in February
("Send() doesn't natively support concurrency limits") turned out to be
true then and false now.

The probe also falsified my own opening claim. It was not 259-wide; it
was 12-wide, the default pool. I had reported a number I had not
measured because it *sounded* like a measurement.

## Traps

**`fluent_guess_as_measurement`.** Twice today a sentence of mine read
like an observation and was a guess: "fans out all 259 at once" (it
was 12) and an acceptance criterion naming `reduce_pr_ledger` as the
producer of `brief_input` (it is a later node; the judge caught it as
R-5). Both were plausible, specific, and wrong. The tell is a concrete
number or identifier I did not obtain from a command output. Cure:
before writing a number into an FR, name the command that produced it.
If there is no command, it is a hypothesis and must be labelled one.

**`graveyard_glob_blindness`.** My REJECTED-FR sweep grepped
`feature-requests/FR-*.md`. Early FRs are `0NN-*.md`. FR-030 — the
single most relevant precedent, a Won't-Fix of *this feature* — was
invisible to the sweep, and the FR asserted "no rejected FR touches map
concurrency." The judge found it in one read. A sweep that misses the
graveyard's oldest quarter is not a sweep. Cure: `ls feature-requests/
| grep -vE '^FR-'` once, to learn the naming variants, before any
"no prior art" claim.

**`gate_message_describes_intent_not_check`** (third occurrence today).
The diary CI gate said "must include a diary reflection" but checked a
filename regex. The FR-983 judge said "brief absent from the committed
tree" but had read the main checkout. `demo-proof-check` said "fatal
execution marker" but its regex `Node .+ failed` had spanned a 200 KB
line from "Node 20 is deprecated" to a `failed` twenty PR bodies later.
In all three, the prose was a *summary* of what the check was *meant*
to do; the check itself was narrower or looser. Cure: when a gate fires
on an artifact you believe is correct, read the check's source before
the message's text. Three in a day is the graduation bar; proposing it
to the Knowledge Graph.

**`habit_flag`.** I added `--full` to the smoke because the previous
proof had it. The README's documented smoke does not. The flag changed
the artifact's shape (a 200 KB state dump), which triggered both the
identifier hit and the greedy-marker false positive. Neither was a
defect in the graph edit; both were a defect in my invocation. Cure:
regenerate proofs by copying the documented command, not by recalling
the last one.

## What went right

- The platform-primitive probe cost one command and deleted an entire
  implementation from the plan. `does_the_platform_already_do_this` is
  the cheapest question in the canon and I nearly skipped it.
- Sole routes held: research (down, honestly recorded), judge (three
  runs, one false finding caught by a probe, six real revisions
  adopted), authoring (agent caught a defect in *my* brief and recorded
  both attempts). The routes were slower than doing it by hand and
  caught things by-hand would have shipped.
- The judge's R-4 on both successors — "deterministic tests are the
  gate; the paid corp run is an observation" — was a better framing
  than mine, and it decoupled two FRs that I had quietly coupled through
  a shared acceptance criterion.
- Snowball check: since the operator's halt this morning, every step
  was either asked for or a gate the asked-for step required. FR-985 is
  judged, folded, and waiting; it is not started.

## Heuristics

- `command_or_hypothesis`: a number in an FR either names the command
  that produced it or is labelled a hypothesis.
- `read_the_check_not_the_message`: a gate's error text summarises
  intent; its source defines behaviour. Three misreads today.
- `copy_the_documented_command`: proof regeneration uses the README's
  text verbatim, never a remembered variant.
- `graveyard_has_two_namings`: any REJECTED sweep covers both `FR-*` and
  `0NN-*` (and reads Status, not filename).

**Seed:** Every gate in this repo has a message and a check. Could a
census graph map each `::error::` string in `scripts/*.sh` and
`.github/workflows/*.yml` to the regex or command beside it, and ask a
model one question per pair — *does the message promise more, less, or
exactly what the check does?* — so that "message ≠ check" is found by
inventory rather than by three separate incidents in one afternoon?
