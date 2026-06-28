---
type: feat
scope: plot_modeller
req: REQ-YG-020
---
- **FR-593 Story-Level Vocabulary (deterministic core)**: Add `StoryVocab`
  (`schema/vocab.py`) as the validated structured binding for `extract_vocab` — a bare
  string is rejected, making the FR-592 markdown-string regression impossible to
  reintroduce. Add `canonicalize_glosses` (`nodes/tools.py`): a pure, deterministic,
  additive alias substitution (case-insensitive, longest-alias-first, word-boundary
  aware) that writes a new `canonical_gloss` field and leaves the original `gloss`
  byte-identical, so no other gloss-consuming layer (L4/L6/L7/L8) is perturbed. The
  corpus precision/recall acceptance gate (world_recall ≥ 0.47 over two runs) is a
  separate validation run. (REQ-YG-020)
