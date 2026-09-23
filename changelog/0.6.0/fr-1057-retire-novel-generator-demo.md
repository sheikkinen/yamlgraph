---
type: removal
scope: examples
---

- **FR-1057 novel_generator retired from `examples/demos/`**: The demo moved to a private project tree and was removed from the repository along with `tests/integration/test_novel_generator.py`. It carried a defect outside FR-1057's frozen scope — `{synopsis.title}` in a non-Jinja message, which `str.format` resolves by `getattr` against a dict LLM output and so can never render — making a successful `demo-output.log` unobtainable. No capability, `ARCHITECTURE.md` entry, README line, or `demo.sh` entry referenced it.
