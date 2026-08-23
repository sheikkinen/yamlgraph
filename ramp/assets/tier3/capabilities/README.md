# Capability Registry (ramp Tier-3 shape)

Installed by `scripts/ramp.sh` (Tier 3) as the **registry shape only —
no entries**. Each capability is one YAML file in this directory named
`CAP-XX-kebab-name.yaml`:

```yaml
name: Human Readable Capability Name
id: CAP-01
status: active          # or: retired (retired CAPs are skipped)
description: >
  What the capability guarantees, in behavioral terms.
requirements:
  - id: REQ-XX-001      # pick one stable prefix per repo and keep it
    description: >
      One testable requirement. Every requirement must be witnessed by
      at least one test tagged @pytest.mark.req("REQ-XX-001").
```

## Conventions

- Every test function carries `@pytest.mark.req("REQ-XX-NNN")` linking
  it to a requirement here. Register the marker in pytest config:
  `markers = ["req(id): links test to requirement(s)"]`.
- `scripts/req_coverage.py` reports coverage; `--strict` exits non-zero
  on any requirement without a witnessing test.
- Wire the gate into `.pre-commit-config.yaml`:

```yaml
  - repo: local
    hooks:
      - id: req-coverage-strict
        name: req_coverage --strict
        entry: python3 scripts/req_coverage.py --strict
        language: system
        pass_filenames: false
        files: (^tests/|^capabilities/)
        stages: [pre-commit]
```
