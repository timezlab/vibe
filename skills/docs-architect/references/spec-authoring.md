# Spec Authoring — Quality Bar

Spec Kit generates the scaffolding; this reference governs what makes the content usable. A spec is usable only if an agent can turn it into a plan without guessing, and a `tasks.md` is usable only if an agent can pick up the next commit without a meeting.

## Contents
1. The executable-spec checklist (spec.md)
2. Committable-unit rule (tasks.md)
3. Banned phrasings
4. Observable done conditions
5. Status lifecycle
6. Tech debt entries
7. Work bigger than one feature

---

## 1. The executable-spec checklist (spec.md)

A spec must answer the questions implementation would otherwise answer by accident. Before accepting a `spec.md` (generated or hand-written), check:

- [ ] **Concrete scope** — not "improve UX" or "support auth"; named behaviors, endpoints, screens
- [ ] **Observable acceptance criteria** — verifiable by reading code or running a command
- [ ] **Non-goals are non-empty** — even small features name 1–2 things deliberately not done; empty non-goals = unchecked scope creep
- [ ] **Named users/callers/systems affected**
- [ ] **Open questions separated from settled decisions** — no hidden policy inside code examples
- [ ] **No "TBD", "etc.", "and more"**

If a reviewer could interpret the spec in two materially different ways, it is not ready — that's what `/speckit.clarify` is for.

Sequence rule: spec → plan → tasks, never plan-first. The plan may decompose work; it may not silently redefine scope or architecture. If implementation reveals the shape is wrong: stop, update the spec, note the change in the plan, then continue.

## 2. Committable-unit rule (tasks.md)

A `tasks.md` entry ≈ one commit. If "done" needs multiple PRs or days, split it.

**Bad (phase-level):**
> - [ ] Week 1: Implement JWT — token module, signing, verification, refresh tokens

**Good (committable):**
> - [ ] Add JWT signing/verification module (`src/auth/jwt.ts`)
>   - Done when: `signToken()` and `verifyToken()` exported with tests
> - [ ] Wire JWT middleware into the app
>   - Done when: `/protected` routes reject missing/expired tokens

Why: an agent resuming mid-stream reads the checklist and knows exactly what to commit next. Phase-level tasks (Week 1, Week 2…) look reasonable to a human skimming but force full re-planning on every resume — this is the single most common defect in generated task lists.

Size heuristics: finishable with one push today → right size. Describing it needs "and" → split. Two people could do it in parallel without conflict → split.

Every task carries a `Files:` hint — a task with no expected touch points forces the next agent to re-discover the architecture.

## 3. Banned phrasings

These consistently produce tasks no agent can pick up. Rewrite on sight:

| Banned | Why it fails | Rewrite to |
|--------|-------------|------------|
| "Implement X module" | No surface, no done condition | Named exports + test cases covered |
| "Add appropriate error handling" | "Appropriate" is untestable | Which calls, which error, which return shape, which test |
| "Handle edge cases" | Which ones? | List them: empty → 400, missing field → 422, >1MB → 413 |
| "Polish / clean up X" | Never done | Name the file and the structural change; "no behavior change; existing tests pass" |
| "Investigate / spike X" | Open-ended | Timeboxed task whose output is a written paragraph in plan.md Decisions |
| "Refactor X for clarity" | "Clarity" is taste | State the move: "extract `validate()` from `routes/login.ts` to `src/validators.ts`; update 3 call sites" |
| "Similar to task N" | Rots when N changes | Write it fully — repetition is cheaper than indirection |

General rule: if the task could mean five things to five agents, it's a topic, not a task. Topics belong in `plan.md` context.

## 4. Observable done conditions

"Implement auth" is not a done condition. "`POST /login` returns a JWT on valid creds; integration test passes" is. Observable = another agent can verify by reading code or running a command, without asking the author.

## 5. Status lifecycle

Feature folders never move — no `completed/` archive. When all tasks are checked:

1. Mark `Status: done`, `Completed: <date>` in the `spec.md`/`plan.md` header
2. Add a one-line outcome note if the result differed from the goal
3. Run the graduation ritual (`freshness.md` §Graduation) — distill decisions into `docs/decisions/`, gotchas into `docs/reference/`, deferred work into `docs/tech-debt.md`
4. **Never rewrite** a done feature's spec/plan/tasks when code later changes — annotate instead (`freshness.md`)

## 6. Tech debt entries

Debt that surfaces during a feature but isn't worth fixing now goes in `docs/tech-debt.md` — one flat file, agents grep it.

```markdown
## <short title>

- **Where:** `src/auth/jwt.ts:42-58`
- **Symptom:** Token refresh uses setTimeout; not resilient to clock drift or restart.
- **Why deferred:** Needs a job queue we don't have yet.
- **Trigger to fix:** When a background job runner lands, migrate this first.
- **Created:** 2026-07-22
```

All four fields are load-bearing: debt without **Where** is a rumor; without **Why deferred**, future agents "helpfully" fix it and hit the same wall; without **Trigger**, debt accumulates forever. Line-level quirks belong here too ("workaround at `file.ts:117` — lib returns `null` not `undefined`; do not 'fix' this check").

## 7. Work bigger than one feature

Split by **deliverable**, not by time. Each deliverable gets its own `specs/NNN-<name>/`; a parent feature's `plan.md` lists them:

```markdown
## Sub-features
- `specs/012-auth-tokens/` — JWT + refresh
- `specs/013-auth-2fa/` — TOTP
```

This keeps each `tasks.md` committable-sized. Run `/speckit.analyze` across the set for consistency.
