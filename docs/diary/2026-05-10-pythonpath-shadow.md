# Diary: The Shadow That Helped and Then Hurt

**Date:** 2026-05-10
**Context:** OC-017 enforcement — migrating voice_runtime from sys.path hack to PyPI dep, culminating in a live call to +358454913431

## What Happened

OC-017 was approved: remove the `PROJECTS_DIR` sys.path insert from outcaller's conftest and start scripts; declare `voice-runtime` as a proper PyPI dependency. Surgical, clear, approved.

Enforcement began. conftest.py fixed. start-out.sh and start-in.sh fixed. Committed. Then: ran `start-symptom-answerer.sh` — the acceptance test. The call failed with:

```
No module named 'voice_runtime.stt'
```

Then after removing the PYTHONPATH export from that script:

```
No module named 'voice_runtime'
```

Two different errors. Two different causes. Both caused by the same original sin.

## The Shadow Mechanism

The PYTHONPATH hack was:
```bash
export PYTHONPATH="${YAMLGRAPH_ROOT}/projects${PYTHONPATH:+:$PYTHONPATH}"
```

This put `projects/` on the path so Python could resolve `from voice_runtime.xxx`. It appeared to work. But `projects/voice_runtime/` is not the package — it's the **project directory** (containing `pyproject.toml`, `README.md`, `voice_runtime/` subdirectory, etc.).

When Python imports `voice_runtime` via `projects/` on the path, it finds the project directory as a namespace package with `__init__.py = None`. No `stt` submodule exists at that level. The real package lives one level deeper: `projects/voice_runtime/voice_runtime/`.

So the hack that "made voice_runtime importable" was actually importing the wrong thing — a hollow namespace that happened to work for `from voice_runtime import VoiceSession` (because `voice_runtime/__init__.py` re-exports everything) but broke for direct submodule access like `from voice_runtime.stt import ...`.

It worked — until it didn't. The working system masked the broken import path.

## The Second Error

After removing PYTHONPATH from the scripts, the yamlgraph `.venv` activated by the script had no `voice_runtime` at all. The editable install existed in the user's default Python, not in the project venv. Fix: `pip install voice-runtime` into `.venv`. Correct boundary — pip, not PYTHONPATH.

## The Trap

**working_system_inertia** + **downstream_fix**: The PYTHONPATH export had been in every start script for months. It worked in dev (where the editable install in the main Python shadowed the namespace package confusion). It broke when:
1. We renamed the source from flat layout to `voice_runtime/` subdir (PyPI prep)
2. The scripts activated `.venv` which had no voice_runtime at all

The trap: we removed the hack from two scripts per OC-017 but left it in 10 others. Partial remediation. The acceptance test caught it immediately.

## The Cure

Three things in sequence:
1. Remove PYTHONPATH from all 10 start scripts (not just the two in scope)
2. Install `voice-runtime` into `.venv` — normalize at the pip boundary
3. Rename `outcaller-yamlgraph/` → `outcaller/` — fix the `projects.outcaller` import that was also broken by the hyphen

After all three: `start-symptom-answerer.sh --phone +358454913431` completed the full call. ninchat_voice greeted in Finnish. The bot answered all 6 symptom questions. Confirmed recap. Call disconnected cleanly.

## The Heuristic

> A PYTHONPATH hack that "works" is a deferred import failure. The path entry that resolves the module may not resolve the module you think it does. Namespace packages are silent about what they expose. Verify submodule imports, not just top-level ones.

More precisely: **the boundary for resolving packages is pip, not PYTHONPATH**. Every PYTHONPATH entry is a promise that can be broken by directory layout changes. `pip install` is a contract.

## Acceptance Test Result

```
Call placed: CA910d2beb10c2ec1bd1d1ecf8b5df737e
Stream: MZ4e568d221b3b96e7a4bc388e7f9b5226
Heard: "Olet soittanut Tervolaan terveysasemalle..."
Spoke: "Oirearvio" → 6 symptom answers → "Kyllä, yhteenveto on oikein."
Disconnected cleanly. call_disconnected: True
```

LangSmith trace: https://eu.smith.langchain.com/o/1c1b3d09-e172-4c82-bddb-5d1fe06a132a/projects/p/f889c0ec-fa9b-4025-b69c-2aa756283ef8/r/019e0fee-3c56-76f1-9207-3adcb6771abe

## Seed

> If PYTHONPATH is a deferred failure and pip is the correct boundary — what happens when the `.venv` itself is the wrong boundary? The `.venv` is per-project but the call infrastructure spans three repos. Is there a correct venv topology for a monorepo with multiple active projects, or is the answer always "install shared deps into every venv that needs them"?
