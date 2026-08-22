# Task: FR-809 resumed validation — FR-791 negative regression smoke (recon disabled)

Validation-only continuation of the FR-809 authoring run. The v2
orchestrator changes are already authored in the working tree. Do NOT
modify any file unless the smoke exposes a defect in
`examples/api-discovery/graph.yaml` or `examples/api-discovery/prompts/`
— those two surfaces are the ONLY repairable boundary; files under
`examples/api-discovery/steps/` and `examples/api-discovery/tools/` are
frozen under FR-809 and must not be touched for any reason.

AC-02 contract: with `use_recon=false` the FR-791 v1 negative smoke
outcome must be preserved.

## Validation (single smoke — budget discipline)

```bash
yamlgraph graph run examples/api-discovery/graph.yaml --var hypothesis="A public JSON API for municipal library loans" --var purpose="data lookup" --var country="FI" --var domain_hint="example.invalid" --var use_recon=false --full
```

Assertions (read the raw terminal `result`):

- Verdict is `not_found` or `needs_manual`, with non-empty
  `steps_tried` that contains neither `recon` nor `browser-sniff`, a
  plain-language `reason`, and alternatives or manual guidance.

Record the command, quoted raw evidence, outcome, and any repairs in
tmp/draft-authoring-report.md.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
