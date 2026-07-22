# Docs Structure — Layout, Scaffolding, Rationale

The tree below is the convergence of the practices of Google (g3doc / SWE book ch.10), GitLab (docs-as-code SSoT), Spotify (Backstage TechDocs), the Diátaxis framework (Canonical, Django, Cloudflare), and the ADR tradition (Nygard, MADR, AWS, Microsoft) — adapted for repos where the primary doc reader is a coding agent. Structured docs measurably pay off for agents: Mintlify's 2026 benchmark found agents with structured docs were ~64% more precise and used ~half the tokens per task.

## Contents
1. The full tree
2. What each location is for
3. Minimum scaffold (day one)
4. ARCHITECTURE.md conventions
5. Naming conventions
6. Design rationale — the three axes

---

## 1. The full tree

```
repo/
├── README.md                  # human entry: what/why, quickstart, links into docs/
├── AGENTS.md                  # agent entry: ≤150 lines, routing table (CLAUDE.md mirrors it)
├── ARCHITECTURE.md            # module map + dependency direction — one page
├── .specify/                  # Spec Kit engine (see speckit.md)
├── specs/NNN-<feature>/       # ephemeral per-feature spec/plan/tasks
└── docs/
    ├── index.md               # map of the docs — navigation only
    ├── decisions/             # ADRs: NNNN-<topic>.md — append-only
    ├── product/               # product specs, DESIGN.md
    ├── guides/                # how-to: setup, deploy, debug, release
    ├── reference/             # dry facts: per-project lib usage, config, schemas
    ├── concepts/              # explanation: domain concepts, background
    └── tech-debt.md           # flat grep-able debt log
```

## 2. What each location is for

**`README.md`** — for humans *finding* the project: what it is, quickstart, links. Entry point, not documentation. Per-package READMEs sit next to their code (purpose, status, usage, links), not inside `docs/`.

**`AGENTS.md` / `CLAUDE.md`** — for agents *working in* the project. A map to the documentation, never the documentation itself. Full discipline: `agents-md.md`.

**`ARCHITECTURE.md`** — "what lives where, what may import what." Conventions in §4.

**`docs/index.md`** — navigation hub: one line + link per doc. Landing pages that scroll or explain have failed (Google's landing-page rule). This is also where an agent that doesn't know the tree starts.

**`docs/decisions/`** — ADRs, `NNNN-<topic>.md`, append-only, superseded-not-edited. The highest-value directory in the repo: code shows *what*, only decisions show *why*. Format: `adr.md`.

**`docs/product/`** — product direction: `DESIGN.md` (where the product is heading, current phase, explicit non-goals) plus per-feature product specs. Product intent and technical decisions live apart because they have different authors and lifecycles.

**`docs/guides/`** — task-oriented how-tos: "set up local dev", "deploy to staging", "debug the websocket layer", "cut a release". One task per file, steps that work every time (Diátaxis "how-to guides").

**`docs/reference/`** — dry lookup facts, structured to mirror the code: how *this project* uses each library (`<lib>.md` — template in `agent-readable.md`), config/env matrices, schemas, CLI surfaces. No narrative, no persuasion — reference is where agents grep mid-task.

**`docs/concepts/`** — understanding-oriented background: domain glossary, "how billing states flow", mental models (Diátaxis "explanation"). Most repos need this last — create it when the first real concept doc exists.

**`docs/tech-debt.md`** — one flat file (entry format: `spec-authoring.md` §6). Flat is intentional: agents grep it, they don't browse it.

**Deliberately absent — `docs/tutorials/`.** The fourth Diátaxis quadrant serves newcomers learning by guided lesson. Internal repos rarely need it (onboarding narrative → CONTRIBUTING.md); add only when the project gains external users who learn it from scratch.

## 3. Minimum scaffold (day one)

Create only what has real content today:

```
README.md                    # human entry — even 15 lines: what this is, quickstart, link to docs/
AGENTS.md                    # write this first — 100 lines, routing table (skeleton: agents-md.md)
ARCHITECTURE.md              # one page: package map + dependency rules
.specify/                    # specify init . --integration claude
docs/
├── index.md                 # even 10 lines — the map must exist before the territory
├── decisions/0001-<first-real-decision>.md    # template: adr.md
└── tech-debt.md             # header + the entry fields as a comment: Where / Symptom / Why deferred / Trigger to fix / Created
```

Greenfield notes (empty repo):
- The "first real decision" already exists: the stack and process choices being made right now (runtime, framework, adopting spec-driven development) are ADR material. Capture one of those — a real decision made today, not a placeholder for a future one.
- ARCHITECTURE.md may describe the *intended* shape before code exists — label it as such ("intended shape; update when the first package lands"). That label is what separates it from the wishlist content banned in hot files.

Add `product/`, `guides/`, `reference/`, `concepts/` only when the first real doc for each exists. Every doc added later gets a line in `index.md` in the same commit — an unindexed doc is invisible to agents that navigate by the map.

## 4. ARCHITECTURE.md conventions

One page, flat and dense — an agent reads this to answer "where does X belong?" in 30 seconds.

Required sections:
1. **Package map** — table, one line per package:

   | Package | Purpose | May import from |
   |---------|---------|-----------------|
   | `core` | Pure types, constants | (nothing) |
   | `domain` | Business rules | `core` |
   | `app` | Orchestration, I/O | `core`, `domain` |
   | `cli` | User-facing entry | `app` |

2. **Dependency direction** — one sentence: "core → domain → app → cli; never reverse."
3. **Key boundaries** — modules that must stay pure / must not touch I/O / etc.

Avoid: ASCII diagrams >15 lines (they rot), class-level detail (belongs in source docstrings), historical narrative ("we used to use X") — that's ADR territory.

## 5. Naming conventions

- Feature folders: `specs/NNN-<kebab-slug>/` (`specs/001-auth-rewrite/`) — sequential, never reused
- ADRs: `docs/decisions/NNNN-<kebab-topic>.md` (`0007-token-storage.md`) — MADR convention, numbered append-only
- Guides: `docs/guides/<verb-phrase>.md` (`deploy-staging.md`, `debug-websockets.md`)
- Reference: `docs/reference/<lib-or-subject>.md` (`drizzle.md`, `env-vars.md`)
- Dates go in the doc body (`Created:` / `Status:` headers), not filenames — filenames are stable anchors agents link to

Consistency beats any particular convention: agents build mental maps from filename patterns.

## 6. Design rationale — the three axes

The tree is the intersection of three classification systems; knowing them tells you where anything new belongs:

- **Reader-mode axis (Diátaxis):** guides = how-to, reference = lookup, concepts = explanation, decisions ≈ explanation-of-the-past. Mixing modes in one doc ("a how-to that argues", "a reference that teaches") is the root cause of confusing docs.
- **Context-tier axis (agent cost):** hot (AGENTS.md, loads every session — every line taxes every task) → warm (ARCHITECTURE.md, active spec) → cold (all of `docs/`, loaded on demand via the routing table). This is the same three-level progressive disclosure Anthropic uses for Agent Skills.
- **Lifecycle axis:** `specs/` die with their feature; `docs/decisions/` is immutable history; everything else in `docs/` is living and updates in the same PR as the code.

One more convergent finding worth internalizing: **discoverability is half the problem** (Spotify's #3 engineer complaint was "can't find docs", Google's was worse). A predictable tree + a maintained `index.md` + a routing table in AGENTS.md is the discoverability layer. Content quality doesn't matter if the reader never finds the file.
