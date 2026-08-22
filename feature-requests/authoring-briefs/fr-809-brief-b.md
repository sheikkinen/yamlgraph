# Task: FR-809 resumed validation — FR-791 regression smokes with recon disabled

This is a validation-only continuation of the FR-809 authoring run. The v2
orchestrator changes are already authored in the working tree
(`examples/api-discovery/graph.yaml` and prompts — do not modify them
unless a smoke exposes a defect; repair honestly and record it).

AC-02 contract: with `use_recon=false` the FR-791 v1 route and both FR-791
smoke outcomes must be preserved.

## Validation

```bash
yamlgraph graph run examples/api-discovery/graph.yaml --var hypothesis="Statistics Finland publishes official statistics through a PxWeb API" --var purpose="programmatic access to Finnish population statistics" --var country="FI" --var domain_hint="stat.fi PxWeb" --var use_recon=false --full
yamlgraph graph run examples/api-discovery/graph.yaml --var hypothesis="A public JSON API for municipal library loans" --var purpose="data lookup" --var country="FI" --var domain_hint="example.invalid" --var use_recon=false --full
```

Assertions (read the raw terminal `result` for each run):

1. Positive smoke: `verdict == "found"`, `profile.platform_family` is
   PxWeb, `profile.url` is a stat.fi PxWeb API URL, `profile.endpoints`
   non-empty, sample data present; `steps_tried` does NOT contain
   `recon` and does NOT contain `browser-sniff`.
2. Negative smoke: verdict is `not_found` or `needs_manual`, non-empty
   `steps_tried` without `recon`, a plain-language `reason`, and
   alternatives or manual guidance.

Record both commands, full verdict evidence (quote the actual profile
URL and endpoints from the raw output), outcomes, and any repairs in
tmp/draft-authoring-report.md.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
