---
name: parallel-agents
description: Orchestrates work across parallel subagents — decides when fanning out beats working solo, decomposes tasks into independent lanes with non-overlapping write surfaces, writes self-contained subagent briefs (objective, context transplant, interfaces, boundaries, output contract), routes model and effort per task, tracks progress in a ledger that survives compaction, verifies results instead of trusting reports, and maps a Spec Kit tasks.md ([P] markers, phases, user stories) onto parallel lanes. Use whenever work could be split across agents or verified by independent reviewers — the user mentions subagents, agent teams, fan-out, parallel implementation/research/review, dispatching agents, worktrees for concurrent work, or says "chạy song song", "chia việc cho nhiều agent", "nhiều agent cùng làm" — including when the right answer is that parallelism is NOT worth it. For git worktree mechanics use git-workflow; for general prompt craft use prompt-guru.
---

# Parallel Agents

Subagents buy two things: **concurrency** on independent work, and **isolation**
— a fresh context that sees exactly what you give it, keeping your own context
free for coordination. Both are real, and both have a price: every dispatch is a
context handoff you must construct, and every result is a claim you must verify.
This skill is about paying that price only where it buys something.

**Core principle:** one agent per independent problem; evidence over reports;
the reviewer never wrote the code it reviews.

## Decide: fan out or work solo

Parallelize only when the work passes the **independence test**:

- Each piece can be understood and completed without the others' context.
- No two pieces write to the same files (disjoint write surfaces).
- No piece consumes another's output (that's a pipeline, not a fan-out).

