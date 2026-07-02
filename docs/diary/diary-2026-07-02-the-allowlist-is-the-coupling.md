# Diary: The Allowlist Is the Coupling

**Date:** 2026-07-02
**FR:** FR-655 (genesis pipeline — post-enforcement cleanup)
**Trap:** downstream_fix, infrastructure_self_exempt

## What Happened

After running the genesis pipeline for Floodmark, the 25 generated canon files
were invisible to git. The `.gitignore` had a complex pattern: ignore all canon
subdirectory YAML, then un-ignore 10 specific Ashfall filenames. When genesis
replaced Ashfall with Floodmark, every new file was silently hidden.

The allowlist was tightly coupled to content that no longer existed.

## The Trap

The original `.gitignore` encoded a workflow assumption: hand-authored seed files
are precious (tracked), LLM-generated files are disposable (ignored). FR-655
eliminated that distinction — genesis output IS the seed. The ignore rules became
a **downstream fix** for a workflow that had been replaced upstream.

More subtly: the allowlist was a form of **infrastructure_self_exempt**. The
gitignore rules were never tested against the new pipeline — they were assumed
to "just work" because they were infrastructure, not code.

## The Cure

Remove the ignore rules entirely. If genesis output is the seed canon, it belongs
in git. The premise (one paragraph) and the schema (Pydantic models) are the
real assets — the canon is regenerable from them. But regenerable doesn't mean
untracked: the canon is the contract that downstream graphs (pathfinder, draft,
close) depend on.

## Heuristic

**Allowlists couple infrastructure to content.** When content is replaced,
allowlists silently break. Prefer broad rules (track everything, ignore nothing)
over fine-grained allowlists that encode assumptions about specific filenames.
If you must allowlist, the list is a test case — verify it on every content change.

## Seed

Can the genesis pipeline detect stale `.gitignore` allowlists — files that are
listed as exceptions but no longer exist on disk? A pre-commit hook that flags
`!path` entries pointing to nonexistent files would have caught this immediately.
