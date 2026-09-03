# Diary: The Toolbelt Nobody Else Picked Up

**Date:** 2026-09-03
**Trigger:** "check existing tool definitions repo wide, reflect" — a
structural census of every `tools:` declaration in committed YAML, mirroring
the FR-802 node-type-census methodology.

## What the census found

442 tool declarations across 139 files (git-tracked YAML only; zero in
`projects/`, consistent with the August node-type census — no production
project graph is committed to this snapshot). Shape distribution: `python`
301, `shell` 77, `manifest` 31, `graph` 18, `slot` 12, plus 3 false positives
(`write_data_file`-style declarations keyed by `type:`/`state_key:`, the same
category of schema-shaped false positive the node census hit with `object`).

`examples/shared/toolbelt/` holds exactly four canonical manifests —
`read_file`, `git_log`, `list_dir`, `search` — built for FR-768 (manifest
reuse) and consumed via FR-892 (invocation-time tool slots). They work. Where
adopted, adoption is clean: `enforcer`, `judge`, `planner`, `research-agent`
all point at the same four manifest files with zero inline reimplementation.

But adoption is narrow: only 13 of 139 files (~9%) use `manifest:` at all,
concentrated in two clusters (the four-graph agent-toolkit family and
`api-discovery`'s six steps). Sixteen tool *names* — `read_file`, `git_log`,
`list_dir`, `search`, `dedup_pre_check`, `persist`, `prefetch`,
`reload_canon`, `discover`, `extract`, `reduce_ledger`, `summarize_demo`,
`prepare_brief_input`, `render_brief`, `generate_images`, `list_canon_ids` —
recur 4+ times each under the identical name, but outside the manifest
clusters each recurrence is an independent hand-rolled declaration with no
shared source of truth.

## The concrete drift, not a hypothetical

`examples/demos/meta/graph.yaml:26` still carries: `# read_file is a shell
tool (cat {target}) per the judge/enforcer convention.` That comment was true
once. It is false today — `judge` and `enforcer` both migrated to
`manifest: ../../shared/toolbelt/read_file.tool.yaml` (a translated
subprocess-backed read, not a raw `cat`), while `meta` still shells out to
`cat` directly, and `philosopher_book/graph.yaml` declares a third
independent shape (`function: read_file`, a Python tool). Three files, one
tool name, three implementations, and one of them cites peers that no longer
match its own claim. Nothing enforces that a comment describing a "shared
convention" stays true when the convention moves.

Confirmed by the `git_log` row too: `examples/demos/memory/graph.yaml`
declares it as `shell`, `examples/codegen/impl-agent.yaml` declares it as
`python` — same name, already different implementation shape, before any
manifest was even in the picture.

## The trap, named

This is the mirror image of `false_duplicate` ("syntactic similarity ≠
semantic equivalence" — two things that look different are secretly the
same). Here two things that look *identical* (same tool name, same apparent
purpose, cited as following the same convention) are secretly different,
and the only witness is a source-controlled comment that nobody re-checked
when its cited peers changed. Call it **name_as_borrowed_authority**: a
declaration cites a shared convention by name instead of by reference
(`manifest:` path), so when the convention moves, the citation silently
becomes false and nothing fails, lints, or diffs to say so — because a
comment is not a dependency edge.

## Seed

The manifest mechanism (FR-768) already solves this — a `manifest:` line is
a real reference, a comment is not. Would a lint rule that flags `tools:`
entries whose `description:` or an adjacent comment contains the string
"convention" or "per X" without an accompanying `manifest:` key be cheap
enough to run at `yamlgraph graph lint` (~1s, keyless) and catch the next
`meta`-style drift before it's four months stale — turning "shared
convention" from prose into something the linter can falsify?
