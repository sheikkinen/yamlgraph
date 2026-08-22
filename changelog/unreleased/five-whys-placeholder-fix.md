---
type: fix
scope: demos
---
- **five-whys placeholder leak**: Demo prompts mixed bare `{problem}` with Jinja2 blocks; Jinja2 auto-detection rendered the placeholder literally, so the model never received the problem statement. Both templates now use `{{ problem }}`.
