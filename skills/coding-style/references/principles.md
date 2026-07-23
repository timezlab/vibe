# Principles — the why behind the rules

Read this when asked to justify, debate, or adapt a style rule. Each
section states the principle, the reasoning, and its strongest sources.
The rules packs encode the *conclusions*; this file carries the evidence.

## Contents

1. Where these rules come from
2. Reading-first and deep modules
3. Duplication: DRY, rule of three, locality of behavior
4. Comments
5. Organize by feature, layer only under pressure
6. Errors: silent failure and fail-open
7. Performance and "clean" structure
8. Style for AI-maintained code
9. Contested — deliberately not encoded
10. Sources

## 1. Where these rules come from

Three inputs, in priority order:

1. **Cross-guide consensus** — rules that appear independently in the
   Google (TS/Python/Go), Uber Go, and Shopify guides and in Google's
   eng-practices: automate formatting, comment the why, never swallow
   errors, small single-purpose units, casing mapped to semantic role.
2. **The modern critique** — where 2018–2026 evidence overturned older
   Clean Code doctrine (function-size quotas, comments-as-failure,
   reflexive DRY), the newer position wins (§2–4).
3. **Deliberate local conventions** — kebab-case filenames, named exports,
   schema-as-type are taste choices with real justifications, applied
   because consistency across this team's repos beats per-repo
   re-litigation.

Where top-tier guides genuinely disagree (§9), the rules stay silent — an
agent enforcing a contested rule as consensus loses trust.

The classic acronyms are all present, refined rather than recited:

| Classic | Where it lives | Refinement |
|---|---|---|
| Readability first | common § Reading beats writing | Unchanged — the root principle |
| KISS | common § Simplicity; SKILL.md priority ladder | Unchanged |
| DRY | common § Duplication and abstraction | Target is *knowledge*, not text; bounded by rule of three and locality of behavior (§3) |
| YAGNI | common § Simplicity; § Functions and modules | Unchanged |
| "Self-documenting code over comments" | **rejected** | The comments-as-failure doctrine lost the 2025 debate (§4); the rules require why-comments instead |

The rules skip acronym-definition blocks because always-on files pay for
every line in every session, and a strong model already knows what
KISS/DRY/YAGNI expand to — what it needs are the decision thresholds
(when to extract, when to add a layer), which is what the sections encode.

## 2. Reading-first and deep modules

Code is read far more than written; "software engineering is programming
integrated over time" (Software Engineering at Google, ch. 1). Every rule
downstream optimizes the reader's experience, not the writer's.

The unit of quality is the **deep module**: a small interface hiding real
implementation complexity (Ousterhout, *A Philosophy of Software Design*).
The inverse — shallow modules whose interface is as complex as their
implementation — adds indirection without hiding anything. This is why the
rules reject line-count quotas: in the 2025 Ousterhout–Martin dialogue,
Martin's own `PrimeGenerator` (decomposed per Clean Code's "functions
should hardly ever be 20 lines") proved hard for its author to re-read 18
years later, and he conceded the point in part. Split when a reader can no
longer hold one idea; never to satisfy a number.

## 3. Duplication: DRY, rule of three, locality of behavior

- **DRY's real target is knowledge**, not text (business rules, constants,
  schemas defined once). Two pieces of code that look alike but encode
  different decisions are not duplication — merging them couples things
  that change for different reasons.
- **Rule of three**: abstract on the third occurrence. One occurrence is a
  fact, two are a coincidence, three reveal the shape. Abstracting at one
  bakes that instance's accidents into the abstraction.
- **Locality of behavior** (Gross, htmx essays): the behavior of a unit
  should be obvious from looking at that unit. LoB and DRY genuinely
  conflict at the margin; when they do, a little visible duplication beats
  logic scattered across files — doubly so for code AI agents maintain
  (§8).
- **Hyrum's Law**: with enough users, every observable behavior of an API
  becomes a contract. This is the argument for small, deliberate public
  surfaces (named exports, explicit signatures) — everything you expose,
  someone will depend on.

## 4. Comments

The Clean Code position ("comments are always failures") is now the
minority view. Ousterhout's counter — the cost of *missing* comments is
10–100× the cost of stale ones, because rationale and invariants are a
layer of information no identifier can carry — held up better in their
2025 dialogue; Martin conceded public interfaces need them.

Encoded as: comment the why (constraints, invariants, trade-offs), never
the what. The strongest form is the **provenance comment**: link the
incident, spec item, or issue that forced non-obvious code —

```python
# Plain `operator.add` made the per-turn reset a no-op (old + [] == old),
# so results leaked across turns (010 T4/T5).
```

— which turns the comment into an audit trail a future reader (or agent)
can verify rather than trust.

## 5. Organize by feature, layer only under pressure

- Group code so that **what changes together lives together** (Shopify
  calls the metric "change locality"). Feature/domain directories deliver
  this; layer-first trees (`controllers/`, `services/`, `models/` at top
  level) scatter each feature across the tree.
