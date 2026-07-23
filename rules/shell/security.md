---
paths:
  - "**/*.sh"
  - "**/*.bash"
---

# Security — shell/Bash

Extends [common/security.md](../common/security.md) — read that first;
this file adds shell-runtime specifics and wins where they conflict. Shell
runs everything it can reach: the whole language is a command sink, so the
boundary between data and code is thinner here than anywhere else.

## Injection is the default failure

- Never interpolate external data (arguments, env, file contents, command
  output) into a command string that gets re-parsed by the shell —
  `eval "$input"`, `bash -c "run $input"`, and building a command in a
  variable are all remote code execution when the input is hostile.
- Pass data as explicit positional arguments (`cmd -- "$file"`), not baked
  into a string. Terminate option parsing with `--` before user-controlled
  values so a filename like `--foo` isn't read as a flag.
- Quote every expansion (see coding-style) — an unquoted `$var` in a
  command is both a correctness bug and an injection vector.

## Untrusted input and files

- Validate that a path stays inside its intended directory before acting
  on it; a `../` in externally-supplied input escapes the base (path
  traversal), same rule as everywhere else.
- Set a restrictive `umask` (e.g. `umask 077`) before writing files that
  may hold secrets, and prefer `mktemp` over predictable `/tmp/$$` names —
  a predictable temp path is a symlink-attack target.

## Secrets and the network

- Keep secrets out of the command line: arguments are visible in `ps` and
  shell history. Pass them via environment or a file, and never `echo` a
  secret into a log.
- Never pipe the network straight into an interpreter (`curl … | sh`) —
  download, inspect, then run (common rule; it bites hardest in shell,
  where it's the idiomatic install one-liner).
- Check exit codes on security-relevant steps; with `set -e` a failed
  `gpg --verify` or checksum aborts, but a step inside a pipeline or `||`
  can still pass unnoticed — verify the verification actually ran.
