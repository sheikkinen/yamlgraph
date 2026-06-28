# Genre Plot: Quest/Adventure — "The Sunken Crown"

**Genre:** Quest / adventure
**Purpose:** Vocabulary stress-test — exercises the **donor sphere** (departure,
donor_test, provision) and the **heroic sphere** (struggle, victory) which are
underused in the saga and thriller examples.
**Premise:** Eira, a scribe's apprentice, must retrieve the Sunken Crown from a
flooded temple to legitimize the new queen before the usurper's army arrives.

---

## Agents

```
Eira, Thane Gault, Ferryman Ossa, Queen Livia, Usurper Kael
```

| Agent | Role | Notes |
|-------|------|-------|
| Eira | Scribe's apprentice (hero) | Knows the temple's layout from old manuscripts |
| Thane Gault | Veteran soldier (helper) | Assigned to protect Eira; distrusts book-learning |
| Ferryman Ossa | Riverlord (donor) | Controls the flooded passage to the temple; tests travelers |
| Queen Livia | Uncrowned queen (dispatcher) | Needs the crown to rally the southern lords |
| Usurper Kael | False king (villain) | Sent raiders to destroy the temple before the crown can be recovered |

---

## Initial state

### World-truth (`initial_world`)

```json
[
  {"pred": "alive", "args": ["Eira"], "value": true},
  {"pred": "alive", "args": ["Thane Gault"], "value": true},
  {"pred": "alive", "args": ["Ferryman Ossa"], "value": true},
  {"pred": "alive", "args": ["Queen Livia"], "value": true},
  {"pred": "alive", "args": ["Usurper Kael"], "value": true},
  {"pred": "at", "args": ["Eira", "Capital"], "value": true},
  {"pred": "at", "args": ["Thane Gault", "Capital"], "value": true},
  {"pred": "at", "args": ["Sunken Crown", "Temple"], "value": true},
  {"pred": "holds", "args": ["Ferryman Ossa", "passage"], "value": true},
  {"pred": "rel", "args": ["Eira", "Queen Livia"], "value": "sworn"},
  {"pred": "rel", "args": ["Thane Gault", "Queen Livia"], "value": "sworn"},
  {"pred": "faction", "args": ["Usurper Kael", "northern_lords"], "value": true},
  {"pred": "faction", "args": ["Queen Livia", "southern_lords"], "value": true}
]
```

### Beliefs (`initial_belief`)

```json
[
  {"observer": "Eira", "fluent": {"pred": "at", "args": ["Sunken Crown", "Temple"]}, "held": true},
  {"observer": "Usurper Kael", "fluent": {"pred": "at", "args": ["Sunken Crown", "Temple"]}, "held": true},
  {"observer": "Eira", "fluent": {"pred": "alive", "args": ["Ferryman Ossa"]}, "held": "uncertain"}
]
```

Key epistemic element: both sides know where the crown is. The race is the source
of tension. Eira is uncertain whether Ossa still lives (the ferryman is a figure
from old manuscripts).

---

## Goals

```json
[
  {"pred": "holds", "args": ["Queen Livia", "Sunken Crown"], "value": true},
  {"pred": "alive", "args": ["Eira"], "value": true},
  {"pred": "alive", "args": ["Thane Gault"], "value": true}
]
```

---

## Functions

### F1 — lack (ch.1)

```json
{
  "id": "F1",
  "kind": "lack",
  "gloss": "Queen Livia summons Eira and Gault: without the Sunken Crown, the southern lords will not swear fealty, and Kael's army will crush them within the month.",
  "subject": "Queen Livia",
  "roles": {"dispatcher": "Queen Livia", "hero": "Eira"},
  "chapter": 1,
  "observers": ["Eira", "Thane Gault"],
  "motivation": {"agent": "Queen Livia", "goal": "legitimize_reign"},
  "threatens": null,
  "enables": ["F2"],
  "pre_world": [],
  "pre_belief": [],
  "eff_world": [],
  "eff_belief": [],
  "eff_affect": [{"op": "open", "char": "Eira", "kind": "guilt"}]
}
```

