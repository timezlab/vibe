# GitHub Issues

Contents: capability detection · before creating · create · triage · metadata and relationships · state changes · readback.

## Feature-detect, and don't substitute

`gh issue` capabilities vary by version — newer docs advertise `--type`/`--parent`/`--blocked-by` that the installed binary may lack. Check `gh issue create --help` / `gh issue edit --help` on the actual binary and use only advertised flags, or a verified `gh api` call (current schema, node IDs, relationship direction). Otherwise leave the field incomplete and report it.

These are not substitutes for each other:

- label `bug` ≠ Issue Type `Bug` (types are set via API, e.g. `gh api … -f type=Bug`; when a type is set, don't also add `[Bug]` title prefixes)
- a body link or comment ≠ a parent/sub-issue or blocked-by relation
- open state ≠ a Project `Status` value; an assignee ≠ a Project ownership field

## Before creating

Confirm the exact host and `OWNER/REPO` (wrong-repo guard in SKILL.md). Read `.github/ISSUE_TEMPLATE/` — issue forms define required fields and IDs; use them as formatting structure. Vulnerabilities and sensitive logs don't go in public issues — use the security policy channel. Search open and closed issues for duplicates and linked PRs first; on a duplicate, link/comment only when authorized.

## Create

Draft the title/body in a file outside the repo and sanitize it: no secrets, no fabricated repro results, versions, severity, or acceptance decisions. Create, capture the number/URL, and read it back before adding metadata. If creation succeeds and later metadata fails, fix the metadata — don't create a replacement issue.

A high-signal bug: observed vs expected, minimal repro, environment, impact evidence, hypotheses labeled as hypotheses, acceptance criteria. A feature: problem and user outcome, scope in/out, constraints, alternatives, acceptance criteria — don't prescribe implementation prematurely.

## Triage existing issues

Triage is classify → act, using the repo's own taxonomy — list existing labels first (`gh label list`); don't invent new ones:

1. Read title, body, and comments; classify type (bug / feature / question / docs) and severity from evidence in the report, not the reporter's framing.
2. Search for duplicates across open **and closed**: `gh issue list --search "<keywords>" --state all --limit 20`. On a confirmed duplicate: comment linking the original, label per repo convention, close as duplicate only when authorized.
3. A bug without reproduction steps: ask for the minimal repro, environment, and expected-vs-observed behavior — don't assign severity to an unreproducible report.
4. Apply labels via `gh issue edit <n> --add-label '…'`; answering a question is a comment mutation — draft outside the repo, sanitize, post. Readback rules below apply to every mutation.

Batch triage is multi-item remote work: track each issue as applied/missing/failed/unknown and report by name.

## Metadata and relationships

Each is a separate mutation with its own readback: labels/assignees/milestone, Issue Type, parent/sub-issue, blocked-by/blocking, Project membership, Project fields, development branch link. For Projects v2, resolve and record the project ID, item ID, field ID, and option/iteration ID — adding an item and setting its field are two operations.

Write the relationship direction in plain language before mutating ("this issue is blocked by #88," "this blocks #120") — reversed directions are a common silent error. Read current state before retrying so retries don't duplicate relationships.

Track multi-field work as applied/missing/failed/unknown per item; report partial completion by name instead of approximating.

## State changes

Close with the supported reason (completed / not planned) matching the actual outcome. Duplicate: link both directions when authorized, then close per repo convention. Transfer, pin, lock, and delete are administrative actions needing explicit scope — deletion rarely helps and doesn't un-leak secrets. `gh issue develop` creates a real linked development branch (verify the link and ref afterward); a branch merely named after the issue is not the same thing.

## Readback

Verify independently: repo, number/URL, state and reason, labels and true Issue Type, relationships and their direction, project fields, development links. Exit code alone is not completion evidence.
