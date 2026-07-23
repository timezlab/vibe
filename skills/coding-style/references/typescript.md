# TypeScript — deep guidance

Read when writing or reviewing TypeScript/React beyond the basics. The
[TypeScript rules pack](../../../rules/typescript/coding-style.md) states
the constraints; this file shows the patterns that satisfy them. Always
defer to the repo's existing framework preset and configs first
(SKILL.md: match the room).

## Contents

1. tsconfig baseline
2. Lint and format baseline
3. Naming map
4. Type patterns
5. Zod: schema as the single source
6. Error handling
7. React and Next.js
8. Async

## 1. tsconfig baseline

Start from the framework's preset (`next`, `vite`, …) and ensure:

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,   // arr[i] is T | undefined — reality
    "verbatimModuleSyntax": true         // forces `import type`, keeps builds tool-agnostic
  }
}
```

`noUncheckedIndexedAccess` is the highest-value flag outside `strict`: it
makes index access honest and surfaces a whole class of "cannot read
property of undefined" at compile time. Enable it in new projects; in
existing ones it can be noisy — propose, don't impose.

## 2. Lint and format baseline

Two tools, two jobs — the linter owns correctness, the formatter owns
whitespace (the split every major org converged on):

- **ESLint** flat config with `typescript-eslint`:
  `recommendedTypeChecked` + `stylisticTypeChecked` (needs
  `parserOptions.projectService: true`). Escalate to `strict` tiers only
  by team choice — they are opinionated and not semver-stable.
- **Prettier** with zero or near-zero options — every option is a future
  debate. Add `eslint-config-prettier` last to silence overlap.
- **Biome** is a legitimate single-tool alternative (lint + format, fast);
  choose per repo, don't mix both formatters.

Key rules worth their noise: `no-floating-promises`,
`no-misused-promises`, `switch-exhaustiveness-check`,
`consistent-type-imports`. Full setup: [enforcement.md](enforcement.md).

## 3. Naming map

| Thing | Convention | Example |
|---|---|---|
| File | kebab-case | `password-input.tsx`, `use-chat.ts` |
| Component / class / type / interface | PascalCase, no `I` prefix | `PasswordInput`, `ChatMessage` |
| Hook | `use` + camelCase; file `use-*.ts` | `useChat` in `use-chat.ts` |
| Function / variable | camelCase, intent + units | `retryDelayMs` |
| Module constant | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Zod schema + its type | one shared PascalCase name | `const ChatMessage = z.object(…); type ChatMessage = z.infer<…>` |

## 4. Type patterns

- **Boundary narrowing**: take `unknown`, prove the shape —
  `safeParse`, a type guard, or `instanceof` — then work with the typed
  value. `as` asserts without proof; reserve it for provably-safe cases
  and say why.
- **Discriminated unions for state**:

  ```ts
  type LoadState =
    | { status: "idle" }
    | { status: "loading" }
    | { status: "error"; error: string }
    | { status: "ready"; data: Report };
  ```

  Parallel booleans (`isLoading`, `isError`, `data?`) allow impossible
  states; the union makes them unrepresentable. Pair with exhaustiveness:

  ```ts
  default: {
    const unreachable: never = state; // compile error when a variant is added
    throw new Error(`Unhandled: ${JSON.stringify(unreachable)}`);
  }
  ```

- **`satisfies`** checks a value against a type while preserving the
  narrower inferred type — use it for config objects and lookup maps.
- **Prefer union types / `as const` maps over `enum`** in new code:
  erasable syntax, no runtime artifact, same exhaustiveness support.
  Match the repo where enums are established.
- **`import type`** for type-only imports (enforced by
  `verbatimModuleSyntax` / `consistent-type-imports`).

## 5. Zod: schema as the single source

```ts
// entities/chat/message.ts — schema and type share one name
export const ChatMessage = z.object({
  id: z.string(),
  role: z.enum(["user", "assistant"]),
  content: z.string(),
  createdAt: z.coerce.date(),
});
export type ChatMessage = z.infer<typeof ChatMessage>;
```

- Parse at the boundary, once: `ChatMessage.safeParse(json)` where data
  enters (API route, SSE handler, storage read) and handle the failure
  branch — log it with context and surface a typed error, don't `!` past
  it. Inside the boundary, pass the typed value; re-parsing everywhere is
  noise.
- Derive variants instead of redefining: `ChatMessage.pick(…)`,
  `.omit(…)`, `.extend(…)`, `z.input<>` vs `z.output<>` when transforms
  differ.
- Env/config: a `z.object` parsed once at startup (`coerce` for numbers/
  booleans) — missing config fails loudly at boot, satisfying the
  no-secret-shaped-defaults rule.

## 6. Error handling

- Typed error classes per failure family, mapped centrally:

  ```ts
  // lib/errors.ts
  export class UnauthorizedError extends Error {}
  export class NotFoundError extends Error {}
  // api/_helpers.ts — one place turns errors into HTTP responses
  export function routeError(err: unknown): Response { /* map by instanceof */ }
  ```

  One envelope shape for all API errors — two endpoints with different
  error bodies force every client to special-case.
- Throw for exceptional failures; return a discriminated result
  (`{ ok: true; value } | { ok: false; error }`) when failure is an
  expected outcome the caller must branch on (parse attempts, user-facing
  validation). Pick per function, don't mix both for the same call.
- `cause` chains: `new Error("context", { cause: err })` preserves the
  origin the way Python's `raise … from` does.

## 7. React and Next.js

- **Server/client boundary explicit**: `page.tsx` stays a thin server
  shell that renders a clearly-marked client sibling (e.g.
  `page.client.tsx` with `"use client"`). Grep-able boundary, minimal
  client bundle.
- **Extract logic from components**: business rules, data transforms, and
  update logic live in plain functions, custom hooks, or reducers —
  testable without rendering (tdd skill: test logic, not components).
  When update logic outgrows two `useState`s, a pure reducer function is
  the testable shape.
- **State placement**: server state belongs to a query library (TanStack
  Query — caching, retries, invalidation); URL-visible state in the URL;
  ephemeral UI state in `useState`. Reach for a global store only for
  genuinely app-wide client state, and prefer several small per-domain
  stores over one monolith.
- **Forms**: schema-first — the Zod schema drives both the resolver
  (`react-hook-form` + `zodResolver`) and the submit payload type.
- **Component granularity**: decompose by interaction complexity, not
  line count — an interactive system (board, editor) splits into focused
  components with colocated small private helpers; a static content page
  can stay one file without shame.
- **Memoization**: with the React Compiler enabled, reflexive
  `useMemo`/`useCallback` is dead weight; without it, memoize where a
  measurement or an obviously hot list render justifies it. Escape
  hatches (`"use no memo"`) carry a comment naming the incompatibility.

## 8. Async

- `no-floating-promises` as a lint error; a genuine fire-and-forget is
  `void doThing(); // fire-and-forget: <why>`.
- Independent work runs concurrently — `Promise.all` (or
  `Promise.allSettled` when partial failure is expected and handled).
- Long-lived or user-cancelable operations accept an `AbortSignal` and
  pass it through to `fetch`/listeners; leaked subscriptions and orphaned
  requests are the JS flavor of fire-and-forget goroutines.
