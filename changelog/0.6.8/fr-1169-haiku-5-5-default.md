---
type: feat
scope: config
req: REQ-YG-043
---
- **FR-1169 Haiku 5.5 is the Anthropic default**: with `ANTHROPIC_MODEL` unset, Anthropic runs now use `claude-haiku-5-5` instead of `claude-haiku-4-5` ($0.10 / $0.50 per MTok against $1 / $5). The 19 example and enforcement graphs and prompts that pinned Haiku 4.5, the script defaults (`req_audit.sh`, `diary_census.sh`, `examples/shared/vision_tool.py`, corpus_census, the plot_modeller spikes), run commands, `.env.sample`, README and reference guides move with it. Haiku 5.5 takes no sampling parameters; `llm_factory` already omits temperature for it. Recorded runs, logs and proofs keep the model they ran on. (REQ-YG-043)
