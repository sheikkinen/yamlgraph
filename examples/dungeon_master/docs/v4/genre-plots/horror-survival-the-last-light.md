# Genre Plot: Horror/Survival — "The Last Light"

**Genre:** Horror / survival
**Purpose:** Vocabulary stress-test — exercises `death` (the only non-Propp kind),
`struggle` with failed victory, `pursuit` as relentless threat, and affect threads
that *do not close* (the horror signature: unresolved dread).
**Premise:** Three miners trapped underground after a collapse discover the
tunnels are not empty. Something hunts by sound. Their only lamp is running out.

---

## Agents

```
Brynn, Aldric, Fen, The Watcher
```

| Agent | Role | Notes |
|-------|------|-------|
| Brynn | Forewoman (hero) | Level-headed; knows the mine layout |
| Aldric | Explosives handler (helper) | Has one remaining charge; loud, impulsive |
| Fen | New hire (victim) | First week; terrified; makes noise |
| The Watcher | Subterranean predator (villain) | Hunts by sound; never fully seen; not an agent with goals — a force |

---

## Initial state

### World-truth (`initial_world`)

```json
[
  {"pred": "alive", "args": ["Brynn"], "value": true},
  {"pred": "alive", "args": ["Aldric"], "value": true},
  {"pred": "alive", "args": ["Fen"], "value": true},
  {"pred": "alive", "args": ["The Watcher"], "value": true},
  {"pred": "at", "args": ["Brynn", "Deep gallery"], "value": true},
  {"pred": "at", "args": ["Aldric", "Deep gallery"], "value": true},
  {"pred": "at", "args": ["Fen", "Deep gallery"], "value": true},
  {"pred": "holds", "args": ["Brynn", "lamp"], "value": true},
  {"pred": "holds", "args": ["Aldric", "charge"], "value": true}
]
```

### Beliefs (`initial_belief`)

```json
[
  {"observer": "Brynn", "fluent": {"pred": "alive", "args": ["The Watcher"]}, "held": false},
  {"observer": "Aldric", "fluent": {"pred": "alive", "args": ["The Watcher"]}, "held": false},
  {"observer": "Fen", "fluent": {"pred": "alive", "args": ["The Watcher"]}, "held": false}
]
```

Key epistemic state: none of the miners believe The Watcher exists. The audience
knows it does (world-truth: alive = true). This is the horror genre's signature
setup — the threat is real but unrecognized.

---

## Goals

```json
[
  {"pred": "alive", "args": ["Brynn"], "value": true},
  {"pred": "alive", "args": ["Aldric"], "value": true},
  {"pred": "alive", "args": ["Fen"], "value": true},
  {"pred": "at", "args": ["Brynn", "Surface"], "value": true}
]
```

Horror's structural irony: the goals are simple (survive, escape). The genre's
power comes from *failing* to achieve them cleanly.

---

## Functions

### F1 — villainy (ch.1)

```json
{
  "id": "F1",
  "kind": "villainy",
  "gloss": "A secondary collapse seals the main shaft. The three miners are trapped in the deep gallery with one lamp and one explosive charge.",
  "subject": "Collapse",
  "roles": {"villain": "Collapse", "victim": "Brynn"},
  "chapter": 1,
  "observers": ["Brynn", "Aldric", "Fen"],
  "motivation": null,
  "threatens": {"agent": "Brynn", "goal": "reach_surface"},
  "enables": ["F2"],
  "pre_world": [],
  "pre_belief": [],
  "eff_world": [],
  "eff_belief": [],
  "eff_affect": [{"op": "open", "char": "Brynn", "kind": "loss"}]
}
```

**`motivation`: null** — the collapse is a natural event, like the flood in
10030-BC. No intentional agent caused it.

### F2 — departure (ch.1)

