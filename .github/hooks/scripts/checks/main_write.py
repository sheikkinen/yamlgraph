#!/usr/bin/env python3
"""FR-889 main-write check — edit tools + lock-mutator fence.

The terminal write barrier on the main checkout is the OS lock
(scripts/worktree.sh lock-main): the kernel refuses the write, no
parsing involved. This module covers only what the kernel cannot:

  1. Editor tool writes (create_file, replace, apply_patch) run as the
     owner and are classified by git plumbing — worktree vs main.
  2. Lock-mutator verbs (chmod/chflags/setfacl) aimed at a governed
     root on main would remove the lock itself and are fenced.
     Operator-decided escapes: git is never fenced; sudo-prefixed forms
     are human-authorized by the password prompt and pass.

The FR-888 shell write grammar is deleted, not relocated (FR-889 C-5).

Contract (env in, stdout out):
  HOOK_INPUT       hook payload JSON
  HOOK_GUARD_ROOT  realpath of the repository this guard polices
  DENY\tedit\t<target>    enforcement-class edit-tool write on main
  DENY-FENCE\t<target>    lock-mutator aimed at a governed root on main
  OVERRIDE\t<realpath>    FR888_ALLOW_MAIN=1 escape armed (audited)
  (empty)                 nothing to report
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

GIT = shutil.which("git") or "/usr/bin/git"

ENFORCE = (
    "yamlgraph/",
    "tests/",
    "scripts/",
    "capabilities/",
    ".github/hooks/",
    "docs/",
    "feature-requests/",
)
DOCS = ("changelog/", "research/", "tmp/", "logs/")
FENCE_VERBS = {"chmod", "chflags", "setfacl"}
EDIT_TOOLS = {
    "create_file",
    "replace_string_in_file",
    "multi_replace_string_in_file",
    "apply_patch",
}


def textual_enforcement(p: str) -> bool:
    s = str(p).replace("\\", "/")
    return any(("/" + e) in ("/" + s) or s.startswith(e) for e in ENFORCE) or any(
        ("/" + e.rstrip("/") + "/") in s for e in ENFORCE
    )


def classify(abs_path: str, guard_root: str) -> str | None:
    """Return 'deny' | 'deny-parse' | None (not enforcement-relevant)."""
    p = Path(abs_path)
    probe = p.parent
    while not probe.is_dir() and probe != probe.parent:
        probe = probe.parent
    try:
        out = subprocess.run(  # noqa: S603  # CONF-441
            [
                GIT,
                "-C",
                str(probe),
                "rev-parse",
                "--path-format=absolute",
                "--git-common-dir",
                "--git-dir",
                "--show-toplevel",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode != 0:
            raise RuntimeError(out.stderr)
        common, gitdir, top = out.stdout.splitlines()[:3]
    except Exception:
        # parse error: fail closed only when an enforcement-class target
        # is textually present (FR-888 R-2, carried forward)
        return "deny-parse" if textual_enforcement(abs_path) else None
    if os.path.realpath(common) != os.path.realpath(gitdir):
        return None  # linked worktree: allowed
    if guard_root and os.path.realpath(top) != guard_root:
        return None  # foreign repository: not ours to police
    try:
        rel = str(Path(os.path.realpath(abs_path)).relative_to(os.path.realpath(top)))
    except ValueError:
        return None
    rel = rel.replace("\\", "/")
    if any(rel == dl.rstrip("/") or rel.startswith(dl) for dl in DOCS):
        return None
    if any(rel == e.rstrip("/") or rel.startswith(e) for e in ENFORCE):
        return "deny"
    return None


def edit_tool_paths(ti: dict) -> list[str]:
    paths = []
    if ti.get("filePath"):
        paths.append(ti["filePath"])
    for r in ti.get("replacements") or []:
        if isinstance(r, dict) and r.get("filePath"):
            paths.append(r["filePath"])
    patch = ti.get("input") or ti.get("patch") or ""
    if isinstance(patch, str):
        paths += re.findall(r"\*\*\* (?:Add|Update|Delete|Move to) File: (.+)", patch)
        paths += re.findall(r"\*\*\* Move to: (.+)", patch)
    return paths


def fence_targets(cmd: str) -> list[str]:
    """Arguments of bare lock-mutator verbs; sudo segments pass whole."""
    hits: list[str] = []
    for seg in re.split(r"&&|\|\||;|\|", cmd):
        toks = seg.split()
        while toks and (
            re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0])
            or toks[0] in ("time", "nohup", "nice")
        ):
            toks.pop(0)
        if not toks or toks[0] == "sudo":
            continue  # sudo = human-authorized (operator decision 2026-08-30)
        if toks[0] in FENCE_VERBS:
            hits += [t for t in toks[1:] if not t.startswith("-")]
    return hits


def main() -> None:
    try:
        d = json.loads(os.environ.get("HOOK_INPUT", "{}"))
    except Exception:
        d = {}
    tool = d.get("tool_name", d.get("toolName", ""))
    ti = d.get("tool_input", d.get("toolInput", d.get("input", {}))) or {}
    if not isinstance(ti, dict):
        ti = {}
    cwd = d.get("cwd", "") or "."
    guard_root = (
        os.path.realpath(os.environ["HOOK_GUARD_ROOT"])
        if os.environ.get("HOOK_GUARD_ROOT")
        else ""
    )

    def resolve(p: str) -> str:
        p = str(p).strip().strip("'\"")
        for pwd_form in ("$PWD", "${PWD}", "$(pwd)"):
            if p.startswith(pwd_form):
                p = cwd + p[len(pwd_form) :]
                break
        return p if os.path.isabs(p) else os.path.join(cwd, p)

    escape = os.environ.get("FR888_ALLOW_MAIN", "") == "1"
    verdict, target = None, ""

    if tool in EDIT_TOOLS:
        for p in edit_tool_paths(ti):
            c = classify(resolve(p), guard_root)
            if c in ("deny", "deny-parse"):
                verdict, target = "edit", p
                break
    else:
        cmd = ti.get("command", "") or ""
        if re.match(r"\s*FR888_ALLOW_MAIN=1\b", cmd):
            escape = True
        for t in fence_targets(cmd):
            if classify(resolve(t), guard_root) in ("deny", "deny-parse"):
                verdict, target = "fence", t
                break

    if verdict and escape:
        print("OVERRIDE\t" + os.path.realpath(resolve(target)))
    elif verdict == "fence":
        print("DENY-FENCE\t" + target.replace('"', ""))
    elif verdict:
        print("DENY\tedit\t" + target.replace('"', ""))


if __name__ == "__main__":
    main()
