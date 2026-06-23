# Genre Plot: Detective Thriller — "The Vanished Witness"

**Genre:** Detective thriller
**Purpose:** Vocabulary stress-test — exercises `lack`, `pursuit`, `exposure`,
`recognition`, `punishment` (the kinds added specifically for this genre).
**Premise:** A witness to a corporate murder disappears the night before trial.
Detective Marren must find the witness, expose the real killer, and survive the
cover-up.

---

## Agents

```
Marren, Lydia, Hagen, Consul Drey, Witness Pell
```

| Agent | Role | Notes |
|-------|------|-------|
| Marren | Detective (hero) | Hired by the court to find Pell |
| Lydia | Marren's partner | Analyst; operates from the office |
| Hagen | Corrupt magistrate (false hero) | Claims to want the trial to proceed; secretly ordered the abduction |
| Consul Drey | Corporate head (villain) | Ordered the original murder; Hagen is his instrument |
| Witness Pell | The vanished witness (victim/donor) | Holds the ledger that proves guilt |

---

## Initial state

### World-truth (`initial_world`)

```json
[
  {"pred": "alive", "args": ["Marren"], "value": true},
  {"pred": "alive", "args": ["Lydia"], "value": true},
  {"pred": "alive", "args": ["Hagen"], "value": true},
  {"pred": "alive", "args": ["Consul Drey"], "value": true},
  {"pred": "alive", "args": ["Witness Pell"], "value": true},
  {"pred": "at", "args": ["Witness Pell", "Safe house"], "value": true},
  {"pred": "holds", "args": ["Witness Pell", "ledger"], "value": true},
  {"pred": "rel", "args": ["Hagen", "Consul Drey"], "value": "co-conspirator"},
  {"pred": "rel", "args": ["Marren", "Lydia"], "value": "partners"},
  {"pred": "faction", "args": ["Hagen", "court"], "value": true},
  {"pred": "faction", "args": ["Consul Drey", "guild"], "value": true}
]
```

### Beliefs (`initial_belief`)

```json
[
  {"observer": "Marren", "fluent": {"pred": "rel", "args": ["Hagen", "Consul Drey"]}, "held": "neutral"},
  {"observer": "Marren", "fluent": {"pred": "at", "args": ["Witness Pell", "Safe house"]}, "held": true},
  {"observer": "Hagen", "fluent": {"pred": "holds", "args": ["Witness Pell", "ledger"]}, "held": true}
]
```

Key epistemic gap: Marren believes Hagen is neutral; the audience knows he is
co-conspirator. This is the dramatic irony that `exposure` resolves.

---

## Goals

```json
[
  {"pred": "alive", "args": ["Witness Pell"], "value": true},
  {"pred": "at", "args": ["Witness Pell", "Court"], "value": true},
  {"pred": "holds", "args": ["Marren", "ledger"], "value": true},
  {"pred": "alive", "args": ["Hagen"], "value": true}
]
```

The detective story goal: the witness survives, appears in court, and the evidence
is secured. Hagen's survival is a goal because the story wants justice, not revenge.

---

## Functions

### F1 — villainy (ch.1)

```json
{
  "id": "F1",
  "kind": "villainy",
  "gloss": "The night before trial, Hagen's hired men abduct Witness Pell from the court safe house and burn the building to destroy evidence.",
  "subject": "Hagen",
  "roles": {"villain": "Hagen", "victim": "Witness Pell"},
  "chapter": 1,
  "observers": ["Marren"],
  "motivation": {"agent": "Hagen", "goal": "protect_Drey"},
  "threatens": {"agent": "Marren", "goal": "deliver_witness"},
  "enables": ["F2"],
  "pre_world": [
    {"pred": "at", "args": ["Witness Pell", "Safe house"], "value": true}
  ],
  "pre_belief": [],
  "eff_world": [
    {"pred": "at", "args": ["Witness Pell", "Safe house"], "value": false},
    {"pred": "at", "args": ["Witness Pell", "Warehouse"], "value": true}
  ],
  "eff_belief": [
    {"observer": "Marren", "fluent": {"pred": "alive", "args": ["Witness Pell"]}, "held": "unknown"}
  ],
  "eff_affect": [{"op": "open", "char": "Marren", "kind": "loss"}]
}
```

### F2 — lack (ch.1)

```json
{
  "id": "F2",
  "kind": "lack",
  "gloss": "Marren arrives at the charred safe house and discovers the witness is gone and the ledger missing — the case collapses without both.",
  "subject": "Marren",
  "roles": {"hero": "Marren"},
  "chapter": 1,
  "observers": ["Marren", "Lydia"],
  "motivation": {"agent": "Marren", "goal": "deliver_witness"},
  "threatens": null,
  "enables": ["F3"],
  "pre_world": [
    {"pred": "at", "args": ["Witness Pell", "Safe house"], "value": false}
  ],
  "pre_belief": [],
  "eff_world": [],
  "eff_belief": [
    {"observer": "Marren", "fluent": {"pred": "holds", "args": ["Witness Pell", "ledger"]}, "held": "unknown"}
  ],
  "eff_affect": []
}
```

