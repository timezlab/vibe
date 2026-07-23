#!/usr/bin/env python3
"""PreToolUse guard (matcher: Read|Edit|Write|NotebookEdit) — secret protection.

Two jobs:
  1. Deny file-tool access to secret-bearing paths (.env and friends, key
     material, credential stores) — reading them puts secrets into model
     context; writing them risks corruption or exfil-staging.
  2. Deny Write/Edit payloads containing live-looking credentials (AWS
     key IDs, GitHub/OpenAI/Slack/GitLab/npm token shapes, private-key
     blocks) — content-level scanning at write time, not just at commit
     time, because a secret written to *any* file is already on disk.

Placeholders stay usable: template files (.env.example/.sample/.template)
pass, and a matched token whose text contains EXAMPLE/PLACEHOLDER/CHANGEME
passes — docs about key formats should use exactly those. Real secrets are
high-entropy and never contain those words.

Deny messages name the pattern class, never the matched value — echoing a
secret into the transcript would itself be a leak.

Fail-closed like the other guards in this pack: crash → deny with the
error, not silent allow. Self-contained: Python 3.9+ stdlib. Contract:
stdin = PreToolUse JSON; stdout = permissionDecision JSON on deny; exit 0.
"""

import json
import re
import sys

GUARDED_TOOLS = {"Read", "Edit", "Write", "NotebookEdit"}

TEMPLATE_SUFFIXES = (".example", ".sample", ".template")

# Files whose embedded API key is public-by-design (Firebase mobile client
# configs — Google ships them in the app bundle, restricted by app id/SHA).
# Content-scanning them only yields known false positives.
PUBLIC_CLIENT_CONFIGS = ("google-services.json", "googleservice-info.plist")

# Path shapes that hold secrets. Matched against the full path, case-insensitive.
SENSITIVE_PATH_PATTERNS = [
    (r"(^|/)\.env(\.[\w.-]+)?$", ".env file"),
    (r"(^|/)(id_rsa|id_ed25519|id_ecdsa|id_dsa)(\.pub)?$", "SSH key"),
    (r"\.(pem|key|p12|pfx|jks|keystore)$", "key/certificate material"),
    (r"(^|/)(credentials|secrets?)\.(json|ya?ml|toml|xml|ini)$", "credentials file"),
    (r"(^|/)\.(aws|azure|gcloud|kube)/", "cloud credential directory"),
    (r"(^|/)\.(npmrc|pypirc|netrc|git-credentials|pgpass)$", "auth-token config"),
    (r"(^|/)(secrets?|credentials?)/", "secrets directory"),
]

# Live-credential shapes for content written via Write/Edit/NotebookEdit.
SECRET_CONTENT_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS access key ID"),
    (r"ghp_[A-Za-z0-9]{36}", "GitHub personal access token"),
    (r"github_pat_[A-Za-z0-9_]{22,}", "GitHub fine-grained PAT"),
    (r"AIza[0-9A-Za-z_\-]{35}", "Google API key"),
    # require a long *contiguous* alphanumeric run so hyphenated CSS/ident
    # tokens ("sk-ai-user-message-text") don't match — real keys are
    # high-entropy blocks, optionally after an sk-proj-/sk-svcacct- prefix.
    (r"sk-[A-Za-z0-9_\-]{0,12}[A-Za-z0-9]{20,}",
     "sk-prefixed API key (OpenAI/Anthropic-style)"),
    (r"xox[baprs]-[A-Za-z0-9\-]{10,}", "Slack token"),
    (r"glpat-[A-Za-z0-9_\-]{20,}", "GitLab personal access token"),
    (r"npm_[A-Za-z0-9]{36}", "npm access token"),
    (r"-----BEGIN\s+(RSA\s+|EC\s+|DSA\s+|OPENSSH\s+|PGP\s+)?PRIVATE KEY(\s+BLOCK)?-----",
     "private key block"),
]

PLACEHOLDER_MARKERS = ("EXAMPLE", "PLACEHOLDER", "CHANGEME", "XXXX")

PATH_COMPILED = [(re.compile(p, re.IGNORECASE), label)
                 for p, label in SENSITIVE_PATH_PATTERNS]
CONTENT_COMPILED = [(re.compile(p), label) for p, label in SECRET_CONTENT_PATTERNS]


def deny(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"[vibe hooks/security] {reason}",
        }
    }))
    sys.exit(0)


def written_text(tool_name, tool_input):
    if tool_name == "Write":
        return tool_input.get("content", "") or ""
    if tool_name == "Edit":
        return tool_input.get("new_string", "") or ""
    if tool_name == "NotebookEdit":
        return tool_input.get("new_source", "") or ""
    return ""  # Read writes nothing


def main():
    payload = json.load(sys.stdin)
    tool_name = payload.get("tool_name", "")
    if tool_name not in GUARDED_TOOLS:
        return
    tool_input = payload.get("tool_input", {}) or {}

    path = (tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    normalized = path.replace("\\", "/")
    if normalized and not normalized.lower().endswith(TEMPLATE_SUFFIXES):
        for regex, label in PATH_COMPILED:
            if regex.search(normalized):
                deny(f"{tool_name} on {label} blocked ({normalized}). Secret "
                     "files stay out of model context; use a template "
                     "(.example) variant, or access it yourself in a terminal.")

    text = written_text(tool_name, tool_input)
    if text and not normalized.lower().endswith(PUBLIC_CLIENT_CONFIGS):
        for regex, label in CONTENT_COMPILED:
            match = regex.search(text)
            if match and not any(m in match.group(0).upper()
                                 for m in PLACEHOLDER_MARKERS):
                deny(f"content matching a live {label} pattern blocked. Use an "
                     "obviously-fake placeholder (containing EXAMPLE/"
                     "PLACEHOLDER) — if this is a real credential it belongs "
                     "in a secret manager, and is now compromised enough to "
                     "rotate.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # fail closed: a crashed guard must not silently allow
        deny(f"guard error ({type(e).__name__}: {e}) — failing closed; "
             "fix or remove this hook in settings to proceed")
    sys.exit(0)
