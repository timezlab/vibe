---
name: parallel-agents
description: Orchestrates work across parallel subagents — decides when fanning out beats working solo, decomposes tasks into independent lanes with non-overlapping write surfaces, writes self-contained subagent briefs (objective, context transplant, boundaries, output contract), routes model and effort per task, tracks progress in a ledger that survives compaction, and verifies results instead of trusting reports. Use whenever work could be split across agents or verified by independent reviewers — the user mentions subagents, agent teams, fan-out, parallel implementation/research/review, dispatching agents, worktrees for concurrent work, or says "chạy song song", "chia việc cho nhiều agent", "nhiều agent cùng làm" — including when the right answer is that parallelism is NOT worth it. For git worktree mechanics use git-workflow; for general prompt craft use prompt-guru.
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

Work solo when tasks are coupled (fixing one failure may fix the others), when
the task needs whole-system understanding, or when it's a single-file edit —
dispatch overhead exceeds the work. Reads are always safe to parallelize;
writes are what need discipline. Deciding *not* to fan out is a valid outcome of
this skill: say so and continue inline.

## Decompose into lanes

Build the dependency graph before dispatching anything. For each lane note:
what it does, its **write surface** (files/dirs it may touch), and how its
result will be verified. Two lanes may run concurrently only if their write
surfaces don't collide.

- Prefer fewer, cohesive lanes — every boundary you draw is a merge you must do.
- Keep tests with the implementation they test; never split "implement X" and
  "test X" into sibling lanes (the pair is self-verifying; separated, neither is).
- Sequential dependencies stay sequential. Don't force a pipeline into a fan-out
  for the feeling of speed.

## The brief

A subagent has zero memory of your conversation. Its brief must be
self-contained, with five parts:

1. **Objective** — one sentence, narrow. "Research X" is not a brief.
2. **Context transplant** — every fact it needs: error messages, file paths,
   interface signatures, decisions already made. But *transplant*, don't *dump*:
   pasting session history into a dispatch is the classic failure (real sessions
   have hit 40k+ characters of which 99% was history). The agent needs its task,
   the interfaces it touches, and the global constraints. Nothing else.
3. **Tool and source guidance** — where to look, what to avoid.
4. **Boundaries** — scope fences against sibling lanes: "fix the tests; do NOT
   change production code", "only touch src/api/". Without fences, agents
   helpfully refactor into each other.
5. **Output contract** — exact return shape and a length cap ("status, root
   cause, files changed as file:line — under 200 words"). Without a contract you
   get pages of narration that pollute your context. Everything a subagent
   prints back stays resident in your context for the rest of the session.

For large artifacts, hand over **files, not pasted text**: write the brief to a
file, have the agent write its report to a file, keep only paths and one-line
summaries in conversation.

## Dispatch and track

- Issue all independent dispatches **in the same message** — that is what makes
  them parallel; one per message is sequential with extra steps.
- Parallel *writers* need isolated workspaces — separate worktrees, one per lane
  (mechanics in **git-workflow**). Parallel *readers* (research, review) share
  the repo freely.
- **Keep a progress ledger** in a file, not just in conversation: one line per
  completed lane ("lane 3: done, commits abc1234..def5678, verified"). Context
  gets compacted; the ledger and git are what survive. The most expensive
  observed failure mode is an orchestrator that lost its place and re-dispatched
  finished work — before dispatching, check the ledger.
- **Route capability to difficulty.** Mechanical, fully-specified tasks go to
  fast/cheap models; judgment, integration, and the final review go to the most
  capable one. But turn count beats token price: a cheap model that takes 3× the
  turns on multi-step work costs more — use cheap tiers only when the task is
  near-transcription.
- **When a lane fails, change something before re-dispatching**: more context,
  a more capable model, or a smaller scope. Blind retry re-runs the same
  failure. If the agent says it's stuck, believe it — an agent that escalates is
  working correctly, and bad work is worse than no work.

## Verify, don't trust

A subagent's report is an unverified claim about its work — often optimistic,
sometimes wrong. "Done" in a report and done in the repo are different facts.

- Verify against the artifact: read the diff, run the suite, check that claimed
  commits exist. Rationales in the report ("kept it simple deliberately") are
  the agent grading its own work — judge the code, not the narration.
- **Separate authorship from review.** The reviewer must be a fresh agent that
  never wrote the code — self-review shares the biases that produced the bugs.
  For results that matter, use two independent reviewers with no shared context
  and treat one catch as a real finding: the other reviewer's blind spot is
  exactly what independence exists to expose.
- Never tell a reviewer what *not* to flag or pre-rate a finding's severity —
  that is pre-judging the review to spare yourself a loop.
- When a review returns findings, dispatch **one** fix agent with the complete
  list — per-finding fixers each rebuild context and re-run suites, costing more
  than the original work.
- After merging parallel lanes, run the full suite once at the integrated state;
  lanes that each passed alone can still conflict semantically. Spot-check even
  clean-looking results — agents make *systematic* errors, so one bad lane
  suggests checking its siblings for the same mistake.

## Failure modes

- **Agent soup** — many agents running, no owner, no merge condition per lane.
- **Overlapping writes** — two lanes editing the same file without worktrees;
  detected only at merge, paid for twice.
- **History dumping** — the brief is the session transcript; the agent drowns.
- **No output contract** — pages of narration nobody asked for, resident in your
  context forever.
- **Trusting reports** — integrating "done" claims without reading a diff.
- **Blind retry** — re-dispatching a failed lane unchanged.
- **Re-dispatching finished work** — no ledger, compacted context, paying twice.

## Boundaries

- Worktree creation, merging, conflict resolution → **git-workflow**.
- Crafting the brief's prose (a brief is a prompt) → **prompt-guru**.
- Implementer agents follow **tdd** — and the test-writer/implementer/reviewer
  split across separate agents is that skill's strongest structural gate.
- Task breakdown for a planned feature → **speckit-tasks**; this skill then
  executes those tasks as lanes.