**`lack` rationale:** This is the Proppian "discovery of an absence" — the hero
recognizes that something essential is missing. It converts the villainy (external
event) into the hero's quest (internal decision).

### F3 — pursuit (ch.2)

```json
{
  "id": "F3",
  "kind": "pursuit",
  "gloss": "Marren and Lydia trace the abductors through dock manifests and bribed watchmen, narrowing the location to the guild warehouse district.",
  "subject": "Marren",
  "roles": {"hero": "Marren", "helper": "Lydia"},
  "chapter": 2,
  "observers": ["Marren", "Lydia"],
  "motivation": {"agent": "Marren", "goal": "find_Pell"},
  "threatens": {"agent": "Consul Drey", "goal": "silence_witness"},
  "enables": ["F4"],
  "pre_world": [],
  "pre_belief": [
    {"observer": "Marren", "fluent": {"pred": "alive", "args": ["Witness Pell"]}, "held": "unknown"}
  ],
  "eff_world": [],
  "eff_belief": [
    {"observer": "Marren", "fluent": {"pred": "at", "args": ["Witness Pell", "Warehouse"]}, "held": true},
    {"observer": "Marren", "fluent": {"pred": "alive", "args": ["Witness Pell"]}, "held": true}
  ],
  "eff_affect": []
}
```

### F4 — donor_test (ch.3)

```json
{
  "id": "F4",
  "kind": "donor_test",
  "gloss": "Pell, terrified and mistrustful, refuses to leave the warehouse unless Marren can prove the court is not compromised — Marren must reveal what she knows about Hagen's involvement.",
  "subject": "Marren",
  "roles": {"hero": "Marren", "donor": "Witness Pell"},
  "chapter": 3,
  "observers": ["Marren", "Witness Pell"],
  "motivation": {"agent": "Marren", "goal": "earn_trust"},
  "threatens": null,
  "enables": ["F5"],
  "pre_world": [
    {"pred": "at", "args": ["Witness Pell", "Warehouse"], "value": true}
  ],
  "pre_belief": [
    {"observer": "Marren", "fluent": {"pred": "at", "args": ["Witness Pell", "Warehouse"]}, "held": true}
  ],
  "eff_world": [],
  "eff_belief": [
    {"observer": "Marren", "fluent": {"pred": "rel", "args": ["Hagen", "Consul Drey"]}, "held": "suspect"}
  ],
  "eff_affect": [{"op": "open", "char": "Marren", "kind": "betrayal"}]
}
```

