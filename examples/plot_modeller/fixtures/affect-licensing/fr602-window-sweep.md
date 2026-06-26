# FR-602 Window Sweep (committed dump)

Deterministic gate beat-tolerance sweep on the **post-FR-600** re-annotated
ground truth and the **post-FR-601** classifier output. No LLM, no model run.
Canonical `main_l7` / `_l7_counts` imported read-only and untouched; window 0
ties out to the frozen gate per genre (asserted).

Reproduce:

```bash
cd examples/plot_modeller && ../../.venv/bin/python probe_l7_misses.py --sweep
```

GT deltas: 28  |  pred deltas (on GT beats): 49

| window | affect_recall | affect_precision | recall_hits |
|--------|---------------|------------------|-------------|
| +/-0 | 0.214 | 0.122 | 6 |
| +/-1 | 0.250 | 0.143 | 7 |
| +/-2 | 0.321 | 0.184 | 9 |
| +/-3 | 0.357 | 0.204 | 10 |

**BEAT-OFF recoverable at +/-1** (recall_hits[1]-recall_hits[0]): **1**

**Precision guard** +/-0 -> +/-1: 0.122 -> 0.143 (delta +0.021)

## Genuine +/-1 BEAT-OFF recall members (1)

| genre | GT beat | PRED beat | off | op | char | kind |
|-------|---------|-----------|-----|----|----|----|
| historical-fiction-the-salt-road | F1 | F2 | +1 | open | Naima | loss |

- **historical-fiction-the-salt-road F1 -> F2** (open Naima loss):
  - GT   beat: Moussa Keita, the governor's nephew, announces a royal salt monopoly: all private salt concessions are forfeit to the crown. The small traders will be destroyed.
  - PRED beat: The council votes to comply. Naima has no leverage — the royal seal makes the monopoly law. Everything her father built is being taken.
