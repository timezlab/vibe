# Where each platform loads harness content

Reference for `vibe sync` adapter work and for placing VIBE's canonical
`skills/`, `agents/`, and (planned) `rules/`, `hooks/`, `commands/` content.
Covers six content dimensions — root instructions, skills, rules, subagents,
hooks, commands — across nine platforms. Facts verified against official
platform docs on **2026-07-23** (deep-read unless marked otherwise; gaps and
confidence noted inline).

> **Drift-prone.** Every dimension on every platform is actively evolving —
> one platform in this table (Windsurf) rebranded mid-quarter. Re-verify
> against the linked docs before building an adapter on any row below.

## Summary matrix

Project-scope paths only; see per-platform sections for user/global scope,
precedence, and format.

| Platform | Root instructions | Skills | Rules | Subagents/agents | Hooks | Commands |
|---|---|---|---|---|---|---|
| Claude Code | `CLAUDE.md` (not `AGENTS.md`) | `.claude/skills/*/SKILL.md` | `.claude/rules/*.md` | `.claude/agents/*.md` | `.claude/settings.json` → `hooks` | `.claude/skills/` (`.claude/commands/*.md` legacy) |
| Codex | `AGENTS.md` (concatenated root→cwd) | `.agents/skills` | *(none — folded into AGENTS.md)* | `.codex/agents/*.toml` | `.codex/hooks.json` / `config.toml` `[hooks]` | `~/.codex/prompts/*.md` (user-only, deprecated) |
| Gemini CLI | `GEMINI.md` (+ configurable `AGENTS.md`) | `.gemini/skills/` / `.agents/skills/` (alias wins) | *(none — policy engine ≠ rules)* | `.gemini/agents/*.md` | `.gemini/settings.json` → `hooks` | `.gemini/commands/*.toml` |
| Cursor | `.cursor/rules/*.mdc` + `AGENTS.md`/`CLAUDE.md` read | `.cursor/skills/` / `.agents/skills/` (+ cross-reads `.claude/`, `.codex/`) | `.cursor/rules/*.mdc` | `.cursor/agents/` (+ cross-reads `.claude/agents/`, `.codex/agents/`) | `.cursor/hooks.json` + `.cursor/hooks/` | `.cursor/commands/*.md` |
| Windsurf → **Devin Desktop** (rebranded Jun 2026) | `.windsurf/rules/*.md` → `.devin/rules/*.md` (+ `AGENTS.md`) | `.windsurf/skills/` / `.agents/skills/` | `.windsurf/rules/*.md` | *(none — built-in dynamic subagents only)* | `.windsurf/hooks.json` | `.windsurf/workflows/*.md` |
| Cline | `.clinerules` or `.clinerules/*.md` (+ `AGENTS.md`) | `.cline/skills/` (+ `.clinerules/skills/`, cross-reads `.claude/skills/`) | `.clinerules/*.md` | *(none — built-in dynamic subagents only)* | `.clinerules/hooks/` (macOS/Linux only) | `.clinerules/workflows/*.md` |
| Kiro | `.kiro/steering/*.md` (+ `AGENTS.md`) | `.kiro/skills/*/SKILL.md` | *(none — steering `inclusion:` modes)* | `.kiro/agents/*.md` | `.kiro/hooks/*.json` (project-only) | `.kiro/prompts/` (CLI, lightly documented) |
| Antigravity | `~/.gemini/GEMINI.md` (+ `AGENTS.md`, medium confidence) | `.agents/skills/*/SKILL.md` | `.agents/rules/` | `.agents/agents/*/agent.md` | `.agents/hooks.json` | *(none found — Workflows serve this role)* |
| GitHub Copilot | `.github/copilot-instructions.md` + `AGENTS.md` (nested wins) | `.github/skills` / `.claude/skills` / `.agents/skills` | `.github/instructions/*.instructions.md` (`applyTo` glob) | `.github/agents/*.agent.md` (legacy `.github/chatmodes/*.chatmode.md`) | `.github/hooks/*.json` (cloud/CLI only) | `.github/prompts/*.prompt.md` |

## The Agent Skills open standard (agentskills.io)