**`donor_test` rationale:** The witness is the donor — they hold the ledger (the
"magical agent" in Propp's terms). But they won't hand it over until tested. The
test forces Marren to confront the possibility of Hagen's corruption, which is the
plot's epistemic turn.

### F5 — provision (ch.3)

```json
{
  "id": "F5",
  "kind": "provision",
  "gloss": "Pell, convinced by Marren's honesty, hands over the ledger — a duplicate hidden in his coat lining — and agrees to testify.",
  "subject": "Witness Pell",
  "roles": {"donor": "Witness Pell", "hero": "Marren"},
  "chapter": 3,
  "observers": ["Marren", "Witness Pell"],
  "motivation": {"agent": "Witness Pell", "goal": "seek_justice"},
  "threatens": {"agent": "Consul Drey", "goal": "silence_witness"},
  "enables": ["F6", "F7"],
  "pre_world": [
    {"pred": "holds", "args": ["Witness Pell", "ledger"], "value": true}
  ],
  "pre_belief": [],
  "eff_world": [
    {"pred": "holds", "args": ["Marren", "ledger"], "value": true}
  ],
  "eff_belief": [],
  "eff_affect": [{"op": "close", "char": "Marren", "kind": "loss"}]
}
```

### F6 — exposure (ch.4)

```json
{
  "id": "F6",
  "kind": "exposure",
  "gloss": "In the courtroom, Marren presents the ledger and names Hagen as the one who ordered the abduction — the magistrate's mask falls in front of the assembled court.",
  "subject": "Marren",
  "roles": {"hero": "Marren", "false_hero": "Hagen"},
  "chapter": 4,
  "observers": ["Marren", "Lydia", "Hagen", "Consul Drey"],
  "motivation": {"agent": "Marren", "goal": "expose_corruption"},
  "threatens": {"agent": "Hagen", "goal": "protect_Drey"},
  "enables": ["F7", "F8"],
  "pre_world": [
    {"pred": "holds", "args": ["Marren", "ledger"], "value": true}
  ],
  "pre_belief": [],
  "eff_world": [],
  "eff_belief": [
    {"observer": "Marren", "fluent": {"pred": "rel", "args": ["Hagen", "Consul Drey"]}, "held": "co-conspirator"},
    {"observer": "Lydia", "fluent": {"pred": "rel", "args": ["Hagen", "Consul Drey"]}, "held": "co-conspirator"}
  ],
  "eff_affect": [{"op": "close", "char": "Marren", "kind": "betrayal"}]
}
```

**`exposure` vs `recognition` distinction:** This is why the split matters. Hagen
is *exposed* (false hero unmasked). Marren will be *recognized* (hero acknowledged)
in the next function. The 10-kind vocabulary would collapse both into `reveal`.

### F7 — recognition (ch.5)

```json
{
  "id": "F7",
  "kind": "recognition",
  "gloss": "The court acknowledges Marren's evidence and Pell's testimony; the case against Consul Drey proceeds to sentencing.",
  "subject": "Marren",
  "roles": {"hero": "Marren", "dispatcher": "Court"},
  "chapter": 5,
  "observers": ["Marren", "Lydia", "Witness Pell"],
  "motivation": {"agent": "Marren", "goal": "deliver_justice"},
  "threatens": {"agent": "Consul Drey", "goal": "avoid_prosecution"},
  "enables": ["F8"],
  "pre_world": [
    {"pred": "at", "args": ["Witness Pell", "Court"], "value": true},
    {"pred": "holds", "args": ["Marren", "ledger"], "value": true}
  ],
  "pre_belief": [
    {"observer": "Marren", "fluent": {"pred": "rel", "args": ["Hagen", "Consul Drey"]}, "held": "co-conspirator"}
  ],
  "eff_world": [],
  "eff_belief": [],
  "eff_affect": [{"op": "open", "char": "Marren", "kind": "hidden_blessing"}]
}
```

### F8 — punishment (ch.5)

```json
{
  "id": "F8",
  "kind": "punishment",
  "gloss": "Consul Drey is sentenced to exile; Hagen is stripped of office and barred from the court. The guild's hold on the judiciary is broken.",
  "subject": "Court",
  "roles": {"dispatcher": "Court", "villain": "Consul Drey", "false_hero": "Hagen"},
  "chapter": 5,
  "observers": ["Marren", "Lydia", "Witness Pell"],
  "motivation": {"agent": "Court", "goal": "restore_order"},
  "threatens": null,
  "enables": [],
  "pre_world": [],
  "pre_belief": [
    {"observer": "Marren", "fluent": {"pred": "rel", "args": ["Hagen", "Consul Drey"]}, "held": "co-conspirator"}
  ],
  "eff_world": [
    {"pred": "at", "args": ["Witness Pell", "Court"], "value": true},
    {"pred": "faction", "args": ["Hagen", "court"], "value": false}
  ],
  "eff_belief": [],
  "eff_affect": [{"op": "close", "char": "Marren", "kind": "hidden_blessing"}]
}
```

---

## Causal link graph

```
F1 ──enables──→ F2    (abduction creates the lack)
F2 ──enables──→ F3    (lack motivates pursuit)
F3 ──enables──→ F4    (finding warehouse enables donor test)
F4 ──enables──→ F5    (passing test earns the ledger)
F5 ──enables──→ F6    (ledger enables courtroom exposure)
F5 ──enables──→ F7    (Pell's testimony enables recognition)
F6 ──enables──→ F7    (exposure of Hagen enables case to proceed)
F6 ──enables──→ F8    (exposure enables punishment)
F7 ──enables──→ F8    (recognition enables sentencing)
```

**Partial order (derived from transitive closure):**

```
F1 → F2 → F3 → F4 → F5 → F6 → F7 → F8
                             ↘      ↗
                              F7 ──┘
```

This is mostly linear (detective stories are investigative chains), but F6 and F7
have a genuine concurrent-enablement: F5 enables both the exposure (F6, via ledger)
and the recognition (F7, via Pell's testimony), and both must complete before
punishment (F8).

---

## Affect threads

| Thread | Open | Close | Arc |
|--------|------|-------|-----|
| `loss` (Marren) | F1 (witness vanishes) | F5 (witness recovered) | 4 functions |
| `betrayal` (Marren) | F4 (learns Hagen may be corrupt) | F6 (exposes Hagen) | 2 functions |
| `hidden_blessing` (Marren) | F7 (case succeeds beyond expectations) | F8 (justice delivered) | 1 function |

All threads close. No affect debt at finale.

---

## Vocabulary coverage

**Kinds used:** villainy, lack, pursuit, donor_test, provision, exposure,
recognition, punishment — **8 of 16** kinds.

This is the genre the 16-kind expansion was designed for. The 4-kind alphabet
(`villainy`, `reconciliation`, `return`, `death`) could express only F1 —
everything else (the investigation, the donor-test, the courtroom exposure) would
collapse into glosses with no structural vocabulary.

---

## Observations for v4 planner

1. **Epistemic layer is load-bearing.** The entire plot hinges on belief state:
   Marren's evolving model of Hagen. A planner that skips beliefs cannot generate
   this genre.
2. **`lack` is the genre's structural hinge.** Without it, the story jumps from
   villainy to pursuit with no clear reason why the hero acts. The lack function
   converts external event → internal motivation.
3. **`exposure` ≠ `recognition`.** Collapsing them loses the dual movement of the
   courtroom climax: the villain's mask falls AND the hero is acknowledged. These
   are structurally different events with different preconditions.
4. **Donor test with an unwilling donor.** The witness is not a helpful fairy-tale
   donor — they are a scared, suspicious person. But the structural role is
   identical: hero must pass a test to receive aid. The gloss carries the tone;
   the kind carries the structure.