Fan-out is expensive before it is fast: a subagent burns roughly 4× the tokens
of doing the work inline, and a full multi-agent session ~15× a single-agent
one (Anthropic's production numbers). The spend must buy wall-clock speed,
isolation, or independent judgment — otherwise solo wins on cost too. Scale the
fleet to the question:

- **One clear question or a single-file edit** → solo; dispatch overhead
  exceeds the work.
- **Bounded comparison or research** → 2–4 agents, one per facet.
- **Broad audit, migration, or many independent failures** → one agent per
  subsystem or failure domain — grouped by cause, never one per file.

Work solo when tasks are coupled (fixing one failure may fix the others) or the
task needs whole-system understanding. Reads are always safe to parallelize;
writes are what need discipline. Deciding *not* to fan out is a valid outcome
of this skill: say so and continue inline.

Isolation itself is a choice, not a default virtue: when a helper should
*continue* your reasoning — same context, no transplant — use a forked subagent
(inherits the full conversation) rather than a briefed fresh one.

## Decompose into lanes

Build the dependency graph before dispatching anything. For each lane note:
what it does, its **write surface** (files/dirs it may touch), and how its
result will be verified. Two lanes may run concurrently only if their write
surfaces don't collide — and only modes with isolated workspaces guarantee
that; shared-workspace modes (agent teams) don't partition writes for you,
so you must.

- Prefer fewer, cohesive lanes — every boundary you draw is a merge you must do.
- Give each lane an **interface contract**: the exact signatures, schemas, or
  file formats it consumes and produces, copied into its brief. This is the
  mechanism that lets a context-isolated lane still fit its neighbors.
- Divide the space explicitly: sibling briefs that are each individually clear
  but mutually vague produce duplicate work — two research agents running the
  same searches. Each brief states what the *other* lanes own.
- Keep tests with the implementation they test; never split "implement X" and
  "test X" into sibling lanes (the pair is self-verifying; separated, neither is).
- Sequential dependencies stay sequential. Don't force a pipeline into a fan-out
  for the feeling of speed.

## The brief

A subagent has zero memory of your conversation. Its brief must be
self-contained, with six parts:

1. **Objective** — one sentence, narrow. "Research X" is not a brief.
2. **Context transplant** — every fact it needs: error messages, file paths,
   decisions already made. But *transplant*, don't *dump*: pasting session
   history into a dispatch is the classic failure (real sessions have hit 40k+
   characters of which 99% was history). The agent needs its task, its
   interfaces, and the global constraints. Nothing else.
3. **Interfaces** — what the lane consumes and produces, as exact signatures
   (from the decomposition step).
4. **Tool and source guidance** — where to look, what to avoid.
5. **Boundaries** — scope fences against sibling lanes: "fix the tests; do NOT
   change production code", "lane 2 owns src/api/ — stay out". Without fences,
   agents helpfully refactor into each other or duplicate each other's work.
6. **Output contract** — exact return shape, a length cap ("status, root cause,
   files changed as file:line — under 200 words"), and a **status field** from
   a fixed vocabulary (below). Without a contract you get pages of narration
   that pollute your context — everything a subagent prints back stays resident
   for the rest of the session.

For large artifacts, hand over **files, not pasted text**: write the brief to a
file, have the agent write its report to a file, keep only paths and one-line
summaries in conversation.

## Dispatch and track

- Issue all independent dispatches **in the same message** — that is what makes
  them parallel; one per message is sequential with extra steps.
- **Specify the model explicitly on every dispatch** — an omitted model
  inherits your session's, usually the most capable and most expensive. Route
  capability to difficulty: mechanical, fully-specified tasks go to fast/cheap
  models; judgment, integration, and the final review go to the most capable
  one. But turn count beats token price: a cheap model that takes 3× the turns
  on multi-step work costs more — use cheap tiers only when the task is
  near-transcription.
- Parallel *writers* need isolated workspaces — separate worktrees, one per lane
  (mechanics in **git-workflow**). Before dispatching a writer, **record its
  BASE commit SHA**; its work is later reviewed as BASE..HEAD, never `HEAD~1`
  (a multi-commit lane silently loses commits from that diff).
- **Keep a progress ledger** in a file, not just in conversation: one line per
  completed lane ("lane 3: done, commits abc1234..def5678, verified"). Context
  gets compacted; the ledger and git are what survive. The most expensive
  observed failure mode is an orchestrator that lost its place and re-dispatched
  finished work — before dispatching, check the ledger.
- **Handle each status differently.** DONE → verify (next section).
  DONE_WITH_CONCERNS → read the concerns and triage before merging.
  NEEDS_CONTEXT → supply the missing fact and re-dispatch. BLOCKED → escalate
  the model tier or shrink the scope — never blind-retry: unchanged input
  re-runs the same failure. An agent that escalates is working correctly, and
  bad work is worse than no work.
- Between lanes, keep going — don't pause to ask "should I continue?". Stop
  only for BLOCKED, genuine ambiguity, or completion.

## Executing a spec's tasks in parallel

When the work comes from a Spec Kit feature (a `tasks.md` generated by
**speckit-tasks**), the artifacts map directly onto this skill:

- **`[P]` markers are candidates, not verdicts.** `[P]` promises different
  files and no dependency on incomplete tasks — re-run the independence test
  anyway, and derive each lane's write surface and interface contract yourself;
  the marker doesn't carry them.
- **Phase boundaries are barriers.** Verify a phase's lanes at the integrated
  state before dispatching the next phase; user-story groupings (`[US1]`…) make
  natural lane bundles that can ship independently.
- **`tasks.md` checkboxes are the ledger.** Tick a task when its lane is
  *verified*, not when the report arrives — the spec directory stays the single
  durable record of progress, so a compacted orchestrator resumes from it.
- **Pre-flight the plan once.** Before dispatching anything, scan for tasks
  that contradict each other or the global constraints; present all findings
  to the user as one batched question — not one interrupt per discovery
  mid-execution. A clean scan proceeds without comment.
- **The plan feeds the briefs — sliced, not whole.** Hand each lane its own
  task's text plus the plan's global constraints copied verbatim; never make a
  lane read the entire plan file. The spec's acceptance criteria go to the
  reviewer — that is what its spec-compliance verdict is judged against.
- **Sequential (non-`[P]`) tasks stay one-at-a-time.** A failed sequential task
  halts the line; a failed `[P]` lane doesn't block its siblings but is triaged
  before anything merges.

## Verify, don't trust

A subagent's report is an unverified claim about its work — often optimistic,
sometimes wrong. "Done" in a report and done in the repo are different facts.

- Verify against the artifact: read the BASE..HEAD diff, run the suite, check
  that claimed commits exist. Rationales in the report ("kept it simple
  deliberately") are the agent grading its own work — judge the code, not the
  narration.
- **Separate authorship from review.** The reviewer must be a fresh agent that
  never wrote the code — self-review shares the biases that produced the bugs.
  A review report answers two separate questions — *does it meet the spec* and
  *is the code good* — and a report missing either verdict is incomplete.
- Independence is about failure modes, not model names: two reviewers on
  different vendors' models still err together (~60% error correlation, even
  cross-provider). Buy real independence with different *lenses* — spec
  compliance vs. security vs. performance — and different evidence. Collect
  verdicts independently **before** any cross-discussion: panels anchor on the
  first vote, so deliberation mostly launders it. Treat one reviewer's catch as
  a real finding — the other's blind spot is exactly what independence exists
  to expose.
- Never tell a reviewer what *not* to flag or pre-rate a finding's severity —
  that is pre-judging the review to spare yourself a loop.
- When a review returns findings, dispatch **one** fix agent with the complete
  list — per-finding fixers each rebuild context and re-run suites, costing more
  than the original work. After the fix, **re-review**; a fix wave that skips
  re-review is an unverified claim like any other.
- Per-lane review is a task-scoped gate; finish with **one whole-branch
  review** at the integrated state — most capable model, full
  MERGE_BASE..HEAD diff handed as a file, plus the accumulated Minor findings
  from per-lane reviews for triage (a roll-up nobody reads is a silent
  discard). Run the full suite there too: lanes that each passed alone can
  still conflict semantically. Spot-check even clean-looking results — agents
  make *systematic* errors, so one bad lane suggests checking its siblings for
  the same mistake.

## Failure modes

- **Agent soup** — many agents running, no owner, no merge condition per lane.
- **Overlapping writes** — two lanes editing the same file without worktrees;
  detected only at merge, paid for twice.
- **Duplicate work** — sibling briefs that don't divide the space; two agents
  quietly doing the same research at 4× cost each.
- **History dumping** — the brief is the session transcript; the agent drowns.
- **No output contract** — pages of narration nobody asked for, resident in your
  context forever.
- **Trusting reports** — integrating "done" claims without reading a diff.
- **Pseudo-independent review** — reviewers with the same prompt, same lens,
  and correlated models sharing one blind spot; independence in name only.
- **Blind retry** — re-dispatching a failed lane unchanged.
- **Re-dispatching finished work** — no ledger, compacted context, paying twice.

## Boundaries

- Worktree creation, merging, conflict resolution → **git-workflow**.
- Crafting the brief's prose (a brief is a prompt) → **prompt-guru**.
- Implementer agents follow **tdd** — and the test-writer/implementer/reviewer
  split across separate agents is that skill's strongest structural gate.
- Task breakdown for a planned feature → **speckit-tasks**; this skill then
  executes those tasks as lanes (see "Executing a spec's tasks in parallel").
- What each *research* lane does inside its context → **research**; this skill
  owns the split and the merge.
