---
type: feat
scope: watcher2
req: REQ-YG-188
---
- **FR-191 Diary Filename Normalization**: Normalize diary filename conventions at creation boundary in watcher2 critique step to prevent CI diary gate failures. Extracts FR number from feature request path, passes as --var fr_num to critique step, adds explicit filename instruction to critique prompt, includes pre-commit hook validation, and makes critique failure blocking. (REQ-YG-188)
