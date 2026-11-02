# Calibration audit

This demo measures whether a decision provider's reported confidence matches
observed accuracy on labeled data. Its mock fixture deliberately reports 0.9
confidence for every answer while answering only 5 of 10 items correctly.

## Run

```bash
tmp/bin/yamlgraph graph run examples/demos/calibration-audit/graph.yaml --full
```

Observed result:

```text
report.ece = 0.4
report.flagged = true
```

The run is keyless because the graph uses the deterministic mock decision
provider. The occupied `[0.8,1.0]` bucket contained all 10 items, with mean
confidence 0.9, accuracy 0.5, and gap 0.4.

## Algorithm

The reducer uses five fixed-width confidence buckets:
`[0,0.2)`, `[0.2,0.4)`, `[0.4,0.6)`, `[0.6,0.8)`, and `[0.8,1.0]`.
Buckets are half-open except for the closed final bucket. Empty buckets have
weight 0. Expected calibration error is
`ECE = Σ (n_b/N)·|acc_b − conf_b|`, and the default flagging threshold is
0.15.

calibration is an operator onboarding gate only; no runtime certification or enforcement mechanism exists; and confidence-based production routing is unsupported until the operator runs this audit against representative labeled data for the real provider and records the result.
