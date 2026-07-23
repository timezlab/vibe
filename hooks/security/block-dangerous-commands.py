#!/usr/bin/env python3
"""PreToolUse guard (matcher: Bash) — deny destructive/exfil command shapes.

Deterministic tripwire for the command classes that end sessions or leak
secrets: recursive force-deletes of critical paths, network-piped shells,
force-pushes to protected branches, disk-level writes, and shell-side
secret-file exfiltration. Guidance lives in rules/skills; this hook is the
enforcement layer that holds even when the model is steered.

Fail-closed by design: if this guard crashes on an input it should have
parsed, it denies with the error attached rather than silently allowing —
a broken guard that pretends to guard is worse than a loud one. (Most
community hooks exit 0 on their own errors; that inverts the safety
property.) To bypass a false positive, run the command yourself in a
terminal, or remove/adjust the hook in settings — the point is that the
*human* makes that call, not the model.

Self-contained: Python 3.9+ stdlib. Contract: stdin = PreToolUse JSON;
stdout = permissionDecision JSON on deny, nothing on pass; exit 0 always
(the JSON carries the decision).
"""

import json
import re
import sys

# Each entry: (compiled regex, reason). Patterns aim at unambiguous danger;
# routine commands (rm -rf node_modules, git push) must pass untouched.
RULES = [
    (r"\brm\s+(-[a-zA-Z]*[rR][a-zA-Z]*[fF][a-zA-Z]*|-[a-zA-Z]*[fF][a-zA-Z]*[rR][a-zA-Z]*|--recursive\s+--force|--force\s+--recursive)\s+"
     r"(/(\s|$)|/\*|~/?(\s|$)|\$HOME\b|\.\.\/?(\s|$)|\*|\.(\s|$))",
     "recursive force-delete targeting a critical path (/, ~, .., *, or cwd)"),
    (r"\b(curl|wget)\b[^|;&]*\|\s*(sudo\s+)?(ba|z|da|fi)?sh\b",
     "piping the network into a shell — download, inspect, then run instead"),
    (r"\bgit\s+push\b[^|;&]*(--force(?!-with-lease)|\s-f\b)[^|;&]*\b(main|master|production|release)\b",
     "force-push to a protected branch"),
    (r"\bgit\s+push\b[^|;&]*\b(origin|upstream)\s+(main|master|production|release)\b[^|;&]*(--force(?!-with-lease)|\s-f\b)",
     "force-push to a protected branch"),
    (r"\bchmod\s+(-[a-zA-Z]+\s+)*(0?777|a\+rwx)\b",
     "world-writable permissions (chmod 777)"),
    (r"\bmkfs(\.\w+)?\b",
     "filesystem format command"),
    (r"\bdd\b[^|;&]*\bof=/dev/(sd|hd|nvme|disk|vd)",
     "raw write to a block device"),
    (r">\s*/dev/(sd|hd|nvme|vd)[a-z0-9]*\b",
     "redirect onto a block device"),
    (r"\b(cat|less|more|head|tail|bat|cp|scp)\b[^|;&>]*[\s/]\.env"
     r"(\.(?!example\b|sample\b|template\b)[\w\-]+)*(\s|$)",
     "reading/copying a .env secrets file via shell — if intended, the human can do it in a terminal"),
    (r"\b(curl|wget|nc|ncat)\b[^;&]*\.(env|pem|key)\b",
     "network command touching a secret-bearing file (exfiltration shape)"),
]

COMPILED = [(re.compile(pattern), reason) for pattern, reason in RULES]


def deny(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"[vibe hooks/security] {reason}",
        }
    }))
    sys.exit(0)


def main():
    payload = json.load(sys.stdin)
    if payload.get("tool_name") != "Bash":
        return  # wrong wiring; nothing to judge
    command = payload.get("tool_input", {}).get("command", "") or ""
    for regex, reason in COMPILED:
        if regex.search(command):
            deny(f"blocked: {reason}.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # fail closed: a crashed guard must not silently allow
        deny(f"guard error ({type(e).__name__}: {e}) — failing closed; "
             "fix or remove this hook in settings to proceed")
    sys.exit(0)
