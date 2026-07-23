# Supply-chain security — vetting dependencies

Read this when adding/updating packages (Mode A), reviewing a diff that
touches manifests or lockfiles, or responding to a supply-chain incident.

Contents:
1. Threat model — why version-level checking
2. Vector taxonomy
3. Checks per ecosystem (the commands)
4. Cooldown configuration
5. Lockfiles, pinning, provenance
6. Incident response
7. Known limits — what these checks cannot catch

## 1. Threat model — why version-level checking

"Is this package trustworthy?" is the wrong question; the right one is
"is this *version*, published *when*, clean *today*?" Representative
2024–2026 incidents (all real, all in OSV/vendor advisories):

| Incident | Date | Vector | Window live |
|---|---|---|---|
| xz-utils 5.6.0/5.6.1 backdoor | 2024-03 | years-long maintainer social engineering | weeks |
| polyfill.io CDN | 2024-06 | domain/account acquisition | months |
| ultralytics (PyPI) 8.3.41/42/45/46 | 2024-12 | GitHub Actions cache poisoning | days |
| tj-actions/changed-files | 2025-03 | CI compromise, all tags retagged | days |
| chalk/debug + ~18 npm pkgs | 2025-09 | maintainer phishing (fake 2FA reset) | ~2h |
| Shai-Hulud worm, waves 1–2 | 2025-09 / 2025-11 | token-stealing self-propagating postinstall; 796 pkgs in wave 2 | hours per pkg |
| axios 1.14.1 / 0.30.4 | 2026-03 | maintainer credential theft → phantom dep dropping a RAT | ~3h |
| Miasma / "Phantom Gyp" | 2026-06 | `binding.gyp` shell-exec at install, *no* postinstall script | <2h |

Two structural facts follow: (a) malicious versions are usually caught in
**hours**, so recency is the strongest single risk signal; (b) `npm
audit`/Dependabot are CVE-remediation tools — GitHub's advisory DB has a
malware category but Dependabot deliberately doesn't alert on it, and
advisories publish after the fact. Malware checking needs OSV's `MAL-`
records (or a behavioral scanner), not a CVE audit.

## 2. Vector taxonomy

- **Maintainer account takeover** — phishing/token theft; publishes to a
  *legitimate* name. Defense: cooldown + provenance, not name-checking.
- **Typosquatting** — near-miss names (`lodahs`). Defense: verify the
  exact name against the intended project's docs/repo.
- **Slopsquatting** — attackers register names LLMs hallucinate. If an
  agent proposed the name from memory, registry verification is
  mandatory: matching repo link, plausible download history, maintainers.
- **Dependency confusion** — public registry package shadowing an
  internal name at a higher version. Defense: scoped packages, registry
  config pinning internal scopes.
- **Install-script abuse** — pre/postinstall runs arbitrary code (the
  dominant 2024–26 payload vector). Defense: inspect scripts pre-install;
  `--ignore-scripts` where viable.
- **Install-time-without-scripts** — Miasma-class `binding.gyp`
  `<!(...)` shell-exec; evades script-only checks. Defense: cooldown +
  advisory lookup; no cheap static check exists.
- **Phantom dependency** — compromised release adds a new, never-imported
  dep that carries the payload (axios 2026). Review new transitive deps
  in lockfile diffs, not just direct ones.
- **Starjacking** — registry page links an unrelated famous repo to fake
  credibility; registries don't verify the link. Check the repo actually
  references the package back.
- **Compromised CI / Actions** — payload injected upstream of the
  registry account (ultralytics, tj-actions). Pin GitHub Actions to
  commit SHAs, not tags.

## 3. Checks per ecosystem

The bundled `scripts/check-package.py` automates the single-package
checks (OSV + recency + scripts + existence). Manual equivalents and
wider sweeps:

**OSV.dev — the free source that includes malware** (`MAL-` IDs):

```bash
# one package@version (ecosystem: npm | PyPI | Go | crates.io | …)
curl -s -d '{"package":{"name":"<pkg>","ecosystem":"npm"},"version":"<v>"}' \
  https://api.osv.dev/v1/query
# batch: POST https://api.osv.dev/v1/querybatch  {"queries":[…]}
# then split ids: MAL-* = malware, rest = CVEs/GHSA
```

