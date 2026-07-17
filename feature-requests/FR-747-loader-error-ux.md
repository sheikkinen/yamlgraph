# FR-747: Loader Error UX — the two FR-744 boundary errors name their fix

**Status:** Proposed
**Type:** Fix (framework ergonomics, `yamlgraph/` loader + prompt parsing)
**Effort:** 0.5 day
**Requested:** 2026-07-17
**First consumer / first event:** the next graph/prompt author who
makes either known mistake; first event = their error message. The
population is measured: the author of FR-744 hit both in one
enforcement *with the skills available and unconsulted* — docs catch
the agent who reads, error messages catch the one who didn't.

## Ideal Result

Every boundary error at the config-parsing layer tells the author what
to write instead. An agent hitting a known contract violation loses
seconds, not a diagnosis cycle; the error message is the
documentation's rung-1 delivery.

## Problem

Two field incidents (FR-744 enforce, 2026-07-17), both stack-trace
shrapnel where the loader knows the fix:

1. **`messages:` role list in a prompt YAML** → `Node distill failed:
   'user'` — a bare KeyError. The parser knows prompts use top-level
   `system:`/`user:` keys and can detect the `messages:` key
   explicitly (the known migration path from OpenAI/Anthropic API
   idioms).
2. **`module: tools` from a graph dir** → `Cannot import module
   'tools': No module named 'tools'` — strict mode names the tool but
   not the cure (`path: tools.py` for graph-local files).

Skills patched with both contracts (2e8b6293); this FR is the code
half. Reception hierarchy: an error message is a tool result — rung 2,
guaranteed read at the exact moment of need.

**Prior art:** FR-744 implementation notes (the incidents);
skills patch 2e8b6293 (the docs half); `DeprecationError` convention
(CLAUDE.md — precedent for actionable framework errors); Commandment 6
(bear witness of thy errors — an unhelpful error hides the fault's
cause). Disposition: pure ergonomics on existing validation paths; no
rejected FR touches error-message territory.

## Proposed Solution

1. **Prompt parser:** if a prompt YAML contains `messages:` and lacks
   `system:`/`user:`, raise at LOAD time (not node-execution time):
   `"Prompt '<name>' uses 'messages:' role list — YAMLGraph prompts
   use top-level 'system:' and 'user:' keys (see author-prompt
   skill)."`
2. **Python tool loader:** when `module:` import fails AND a file
   matching the module name exists relative to the graph dir, append
   to the strict-mode error: `"hint: '<mod>.py' exists next to the
   graph — graph-local tools use 'path: <mod>.py', not 'module:'."`
3. Both errors carry the contract, not just the failure.

## Acceptance Criteria

- [ ] AC-01 RED: two condemning tests reproducing the exact field
      errors, asserting the new messages.
- [ ] AC-02: load-time detection for the prompt case (fails at
      graph-load, not mid-run — the FR-744 run burned a fetch cycle
      before the prompt failed).
- [ ] AC-03: `graph lint` surfaces both defects (the lint ran clean
      over the broken prompt in FR-744 — a lint gap, witnessed).

## Out of scope (purge list)

- Supporting `messages:` lists (the contract stands; this FR improves
  its enforcement, not its surface).
- General error-message audit (only the two measured incidents).

## Questions for the human (as options, or 'none')

None — two incidents, two messages, three witnesses.
