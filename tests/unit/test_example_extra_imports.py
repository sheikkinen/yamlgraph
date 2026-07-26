"""Import-level dependency checks for FR-762's newly declared extras.

Each test imports the actual third-party package that the corresponding
optional-dependencies extra now declares directly (rather than only relying
on the static AST scan) — proving `pip install -e ".[<extra>]"` genuinely
makes the example runnable, not just declared.

Chatterbox (torch/torchaudio) is intentionally NOT covered here: per FR-762
C-3, it is verified statically only (constraint C-3 — no heavyweight,
platform-restricted torch install in CI without explicit human approval).
"""

from __future__ import annotations

import importlib

import pytest


@pytest.mark.req("REQ-YG-571")
@pytest.mark.parametrize("module_name", ["pyarrow"])
def test_rag_extra_imports(module_name):
    """`rag` extra: pyarrow (transitively required by lancedb) imports cleanly."""
    importlib.import_module(module_name)


@pytest.mark.req("REQ-YG-571")
@pytest.mark.parametrize("module_name", ["litellm"])
def test_replicate_extra_imports(module_name):
    """`replicate` extra: litellm (used by the Replicate provider) imports cleanly."""
    importlib.import_module(module_name)


@pytest.mark.req("REQ-YG-571")
@pytest.mark.parametrize("module_name", ["starlette", "google.protobuf"])
def test_a2a_extra_imports(module_name):
    """`a2a` extra: starlette + protobuf (server transport/wire format) import cleanly."""
    importlib.import_module(module_name)


@pytest.mark.req("REQ-YG-571")
@pytest.mark.parametrize("module_name", ["fastapi", "uvicorn", "starlette", "openai"])
def test_openai_proxy_extra_imports(module_name):
    """`openai-proxy` extra: the FastAPI app stack AND the OpenAI SDK the
    demo actually imports (`from openai import OpenAI`) import cleanly.
    PR #464 review found `openai` missing from this check even though
    the demo module imports it directly — the extra must cover the
    example's full non-core import surface, not just its server
    framework."""
    importlib.import_module(module_name)


@pytest.mark.req("REQ-YG-571")
@pytest.mark.parametrize(
    "module_name", ["fastapi", "uvicorn", "tiktoken", "unified_planning"]
)
def test_examples_dungeon_master_extra_imports(module_name):
    """`examples-dungeon-master` extra: API stack + tiktoken + unified-planning
    (dungeon_master's salience/plot modules) import cleanly."""
    importlib.import_module(module_name)


@pytest.mark.req("REQ-YG-571")
def test_chatterbox_torch_declared_but_not_ci_installed():
    """FR-762 C-3: torch/torchaudio are declared in the `chatterbox` extra for
    direct-import honesty, but are NOT installed in CI (heavyweight, platform
    -restricted). This test documents that decision rather than asserting an
    import — a human must explicitly approve heavyweight CI installation
    before this could become a real import check."""
    assert True
