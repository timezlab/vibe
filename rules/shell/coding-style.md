---
paths:
  - "**/*.sh"
  - "**/*.bash"
  - "**/.bashrc"
  - "**/.zshrc"
  - "**/.profile"
---

# Coding style — shell/Bash

Extends [common/coding-style.md](../common/coding-style.md) — read that
first; this file adds shell specifics and wins where they conflict. Shell
is write-once-read-never by reputation; these rules exist because the
language fails silently by default, so readability *is* correctness here.

## Strict mode and safety

- Start executable scripts with `set -euo pipefail` — without it a failed
  command, an unset variable, or a broken pipe is swallowed and the script
  charges on with corrupt state. This is the single highest-value line in
  a shell script.
- Set `IFS=$'\n\t'` when word-splitting matters; the default space-tab-
  newline splits on spaces inside filenames.

## Quoting and expansion

- Quote every expansion: `"$var"`, `"${arr[@]}"`, `"$(cmd)"`. An unquoted
  expansion word-splits and glob-expands — the cause of most "worked in
  test, broke on a path with a space" shell bugs.
- Prefer `"${var}"` braces at ambiguous boundaries and `${var:?message}`
  to fail loudly on a required-but-empty variable.

## Constructs

- `[[ … ]]` over `[ … ]` for tests (no word-splitting surprises, supports
  `&&`/`||`/`=~`); `$(( … ))` for arithmetic.
- `$(cmd)` over backticks — nestable and readable.
- Loop over arrays (`for f in "${files[@]}"`), never over unquoted
  `$(ls)` or a string of names — filenames with spaces or newlines break
  the latter.
- Functions with `local` variables over globals; a bare assignment in a
  function leaks to global scope.

## Enforcement

- Run **ShellCheck** — it catches the quoting, `set -e`, and word-split
  classes above mechanically; a shell rule ShellCheck enforces will not
  drift. Treat its warnings as errors unless a line carries a
  `# shellcheck disable=SCxxxx` with a stated reason.
- Reach for a real language (Python) once a script grows conditionals,
  data structures, or arg parsing beyond a few flags — Bash past ~100
  lines is usually the wrong tool, not a badge.
