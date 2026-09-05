"""yamlgraph-outsider (llm-node spike) — fetch a PR, derive the verdict, render, post.

Standalone: pydantic + stdlib + `gh`. No Copilot CLI, no repo doctrine.
The model's answer arrives as STRUCTURED output (prompt schema), so there is
no markdown parsing step; the fail-closed boundary is the schema plus the
checks below.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HEDGES = ("does not say", "something called", "not stated", "cannot tell")
MAX_UNCLEAR = 8
MAX_NEEDS = 10
_PR_RE = re.compile(r"^\d{1,7}$")
_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _pr_and_repo(state: dict[str, Any]) -> tuple[str, str]:
    """System boundary: the PR number and repo slug arrive from the CLI; validate before subprocess."""
    pr = str(state.get("pr", "")).strip()
    repo = str(state.get("repo", "")).strip()
    if not _PR_RE.match(pr):
        raise ValueError(f"pr must be a number, got {pr!r}")
    if not _REPO_RE.match(repo):
        raise ValueError(f"repo must be owner/name, got {repo!r}")
    return pr, repo


def _gh() -> str:
    path = shutil.which("gh")
    if not path:
        raise RuntimeError("gh CLI not found on PATH")
    return path


def fetch_pr(state: dict[str, Any]) -> str:
    """Title + body as markdown, via gh. `--var input_path=` bypasses GitHub for fixtures."""
    path = str(state.get("input_path") or "").strip()
    if path:
        return Path(path).read_text(encoding="utf-8")
    pr, repo = _pr_and_repo(state)
    out = subprocess.run(  # noqa: S603
        [_gh(), "pr", "view", pr, "-R", repo, "--json", "title,body,headRefOid"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    d = json.loads(out)
    return f"# {d['title']}\n\n{d['body']}\n\n<!-- head_sha: {d['headRefOid']} -->"


def _split_item(raw: str) -> tuple[str, str]:
    # Structured output gives one string per item: "“quote” · question" (or "quote — question").
    for sep in (" · ", " — ", " -- ", ": "):
        if sep in raw:
            q, _, rest = raw.partition(sep)
            return q.strip().strip("“”\"'`*"), rest.strip()
    return raw.strip().strip("“”\"'`*"), ""


def _lines(value: Any) -> list[str]:
    """Provider type lie (FR-059 class): lists arrive as JSON strings or newline text. Normalise here."""
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    text = str(value or "").strip()
    if text.startswith("["):
        try:
            return [str(x).strip() for x in json.loads(text) if str(x).strip()]
        except json.JSONDecodeError:
            pass
    return [ln.strip().lstrip("-*• ").strip() for ln in text.splitlines() if ln.strip()]


def finalize(state: dict[str, Any]) -> dict[str, Any]:
    """Validate the structured reading, derive the verdict, render, optionally post."""
    r = state.get("reading")
    if not isinstance(r, dict):
        r = getattr(r, "model_dump", lambda: None)() or {}
    restatement = str(r.get("restatement", "")).strip()
    opinion = str(r.get("opinion", "")).strip().upper()
    reason = str(r.get("opinion_reason", "")).strip()
    unclear = _lines(r.get("unclear"))
    needs = _lines(r.get("needs"))
    problems = []
    if not restatement:
        problems.append("empty restatement")
    if opinion not in {"YES", "NO"}:
        problems.append(f"opinion {opinion!r} not YES/NO")
    if not reason:
        problems.append("empty opinion reason")
    if len(unclear) > MAX_UNCLEAR:
        problems.append(f"{len(unclear)} unclear items > {MAX_UNCLEAR}")
    if len(needs) > MAX_NEEDS:
        problems.append(f"{len(needs)} needs > {MAX_NEEDS}")
    items = [_split_item(u) for u in unclear]
    if any(not q for q, _ in items) or any(not qq for _, qq in items):
        problems.append("an unclear item lacks a quote or a question")
    if problems:
        raise ValueError("reading rejected (fail closed): " + "; ".join(problems))

    low = restatement.casefold()
    verdict = "YES" if len(items) <= 2 and not any(h in low for h in HEDGES) else "NO"
    model = str(state.get("model", "?"))
    source = str(state.get("pr") or state.get("input_path") or "?")
    lines = [
        f"**Derived verdict:** {verdict}  (rule: ≤ 2 unclear items and no hedge in the restatement; computed in code)",
        f"<!-- yamlgraph-outsider (llm node) | source: {source} | model: {model} | {datetime.now(UTC).isoformat()} -->",
        "",
        "## 1. In my own words",
        "",
        restatement,
        "",
        "## 2. Could I decide whether to merge this from the description alone?",
        "",
        opinion,
        f"(model's non-authoritative opinion) {reason}",
        "",
        "## 3. Words and references I could not understand",
        "",
        *([f"- **“{q}”** · {qq}" for q, qq in items] or ["nothing"]),
        "",
        "## 4. What a merge decision would still need",
        "",
        *([f"- [ ] {n}" for n in needs] or ["nothing"]),
        "",
    ]
    report = "\n".join(lines)
    out = Path(str(state["report_path"]))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")

    posted = False
    if str(state.get("post", "false")).lower() == "true" and state.get("pr"):
        pr, repo = _pr_and_repo(state)
        subprocess.run(  # noqa: S603
            [_gh(), "pr", "comment", pr, "-R", repo, "--body-file", str(out)],
            check=True,
            capture_output=True,
        )
        posted = True
    return {
        "derived_verdict": verdict,
        "model_opinion": opinion,
        "unclear_count": len(items),
        "needs_count": len(needs),
        "report_path": str(out),
        "input_sha256": hashlib.sha256(
            str(state.get("pr_text", "")).encode()
        ).hexdigest()[:16],
        "posted": posted,
    }
