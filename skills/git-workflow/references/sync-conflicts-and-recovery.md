# Synchronization, Conflicts, and Recovery

Contents: integrate · fork hygiene · conflicts · push · rewriting history non-interactively · recovery playbook.

## Integrate deliberately

`git pull` immediately integrates according to config — fetch first, then choose the integration on purpose. Choose by repo policy and collaboration state, not aesthetics:

- **Rebase** when updating your own unpublished task branch onto the latest base, or when the repo mandates linear history.
- **Merge** when integrating into a shared branch, or into any branch someone else may have based work on.
- **Never rebase** commits that are published on a shared branch, that others have built on, or that are already merged — the rewrite forces every collaborator to repair their history.

Before any rebase, cherry-pick, or history surgery, preserve the current tip: `git branch rescue/<task> HEAD`.

## Fork hygiene

A fork drifts; sync it from the source repo, not by re-cloning:

```bash
git remote add upstream https://github.com/<owner>/<repo>.git   # once; verify with git remote -v
git fetch upstream
git switch <default> && git merge --ff-only upstream/<default>  # ff-only: a fork's default should carry no unique commits
git push origin <default>
```

If `--ff-only` refuses, the fork's default has local commits — stop and move them to a branch deliberately instead of forcing a merge knot. Task branches then rebase or merge from the updated default as usual.

## Conflicts

Blind `--ours`/`--theirs` sweeps silently drop features. Per conflicted path: read all three sides (base/ours/theirs — the labels flip meaning between merge and rebase, so confirm which side is which before trusting them), reconstruct the intended behavior keeping both sides' compatible changes, remove markers, stage that file, run focused tests. Lockfiles and generated files: don't hand-edit markers — take one side and regenerate with the authoritative tool.

Abort only with the matching command for an operation you own (`git merge --abort`, `git rebase --abort`, …); never delete `.git` state files as an "abort." Verify HEAD and status afterward.

## Push

Before: inspect outgoing commits (`git log @{u}..` or `base..HEAD`) and the three-dot diff; scan for secrets; confirm the remote target (wrong-repo guard in SKILL.md). Push an explicit shape — `git push origin HEAD:refs/heads/<branch>` — then verify: `git ls-remote origin <branch>` matches your SHA.

## Rewriting history (non-interactively)

`git rebase -i` hangs the harness. Non-interactive equivalents:

```bash
GIT_SEQUENCE_EDITOR=true git rebase --autosquash <base>   # apply fixup! commits without an editor
git rebase <base>                                          # plain replay onto a new base
git reset --soft <base> && git commit -F /tmp/msg.txt      # squash everything since base into one commit
```

For published history, default to a follow-up commit. An authorized rewrite runs in this order: fetch → record the old local head and exact remote tip → rescue ref → rewrite → compare series (`git range-diff <old-tip>...HEAD`) and run tests → re-read the remote tip → push with `--force-with-lease=<branch>:<expected-sha>`. A failed lease means someone moved the branch: stop and reassess — never fall back to `--force`. Even a successful lease can't protect review approvals, comment anchors, or a collaborator's unpushed commits.

## Recovery playbook

Committed work is almost never lost; uncommitted work often is. In order:

1. **Find the commit.** `git reflog` (or `git reflog <branch>`) lists where HEAD has been — across resets, rebases, and branch deletions. `git log -g --grep=<text>` searches it.
2. **Preserve before touching.** `git branch rescue/<name> <sha>` — never `reset --hard` toward a candidate you haven't secured.
3. **Inspect** (`git show <sha>`), then integrate via merge, cherry-pick, or branch switch.
4. Unreachable even from reflog: `git fsck --lost-found`, then inspect `.git/lost-found/`.

State the limits plainly: reflogs are local and expire — not a backup, not remote evidence; nothing recovers work that was never committed or stashed (which is why checkpoint commits exist). Avoid `gc` or aggressive cleanup while recovering.

A bad published update is fixed forward: `git revert` (a merge revert needs an intentional `-m` mainline parent), a recovery branch/PR, or an explicitly coordinated restoration with an exact lease — not a silent force-push of the old SHA.
