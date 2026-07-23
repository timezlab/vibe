# Vulnerability classes — what to hunt and how to confirm

Read this during change review (Mode B) and full audit (Mode C). Grep
patterns *locate candidates*; a finding exists only when untrusted data
demonstrably reaches the sink through the actual code path.

Contents:
1. Current canon (2025 editions)
2. Class table — pattern, grep, CWE
3. Language hot spots
4. LLM-era classes
5. Where generated code fails most

## 1. Current canon

OWASP Top 10:2025 — A01 Broken Access Control (now absorbs SSRF) · A02
Security Misconfiguration · A03 Software Supply Chain Failures (new —
covered by [supply-chain.md](supply-chain.md)) · A04 Cryptographic
Failures · A05 Injection · A06 Insecure Design · A07 Authentication
Failures · A08 Software/Data Integrity Failures · A09 Security Logging &
Alerting Failures · A10 Mishandling of Exceptional Conditions (new:
error-handling and logic bugs).

CWE Top 25 (2025) leads with XSS(79), SQLi(89), CSRF(352), Missing
Authorization(862) — access-control weaknesses (862/863/284/639) are the
fastest risers. Reviews that only hunt injection miss the trend: **check
authorization on every changed endpoint**.

## 2. Class table

| Class | Vulnerable shape | Grep for | CWE |
|---|---|---|---|
| SQL injection | string-built query reaches `execute`/`query` | `execute(f"`, `.query(\`…${`, `+ userInput` near SQL verbs | 89 |
| Command injection | external data in a shell string | `shell=True`, `child_process.exec(`, `os.system(` | 78 |
| Template injection (SSTI) | user input compiled as template | `render_template_string(`, template engines fed request data | 94 |
| XSS | untrusted data → HTML/DOM unencoded | `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `\|safe` | 79 |
| SSRF | server fetches user-supplied URL | `fetch(`/`requests.get(` on request-derived URL, no host allow-list | 918 |
| Path traversal | user path in file I/O uncontained | `path.join(dir, req…)`, `open(base +`, missing resolve+prefix check | 22 |
| Insecure deserialization | code-executing format on untrusted bytes | `pickle.loads(`, `yaml.load(` sans SafeLoader, `unserialize(` | 502 |
| IDOR / BOLA | resource fetched by ID, no ownership filter | handlers where the only filter is the ID; missing `owner_id`/tenant clause | 639/862 |
| Missing function-level authz | endpoint lacks the check its siblings have | diff the auth decorator/middleware across sibling routes | 862/863 |
| JWT misconfig | signature/algorithm not enforced | `verify=False`, `algorithms=["none"]`, unpinned `algorithms` | 347 |
| Hardcoded secrets | live credential literal in source | `AKIA[0-9A-Z]{16}`, `ghp_\w{36}`, `AIza[\w-]{35}`, `-----BEGIN…PRIVATE KEY`, `password\s*=\s*["']` | 798 |
| Weak crypto | broken algo/PRNG for security | `md5(`, `sha1(` (security context), `AES/ECB`, `Math.random()`/`random.` for tokens | 327/330 |
| Race / TOCTOU | check-then-act without atomicity | exists-check then write; balance-check then debit, no lock/transaction | 367 |
| Prototype pollution | unguarded deep-merge of external JSON | `__proto__`, `constructor.prototype` reachable in merge path | 1321 |
| Zip Slip | archive entries extracted uncontained | `extractall(`, `path.join(dest, entry…)` unchecked | 22 |
| Mass assignment | whole request body bound to model | `**request.data`, `Object.assign(user, req.body)` | 915 |
| Open redirect | redirect target from raw param | `redirect(request.args.get(`, `res.redirect(req.query.` | 601 |
| XXE | XML parser resolves external entities | XML parse without secure-processing/`resolve_entities=False` | 611 |
| Unrestricted upload | type/size/path of uploads unvalidated | upload handlers writing original filenames; missing content-type/extension allow-list | 434 |

Note the review-policy interaction: several greppable classes (ReDoS,
open redirect, prototype pollution) are **excluded or
high-confidence-only** by the default FP policy — locate them, then check
[false-positives.md](false-positives.md) before reporting.

## 3. Language hot spots

**TypeScript/Node** — prototype pollution in merge utilities; SSRF in
webhook/preview/fetch-URL features; `child_process` interpolation; unsafe
HTML sinks behind "sanitize later" comments; Zip Slip in upload handling
(`adm-zip`, `unzipper`); `Math.random()` tokens; JWT libs accepting the
header's algorithm.

**Python** — `pickle`/`yaml.load` on anything external; f-string SQL;
`subprocess(shell=True)`; Django/DRF mass assignment (missing `fields=`);
SSRF via `requests.get` on user URLs; XXE via stdlib XML defaults;
`tarfile.extractall` without member validation.

## 4. LLM-era classes

For applications *using* LLMs (OWASP LLM Top 10:2025):

- **Prompt injection (LLM01)** — untrusted content steering the model.
  In code review terms: user/web/tool content concatenated into prompts
  that also carry instructions, with no separation or output constraint.
- **Improper output handling (LLM05)** — model output treated as trusted:
  rendered as HTML (XSS), executed (`eval`, shell), or interpolated into
  SQL. Model output is untrusted input like any other.
- **Excessive agency (LLM06)** — agent/tool wiring where the model can
  reach data or actions beyond the task's need: broad DB creds handed to
  a chat feature, shell tools exposed to summarizers. Flag scope, not
  just sinks.

For the agent harness itself (hooks, MCP, skills) →
[agent-harness.md](agent-harness.md).

## 5. Where generated code fails most

Benchmark evidence (Veracode 2025–26 GenAI reports; adversarial 4-CWE
benchmark, so a worst-case measure, not an organic rate): generators now
handle SQLi and crypto choices fairly well but persistently fail
**taint-tracking classes** — XSS and log/output injection defense failed
~85% regardless of model. Calibrate review attention accordingly: the
data-flow classes (XSS, output injection, SSRF) deserve tracing effort
even when the code "looks idiomatic", and doubly so in diffs authored by
coding agents.
