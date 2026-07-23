# Branches and Worktrees

Contents: harness first · branches · creating a worktree · parallel agents · finishing a branch · cleanup gate.

## Never fight the harness

If the coding harness has a native workspace/worktree mechanism (a worktree tool, `/worktree` command, isolated-workspace option), use it. Raw `git worktree add` behind the harness's back creates state it can't see or manage — the most common worktree mistake. Fall back to raw git only when no native mechanism exists.

## Branches

Branch per task from a verified base. Follow repo naming policy; absent one, use `<type>/<kebab-description>`:

| Type | For | Example |
|---|---|---|
| `feat/` | new behavior | `feat/cache-warming` |
| `fix/` | bug fix | `fix/token-refresh` |
| `refactor/` | no behavior change | `refactor/extract-billing-client` |
| `chore/` | tooling, deps, config | `chore/bump-node-22` |
| `docs/` `test/` | docs / tests only | `docs/api-pagination` |

Name the change, not the ticket ID alone (`fix/login-timeout`, not `fix/JIRA-1234`). Detect the default branch rather than guessing:

```bash
git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||'
# fallback if origin/HEAD is unset:
for b in main master develop; do git show-ref --verify -q "refs/heads/$b" && { echo "$b"; break; }; done
```

Record the base SHA before starting work. Give detached-HEAD work a durable branch before it can expire.

## Creating a worktree (when isolation is needed)

Isolate when your work overlaps dirty state you don't own, runs concurrently with another writer, or risky debugging needs its own surface.

Preflight: linked-worktree/submodule detection (safety-and-state.md); confirm the target branch isn't checked out in another worktree — git refuses one branch in two worktrees; don't force it. Location: follow existing convention (`.worktrees/`, `worktrees/`, or a sibling directory). A path inside the repo must be gitignored — prove it with `git check-ignore <path>` before creating; if it isn't, add it to `.gitignore` and commit that first.

After `git worktree add`, verify with `git worktree list`, then make the tree runnable — gitignored files don't follow the checkout:

- copy `.env`/`.env.local` from templates, adjusting per-worktree values;
- install dependencies (each worktree gets its own `node_modules`; pnpm-style shared stores dedupe the cost);
- offset dev-server and database ports per worktree — port collisions are the top parallel-worktree failure;
- run the test baseline. If it fails before you've changed anything, stop and report: you can't distinguish your bugs from pre-existing ones.

## Parallel agents

Two writers sharing one worktree/index silently overwrite each other's staged changes — a Git limitation, not a policy choice. One owner per worktree/index/branch.

Partitioning is decided at plan time, not by git: split tasks so no two agents write the same files; agree up front on shared surfaces (interfaces, schemas, lockfiles, migrations, formatter sweeps); run one validation pass on the merged result at the end. Another agent may read a worktree but must not stage, switch, reset, or clean it without an explicit handoff (HEAD, status, commits, tests, base assumptions).

## Finishing a branch

When implementation is done, require passing tests first — a failing suite blocks the whole menu. Then present exactly these options instead of an open question:

1. Merge back into the default branch locally
2. Push and create a PR
3. Keep the branch as-is for now
4. Discard this work

For discard: show what dies first (branch name, `git log --oneline base..HEAD`, worktree path) and require the user to literally type `discard`.

Ordering invariants for option 1 — each step exists because the next fails without it:

```bash
cd <main checkout root>                         # not inside the worktree being removed
git switch <default> && git merge --no-ff <branch>
<run tests on the merged result>                # the branch passing ≠ the merge passing
git worktree remove <path>                      # fails when CWD is inside it
git branch -d <branch>                          # fails while a worktree still holds the branch
git worktree prune
```

For option 2, keep the worktree alive — it's needed to iterate on review feedback.

## Cleanup gate

Deleting worktrees and branches is one of the few genuinely irreversible git actions once reflog expires. Remove only what you created (your `.worktrees/` entries, your task branches), and only after proving: no active user or process in the path; clean status including untracked files; every unique commit reachable from a durable branch/tag/remote ref; no nested repository or submodule inside. Don't use `--force` to erase unexplained dirt. `worktree remove`, local `branch -d`, and remote branch deletion are three separate decisions — remote deletion needs its own authority.

Finding candidates safely:

```bash
git fetch -p                                  # drop tracking refs for branches already deleted on the remote
git branch --merged <default>                 # branches whose every commit is reachable from <default> — safe for -d
```

Caveat: in squash-merge repos `--merged` misses merged branches (the squash commit is new; the branch's commits stay unreachable), and `branch -d` will refuse. Verify via the PR's merged state instead, then deletion is `-D` — which makes it a destructive action needing the proof above, not a convenience.