```json
{
  "id": "F2",
  "kind": "departure",
  "gloss": "Brynn leads the group deeper into the abandoned tunnels, the only direction that isn't rubble. The lamp flickers.",
  "subject": "Brynn",
  "roles": {"hero": "Brynn", "helper": "Aldric"},
  "chapter": 1,
  "observers": ["Brynn", "Aldric", "Fen"],
  "motivation": {"agent": "Brynn", "goal": "find_exit"},
  "threatens": null,
  "enables": ["F3"],
  "pre_world": [
    {"pred": "holds", "args": ["Brynn", "lamp"], "value": true}
  ],
  "pre_belief": [],
  "eff_world": [
    {"pred": "at", "args": ["Brynn", "Deep gallery"], "value": false},
    {"pred": "at", "args": ["Brynn", "Abandoned tunnels"], "value": true},
    {"pred": "at", "args": ["Aldric", "Abandoned tunnels"], "value": true},
    {"pred": "at", "args": ["Fen", "Abandoned tunnels"], "value": true}
  ],
  "eff_belief": [],
  "eff_affect": []
}
```

### F3 — pursuit (ch.2)

```json
{
  "id": "F3",
  "kind": "pursuit",
  "gloss": "Scraping sounds echo from behind — something large, moving in the dark, pausing when they stop talking. Fen panics and shouts. The sounds accelerate.",
  "subject": "The Watcher",
  "roles": {"villain": "The Watcher", "victim": "Fen"},
  "chapter": 2,
  "observers": ["Brynn", "Aldric", "Fen"],
  "motivation": null,
  "threatens": {"agent": "Brynn", "goal": "protect_crew"},
  "enables": ["F4"],
  "pre_world": [
    {"pred": "alive", "args": ["The Watcher"], "value": true}
  ],
  "pre_belief": [
    {"observer": "Brynn", "fluent": {"pred": "alive", "args": ["The Watcher"]}, "held": false}
  ],
  "eff_world": [],
  "eff_belief": [
    {"observer": "Brynn", "fluent": {"pred": "alive", "args": ["The Watcher"]}, "held": true},
    {"observer": "Aldric", "fluent": {"pred": "alive", "args": ["The Watcher"]}, "held": true},
    {"observer": "Fen", "fluent": {"pred": "alive", "args": ["The Watcher"]}, "held": true}
  ],
  "eff_affect": [{"op": "open", "char": "Brynn", "kind": "guilt"}]
}
```

**Epistemic flip:** This is where the miners' model of reality updates. The belief
`alive(Watcher) = false` flips to `true`. The horror genre's first-act turn is
always this epistemic violation: the world is not what you thought.

**Affect:** Brynn opens guilt because she chose this direction — deeper, toward
the thing.

### F4 — death (ch.3)

```json
{
  "id": "F4",
  "kind": "death",
  "gloss": "Fen stumbles in the dark and cries out. The Watcher takes him. Brynn and Aldric hear it happen but cannot see. When the lamp steadies, Fen is gone.",
  "subject": "The Watcher",
  "roles": {"villain": "The Watcher", "victim": "Fen"},
  "chapter": 3,
  "observers": ["Brynn", "Aldric"],
  "motivation": null,
  "threatens": {"agent": "Brynn", "goal": "protect_crew"},
  "enables": ["F5"],
  "pre_world": [
    {"pred": "alive", "args": ["Fen"], "value": true}
  ],
  "pre_belief": [],
  "eff_world": [
    {"pred": "alive", "args": ["Fen"], "value": false}
  ],
  "eff_belief": [],
  "eff_affect": [{"op": "open", "char": "Brynn", "kind": "retaliation"}]
}
```

**`death` is the non-Propp kind.** In Propp, death is a consequence of villainy
(Function 8). But here it needs its own structural slot because:
1. It is a permanent world-state change (Rule 3: monotonic lifecycle).
2. It opens a new affect thread (retaliation) that didn't exist before.
3. The DM needs to know a character is removed from the cast.

**Goal failure:** `alive(Fen) = true` is a stated goal. This function violates it.
The horror genre's structural signature: goals fail mid-story, and the plan
continues anyway.

