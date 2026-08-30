---
type: fix
scope: research
req: REQ-YG-623
---
- **FR-932 Prior-art retrieval reaches the research route**: `build_prior_art`
  gains a `rare_floor` opt-out so a consumer that grounds a context window
  receives ranked hits where an interrupting hook stays silent. Also guards the
  optional FR-814 `import yaml` — `fr-checks.sh` invokes the module with bare
  system `python3` and swallows stderr, so a missing PyYAML had been killing the
  prior-art notification hook silently. (REQ-YG-282)
