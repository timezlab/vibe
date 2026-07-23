# Rules

Always-on rule packs: short, normative constraints an agent follows in
every session — the "what". Deep guidance — the "how" — lives in skills,
loaded on demand (for these packs: the `coding-style`, `security-audit`,
and `debugging` skills). Rules stay thin because every always-loaded line
competes with
the task's own context. Rules are also only *context* — deterministic
enforcement of the security rules lives in `hooks/security/`.

## Layout and precedence

```
rules/
├── common/       # language-agnostic; loads unconditionally
├── typescript/   # extends common; loads for **/*.ts(x) and friends
├── python/       # extends common; loads for **/*.py
└── shell/        # extends common; loads for **/*.sh, **/*.bash
```

Topics per pack: `coding-style` (how code reads), `security` (what's
safe), and `agent-behavior` (how the agent acts — scope, honesty,
convention-following). `agent-behavior` is common-only: conduct doesn't
vary by language, so there's no per-language override to write.

- Language packs open with an "extends" line and only add or override.
  Where a language file conflicts with common, the language file wins —
  idiomatic exceptions beat generic defaults.
- Path scoping uses Claude Code rule frontmatter: a `paths:` glob list; a
  rule file without `paths:` loads always.

## How they load

- **This repo**: `.claude/rules` is a symlink here — Claude Code discovers
  project rules recursively.
- **Other repos / user scope**: copy whole packs
  (`cp -r rules/common rules/typescript ~/.claude/rules/vibe/`) — packs
  cross-reference by relative path, so copy directories, don't flatten
  files together. Claude Code plugins cannot distribute rules
  ([ADR 0005](../docs/decisions/0005-use-a-claude-compatible-plugin-layout.md)),
  so a copy step is required on every distribution path; the planned
  `vibe sync` owns this plus per-platform transforms (e.g. Cursor `.mdc`
  with `alwaysApply`/`globs`).

## Adding a pack

For a new *language* pack, mirror the `common/` filenames it needs to
extend (`coding-style.md`, `security.md`), open with the extends line, keep
each file under ~100 lines, and give every rule its why — a bare
prohibition teaches nothing and gets ignored. A new *topic* (like
`agent-behavior`) is a common-only file unless the constraint genuinely
differs by language. Format decision:
[ADR 0007](../docs/decisions/0007-adopt-claude-native-rule-packs.md);
security layering: [ADR 0008](../docs/decisions/0008-adopt-a-layered-security-harness.md).
