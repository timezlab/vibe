# Skills Authoring & Optimization

Distilled from platform.claude.com/docs Agent Skills best practices and anthropic.com/engineering "Equipping agents for the real world with Agent Skills".

## Contents
1. How triggering works (why the description is everything)
2. Naming and description
3. Progressive disclosure and file layout
4. Body writing: conciseness and degrees of freedom
5. Scripts vs instructions
6. Workflows, checklists, feedback loops
7. The eval-first iteration loop
8. Review checklist for an existing skill

## 1. How triggering works

- Only the skill's **name + description** are preloaded; Claude chooses among potentially 100+ skills on the description alone. The body loads only after triggering. Therefore: triggering problems are *description* problems; behavior problems are *body* problems. Diagnose which one you have before editing.
- Claude tends to **under-trigger**: it consults skills only for tasks it can't trivially handle itself. Descriptions should be a little pushy — enumerate the concrete user phrasings and situations that should trigger, including indirect ones ("even if they don't explicitly say 'dashboard'").

## 2. Naming and description

- Name: lowercase, numbers, hyphens, ≤64 chars. Gerund form (`processing-pdfs`) or a clear noun phrase. Never `helper`/`utils`, never reserved words ("anthropic", "claude").
- Description: ≤1024 chars, **third person**, and must contain both halves — *what it does* + *when to use it* — with concrete trigger terms:
  - Good: "Extracts text and tables from PDF files. Use when working with PDFs or when the user mentions forms, scanned documents, or document extraction."
  - Bad: "Helps with documents."
- ALL when-to-use information lives in the description, none in the body — the body is invisible until after the trigger decision.
- Cover near-miss phrasings and the competing-skill boundary ("use X-skill for spreadsheets; this skill for PDFs only").

## 3. Progressive disclosure and file layout

Three levels: (1) name+description — always in context; (2) SKILL.md body — loaded on trigger, keep **<500 lines**; (3) references/scripts/assets — loaded or executed on demand, zero cost until used.

- Split by domain with descriptive filenames (`references/aws.md`, `references/gcp.md`) so only relevant material loads. Split out mutually-exclusive or rarely-used content first.
- Keep reference links **one level deep** from SKILL.md — nested chains cause partial reads (`head -100`) and missed content. Tell the reader explicitly when to read each file.
- Reference files >100 lines get a table of contents at the top.
- Bundle: `scripts/` (executable helpers), `references/` (docs read into context), `assets/` (templates/fonts used in output, never read).

## 4. Body writing: conciseness and degrees of freedom

- Default assumption: **Claude is already very smart.** Challenge every sentence: "does Claude really need this explained?" Anthropic's own example cuts a 150-token instruction to 50 with no loss.
- Imperative form. Explain the *why* behind non-obvious rules instead of stacking MUSTs (heavy ALL-CAPS is a yellow flag — see system-prompts.md).
- Match **degrees of freedom** to task fragility:
  - **High** (heuristics, principles): many valid approaches — creative/analytical work.
  - **Medium** (pseudocode, templates with parameters): a preferred pattern exists.
  - **Low** ("Run exactly this script; do not modify the command"): fragile, sequence-critical, or destructive operations.
- Consistent terminology throughout; one default path with an escape hatch beats a menu of options; forward-slash paths; fully-qualify MCP tools (`Server:tool_name`); state package dependencies explicitly; no time-sensitive info in the body (park legacy info in a collapsed "old patterns" section if needed).
- Input/output example pairs when output style matters.

## 5. Scripts vs instructions

- Deterministic, repetitive, or fragile operations → bundle a script instead of instructing Claude to write code each run: cheaper, faster, reliable. Strong signal: if test runs show Claude writing the same helper script every time, that script belongs in `scripts/`.
- Scripts handle their own errors ("solve, don't defer") and contain no unexplained magic numbers.
- State explicitly whether a file is to be **executed** ("Run `scripts/analyze.py`") or **read as reference** — ambiguity wastes context or breaks the run.

## 6. Workflows, checklists, feedback loops

- Multi-step procedures: numbered workflow + a copyable checklist the agent can tick off.
- Build feedback loops for quality-critical outputs: run validator → fix → re-run; "only proceed when validation passes."
- High-stakes or batch operations: plan → write plan to file → validate the plan → execute → verify.

## 7. The eval-first iteration loop

- **Build evals before documentation**: run Claude *without* the skill on ~3 representative tasks, record the failures, then write the minimal instructions that fix them. The failures define what the skill must say — this prevents writing content the model didn't need.
- Iterate with two instances: Claude A edits the skill; Claude B (fresh context, skill installed) runs real tasks. Feed B's failures back to A. Never trust the author-context's own judgment of the skill — it can't experience cold-start reading.
- Watch *how* B navigates: unexpected read order, skipped reference files, or a file re-read repeatedly all signal structural problems, not content problems.
- Test on every model tier that will use the skill (Haiku needs more guidance than Opus).
- Generalize from feedback — fix the pattern, not the example; avoid overfitting the skill to the test prompts.

## 8. Review checklist for an existing skill

Walk in order; each item names its fix-location:

1. Description contains what + when + concrete triggers, third person, pushy enough? (§2)
2. Any when-to-use info stranded in the body? Move to description. (§2)
3. Body <500 lines? If not, split by domain into references. (§3)
4. Reference files one level deep, each with a clear "read this when…" pointer, TOC if >100 lines? (§3)
5. Every sentence earns its tokens? Cut what a smart model knows. (§4)
6. Degrees of freedom match fragility — no rigid script for creative work, no loose heuristics for destructive ops? (§4)
7. Repeated codegen across runs → bundle as script; execute-vs-read explicit? (§5)
8. Quality-critical steps have a validator loop / observable done-condition? (§6)
9. Evals exist? If not, propose 3 representative test tasks before further edits. (§7)
