# vibe

VIBE (Vibe Integrated Build Environment): canonical agent-harness content +
(planned) local multi-agent workspace app. Pre-alpha — no `vibe` CLI or web
app exists yet; this repo is skills + docs foundation today.

## Stack

Markdown skills/docs · GitHub Spec Kit (`specify` CLI) · planned app:
Node/TypeScript, node-pty, xterm.js, Dockview.

## Key rules

- Canonical sources only: `skills/`, `agents/`, `rules/`, and `hooks/` are
  the source of truth; `.agents/skills/`, `.claude/skills/`,
  `.claude/agents/`, and `.claude/rules/` are symlinks into them — never
  edit or copy content there. Hooks wire via `settings.json`, not
  symlinks (per-project opt-in).
- Generated platform outputs are build artifacts — regenerate, never
  hand-patch (constitution principle I).
- ADRs in `docs/decisions/` are append-only; reversing a decision = new ADR
  with supersession links.
- Docs update in the same change as the code that invalidates them.
- Don't present planned commands (`vibe`, `vibe ui`, `vibe sync`) as
  implemented.

## Commands

- Validate a skill: `uvx --from 'skills-ref==0.1.1' agentskills validate skills/<name>`
- Spec Kit: `specify check` · feature flow via `/speckit-specify` →
  `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`
- Commits: `skill: <name> (<desc>)` for new skills, `fix(<name>): …` /
  `docs: …` / `chore: …` otherwise. No Co-Authored-By lines.

## Spec gate

Use Spec Kit only for work with ≥3 tasks / >2 days / changed contracts or a
debatable done condition — otherwise just make the change. No active feature
spec exists; the first qualifying feature takes `specs/001-*`.

## Docs map

| When you need to… | Read |
|---|---|
| Understand the repo structure | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Find active feature work | `specs/NNN-*/` (empty — no active feature yet) |
| Understand product intent / scope | [docs/product/DESIGN.md](docs/product/DESIGN.md) |
| Check the roadmap or open decision gates | [docs/product/roadmap.md](docs/product/roadmap.md) |
| Understand why a technical choice was made | [docs/index.md](docs/index.md#decisions-adrs--append-only) |
| Check known debt/quirks | [docs/tech-debt.md](docs/tech-debt.md) |
| Contribute a skill | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Standing principles for features | [.specify/memory/constitution.md](.specify/memory/constitution.md) |
