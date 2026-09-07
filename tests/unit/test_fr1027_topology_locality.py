"""FR-1027 witnesses — frozen topology (AC-02, AC-04) and locality audit (AC-17).

The topology test asserts the committed graph against the FR § Frozen
topology: node set, edge order, slots, every LLM node Azure-pinned at
temperature 0, every map with a numeric max_items, and no `model:` key.
The locality audit scans every committed artifact of the demo for private
identifiers: non-demo GitHub owners in commands/fixtures, Atlassian hosts,
non-fixture issue keys, e-mails, and output roots outside the two allowed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO = REPO_ROOT / "examples" / "demos" / "org_ai_dossier"
ADAPTERS = REPO_ROOT / "examples" / "demos" / "corpus_census" / "adapters"
GRAPH = yaml.safe_load((DEMO / "graph.yaml").read_text(encoding="utf-8"))

EXPECTED_NODES = [
    "preflight",
    "coverage_gh",
    "gh_discover",
    "gh_extract_items",
    "inject_repo_canaries",
    "gh_search",
    "classify_repos",
    "coverage_jira",
    "jira_discover",
    "jira_extract_items",
    "inject_jira_canaries",
    "classify_jira",
    "reduce",
    "prepare_person_input",
    "summarize_persons",
    "prepare_findings_input",
    "synthesize_findings",
    "synthesize_onepager",
    "render_artifacts",
]
EXPECTED_SLOTS = {
    "preflight",
    "gh_discover",
    "gh_extract",
    "gh_search",
    "jira_coverage",
    "jira_discover",
    "jira_extract",
}
EXPECTED_STATE = {
    "org",
    "visibility",
    "window_days",
    "top_persons",
    "persons_llm",
    "persons_llm_ack",
    "out_dir",
    "preflight_ok",
    "coverage_gh",
    "api_calls_estimated",
    "llm_calls_estimated",
    "run_started",
    "repo_items",
    "repo_bundles",
    "search_hits",
    "repo_findings",
    "coverage_jira",
    "jira_items",
    "jira_bundles",
    "jira_findings",
    "reduced",
    "person_input",
    "persons_llm_active",
    "person_summaries",
    "findings_input",
    "findings_claims",
    "onepager_claims",
    "artifacts",
}


def _llm_nodes():
    for name, node in GRAPH["nodes"].items():
        if node.get("type") == "llm":
            yield name, node
        if node.get("type") == "map" and node["node"].get("type") == "llm":
            yield name, node["node"]


@pytest.mark.req("REQ-YG-670")
def test_topology_nodes_slots_state_frozen():
    assert list(GRAPH["nodes"]) == EXPECTED_NODES
    slots = {n for n, t in GRAPH["tools"].items() if t.get("slot")}
    assert slots == EXPECTED_SLOTS
    assert set(GRAPH["state"]) == EXPECTED_STATE
    for key in (
        "repo_bundles",
        "repo_findings",
        "jira_bundles",
        "jira_findings",
        "person_summaries",
    ):
        assert GRAPH["state"][key].get("reducer") == "sorted_add", key
    assert GRAPH["defaults"] == {"provider": "azure", "temperature": 0.0}
    assert GRAPH["config"] == {
        "max_map_items": 400,
        "max_concurrency": 4,
        "timeout": 5400,
    }


@pytest.mark.req("REQ-YG-670")
def test_topology_edges_linear_with_single_persons_branch():
    edges = GRAPH["edges"]
    plain = [(e["from"], e["to"]) for e in edges if "condition" not in e]
    linear = list(
        zip(["START", *EXPECTED_NODES[:13]], EXPECTED_NODES[:14], strict=True)
    )
    for pair in linear:
        assert pair in plain, pair
    conds = {(e["from"], e["to"]): e["condition"] for e in edges if "condition" in e}
    assert conds == {
        ("prepare_person_input", "summarize_persons"): "persons_llm_active == true",
        (
            "prepare_person_input",
            "prepare_findings_input",
        ): "persons_llm_active != true",
    }
    for pair in [
        ("summarize_persons", "prepare_findings_input"),
        ("prepare_findings_input", "synthesize_findings"),
        ("synthesize_findings", "synthesize_onepager"),
        ("synthesize_onepager", "render_artifacts"),
        ("render_artifacts", "END"),
    ]:
        assert pair in plain, pair


@pytest.mark.req("REQ-YG-670")
def test_every_llm_node_azure_pinned_temperature_zero_no_model_no_fallback():
    llm = dict(_llm_nodes())
    assert set(llm) == {
        "classify_repos",
        "classify_jira",
        "summarize_persons",
        "synthesize_findings",
        "synthesize_onepager",
    }
    for name, node in llm.items():
        assert node.get("provider") == "azure", name
        assert node.get("temperature") in (0, 0.0), name
        assert "model" not in node and "fallback" not in node, name
    text = (DEMO / "graph.yaml").read_text(encoding="utf-8")
    assert "fallback" not in text and "\nmodel:" not in text


@pytest.mark.req("REQ-YG-670")
def test_every_map_has_numeric_max_items_and_python_nodes_fail_closed():
    for name, node in GRAPH["nodes"].items():
        if node.get("type") == "map":
            assert (
                isinstance(node.get("max_items"), int) and node["max_items"] > 0
            ), name
            if node["node"].get("type") == "python":
                assert node["node"].get("on_error") == "fail", name
        elif node.get("type") == "python":
            assert node.get("on_error") == "fail", name
    assert GRAPH["nodes"]["gh_extract_items"]["max_items"] == 400
    assert GRAPH["nodes"]["jira_extract_items"]["max_items"] == 150
    assert GRAPH["nodes"]["summarize_persons"]["max_items"] == 60


@pytest.mark.req("REQ-YG-670")
def test_prompts_exist_and_never_mention_canaries():
    for name in (
        "classify_repo_ai",
        "classify_jira_ai",
        "summarize_person",
        "synthesize_findings",
        "synthesize_onepager",
    ):
        text = (DEMO / "prompts" / f"{name}.yaml").read_text(encoding="utf-8").lower()
        assert "canary" not in text and "expected answer" not in text, name
        assert "schema:" in text, name


# --- locality audit (AC-17) ----------------------------------------------------------


ALLOWED_OWNER = "sheikkinen"
OWNER_RE = re.compile(r"--owner\s+([A-Za-z0-9_.-]+)|--var org=([A-Za-z0-9_.-]+)")
ISSUE_KEY_RE = re.compile(r"\b([A-Z][A-Z0-9_]{1,}-\d+)\b")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ATLASSIAN_RE = re.compile(r"[a-z0-9-]+\.atlassian\.net")
# Provider endpoint hostnames identify corp infrastructure; proofs must not carry them.
ENDPOINT_RE = re.compile(
    r"[a-z0-9.-]+\.(?:cognitiveservices\.azure\.com|openai\.azure\.com|services\.ai\.azure\.com)"
)
OUT_ROOT_RE = re.compile(r"out_dir=([^\s\\]+)")
ALLOWED_ISSUE_PREFIXES = (
    "DEMOAI-",
    "DEMOWEB-",
    "DEMOOLD-",
    "ISO-",
    "UTF-",
    "RFC-",
    "SHA-",
    "GPT-",
    "CANARYA-",
    "CANARYB-",
    "P000-",
    "P1-",
    "REQ-YG-",
    "FR-",
    "CAP-",
    "NC-",
    "ADR-",
    "CONF-",
    "AC-",
    "R-",
    "C-",
    "D-",
)


def _committed_artifacts() -> list[Path]:
    files = [
        DEMO / "graph.yaml",
        DEMO / "README.md",
        DEMO / "preflight.tool.yaml",
        DEMO / "smoke_preflight.tool.yaml",
        DEMO / "canaries.py",
    ]
    files += sorted((DEMO / "prompts").glob("*.yaml"))
    files += sorted((ADAPTERS / "fixtures" / "jira").glob("*.json"))
    files += sorted(ADAPTERS.glob("jira-*.tool.yaml")) + sorted(
        ADAPTERS.glob("gh-*.tool.yaml")
    )
    for log in (DEMO / "demo-output.log", ADAPTERS.parent / "demo-output.log"):
        if log.exists():
            files.append(log)
    return files


@pytest.mark.req("REQ-YG-670")
def test_locality_audit_no_private_identifiers_in_committed_artifacts():
    problems: list[str] = []
    for path in _committed_artifacts():
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(REPO_ROOT)
        for m in OWNER_RE.finditer(text):
            owner = m.group(1) or m.group(2)
            if owner not in (ALLOWED_OWNER, "<org>"):
                problems.append(f"{rel}: owner {owner!r}")
        if ATLASSIAN_RE.search(text):
            problems.append(f"{rel}: atlassian host")
        for m in ENDPOINT_RE.finditer(text):
            problems.append(f"{rel}: provider endpoint host {m.group(0)!r}")
        for m in EMAIL_RE.finditer(text):
            problems.append(f"{rel}: e-mail {m.group(0)!r}")
        for m in ISSUE_KEY_RE.finditer(text):
            if not m.group(1).startswith(ALLOWED_ISSUE_PREFIXES):
                problems.append(f"{rel}: issue key {m.group(1)!r}")
        for m in OUT_ROOT_RE.finditer(text):
            if not m.group(1).startswith(
                ("tmp/org-ai-dossier-smoke/", "research/org-ai-dossier/")
            ):
                problems.append(f"{rel}: out_dir {m.group(1)!r}")
    assert not problems, "\n".join(problems)


@pytest.mark.req("REQ-YG-670")
def test_demo_output_log_is_public_smoke_only():
    log = DEMO / "demo-output.log"
    assert log.exists(), "demo-output.log must be committed (smoke proof)"
    text = log.read_text(encoding="utf-8", errors="replace")
    assert "'persons_llm': 'false'" in text and "'visibility': 'public'" in text
    assert "jira-fixture-" in text or "coverage_jira" in text
    for repo_id in re.findall(r"'id': '([^/']+)/[^']+'", text):
        assert repo_id in (ALLOWED_OWNER, "__canary__"), repo_id


@pytest.mark.req("REQ-YG-670")
def test_readme_carries_fr962_warning_verbatim_and_policy_switch():
    readme = (DEMO / "README.md").read_text(encoding="utf-8")
    sibling = (
        REPO_ROOT / "examples" / "demos" / "person_profile_census" / "README.md"
    ).read_text(encoding="utf-8")
    warning = sibling[sibling.index("> **Use only on your own footprint") :]
    warning = warning[: warning.index("controller.") + len("controller.")]
    assert warning in readme, "FR-962 warning block must be reproduced verbatim"
    assert "persons_llm" in readme and "persons_llm_ack" in readme
    assert "research/org-ai-dossier/" in readme
