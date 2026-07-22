# AGENTS.md / CLAUDE.md Discipline

`AGENTS.md` (and its mirrors `CLAUDE.md`, `GEMINI.md`) is the **hottest** doc in the repo — it loads every session, crowding out the task, the code, and the docs that would actually solve the problem. Every line must earn its place.

The failure mode is predictable: the file grows to 400 lines, nobody maintains it, the agent ignores the bottom half, signal-to-noise collapses. The fix is structural, not cosmetic.

## Contents
1. Size targets and hard limits
2. Table of contents, not encyclopedia
3. What belongs / what doesn't
4. Skeleton
5. Anti-patterns
6. Audit procedure
7. One source, many mirrors (CLAUDE.md, GEMINI.md, monorepos)

---

## 1. Size targets and hard limits

- Target **~100 lines, hard ceiling 150**. Past 150, something belongs in `docs/` instead.
- These aren't style preferences. Codex concatenates AGENTS.md files with a default **32 KiB cap and silently truncates** the rest; practitioners converge on <300 lines max (HumanLayer runs <60); Anthropic's own guidance: bloated CLAUDE.md files cause Claude to ignore your actual instructions.
- The per-line test (Anthropic's): **"Would removing this line cause the agent to make mistakes?"** If not, cut it.
- A rule that keeps being ignored is not a prompting problem — the file is too long, or the rule belongs in a hook/linter where it's enforced deterministically.

## 2. Table of contents, not encyclopedia

AGENTS.md answers **"where do I look?"**, not **"what do I do?"**

**Weak (encyclopedia):**
> ## Testing
> We use vitest. Tests live in `tests/` folders. Write failing tests first. Use describe/it blocks. Mock external services. Prefer integration tests... (40 more lines)

**Strong (table of contents):**
> ## Testing
> - vitest, tests in `tests/` per package (not co-located)
> - TDD: failing test → implement → pass → commit
> - Full conventions: `docs/reference/vitest.md`

## 3. What belongs / what doesn't

**Yes:**
- Project identity — 1–2 sentences
- Stack summary — one line
- The 3–5 inviolable rules (real damage if violated)
- The routing table: "for X, read Y"
- Commit / test / build commands the agent can't guess
- Pointer to `ARCHITECTURE.md`

**No — route elsewhere:**
- Coding style guides → linter config or rules files (enforced beats described)
- Architectural rationale → `docs/decisions/`
- Feature specs → `specs/` or `docs/product/`
- Library how-tos → `docs/reference/<lib>.md`
- History → git log or superseded ADRs
- Onboarding narrative → CONTRIBUTING.md / README.md
- Anything the model already knows ("be careful with git push") — restating known things is pure context tax

If in doubt: would this rot in 3 months untouched? Then it needs a home with an update trigger, and that home is not the hot file.

## 4. Skeleton

```markdown
# <project-name>

<One sentence: what this repo is.>

## Stack
<Language, runtime, package manager, key frameworks — one line.>

## Key rules
- <3–5 bullets an agent must not violate.>

## Commands
- Build: `<cmd>` · Test: `<cmd>` · Lint: `<cmd>`
- Commits: <style>

## Docs map

| When you need to...      | Read                              |
|--------------------------|-----------------------------------|
| Understand the structure | `ARCHITECTURE.md`                 |
| Understand a decision    | `docs/decisions/` (see index)     |
| Find active work         | `specs/NNN-*/`                    |
| Check known debt/quirks  | `docs/tech-debt.md`               |
| Use library X correctly  | `docs/reference/<lib>.md`         |
| Deploy / debug / release | `docs/guides/<task>.md`           |
```

~30 lines of signal. Fill in; resist expanding sections into paragraphs.

## 5. Anti-patterns

- **The manifesto** — "our philosophy is clean, maintainable code…". Agents need rules with file paths, not philosophy.
- **The changelog** — "recently we migrated from X to Y". Git log territory.
- **The tutorial** — step-by-step how-tos. Move to `docs/guides/`, link.
- **The safety blanket** — restating system-prompt basics.
- **The wishlist** — "in the future we want…". Goes to `docs/product/DESIGN.md`.
- **Stale paths** — a routing entry pointing at a moved file actively poisons context; worse than no entry. The freshness sweep (`freshness.md`) covers AGENTS.md first for this reason.
- **README duplication** — README is for humans finding the project; AGENTS.md for agents working in it. Identity line may overlap; setup instructions get linked, not repeated.

## 6. Audit procedure

Line by line, five questions:

1. Would removing this change agent behavior? No → cut.
2. Duplicated elsewhere? → keep one copy, link the other.
3. Will it rot (versions, names, "currently")? → move to a dated doc or delete.
4. Rule or narrative? Narrative → move. Rule → keep, tighten.
5. Could a pointer replace the paragraph? → almost always yes.

Typical result: 300 lines → 80 lines + 4 docs under `docs/`. Information doesn't disappear; it moves to where it loads only when needed.

## 7. One source, many mirrors

**AGENTS.md is the canonical file.** As of 2026 it's read natively by Codex, Cursor, Copilot/VS Code (default on), Windsurf/Devin, Zed, and Cline — no mirror needed for any of those. Exactly two mainstream tools don't read it, and both get a **one-line import file** (never a symlink):

- **Claude Code** reads only CLAUDE.md — it does *not* fall back to AGENTS.md. Create a `CLAUDE.md` whose body is exactly `@AGENTS.md`; Claude Code inlines the import at session start (depth ≤4, skipped inside code blocks). This is Anthropic's documented recommendation. Claude-specific lines go *below* the import.
- **Gemini CLI** reads only GEMINI.md by default. Either a `GEMINI.md` containing `@./AGENTS.md` (import processor is on by default), or skip the wrapper entirely and commit `.gemini/settings.json` with `"context": { "fileName": ["AGENTS.md"] }`.

Why import, not symlink: a committed symlink on a Windows checkout (where `core.symlinks` defaults to false) silently becomes a plain text file whose entire content is the string "AGENTS.md" — every tool then loads a one-word context file with no error. The import needs no OS privileges, survives any checkout, and still allows tool-specific lines under it; drift is structurally impossible either way. If you find a hand-copied CLAUDE.md, replace its duplicated body with the import.

Per-tool gotchas worth knowing:
- Plain markdown links (`[see](AGENTS.md)`) are **not** auto-inlined by any tool — only true import syntax guarantees the content reaches context.
- **Zed** uses first-match-wins across `.rules` → `.cursorrules` → … → `AGENTS.md`: a leftover `.rules` or `.cursorrules` silently shadows AGENTS.md — delete the legacy files.
- **Aider** doesn't auto-read anything: add `read: [AGENTS.md]` to `.aider.conf.yml`.

**Monorepos:** nested AGENTS.md per package, nearest-file-wins (the standard's precedence rule; OpenAI's monorepo carries 88 of them). The root file stays global-only: stack, commands, routing. Package specifics live in the package's own file — this is also the escape hatch when the root file presses against the size ceiling.
