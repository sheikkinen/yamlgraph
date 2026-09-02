"""FR-294: Pre-commit venv PATH isolation.

Verify that the pre-commit pytest hook prepends .venv/bin to PATH
so subprocess calls to venv-installed tools succeed.
"""

import pytest


@pytest.mark.req("REQ-YG-012")
def test_precommit_hook_exports_venv_path():
    """Pre-commit pytest hook must export PATH with .venv/bin prepended."""
    from pathlib import Path

    config = Path(__file__).parents[2] / ".pre-commit-config.yaml"
    content = config.read_text(encoding="utf-8")
    assert (
        'export PATH=".venv/bin:$PATH"' in content
    ), "Pre-commit pytest hook missing PATH export for .venv/bin"
