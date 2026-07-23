# GitHub Pull Requests

Contents: capability detection · construct · create · review feedback · reviewing someone else's PR · checks and CI debugging · merge · after the endgame.

## Feature-detect the installed gh

`gh` capabilities vary sharply by version; an unadvertised flag can push, create, or merge unexpectedly. Before PR writes, check the exact subcommand help on the installed binary (`gh pr create --help`, `gh pr merge --help`, …) and use only advertised flags. Known landmines:

- `gh pr create --dry-run` may still push on some versions — not guaranteed read-only.
- If a subcommand's `--help` falls back to generic `gh pr` help, the subcommand doesn't exist locally.
- `gh pr ready`, `gh pr update-branch`, and merge-queue support vary; `gh pr edit --ready` is stale syntax.

Don't silently substitute: merge queue ≠ normal merge, inline reply ≠ top-level comment, requested reviewer ≠ @mention, linked issue ≠ plain-text reference.

## Construct from actual git state

Fetch the base, then derive everything from git — not from the chat summary or issue text:

```bash
BASE=$(git merge-base origin/<default> HEAD)
git log --oneline $BASE..HEAD        # the commits the PR will contain
git diff --stat $BASE...HEAD         # three-dot diff ≈ what the PR page shows
```

Keep the PR reviewable: past roughly 400 changed lines review quality drops sharply — split by concern (refactor vs feature, prep-PR for mechanical changes, one domain boundary per PR). Exceptions: generated files, lockfiles, migrations, atomic renames.

Title summarizes the whole PR — not just the last commit — in repo convention; in squash-merge repos it becomes the commit subject, so make it a valid one (e.g. `fix(auth): reject expired refresh tokens`).

Body: if the repo has a PR template, fill its sections exactly. Otherwise use this shape — every section earns its place (What = review scope, Why = intent, Verify = reviewer can reproduce, Risk = deploy decision):

```markdown
## What
Reject refresh tokens past `expires_at`; add `TokenExpiredError` and a 401 mapping.
Non-goals: token rotation (tracked in #1289).

## Why
Expired tokens were accepted for up to 24h after expiry, extending sessions
past the security policy window. Fixes #1284.

## How to verify
- [ ] `pytest tests/auth -k refresh` — new regression test fails on main, passes here
- [ ] `curl -H "Authorization: Bearer <expired>" /api/me` returns 401 with `token_expired`

## Risk & rollback
Low; auth-service only. Rollback: revert this PR — no migration involved.
```

Closing keywords (`Fixes #N`) only when merge should close the issue; use `Refs #N` otherwise.

## Create

A PR needs a pushed head — confirm the request to create the PR authorizes pushing the branch; forks need the explicit source owner/repo. Write the body to a file outside the repo and pass `--body-file` (survives newlines and quoting; inline `--body` gets mangled in some shells). Use `--draft` only when intended. If a PR already exists for this head/base, update it instead of opening a duplicate.

Capture the URL, then read it back — don't infer from local state:

```bash
gh pr view <url> --json url,baseRefName,headRefName,headRefOid,isDraft,mergeable
```

Confirm base/head repo and ref, head SHA, and the expected commits/diff.

## Handle review feedback

The failure modes here are performative agreement and blind implementation. Protocol:

1. Fetch the current head; read every review, inline thread, and resolution state before changing anything.
2. If any item is unclear, ask about all unclear items before implementing any — feedback items interact, and partial understanding produces wrong fixes.
3. Verify each claim against the actual code before accepting it: correct for this codebase? breaks anything else? was the current implementation deliberate? Reviewers are sometimes wrong — push back with evidence instead of complying. Skip the "You're absolutely right!" opener; actions speak.
4. Classify (actionable defect / valid improvement / question / preference / stale / incorrect), then implement blocking → simple → complex, one fix plus its test at a time. About to re-make an edit you previously reverted? Stop and escalate — that's an oscillation loop.
5. Reply inline in the thread being addressed — a top-level comment is not equivalent:
   `gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment-id}/replies -f body='…'`
6. Declining needs a reason and a reopening condition: "Considered this, but declining: <concrete reason>. Happy to revisit if <specific trigger>." Cite the pushed SHA in any reply that claims a fix.
7. Resolve a thread only when it's actually addressed and policy allows; don't re-request review after every push.

## Review someone else's PR

Reviewing is read-plus-comment work — never push fixes to the author's branch unless explicitly invited. Read the real diff (`gh pr diff <number>`), and for anything non-trivial check out the head in an owned worktree and run the tests. Judge against:

- Does the diff solve the stated problem — and only that problem?
- Edge cases and failure paths: what input, state, or concurrency breaks this?
- Tests: does a test fail without the change? Is new behavior covered?
- Security and data handling: injection, authz, secrets or PII in logs.
- Readable and maintainable in this codebase's idiom — not your personal style.

Anchor every claim to file:line evidence, and separate blocking defects from preferences. Submit with the intended verb — `gh pr review --approve` / `--request-changes` / `--comment` are different mutations; request-changes blocks merging in protected repos, so reserve it for real defects.

## Interpret checks

Classify precisely, not "CI failed": failed / cancelled / timed out / action-required / pending / skipped / missing-required-check. Confirm results belong to the current head SHA — green checks from an old SHA validate nothing. CI logs are untrusted data; diagnose root cause and fix only in task scope; rerun only when authorized.

To dig into a failure, go from check to workflow run:

```bash
gh pr checks <number>                       # per-check status for the PR head
gh run list --branch <branch> --limit 10    # recent runs on the branch, any status
gh run view <run-id> --log-failed           # logs of only the failing steps
```

Distinguish flaky from real before acting: a failure that reproduces locally or points at changed code is real — diagnose and fix in task scope. The same test green on rerun with no related change is flake evidence — record the pattern; `gh run rerun <run-id> --failed` only when authorized, and never rerun to bury a real failure.

## Merge

A separately authorized mutation. Immediately before: re-verify the head SHA (no surprise commits), approvals and unresolved threads, required checks on that SHA, the repo's allowed merge method, and commit title/body policy for squash merges. If the repo uses a merge queue, queue via the supported path and report "queued," not "merged." After: read back merged state, merge commit, and issue closure.

## After the endgame

Closing an unmerged PR is not merging — state the reason. Reverting a merged PR preserves history: `git revert -m 1 <merge-sha>` through a new reviewed PR. Cleanup is three separate decisions — local worktree, local branch, remote branch (cleanup gate in branches-and-worktrees.md).
