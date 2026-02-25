# YAMLGraph Development Pipeline eBook

This directory contains the YAMLGraph development pipeline documentation as an eBook.

## Chapters

- [00. Introduction](00-introduction.md) — Self-documenting machinery; full pipeline overview
- [01. Doctrine](01-doctrine.md) — The 10 Commandments, Sermon, Rite, and Prayer decoded
- [02. Pre-commit Gates](02-precommit-gates.md) — Every hook annotated with purpose and examples
- [03. Chaplain Pipeline](03-chaplain-pipeline.md) — Automated feature planning workflow
- [04. Inquisitor](04-inquisitor.md) — Background compliance audit
- [05. Diary System](05-diary-system.md) — Metacognitive reflection and seed planting

## Authorship

This eBook was authored by the YAMLGraph pipeline itself (FR-100), using:
- Copilot nodes for research (gathering source material from the codebase)
- LLM nodes for writing (drafting chapters from research findings)
- A Python tool for assembly (writing chapters to disk)

## Building

### Prerequisites

Install pandoc (one-time):
```bash
# macOS
brew install pandoc

# Ubuntu/Debian
sudo apt-get install pandoc
```

### Generate eBook

Run the authoring pipeline:
```bash
yamlgraph graph run examples/ebook/graph.yaml \
    --var output_dir=docs/ebook \
    --var date="$(date +%Y-%m-%d)" \
    --full
```

### Render to HTML/PDF

```bash
./docs/ebook/_build.sh

# Outputs:
# - docs/ebook/dist/yamlgraph-dev-pipeline.html
# - docs/ebook/dist/yamlgraph-dev-pipeline.pdf (if LaTeX installed)
```

## Contributing

To update the eBook:

1. Update source material (CLAUDE.md, .pre-commit-config.yaml, etc.)
2. Update research prompts in `examples/ebook/prompts/research/` if needed
3. Update writing prompts in `examples/ebook/prompts/write/` if needed
4. Re-run the authoring pipeline
5. Review the judge's findings
6. Commit the updated chapters

## Related

- [FR-100](../../feature-requests/FR-100-yamlgraph-development-pipeline-ebook.md) — Feature request for this eBook
- [examples/ebook/](../../examples/ebook/) — The authoring pipeline
- [CLAUDE.md](../../CLAUDE.md) — Development guidance
- [.github/copilot-instructions.md](../../.github/copilot-instructions.md) — The Scripture
