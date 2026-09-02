"""FR-865 — Ramp installer contract tests (RED first, AC-15).

Covers ACs 02–13 and 16–18: manifest schema and validation rejections,
tier monotonicity, dry-run, install byte-fidelity, idempotency, refusals,
overwrite/backup/rollback, target manifest record, curated-asset
consumption and drift evidence, consumer registry, and source scans.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ramp_installer as ri  # noqa: E402

RAMP_DIR = REPO_ROOT / "ramp"
MANIFEST = RAMP_DIR / "manifest.yaml"
FIXTURE = RAMP_DIR / "fixtures" / "target-repo"
CLI = REPO_ROOT / "scripts" / "ramp_installer.py"
WRAPPER = REPO_ROOT / "scripts" / "ramp.sh"

pytestmark = pytest.mark.process


# ── helpers ──────────────────────────────────────────────────────────


def make_target(tmp_path: Path, shape: str = "supported") -> Path:
    """Copy the committed fixture into tmp and shape it."""
    target = tmp_path / "target"
    shutil.copytree(FIXTURE, target)
    (target / ".git").mkdir()
    (target / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    if shape == "missing-tests":
        shutil.rmtree(target / "tests")
    elif shape == "missing-ruff":
        py = target / "pyproject.toml"
        py.write_text(py.read_text(encoding="utf-8").replace("[tool.ruff]\nline-length = 88\n", ""), encoding="utf-8")
    elif shape == "non-repo":
        shutil.rmtree(target / ".git")
    elif shape == "worktree":
        shutil.rmtree(target / ".git")
        (target / ".git").write_text("gitdir: /somewhere/else\n", encoding="utf-8")
    return target


def run_cli(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    full_env = {**os.environ, **(env or {})}
    return subprocess.run(
        [sys.executable, str(CLI), *[str(a) for a in args]],
        capture_output=True,
        text=True,
        env=full_env,
    )


def tree_state(root: Path) -> dict[str, tuple[str, float]]:
    """Map of relpath -> (sha256, mtime) for every file under root."""
    state = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            state[str(p.relative_to(root))] = (
                hashlib.sha256(p.read_bytes()).hexdigest(),
                p.stat().st_mtime,
            )
    return state


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture()
def entries():
    return ri.load_manifest(MANIFEST)


# ── AC-02 / AC-03: manifest schema and validation ────────────────────


@pytest.mark.req("REQ-YG-610")
def test_manifest_schema_fields(entries):
    assert entries, "manifest must enumerate assets"
    for e in entries:
        assert not Path(e.source).is_absolute()
        assert not Path(e.destination).is_absolute()
        assert ".." not in Path(e.source).parts
        assert ".." not in Path(e.destination).parts
        assert e.source == os.path.normpath(e.source)
        assert e.destination == os.path.normpath(e.destination)
        assert e.tier in (1, 2, 3)
        assert e.overwrite in ("never", "force-backup")
        assert e.provenance in ("authored", "mirror_exact", "curation_diff")


@pytest.mark.req("REQ-YG-610")
def test_manifest_sources_exist_and_are_files(entries):
    for e in entries:
        src = RAMP_DIR / e.source
        assert src.is_file(), f"missing source: {e.source}"
        assert not src.is_symlink() or e.allow_symlink


@pytest.mark.req("REQ-YG-610")
def test_manifest_no_duplicate_destinations(entries):
    dests = [e.destination for e in entries]
    assert len(dests) == len(set(dests))


@pytest.mark.req("REQ-YG-610")
@pytest.mark.parametrize(
    "entry,reason",
    [
        ({"source": "/abs/x", "destination": "x", "tier": 1}, "absolute"),
        ({"source": "assets/../x", "destination": "x", "tier": 1}, "traversal"),
        ({"source": "assets", "destination": "x", "tier": 1}, "directory"),
        ({"source": "assets/nope.txt", "destination": "x", "tier": 1}, "missing"),
        (
            {"source": "assets/tier1/AGENTS.md", "destination": "/etc/x", "tier": 1},
            "absolute destination",
        ),
        (
            {
                "source": "assets/tier1/AGENTS.md",
                "destination": "logs/audit.jsonl",
                "tier": 1,
            },
            "generated",
        ),
        (
            {
                "source": "assets/tier1/AGENTS.md",
                "destination": "__pycache__/x.pyc",
                "tier": 1,
            },
            "cache",
        ),
        ({"source": "assets/tier1/AGENTS.md", "destination": "x", "tier": 9}, "tier"),
    ],
)
def test_manifest_rejects_bad_entries(tmp_path, entry, reason):
    bad = tmp_path / "manifest.yaml"
    base = {"overwrite": "never", "authored": True}
    bad.write_text(yaml.safe_dump({"schema_version": 1, "entries": [base | entry]}), encoding="utf-8")
    with pytest.raises(ri.ManifestError):
        ri.load_manifest(bad, ramp_dir=RAMP_DIR)


@pytest.mark.req("REQ-YG-610")
def test_manifest_rejects_duplicate_destination(tmp_path):
    e = {
        "source": "assets/tier1/AGENTS.md",
        "destination": "AGENTS.md",
        "tier": 1,
        "overwrite": "never",
        "authored": True,
    }
    bad = tmp_path / "manifest.yaml"
    bad.write_text(yaml.safe_dump({"schema_version": 1, "entries": [e, dict(e)]}), encoding="utf-8")
    with pytest.raises(ri.ManifestError):
        ri.load_manifest(bad, ramp_dir=RAMP_DIR)


@pytest.mark.req("REQ-YG-610")
def test_manifest_rejects_double_provenance(tmp_path):
    e = {
        "source": "assets/tier1/AGENTS.md",
        "destination": "AGENTS.md",
        "tier": 1,
        "overwrite": "never",
        "authored": True,
        "mirror_exact": "AGENTS.md",
    }
    bad = tmp_path / "manifest.yaml"
    bad.write_text(yaml.safe_dump({"schema_version": 1, "entries": [e]}), encoding="utf-8")
    with pytest.raises(ri.ManifestError):
        ri.load_manifest(bad, ramp_dir=RAMP_DIR)


# ── AC-04: tier monotonicity from the manifest ───────────────────────


@pytest.mark.req("REQ-YG-610")
def test_tier_expansion_is_monotonic_set_containment(entries):
    t1 = {e.destination for e in entries if e.tier <= 1}
    t2 = {e.destination for e in entries if e.tier <= 2}
    t3 = {e.destination for e in entries if e.tier <= 3}
    assert t1 and t1 < t2 < t3
    assert {e.destination for e in ri.select_tier(entries, 2)} == t2


# ── AC-05: dry-run ───────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-611")
@pytest.mark.parametrize("tier", [1, 2, 3])
def test_dry_run_prints_actions_writes_nothing(tmp_path, entries, tier):
    target = make_target(tmp_path)
    before = tree_state(target)
    r = run_cli(target, "--tier", str(tier), "--dry-run")
    assert r.returncode == 0, r.stderr
    assert tree_state(target) == before
    for e in ri.select_tier(entries, tier):
        assert e.destination in r.stdout
    assert "create" in r.stdout


@pytest.mark.req("REQ-YG-611")
def test_dry_run_prints_would_be_consumer_row(tmp_path):
    target = make_target(tmp_path)
    consumers = tmp_path / "consumers.md"
    r = run_cli(
        target,
        "--tier",
        "1",
        "--dry-run",
        "--record-consumer",
        "acme/widget",
        env={"RAMP_CONSUMERS_FILE": str(consumers)},
    )
    assert r.returncode == 0, r.stderr
    assert "acme/widget" in r.stdout
    assert not consumers.exists()


# ── AC-06: Tier-1 install byte fidelity ──────────────────────────────


@pytest.mark.req("REQ-YG-611")
def test_tier1_install_creates_all_destinations_byte_identical(tmp_path, entries):
    target = make_target(tmp_path)
    r = run_cli(target, "--tier", "1")
    assert r.returncode == 0, r.stderr
    for e in ri.select_tier(entries, 1):
        dest = target / e.destination
        assert dest.is_file(), f"not installed: {e.destination}"
        assert dest.read_bytes() == (RAMP_DIR / e.source).read_bytes()
        if e.executable:
            assert os.access(dest, os.X_OK)
    assert "pre-commit install" in r.stdout  # printed, never executed


# ── AC-07: idempotency ───────────────────────────────────────────────


@pytest.mark.req("REQ-YG-611")
def test_second_run_is_idempotent(tmp_path, entries):
    target = make_target(tmp_path)
    assert run_cli(target, "--tier", "1").returncode == 0
    before = tree_state(target)
    r = run_cli(target, "--tier", "1")
    assert r.returncode == 0, r.stderr
    assert tree_state(target) == before
    for e in ri.select_tier(entries, 1):
        assert f"skip exists {e.destination}" in r.stdout


# ── AC-08: AGENTS.md sentinel and --force contract ───────────────────


@pytest.mark.req("REQ-YG-612")
def test_existing_agents_md_survives_without_force(tmp_path):
    target = make_target(tmp_path)
    sentinel = "# SENTINEL — real doctrine, do not clobber\n"
    (target / "AGENTS.md").write_text(sentinel, encoding="utf-8")
    r = run_cli(target, "--tier", "1")
    assert r.returncode == 0, r.stderr
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == sentinel


@pytest.mark.req("REQ-YG-612")
def test_force_overwrite_backs_up_and_records_hashes(tmp_path):
    target = make_target(tmp_path)
    sentinel = "# SENTINEL\n"
    (target / "AGENTS.md").write_text(sentinel, encoding="utf-8")
    r = run_cli(target, "--tier", "1", "--force")
    assert r.returncode == 0, r.stderr
    doc = ri.parse_target_manifest(target / "docs" / "ramp-manifest.md")
    row = doc["rows"]["AGENTS.md"]
    assert row["action"] == "overwritten"
    backup = target / row["backup"]
    assert backup.read_text(encoding="utf-8") == sentinel
    assert row["installed_sha256"] == sha256(target / "AGENTS.md")


# ── AC-09: target manifest record ────────────────────────────────────


@pytest.mark.req("REQ-YG-612")
def test_ramp_manifest_doc_records_everything(tmp_path, entries):
    target = make_target(tmp_path)
    assert run_cli(target, "--tier", "1").returncode == 0
    doc = ri.parse_target_manifest(target / "docs" / "ramp-manifest.md")
    assert doc["source_sha"]
    for e in ri.select_tier(entries, 1):
        row = doc["rows"][e.destination]
        assert row["source"] == e.source
        assert row["action"] == "created"
        assert row["installed_sha256"] == sha256(target / e.destination)


# ── AC-10: rollback ──────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-612")
def test_rollback_deletes_created_restores_backups(tmp_path, entries):
    target = make_target(tmp_path)
    sentinel = "# SENTINEL\n"
    (target / "AGENTS.md").write_text(sentinel, encoding="utf-8")
    pre_existing = tree_state(target)
    assert run_cli(target, "--tier", "1", "--force").returncode == 0
    r = run_cli(target, "--rollback")
    assert r.returncode == 0, r.stderr
    for e in ri.select_tier(entries, 1):
        if e.destination == "AGENTS.md":
            continue
        assert not (target / e.destination).exists()
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == sentinel
    after = {k: v[0] for k, v in tree_state(target).items()}
    for path, (digest, _) in pre_existing.items():
        assert after.get(path) == digest, f"pre-existing file harmed: {path}"


# ── AC-11: refusals ──────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-612")
@pytest.mark.parametrize(
    "shape", ["non-repo", "worktree", "missing-tests", "missing-ruff"]
)
def test_refusals_exit_nonzero_write_nothing(tmp_path, shape):
    target = make_target(tmp_path, shape=shape)
    before = tree_state(target)
    r = run_cli(target, "--tier", "1")
    assert r.returncode != 0
    assert tree_state(target) == before


@pytest.mark.req("REQ-YG-612")
def test_refuses_nested_subdirectory(tmp_path):
    target = make_target(tmp_path)
    nested = target / "tests"
    r = run_cli(nested, "--tier", "1")
    assert r.returncode != 0
    assert not (nested / "AGENTS.md").exists()


@pytest.mark.req("REQ-YG-612")
def test_refuses_this_repository():
    r = run_cli(REPO_ROOT, "--tier", "1")
    assert r.returncode != 0
    assert "refus" in (r.stderr + r.stdout).lower()


# ── AC-12: source scans ──────────────────────────────────────────────


@pytest.mark.req("REQ-YG-613")
def test_installer_source_scan_no_llm_network_or_target_git():
    src = CLI.read_text(encoding="utf-8")
    for token in (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "anthropic",
        "openai",
        "create_llm",
    ):
        assert token not in src, f"forbidden token in installer: {token}"
    # the only git invocation allowed is rev-parse against this repo
    for token in ("git add", "git commit", "git push", "git init", "git checkout"):
        assert token not in src, f"target-mutating git in installer: {token}"


@pytest.mark.req("REQ-YG-613")
def test_tier1_assets_are_domain_free(entries):
    for e in ri.select_tier(entries, 1):
        text = (RAMP_DIR / e.source).read_text(encoding="utf-8")
        for marker in (".chaplain", "REQ-YG", "examples/", "yamlgraph/"):
            assert marker not in text, f"domain marker {marker!r} in {e.source}"


@pytest.mark.req("REQ-YG-613")
def test_no_hook_logs_or_pycache_shipped(entries):
    for e in entries:
        for part in ("logs", "__pycache__", "audit.jsonl"):
            assert part not in Path(e.source).parts
            assert part not in Path(e.destination).parts


# ── AC-13: CI asset is an explicit inert stub ────────────────────────


@pytest.mark.req("REQ-YG-613")
def test_ci_workflow_is_inert_setup_stub(entries):
    ci = [
        e
        for e in ri.select_tier(entries, 1)
        if e.destination.startswith(".github/workflows/")
    ]
    assert len(ci) == 1
    text = (RAMP_DIR / ci[0].source).read_text(encoding="utf-8")
    wf = yaml.safe_load(text)
    triggers = wf.get("on") or wf.get(True)
    assert triggers == "workflow_dispatch" or list(triggers) == ["workflow_dispatch"]
    assert "stub" in text.lower()
    assert "schedule:" not in text
    assert "secrets." not in text


# ── AC-16: curated Tier-1 pre-commit config is consumed here ─────────


def _curated_precommit(entries) -> Path:
    matches = [
        e
        for e in ri.select_tier(entries, 1)
        if e.destination == ".pre-commit-config.yaml"
    ]
    assert len(matches) == 1
    return RAMP_DIR / matches[0].source


@pytest.mark.req("REQ-YG-613")
def test_curated_precommit_config_is_valid(entries):
    if not shutil.which("pre-commit"):
        pytest.skip("pre-commit not installed")
    r = subprocess.run(
        ["pre-commit", "validate-config", str(_curated_precommit(entries))],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr


@pytest.mark.req("REQ-YG-613")
@pytest.mark.slow
def test_curated_precommit_runs_against_fixture(tmp_path, entries):
    if not shutil.which("pre-commit"):
        pytest.skip("pre-commit not installed")
    target = tmp_path / "target"
    shutil.copytree(FIXTURE, target)
    subprocess.run(["git", "init", "-q"], cwd=target, check=True)
    subprocess.run(["git", "add", "-A"], cwd=target, check=True)
    r = subprocess.run(
        ["pre-commit", "run", "--all-files", "-c", str(_curated_precommit(entries))],
        cwd=target,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"curated config failed on fixture:\n{r.stdout}"


# ── AC-17: drift evidence ────────────────────────────────────────────


@pytest.mark.req("REQ-YG-613")
def test_mirror_exact_entries_match_live_bytes(entries):
    mirrored = [e for e in entries if e.provenance == "mirror_exact"]
    assert mirrored, "expected at least one mirror_exact entry"
    for e in mirrored:
        live = REPO_ROOT / e.mirror_exact
        assert live.is_file(), f"live counterpart missing: {e.mirror_exact}"
        assert (RAMP_DIR / e.source).read_bytes() == live.read_bytes(), (
            f"drift: {e.source} != live {e.mirror_exact} — re-copy or record a "
            "curation diff (FR-865 AC-17)"
        )


@pytest.mark.req("REQ-YG-613")
def test_curation_diff_entries_have_records(entries):
    curated = [e for e in entries if e.provenance == "curation_diff"]
    assert curated, "expected at least one curation_diff entry"
    diffs = (RAMP_DIR / "curation-diffs.md").read_text(encoding="utf-8")
    for e in curated:
        record, _, anchor = e.curation_diff.partition("#")
        assert record == "curation-diffs.md"
        section = diffs.split(f"## {anchor}")
        assert len(section) == 2, f"no record for {e.source} (anchor {anchor})"
        body = section[1].split("\n## ")[0]
        for field in ("live source:", "curated asset:", "removed/changed:", "reason:"):
            assert field in body, f"record {anchor} missing {field!r}"


# ── AC-18: consumer registry ─────────────────────────────────────────


@pytest.mark.req("REQ-YG-613")
def test_record_consumer_appends_then_updates_idempotently(tmp_path):
    target = make_target(tmp_path)
    consumers = tmp_path / "consumers.md"
    env = {"RAMP_CONSUMERS_FILE": str(consumers)}
    r1 = run_cli(target, "--tier", "1", "--record-consumer", "acme/widget", env=env)
    assert r1.returncode == 0, r1.stderr
    r2 = run_cli(target, "--tier", "1", "--record-consumer", "acme/widget", env=env)
    assert r2.returncode == 0, r2.stderr
    rows = [
        ln
        for ln in consumers.read_text(encoding="utf-8").splitlines()
        if ln.startswith("|") and "acme/widget" in ln
    ]
    assert len(rows) == 1
    assert "/Users" not in consumers.read_text(encoding="utf-8")


@pytest.mark.req("REQ-YG-613")
@pytest.mark.parametrize(
    "slug",
    ["/abs/path", "https://user:pass@github.com/a/b", "git@github.com:a/b", "plain"],
)
def test_record_consumer_rejects_non_slug(tmp_path, slug):
    target = make_target(tmp_path)
    consumers = tmp_path / "consumers.md"
    r = run_cli(
        target,
        "--tier",
        "1",
        "--record-consumer",
        slug,
        env={"RAMP_CONSUMERS_FILE": str(consumers)},
    )
    assert r.returncode != 0
    assert not consumers.exists()


@pytest.mark.req("REQ-YG-613")
def test_consumers_registry_documents_schema():
    text = (RAMP_DIR / "consumers.md").read_text(encoding="utf-8")
    assert "| target |" in text
    assert "manifest" in text
    assert "slug" in text.lower()


# ── wrapper ──────────────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-611")
def test_wrapper_delegates(tmp_path):
    target = make_target(tmp_path)
    assert os.access(WRAPPER, os.X_OK)
    r = subprocess.run(
        [str(WRAPPER), str(target), "--tier", "1", "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert "create" in r.stdout
