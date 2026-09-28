"""FR-1137: test corpus map — freeze, extract, partition, reconcile, canary, render.

The graph's LLM stage is a claim; these witnesses pin the deterministic code
that owns identity, coverage, ceilings, hashes and rendering around it.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
import yaml

from examples.demos.test_map import extract, reconcile, tools
from scripts.req_coverage import extract_req_markers

# References examples/ (process boundary, FR-756)
pytestmark = pytest.mark.process

DEMO = Path("examples/demos/test_map")

MARKED_SOURCE = '''\
"""Fixture module."""

import os
from pathlib import Path

import pytest

pytestmark = [pytest.mark.slow]


def helper():
    return os.sep


@pytest.mark.req("REQ-YG-001")
def test_plain():
    assert helper()


@pytest.mark.asyncio
async def test_async_one():
    assert Path(".")


@pytest.mark.process
class TestGroup:
    pytestmark = pytest.mark.integration

    @pytest.mark.req("REQ-YG-002")
    @pytest.mark.parametrize("x", [1, 2])
    def test_method(self, x):
        assert x

    def not_a_test(self):
        pass


class Helper:
    def test_ignored(self):
        pass
'''


def _test_block(name: str, lines: int) -> str:
    body = "".join(f"    value_{i} = {i}\n" for i in range(lines))
    return f"\n\ndef {name}():\n{body}    assert True\n"


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def _repo(tmp_path: Path, files: dict[str, str]) -> Path:
    root = tmp_path / "repo"
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "fixture")
    return root


def _freeze(root: Path, scope: str = "tests/unit") -> dict:
    return tools.freeze_corpus({"root": str(root), "scope": scope})["corpus"]


def _good_findings(corpus: dict, target: str = "core", ttype: str = "unit") -> list:
    findings = []
    for index, part in enumerate(corpus["partitions"]):
        records = [
            {
                "nodeid": nodeid,
                "description": "Checks the fixture behaviour.",
                "target": target,
                "test_type": ttype,
            }
            for nodeid in part["nodeids"]
        ]
        findings.append({"records": records, "_map_index": index})
    return findings


def _canary(tmp_path: Path, entries: list[dict], name: str = "canary.json") -> str:
    path = tmp_path / name
    path.write_text(json.dumps(entries), encoding="utf-8")
    return str(path)


def _publish_state(tmp_path: Path, corpus: dict, findings: list, **extra) -> dict:
    out = tmp_path / "out"
    state = {
        "corpus": corpus,
        "findings": findings,
        "findings_failures": [],
        "json_path": str(out / "test-map.json"),
        "md_path": str(out / "test-map.md"),
        "canary_path": _canary(tmp_path, [], "empty-canary.json"),
        "run_id": "run-fixture",
    }
    state.update(extra)
    return state


@pytest.fixture
def small_repo(tmp_path: Path) -> Path:
    return _repo(
        tmp_path,
        {
            "tests/unit/test_alpha.py": MARKED_SOURCE,
            "tests/unit/test_beta.py": "def test_beta():\n    assert 1\n",
            "tests/unit/conftest.py": "import pytest\n",
            "tests/unit/test_empty.py": "X = 1\n",
        },
    )


# --- AC-03 extraction -------------------------------------------------------


@pytest.mark.req("REQ-YG-723")
def test_extract_nodeids_lines_async_class_and_markers(tmp_path: Path) -> None:
    path = tmp_path / "test_alpha.py"
    path.write_text(MARKED_SOURCE, encoding="utf-8")
    rows = extract.extract_tests(path, "tests/unit/test_alpha.py")
    by_id = {row.nodeid: row for row in rows}
    assert list(by_id) == [
        "tests/unit/test_alpha.py::test_plain",
        "tests/unit/test_alpha.py::test_async_one",
        "tests/unit/test_alpha.py::TestGroup::test_method",
    ]
    plain = by_id["tests/unit/test_alpha.py::test_plain"]
    assert plain.line == MARKED_SOURCE.splitlines().index("def test_plain():") + 1
    assert plain.is_async is False
    assert plain.markers == ["slow"]
    assert by_id["tests/unit/test_alpha.py::test_async_one"].is_async is True
    assert by_id["tests/unit/test_alpha.py::test_async_one"].markers == [
        "asyncio",
        "slow",
    ]
    method = by_id["tests/unit/test_alpha.py::TestGroup::test_method"]
    assert method.markers == ["integration", "parametrize", "process", "slow"]
    assert "req" not in method.markers


@pytest.mark.req("REQ-YG-723")
def test_reqs_equal_imported_req_coverage_extractor(tmp_path: Path) -> None:
    path = tmp_path / "test_alpha.py"
    path.write_text(MARKED_SOURCE, encoding="utf-8")
    rows = extract.extract_tests(path, "tests/unit/test_alpha.py")
    expected: dict[str, list[str]] = {}
    for req, keys in extract_req_markers(path).items():
        for key in keys:
            expected.setdefault(key, []).append(req)
    got = {
        "::".join([path.stem, *row.nodeid.split("::")[1:]]): row.reqs
        for row in rows
        if row.reqs
    }
    assert got == {key: sorted(reqs) for key, reqs in expected.items()}
    assert got == {
        "test_alpha::test_plain": ["REQ-YG-001"],
        "test_alpha::TestGroup::test_method": ["REQ-YG-002"],
    }


@pytest.mark.req("REQ-YG-723")
def test_freeze_records_sha_hashes_bytes_and_skips_non_test_files(
    small_repo: Path,
) -> None:
    corpus = _freeze(small_repo)
    prov = corpus["provenance"]
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=small_repo, capture_output=True, text=True
    ).stdout.strip()
    assert prov["commit_sha"] == head
    paths = [entry["path"] for entry in prov["files"]]
    assert paths == [
        "tests/unit/test_alpha.py",
        "tests/unit/test_beta.py",
        "tests/unit/test_empty.py",
    ]
    alpha = prov["files"][0]
    raw = (small_repo / "tests/unit/test_alpha.py").read_bytes()
    assert alpha["sha256"] == hashlib.sha256(raw).hexdigest()
    assert alpha["bytes"] == len(raw)
    assert alpha["tests"] == 3
    assert prov["counts"] == {"files": 3, "tests": 4, "partitions": 2}
    lines = "".join(f"{e['path']}\t{e['sha256']}\n" for e in prov["files"])
    assert prov["corpus_hash"] == hashlib.sha256(lines.encode()).hexdigest()


@pytest.mark.req("REQ-YG-723")
@pytest.mark.parametrize("dirt", ["modified", "untracked"])
def test_freeze_rejects_dirty_scope(small_repo: Path, dirt: str) -> None:
    if dirt == "modified":
        (small_repo / "tests/unit/test_beta.py").write_text("def test_x(): pass\n")
    else:
        (small_repo / "tests/unit/test_new.py").write_text("def test_x(): pass\n")
    with pytest.raises(ValueError, match="dirty"):
        _freeze(small_repo)


# --- AC-04 partitioning and ceilings ----------------------------------------


@pytest.mark.req("REQ-YG-723")
def test_small_file_is_one_payload_with_imports_and_metadata(tmp_path: Path) -> None:
    path = tmp_path / "test_alpha.py"
    path.write_text(MARKED_SOURCE, encoding="utf-8")
    rows = extract.extract_tests(path, "tests/unit/test_alpha.py")
    payloads = extract.build_payloads(
        "tests/unit/test_alpha.py", MARKED_SOURCE, rows, 8000
    )
    assert len(payloads) == 1
    payload = payloads[0]
    assert payload.partition_id == "tests/unit/test_alpha.py#1"
    assert payload.path == "tests/unit/test_alpha.py"
    assert payload.nodeids == [row.nodeid for row in rows]
    assert "import os" in payload.text
    assert "from pathlib import Path" in payload.text
    assert "async def test_async_one" in payload.text
    assert "def helper" not in payload.text


@pytest.mark.req("REQ-YG-723")
def test_large_file_splits_only_between_whole_tests(tmp_path: Path) -> None:
    source = "import os\n" + "".join(_test_block(f"test_{i}", 40) for i in range(12))
    path = tmp_path / "test_big.py"
    path.write_text(source, encoding="utf-8")
    rows = extract.extract_tests(path, "tests/unit/test_big.py")
    payloads = extract.build_payloads("tests/unit/test_big.py", source, rows, 600)
    assert len(payloads) > 1
    assert [p.partition_id for p in payloads] == [
        f"tests/unit/test_big.py#{i}" for i in range(1, len(payloads) + 1)
    ]
    flat = [nodeid for p in payloads for nodeid in p.nodeids]
    assert flat == [row.nodeid for row in rows]
    for payload in payloads:
        assert payload.text.count("import os") == 1
        assert payload.est_tokens <= 600
        for nodeid in payload.nodeids:
            name = nodeid.rsplit("::", 1)[1]
            assert f"def {name}():" in payload.text
            assert "    value_39 = 39\n    assert True" in payload.text
    again = extract.build_payloads("tests/unit/test_big.py", source, rows, 600)
    assert again == payloads


@pytest.mark.req("REQ-YG-723")
def test_single_test_over_token_budget_fails(tmp_path: Path) -> None:
    source = "import os\n" + _test_block("test_huge", 400)
    path = tmp_path / "test_huge.py"
    path.write_text(source, encoding="utf-8")
    rows = extract.extract_tests(path, "tests/unit/test_huge.py")
    with pytest.raises(ValueError, match="token"):
        extract.build_payloads("tests/unit/test_huge.py", source, rows, 600)


@pytest.mark.req("REQ-YG-723")
@pytest.mark.parametrize(
    ("ceiling", "value", "match"),
    [
        ("MAX_FILES", 2, "files"),
        ("MAX_SOURCE_BYTES", 10, "bytes"),
        ("MAX_PARTITIONS", 1, "partitions"),
        ("MAX_PAYLOAD_TOKENS", 5, "token"),
    ],
)
def test_ceilings_reject_before_any_llm_call(
    small_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    ceiling: str,
    value: int,
    match: str,
) -> None:
    monkeypatch.setattr(tools, ceiling, value)
    with pytest.raises(ValueError, match=match):
        _freeze(small_repo)


# --- AC-05 model policy and graph wiring -------------------------------------


@pytest.mark.req("REQ-YG-723")
def test_provenance_records_default_provider_model_resolution(
    small_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PROVIDER", "inception")
    monkeypatch.setitem(tools.DEFAULT_MODELS, "inception", "mercury-fixture")
    prov = _freeze(small_repo)["provenance"]
    assert (prov["provider"], prov["model"], prov["temperature"]) == (
        "inception",
        "mercury-fixture",
        0.0,
    )
    monkeypatch.delenv("PROVIDER")
    prov = _freeze(small_repo)["provenance"]
    assert prov["provider"] == "anthropic"
    assert prov["model"] == tools.DEFAULT_MODELS["anthropic"]


def _graph() -> dict:
    return yaml.safe_load((DEMO / "graph.yaml").read_text(encoding="utf-8"))


def _map_node(graph: dict) -> dict:
    maps = [n for n in graph["nodes"].values() if n.get("type") == "map"]
    assert len(maps) == 1
    return maps[0]


@pytest.mark.req("REQ-YG-723")
def test_graph_map_uses_default_model_and_frozen_ceilings() -> None:
    graph = _graph()
    assert "provider" not in graph.get("defaults", {})
    assert "model" not in graph.get("defaults", {})
    node = _map_node(graph)
    sub = node["node"]
    assert sub["type"] == "llm"
    assert "provider" not in sub and "model" not in sub
    assert sub["temperature"] == tools.TEMPERATURE
    assert sub["timeout"] == tools.CALL_TIMEOUT_S
    assert sub["on_error"] == "retry"
    assert sub["max_retries"] >= 1
    assert node["min_success"] == pytest.approx(1 - tools.MAX_FAILED_PARTITION_RATE)
    assert node["max_items"] == tools.MAX_PARTITIONS
    config = graph["config"]
    assert config["max_map_items"] == tools.MAX_PARTITIONS
    assert config["max_concurrency"] == tools.MAX_CONCURRENCY
    assert config["timeout"] == tools.GRAPH_TIMEOUT_S
    assert "canary" not in json.dumps(sub)


@pytest.mark.req("REQ-YG-723")
def test_prompt_schema_enums_and_tie_break_match_tools() -> None:
    sub = _map_node(_graph())["node"]
    prompt = yaml.safe_load(
        (DEMO / "prompts" / f"{sub['prompt']}.yaml").read_text(encoding="utf-8")
    )
    text = json.dumps(prompt)
    for value in (*reconcile.TARGETS, *reconcile.TEST_TYPES):
        assert f'"{value}"' in text
    assert " > ".join(reconcile.TIE_BREAK) in text
    assert "canary" not in text.lower()


# --- AC-06 reconciliation rejects every defect -------------------------------


def _mutate(kind: str, corpus: dict, findings: list) -> tuple[list, list]:
    failures: list = []
    first = findings[0]["records"]
    if kind == "missing":
        first.pop()
    elif kind == "unknown":
        first.append({**first[0], "nodeid": "tests/unit/test_alpha.py::test_ghost"})
    elif kind == "duplicate":
        first.append(dict(first[0]))
    elif kind == "bad_target":
        first[0]["target"] = "framework"
    elif kind == "bad_type":
        first[0]["test_type"] = "e2e"
    elif kind == "bad_description":
        first[0]["description"] = "Checks one thing. Then another."
    elif kind == "wrong_partition":
        moved = findings[1]["records"].pop()
        first.append(moved)
    elif kind == "map_error":
        findings.pop(1)
        failures.append(
            {
                "map": "map_partitions",
                "dispatch": "d1",
                "index": 1,
                "error_type": "TIMEOUT_ERROR",
                "message": "provider timeout",
                "node": "map_partitions",
                "tolerated": True,
            }
        )
    elif kind == "missing_result":
        findings.pop(1)
    elif kind == "malformed":
        first[0] = {"nodeid": first[0]["nodeid"]}
    return findings, failures


DEFECTS = [
    "missing",
    "unknown",
    "duplicate",
    "bad_target",
    "bad_type",
    "bad_description",
    "wrong_partition",
    "map_error",
    "missing_result",
    "malformed",
]


@pytest.mark.req("REQ-YG-723")
@pytest.mark.parametrize("kind", DEFECTS)
def test_any_defect_rejects_and_writes_only_diagnostics(
    small_repo: Path, tmp_path: Path, kind: str
) -> None:
    corpus = _freeze(small_repo)
    findings, failures = _mutate(kind, corpus, _good_findings(corpus))
    state = _publish_state(tmp_path, corpus, findings, findings_failures=failures)
    out = Path(state["json_path"]).parent
    out.mkdir(parents=True)
    Path(state["json_path"]).write_text("stale", encoding="utf-8")
    Path(state["md_path"]).write_text("stale", encoding="utf-8")
    with pytest.raises(RuntimeError, match="rejected"):
        tools.publish_map(state)
    assert not Path(state["json_path"]).exists()
    assert not Path(state["md_path"]).exists()
    report = json.loads((out / "test-map-rejected.json").read_text(encoding="utf-8"))
    assert report["defects"], kind
    assert kind in {d["kind"] for d in report["defects"]}
    assert report["raw_findings"]


@pytest.mark.req("REQ-YG-723")
def test_runtime_map_failure_objects_still_write_the_rejection_report(
    small_repo: Path, tmp_path: Path
) -> None:
    # The map runtime delivers MapFailure models, not dicts (full run 2026-09-28).
    from yamlgraph.models.map_results import MapFailure

    corpus = _freeze(small_repo)
    findings, failures = _mutate("map_error", corpus, _good_findings(corpus))
    state = _publish_state(
        tmp_path,
        corpus,
        findings,
        findings_failures=[MapFailure.model_validate(f) for f in failures],
    )
    with pytest.raises(RuntimeError, match="rejected"):
        tools.publish_map(state)
    out = Path(state["json_path"]).parent
    report = json.loads((out / "test-map-rejected.json").read_text(encoding="utf-8"))
    assert report["failures"][0]["message"] == "provider timeout"
    assert "map_error" in {d["kind"] for d in report["defects"]}


# --- Operator amendment: at most 5% of partitions may fail ------------------


@pytest.fixture
def wide_repo(tmp_path: Path) -> Path:
    files = {
        f"tests/unit/test_w{i:02d}.py": f"def test_w{i:02d}():\n    assert 1\n"
        for i in range(20)
    }
    return _repo(tmp_path, files)


def _fail_partition(kind: str, findings: list, failures: list, index: int) -> None:
    if kind == "map_error":
        findings[:] = [f for f in findings if f["_map_index"] != index]
        failures.append(
            {
                "map": "classify",
                "dispatch": "d1",
                "index": index,
                "error_type": "ValidationError",
                "message": "Input should be an object",
                "node": "_map_classify_sub",
                "tolerated": False,
            }
        )
    else:
        findings[index]["records"][0]["description"] = "Two. Sentences."


@pytest.mark.req("REQ-YG-723")
@pytest.mark.parametrize("kind", ["map_error", "bad_description"])
def test_failed_partitions_within_rate_are_listed_not_hidden(
    wide_repo: Path, tmp_path: Path, kind: str
) -> None:
    corpus = _freeze(wide_repo)
    assert len(corpus["partitions"]) == 20
    findings, failures = _good_findings(corpus), []
    _fail_partition(kind, findings, failures, 3)
    state = _publish_state(tmp_path, corpus, findings, findings_failures=failures)
    tools.publish_map(state)
    doc = json.loads(Path(state["json_path"]).read_text(encoding="utf-8"))
    lost = corpus["partitions"][3]
    assert [f["partition_id"] for f in doc["failed_partitions"]] == [
        lost["partition_id"]
    ]
    assert doc["failed_partitions"][0]["nodeids"] == lost["nodeids"]
    assert kind in {d["kind"] for d in doc["failed_partitions"][0]["defects"]}
    assert lost["nodeids"][0] not in {row["nodeid"] for row in doc["rows"]}
    assert len(doc["rows"]) == 19
    recon = doc["provenance"]["reconciliation"]
    assert (recon["failed_partitions"], recon["failed_rows"]) == (1, 1)
    markdown = Path(state["md_path"]).read_text(encoding="utf-8")
    assert "## Failed partitions" in markdown
    assert f"`{lost['nodeids'][0]}`" in markdown


@pytest.mark.req("REQ-YG-723")
def test_failure_rate_over_limit_rejects(wide_repo: Path, tmp_path: Path) -> None:
    corpus = _freeze(wide_repo)
    findings, failures = _good_findings(corpus), []
    _fail_partition("map_error", findings, failures, 3)
    _fail_partition("bad_description", findings, failures, 7)
    state = _publish_state(tmp_path, corpus, findings, findings_failures=failures)
    with pytest.raises(RuntimeError, match="rejected"):
        tools.publish_map(state)
    assert not Path(state["json_path"]).exists()
    out = Path(state["json_path"]).parent
    report = json.loads((out / "test-map-rejected.json").read_text(encoding="utf-8"))
    assert "failure_rate" in {d["kind"] for d in report["defects"]}


@pytest.mark.req("REQ-YG-723")
def test_unattributed_defect_rejects_under_the_rate(
    wide_repo: Path, tmp_path: Path
) -> None:
    corpus = _freeze(wide_repo)
    findings = _good_findings(corpus)
    findings.append(dict(findings[0]))
    state = _publish_state(tmp_path, corpus, findings)
    with pytest.raises(RuntimeError, match="rejected"):
        tools.publish_map(state)


@pytest.mark.req("REQ-YG-723")
def test_canary_in_failed_partition_is_skipped_not_passed(
    wide_repo: Path, tmp_path: Path
) -> None:
    corpus = _freeze(wide_repo)
    findings, failures = _good_findings(corpus), []
    _fail_partition("map_error", findings, failures, 3)
    canary = _canary(
        tmp_path,
        [
            {"nodeid": nid, "target": "core", "test_type": "unit"}
            for nid in (
                corpus["partitions"][3]["nodeids"][0],
                corpus["partitions"][4]["nodeids"][0],
            )
        ],
    )
    state = _publish_state(
        tmp_path, corpus, findings, findings_failures=failures, canary_path=canary
    )
    tools.publish_map(state)
    doc = json.loads(Path(state["json_path"]).read_text(encoding="utf-8"))
    assert doc["provenance"]["canary"] == {"checked": 2, "passed": 1, "skipped": 1}


@pytest.mark.req("REQ-YG-723")
def test_bad_description_keeps_raw_text_in_diagnostics(
    small_repo: Path, tmp_path: Path
) -> None:
    corpus = _freeze(small_repo)
    findings, _ = _mutate("bad_description", corpus, _good_findings(corpus))
    state = _publish_state(tmp_path, corpus, findings)
    with pytest.raises(RuntimeError):
        tools.publish_map(state)
    out = Path(state["json_path"]).parent
    report = json.loads((out / "test-map-rejected.json").read_text(encoding="utf-8"))
    defect = next(d for d in report["defects"] if d["kind"] == "bad_description")
    assert defect["raw"] == "Checks one thing. Then another."


# --- AC-07 taxonomy and the sentence boundary --------------------------------


@pytest.mark.req("REQ-YG-723")
@pytest.mark.parametrize(
    "target", ["core", "linter", "examples", "scripts", "docs", "other"]
)
@pytest.mark.parametrize("ttype", ["unit", "integration", "other"])
def test_every_target_and_type_is_accepted(
    small_repo: Path, tmp_path: Path, target: str, ttype: str
) -> None:
    assert (*reconcile.TARGETS,) == (
        "core",
        "linter",
        "examples",
        "scripts",
        "docs",
        "other",
    )
    assert (*reconcile.TEST_TYPES,) == ("unit", "integration", "other")
    corpus = _freeze(small_repo)
    result = tools.publish_map(
        _publish_state(tmp_path, corpus, _good_findings(corpus, target, ttype))
    )["result"]
    assert result["rows"] == 4


@pytest.mark.req("REQ-YG-723")
def test_tie_break_order_is_frozen() -> None:
    assert reconcile.TIE_BREAK == (
        "linter",
        "examples",
        "scripts",
        "docs",
        "core",
        "other",
    )


@pytest.mark.req("REQ-YG-723")
@pytest.mark.parametrize(
    "text",
    [
        "Checks that yamlgraph.linter flags graph.yaml nodes.",
        "Verifies defaults, e.g. the provider, are resolved.",
        "Asserts parsing works for v1.2 inputs!",
        "Does the loader reject tabs?",
        "Covers i.e. the empty case and etc. edge paths.",
    ],
)
def test_one_sentence_validator_accepts(text: str) -> None:
    assert reconcile.validate_description(text) is None


@pytest.mark.req("REQ-YG-723")
@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "Checks one thing",
        "Checks one thing. Then another.",
        "Checks one thing!  And more.",
        "Checks one thing.\nSecond line.",
        "Checks one thing..",
        "Checks one thing?!",
    ],
)
def test_one_sentence_validator_rejects(text: str) -> None:
    assert reconcile.validate_description(text) is not None


# --- AC-08 markdown derived from JSON ----------------------------------------


@pytest.mark.req("REQ-YG-723")
def test_markdown_counts_and_nodeids_match_json(
    small_repo: Path, tmp_path: Path
) -> None:
    corpus = _freeze(small_repo)
    findings = _good_findings(corpus)
    findings[0]["records"][0]["target"] = "linter"
    findings[0]["records"][1]["test_type"] = "integration"
    findings[0]["records"][2]["description"] = "Checks a | pipe in text."
    state = _publish_state(tmp_path, corpus, findings)
    tools.publish_map(state)
    doc = json.loads(Path(state["json_path"]).read_text(encoding="utf-8"))
    markdown = Path(state["md_path"]).read_text(encoding="utf-8")
    assert markdown == reconcile.render_markdown(doc)
    for row in doc["rows"]:
        assert markdown.count(f"`{row['nodeid']}`") == 1
    counts: dict[tuple[str, str], int] = {}
    for row in doc["rows"]:
        key = (row["target"], row["test_type"])
        counts[key] = counts.get(key, 0) + 1
    for (target, ttype), count in counts.items():
        assert f"| {target} | {ttype} | {count} |" in markdown
    assert "a \\| pipe" in markdown


# --- AC-09 withheld canary ---------------------------------------------------


@pytest.mark.req("REQ-YG-723")
def test_payloads_carry_no_canary_answers(small_repo: Path) -> None:
    corpus = _freeze(small_repo)
    for part in corpus["partitions"]:
        assert set(part) == {"partition_id", "path", "nodeids", "text", "est_tokens"}


@pytest.mark.req("REQ-YG-723")
@pytest.mark.parametrize("miss", ["mismatch", "absent"])
def test_canary_miss_rejects_before_render(
    small_repo: Path, tmp_path: Path, miss: str
) -> None:
    corpus = _freeze(small_repo)
    nodeid = (
        "tests/unit/test_beta.py::test_beta"
        if miss == "mismatch"
        else "tests/unit/test_beta.py::test_gone"
    )
    canary = _canary(
        tmp_path, [{"nodeid": nodeid, "target": "docs", "test_type": "unit"}]
    )
    state = _publish_state(tmp_path, corpus, _good_findings(corpus), canary_path=canary)
    with pytest.raises(RuntimeError, match="rejected"):
        tools.publish_map(state)
    assert not Path(state["json_path"]).exists()
    assert not Path(state["md_path"]).exists()
    report = json.loads(
        (Path(state["json_path"]).parent / "test-map-rejected.json").read_text(
            encoding="utf-8"
        )
    )
    assert {d["kind"] for d in report["defects"]} == {f"canary_{miss}"}


@pytest.mark.req("REQ-YG-723")
def test_committed_canary_covers_every_target_and_unit_integration() -> None:
    entries = json.loads((DEMO / "canary.json").read_text(encoding="utf-8"))
    assert {e["target"] for e in entries} == set(reconcile.TARGETS)
    assert any(
        e["nodeid"].startswith("tests/unit/") and e["test_type"] == "integration"
        for e in entries
    )
    for entry in entries:
        rel = entry["nodeid"].split("::", 1)[0]
        rows = extract.extract_tests(Path(rel), rel)
        assert entry["nodeid"] in {row.nodeid for row in rows}


# --- AC-10 provenance --------------------------------------------------------


@pytest.mark.req("REQ-YG-723")
def test_accepted_provenance_is_complete(small_repo: Path, tmp_path: Path) -> None:
    corpus = _freeze(small_repo)
    canary = _canary(
        tmp_path,
        [
            {
                "nodeid": "tests/unit/test_beta.py::test_beta",
                "target": "core",
                "test_type": "unit",
            }
        ],
    )
    state = _publish_state(tmp_path, corpus, _good_findings(corpus), canary_path=canary)
    result = tools.publish_map(state)["result"]
    doc = json.loads(Path(state["json_path"]).read_text(encoding="utf-8"))
    prov = doc["provenance"]
    frozen = corpus["provenance"]
    for key in (
        "commit_sha",
        "files",
        "corpus_hash",
        "provider",
        "model",
        "temperature",
        "counts",
        "scope",
        "ceilings",
    ):
        assert prov[key] == frozen[key]
    assert prov["run_id"] == "run-fixture"
    rows_blob = json.dumps(doc["rows"], sort_keys=True, separators=(",", ":"))
    assert prov["artifact_hash"] == hashlib.sha256(rows_blob.encode()).hexdigest()
    assert prov["calls"] == {"estimated": 2, "actual": 2}
    assert prov["reconciliation"] == {
        "rows": 4,
        "failed_rows": 0,
        "failed_partitions": 0,
        "defects": 0,
        "max_failed_partition_rate": tools.MAX_FAILED_PARTITION_RATE,
    }
    assert prov["canary"] == {"checked": 1, "passed": 1, "skipped": 0}
    assert doc["failed_partitions"] == []
    assert result["artifact_hash"] == prov["artifact_hash"]
    assert [row["nodeid"] for row in doc["rows"]] == [
        row["nodeid"] for row in corpus["rows"]
    ]
    raw = (Path(state["json_path"]).parent / "raw-responses.jsonl").read_text(
        encoding="utf-8"
    )
    assert [json.loads(line)["partition_id"] for line in raw.splitlines()] == [
        part["partition_id"] for part in corpus["partitions"]
    ]
