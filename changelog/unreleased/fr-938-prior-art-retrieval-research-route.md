---
type: fix
scope: research
req: REQ-YG-623
---
- **FR-938 Prior-art retrieval reaches the research route**: `build_prior_art`
  gains a `rare_floor` opt-out so a consumer that grounds a context window
  receives ranked hits where an interrupting hook stays silent. Also guards the
  optional FR-814 `import yaml` — `fr-checks.sh` invokes the module with bare
  system `python3` and swallows stderr, so a missing PyYAML had been killing the
  prior-art notification hook silently. (REQ-YG-282)
- **FR-938 Retrieval runs on the seam the graph actually uses**: the research
  route's `collect_committed_context` received the whole state as one positional
  dict (the python-node calling convention) while every unit witness passed two
  positional strings, so `brief_path` kept its empty default and the prior-art
  branch was dead in the only caller that matters. The node now reads
  `brief_path` out of that dict, and a witness exercises the call the way the
  graph makes it. First live run emits ranked prior art into the persona context
  and the artifact. (REQ-YG-282)
