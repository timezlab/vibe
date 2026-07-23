# Releases

Contents: find the current version · decide the bump from the diff · changelog · execute · verify.

Steps 1–3 are read-only reconnaissance. Step 4 mutates state and is blocked until the user has confirmed the version (Gate 1) and the changelog (Gate 2) — a release is public and hard to retract, so being confident in the bump is not a substitute for confirmation. In a non-interactive session where nobody can answer, stop after step 3 and deliver the proposal; do not tag or publish.

## 1. Find the current version — tags, not Releases

Many repos tag without creating GitHub Releases, so `gh release list` under-reports. Tags are the source of truth:

```bash
git fetch --tags
git tag --sort=-version:refname | head -5      # version-aware: 1.10.0 > 1.9.0 (alphabetical sort gets this wrong)
git ls-remote --tags origin | grep <tag>        # confirm the latest tag exists on the remote, not only locally
```

No tags at all → the baseline is the root commit: `git rev-list --max-parents=0 HEAD`. Also check for versions recorded in files (`package.json`, `pyproject.toml`, `VERSION`) — those must be bumped in a commit before tagging.

## 2. Decide the bump from the diff, not the commit messages

Commit messages state intent; the diff is what actually shipped. When they conflict, the diff wins — a commit saying `fix: typo` that removes a public method is a MAJOR change.

Scope the diff to the public surface and drop noise:

```bash
git diff $LAST_TAG..HEAD --stat -- src/ ':(exclude)**/*test*' ':(exclude)*.lock' ':(exclude)docs/'
```

Ask once which paths are the public surface if unclear; on a huge diff, `--stat` first, then read the files that look like API surface (`index.*`, `api.*`, `__init__.*`).

| Diff shows | Bump |
|---|---|
| removed/renamed public symbol, changed signature or return type, changed default of an optional param callers may rely on | MAJOR |
| new public symbol/endpoint/option, backward-compatible behavior addition | MINOR |
| bug fixes, internal refactors, docs, dependency updates without API impact | PATCH |

Pre-1.0 convention allows breaking on MINOR — follow the repo's own history. A revert counts as whatever the net diff shows. When genuinely in doubt, prefer the larger bump. **Gate 1:** propose the version citing specific code findings, and wait for confirmation.

## 3. Changelog

Group by impact (Breaking / Added / Fixed / Internal), written from the diff with commit messages as context, in the repo's existing format (`CHANGELOG.md` convention or previous release-notes style). Link PRs/issues where the repo does. `gh api repos/{owner}/{repo}/releases/generate-notes -f tag_name=v$VERSION` (or `gh release create --generate-notes`) drafts notes from merged PR titles — a starting point only: PR titles state intent, so reconcile the draft against the step-2 diff before presenting it. **Gate 2:** confirm the text.

## 4. Execute

Follow the repo's documented release process if one exists (release PR, CI-driven publish, tag-triggered pipeline) — don't invent a parallel one. A typical direct flow:

```bash
# bump version files + CHANGELOG in a commit on the default branch (via PR if the branch is protected)
git tag -a v$VERSION -m "v$VERSION"
git push origin v$VERSION
gh release create v$VERSION --title "v$VERSION" --notes-file /tmp/notes.md   # --notes-file, not inline --notes
```

## 5. Verify

`git ls-remote --tags origin | grep v$VERSION` (tag on the remote), `gh release view v$VERSION --json url,tagName,isDraft` (release exists, right tag, right draft state), and confirm any tag-triggered CI/publish pipeline actually started. Exit code 0 from `gh release create` is not proof the artifacts published.
