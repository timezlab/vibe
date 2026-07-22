# Spec Kit — Setup & Workflow

GitHub Spec Kit (`github/spec-kit`) is the spec-driven-development engine this skill standardizes on: one folder per feature holding `spec.md` (what & why), `plan.md` (how), `tasks.md` (checklist), driven by `/speckit.*` slash commands.

Spec Kit releases weekly and details below rot fast (snapshot: v0.13.x, 2026-07 — see `MAINTENANCE.md`). When anything disagrees with reality, trust `specify --help` and the official docs at github.github.io/spec-kit.

## Contents
1. When to use it — and when not to
2. Install & init
3. What gets scaffolded
4. The command workflow
5. Claude Code–specific practices
6. Known failure modes

---

## 1. When to use it — and when not to

Use Spec Kit when **any** of these hold:
- The work spans ≥3 tasks or more than ~2 days
- The spec must outlive one agent session or be read by other people/tools
- User-visible behavior, API shape, or data contracts change
- Reasonable engineers could disagree on what "done" means

Skip it (deliberately, and say so) for bug fixes, mechanical single-commit changes, and exploratory spikes — plan mode for anything that still needs a plan, or just make the change when it's one obvious commit. This gate matters: the most common criticism of Spec Kit is ceremony on small tasks ("generates the illusion of work"). A spec you didn't need is context pollution for every future session.

If the user explicitly asks for a spec on below-gate work, don't refuse silently and don't comply silently: state the gate and the cost in one sentence, then follow their call.

## 2. Install & init

Two independent choices — how to install, then what to init. Init runs **once**; don't combine both init forms.

```bash
# 1) install the CLI (persistent; specify-cli is on PyPI)
uv tool install specify-cli        # or skip installing: prefix commands with `uvx`, e.g. `uvx specify-cli init .`

# 2) init once — existing repo (new project: specify init <name> --integration claude)
specify init . --integration claude
```

Notes:
- The flag is `--integration` (older posts show `--ai` — renamed). Omit it for an interactive picker.
- `specify init` is not the end of bootstrap — bootstrap is done when `/speckit.constitution` has seeded real principles into `.specify/memory/constitution.md` (run it in the first agent session).
- For Claude Code, commands install as **skills under `.claude/skills/`** (the old `.claude/commands/*.md` layout is legacy).
- Multiple agent integrations can coexist in one repo (Claude Code + Cursor + Copilot are multi-install safe) — run `specify integration install <key>` per agent; list keys with `specify integration list`.
- Keep the CLI current: `specify self check` / `specify self upgrade`.

## 3. What gets scaffolded

```
.specify/
├── memory/constitution.md    # standing principles all features inherit
├── templates/                # spec/plan/tasks templates (+ overrides/ for project-local edits)
├── scripts/                  # automation used by the commands
└── feature.json              # tracks the active feature
specs/
└── NNN-<feature-name>/       # created per feature AT REPO ROOT (not inside .specify/)
    ├── spec.md  plan.md  tasks.md
    ├── research.md  data-model.md  quickstart.md      # generated when relevant
    └── contracts/  checklists/
```

Two integration points with the docs tree this skill maintains:
- `constitution.md` holds standing principles ("all packages are ESM", "no default exports") — it is the *warm* twin of AGENTS.md. Don't duplicate between them; AGENTS.md routes, constitution rules.
- `specs/` folders are **ephemeral**: historical record once the feature ships. Durable knowledge graduates into `docs/` (see `freshness.md` §Graduation).

## 4. The command workflow

Full path (heavyweight features):

```
/speckit.constitution → /speckit.specify → /speckit.clarify → /speckit.plan
→ /speckit.checklist → /speckit.tasks → /speckit.analyze → /speckit.implement
→ /speckit.converge
```

Short path (typical feature):

```
/speckit.specify → /speckit.plan → /speckit.tasks → /speckit.implement → /speckit.converge
```

| Command | What it does | Skip when |
|---------|--------------|-----------|
| `/speckit.constitution` | Create/update standing principles | Already exists and current |
| `/speckit.specify` | Write `spec.md` — goal, acceptance, non-goals | Never (this is the point) |
| `/speckit.clarify` | Interrogate the spec's ambiguities before planning | Spec is already unambiguous |
| `/speckit.plan` | Write `plan.md` — technical shape | Never |
| `/speckit.checklist` | Quality checklists for the plan | Small features |
| `/speckit.tasks` | Derive `tasks.md` committable units | Never |
| `/speckit.analyze` | Cross-artifact consistency check (spec vs plan vs tasks) | Single small artifact set |
| `/speckit.implement` | Execute tasks | You're implementing manually |
| `/speckit.converge` | Diff codebase against spec/plan/tasks, append remaining work | Nothing was implemented yet |

`/speckit.converge` (added mid-2026) is the anti-drift step: run it at the end of each implementation session so the spec reflects what actually got built. Before it existed, spec drift was the tool's #1 reported failure.

Also useful: `/speckit.taskstoissues` converts `tasks.md` into GitHub issues when work is handed to a team.

## 5. Claude Code–specific practices

- Run `/speckit.specify` and `/speckit.plan` in **plan mode**; annotate the generated plan by hand, then iterate ("address all notes, don't implement yet") before `/speckit.implement`.
- `/speckit.clarify` before plan and `/speckit.analyze` before implement are the two highest-value optional steps — they catch ambiguity while it's still cheap.
- Constitution rules are **advisory** — the model reads them, nothing enforces them. For rules that must hold deterministically (lint, banned imports, commit format), pair the constitution with Claude Code hooks.
- Keep CLAUDE.md/AGENTS.md separate from the constitution: the hot file routes ("specs live in `specs/`, principles in constitution"), the constitution holds the principles themselves.

## 6. Known failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Six documents for a two-hour change | Spec Kit applied below its size gate | Delete the folder, use plan mode; note the gate in AGENTS.md |
| Spec says X, code does Y | Implementation sessions never resynced | Run `/speckit.converge` after each session; on conflict, trust code, fix spec |
| Specs restate the obvious at length | Accepting generated text uncritically | Apply the executable-spec checklist in `spec-authoring.md`; cut filler |
| Old `.claude/commands/speckit-*` files linger | Pre-skills-migration install | `specify self upgrade`, re-run integration install, delete legacy files |
| Docs/blog instructions don't match CLI | Weekly release cadence | `specify --help` is the truth; update `MAINTENANCE.md` snapshot |
