# Freshness — Divergence, Post-Refactor Sweep, Spec Graduation

Docs that contradict code are a critical failure: an agent following a stale doc confidently implements the wrong thing, and a stale routing entry poisons every session that loads it. **Trust the code, fix the doc** — on any divergence, the code is the truth and the doc is the bug.

## Contents
1. Triggers
2. The post-refactor sweep (grep-driven)
3. Completed specs: annotate, never rewrite
4. Spec graduation — when a feature ships
5. Done-condition

---

## 1. Triggers

Run the sweep (§2) after any of: renamed function/class/type · moved file or changed module boundary · reversed decision · completed `tasks.md` item that changed a public surface. Run graduation (§4) when a feature's status flips to done. Additionally run `/speckit.converge` at the end of implementation sessions so the *active spec* tracks reality — the sweep below covers everything else.

## 2. The post-refactor sweep (grep-driven)

Write down the old and new names first — you'll grep these strings repeatedly:

```
Old: <OldName>, <old/path>, <oldMethod>    New: <NewName>, <new/path>, <newMethod>
```

Then walk four surfaces. Agents (and humans) systematically under-scope this to "update the docs" — the doc layer is only a quarter of it.

**Surface 1 — docs:**
```bash
grep -rn "OldName\|old/path" AGENTS.md CLAUDE.md ARCHITECTURE.md README.md CONTRIBUTING.md docs/ specs/
```
- AGENTS.md routing entries and inline examples (do this file first — it's hot)
- ARCHITECTURE.md package table and dependency rules
- Active `specs/`: update tasks/paths, note the rename in `plan.md` Decisions
- Done `specs/`: **annotate, don't edit** (§3)
- `docs/decisions/`: if the refactor *reverses* an ADR → new ADR + supersede the old; re-check every "Must now be true" invariant still names real symbols
- `docs/tech-debt.md`: update locations; delete entries the refactor resolved
- `docs/reference/`, `docs/guides/`, `docs/product/`: code examples and paths

**Surface 2 — source-level docs** (the most-missed layer):
```bash
grep -rn "OldName\|oldMethod" --include="*.ts" --include="*.tsx"
```
- JSDoc/TSDoc prose: `@param`/`@returns` naming old types, `@see` to moved files, `@example` imports
- Test descriptions: `describe('OldName')` — stale names make CI failures confusing
- Error messages and log strings that name the symbol

**Surface 3 — config/build** (failures here are the most confusing — builds pass, imports silently resolve wrong):
```bash
grep -rn "old/path\|OldName" tsconfig*.json package.json packages/*/package.json \
  *.config.* .github/ 2>/dev/null; grep -rn "OldName\|old/path" --include="index.ts" .
```
- tsconfig `paths` aliases, project `references`, include/exclude globs
- package.json `exports` subpaths, `main`/`types`, script names
- Barrel files re-exporting the old name or old path (decide: compat re-export for one release, or clean break — document either)
- Bundler entry points/aliases, CI workflow paths, cache keys

**Surface 4 — catch-all:**
```bash
grep -rn "OldName\|old/path\|oldMethod" --exclude-dir={node_modules,.git,dist,coverage}
```
Every remaining hit is either intentional (dated annotations, deprecation notes, changelog) or stale — fix the stale ones.

## 3. Completed specs: annotate, never rewrite

A done feature's spec/plan/tasks is historical record — it documents *what we knew when we decided*, and readers use git for the present. Rewriting it destroys that trail.

When a later change invalidates references in a done spec, add a dated note at the top and leave the body untouched:

```markdown
> **Note (2026-07-22):** `OldName` was renamed to `NewName` and moved to
> `src/new/path/` after this feature completed. References below reflect
> the state at completion time.
```

## 4. Spec graduation — when a feature ships

Specs are ephemeral; the knowledge inside them often isn't. When marking a feature done, spend 10 minutes distilling before the context evaporates:

1. **Decisions → ADRs.** Scan `plan.md` Decisions for anything that creates an invariant, would restart a debate, or you'd hate to see silently undone → `docs/decisions/NNNN-<topic>.md` (`adr.md` has the bar). Most features graduate 0–2 ADRs; forcing more produces noise.
2. **Gotchas → reference.** Library quirks and symptom→cause→fix discoveries from implementation → the relevant `docs/reference/<lib>.md`.
3. **Deferred work → tech debt.** Unchecked tasks and known shortcuts → `docs/tech-debt.md` entries (with Where/Symptom/Why-deferred/Trigger). Then check them off in `tasks.md` with a pointer.
4. **Surface changes → living docs.** New commands, env vars, or module boundaries → AGENTS.md routing, ARCHITECTURE.md, `docs/guides/`.
5. Mark `Status: done, Completed: <date>` in the spec header; add a one-line outcome note if it differed from the goal.

Skipping graduation is how repos end up with 40 dead spec folders as the only record of every decision ever made — technically present, practically unfindable.

## 5. Done-condition

The sweep is complete when **grep for the old name returns only intentional, dated hits** — and graduation is complete when the spec folder could be deleted tomorrow without losing any decision, quirk, or debt (you won't delete it; it's history — but nothing durable should live only there).

- [ ] All four surfaces walked (docs · source-level · config/build · catch-all)
- [ ] Done specs annotated, not edited; active specs' `plan.md` notes the rename
- [ ] ADR supersession handled if a decision was reversed; "Must now be true" invariants still name real symbols
- [ ] Final grep: only intentional hits remain
