# Safety and Repository State

Read this before the first mutation in an unfamiliar, dirty, shared, linked, or automation-managed repository.

## Intake

Least-invasive reads first: repo root, current branch/upstream, `git status --short --branch`, recent log, remotes (redact credentials embedded in URLs), `git worktree list`. Read applicable `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, and `.github/` policy before commit, push, rewrite, or merge — they define protected branches, DCO/signing, hook, and convention requirements.

Individual commands legitimately fail on unborn branches, detached HEAD, bare repos, or missing upstreams. Interpret the failure; don't bury it in a blind command chain.

## Classify topology

Agents that skip this step commit into the wrong repository or break submodule boundaries:

- `git rev-parse --git-dir --git-common-dir` — different values mean a linked worktree (metadata shared with a main checkout elsewhere). Check `git rev-parse --show-superproject-working-tree` first: inside a submodule the dir mismatch is normal, and the submodule is a separate repository with its own scope.
- `git branch --show-current` empty → detached HEAD. Create a branch before task commits unless detached work is explicitly wanted.
- `git rev-parse --verify HEAD` fails → unborn repository: no `HEAD~1`, no merge bases, no default branch yet.
- A coding harness may own workspace creation, naming, and cleanup. Prefer its lifecycle over nested raw worktrees (see branches-and-worktrees.md).

## Map ownership before touching anything

The #1 agent failure is staging or destroying another writer's work-in-progress. Classify every relevant path:

| Class | Meaning | Handling |
|---|---|---|
| owned | you created/changed it for this task | free to stage |
| shared | intentionally coordinated with another owner | per agreement only |
| unknown | pre-existing, unclear provenance | leave untouched — no stash, reset, clean, blanket add, or "temporary" commit |
| generated | reproducible output | repo policy decides whether it's committed |

If task work overlaps unknown state, isolate in a worktree or stop for direction.

## Detect active operations

`git status` names an in-progress merge, rebase, cherry-pick, revert, or bisect. Resolve operation state files relative to `git rev-parse --git-dir`, not an assumed `.git/`. If an operation is active and not yours: don't start another one, don't delete lock or state files, and continue or abort only with task ownership and a verified rollback.

## Sensitive data

Before anything leaves the machine, scan staged diffs, messages, and issue/PR bodies for credentials, tokens, connection strings, private URLs, and env files. A secret already committed or pushed is an incident: stop normal delivery, don't repeat the value in output, and follow rotation policy — deleting it from the next diff is not remediation.

## Boundary evidence

After each mutation, run the narrowest read that proves its result plus `git status --short --branch`. Hand off: topology, current ref, ownership of remaining dirty paths, active operations, mutations performed, and verification results.
