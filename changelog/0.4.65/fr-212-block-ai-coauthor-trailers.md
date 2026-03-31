---
type: feat
scope: hooks
req: REQ-YG-215
---
- **FR-212 Block AI Co-Author Trailers**: `commit-msg` hook `block-ai-coauthor` (`scripts/block_ai_coauthor.py`) rejects commits containing AI agent `Co-authored-by:` trailers (Copilot, Claude, ChatGPT, Gemini, GPT-*) with penance liturgy; human co-authors pass unblocked. (REQ-YG-215)
