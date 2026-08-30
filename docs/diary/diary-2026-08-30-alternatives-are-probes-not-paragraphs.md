# Diary — 2026-08-30 — Alternatives Are Probes, Not Paragraphs

## What happened

Operator issued a deliberately absurd challenge: "brew coffee; acceptance:
operator gets coffee, black. Plan as FR — think outside the box." Three
iterations followed, and the gradient between them is the entry.

**v1 (unprompted):** clever framing — human-as-effector inversion
(agent-in-the-loop for the human), prompt-contract clauses applied to a
wetware actuator, one real probe (`shortcuts list`: no coffee automation,
nearest match a shortcut named "Pidä tauko"). But the Alternatives table
was written from priors: "Wolt: 30–45 min, lukewarm" was invented, not
measured. Verdict from operator: weak.

**Push 1 → legacy channels.** "Old solutions would have been UDP broadcast
'EMERGENCY: Coffee needed at desk xxxx'. Witty follow-up: how many did you
get?" I executed the broadcast instead of describing it: 95 bytes to
255.255.255.255:2324 (port per RFC 2324), 5 s ACK window, **0 ACKs** — the
measured answer to "how many": delivery semantics at-most-N cups,
exactly-zero accountability. First census row I could not have written
without running a command.

**Push 2 → "modern coffee providers unexplored; operator location
unknown."** Both gaps closed by measurement: IP-geoloc + WiFi association +
question-channel ACK triangulated the operator (Oulu, at the machine,
liveness proven by the answered interrupt); live Wolt discovery API
returned **190 deliverable venues, 7 coffee-capable, 5 online, best ETA
20 min** — including a 9.8-rated café I could not have invented. The Wolt
row flipped from "rejected (speculation)" to "measured contingency."

Operator's close: "legit recon, very much out-of-the-box — but I had to
push you several times. This is the level of thinking required for novel
tasks."

## Traps encountered

- **Alternatives-as-rhetoric.** My default "Alternatives Considered" is a
  justification section: a strawman lineup written to lose against the
  already-chosen solution. Kin to `research_as_inventory` but worse —
  inventory at least describes what exists; my v1 table described what I
  *assumed*. Every probe that later replaced a rhetorical row cost one
  command (one datagram, one curl, one CLI call). I skipped them not for
  cost but because generation is my ambient mode: writing plausible
  alternatives *feels like* exploring. `continuation_bias` in census form.
- **Unmeasured premise as latent finding.** "Operator is at the desk" sat
  unexamined in v1; the operator's F2 ("location unknown") was
  pre-mortemable — "the interrupt fired at an empty desk" is exactly the
  witness `pre_mortem` would have written. Every unmeasured assumption in
  an FR is a judge finding in waiting.
- **First-person tool horizon, again.** Every capability the pushes
  "unlocked" (UDP sockets, public discovery APIs, `shortcuts`, `osascript`,
  IP geoloc) was available the entire time. Familiarity filed them under
  "things I know about," not "things I wield" — the same trap recorded at
  the `is_this_a_graph` graduation, new surface.

## What worked

- Executing the joke. The UDP broadcast and the Wolt query turned banter
  into evidence; the absurd task became a real exercise in environment
  probing because each channel was *run*, not narrated.
- The decision table with a held boundary: census the providers, never
  place the order — purchases are deployment gates addressed to the human
  (deployment-gate doctrine holds even for coffee).
- The operator's push-loop itself: "name a channel class not yet probed,"
  asked repeatedly until the census closes. That loop IS the outside-the-box
  method, and it terminates (census closed = every remaining class has a
  stated elimination).

## Heuristic

Every row of an Alternatives table must contain one number or detail that
could not exist without an executed probe. A row without one is a
prediction wearing a disposition. This is `read_raw_output_first` extended
from measurement FRs to alternatives sections — same substance-over-
presence logic, new surface. Second confirmed recurrence graduates it.

## Seed

The push-loop ("is there a channel class I haven't probed? — repeat until
the answer is 'census closed because X'") has a firing moment: FR
authoring, before freezing Alternatives. Could the judge skeleton demand
it mechanically — "name one channel class absent from this census, or
state why the census is closed" — the way the challenge gate demands the
strongest case against?
