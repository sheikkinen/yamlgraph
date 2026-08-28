"""FR-900: ledger cache-price fix + monthly repo×model cost report.

Condemns the load_prices() cache_price defect (models.json schema key is
cache_read_price; the old reader priced cache reads at 0 for every model,
underestimating the calibrated best bound ~5×) and pins the new seams:
parse_price_sheet, module-level credits with a cache-write term, workspace
attribution, and the --month/--by-repo report.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

pytestmark = pytest.mark.process  # exercises scripts/ (FR-756 process boundary)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "vscode"))

import ledger  # noqa: E402

FABLE_SHEET = {
    "data": [
        {
            "capabilities": {"family": "claude-fable-5"},
            "billing": {
                "token_prices": {
                    "default": {
                        "input_price": 1000,
                        "output_price": 5000,
                        "cache_read_price": 100,
                        "cache_write_price": 1250,
                        "cache_write_1h_price": 2000,
                        "max_prompt_tokens": 200000,
                    },
                    "long_context": {
                        "input_price": 1000,
                        "output_price": 5000,
                        "cache_read_price": 100,
                        "max_prompt_tokens": 936000,
                    },
                }
            },
        }
    ]
}

FABLE_PRICES = {"in": 1000, "out": 5000, "cache": 100, "cache_w": 1250}


# ── AC-01: parser reads the real schema keys ─────────────────────────────────


@pytest.mark.req("REQ-YG-626")
def test_parse_price_sheet_reads_cache_read_and_write_prices():
    prices = ledger.parse_price_sheet(FABLE_SHEET)
    assert prices["claude-fable-5"] == FABLE_PRICES


# ── AC-02: load_prices delegates; missing sheet stays empty ─────────────────


@pytest.mark.req("REQ-YG-626")
def test_load_prices_delegates_to_parse_price_sheet(tmp_path, monkeypatch):
    sheet_dir = tmp_path / "ws1/GitHub.copilot-chat/debug-logs/s1"
    sheet_dir.mkdir(parents=True)
    (sheet_dir / "models.json").write_text(json.dumps(FABLE_SHEET))
    monkeypatch.setattr(ledger, "WS_STORAGE", tmp_path)
    assert ledger.load_prices()["claude-fable-5"] == FABLE_PRICES


@pytest.mark.req("REQ-YG-626")
def test_load_prices_no_sheet_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "WS_STORAGE", tmp_path)
    assert ledger.load_prices() == {}


# ── AC-03/AC-04: credit arithmetic with cache read + write terms ────────────


@pytest.mark.req("REQ-YG-626")
def test_credits_fable_best_includes_cache_read_and_write():
    prices = {"claude-fable-5": FABLE_PRICES}
    best, worst = ledger.credits(prices, "claude-fable-5", 1_000_000, 0)
    # best = 0.02 × (1000 + 1250) + 0.98 × 100 = 143 cr per 1M prompt tokens
    assert best == pytest.approx(143.0, abs=0.1)
    assert worst == pytest.approx(1000.0)


@pytest.mark.req("REQ-YG-626")
def test_unknown_model_fallback_is_conservative_and_has_cache_write():
    assert "cache_w" in ledger.UNKNOWN_MODEL_PRICE
    known = {"claude-fable-5": FABLE_PRICES}
    best_unknown, worst_unknown = ledger.credits({}, "mystery-model", 1_000_000, 1000)
    best_fable, worst_fable = ledger.credits(known, "claude-fable-5", 1_000_000, 1000)
    assert best_unknown >= best_fable
    assert worst_unknown >= worst_fable


# ── AC-05: workspace name resolution ─────────────────────────────────────────


@pytest.mark.req("REQ-YG-626")
@pytest.mark.parametrize("key", ["folder", "workspace", "configuration"])
def test_workspace_name_resolves_uri_basename(tmp_path, key):
    ws = tmp_path / "0123456789abcdef"
    ws.mkdir()
    (ws / "workspace.json").write_text(json.dumps({key: "file:///Users/x/src/myrepo"}))
    assert ledger.workspace_name(ws) == "myrepo"


@pytest.mark.req("REQ-YG-626")
def test_workspace_name_falls_back_to_hash_prefix(tmp_path):
    ws = tmp_path / "0123456789abcdef"
    ws.mkdir()
    assert ledger.workspace_name(ws) == "01234567"


# ── AC-06/AC-07: repo attribution through iter_requests and the report ──────


def _fake_store(tmp_path: Path) -> Path:
    ws = tmp_path / "aaaa1111"
    (ws / "chatSessions").mkdir(parents=True)
    (ws / "workspace.json").write_text(json.dumps({"folder": "file:///src/repo-a"}))
    ts = int(datetime(2026, 8, 15, 12, 0).timestamp() * 1000)
    old = int(datetime(2026, 7, 1, 12, 0).timestamp() * 1000)
    (ws / "chatSessions/s1.jsonl").write_text(
        f'{{"requestId":"r1","timestamp":{ts},"modelId":"copilot/claude-fable-5",'
        f'"promptTokens":1000000,"outputTokens":100}}\n'
        f'{{"requestId":"r2","timestamp":{old},"modelId":"copilot/claude-fable-5",'
        f'"promptTokens":500,"outputTokens":5}}\n'
    )
    return tmp_path


@pytest.mark.req("REQ-YG-626")
def test_iter_requests_yields_repo_name(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "WS_STORAGE", _fake_store(tmp_path))
    rows = list(ledger.iter_requests())
    assert len(rows) == 2
    when, model, prompt, out, sid, repo = rows[0]
    assert repo == "repo-a"
    assert model == "claude-fable-5"
    assert sid == "s1"


@pytest.mark.req("REQ-YG-626")
def test_month_by_repo_report_groups_and_totals(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ledger, "WS_STORAGE", _fake_store(tmp_path))
    monkeypatch.setattr(ledger, "load_prices", lambda: {"claude-fable-5": FABLE_PRICES})
    monkeypatch.setattr(sys, "argv", ["ledger.py", "--month", "2026-08", "--by-repo"])
    ledger.main()
    out = capsys.readouterr().out
    assert "repo-a" in out
    assert "claude-fable-5" in out
    # only the August request is included: 1 req, not the July one
    assert "TOTAL" in out
    total_line = next(line for line in out.splitlines() if "TOTAL" in line)
    assert "1 req" in total_line


# ── AC-09: CLI smoke ─────────────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-626")
@pytest.mark.parametrize("args", [["--help"], ["--tap"]])
def test_cli_smoke_exits_zero(args):
    r = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts/vscode/ledger.py"), *args],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0, r.stderr