### F5 — struggle (ch.4)

```json
{
  "id": "F5",
  "kind": "struggle",
  "gloss": "Aldric detonates his last charge to collapse a side tunnel behind them, buying time. The blast is deafening. The lamp goes out.",
  "subject": "Aldric",
  "roles": {"hero": "Aldric", "villain": "The Watcher"},
  "chapter": 4,
  "observers": ["Brynn", "Aldric"],
  "motivation": {"agent": "Aldric", "goal": "buy_time"},
  "threatens": null,
  "enables": ["F6"],
  "pre_world": [
    {"pred": "holds", "args": ["Aldric", "charge"], "value": true}
  ],
  "pre_belief": [],
  "eff_world": [
    {"pred": "holds", "args": ["Aldric", "charge"], "value": false},
    {"pred": "holds", "args": ["Brynn", "lamp"], "value": false}
  ],
  "eff_belief": [],
  "eff_affect": []
}
```

**No victory follows.** In the quest genre, `struggle → victory` is the canonical
pair. Horror breaks this: the struggle *costs* resources (the charge is gone, the
lamp is out) and buys only time, not resolution. The absence of a `victory`
function is itself structural information.

### F6 — rescue (ch.5)

```json
{
  "id": "F6",
  "kind": "rescue",
  "gloss": "In total darkness, Brynn feels moving air — a ventilation shaft. She and Aldric climb blind, hands on the rock walls, the scraping sounds resuming below.",
  "subject": "Brynn",
  "roles": {"hero": "Brynn", "helper": "Aldric"},
  "chapter": 5,
  "observers": ["Brynn", "Aldric"],
  "motivation": {"agent": "Brynn", "goal": "reach_surface"},
  "threatens": null,
  "enables": ["F7"],
  "pre_world": [
    {"pred": "at", "args": ["Brynn", "Abandoned tunnels"], "value": true}
  ],
  "pre_belief": [],
  "eff_world": [
    {"pred": "at", "args": ["Brynn", "Ventilation shaft"], "value": true},
    {"pred": "at", "args": ["Aldric", "Ventilation shaft"], "value": true}
  ],
  "eff_belief": [],
  "eff_affect": []
}
```

**`rescue` after `pursuit`:** This is the Proppian pair — pursuit (F3) threatens,
rescue (F6) escapes. But in horror, the escape is provisional, not final. The
scraping sounds resume.

### F7 — return (ch.6)

```json
{
  "id": "F7",
  "kind": "return",
  "gloss": "Brynn and Aldric emerge from the shaft into grey daylight. They do not speak. Behind them, the shaft exhales cold air. Something moves, far down.",
  "subject": "Brynn",
  "roles": {"hero": "Brynn", "helper": "Aldric"},
  "chapter": 6,
  "observers": ["Brynn", "Aldric"],
  "motivation": {"agent": "Brynn", "goal": "reach_surface"},
  "threatens": null,
  "enables": [],
  "pre_world": [
    {"pred": "at", "args": ["Brynn", "Ventilation shaft"], "value": true}
  ],
  "pre_belief": [],
  "eff_world": [
    {"pred": "at", "args": ["Brynn", "Surface"], "value": true},
    {"pred": "at", "args": ["Aldric", "Surface"], "value": true}
  ],
  "eff_belief": [],
  "eff_affect": [{"op": "close", "char": "Brynn", "kind": "loss"}]
}
```

**Terminal function.** `enables: []` — no downstream dependencies. But note what
does NOT happen: there is no `victory`, no `punishment`, no `liquidation`. The
threat is not defeated — it is escaped. This is structurally distinct from the
quest and thriller endings.

---

## Causal link graph

