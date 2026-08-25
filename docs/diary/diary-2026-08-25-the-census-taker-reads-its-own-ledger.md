# 2026-08-25 — The census taker reads its own ledger

FR-884 went from invoice screenshot to enforced investigation in one day:
census script (TDD), 10 sessions raw-read end-to-end, classifier authored
via the sole route, 74/74 sessions classified by a pinned haiku map,
ranked report, three inbox proposals.

## The traps I hit

**The store outgrew the tool, silently.** `now.py --brief` — built five
weeks ago to give agents situational awareness — had been dead for an
unknown time: the unrotated OTel tap hit 942MB and the full parse blew the
5s hook budget, so the fail-open design delivered silence. Nothing alerted;
the census's own test suite tripped over it by accident. Fail-open without
a liveness witness is fail-silent: the safety property ("never block
session start") ate the function ("brief the session"). The cure was a
bounded tail-read — normalize at the boundary where the unbounded file
enters, not a bigger timeout.

**The guard cannot parse what it cannot imagine.** The FR-767 write-guard
denied a *read* (`graph run`) because a `time` prefix and a multiline
python suffix made the command "unrecognized shape touching governed
artifact — fail closed". Correct behavior for a fail-closed guard, but the
lesson for the operator side: keep command shapes boring near governed
paths. Two other false positives (`SKIP=pytest … | tail`) had the same
grammar-poverty root.

**Chained commands lie about what ran.** A `&&`-chain aborted at a failed
`git add`, so the later `printf > tmp/msg.txt` never executed — and three
subsequent commits reused a stale message file, producing a changelog-gate
failure diagnosed at entirely the wrong layer. `tmp/msg.txt` is shared
mutable state across turns; verify its content, not its existence
(substance_over_presence, applied to my own plumbing).

## The insight

The raw read beat the metric again (read_raw_output_first, in a new key):
the classifier says deploy-watch is 6.3% — a modest bucket. Only reading
the 472-turn transcript shows what that bucket is made of: one-word "poll"
turns each paying 200K–700K prompt tokens of context resend. The
aggregate hides the unit economics; the transcript IS the unit economics.
And the strongest finding needed no construction at all: 18.5% of premium
tokens went to interactive judging while the pinned judge route sat there
— builders_never_call now has a price tag (~120M tokens).

Dogfood note: the classifier itself was the first real fit-tested
delegation of the window — map+reduce, pinned mini model, authored by the
governed route, and the authoring agent caught and repaired a privacy leak
(skeletons in final state) I had not specified against.

**Seed:** the census is a snapshot; adoption gaps only show up as *rates*.
Should the classifier graph run monthly on a cron (window = last 30 days)
and append a one-row time series — so proposals like the judge-adoption
nudge get their acceptance criterion ("interactive judge share < 5%")
measured by the same instrument that justified them?
