# FR-747: Loader Error UX — the two FR-744 boundary errors name their fix

**Status:** Completed
**Type:** Fix (framework ergonomics, `yamlgraph/` loader + prompt parsing)
**Effort:** 0.5 day
**Requested:** 2026-07-17
**Judged:** 2026-07-17 — approved; AC-02's "load time" made precise
against the actual loading semantics
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
   `system:`/`user:`, raise in `load_prompt` (F1: lazy load — fires
   before any LLM call in that node; eager compile-time loading is
   purged; the pre-run guarantee is lint's, per AC-03):
   `"Prompt '<name>' uses 'messages:' role list — YAMLGraph prompts
   use top-level 'system:' and 'user:' keys (see author-prompt
   skill)."`
2. **Python tool loader:** when `module:` import fails AND a file
   matching the module name exists relative to the graph dir, append
   to the strict-mode error: `"hint: '<mod>.py' exists next to the
   graph — graph-local tools use 'path: <mod>.py', not 'module:'."`
3. Both errors carry the contract, not just the failure.

## Acceptance Criteria

- [x] AC-01 RED: two condemning tests reproducing the exact field
      errors, asserting the new messages.
- [x] AC-02: load-time detection for the prompt case (per F1: the
      raise lives in `load_prompt`, ahead of any LLM call in the node;
      the pre-run guarantee moved to lint).
- [x] AC-03: `graph lint` surfaces both defects (the lint ran clean
      over the broken prompt in FR-744 — a lint gap, witnessed).

## Out of scope (purge list)

- Supporting `messages:` lists (the contract stands; this FR improves
  its enforcement, not its surface).
- General error-message audit (only the two measured incidents).

## Questions for the human (as options, or 'none')

None — two incidents, two messages, three witnesses.

## Judgement (2026-07-17)

**Verdict: APPROVED — 3 findings.** Verified: the exact error string
lives at `yamlgraph/tools/python_tool.py:132`; prompt loading is
`yamlgraph/utils/prompts.py:load_prompt` (returns the system/user
dict; the field KeyError fires downstream); `graph lint` does not
load prompt files today — the AC-03 lint gap is real.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **Prompts load lazily** (at node execution), so AC-02's "fails at graph-load" would require eager prompt resolution at compile — a framework-semantics change (dynamic prompts_dir/fallback resolution paths exist), disproportionate to two error messages | AC-02 re-pinned: the actionable raise lives in `load_prompt` (fires before any LLM call in that node — still ahead of the FR-744 burn point within the node); the PRE-RUN guarantee belongs to `graph lint` (AC-03), which gains a prompt-resolution pass over each node's `prompt:` reference. Eager compile-time loading is PURGED |
| F2 | The `module:` hint needs graph-dir context at the python_tool boundary, and a speculative hint on every import failure would be noise | Hint appended ONLY when `<module>.py` exists relative to the graph dir (verified file existence, never speculation); otherwise the current error stands unchanged |
| F3 | The `messages:` detection must not fire on prompts that legitimately contain a `messages` VARIABLE or field name | Detection keys on a top-level `messages:` mapping key in the parsed YAML combined with ABSENT `system:`/`user:` — both conditions, parsed-structure level, never text grep |

Scope otherwise frozen; the purge list (no `messages:` support, no
general audit) stands.

## Enforcement Record (2026-07-18)

RED 573158a8 (4 condemning witnesses + 3 F2/F3 negatives), GREEN in the
same arc. Delivered:

- `check_messages_contract` in [yamlgraph/utils/prompts.py](../yamlgraph/utils/prompts.py)
  — parsed-structure detection (F3), applied in both `load_prompt` and
  `load_prompt_path`; a `messages` variable in a valid prompt never
  fires (witnessed).
- `module:` hint in [yamlgraph/tools/python_tool.py](../yamlgraph/tools/python_tool.py)
  — appended ONLY when `<module>.py` exists under `graph_root` (F2);
  the error is otherwise byte-identical (witnessed).
- Lint pass in [yamlgraph/linter/checks_loader_ux.py](../yamlgraph/linter/checks_loader_ux.py)
  (new module; siblings sit at the 450-line cap): E006 prompt
  messages-contract, E008 module-vs-graph-local file; wired into
  `lint_graph` (AC-03). Full suite 5077 passed; real graphs lint clean
  (no false positives on hello/fr_triage/world_distill).

**Triage calibration:** upheld 1 / overturned 0 / deferred 0 — the
FR-745 triage pre-mortem caught this FR's own §1 "raise at LOAD time"
contradicting the judgement's F1 lazy-load pin; §1 and AC-02 reworded
above before enforcement (first entry in the FR-745 AC-05 ledger).