**Affect:** Eira feels the weight of responsibility — if she fails, the queen
falls. The guilt is not moral guilt but the burden of obligation.

### F2 — departure (ch.1)

```json
{
  "id": "F2",
  "kind": "departure",
  "gloss": "Eira and Gault leave the capital at dawn, traveling south along the flooded river road toward the old temple.",
  "subject": "Eira",
  "roles": {"hero": "Eira", "helper": "Thane Gault"},
  "chapter": 1,
  "observers": ["Eira", "Thane Gault"],
  "motivation": {"agent": "Eira", "goal": "retrieve_crown"},
  "threatens": {"agent": "Usurper Kael", "goal": "prevent_coronation"},
  "enables": ["F3"],
  "pre_world": [
    {"pred": "at", "args": ["Eira", "Capital"], "value": true}
  ],
  "pre_belief": [],
  "eff_world": [
    {"pred": "at", "args": ["Eira", "Capital"], "value": false},
    {"pred": "at", "args": ["Eira", "River road"], "value": true},
    {"pred": "at", "args": ["Thane Gault", "Capital"], "value": false},
    {"pred": "at", "args": ["Thane Gault", "River road"], "value": true}
  ],
  "eff_belief": [],
  "eff_affect": []
}
```

### F3 — donor_test (ch.2)

```json
{
  "id": "F3",
  "kind": "donor_test",
  "gloss": "At the flooded fork, Ferryman Ossa blocks the passage and demands Eira recite the temple's true name from memory — no manuscript, no notes. Gault reaches for his sword but Eira stops him.",
  "subject": "Eira",
  "roles": {"hero": "Eira", "donor": "Ferryman Ossa"},
  "chapter": 2,
  "observers": ["Eira", "Thane Gault", "Ferryman Ossa"],
  "motivation": {"agent": "Ferryman Ossa", "goal": "guard_temple"},
  "threatens": null,
  "enables": ["F4"],
  "pre_world": [
    {"pred": "at", "args": ["Eira", "River road"], "value": true},
    {"pred": "holds", "args": ["Ferryman Ossa", "passage"], "value": true}
  ],
  "pre_belief": [],
  "eff_world": [],
  "eff_belief": [
    {"observer": "Ferryman Ossa", "fluent": {"pred": "rel", "args": ["Eira", "Queen Livia"]}, "held": "worthy"}
  ],
  "eff_affect": []
}
```

**Structural note:** This is the classic Propp donor test — the hero must prove
worthiness not through force (Gault's instinct) but through knowledge (Eira's
domain). The gloss carries the character moment; the kind carries the structural
role: *the hero is tested before receiving aid*.

### F4 — provision (ch.2)

```json
{
  "id": "F4",
  "kind": "provision",
  "gloss": "Ossa ferries them through the flooded gorge and gives Eira a breathing reed — 'the temple is underwater past the second gate.'",
  "subject": "Ferryman Ossa",
  "roles": {"donor": "Ferryman Ossa", "hero": "Eira"},
  "chapter": 2,
  "observers": ["Eira", "Thane Gault"],
  "motivation": {"agent": "Ferryman Ossa", "goal": "guard_temple"},
  "threatens": null,
  "enables": ["F5"],
  "pre_world": [
    {"pred": "holds", "args": ["Ferryman Ossa", "passage"], "value": true}
  ],
  "pre_belief": [
    {"observer": "Ferryman Ossa", "fluent": {"pred": "rel", "args": ["Eira", "Queen Livia"]}, "held": "worthy"}
  ],
  "eff_world": [
    {"pred": "at", "args": ["Eira", "Temple"], "value": true},
    {"pred": "at", "args": ["Thane Gault", "Temple"], "value": true},
    {"pred": "holds", "args": ["Eira", "breathing_reed"], "value": true}
  ],
  "eff_belief": [],
  "eff_affect": []
}
```

