# Reflection: FR-239 — Chatterbox Multilingual CLI

**Date:** 2026-04-19
**Branch:** feat/fr-239-chatterbox-speak-multilingual

## What Was Built

Added `--lang` flag to `speak.py`, splitting the CLI into two explicit synthesis paths:
- **English / voice-cloning** (`--lang en`, default): `ChatterboxTTS` + `--ref` required
- **Multilingual** (`--lang <non-en>`): `ChatterboxMultilingualTTS`, `--ref` incompatible

## Cognitive Process

The task was structurally clear from the FR, but one trap surfaced immediately: the
existing test `test_speak_py_has_no_lang_argument` asserted the *absence* of `--lang`.
This was a contract test for the prior FR-237 constraint that `--lang` should not exist
(the README justified it as "an argument that only changes the filename without
influencing synthesis would mislead users"). FR-239 supersedes that constraint — the
flag now genuinely influences which model is invoked, making it honest.

The inversion — deleting a "negative assertion" test and replacing it with a positive
one — is a clean signal that scope has legitimately expanded rather than drifted.

## Traps Encountered

**Old negative test as dead weight.** The `test_speak_py_has_no_lang_argument` test
was written to protect against premature feature addition. Once the feature request
explicitly sanctions the flag, keeping the test would have been *test pollution*:
a guard that now guards against the correct behaviour. The cure: replace it with
`test_speak_py_has_lang_argument`, inverting the assertion.

**`--ref` optionality.** Making `--ref` optional (from `required=True`) requires the
error path to shift from argparse's automatic validation to explicit `parser.error()`
calls. This is correct — argparse `required=True` cannot express the conditional logic
"required only when `--lang en`". Explicit validation keeps the error message domain-specific.

## Heuristic

> When a "must not exist" test becomes false after a legitimate FR, replace it with
> "must exist" — not delete it. The test's inversion proves the FR was correctly scoped.

## Seed

Could `speak.py` support a `--devices` flag that lists available backends (cuda/mps/cpu)
without synthesising anything, helping users debug hardware detection before a slow
model download? And could `yamlgraph graph info` expose `required_hardware` hints from
demo YAMLs?