- Layered/hexagonal/onion abstraction earns its cost only where domain
  logic is genuinely complex. Applied by default to CRUD it is speculative
  generality — the counter-movement is vertical slices (Bogard): maximize
  coupling within a slice, minimize it between slices.
- Default to a modular monolith with enforced boundaries (Shopify: 37
  components, dependency graph enforced in CI); extract a service only for
  a named reason — independent scaling, compliance isolation, an org
  boundary — never as the default shape.

## 6. Errors: silent failure and fail-open

The one rule every surveyed guide shares, each in its own idiom: Google TS
(empty catch requires justification), Google Python (no bare `except`),
Uber Go (handle each error exactly once), Shopify Ruby (no bare `rescue`).
Silent failure converts bugs into mysteries.

The sharpest special case is **fail-open**: a validation, review, or auth
step that defaults to "pass" when it errors. Observed in the wild as a
review node whose `except Exception` returned `review_status: "pass"` —
making an LLM timeout indistinguishable from a passed review, in the exact
component the product's trust story depended on. On safety-relevant paths
an error must produce reject/retry; fail-open is reserved for genuinely
best-effort side work and labeled as such in a comment.

## 7. Performance and "clean" structure

Structural virtue has runtime cost: Muratori measured order-of-magnitude
differences between polymorphic dispatch and data-oriented alternatives on
hot paths. The consensus middle: readability defaults are right for most
code *and* are overridable by measurement — a profiled hot path may
justify mutation, tables over polymorphism, or manual memoization, with a
comment saying it was measured. Never pre-optimize on vibes; never dismiss
a measured regression with "but it's cleaner".

## 8. Style for AI-maintained code

Guidance that emerged 2024–2026, consistent across Anthropic, Cursor, and
practitioner writing:

- **Boring, explicit, locally-legible code** is what both agents and
  reviewers parse best; metaprogramming and hidden magic degrade agents
  disproportionately.
- **Give the agent a runnable check** — formatter, linter, type-checker,
  tests. "Looks done" is the only signal an agent has without one; the
  entire enforcement reference exists because of this.
- **Rules files stay short** — for every line, ask whether removing it
  would cause a mistake; bloated instruction files get diluted and
  ignored (Anthropic's CLAUDE.md guidance — which explicitly names
  "write clean code" as noise to cut; rules must be concrete).
- **Explicit beats tacit**: agents lack the absorbed judgment of a senior
  engineer, so conventions must be written where a human team could rely
  on osmosis (Stack Overflow eng blog, 2026).

Empirical caveat: current agents *over*-produce duplication rather than
over-abstract, so locality-of-behavior guidance is a judgment call, not a
license to copy-paste — the rule of three still governs.

## 9. Contested — deliberately not encoded

Top-tier sources genuinely disagree on these; the rules stay silent, and
so should a reviewer claiming consensus:

- **Function/file size numbers** — any specific limit is taste; depth of
  interface is the test (§2).
- **TDD as universally mandatory** — Martin defends, Ousterhout and
  others push back. This repo's tdd skill applies when implementing;
  whether every spike needs it stays a judgment call the tdd skill itself
  documents.
- **How much duplication is acceptable** — no agreed threshold (§3, §8).
- **Comment density** — the why-not-what direction is consensus; how many
  is not.
- **Prescriptive vs principle-based guides** — Google Go (five ranked
  principles) and Uber Go (dozens of mechanical rules) both work at
  top-tier orgs. These packs choose few-rules-with-whys; that is a choice,
  not a law.
- **Microservices vs monolith at extreme scale** — monolith-first is the
  documented trend, not a universal law.

## 10. Sources

- Winters, Manshreck, Wright — *Software Engineering at Google* (2020),
  ch. 1; Hyrum's Law. abseil.io/resources/swe-book
- Ousterhout — *A Philosophy of Software Design* (2018/2021); deep
  modules, define errors out of existence.
- Ousterhout & Martin — aposd-vs-clean-code dialogue (GitHub, Feb 2025);
  function length, comments, TDD.
- Google style guides — google.github.io/styleguide (TS, Python, Go);
  eng-practices (small CLs, review order, "Nit:").
- Uber Go Style Guide — github.com/uber-go/guide; handle-errors-once, no
  fire-and-forget goroutines.
- Shopify Engineering — modular monolith / Packwerk posts (2019–2020);
  "change locality".
- Bogard — Vertical Slice Architecture. jimmybogard.com
- Gross — Locality of Behaviour (2020). htmx.org/essays
- Muratori — "Clean" Code, Horrible Performance (2022);
  computerenhance.com. Plus Teran's rebuttal (2023).
- Go blog "gofmt" (2013), Prettier option philosophy, Black README —
  formatting-without-debate doctrine.
- Anthropic — Claude Code best practices (CLAUDE.md content rules,
  verification loops). code.claude.com/docs
- Cursor — Best practices for coding with agents (2025–26).
- Stack Overflow blog — Building shared coding guidelines for AI (2026).
- The Grug Brained Developer (grugbrain.dev) — complexity, premature
  abstraction.