**Whole lockfile** (preferred for audits — covers transitives):

```bash
osv-scanner scan -L package-lock.json    # also pnpm-lock.yaml, yarn.lock,
osv-scanner scan -L uv.lock              # requirements.txt, poetry.lock…
```

**npm registry metadata** (no install, nothing executes):

```bash
npm view <pkg> time --json     # publish timestamps per version
npm view <pkg>@<v> scripts     # lifecycle scripts that would run
npm pack <pkg>@<v>             # download tarball for inspection, no exec
```

**Python**: `pip-audit --vulnerability-service=osv` (default PyPA feed is
CVE-oriented; the OSV backend adds malware records — note: OSV's PyPI
malware coverage is thinner than npm's, treat a clean result as "no known
advisory", not "verified clean"). Release times:
`curl -s https://pypi.org/pypi/<pkg>/json | jq '.releases | keys'`.

**CVE-side complements**: `npm audit` / `pnpm audit` for fix-available
CVE triage; `deps.dev` API for cross-registry metadata and dependency
graphs. Behavioral scanners (Socket.dev and similar) detect malware
pre-advisory; their precision figures are vendor-reported — useful layer,
not ground truth.

## 4. Cooldown configuration

Nearly every incident above would have been harmless under a 24h install
delay. Units differ per tool — copy carefully:

| Tool | Setting | Unit | Since |
|---|---|---|---|
| pnpm | `minimumReleaseAge` | minutes | 10.16; default 1440 in pnpm 11+ |
| npm | `min-release-age` (`.npmrc`) | days | 11.10.0 |
| Bun | `minimumReleaseAge` | seconds | 2025 |
| Renovate | `minimumReleaseAge` | duration string | — (also constrains transitives via `--before`) |
| Dependabot | `cooldown` | days | mid-2025 |

Escape hatch when a specific fresh version is genuinely needed:
`npm i --min-release-age 0 <pkg>@<v>` — after a Mode A check on exactly
that version.

## 5. Lockfiles, pinning, provenance

- The lockfile is the only record of what actually ran — commit it, and
  review its *diff* like code: new transitive deps, changed integrity
  hashes, and registry URL changes are all reviewable events.
- Loose ranges (`^`, `~`) + no cooldown = auto-upgrade into whatever was
  published minutes ago. Ranges are fine *with* a cooldown; without one,
  pin exact versions for direct deps.
- Emergency pin across the whole graph: npm `overrides` / pnpm
  `overrides` / Yarn `resolutions`, then regenerate the lockfile.
- npm provenance (Sigstore attestations) binds a package to the CI run
  that built it — verify with `npm audit signatures`. Raises the bar on
  build-pipeline compromise; does nothing against stolen maintainer
  credentials (axios 2026 was fully "legitimately" signed-in).

## 6. Incident response

When a dependency in use is reported compromised:

1. **Stop the bleeding**: freeze installs/CI; pin the last-known-good
   version via `overrides`/`resolutions` everywhere in the graph.
2. **Determine exposure**: did the malicious version actually install
   here? (lockfile history, `npm ls <pkg>`, CI logs, install timestamps
   vs the incident window).
3. **If it ran, assume credential theft** — the dominant 2024–26 payload:
   rotate npm/PyPI tokens, cloud keys, `GITHUB_TOKEN`-adjacent secrets on
   any machine/CI that installed it; check for exfil artifacts
   (unexpected public repos, new workflow files, odd outbound calls).
4. **Clean**: purge caches (`npm cache clean --force`), reinstall from
   the pinned lockfile, rebuild CI images.
5. **Record it** (repo docs/ADR): affected versions, exposure verdict,
   rotations done — future audits start from facts, not memory.

## 7. Known limits

- **Advisory lag**: OSV/GHSA record incidents after detection. A clean
  OSV result on a version published 40 minutes ago means "nothing known
  yet". Cooldown exists precisely for this gap.
- **Script inspection misses Miasma-class vectors** (install-time exec
  without lifecycle scripts) and `--ignore-scripts` doesn't stop them
  either; it also breaks legitimate native builds.
- **Registry metadata is attacker-writable** (starjacking): repo links
  and READMEs are claims, not evidence.
- These checks vet *published artifacts*; they can't see a compromised
  build pipeline before the first advisory (provenance verification
  partially covers this).
