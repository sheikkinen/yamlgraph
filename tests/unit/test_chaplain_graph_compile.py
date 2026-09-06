"""FR-699: Chaplain graph compilation witness tests.

Condemns the defect class behind the FR-445 x FR-658 path-doubling incident
(commit 1ed5b8b6): chaplain graph configs are production infrastructure that
no test compiled, so loader-semantics changes armed landmines silently.

Wiring only — no graph execution, no LLM calls.
"""

import importlib.util
from pathlib import Path

import pytest

from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
# FR-1011 moved the live process graphs to graphs/; FR-1012 removed the runtime.
CHAPLAIN_GRAPHS = sorted(
    p for p in (REPO_ROOT / "graphs").rglob("*.yaml") if "prompts" not in p.parts
)


@pytest.mark.req("REQ-YG-529")
def test_chaplain_graph_configs_discovered() -> None:
    """The glob must find the process graphs — an empty list would vacuously pass."""
    assert len(CHAPLAIN_GRAPHS) >= 4, [str(p) for p in CHAPLAIN_GRAPHS]


@pytest.mark.req("REQ-YG-529")
@pytest.mark.parametrize(
    "graph_path",
    CHAPLAIN_GRAPHS,
    ids=[str(p.relative_to(REPO_ROOT)) for p in CHAPLAIN_GRAPHS],
)
def test_chaplain_graph_compiles(graph_path: Path) -> None:
    """Every chaplain graph config loads and compiles; declared tools resolve.

    Fails on the pre-fix tree (b17a8b5e) with FileNotFoundError on the
    doubled tool path — the condemning test 1ed5b8b6 lacked.
    """
    config = load_graph_config(str(graph_path))
    compile_graph(config)


@pytest.mark.req("REQ-YG-529")
def test_philosopher_write_diary_proxy_wiring() -> None:
    """The write_diary proxy resolves the sibling graphs/philosopher/diary.py and its callable.

    Wiring only: the incident was a broken link, not broken behavior.
    """
    tools_path = REPO_ROOT / "graphs" / "philosopher" / "tools.py"
    lib_path = tools_path.with_name("diary.py")
    assert lib_path.is_file(), f"proxy target missing: {lib_path}"

    spec = importlib.util.spec_from_file_location(
        "chaplain_lib_diary_witness", lib_path
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(getattr(mod, "write_diary", None))
