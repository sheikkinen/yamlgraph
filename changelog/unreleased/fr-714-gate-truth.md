---
type: feat
scope: ci
req: REQ-YG-542
---
- **FR-714 Gate-Truth Alignment**: bandit (medium+ severity) now gates in pre-commit — the code-analysis skill's "0 medium+" claim finally has enforcement behind it. The five standing findings carry `# nosec` markers with confession entries (B701 jinja prompt templates, 2× B104 dev-server bind defaults, B108 FSM socket prefix, B602 shell tool — the last a pre-existing unconfessed nosec found by judgement). The confession scanner counts nosec alongside noqa; unconfessed nosec fails `--strict`. Coverage gate raised 70 → 85 (measured 90.36%); CLAUDE.md's stale "80%" claim corrected to the enforced value. (REQ-YG-542)