### F5 — struggle (ch.3)

```json
{
  "id": "F5",
  "kind": "struggle",
  "gloss": "Inside the flooded temple, Eira dives past the second gate while Gault holds off Kael's raiders who arrived by a different route. The water is black and the reed is her only air.",
  "subject": "Eira",
  "roles": {"hero": "Eira", "helper": "Thane Gault", "villain": "Usurper Kael"},
  "chapter": 3,
  "observers": ["Eira", "Thane Gault"],
  "motivation": {"agent": "Eira", "goal": "retrieve_crown"},
  "threatens": {"agent": "Usurper Kael", "goal": "prevent_coronation"},
  "enables": ["F6"],
  "pre_world": [
    {"pred": "at", "args": ["Eira", "Temple"], "value": true},
    {"pred": "holds", "args": ["Eira", "breathing_reed"], "value": true},
    {"pred": "at", "args": ["Sunken Crown", "Temple"], "value": true}
  ],
  "pre_belief": [],
  "eff_world": [],
  "eff_belief": [],
  "eff_affect": [{"op": "open", "char": "Eira", "kind": "loss"}]
}
```

**Affect:** The `loss` opens because Gault is fighting alone above — Eira cannot
help him and doesn't know if he survives. The structural purpose: the struggle
must cost something emotionally, not just physically.

### F6 — victory (ch.3)

```json
{
  "id": "F6",
  "kind": "victory",
  "gloss": "Eira surfaces with the Sunken Crown in her hands. Above, Gault has driven off the raiders — bloodied but alive. The temple is theirs.",
  "subject": "Eira",
  "roles": {"hero": "Eira", "helper": "Thane Gault"},
  "chapter": 3,
  "observers": ["Eira", "Thane Gault"],
  "motivation": {"agent": "Eira", "goal": "retrieve_crown"},
  "threatens": {"agent": "Usurper Kael", "goal": "prevent_coronation"},
  "enables": ["F7"],
  "pre_world": [
    {"pred": "at", "args": ["Sunken Crown", "Temple"], "value": true}
  ],
  "pre_belief": [],
  "eff_world": [
    {"pred": "holds", "args": ["Eira", "Sunken Crown"], "value": true},
    {"pred": "at", "args": ["Sunken Crown", "Temple"], "value": false}
  ],
  "eff_belief": [],
  "eff_affect": [{"op": "close", "char": "Eira", "kind": "loss"}]
}
```

### F7 — return (ch.4)

```json
{
  "id": "F7",
  "kind": "return",
  "gloss": "Eira and Gault ride north through enemy territory, the crown wrapped in oilcloth against Eira's chest.",
  "subject": "Eira",
  "roles": {"hero": "Eira", "helper": "Thane Gault"},
  "chapter": 4,
  "observers": ["Eira", "Thane Gault"],
  "motivation": {"agent": "Eira", "goal": "deliver_crown"},
  "threatens": {"agent": "Usurper Kael", "goal": "prevent_coronation"},
  "enables": ["F8"],
  "pre_world": [
    {"pred": "holds", "args": ["Eira", "Sunken Crown"], "value": true}
  ],
  "pre_belief": [],
  "eff_world": [
    {"pred": "at", "args": ["Eira", "Capital"], "value": true},
    {"pred": "at", "args": ["Thane Gault", "Capital"], "value": true}
  ],
  "eff_belief": [],
  "eff_affect": []
}
```

### F8 — liquidation (ch.5)

