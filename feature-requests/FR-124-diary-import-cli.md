# Feature Request: Diary Import CLI Command

**Priority:** LOW
**Type:** Enhancement
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-03-07
**Judged:** 2026-03-07

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted to implement.

**Evaluation:**

1. **Scope: Clear and minimal.** Single responsibility: extract existing import logic → expose via CLI. No speculative extensibility. The `--source` and `--dry-run` flags are the minimal useful surface.

2. **Contradictions/Ambiguities: None blocking.** One edge noted below (Judge's Note #1). All architectural claims verified against codebase.

3. **Acceptance criteria: Measurable.** All 12 criteria are testable. CLI operations, output format, exit codes, error handling, req traceability — all verifiable.

4. **Implementation: Feasible.** Straightforward extract-and-wrap refactoring. The `cmd_*_dispatch()` pattern in `graph_commands.py` and `schema_commands.py` maps directly. `diary_rotate.py` functions (`import_scheduled_entries`, `import_git_reports`) already exist and return counts — upgrading to `ImportResult` is mechanical.

5. **Architecture alignment: Strong.** CLI registration follows `argparse` + dispatch pattern. New `yamlgraph/diary/` package correctly placed (framework-level, not `examples/`). Separation from `examples/shared/diary.py` (write concern) is justified. REQ-YG-122 is the next available requirement ID.

**Verified claims:**
- ✅ `scripts/diary_rotate.py` contains both import functions (return `int`)
- ✅ `examples/shared/diary.py` serves graph node writes (distinct concern)
- ✅ `yamlgraph/diary/` does not yet exist
- ✅ CLI uses `cmd_*_dispatch()` + 2-level argparse subparsers
- ✅ Pre-commit hook at `.pre-commit-config.yaml` runs `diary_rotate.py`
- ✅ `tests/unit/test_diary_rotate.py` exists (321 lines, tagged REQ-YG-063)
- ✅ REQ-YG-122 is available (highest is REQ-YG-121)
- ✅ FR-124 is the correct next FR number (FR-123 is highest)
- ✅ `DIARY = Path("docs/diary.md")` is CWD-relative in existing code — FR is consistent

**Judge's Notes (non-blocking, address during implementation):**

1. **Missing `--source` distinction (Commandment 6 — plausible wrong answer trap).** The behavior table says "Missing source dir → exit 0" without distinguishing *default* missing (normal — no scheduled outputs yet) from *explicit* `--source /typo` missing (user error — should warn). During implementation, consider: if `--source` is explicitly provided and the path doesn't exist, emit a warning line before "Nothing to import." This preserves exit 0 for automation but surfaces the issue for humans. Not a scope change — a refinement within the "Missing source dir" row.

2. **`ImportResult` as `dataclass`.** Appropriate for internal data transfer. Not an LLM output, so Pydantic (Commandment 5) is not required here. Noted for clarity.

## Summary

Add a `yamlgraph diary import` CLI command that exposes the existing `diary_rotate.py` import logic as a user-invocable operation with dry-run support and status reporting.

## Value Statement

Developers maintaining scheduled YAMLGraphs get on-demand visibility into pending imports and can trigger them without waiting for the next commit's pre-commit hook.

## Problem

Scheduled YAMLGraphs (diary digest, git report) deposit output files into `~/scheduled-yamlgraphs/outputs/`. Today, these are only imported into `docs/diary.md` via the `diary-rotate` pre-commit hook — meaning imports happen silently, only at commit time, with no way to:

1. **Inspect** what's pending without reading the filesystem manually.
2. **Import on demand** without making a commit.
3. **Dry-run** to verify new entries before they land in the diary.
4. **Validate** that upstream pipeline outputs are well-formed before import.

The pre-commit hook is fire-and-forget: it doesn't report what it imported, and a failed parse is silent.

## Proposed Solution

### CLI Surface

```bash
# Show pending imports without modifying diary
yamlgraph diary import --dry-run

# Import all pending entries into docs/diary.md
yamlgraph diary import

# Override source base directory (testing, CI)
yamlgraph diary import --source ~/custom-outputs/
```

### `--source` Directory Semantics

The `--source` flag replaces the **base** directory (`~/scheduled-yamlgraphs/outputs/`), preserving the internal subdirectory structure. Both import functions apply their own filename patterns relative to the base:

- `import_scheduled_entries()` globs `{source}/diary_entry_*.md` (flat)
- `import_git_reports()` globs `{source}/git_report/report_*.txt` (subfolder)

This matches the existing `diary_rotate.py` convention where `SCHEDULED_OUTPUTS` is the shared root and `import_git_reports()` appends `git_report/` internally.

### Implementation

#### 1. Shared import module: `yamlgraph/diary/importer.py`

Extract `import_scheduled_entries()` and `import_git_reports()` from `scripts/diary_rotate.py` into a new `yamlgraph/diary/` package. This is CLI-facing core functionality, not an example utility — it belongs in the framework package, not in `examples/shared/diary.py` (which serves graph node write operations).

**Justification for `yamlgraph/diary/` over `examples/shared/`:** The import logic is invoked by the CLI and by the pre-commit hook — both are framework-level entry points. The `examples/shared/diary.py` module provides `write_diary()` for graph nodes (FR-097), a different concern. Separation keeps the import/write responsibilities clear.

The extracted functions gain two changes:
- Accept an optional `source_dir: Path | None` parameter (defaults to `~/scheduled-yamlgraphs/outputs/`).
- Return structured results (`list[ImportResult]`) instead of a bare count, enabling the CLI to report per-file status.

```python
# yamlgraph/diary/importer.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

@dataclass
class ImportResult:
    """Result of importing a single file."""
    filename: str
    entry_type: str          # "World Digest" | "Git Report"
    entry_date: str          # "YYYY-MM-DD"
    status: str              # "imported" | "skipped" | "error"
    message: str | None = None  # Error detail or skip reason


def import_scheduled_entries(
    diary_path: Path,
    source_dir: Path | None = None,
    *,
    dry_run: bool = False,
) -> list[ImportResult]:
    """Import pending diary entries from source directory.

    Globs ``{source_dir}/diary_entry_*.md``.  When *source_dir* is None
    the default ``~/scheduled-yamlgraphs/outputs/`` is used.
    """
    ...


def import_git_reports(
    diary_path: Path,
    source_dir: Path | None = None,
    *,
    dry_run: bool = False,
) -> list[ImportResult]:
    """Import pending git reports from source directory.

    Globs ``{source_dir}/git_report/report_*.txt``.  When *source_dir*
    is None the default ``~/scheduled-yamlgraphs/outputs/`` is used.
    """
    ...
```

#### 2. CLI command: `yamlgraph/cli/diary_commands.py`

Follow the existing argparse + `cmd_*_dispatch()` pattern used by `graph_commands.py` and `schema_commands.py`:

```python
# yamlgraph/cli/diary_commands.py
from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from yamlgraph.diary.importer import import_git_reports, import_scheduled_entries


def cmd_diary_import(args: Namespace) -> None:
    """Import pending scheduled insights into docs/diary.md."""
    diary_path = Path("docs/diary.md")
    source_dir = Path(args.source) if args.source else None
    dry_run = args.dry_run

    if dry_run:
        label = source_dir or "~/scheduled-yamlgraphs/outputs/"
        print(f"📋 Pending scheduled imports ({label}):")

    results = import_scheduled_entries(diary_path, source_dir, dry_run=dry_run)
    results += import_git_reports(diary_path, source_dir, dry_run=dry_run)

    if not results:
        print("Nothing to import.")
        return

    has_errors = False
    for r in results:
        if r.status == "error":
            print(f"✗ {r.filename}: {r.message}")
            has_errors = True
        elif r.status == "skipped":
            print(f"⏭️  {r.filename} ({r.message})")
        elif dry_run:
            print(f"  📝 {r.filename}  ({r.entry_type})")
        else:
            print(f"✓ Imported {r.filename} ({r.entry_type})")

    count = sum(1 for r in results if r.status == "imported")
    if dry_run:
        pending = sum(1 for r in results if r.status != "error")
        print(f"\n{pending} file(s) ready to import. Run without --dry-run to apply.")
    else:
        print(f"\n{count} file(s) imported into {diary_path}.")

    if has_errors:
        raise SystemExit(1)


def cmd_diary_dispatch(args: Namespace) -> None:
    """Dispatch to diary subcommands."""
    if args.diary_command == "import":
        cmd_diary_import(args)
    else:
        print("Unknown diary command. Use: yamlgraph diary import --help")
        raise SystemExit(1)
```

#### 3. Register in CLI: `yamlgraph/cli/__init__.py`

Add the `diary` command group after the existing `schema` group, following the same pattern:

```python
from yamlgraph.cli.diary_commands import cmd_diary_dispatch

# === Diary commands (FR-124) ===
diary_parser = subparsers.add_parser(
    "diary", help="Diary management commands"
)
diary_subparsers = diary_parser.add_subparsers(
    dest="diary_command", help="Diary subcommands"
)

# diary import
diary_import_parser = diary_subparsers.add_parser(
    "import", help="Import pending scheduled insights into docs/diary.md"
)
diary_import_parser.add_argument(
    "--dry-run",
    action="store_true",
    dest="dry_run",
    help="Show pending imports without modifying diary",
)
diary_import_parser.add_argument(
    "--source",
    type=str,
    default=None,
    help="Override source base directory (default: ~/scheduled-yamlgraphs/outputs/)",
)

diary_parser.set_defaults(func=cmd_diary_dispatch)
```

#### 4. Update `scripts/diary_rotate.py`

Replace the inline import logic with calls to the shared module:

```python
from yamlgraph.diary.importer import import_scheduled_entries, import_git_reports

# In main():
results = import_scheduled_entries(DIARY, SCHEDULED_OUTPUTS)
results += import_git_reports(DIARY, SCHEDULED_OUTPUTS)
imported = sum(1 for r in results if r.status == "imported")
```

### Behavior

| Flag | Action |
|------|--------|
| (none) | Import all pending files, print summary, exit 0 |
| `--dry-run` | List pending files with type and date, exit 0 |
| No pending files | Print "Nothing to import", exit 0 |
| Missing source dir | Print "Nothing to import", exit 0 (matches current hook behavior) |
| Malformed file | Print error with filename, skip file, exit 1 |

### Output format (dry-run example)

```
📋 Pending scheduled imports (~/scheduled-yamlgraphs/outputs/):
  📝 diary_entry_20260307.md  (World Digest)
  📝 diary_entry_20260306.md  (World Digest)
  📝 report_20260307_031000.txt  (Git Report)

3 file(s) ready to import. Run without --dry-run to apply.
```

### Output format (import example)

```
✓ Imported diary_entry_20260307.md (World Digest)
✓ Imported diary_entry_20260306.md (World Digest)
✓ Imported report_20260307_031000.txt (Git Report)

3 file(s) imported into docs/diary.md.
```

## Acceptance Criteria

- [ ] `yamlgraph diary import` imports pending diary entries and git reports into `docs/diary.md`
- [ ] `yamlgraph diary import --dry-run` lists pending files without modifying diary
- [ ] `--source` flag overrides the base directory; both functions preserve their internal glob patterns relative to it
- [ ] Dry-run output includes header line with source directory label
- [ ] Import summary printed to stdout with per-file status
- [ ] Malformed files are reported with filename and skipped (non-zero exit)
- [ ] Missing source directory prints "Nothing to import" and exits 0
- [ ] Pre-commit hook still works (uses same extracted `yamlgraph.diary.importer` logic)
- [ ] Unit tests for CLI command (success, dry-run, empty, missing dir, malformed)
- [ ] Tests tagged with `@pytest.mark.req("REQ-YG-122")`
- [ ] `REQ-YG-122` added to `ARCHITECTURE.md` and `scripts/req_coverage.py`
- [ ] Documentation updated (CLI help text sufficient; no new docs page needed)

## Alternatives Considered

1. **Status-only command** (`yamlgraph diary status`): Lighter but doesn't solve the "import without committing" need.
2. **Enhance pre-commit hook with verbose output**: Would add noise to every commit; current silent behavior is appropriate for the hook context.
3. **Separate `yamlgraph scheduled` command group**: Over-scoped; "diary import" is the only action needed today. Can evolve later if more scheduled pipeline management is needed.

## Related

- FR-046: Diary World Digest (implemented — created the scheduled pipeline)
- FR-093: Chaplain Diary Append (implemented — auto-log Plan→Judge decisions)
- FR-097: Refactor diary writing shared (implemented — shared diary utilities in `examples/shared/diary.py`)
- `scripts/diary_rotate.py`: Current import logic (to be refactored)
- `tests/unit/test_diary_rotate.py`: Existing test coverage for rotation + import
