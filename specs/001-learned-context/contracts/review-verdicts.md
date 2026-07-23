# Contract: Review and evolve skills

Both are user-invoked skills (canonical in `skills/`, reachable as
`/instinct-review` and `/evolve`). They are the ONLY actors that move
instinct files between states (besides a human moving files by hand, which
the design treats as equivalent — the gate is the directory, not the tool).

## `/instinct-review`

**Precondition**: resolves the store like every consumer
([store-layout.md](store-layout.md)). No pending instincts ⇒ say so, also
report any invariant warnings (status/directory mismatch, malformed files),
and stop.

**Per pending instinct, in `created` order**, present:

1. the instinct (trigger, action, confidence, evidence);
2. **overlap report** — the skill greps for related content in: rule packs
   (`rules/`), skill names/descriptions (`skills/*/SKILL.md` frontmatter),
   project instructions (`CLAUDE.md`/`AGENTS.md`), platform memory index
   (`MEMORY.md` if present), and existing instincts in all states. Matches
   are quoted with file paths — this is the dedup mechanism (FR-008);
3. the four verdicts (one question, user chooses):

| Verdict | File effect | Side effects |
|---|---|---|
| **Approve** | move `pending/<id>.md` → `approved/` | `last-confirmed` ← today; `status: approved`; backup mirror; append `## Review notes` line |
| **Improve then approve** | user/skill edits content, then as Approve | edits summarized in `## Review notes` |
| **Absorb** | move → `rejected/` with note naming the absorbing target | the edit to the existing rule/skill/doc is *proposed* as a normal working-tree change for the user to review — never auto-committed |
| **Reject** | move → `rejected/` | none; archive prevents re-proposal (FR-007) |

**Postcondition**: decisions take effect next session (US3). The skill
never touches `approved/` except via an explicit verdict, and never edits
files outside the store except as proposed working-tree changes.

## `/evolve`

**Precondition**: ≥ 2 approved instincts sharing a `domain` (or an explicit
user-named cluster). Otherwise: report nothing to evolve.

**Behavior**:

1. cluster approved instincts by `domain` + trigger similarity (string
   grouping, no ML); present clusters and let the user pick;
2. generate a draft canonical asset in the working tree — a new/edited
   rule file under `rules/` or skill under `skills/` matching repo
   conventions (CONTRIBUTING.md), carrying provenance:
   `evolved_from: [<instinct-ids>]` in frontmatter or header comment;
3. the draft goes through normal git review — the skill NEVER commits,
   pushes, or merges;
4. **retirement is a separate, explicit step**: after the user confirms the
   asset merged, `/evolve --retire <asset-path>` (or re-running the skill,
   which detects merged provenance) moves the source instincts
   `approved/` → `retired/`, sets `status: retired` and `evolved-into`,
   and mirrors to backup. No automatic retirement on generation — the
   lesson must never be in limbo (out of `approved/` while its asset is
   still an unmerged draft).

**Postcondition**: retired instincts no longer load (FR-012, US4 scenario
2); provenance is traceable in both directions (asset lists instinct ids;
instinct points at asset path).
