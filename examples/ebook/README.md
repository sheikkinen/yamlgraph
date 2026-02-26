# eBook Pipeline Example

Generates a technical eBook about YAMLGraph development practices using a file-based write→judge→amend pattern.

## Architecture

Each chapter goes through three phases:
1. **Write** - Copilot generates the chapter content to a file
2. **Judge** - Copilot reviews the file and appends a `## JUDGMENT` section
3. **Amend** - Copilot fixes issues based on judgment, removes judgment section, overwrites file

```
write_introduction → judge_introduction → amend_introduction
        ↓
write_doctrine → judge_doctrine → amend_doctrine
        ↓
       ...
```

**Key insight**: All data flows through files. No subgraphs, no complex state mapping.

## Chapters

| # | Filename | Topic |
|---|----------|-------|
| 00 | introduction.md | eBook overview and YAMLGraph philosophy |
| 01 | doctrine.md | The 10 Commandments (verbatim from `.github/copilot-instructions.md`) |
| 02 | precommit-gates.md | Pre-commit hooks and CI enforcement |
| 03 | chaplain-pipeline.md | Research→Plan→Judge→Execute workflow |
| 04 | inquisitor.md | Error handling and correction rites |
| 05 | diary-system.md | Metacognitive reflection patterns |
| 06 | traceability.md | ADR-001 requirement traceability matrix |
| 07 | yamlgraph-core.md | How it works, how to use it, how to extend it (compilation, node types, patterns, production) |
| 08 | wizard.md | The wizard behind the curtain: engine internals, linter, radon, vulture, jscpd, quality toolchain |

## Usage

### Parallel (recommended)

```bash
# Run all chapters with 2 parallel workers (default)
./examples/ebook/run-chapters.sh

# Custom workers and output directory
./examples/ebook/run-chapters.sh 3 docs/ebook/v1

# Sequential (safe mode)
./examples/ebook/run-chapters.sh 1
```

### Single chapter

```bash
yamlgraph graph run examples/ebook/graph-ch07.yaml \
  --var output_dir=docs/ebook/v1 \
  --var filename=07-yamlgraph-core.md \
  --full
```

## Prompts

```
prompts/
├── chapter/           # Per-chapter writing prompts
│   ├── introduction.yaml
│   ├── doctrine.yaml
│   ├── precommit_gates.yaml
│   ├── chaplain_pipeline.yaml
│   ├── inquisitor.yaml
│   ├── diary_system.yaml
│   ├── traceability.yaml
│   └── compilation_pipeline.yaml
│   └── wizard.yaml
├── judge/
│   └── chapter.yaml   # Universal judgment prompt
└── amend/
    └── chapter.yaml   # Universal amendment prompt
```

## Requirements

- `allow_all_paths: true` - Copilot needs file system access
- `allow_all_tools: true` - Copilot uses read/write tools

## Related

- [FR-103](../../feature-requests/FR-103-ebook-inquisitor-subgraph.md) - Feature request
- [copilot-instructions.md](../../.github/copilot-instructions.md) - Source doctrine
