#!/usr/bin/env python3
"""Pre-install package safety check: live OSV lookup + registry metadata.

Checks one package (optionally a specific version) for:
  - OSV.dev advisories, split into malware (MAL- prefix) vs vulnerabilities
    (CVE/GHSA) — malware coverage is the gap `npm audit` doesn't fill
  - publish recency (most 2024-2026 malicious versions lived <3h; a
    version younger than the cooldown window is the risky case)
  - npm lifecycle install scripts (preinstall/install/postinstall)
  - existence (a 404 name may be a typo or an LLM-hallucinated name that
    an attacker could register — slopsquatting)

Live queries, not a hardcoded IOC list, so results reflect today's
advisories. Fails closed: any network/parse failure downgrades to CAUTION
("verify manually"), never a silent SAFE.

Usage:
  check-package.py --ecosystem npm  --name axios --version 1.14.1
  check-package.py --ecosystem PyPI --name requests
  check-package.py --ecosystem npm --name left-pad --json

Exit codes: 0 SAFE · 1 BLOCK (malware advisory hits the resolved version)
· 2 CAUTION (CVEs, too-new release, install scripts on a new dep, name
not found, or verification failed). Python 3.9+ stdlib only.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

OSV_QUERY_URL = "https://api.osv.dev/v1/query"
TIMEOUT_SECONDS = 10
DEFAULT_MIN_AGE_HOURS = 24  # mirrors pnpm 11's default minimumReleaseAge


def http_json(url, payload=None):
    """GET (payload None) or POST JSON; returns (data, error_string)."""
    try:
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json",
                     "User-Agent": "vibe-security-audit/1.0"},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode()), None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, "404"
        return None, f"HTTP {e.code} from {url}"
    except Exception as e:  # timeout, DNS, TLS, bad JSON — all fail closed
        return None, f"{type(e).__name__}: {e}"


def parse_iso(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def registry_metadata(ecosystem, name, version):
    """Resolve (version, published_at, install_scripts, error)."""
    if ecosystem == "npm":
        doc, err = http_json(f"https://registry.npmjs.org/{name}")
        if err:
            return None, None, [], err
        version = version or doc.get("dist-tags", {}).get("latest")
        published = parse_iso(doc.get("time", {}).get(version, ""))
        scripts = doc.get("versions", {}).get(version, {}).get("scripts", {})
        lifecycle = [s for s in ("preinstall", "install", "postinstall")
                     if s in scripts]
        return version, published, lifecycle, None

    # PyPI: version-specific endpoint gives that release's upload times
    suffix = f"/{version}" if version else ""
    doc, err = http_json(f"https://pypi.org/pypi/{name}{suffix}/json")
    if err:
        return None, None, [], err
    version = version or doc.get("info", {}).get("version")
    uploads = [parse_iso(u.get("upload_time_iso_8601", ""))
               for u in doc.get("urls", [])]
    published = min((u for u in uploads if u), default=None)
    return version, published, [], None  # PyPI has no npm-style scripts field


def osv_advisories(ecosystem, name, version):
    """Query OSV for the resolved version. Returns (mal_ids, vuln_ids, err)."""
    payload = {"package": {"name": name, "ecosystem": ecosystem}}
    if version:
        payload["version"] = version
    data, err = http_json(OSV_QUERY_URL, payload)
    if err and err != "404":
        return [], [], err
    ids = [v.get("id", "") for v in (data or {}).get("vulns", [])]
    return ([i for i in ids if i.startswith("MAL-")],
            [i for i in ids if not i.startswith("MAL-")],
            None)


def check(ecosystem, name, version, min_age_hours):
    result = {"ecosystem": ecosystem, "name": name,
              "requested_version": version, "verdict": "SAFE",
              "reasons": [], "notes": []}

    resolved, published, lifecycle, reg_err = registry_metadata(
        ecosystem, name, version)
    if reg_err == "404":
        result["verdict"] = "CAUTION"
        result["reasons"].append(
            "not found on the registry — possible typo or hallucinated "
            "name (slopsquat risk); verify the intended package name")
        return result
    if reg_err:
        result["verdict"] = "CAUTION"
        result["reasons"].append(
            f"registry unreachable ({reg_err}) — verify manually")
        return result
    result["resolved_version"] = resolved

    mal, vulns, osv_err = osv_advisories(ecosystem, name, resolved)
    if osv_err:
        result["verdict"] = "CAUTION"
        result["reasons"].append(
            f"OSV unreachable ({osv_err}) — malware status unverified")
    if mal:
        result["verdict"] = "BLOCK"
        result["reasons"].append(
            f"malware advisories affect {name}@{resolved}: "
            + ", ".join(sorted(mal)[:5]))
    elif vulns:
        if result["verdict"] == "SAFE":
            result["verdict"] = "CAUTION"
        result["reasons"].append(
            f"{len(vulns)} known vulnerability advisories affect "
            f"{resolved} (e.g. {', '.join(sorted(vulns)[:3])}) — review "
            "severity/fixed-in before installing")

    if published:
        age_hours = ((datetime.now(timezone.utc) - published)
                     .total_seconds() / 3600)
        result["published_at"] = published.isoformat()
        result["age_hours"] = round(age_hours, 1)
        if age_hours < min_age_hours and result["verdict"] != "BLOCK":
            result["verdict"] = "CAUTION"
            result["reasons"].append(
                f"published {age_hours:.1f}h ago (< {min_age_hours}h "
                "cooldown) — most malicious releases are caught within "
                "hours; wait or pin an older version")
    else:
        result["notes"].append("publish time unavailable — recency unchecked")

    if lifecycle:
        result["notes"].append(
            f"declares install scripts ({', '.join(lifecycle)}) — code "
            "runs at install time; inspect with `npm view "
            f"{name}@{resolved} scripts` before installing")
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ecosystem", required=True,
                    help="npm or PyPI (case-insensitive)")
    ap.add_argument("--name", required=True)
    ap.add_argument("--version", default=None)
    ap.add_argument("--min-age-hours", type=float,
                    default=DEFAULT_MIN_AGE_HOURS)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    eco = {"npm": "npm", "pypi": "PyPI"}.get(args.ecosystem.lower())
    if not eco:
        ap.error("--ecosystem must be npm or PyPI")

    result = check(eco, args.name, args.version, args.min_age_hours)

    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        target = f"{result['name']}@{result.get('resolved_version', '?')}"
        print(f"{result['verdict']}: {eco} {target}")
        for reason in result["reasons"]:
            print(f"  ! {reason}")
        for note in result["notes"]:
            print(f"  - {note}")

    sys.exit({"SAFE": 0, "BLOCK": 1, "CAUTION": 2}[result["verdict"]])


if __name__ == "__main__":
    main()
