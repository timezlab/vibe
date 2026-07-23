# Staging and Commits

Contents: staging discipline · non-interactive hunk staging · flag gotchas · hooks · the message · attribution · amend vs follow-up · verification.

## The index is the proposed commit

Blanket staging (`git add .`, `git add -A`, `git commit -a`) is the most common agent mistake: it captures debug output, another writer's work, and secrets into one unreviewable commit. Stage explicit paths you own, then review content, not filenames: walk `git diff --cached` line by line — every staged line belongs to the stated intent, nothing unknown-owned or generated slipped in; `git diff --cached --check` when whitespace policy matters.

Split when changes have different motivations, rollback paths, or reviewers; keep a behavior change together with the test that proves it. Typical plan for a mixed diff:

1. behavioral fix + regression test
2. mechanical refactor that follows
3. regenerated artifacts required by 1–2
4. unrelated pre-existing work — leave unstaged

## Non-interactive hunk staging

`git add -p` and `git add -e` are interactive and will hang the harness. To stage part of a file:

```bash
git diff -- path/file.py > /tmp/full.patch     # 1. capture the diff
# 2. copy to /tmp/part.patch and delete the hunks you don't want (keep the ---/+++ headers)
git apply --cached /tmp/part.patch             # 3. stage just those hunks
git diff --cached -- path/file.py              # 4. verify the staged subset
```

For a new (untracked) file you want to hunk-stage, run `git add -N path` first so it appears in `git diff`. When hunks interleave too tightly to split by patch, edit a copy of the file to the intended intermediate state, or commit whole and reshape with a fixup.

## Commit flag gotchas

| Flag | Gotcha |
|---|---|
| `-a` | Stages modified/deleted tracked files but not untracked — in a mixed tree it grabs unrelated changes while missing your new files. |
| `--amend` | Replaces the tip with a new SHA. Unpublished work only; published tips need rewrite preflight (sync reference). |
| `--fixup=<sha>` | Deferred history rewrite — squash later with `GIT_SEQUENCE_EDITOR=true git rebase --autosquash`. |
| `-C <commit>` | Copies message and authorship. Not a neutral text copy. |
| Repeated `-m` | Each becomes a paragraph — the safe multi-paragraph builder. A literal `\n` inside one `-m` stays literal. |
| `--no-verify` | Not available as a convenience — see the safety protocol. |

Long messages: heredoc (`git commit -m "$(cat <<'EOF' … EOF)"`) or write the message to a file outside the repo and use `-F /tmp/msg.txt`. Let `-s` add its own signoff trailer; don't duplicate it manually.

## Hooks may mutate state

A hook can reject the commit or rewrite files (formatters). On failure or modification: read the full output, rerun `git status` and both diffs, identify what the hook changed, stage only the intended corrections, and create a fresh commit. A repeated identical failure means the fix isn't landing — diagnose instead of looping, and never reach for `--no-verify`.

## Write the message from the staged diff

The diff already shows the *what*; the body carries the *why* — previous behavior, new behavior, tradeoffs, compatibility, rollback. This is load-bearing, not ceremony: commit messages are how the next fresh-context agent session reconstructs intent. Convention precedence:

1. repository instructions / templates / commitlint config;
2. recent accepted history;
3. Conventional Commits when structured messages help;
4. otherwise: a specific imperative subject ("reject expired tokens," not "update auth") plus a why-body.

**When the body is required — decide by rule, not by mood.** Write a body
whenever the commit touches more than one file, adds a mechanism /
decision / convention, or carries a *why* the diff can't show. Subject-only
is reserved for changes whose intent is complete in the one line — a typo,
a version bump, an obvious single rename. A description packed into the
subject (`skill: x (…)`, `feat(y): …`) is still a subject, not a body; a
substantial change needs both. Calibrate body depth to the change's
weight: in a batch of commits, the largest or most novel one earns the
*most* body, not the least. Sequential body-or-not calls made under
momentum are exactly what leaves a batch's messages uneven — a big commit
with a one-line message next to a trivial one with three; hold every
commit in the pass to this same bar.

Conventional Commit types — pick by what the diff does, not what the ticket says; the type is a release signal (see releases.md):

| Type | For | Release |
|---|---|---|
| `fix:` | bug fix | patch |
| `feat:` | new behavior | minor |
| `feat!:` / `BREAKING CHANGE:` footer | incompatible change | major |
| `refactor:` `perf:` | no behavior change / perf only | none |
| `chore:` `build:` `ci:` | tooling, deps, pipelines | none |
| `docs:` `test:` `style:` | docs, tests, formatting only | none |

Optional scope in parentheses: `fix(auth): reject expired tokens`.

`Fixes #418` closes the issue when the change reaches the default branch; `Refs: #418` doesn't — choose deliberately.

One shape worth copying (subject = observable change; body = why, behavior delta, rollback):

```text
fix(cache): avoid reusing expired entries

Expired entries stayed addressable while background refresh was in
flight, letting stale authorization data escape the cache boundary.
Remove the entry before scheduling refresh: more misses during the
refresh window, but expired data is never read again.

Rollback: revert this commit; no migration required.

Refs: #418
```

## Attribution: three different mechanisms

| Mechanism | Certifies | Does not mean |
|---|---|---|
| `Co-authored-by:` trailer | another real human contributed | AI/tool/vendor credit |
| `Signed-off-by:` / `-s` | project-defined legal certification (commonly DCO) | a cryptographic signature |
| `-S` / `--gpg-sign` | cryptographic signature on the commit object | DCO or co-authorship |

Don't add `Co-authored-by` for an AI, model, or tool, and don't fabricate any of the three. Add a human co-author only when asked or required by policy, using the exact name/email that person publishes. Before `-s`, confirm the certification actually applies; before `-S`, confirm the configured key and verify the signature afterward.

## Amend, fixup, or follow-up

- Unpublished tip with wrong content/message → amend, after verifying HEAD and staged scope.
- Published/shared branch → follow-up commit by default; a rewrite stales reviews, reruns CI, and diverges collaborators.
- Fixup + autosquash → when the repo reviews corrections separately; the squash itself is a history rewrite.

## Verify the commit

`git show --format=fuller --stat HEAD` plus `git status --short`: the tree matches the reviewed index, the full message is correct, author/committer/trailers are right, and unrelated changes remain outside. A successful commit command says nothing about whether the software still works — run the relevant tests.