```
F1 ──enables──→ F2    (collapse forces deeper movement)
F2 ──enables──→ F3    (entering tunnels triggers pursuit)
F3 ──enables──→ F4    (pursuit leads to Fen's death)
F4 ──enables──→ F5    (death motivates desperate struggle)
F5 ──enables──→ F6    (blast buys time for escape attempt)
F6 ──enables──→ F7    (ventilation shaft leads to surface)
```

**Partial order:** Strictly linear. The horror genre's claustrophobic structure —
there is only one path, no branching, no choices. This is thematically appropriate:
the characters have no agency over the direction, only the pace.

```
F1 → F2 → F3 → F4 → F5 → F6 → F7
```

---

## Affect threads

| Thread | Open | Close | Arc |
|--------|------|-------|-----|
| `loss` (Brynn) | F1 (trapped) | F7 (escaped) | 6 functions — full span |
| `guilt` (Brynn) | F3 (chose to go deeper) | **UNCLOSED** | — |
| `retaliation` (Brynn) | F4 (Fen killed) | **UNCLOSED** | — |

**Two threads do not close.** This is the horror genre's affect signature. In the
saga, all threads close (catharsis). In the thriller, all threads close (justice).
In horror, unresolved affect IS the ending — the guilt of leading them deeper, the
anger at Fen's death, these emotions have no outlet. The survivors escape but are
not healed.

**Structural implication for the validator:** The affect-closure check (Rule 5)
must be genre-aware. A plan that leaves threads open is a *defect* in saga/thriller
but a *feature* in horror. The v4 planner needs a genre parameter that relaxes
Rule 5 for horror premises.

---

## Vocabulary coverage

**Kinds used:** villainy, departure, pursuit, death, struggle, rescue, return —
**7 of 16** kinds.

**Kinds conspicuously absent:**
- No `victory` — the threat is escaped, not defeated
- No `recognition` / `exposure` — no truth is revealed; the Watcher remains unknown
- No `punishment` — the villain faces no consequences
- No `reconciliation` — relationships don't change; they only diminish
- No `liquidation` — the original lack (safety) is not resolved; it is fled

These absences are genre-diagnostic. A planner that knows the genre should
*not generate* these kinds for horror. The vocabulary coverage table in the v3
plan estimated horror at ~65% — this example confirms: 7 of 16 is 44%, but
the 7 used are the *right* 7. The other 9 kinds are structurally inappropriate
for the genre.

---

## Goal evaluation at finale

| Goal | Achieved? | Notes |
|------|-----------|-------|
| `alive(Brynn) = true` | Yes | Hero survives |
| `alive(Aldric) = true` | Yes | Helper survives |
| `alive(Fen) = true` | **No** | Killed in F4 |
| `at(Brynn, Surface) = true` | Yes | Escaped |

**3 of 4 goals achieved.** One character dead. In saga and quest, all goals are
achieved. In thriller, all goals are achieved. In horror, partial goal failure is
the norm — the cost of survival is measured in the goals that failed.

---

## Observations for v4 planner

1. **`death` earns its place.** This is the genre where the non-Propp kind is
   essential. Without it, Fen's removal is either a `villainy` effect (loses the
   structural distinction between "harm" and "permanent removal") or unrepresented.
2. **Unclosed affect is genre-appropriate.** The validator must not reject horror
   plans for open affect threads. Genre metadata (`genre: horror`) should relax
   Rule 5 to a warning rather than an error.
3. **Partial goal failure is genre-appropriate.** Similarly, the goal-reachability
   check (Rule 6) should distinguish "unreachable from the start" (a defect) from
   "rendered unreachable by a death function" (a horror-appropriate plot event).
4. **The `motivation: null` pattern recurs.** The Watcher, like the flood in
   10030-BC, is not an intentional agent. Horror villains are often forces rather
   than characters — Rule 8 (motivated action) correctly exempts them via null.
5. **`struggle` without `victory` is a genre signal.** In quest, they pair. In
   horror, struggle stands alone — the hero expends resources but does not win.
   A genre-aware planner could use this as a generation rule: `if genre == horror:
   do not follow struggle with victory`.
