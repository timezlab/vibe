---
paths:
  - "**/*.py"
  - "**/requirements*.txt"
  - "**/pyproject.toml"
---

# Security — Python

Extends [common/security.md](../common/security.md) — read that first;
this file adds PyPI-ecosystem and Python-runtime specifics and wins where
they conflict.

## PyPI supply chain

- pip has no native release-age cooldown — enforce recency manually
  (`https://pypi.org/pypi/<name>/json` shows upload times; the
  `security-audit` skill's check script automates it) or via
  Renovate/Dependabot cooldown.
- `pip-audit` covers CVEs; add `--vulnerability-service=osv` to inherit
  OSV's malware (`MAL-`) coverage.
- Pin with a lockfile (`uv.lock`, `poetry.lock`, hash-pinned
  requirements); a bare `requirements.txt` of ranges re-resolves on every
  install.

## Code-executing formats

- `pickle.loads`, `yaml.load` (without `SafeLoader`), and `eval`/`exec`
  on external data are remote code execution by design — use `json`,
  `yaml.safe_load`, `ast.literal_eval`.
- XML from outside: parse with defusedxml or entity resolution disabled
  (XXE).

## Injection sinks

- `subprocess` with `shell=True` on external data → list args with
  `shell=False`.
- SQL via f-string/`.format()`/`%` → parameterized queries or the ORM.
- Django/DRF: explicit `fields=` allow-lists on forms/serializers —
  `**request.data` into a model is mass assignment.

## Paths and randomness

- Contain user paths: `Path(base, name).resolve()` then
  `.is_relative_to(base)` before I/O; validate archive entry paths before
  extraction.
- The `random` module never produces secrets — use the `secrets` module.
