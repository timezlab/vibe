---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.mts"
  - "**/*.cts"
  - "**/*.js"
  - "**/*.jsx"
---

# Coding style — TypeScript

Extends [common/coding-style.md](../common/coding-style.md) — read that
first; this file adds TypeScript specifics and wins where they conflict.
In plain `.js`/`.jsx` files the type-level rules (§ Types, the `z.infer`
derivation) have no compiler to enforce them and don't apply; everything
else — files/exports, runtime parsing, async, React, immutability — does.

## Files and exports

- Filenames are kebab-case: `password-input.tsx` exporting `PasswordInput`,
  `use-chat.ts` exporting `useChat`. Case-only renames of PascalCase files
  break silently between case-insensitive (macOS) and case-sensitive
  (Linux/CI) filesystems.
- Named exports only; `export default` exists solely where the framework
  demands it (Next.js `page.tsx`/`layout.tsx`, config files). A default
  export has no canonical name — every import site can invent its own,
  which breaks rename and find-references.

## Types

- `strict: true` is assumed; write code that passes it.
- At untyped boundaries prefer `unknown` and narrow immediately; `any` only
  where a dependency's types are genuinely broken — one line, with the
  reason.
- Let inference type locals; annotate exported function signatures
  explicitly — they are the contract.
- Model state as discriminated unions
  (`status: 'active' | 'resolved' | 'closed'`), not parallel booleans; add
  a `never` exhaustiveness check where the union will grow.
- Prefer narrowing over `as` casts and `!` assertions — both silence
  exactly the errors strict mode exists to raise.
- Throw only `Error` (or subclasses); anything else loses the stack trace.

## Schema as the single source of shape

Define each externally-visible shape once as a schema and derive the type:

```ts
export const ChatMessage = z.object({ /* … */ });
export type ChatMessage = z.infer<typeof ChatMessage>;
```

Never hand-write a parallel `interface` for a shape a schema already
defines — the two will drift. Parse external data (API, SSE, storage, LLM
output) with `safeParse` at the boundary and handle the failure branch.

## Async

- No floating promises: `await` it, return it, or `void` it with a comment
  saying fire-and-forget is intended.
- Independent awaits run in parallel — `Promise.all([...])`, not a
  sequential await chain.

## React

- Function components and hooks; extract non-trivial logic into plain
  functions or custom hooks so it tests without rendering (the tdd skill:
  test logic, not components).
- Keep the server/client boundary explicit: a server `page.tsx` stays a
  thin shell; interactive code lives in a clearly-marked client component.
- Reach for `useReducer`/pure state functions when update logic outgrows a
  couple of `useState`s — pure functions test cheaply.
- Memoize for a measured reason, not by reflex — with the React Compiler
  enabled, reflexive `useMemo`/`useCallback` is usually dead weight.

## Immutability

Default to `const` and non-mutating updates (spread, `toSorted`,
`toReversed`) for shared or passed-in data. Local mutation inside a
function you own is fine when clearer or measurably faster; mutating
parameters or shared state is action at a distance.
