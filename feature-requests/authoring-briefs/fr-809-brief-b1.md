# Task: FR-809 resumed validation — FR-791 positive regression smoke (recon disabled)

Validation-only continuation of the FR-809 authoring run. The v2
orchestrator changes are already authored in the working tree. Do NOT
modify any file unless the smoke exposes a defect in
`examples/api-discovery/graph.yaml` or `examples/api-discovery/prompts/`
— those two surfaces are the ONLY repairable boundary; files under
`examples/api-discovery/steps/` and `examples/api-discovery/tools/` are
frozen under FR-809 and must not be touched for any reason.

AC-02 contract: with `use_recon=false` the FR-791 v1 positive smoke
outcome must be preserved.

## Validation (single smoke — budget discipline)

```bash
yamlgraph graph run examples/api-discovery/graph.yaml --var hypothesis="Statistics Finland publishes official statistics through a PxWeb API" --var purpose="programmatic access to Finnish population statistics" --var country="FI" --var domain_hint="stat.fi PxWeb" --var use_recon=false --full
```

Assertions (read the raw terminal `result`):

- `verdict == "found"`, `profile.platform_family` is PxWeb,
  `profile.url` is a stat.fi PxWeb API URL, `profile.endpoints`
  non-empty, sample data present.
- `steps_tried` contains neither `recon` nor `browser-sniff`.

Record the command, quoted raw evidence (actual profile URL and
endpoints), outcome, and any repairs in tmp/draft-authoring-report.md.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
