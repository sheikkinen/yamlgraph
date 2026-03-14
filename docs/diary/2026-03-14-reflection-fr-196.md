# FR-196 Reflection: Portable Chaplain

## What Changed

Relocated Chaplain graphs from `examples/` to `.chaplain/graphs/` for portability:
- `examples/copilot/` → `.chaplain/graphs/copilot/`
- `examples/enforce/` → `.chaplain/graphs/enforce/`
- `examples/philosopher/` → `.chaplain/graphs/philosopher/`

Added `path` field to `PythonToolConfig` for file-path-based Python tool loading.

## Trap Encountered

**downstream_fix**: Initially considered patching import paths in multiple shell scripts. Instead, normalized at the entry point — the tool config — by adding `path` field alongside `module`.

## Cure Applied

**callsite_fix**: Tool loading logic updated at the single point where Python tools are resolved (`tool_parser.py`), not in every script that invokes graphs.

## Seed

Could `.chaplain/` become a self-contained package installable via `pip install -e .chaplain/`? Would enable true portability across projects without copying files.
