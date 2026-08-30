#!/usr/bin/env python3
"""FR-902 session-lane guard analyzer (extracted by FR-889 §4c).

Once a session owns a lane (record in logs/session-lanes/), write-shaped
tool calls targeting THIS repository outside the lane are denied with
redirection to the lane. Reads and out-of-repo writes are untouched.

FR-889 §4c retired the cwd-proxy heuristics: the hook payload cwd is the
workspace root, never the terminal's actual cwd, so treating `git …` or
interpreter invocations as writes-to-cwd produced systematic false
denials (five live witnesses in one enforcement session). Only commands
with resolvable explicit targets are guarded.

The escape FR902_ALLOW_OUTSIDE=1 is recognized per-segment by tokenizer
(the position-0 regex missed `cd x && FR902_ALLOW_OUTSIDE=1 …`) and
lifts ONLY this denial class — later checks still apply (C-5).

Contract (env in, stdout out):
  HOOK_INPUT       hook payload JSON
  HOOK_GUARD_ROOT  realpath of the repository this guard polices
  FR902_REC        path to the session-lane record JSON
  DENY\t<lane>       out-of-lane write
  OVERRIDE\t<lane>   escape armed (audited by the caller)
  (empty)            nothing to report — fail-open by design
"""

import json
import os
import re
import sys

PATHISH = re.compile(r"[^\s\"';|&<>]+")
EDIT_TOOLS = {
    "create_file",
    "replace_string_in_file",
    "multi_replace_string_in_file",
    "apply_patch",
}
WRITE_VERBS = (
    "cp",
    "mv",
    "rsync",
    "install",
    "touch",
    "mkdir",
    "rm",
    "ln",
    "chmod",
    "truncate",
    "dd",
)


def escape_armed(cmd: str) -> bool:
    """FR902_ALLOW_OUTSIDE=1 as env prefix in ANY segment (§4c tokenizer)."""
    for seg in re.split(r"&&|\|\||;|\|", cmd):
        toks = seg.split()
        while toks and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0]):
            if toks[0] == "FR902_ALLOW_OUTSIDE=1":
                return True
            toks.pop(0)
    return False


def terminal_targets(cmd: str) -> list[str]:
    targets = []
    for m in re.finditer(r">>?\s*[\"']?(" + PATHISH.pattern + ")", cmd):
        targets.append(m.group(1))
    for m in re.finditer(r"\btee\s+(?:-a\s+)?[\"']?(" + PATHISH.pattern + ")", cmd):
        targets.append(m.group(1))
    for seg in re.split(r"&&|\|\||;|\|", cmd):
        toks = seg.split()
        while toks and (
            re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0])
            or toks[0] in ("time", "nohup", "nice")
        ):
            toks.pop(0)
        if not toks:
            continue
        if toks[0] in WRITE_VERBS:
            targets += [t for t in toks[1:] if not t.startswith("-")]
        if toks[0] == "sed" and any(t.startswith("-i") for t in toks):
            targets += [t for t in toks[1:] if not t.startswith("-")]
    return targets


def edit_targets(ti: dict) -> list[str]:
    targets = []
    if ti.get("filePath"):
        targets.append(ti["filePath"])
    for r in ti.get("replacements") or []:
        if isinstance(r, dict) and r.get("filePath"):
            targets.append(r["filePath"])
    patch = ti.get("input") or ti.get("patch") or ""
    if isinstance(patch, str):
        targets += re.findall(r"\*\*\* (?:Add|Update|Delete|Move to) File: (.+)", patch)
    return targets


def main() -> None:
    try:
        d = json.loads(os.environ.get("HOOK_INPUT", "{}"))
        with open(os.environ["FR902_REC"]) as fh:
            rec = json.load(fh)
        lane = os.path.realpath(rec["lane"])
        root = os.path.realpath(os.environ["HOOK_GUARD_ROOT"])
    except Exception:
        sys.exit(0)  # fail-open: unreadable record must not brick the session
    if not lane or not os.path.isdir(lane):
        sys.exit(0)

    tool = d.get("tool_name", d.get("toolName", ""))
    ti = d.get("tool_input", d.get("toolInput", d.get("input", {}))) or {}
    if not isinstance(ti, dict):
        ti = {}
    cwd = d.get("cwd", "") or "."

    def resolve(p: str) -> str:
        p = str(p).strip().strip("'\"")
        for pwd_form in ("$PWD", "${PWD}", "$(pwd)"):
            if p.startswith(pwd_form):
                p = cwd + p[len(pwd_form) :]
                break
        return os.path.realpath(p if os.path.isabs(p) else os.path.join(cwd, p))

    def inside(p: str, base: str) -> bool:
        return p == base or p.startswith(base + os.sep)

    if tool in EDIT_TOOLS:
        targets = edit_targets(ti)
        cmd = ""
    else:
        cmd = ti.get("command", "") or ""
        targets = terminal_targets(cmd)

    for t in targets:
        rp = resolve(t)
        if inside(rp, root) and not inside(rp, lane):
            esc = os.environ.get("FR902_ALLOW_OUTSIDE", "") == "1"
            if not esc and tool in ("run_in_terminal", "send_to_terminal"):
                esc = escape_armed(cmd)
            print(("OVERRIDE\t" if esc else "DENY\t") + lane)
            break


if __name__ == "__main__":
    main()
