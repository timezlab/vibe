# History Inspection and Debugging

Use read-only history tools to answer a specific question before proposing any mutation. Preserve evidence: no rebase, reset, amend, clean, or force-push during diagnosis unless repair is separately requested.

## Route by question

| Question | Tools |
|---|---|
| What differs now? | `status`, `diff`, `diff --cached`, `show` |
| Which commits are in head but not base? | `log base..head`, `cherry` |
| What will a PR show? | merge base + `diff base...head` |
| How did two patch series change? | `range-diff` |
| When/why did this text change? | `log -p`, `log -S<string>`, `log -G<regex>`, `blame` |
| Which commit introduced a regression? | deterministic test + `bisect` |
| Where did a lost commit/branch go? | `reflog` → recovery playbook in sync-conflicts-and-recovery.md |

Resolve ambiguous names with `git rev-parse --verify <ref>`; use explicit refs and `--` path boundaries.

## Range semantics

Agents regularly produce wrong PR diffs by confusing the two range forms:

- `git diff A..B` (same as `git diff A B`) compares the endpoint trees directly.
- `git diff A...B` compares B against the merge base of A and B — this is what approximates a PR diff.
- `git log A..B` lists commits reachable from B but not A.

Inspect both the commit range and the final diff: reverted or unrelated commits can vanish from the endpoint diff while still being in the range.

## Bisect

Bisect moves HEAD and records state — run it in a clean, owned worktree only.

1. Prove known-good and known-bad commits with the same deterministic test.
2. Mark good/bad; `skip` only genuinely untestable commits.
3. `git bisect run <script>` automates it: exit 0 = good, 1–127 = bad, 125 = skip. Inspect the script before running.
4. Reproduce the first-bad candidate manually — flaky tests and broken historical builds mislead bisect.
5. Always `git bisect reset` and verify restoration.

## Diagnostic handoff

Report the question asked, refs/range inspected, commands and evidence, confidence and alternatives, and whether state moved (e.g., bisect). If no fix was requested, stop after diagnosis and propose the smallest repair without performing it.
