# Contributing

Thanks for helping build VIBE. The project is **pre-alpha**: today you can
contribute skills and documentation. CLI/app contributions open once those
packages exist (Phases 1–2 of the [roadmap](docs/product/roadmap.md)).

## Setup assumptions

- Git, and [uv](https://docs.astral.sh/uv/) for `uvx` (skill validation,
  Spec Kit CLI).
- Skills are edited at their canonical source under `skills/` —
  `.agents/skills/` and `.claude/skills/` are symlinks; never edit or copy
  content there.

## Add or update a skill

Place each skill in `skills/<skill-name>/` with at least a `SKILL.md`; add
`references/`, `scripts/`, or `assets/` only when the skill needs them at
runtime.

Minimum frontmatter:

```yaml
---
name: skill-name
description: Describe what the skill does and when an agent should use it.
---
```

Rules:

- Lowercase letters, numbers, hyphens for the name; ≤64 chars; matches the
  directory name.
- Description ≤1,024 chars and covers both capability and activation context.
- `SKILL.md` focused and under 500 lines; move detail into `references/`
  (one level deep) and link from `SKILL.md`.
- Runtime scripts self-contained, deterministic, explicit about dependencies;
  test every script that changes.
- No secrets, credentials, private URLs, or generated artifacts.
- New skill → add it to the skills list in [README.md](README.md).

Validate before opening a PR:

```bash
uvx --from 'skills-ref==0.1.1' agentskills validate skills/<skill-name>
```

## Documentation rules

- **Docs ship in the same PR as the change that invalidates them.** A PR that
  changes behavior without updating the affected docs is incomplete.
- Where things go: product intent → `docs/product/` · technical decisions →
  a new ADR in `docs/decisions/` (append-only; supersede, don't edit) ·
  debt → `docs/tech-debt.md` · agent routing → `AGENTS.md` (≤150 lines).
- Every new doc under `docs/` gets a one-line entry in
  [docs/index.md](docs/index.md).
- Link to facts, don't duplicate them.

## Spec Kit gate

Use Spec Kit (`/speckit-specify` → `/speckit-plan` → `/speckit-tasks` →
`/speckit-implement`) only for work with **≥3 tasks, >2 days, changed
user-visible behavior/contracts, or a debatable done condition**. Below the
gate, just make the change. Standing principles:
[.specify/memory/constitution.md](.specify/memory/constitution.md).

## Commits and PRs

- `skill: <name> (<short description>)` for new skills;
  `fix(<name>): …`, `docs: …`, `chore: …` otherwise.
- Keep a PR to one skill or one repository concern.

Pre-PR checklist:

- [ ] Changed skills pass `agentskills validate`.
- [ ] Referenced files and commands exist (no planned command presented as
      implemented).
- [ ] Affected docs updated in this PR; new docs indexed in `docs/index.md`.
- [ ] Behavior changes explained, with representative test prompts when skill
      triggering changed.

By contributing, you agree your contribution is licensed under the
[MIT License](LICENSE).
