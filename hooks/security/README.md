# Security hooks

The enforcement layer of the vibe security harness. Rules and skills are
context — the model can be steered around them; hooks and
`permissions.deny` are the only mechanisms the client enforces regardless
of what the model decides. This pack pairs with `rules/*/security.md`
(the always-on "what") and `skills/security-audit/` (the on-demand
"how"): guidance persuades, these scripts block.

| Script | Event / matcher | Blocks | Decision |
|---|---|---|---|
| `block-dangerous-commands.py` | PreToolUse / `Bash` | recursive force-deletes of critical paths, `curl \| sh`, force-push to protected branches, `chmod 777`, block-device writes, shell reads/exfil of secret files | deny |
| `protect-secrets.py` | PreToolUse / `Read\|Edit\|Write\|NotebookEdit` | file-tool access to secret paths (`.env`, keys, credential stores) and Write/Edit payloads matching live credential shapes (AWS/GitHub/Google/Slack/GitLab/npm/private-key) | deny |
| `dependency-gate.py` | PreToolUse / `Bash` | installing package versions with OSV `MAL-` malware advisories (deny); versions younger than the cooldown, unknown names, or unverifiable installs (ask) | deny / ask |

## Wiring (Claude Code)

Copy the scripts (or the whole directory), then add to
`.claude/settings.json` — project-level so the whole team inherits it:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/hooks/security/block-dangerous-commands.py\"" },
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/hooks/security/dependency-gate.py\"" }
        ]
      },
      {
        "matcher": "Read|Edit|Write|NotebookEdit",
        "hooks": [
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/hooks/security/protect-secrets.py\"" }
        ]
      }
    ]
  }
}
```

Each script is independent — wire the subset you want. Requirements:
`python3` (3.9+) on PATH; stdlib only, no installs. Other harnesses
(Cursor, Codex, …) need per-platform event adapters — owned by the
planned `vibe sync` ([ARCHITECTURE.md](../../ARCHITECTURE.md)); until
then these are Claude Code-native.

## Design decisions

- **Fail closed.** A guard that crashes emits *deny* (the two blockers)
  or *ask* (the gate) with the error attached — never a silent allow.
  Most community hooks `exit 0` on their own exceptions, which turns
  every hook bug into a silent security hole. Trade-off accepted: a
  broken guard is loud and annoying until fixed or removed; that is the
  point.
- **Deny messages never echo secrets.** Pattern class and path only.
- **Ask, not deny, for uncertainty.** The dependency gate hard-denies
  only on a positive malware advisory; cooldown violations, unknown
  names, and network failures escalate to the human instead of bricking
  installs.
- **CVEs don't block installs.** Routine CVE triage belongs to audit
  tooling (`osv-scanner`, Mode A of the security-audit skill); a gate
  that blocks on every CVE gets disabled within a week. CVE counts
  surface as context.
- **Placeholders stay writable.** `.env.example`-style templates and
  tokens containing `EXAMPLE`/`PLACEHOLDER`/`CHANGEME` pass the secret
  scan — docs and templates should use exactly those.

## Limits — read before trusting

- These are **tripwires, not a sandbox**. Regex guards catch the
  straightforward dangerous shapes; a determined bypass (obfuscation,
  base64, writing a script then running it) exists for all of them. Hard
  guarantees need `permissions.deny` and OS-level sandboxing — use hooks
  as the fast layer, not the only layer.
- `protect-secrets.py` guards the file tools; reading secrets via
  `Grep` or other paths isn't covered (the Bash-side shapes are covered
  by `block-dangerous-commands.py`).
- The dependency gate parses common install-command shapes (npm/pnpm/
  yarn/bun add|install, pip/uv install) for npm + PyPI; exotic
  invocations, other ecosystems, and `-r requirements.txt` bulk installs
  pass through — sweep those with `osv-scanner` instead. Checks the
  first `VIBE_DEP_GATE_MAX_PKGS` (default 5) specs and *asks* about the
  remainder rather than silently truncating. It matches the install verb
  anywhere in the command, so an install phrase quoted inside an `echo`/
  help string (`echo "run pip install foo"`) triggers a spurious *ask* —
  harmless (never a deny), but a known over-catch; distinguishing it needs
  a real shell parser.
- Latency: the two Bash guards add ~50–100 ms per Bash call; the
  dependency gate adds network time (~1–3 s) only on install commands.

## Knobs

| Env var | Default | Meaning |
|---|---|---|
| `VIBE_MIN_RELEASE_AGE_HOURS` | `24` | dependency-gate cooldown window |
| `VIBE_DEP_GATE_MAX_PKGS` | `5` | max specs vetted per install command |

## Testing a change

Every script change gets exercised with crafted stdin before shipping:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' \
  | python3 hooks/security/block-dangerous-commands.py   # expect deny JSON
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf node_modules"}}' \
  | python3 hooks/security/block-dangerous-commands.py   # expect silence
echo '{"tool_name":"Read","tool_input":{"file_path":"/app/.env"}}' \
  | python3 hooks/security/protect-secrets.py            # expect deny JSON
echo '{"tool_name":"Bash","tool_input":{"command":"npm install left-pad"}}' \
  | python3 hooks/security/dependency-gate.py            # network: pass/ask
```