Unlike every other dimension, **skills converge on one cross-vendor
directory**: `.agents/skills/`, defined by the independent
[Agent Skills specification](https://agentskills.io/specification)
(Apache-2.0/CC-BY-4.0, `agentskills/agentskills` on GitHub, validated by the
`skills-ref` package this repo already uses). Every platform surveyed here
either reads `.agents/skills/` directly or aliases it with precedence over
its native path:

- **Codex**: `.agents/skills` (cwd→root) is the *primary* path, no separate
  native directory.
- **Gemini CLI, Antigravity, Cursor, Windsurf, GitHub Copilot**: `.agents/skills/`
  is an alias that **wins** over the platform's native `<tool>/skills/` on
  conflict.
- **Claude Code, Kiro**: native path (`.claude/skills/`, `.kiro/skills/`) *is*
  the standard's reference implementation — no separate `.agents/skills/` read.
- **Cline**: structurally compatible (folder + `SKILL.md`) but no official doc
  states standard conformance — treat as unconfirmed.

**`SKILL.md` format** (near-universal): a directory per skill containing
`SKILL.md` — YAML frontmatter with required `name` + `description` (the
`description` drives auto-invocation — it must state *when* to use the
skill), optional invocation-control fields (e.g. `paths`,
`disable-model-invocation`, `metadata`, license/compatibility tags vary by
platform) — followed by a Markdown body that is the skill's instructions.
Optional sibling folders: `scripts/`, `references/`, `assets/`.

This is why VIBE's `.agents/skills` symlink already covers Codex and Gemini
CLI (and would cover Cursor, Windsurf, Antigravity, Copilot) with zero
adapter work — see [ADR 0004](../decisions/0004-compile-canonical-content-through-adapters.md).
**No equivalent standard exists for subagents** — see below.

## Per-platform detail

### Claude Code

Source: [Memory](https://code.claude.com/docs/en/memory) ·
[Skills](https://code.claude.com/docs/en/skills) ·
[Subagents](https://code.claude.com/docs/en/sub-agents) ·
[Hooks](https://code.claude.com/docs/en/hooks) ·
[MCP](https://code.claude.com/docs/en/mcp)

- **Root instructions**: `./CLAUDE.md` or `./.claude/CLAUDE.md` (project),
  `./CLAUDE.local.md` (personal, gitignored), `~/.claude/CLAUDE.md` (user),
  `/etc/claude-code/CLAUDE.md` (org-managed, loads first). **Does not read
  `AGENTS.md` natively** — docs state this explicitly; the supported
  workaround is a `@AGENTS.md` import line or a `CLAUDE.md → AGENTS.md`
  symlink (this repo uses the import line — [CLAUDE.md](../../CLAUDE.md)).
  Walks cwd→repo-root, **concatenating** (not overriding); supports
  `@path` imports (max depth 4).
- **Skills**: `.claude/skills/<name>/SKILL.md` (project, nested subdirs
  auto-discovered) / `~/.claude/skills/<name>/SKILL.md` (user) / plugin
  `<plugin>/skills/<name>/SKILL.md`. Frontmatter: `name`, `description`
  required. Precedence: enterprise > personal > project > bundled.
- **Rules**: `.claude/rules/*.md` (project, recursive) /
  `~/.claude/rules/*.md` (user). Optional frontmatter `paths:` glob list for
  path-scoping; unscoped rules load unconditionally alongside CLAUDE.md.
- **Subagents**: `.claude/agents/*.md` (project) / `~/.claude/agents/*.md`
  (user). Frontmatter: `name` + `description` required; optional `tools`,
  `disallowedTools`, `model`, `permissionMode`, `mcpServers`, `hooks`,
  `maxTurns`, **`skills`** (preloads full skill content into context —
  VIBE's agent→skill link, see [ADR 0006](../decisions/0006-predefine-research-agents-by-modality.md)),
  `initialPrompt`, `memory`, `effort`, `background`, `isolation`, `color`.
  Body = the subagent's entire system prompt (no inherited main prompt).
- **Hooks**: not a separate file type — nested inside `~/.claude/settings.json`
  (user) / `.claude/settings.json` (project) / `.claude/settings.local.json`
  (local, gitignored) as `hooks.<EventName>[].hooks[]` (JSON).
- **Commands**: current form is a skill (`.claude/skills/<name>/SKILL.md`,
  invoked `/<name>`); legacy `.claude/commands/*.md` / `~/.claude/commands/*.md`
  still supported — skill wins on name collision.
- Bonus MCP: `.mcp.json` (project) / `~/.claude.json` (user).

### Codex

Source: [AGENTS.md](https://developers.openai.com/codex/guides/agents-md) ·
[Skills](https://developers.openai.com/codex/skills) ·
[Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) ·
[Hooks](https://developers.openai.com/codex/hooks) ·
[Custom Prompts](https://developers.openai.com/codex/custom-prompts) ·
[MCP](https://developers.openai.com/codex/mcp)

- **Root instructions**: `AGENTS.md` / `AGENTS.override.md` in every
  directory from git root to cwd, `~/.codex/AGENTS.md` (user,
  `CODEX_HOME`-relative). **Concatenates** every file found root→cwd
  (deeper wins on conflict via ordering, not override), capped at 32 KiB
  (`project_doc_max_bytes`).
- **Skills**: `.agents/skills` (cwd→root), `$HOME/.agents/skills` (user),
  `/etc/codex/skills` (admin), plus bundled system skills. This *is* the
  primary path — no separate native `.codex/skills`.
- **Rules**: no distinct mechanism — AGENTS.md's hierarchy is the only
  supplementary-instructions surface.
- **Subagents**: `.codex/agents/*.toml` (project) / `~/.codex/agents/*.toml`
  (user) — **the only TOML format** in this survey. Required: `name`,
  `description`, `developer_instructions`. Optional: `model`,
  `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, `skills.config`.
  Global `[agents]` block in `config.toml` sets concurrency/default-model
  cascades.
- **Hooks**: `.codex/hooks.json` or `[hooks]` table in `.codex/config.toml`
  (project, requires trust) / `~/.codex/hooks.json` (user). Layers are
  additive. Events: `SessionStart`, `SubagentStart`, `PreToolUse`,
  `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`,
  `UserPromptSubmit`, `SubagentStop`, `Stop`.
- **Commands**: `~/.codex/prompts/*.md` (user-only, flat, no project scope)
  — **officially deprecated** in favor of Skills.
- Bonus MCP: `~/.codex/config.toml` (user) / `.codex/config.toml` (project,
  trusted-only), `[mcp_servers.<name>]`.

### Gemini CLI

Source: [GEMINI.md](https://geminicli.com/docs/cli/gemini-md/) ·
[Skills](https://geminicli.com/docs/cli/skills/) ·
[Policy engine](https://geminicli.com/docs/reference/policy-engine/) ·
[Subagents](https://geminicli.com/docs/core/subagents/) ·
[Hooks](https://geminicli.com/docs/hooks/) ·
[Commands](https://geminicli.com/docs/reference/commands/) ·
[MCP](https://geminicli.com/docs/tools/mcp-server/)

- **Root instructions**: `GEMINI.md` (cwd + parents to `.git` root, plus
  subdirs), `~/.gemini/GEMINI.md` (user). `AGENTS.md` support is
  **opt-in via `settings.json` → `context.fileName`** (string or array,
  e.g. `["AGENTS.md","GEMINI.md"]`) — not read by default. Supports
  `@file.md` imports.
- **Skills**: precedence low→high: built-in → extension → user
  (`~/.gemini/skills/` or `~/.agents/skills/`) → workspace
  (`.gemini/skills/` or `.agents/skills/`); within each tier `.agents/skills/`
  wins.
- **Rules**: no distinct dimension — the policy engine
  (`.gemini/policies/*.toml`) governs tool-execution permissions, not
  coding-style guidelines; not equivalent to "rules" elsewhere in this doc.
- **Subagents**: `.gemini/agents/*.md` (project) / `~/.gemini/agents/*.md`
  (user), Markdown + YAML. Required: `name` (lowercase slug, used as tool
  name), `description`. Optional: `kind` (`local`/`remote`), `tools`
  (wildcards `*`, `mcp_*`), `mcpServers` (inline), `model`, `temperature`,
  `max_turns`, `timeout_mins`. Extensions can bundle agents; separate
  remote-agent (`kind: remote`) docs exist.
- **Hooks**: inside `settings.json` (`.gemini/settings.json` project,
  `~/.gemini/settings.json` user, merged with extensions), not standalone
  files. Events: `SessionStart/End`, `BeforeAgent/AfterAgent`,
  `BeforeModel/AfterModel`, `BeforeTool/AfterTool`, `Notification`.
- **Commands**: `.gemini/commands/*.toml` (project) / `~/.gemini/commands/*.toml`
  (user). Required key `prompt`; subdirs become `/namespace:command`.
- Bonus MCP: `mcpServers` key inside `settings.json` at either scope.

### Cursor

Source: [Rules](https://cursor.com/docs/context/rules) ·
[Skills](https://cursor.com/docs/context/skills) ·
[Subagents](https://cursor.com/docs/subagents.md) ·
[Slash commands](https://cursor.com/docs/cli/reference/slash-commands) ·
[MCP](https://cursor.com/docs/mcp)

- **Root instructions**: legacy `.cursorrules` (deprecated, still read);
  current system is `.cursor/rules/*.mdc` (see Rules below). **Reads
  `AGENTS.md`** in project root and subdirectories (more-specific wins);
  CLI also reads `CLAUDE.md`. No documented user/global `AGENTS.md` path.
- **Skills**: `.cursor/skills/` and `.agents/skills/` (project) /
  `~/.cursor/skills/` and `~/.agents/skills/` (user); also cross-reads
  `.claude/skills/` and `.codex/skills/` at both scopes. Frontmatter:
  `name`, `description` required; optional `paths`,
  `disable-model-invocation`, `metadata`.
- **Rules**: `.cursor/rules/*.mdc` only (plain `.md` ignored except
  `AGENTS.md`). Frontmatter drives four modes: Always Apply, Apply
  Intelligently (agent judges via `description`), Apply to Specific Files
  (glob), Apply Manually (`@`-mention). User Rules live in editor
  Settings, not a plain file. Precedence: Team (dashboard) > Project >
  User.
- **Subagents**: `.cursor/agents/` (project) / `~/.cursor/agents/` (user)
  — **and `.claude/agents/` + `.codex/agents/` (and their `~` equivalents)
  are explicitly documented compatibility paths**, confirmed directly on
  cursor.com/docs/subagents.md (not just changelog silence — resolves the
  prior draft's "plausible, not corroborated" caveat to **confirmed**).
  `.cursor/` wins on name conflict. Frontmatter: `name`, `description`
  required; optional `model` (`inherit` or explicit ID), `readonly`,
  `is_background`.
- **Hooks**: `.cursor/hooks.json` + `.cursor/hooks/` (project) /
  `~/.cursor/hooks.json` + `~/.cursor/hooks/` (user). JSON
  `{version, hooks: {<event>: [...]}}`. Docs also claim "Claude Code hooks
  compatibility" (2.4 changelog) — unverified beyond that mention.
- **Commands**: `.cursor/commands/*.md` (project) / `~/.cursor/commands/*.md`
  (user/global), freeform Markdown prompt templates.
- Bonus MCP: `.cursor/mcp.json` (project) / `~/.cursor/mcp.json` (user).

### Windsurf → Devin Desktop

**Rebranded by Cognition to "Devin Desktop" on 2026-06-02**;
`docs.windsurf.com` now 307-redirects to `docs.devin.ai`. Cascade (the
agent) is being succeeded by "Devin Local"; legacy Cascade config was
available through 2026-07-01. Legacy `.windsurf/*` paths still read for
backward compatibility; current docs describe `.devin/*` as the forward
path — **re-verify before relying on either.**

Source: [Memories](https://docs.devin.ai/desktop/cascade/memories) ·
[Skills](https://docs.devin.ai/desktop/cascade/skills) ·
[Hooks](https://docs.devin.ai/desktop/cascade/hooks) ·
[Workflows](https://docs.devin.ai/windsurf/plugins/cascade/workflows) ·
[MCP](https://docs.windsurf.com/windsurf/cascade/mcp) ·
[rebrand announcement](https://devin.ai/blog/windsurf-is-now-devin-desktop)

- **Root instructions**: `.windsurfrules` (legacy) → `.windsurf/rules/*.md`
  → `.devin/rules/*.md` (current preferred), `~/.codeium/windsurf/memories/global_rules.md`
  (user). **Reads `AGENTS.md`/`agents.md`** through the same rules engine;
  can also import `.cursor/rules` (`.mdc`).
- **Skills**: `.windsurf/skills/<name>/SKILL.md` (project), also discovers
  `.agents/skills/` and (with a compat flag) `.claude/skills/`. Global:
  `~/.agents/skills/`, `~/.claude/skills/` (compat), enterprise
  `~/.codeium/windsurf/skills/`.
- **Rules**: same as root instructions. Frontmatter `trigger:` —
  `always_on`, `model_decision` (description-gated), `glob`, `manual`.
  Limits: 12,000 chars/workspace file, 6,000/global file (single-source,
  not independently cross-verified).
- **Subagents**: **no user-authored persona-file directory found.** Devin
  Local natively spawns parallel subagents for task decomposition
  (architecture feature, not user-configurable); Agent Client Protocol
  (ACP) lets external agents (Codex, Claude Agent) run inside the editor
  instead.
- **Hooks**: `.windsurf/hooks.json` (project) / `~/.codeium/windsurf/hooks.json`
  (user) / enterprise system-level. JSON keyed by event
  (`pre_read_code`, `pre_write_code`, `pre_run_command`, `pre_mcp_tool_use`,
  `pre_user_prompt` blocking; `post_*` observational).
- **Commands**: `.windsurf/workflows/*.md` (project, walks to git root) /
  `~/.codeium/windsurf/global_workflows/` (user), invoked `/workflow-name`;
  workflows can call other workflows. 12,000 char/file limit.
- Bonus MCP: `~/.codeium/windsurf/mcp_config.json`.

### Cline

Source: [Cline Rules](https://docs.cline.bot/features/cline-rules) ·
[Skills](https://docs.cline.bot/customization/skills) ·
[Memory Bank](https://docs.cline.bot/best-practices/memory-bank) ·
[Subagents](https://docs.cline.bot/features/subagents) ·
[Hooks blog post](https://cline.bot/blog/cline-v3-36-hooks) ·
[Commands](https://docs.cline.bot/core-workflows/using-commands) ·
[MCP](https://docs.cline.bot/mcp/mcp-overview)

- **Root instructions**: `.clinerules` (single file) or `.clinerules/`
  (directory of `.md`/`.txt`, numeric-prefix ordering), `~/Documents/Cline/Rules`
  (user; `Documents\Cline\Rules` on Windows). **Auto-detects `AGENTS.md`**
  (project) and `~/.agents/AGENTS.md` (global), plus legacy
  `.cursorrules`/`.windsurfrules` cross-reads. All files individually
  toggleable in the Rules panel.
- **Skills**: `.cline/skills/` (recommended) / `.clinerules/skills/`
  (project), cross-reads `.claude/skills/`; `~/.cline/skills/` (user).
  Frontmatter: `name`, `description` required. Loaded on-demand
  (progressive disclosure). *Memory Bank* is a distinct
  documentation-methodology convention (`memory-bank/*.md`), not a skills
  loader.
- **Rules**: same as root instructions (`.clinerules/`); workspace wins on
  conflict with global.
- **Subagents**: **built-in/dynamic only — no user-defined file format.**
  Cline autonomously spawns read-only research subagents (no writes, no
  MCP, no browser); toggled via Settings only, no directory or persona file.
- **Hooks**: `.clinerules/hooks/` (project) / `~/Documents/Cline/Rules/Hooks/`
  (user). Executable scripts named exactly for the event
  (`PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `TaskStart`,
  `TaskResume`, `TaskCancel`), stdin/stdout JSON. **macOS/Linux only.**
- **Commands**: `.clinerules/workflows/*.md` (project) /
  `~/Documents/Cline/Workflows/` (user/global), invoked `/workflow-name`;
  project wins on collision.
- Bonus MCP: `cline_mcp_settings.json` under VS Code global storage.

### Kiro

Source: [Steering](https://kiro.dev/docs/steering/) ·
[Skills](https://kiro.dev/docs/skills/) ·
[Subagents (chat)](https://kiro.dev/docs/chat/subagents/) ·
[Subagents (CLI)](https://kiro.dev/docs/cli/custom-agents/) ·
[Hooks](https://kiro.dev/docs/hooks/) ·
[Slash commands](https://kiro.dev/docs/chat/slash-commands/) ·
[MCP](https://kiro.dev/docs/mcp/)

- **Root instructions**: `.kiro/steering/*.md` (project; foundation files
  `product.md`/`tech.md`/`structure.md` auto-generated), `~/.kiro/steering/*.md`
  (user, lower priority than workspace). **Reads a root `AGENTS.md`** (or
  one placed under `~/.kiro/steering/`) as always-included content — it does
  *not* get the `inclusion:` frontmatter modes native steering files get.
- **Skills**: `.kiro/skills/<name>/SKILL.md` (project) /
  `~/.kiro/skills/<name>/SKILL.md` (user), following agentskills.io.
  Auto-registers as `/skill-name`.
- **Rules**: no separate dimension — steering files' `inclusion:`
  frontmatter *is* the rules mechanism: `always` (default), `fileMatch` +
  `fileMatchPattern` (glob-gated), `manual` (`#steering-file-name` or slash
  command), `auto` + `description` (semantic-gated, also a slash command).
- **Subagents**: `.kiro/agents/*.md` (project) / `~/.kiro/agents/*.md`
  (user). Frontmatter: `name`, `description`, `tools`, `model`. Body =
  system prompt. Auto-triggers off `description` or invoked as `/name`.
- **Hooks**: `.kiro/hooks/*.json` — **project/workspace scope only, no
  documented global path.** JSON: `version`, `hooks[]` with `name`,
  trigger/event, file-match pattern, `action` (command or agent-prompt),
  `timeout`, `enabled`.
- **Commands**: skills/subagents auto-register as `/name`; CLI additionally
  has `.kiro/prompts/` reusable prompt templates (`/prompts create|edit|get|list|remove`)
  — lightly documented, IDE-side equivalent unclear.
- Bonus MCP: `.kiro/settings/mcp.json` (project) / `~/.kiro/settings/mcp.json`
  (user; workspace overrides).

### Antigravity

Newest, least-documented platform surveyed — several claims below are
single-source or medium-confidence; a linked Google forum bug report
suggests file-based custom agents are functionally immature.

Source: [Rules & Workflows](https://antigravity.google/docs/rules-workflows) ·
[Skills](https://antigravity.google/docs/skills) ·
[Agents CLI](https://antigravity.google/docs/cli/commands/agents) ·
[Subagents](https://antigravity.google/docs/subagents) ·
[Hooks](https://antigravity.google/docs/hooks) ·
[MCP](https://antigravity.google/docs/mcp) ·
[AGENTS.md/skills.md codelab](https://codelabs.developers.google.com/autonomous-ai-developer-pipelines-antigravity)

- **Root instructions**: `~/.gemini/GEMINI.md` (confirmed on primary docs
  page). `AGENTS.md` support is confirmed by a Google-authored codelab but
  **not** spelled out on the main rules-workflows doc page — treat
  precedence between `GEMINI.md`/`AGENTS.md` as unconfirmed (medium
  confidence).
- **Skills**: `.agents/skills/<name>/SKILL.md` (project; legacy
  `.agent/skills` also read) / `~/.gemini/config/skills/<name>/SKILL.md`
  (user) — explicit agentskills.io conformance (high confidence).
- **Rules**: `.agents/rules/` (project, legacy fallback `.agent/rules/`) /
  `~/.gemini/GEMINI.md` (user). Markdown, 12,000-char/file limit. Supports
  `@filename` cross-references.
- **Subagents**: `.agents/agents/<name>/agent.md` (project) /
  `~/.gemini/config/agents/<name>/agent.md` (user), Markdown + YAML
  frontmatter (`name`, `description`, system instructions), distinct from
  the built-in Manager/Worker (research/browser/self) subagents.
  Medium-high confidence — path confirmed, but see the immaturity caveat
  above.
- **Hooks**: `hooks.json` in `.agents/` (project) / `~/.gemini/config/`
  (user). Events: `PreToolUse`, `PostToolUse`, `PreInvocation`,
  `PostInvocation`, `Stop`.
- **Commands**: no documented user-authored slash-command file format —
  built-in CLI/IDE commands only; Workflows (under Rules) fill this role.
- Bonus MCP: `~/.gemini/config/mcp_config.json` (user) /
  `.agents/mcp_config.json` (project, overrides).

### GitHub Copilot

Covers coding agent (cloud), Copilot CLI, and VS Code agent mode together —
scope differs per sub-surface where noted.

Source: [Repository custom instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions) ·
[AGENTS.md support](https://github.blog/changelog/2025-08-28-copilot-coding-agent-now-supports-agents-md-custom-instructions/) ·
[Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) ·
[Custom agents (VS Code)](https://code.visualstudio.com/docs/agent-customization/custom-agents) ·
[Hooks](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/use-hooks) ·
[Prompt files](https://docs.github.com/en/copilot/tutorials/customization-library/prompt-files/your-first-prompt-file) ·
[MCP for CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers)

- **Root instructions**: `.github/copilot-instructions.md` (repo-wide) +
  `.github/instructions/*.instructions.md` (path-scoped, frontmatter
  `applyTo: <glob>`, optional `excludeAgent`). **Reads root `AGENTS.md`**,
  with nested `AGENTS.md` in subdirectories taking precedence for their
  scope (added 2025-08-28); also reads `CLAUDE.md`/`GEMINI.md` if present.
  User scope is settings-based (not a repo file); precedence personal >
  repository > organization.
- **Skills**: checked in order `.github/skills`, `.claude/skills`,
  `.agents/skills` (project) / `~/.copilot/skills`, `~/.agents/skills`
  (user) — explicit agentskills.io conformance, explicit cross-read of
  `.claude/skills`.
- **Rules**: no separate dimension — `.github/instructions/*.instructions.md`
  with `applyTo` glob frontmatter *is* the rules mechanism.
- **Subagents**: `.github/agents/*.agent.md` (current), `.claude/agents/`
  also recognized; `~/.copilot/agents/` (user). Legacy
  `.github/chatmodes/*.chatmode.md` still works and VS Code offers a
  quick-fix rename to `.agent.md` (single-source on rename timing).
  Frontmatter: persona + allowed-tools fields.
- **Hooks**: `.github/hooks/*.json`, **project-only, must be on default
  branch**. JSON `{version, hooks: {sessionStart, sessionEnd,
  userPromptSubmitted, preToolUse, postToolUse, errorOccurred}}`. Confirmed
  for coding agent (cloud) + CLI; VS Code agent-mode support unconfirmed
  either way. Adjacent: `.github/workflows/copilot-setup-steps.yml` (a real
  Actions job) for environment pre-install.
- **Commands**: `.github/prompts/*.prompt.md`, invoked `/name` — IDE-only
  (VS Code, Visual Studio, JetBrains); cloud coding agent support
  unconfirmed.
- Bonus MCP: `~/.copilot/mcp-config.json` (CLI user) /
  `.copilot/mcp-config.json` or `.github/mcp.json` (CLI project) /
  `.vscode/mcp.json` (VS Code) — precedence order single-source.

## Subfolder nesting (agents / rules / commands)

Whether `<dir>/subfolder/file` is discovered at all, and — if so — whether
the subfolder path becomes part of the registered name/invocation, or is
purely organizational. This matters directly for VIBE: `agents/research/*.md`
is a nested layout. Verified 2026-07-23; several cells are undocumented
either way rather than confirmed negative — see per-platform notes.

| Platform | Agents | Rules | Commands |
|---|---|---|---|
| Claude Code | ✅ recursive, **name-field only** (plugin exception: subfolder scopes the id, `plugin:review:security`) | ✅ recursive, organizational only | ❌ flat only — legacy path-namespacing was reported broken and closed "not planned" |
| Codex | ⚠️ undocumented either way | *(n/a — folded into AGENTS.md; root→cwd walk only, not full-tree recursion)* | ❌ flat only, **explicitly documented**: "Codex scans only the top-level Markdown files" |
| Gemini CLI | ❌ flat only — confirmed by reading `agentLoader.ts` source (filters files, does not recurse) | *(n/a — no rules dimension)* | ✅ recursive, **path becomes a namespace**: `git/commit.toml` → `/git:commit` |
| Cursor | ❌ flat only — no official doc, confirmed by an open community feature request asking for it | ✅ recursive, organizational only | ⚠️ split: IDE recursively scans (undocumented/emergent), **CLI does not** — a documented "known behavior difference" |
| Windsurf/Devin | *(n/a — no user-authored agent file format)* | ✅ recursive, **lazy-loaded by scope** (subdir rules load only when a file in that subtree is touched) | ✅ recursive; nested-workflow invocation-name format undocumented |
| Cline | *(n/a — no user-authored agent file format)* | ⚠️ undocumented — docs only ever show flat examples | ⚠️ undocumented — same caveat |
| Kiro | ✅ recursive, **and path becomes the name**: `.kiro/agents/research/code-researcher.md` registers/invokes as `research/code-researcher`, not `code-researcher` | ⚠️ implied via a `**/*.md` glob example, not confirmed for the default loader | *(n/a — no distinct commands dimension)* |
| Antigravity | ⚠️ undocumented either way (docs show only one level: `.agents/agents/<name>/agent.md`) | ⚠️ undocumented either way | *(n/a — no documented commands dimension)* |
| GitHub Copilot | ❌ flat only — a nested-folder bug report and feature request exist, closed "not planned" | ✅ recursive (`.instructions.md`) — VS Code docs state this explicitly; `applyTo` glob still does the actual scoping, not the path | ⚠️ undocumented either way |

**Practical read for VIBE's `agents/research/` layout**: only **Claude Code**
and **Kiro** accept it as-is, and even they diverge — Claude Code ignores the
subfolder for identity, Kiro folds it into the invoked name. Every other
subagent-capable target (Codex, Gemini CLI, Cursor, Copilot) either flattens
silently, drops the file, or is undocumented — a `vibe sync` agent adapter
must **flatten to the target's top level** and resolve name collisions
itself; it cannot assume nested source layout survives the copy.

## Cross-cutting notes

- **Subagent format has no cross-vendor standard**, unlike skills. Claude
  Code, Gemini CLI, Kiro, Antigravity, and Copilot all independently landed
  on "Markdown + YAML frontmatter, body = system prompt" but each uses its
  **own directory** with no cross-reads between them. Codex is the outlier
  format-wise (TOML). Cursor and Copilot are the only platforms that
  **explicitly cross-read Claude Code's `.claude/agents/`** (Cursor also
  reads `.codex/agents/`) — this is bilateral compatibility engineering by
  those two vendors, not a shared spec. Windsurf/Devin Desktop and Cline
  have **no user-authored subagent file format at all** — both restrict
  subagents to built-in, dynamically-spawned task decomposition.
- **"Rules" isn't universal.** Codex and Gemini CLI fold everything into
  their root-instructions hierarchy (AGENTS.md/GEMINI.md); Kiro's
  equivalent is steering-file `inclusion:` modes, not a separate rules
  directory.
- **Hooks are JSON almost everywhere** but event names, trust
  requirements, and scope (project-only for Kiro and Copilot; both scopes
  elsewhere) vary per platform — no shared schema.
- **Major rebrand mid-survey**: Windsurf → Devin Desktop (Cognition,
  2026-06-02). Legacy `.windsurf/*` paths still work; treat `.devin/*` as
  the forward path pending re-verification.

## Implications for VIBE

- `skills/` → `.agents/skills` symlink already reaches Codex and Gemini CLI
  today with zero adapter work, and would reach Cursor, Windsurf/Devin,
  Antigravity, and Copilot the same way if VIBE ever ships content there —
  see [ADR 0004](../decisions/0004-compile-canonical-content-through-adapters.md).
- `agents/` → `.claude/agents` symlink reaches Claude Code natively and
  Cursor/Copilot via their cross-reads, but **not** Codex (needs TOML
  translation), Gemini CLI, Kiro, or Antigravity (each needs its own
  `vibe sync` adapter target) — see [ADR 0006](../decisions/0006-predefine-research-agents-by-modality.md).
  The symlink also only works *because* today's `agents/research/*.md` is
  one nesting level deep and Claude Code ignores subfolders for identity;
  a future adapter targeting Gemini CLI, Cursor, or Copilot must flatten
  this layout rather than mirror it — see Subfolder nesting above.
- A future `rules/`, `hooks/`, or `commands/` canonical directory
  (roadmap 🔜 items per [ARCHITECTURE.md](../../ARCHITECTURE.md)) has no
  cross-vendor symlink shortcut available — every platform in this survey
  uses its own path and, for hooks, its own event schema. Adapter work,
  not a symlink, for all three.

## Sources

Numbered by platform; full URLs also inline above.

1. Claude Code — [Memory](https://code.claude.com/docs/en/memory), [Skills](https://code.claude.com/docs/en/skills), [Sub-agents](https://code.claude.com/docs/en/sub-agents), [Hooks](https://code.claude.com/docs/en/hooks), [MCP](https://code.claude.com/docs/en/mcp) — deep-read 2026-07-23.
2. Codex — [AGENTS.md](https://developers.openai.com/codex/guides/agents-md), [Skills](https://developers.openai.com/codex/skills), [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [Hooks](https://developers.openai.com/codex/hooks), [Custom Prompts](https://developers.openai.com/codex/custom-prompts), [MCP](https://developers.openai.com/codex/mcp) — deep-read 2026-07-23.
3. Gemini CLI — [GEMINI.md](https://geminicli.com/docs/cli/gemini-md/), [Skills](https://geminicli.com/docs/cli/skills/), [Policy engine](https://geminicli.com/docs/reference/policy-engine/), [Subagents](https://geminicli.com/docs/core/subagents/), [Remote subagents](https://geminicli.com/docs/core/remote-agents/), [Hooks](https://geminicli.com/docs/hooks/), [Commands](https://geminicli.com/docs/reference/commands/), [MCP](https://geminicli.com/docs/tools/mcp-server/) — deep-read 2026-07-23.
4. Cursor — [Rules](https://cursor.com/docs/context/rules), [Skills](https://cursor.com/docs/context/skills), [Subagents](https://cursor.com/docs/subagents.md), [Slash commands](https://cursor.com/docs/cli/reference/slash-commands), [MCP](https://cursor.com/docs/mcp) — deep-read 2026-07-23; subagent cross-read claim now confirmed (previously flagged single-source in an earlier draft of this survey).
5. Windsurf/Devin Desktop — [Memories](https://docs.devin.ai/desktop/cascade/memories), [Skills](https://docs.devin.ai/desktop/cascade/skills), [Hooks](https://docs.devin.ai/desktop/cascade/hooks), [Workflows](https://docs.devin.ai/windsurf/plugins/cascade/workflows), [MCP](https://docs.windsurf.com/windsurf/cascade/mcp), [rebrand announcement](https://devin.ai/blog/windsurf-is-now-devin-desktop) — fetched 2026-07-23; platform mid-rebrand, several single-source claims flagged inline.
6. Cline — [Cline Rules](https://docs.cline.bot/features/cline-rules), [Skills](https://docs.cline.bot/customization/skills), [Memory Bank](https://docs.cline.bot/best-practices/memory-bank), [Subagents](https://docs.cline.bot/features/subagents), [Hooks](https://cline.bot/blog/cline-v3-36-hooks), [Commands](https://docs.cline.bot/core-workflows/using-commands), [MCP](https://docs.cline.bot/mcp/mcp-overview) — deep-read 2026-07-23.
7. Kiro — [Steering](https://kiro.dev/docs/steering/), [Skills](https://kiro.dev/docs/skills/), [Subagents (chat)](https://kiro.dev/docs/chat/subagents/), [Subagents (CLI)](https://kiro.dev/docs/cli/custom-agents/), [Hooks](https://kiro.dev/docs/hooks/), [Slash commands](https://kiro.dev/docs/chat/slash-commands/), [MCP](https://kiro.dev/docs/mcp/) — deep-read 2026-07-23.
8. Antigravity — [Rules & Workflows](https://antigravity.google/docs/rules-workflows), [Skills](https://antigravity.google/docs/skills), [Agents CLI](https://antigravity.google/docs/cli/commands/agents), [Subagents](https://antigravity.google/docs/subagents), [Hooks](https://antigravity.google/docs/hooks), [MCP](https://antigravity.google/docs/mcp), [codelab](https://codelabs.developers.google.com/autonomous-ai-developer-pipelines-antigravity) — fetched 2026-07-23; newest/least-documented platform surveyed, several medium-confidence claims flagged inline.
9. GitHub Copilot — [Repository custom instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions), [AGENTS.md changelog](https://github.blog/changelog/2025-08-28-copilot-coding-agent-now-supports-agents-md-custom-instructions/), [Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills), [Custom agents](https://code.visualstudio.com/docs/agent-customization/custom-agents), [Hooks](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/use-hooks), [Prompt files](https://docs.github.com/en/copilot/tutorials/customization-library/prompt-files/your-first-prompt-file), [MCP](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers) — deep-read 2026-07-23.
10. [Agent Skills Specification](https://agentskills.io/specification), [agentskills/agentskills](https://github.com/agentskills/agentskills), [skills-ref on PyPI](https://pypi.org/project/skills-ref/) — cross-vendor skills standard, fetched 2026-07-23.
