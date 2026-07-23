#!/usr/bin/env python3
"""PreToolUse guard (matcher: Bash) — vet packages at install time.

Intercepts npm/pnpm/yarn/bun/pip/uv add-package commands, resolves each
requested package against the registry and OSV.dev, and:

  deny  — an OSV malware advisory (MAL-) affects the resolved version
  ask   — version published under the cooldown window (default 24h — most
          2024–2026 malicious releases were pulled within hours), package
          not found (typo / LLM-hallucinated name an attacker may have
          registered), or verification impossible (network down: fail
          closed to a human decision, never a silent allow)
  pass  — silently, for everything else (CVE-only advisories surface as
          context, not blocks: routine CVE triage belongs to audit
          tooling, and denying on every CVE would train users to disable
          the gate)

This is the install-time layer the ecosystem lacks: CVE auditors lag
malware by design, and advisories publish after the fact — the cooldown
"ask" covers the gap between a malicious publish and its advisory.

Non-install commands exit in microseconds (no network). Lockfile-only
installs (bare `npm install`/`pnpm install`) pass — the gate targets NEW
specs; sweep lockfiles with `osv-scanner` (security-audit skill, Mode A).
Knobs: VIBE_MIN_RELEASE_AGE_HOURS (default 24), VIBE_DEP_GATE_MAX_PKGS
(default 5, latency bound). Python 3.9+ stdlib only.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

TIMEOUT_SECONDS = 6
MIN_AGE_HOURS = float(os.environ.get("VIBE_MIN_RELEASE_AGE_HOURS", "24"))
MAX_PKGS = int(os.environ.get("VIBE_DEP_GATE_MAX_PKGS", "5"))

INSTALL_RE = re.compile(
    r"\b(?:(npm)\s+(?:install|i|add)|(pnpm)\s+(?:add|install|i)|"
    r"(yarn)\s+add|(bun)\s+(?:add|install|i)|"
    r"(pip3?)\s+install|(uv)\s+(?:add|pip\s+install))\s+(.*)",
)
# Flags and flag-values we skip while collecting package specs.
SKIP_VALUE_FLAGS = {"-r", "--requirement", "--index-url", "-i", "--registry",
                    "--extra-index-url", "-t", "--target"}


def parse_specs(command):
    """Return (ecosystem, [(name, version|None), …]) or (None, [])."""
    m = INSTALL_RE.search(command)
    if not m:
        return None, []
    ecosystem = "PyPI" if (m.group(5) or m.group(6)) else "npm"
    specs, skip_next = [], False
    for token in m.group(7).split():
        token = token.strip("'\"")  # shells quote specs: "pkg==1.0", '.[dev]'
        if skip_next:
            skip_next = False
            continue
        if not token:
            continue
        if token in SKIP_VALUE_FLAGS:
            skip_next = True
            continue
        if token.startswith("-"):
            continue
        if token in {"&&", "||", ";", "|"}:
            break  # only judge the install segment
        if ecosystem == "npm":
            # @scope/name@ver | name@ver | name ; git/file/url specs -> name unknown, skip
            if token.startswith(("git+", "file:", "http:", "https:", ".", "/")):
                continue
            at = token.rfind("@")
            if at > 0:
                specs.append((token[:at], token[at + 1:] or None))
            else:
                specs.append((token, None))
        else:
            if token.startswith(("git+", "http:", "https:", ".", "/", "-e")):
                continue
            pin = re.match(r"([A-Za-z0-9._\-\[\]]+)==([\w.\-+!]+)$", token)
            if pin:
                specs.append((pin.group(1).split("[")[0], pin.group(2)))
            else:
                name = re.split(r"[<>=!~;]", token)[0].split("[")[0]
                if name:
                    specs.append((name, None))
    return ecosystem, specs


def http_json(url, payload=None):
    try:
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json",
                     "User-Agent": "vibe-dependency-gate/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, "404" if e.code == 404 else f"HTTP {e.code}"
    except Exception as e:
        return None, f"{type(e).__name__}"


def parse_iso(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def resolve(ecosystem, name, version):
    """-> (resolved_version, published_at, error)"""
    if ecosystem == "npm":
        doc, err = http_json(f"https://registry.npmjs.org/{name}")
        if err:
            return None, None, err
        version = version or doc.get("dist-tags", {}).get("latest")
        return version, parse_iso(doc.get("time", {}).get(version, "")), None
    suffix = f"/{version}" if version else ""
    doc, err = http_json(f"https://pypi.org/pypi/{name}{suffix}/json")
    if err:
        return None, None, err
    version = version or doc.get("info", {}).get("version")
    uploads = [parse_iso(u.get("upload_time_iso_8601", ""))
               for u in doc.get("urls", [])]
    return version, min((u for u in uploads if u), default=None), None


def judge(ecosystem, name, version):
    """-> (decision, reason) with decision in deny|ask|note|pass."""
    resolved, published, err = resolve(ecosystem, name, version)
    if err == "404":
        return "ask", (f"{name}: not found on {ecosystem} — possible typo or "
                       "hallucinated name (slopsquat risk); verify the name")
    if err:
        return "ask", (f"{name}: registry unreachable ({err}) — cannot verify; "
                       "failing closed to a human decision")

    payload = {"package": {"name": name, "ecosystem": ecosystem},
               "version": resolved}
    osv, osv_err = http_json("https://api.osv.dev/v1/query", payload)
    if osv_err and osv_err != "404":
        return "ask", (f"{name}@{resolved}: OSV unreachable ({osv_err}) — "
                       "malware status unverified; failing closed")
    ids = [v.get("id", "") for v in (osv or {}).get("vulns", [])]
    mal = sorted(i for i in ids if i.startswith("MAL-"))
    if mal:
        return "deny", (f"{name}@{resolved}: OSV malware advisories "
                        f"{', '.join(mal[:4])} — do not install this version")

    if published:
        age_h = (datetime.now(timezone.utc) - published).total_seconds() / 3600
        if age_h < MIN_AGE_HOURS:
            return "ask", (f"{name}@{resolved}: published {age_h:.1f}h ago "
                           f"(< {MIN_AGE_HOURS:.0f}h cooldown) — most malicious "
                           "releases are caught within hours; wait, or approve "
                           "if this fresh version is intentional")
    cves = len(ids)
    if cves:
        return "note", (f"{name}@{resolved}: {cves} known vulnerability "
                        "advisories (CVE/GHSA) — review before relying on it")
    return "pass", ""


def emit(decision, reasons, notes):
    out = {"hookEventName": "PreToolUse"}
    if decision in ("deny", "ask"):
        out["permissionDecision"] = decision
        out["permissionDecisionReason"] = "[vibe dependency-gate] " + " | ".join(reasons)
    if notes:
        out["additionalContext"] = "[vibe dependency-gate] " + " | ".join(notes)
    if len(out) > 1:
        print(json.dumps({"hookSpecificOutput": out}))


def main():
    payload = json.load(sys.stdin)
    if payload.get("tool_name") != "Bash":
        return
    command = payload.get("tool_input", {}).get("command", "") or ""
    ecosystem, specs = parse_specs(command)
    if not specs:
        return  # not an install of new specs — zero-cost pass

    dropped = len(specs) - MAX_PKGS
    reasons, notes, decision = [], [], "pass"
    for name, version in specs[:MAX_PKGS]:
        verdict, reason = judge(ecosystem, name, version)
        if verdict == "deny":
            decision = "deny"
            reasons.append(reason)
        elif verdict == "ask":
            if decision != "deny":
                decision = "ask"
            reasons.append(reason)
        elif verdict == "note":
            notes.append(reason)
    if dropped > 0:
        # never silently truncate a safety check
        if decision == "pass":
            decision = "ask"
        reasons.append(f"{dropped} further package(s) not checked "
                       f"(VIBE_DEP_GATE_MAX_PKGS={MAX_PKGS}) — verify them "
                       "with the security-audit skill")
    emit(decision, reasons, notes)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # fail closed — but to "ask", not "deny": a gate
        # bug shouldn't hard-block all installs, and "ask" still surfaces it.
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                f"[vibe dependency-gate] gate error ({type(e).__name__}: {e}) "
                "— could not vet this install; approve manually or fix the hook"),
        }}))
    sys.exit(0)
