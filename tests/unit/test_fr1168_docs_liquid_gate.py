"""FR-1168: the Pages docs gate — no active Liquid outside {% raw %}.

Every fixture is an isolated tmp_path docs tree; nothing touches the shared
checkout.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_docs_liquid.py"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "commitlint.yml"
PRECOMMIT = REPO_ROOT / ".pre-commit-config.yaml"

pytestmark = [pytest.mark.req("REQ-YG-731"), pytest.mark.process]


def _load():
    spec = importlib.util.spec_from_file_location("check_docs_liquid", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def gate():
    return _load()


def _docs(tmp_path: Path, files: dict[str, str | bytes], config: str | None = None):
    root = tmp_path / "docs"
    root.mkdir()
    (root / "_config.yml").write_text(
        config if config is not None else 'exclude:\n  - "diary"\n  - "diary-*.md"\n',
        encoding="utf-8",
    )
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(body, bytes):
            p.write_bytes(body)
        else:
            p.write_text(body, encoding="utf-8")
    return root


def _codes(gate, text: str) -> list[tuple[int, str]]:
    return [(f.line, f.code) for f in gate.scan_text(text)]


# --- rule -------------------------------------------------------------------


def test_unterminated_variable_is_l001(gate):
    assert _codes(gate, "a\nquote `{{ <key>` here\n") == [(2, "L001")]


def test_balanced_variable_is_l001(gate):
    assert _codes(gate, "x: ${{ secrets.KEY }}\n") == [(1, "L001")]


def test_tags_are_l002(gate):
    assert _codes(gate, "{% set x = 1 %}\n{% comment %}c{% endcomment %}\n") == [
        (1, "L002"),
        (2, "L002"),
        (2, "L002"),
    ]


def test_noncanonical_raw_openers_are_l002(gate):
    assert _codes(gate, "{%- raw %}a\n{% raw x %}b\n") == [(1, "L002"), (2, "L002")]


def test_fenced_code_is_not_protected(gate):
    assert _codes(gate, "```yaml\nk: {{ v }}\n```\n") == [(2, "L001")]


def test_inline_and_block_raw_pass(gate):
    text = (
        "inline `{% raw %}{{ <key>{% endraw %}` ok\n"
        "{% raw %}\n```\n{{ a }}\n{% if b %}\n```\n{% endraw %}\n"
    )
    assert _codes(gate, text) == []


def test_unclosed_raw_is_l003_at_opener(gate):
    assert _codes(gate, "ok\n{% raw %}\n{{ a }}\n") == [(2, "L003")]


def test_closer_with_arguments_closes_raw_early(gate):
    text = "{% raw %}literal{% endraw ignored %}{{ secret }}{% raw %}tail{% endraw %}\n"
    assert _codes(gate, text) == [(1, "L004"), (1, "L001")]


def test_endraw_with_right_trim_closes_and_is_l004(gate):
    assert _codes(gate, "{% raw %}a{% endraw -%}{{ b }}\n") == [
        (1, "L004"),
        (1, "L001"),
    ]


def test_left_trim_endraw_does_not_close(gate):
    assert _codes(gate, "{% raw %}a{%- endraw %}{{ b }}{% endraw %}\n") == [(1, "L004")]
    assert _codes(gate, "{% raw %}a\n{%- endraw %}\n") == [(2, "L004"), (1, "L003")]


# --- selection --------------------------------------------------------------


def _scan_tree(gate, root: Path) -> list[tuple[str, int, str]]:
    excludes = gate.load_excludes(root)
    out = []
    for path in gate.select_files(root, excludes):
        out += [(f.path, f.line, f.code) for f in gate.scan_file(path, root)]
    return sorted(out)


def test_front_matter_stripped_with_source_lines(gate, tmp_path):
    root = _docs(tmp_path, {"p.md": "---\ntitle: '{{ x }}'\n---\nbody {{ y }}\n"})
    assert _scan_tree(gate, root) == [("p.md", 4, "L001")]


def test_markdown_extensions_scanned(gate, tmp_path):
    root = _docs(
        tmp_path, {"a.markdown": "{{ a }}", "b.mkd": "{{ b }}", "c.md": "{{ c }}"}
    )
    assert [p for p, _, _ in _scan_tree(gate, root)] == ["a.markdown", "b.mkd", "c.md"]


def test_non_markdown_scanned_only_with_front_matter(gate, tmp_path):
    root = _docs(
        tmp_path,
        {
            "fm.yaml": "---\n---\n{{ a }}\n",
            "plain.yaml": "{{ b }}\n",
            "x.html": "{{ c }}",
        },
    )
    assert _scan_tree(gate, root) == [("fm.yaml", 3, "L001")]


def test_excludes_and_special_paths_not_scanned(gate, tmp_path):
    root = _docs(
        tmp_path,
        {
            "diary/d.md": "{{ a }}",
            "diary-2026-01-01.md": "{{ b }}",
            "_drafts/x.md": "{{ c }}",
            ".hidden/y.md": "{{ d }}",
            "sub/#z.md": "{{ e }}",
            "_posts/2026-01-01-post.md": "{{ f }}",
            "_posts/undated.md": "{{ g }}",
        },
    )
    assert _scan_tree(gate, root) == [("_posts/2026-01-01-post.md", 1, "L001")]


def test_excludes_read_from_config_at_run_time(gate, tmp_path):
    root = _docs(tmp_path, {"inv/a.md": "{{ a }}"}, config="exclude:\n  - inv\n")
    assert _scan_tree(gate, root) == []
    (root / "_config.yml").write_text("exclude: []\n", encoding="utf-8")
    assert _scan_tree(gate, root) == [("inv/a.md", 1, "L001")]


# --- errors and CLI ---------------------------------------------------------


@pytest.mark.parametrize(
    "config",
    [
        None,
        "exclude: [unclosed\n",
        "- a list\n",
        "exclude: diary\n",
        "exclude:\n  - 3\n",
    ],
    ids=["missing", "malformed", "non-mapping", "non-list", "non-string"],
)
def test_config_errors_exit_2(gate, tmp_path, config, capsys):
    root = _docs(tmp_path, {"a.md": "fine"}, config=config or "")
    if config is None:
        (root / "_config.yml").unlink()
    assert gate.main(["--root", str(root)]) == 2
    assert "_config.yml" in capsys.readouterr().err


def test_invalid_utf8_exits_2(gate, tmp_path, capsys):
    root = _docs(tmp_path, {"bad.md": b"\xff\xfe{{"})
    assert gate.main(["--root", str(root)]) == 2
    assert "bad.md" in capsys.readouterr().err


def test_cli_reports_and_exits_1(gate, tmp_path, capsys):
    root = _docs(tmp_path, {"a.md": "ok\n{{ x }}\n", "b.md": "clean\n"})
    assert gate.main(["--root", str(root)]) == 1
    out = capsys.readouterr().out
    assert "a.md:2: L001" in out and "{% raw %}" in out and "b.md" not in out


def test_cli_clean_tree_exits_0(gate, tmp_path):
    root = _docs(tmp_path, {"a.md": "{% raw %}{{ x }}{% endraw %}\n"})
    assert gate.main(["--root", str(root)]) == 0


def test_cli_paths_restrict_scan(gate, tmp_path):
    root = _docs(tmp_path, {"a.md": "{{ x }}", "b.md": "clean"})
    assert gate.main(["--root", str(root), str(root / "b.md")]) == 0
    assert gate.main(["--root", str(root), str(root / "a.md")]) == 1


def test_config_path_argument_triggers_full_scan(gate, tmp_path):
    root = _docs(tmp_path, {"a.md": "{{ x }}", "b.md": "clean"})
    assert gate.main(["--root", str(root), str(root / "_config.yml")]) == 1


# --- wiring -----------------------------------------------------------------


def test_precommit_hook_wired():
    hooks = [
        h
        for repo in yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))["repos"]
        for h in repo.get("hooks", [])
    ]
    hook = next(h for h in hooks if h["id"] == "docs-liquid")
    assert "scripts/check_docs_liquid.py" in hook["entry"]
    assert hook["files"] == "^docs/"
    assert hook.get("pass_filenames", True) is True


def test_ci_job_always_runs_scanner_and_real_build():
    wf = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    job = wf["jobs"]["docs-liquid"]
    assert job["name"] == "Docs Liquid (Pages build)"
    assert "if" not in job and "needs" not in job
    assert job["permissions"] == {"contents": "read"}
    steps = job["steps"]
    runs = "\n".join(s.get("run", "") for s in steps)
    uses = [s.get("uses", "") for s in steps]
    assert any(u.startswith("actions/checkout@") for u in uses)
    assert "python scripts/check_docs_liquid.py" in runs
    build = next(
        s for s in steps if s.get("uses", "").startswith("actions/jekyll-build-pages@")
    )
    assert build["with"]["source"] == "./docs"
    assert "{{ secrets.AZURE_SPEECH_KEY }}" in runs and "{{ <key>" in runs
    assert all(not s.get("if") for s in steps)


# --- gate bite --------------------------------------------------------------


@pytest.mark.skipif(shutil.which("pre-commit") is None, reason="pre-commit not on PATH")
def test_precommit_hook_bites_in_throwaway_repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy(SCRIPT, repo / "scripts" / SCRIPT.name)
    (repo / ".pre-commit-config.yaml").write_text(
        "repos:\n  - repo: local\n    hooks:\n"
        "      - id: docs-liquid\n        name: docs liquid\n"
        "        entry: python scripts/check_docs_liquid.py\n"
        "        language: system\n        files: ^docs/\n",
        encoding="utf-8",
    )
    docs = repo / "docs"
    docs.mkdir()
    (docs / "_config.yml").write_text("exclude: []\n", encoding="utf-8")
    witness = docs / "liquid-gate-witness.md"
    witness.write_text("value: {{ x }}\n", encoding="utf-8")

    def git(*args):
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)

    git("init", "-q")
    git("add", ".")

    def run():
        return subprocess.run(
            [
                "pre-commit",
                "run",
                "docs-liquid",
                "--files",
                "docs/liquid-gate-witness.md",
            ],
            cwd=repo,
            capture_output=True,
            text=True,
        )

    red = run()
    assert red.returncode == 1
    assert "liquid-gate-witness.md:1: L001" in red.stdout

    witness.write_text("value: {% raw %}{{ x }}{% endraw %}\n", encoding="utf-8")
    git("add", ".")
    green = run()
    assert green.returncode == 0, green.stdout