```json
{
  "id": "F8",
  "kind": "liquidation",
  "gloss": "Eira places the Sunken Crown on Queen Livia's head before the assembled southern lords. The oaths are sworn. The lack is liquidated — the kingdom has a legitimate ruler.",
  "subject": "Eira",
  "roles": {"hero": "Eira", "dispatcher": "Queen Livia"},
  "chapter": 5,
  "observers": ["Eira", "Thane Gault", "Queen Livia"],
  "motivation": {"agent": "Eira", "goal": "legitimize_queen"},
  "threatens": {"agent": "Usurper Kael", "goal": "seize_throne"},
  "enables": [],
  "pre_world": [
    {"pred": "holds", "args": ["Eira", "Sunken Crown"], "value": true},
    {"pred": "at", "args": ["Eira", "Capital"], "value": true}
  ],
  "pre_belief": [],
  "eff_world": [
    {"pred": "holds", "args": ["Queen Livia", "Sunken Crown"], "value": true},
    {"pred": "holds", "args": ["Eira", "Sunken Crown"], "value": false}
  ],
  "eff_belief": [],
  "eff_affect": [{"op": "close", "char": "Eira", "kind": "guilt"}]
}
```

**`liquidation` rationale:** This is Propp's K — the original lack (F1) is
resolved. The crown that was missing is now in the queen's hands. The structural
arc: `lack → departure → donor_test → provision → struggle → victory → return →
liquidation` is the complete Proppian quest sequence.

---

## Causal link graph

```
F1 ──enables──→ F2    (lack motivates departure)
F2 ──enables──→ F3    (travel brings hero to donor)
F3 ──enables──→ F4    (passing test earns provision)
F4 ──enables──→ F5    (provision enables the struggle)
F5 ──enables──→ F6    (struggle resolves in victory)
F6 ──enables──→ F7    (crown acquired, hero returns)
F7 ──enables──→ F8    (return enables the coronation)
```

**Partial order:** Strictly linear. This is characteristic of the quest genre —
the hero follows a single path forward. The causal links add no information beyond
temporal order here (confirming H3 from the spine paper test: partial-order value
only emerges with branching).

```
F1 → F2 → F3 → F4 → F5 → F6 → F7 → F8
```

---

## Affect threads

| Thread | Open | Close | Arc |
|--------|------|-------|-----|
| `guilt` (Eira) | F1 (burden of responsibility) | F8 (crown delivered) | 7 functions — full story span |
| `loss` (Eira) | F5 (fear for Gault during struggle) | F6 (Gault survived) | 1 function |

All threads close. No affect debt at finale.

---

## Vocabulary coverage

**Kinds used:** lack, departure, donor_test, provision, struggle, victory, return,
liquidation — **8 of 16** kinds.

This exercises the Proppian donor and heroic spheres almost completely. The quest
genre is the "home genre" for these kinds — they were *designed* for this arc.

**Complementary to other examples:**
- Saga (10030-BC): villainy, reconciliation, return — **3 kinds**
- Thriller (Vanished Witness): villainy, lack, pursuit, donor_test, provision,
  exposure, recognition, punishment — **8 kinds**
- Quest (Sunken Crown): lack, departure, donor_test, provision, struggle, victory,
  return, liquidation — **8 kinds**

Combined, the three examples exercise **14 of 16** kinds. Only `rescue` and
`death` remain unexercised (rescue needs a pursuit+capture arc; death appears in
the horror example).

---

## Observations for v4 planner

1. **The quest is the easiest genre for the planner.** The causal chain is linear
   and the kinds follow Propp's canonical sequence. A small model that knows the
   quest template can generate this with minimal reasoning.
2. **`liquidation` completes the `lack`.** These two kinds are structurally paired
   — a planner should check that every `lack` has a corresponding `liquidation`.
3. **The donor sphere is not optional.** Without donor_test + provision, the hero
   magically has what they need. The test is where the hero *earns* the aid, which
   is the emotional core of the quest — not the struggle itself.
4. **Location tracking matters.** This genre moves the hero through space:
   Capital → River road → Temple → Capital. The `at` predicate is structurally
   load-bearing, unlike the saga where everyone is in the same valley.
