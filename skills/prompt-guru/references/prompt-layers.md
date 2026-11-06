# Prompt Layers: System vs User Turn

Where an instruction lives decides how it behaves. The **system layer** (system prompt, CLAUDE.md, project instructions, skills) is written by the operator, holds for the whole conversation, and wins conflicts; the **user layer** (the user turn — a chat message, the per-call user message of an API prompt, a request to a coding agent) carries one request and its data. Many "the model ignores my prompt" complaints are placement problems, not wording problems. Distilled from Anthropic's "Prompting best practices" hub and "Mid-conversation system messages" page (platform.claude.com/docs), the Claude Code best-practices docs (code.claude.com/docs/en/best-practices — the engineering post of the same name now redirects there), Anthropic Help Center articles ("Give Claude context: CLAUDE.md and better prompts", Projects, personalization), "Define success criteria", and the per-model prompting pages. Other providers split the layers the same way (OpenAI `developer` / `user`, Gemini `system_instruction`) — API mechanics live in the provider files.

## Contents
1. The two layers
2. What goes where
3. Writing a user-turn prompt
4. Prompting a coding agent (Claude Code guidance; generalizes)
5. Optimizing a user prompt
6. Operator moves at the user boundary
7. User-controlled system layers in Anthropic products
8. Testing across layers

## 1. The two layers

| | System layer | User layer |
|---|---|---|
| Written by | the operator / developer — or the user, through project instructions, preferences, CLAUDE.md | the end user, per request |
| Lifetime | the whole conversation; cached as a stable prefix | one turn; changes every call |
| Authority | Anthropic: a `system` message "is treated as coming from you, the application operator"; when the two conflict, "system instructions take precedence" | followed — "Claude does follow instructions that arrive in user turns" — but yields to the system layer on conflict |
| Content | role, standing rules with their why, tool guidance, default output format, domain constants | the task, its inputs, per-request format, this turn's examples |
| Cost | every line taxes every turn | paid once |

Consequences: a rule that must hold even if the end user asks otherwise goes in the system layer; a need that exists for one request stays in the user turn; anything repeated verbatim across user turns is a system-layer instruction being paid for by hand.

## 2. What goes where

| Content | Layer | Why |
|---|---|---|
| Role / identity (`"You are a helpful coding assistant specializing in Python."`) | system | a role in the system prompt focuses behavior and tone — "even a single sentence makes a difference" |
| Operator-level facts and constraints (policy, scope, safety, tenancy) | system | must survive a user asking otherwise |
| Tool guidance and boundaries between tools | system (+ the tool descriptions themselves) | stable across requests |
| Default output format and tone | system; per-request overrides in the user turn | the default is standing, the exception is one turn's |
| The task: what to produce, for whom, what done looks like | user | changes per call |
| Input data and documents (20k+ tokens at the top of the turn, in indexed `<document>` tags), pasted text | user | per-request. Never the system prompt, and never a mid-conversation `system` message — tool output and retrieved documents stay in `tool_result` blocks |
| Examples | stable ones in the system prompt; task-shaped ones at the start of the first user message (where Anthropic's prompt improver places them) | examples teach format and length — put them where the pattern they teach lives |
| Variables (`{{ANNUAL_REPORT}}`) | user turn, inside tags | the fixed/variable split is what makes a prompt testable |
| Dynamic context (date, user profile) | rendered into `system` once per conversation — only when the prompt is built per conversation; a system prompt shared across users carries no per-user facts (they arrive in the user turn or a `tool_result`) | re-rendering the date each turn breaks the cache (Haiku 5.5 page); a per-customer fact in a shared prompt leaks to every other customer |
| No-preamble rule, "the rules in this system prompt hold for the whole conversation" | system | standing behavior |
| Continuation ("Your previous response ended with… continue"), refusal steering, context reminders | user | Anthropic's prefill migrations put all three in the user turn |
| A behavior change that becomes relevant later in a conversation | an appended `system`-role message (provider file §6), not an edit to the top-level system prompt | keeps the cached prefix and operator authority |

## 3. Writing a user-turn prompt

A good user turn is a brief, not a wish. Anthropic's test: show it to a colleague with minimal context — if they'd be confused, the model will be. Cover, roughly in this order:

1. **The ask, as an imperative.** "Change this function to improve its performance" gets edits; "Can you suggest some changes…?" gets suggestions. If you want ideas or a plan rather than the work, say so — open-ended asks overshoot on current eager models (documented for Sonnet 5.5).
2. **Context the model can't infer**: why this matters, who reads the output, what it's for. Anthropic's pair: "Create a meal plan for a Mediterranean diet" vs "Design a Mediterranean diet meal plan for pre-diabetic management. 1,800 calories daily…".
3. **The inputs, as data**: documents and pasted material in named tags, long material at the top of the turn and the question after it ("queries at the end can improve response quality by up to 30 percent"); on 20k+ token documents, ask for the relevant quotes in `<quotes>` tags first, then the answer grounded in them.
4. **What done looks like**: the format stated positively ("smoothly flowing prose paragraphs", not "no markdown"), length, structure, and the acceptance check — for research, success criteria plus a request to verify across sources.
5. **Steps only where order or completeness matters**, numbered. Multi-stage work with distinct outputs chains better as sequential prompts, one job each (accuracy for latency).
6. **The why on every constraint**: "read aloud by a text-to-speech engine, so never use ellipses" generalizes; a bare prohibition doesn't.
7. **Permission to not know**: "If you're unsure, say 'I don't have enough information to confidently assess this.'" — Anthropic's documented hallucination reducer and the natural partner of the acceptance check.
8. **Examples sparingly**: one, then more only if the output misses. Current models weight examples heavily, so each one silently teaches format, tone, and length.

Length: no vendor publishes a budget for a user turn. It earns its length with context, inputs, and the done condition — never with rules; a line that would hold for every request is a system-layer line (§7).

Leave out: pleading and emphasis (a plainly worded line is followed; stacked IMPORTANT / MUST makes the model over-apply the rule); "think step by step" / "think carefully" scaffolds on thinking models (depth is the effort parameter — on Opus 5.5 lowering effort is more reliable than any prompt line, and on Haiku 5.5 "answer directly" didn't stop it thinking); and requests to show reasoning in the answer (on current Claude models that invites `reasoning_extraction` refusals — ask for a short rationale or an action summary instead).

## 4. Prompting a coding agent (Claude Code guidance; generalizes)

Anthropic's Claude Code docs are its most concrete official guidance on user-turn prompts to an agent:

- **Name the file, the symptom, and what fixed looks like.** Not "fix the login bug" but "users report login fails after the session times out. look at token refresh in src/auth/, write a failing test that reproduces it, then fix it". Not "add a calendar widget" but "follow the pattern in HotDogWidget.php and build a calendar widget that lets you pick a month and page between years. no new libraries".
- **State the outcome and its why, not the edit steps.** Not "Open `userService.ts`, find `validate`, add a null check on line 42" but "Users with no email are crashing the validation step. Make it handle that gracefully and add a test." Add acceptance criteria ("tests pass", "matches the style of the other handlers") and paste the full error, not a paraphrase. Numbered steps are fine for the investigation workflow (trace, reproduce, fix, verify); it is the edit itself you don't dictate.
- **State your preference between two reasonable approaches** — the agent cannot read it from the code.
- **Hand over inputs instead of describing them**: `@path` for files, screenshots, piped output (`cat error.log | claude -p "…"`).
- **Give it a pass/fail check and ask for evidence** — tests, exit code, linter, fixture diff, screenshot — and the command plus its output in the report. When asking for a review, add "skip style", or a reviewer will always find something.
- **Scope, not begging, for depth.** "think step by step" and "be thorough" are ordinary prompt text that nudge within the effort setting; set effort instead (`/effort` — Claude Code defaults Opus 5.5, Sonnet 5.5, and Haiku 5.5 to `medium`; API defaults differ, provider file §5). "be ambitious" still helps because it sets scope; `ultrathink` still raises a single turn.
- **Vague is fine for exploration** — the cost is more corrections. When you don't know what you want, ask the agent to interview you and write `SPEC.md`, then build from it in a fresh session.
- **Plan before large changes**: "Plan how you'd add rate limiting… Don't change anything yet."
- **Steer early.** Watch the first minute; interrupt (`Esc`) and roll back (`/rewind`) when it drifts; correct the specific problem rather than restating the request. After two failed corrections, `/clear` and write a better prompt. `/clear` between unrelated tasks; `/compact <focus>` to keep what matters.
- **Before an unattended run, answer five questions**: what does done look like, how does it check its own work, what may it touch, what stops it, who signs off.
- **Stop doing** (Anthropic's own list): ALL CAPS emphasis; "keep going / don't be lazy"; architecture dumps in CLAUDE.md; "the context window is your main constraint"; spawning subagents "for a better answer".

## 5. Optimizing a user prompt

Diagnose by the observed failure, fix in the smallest way, and check whether the fix belongs in a different layer:

| Observed failure | Usual cause | Fix |
|---|---|---|
| Generic output, misses the point | no context or audience in the ask | add why / who / what-for (§3.2); run the colleague test |
| Suggestions instead of changes; a plan instead of work | the ask was a question | imperative verb — or say "plan only" when that is what you want |
| Does far more than asked | open-ended ask on a literal, eager model | state the scope ("only the validation step") and what to leave alone |
| Wrong format or length | format implied, or taught by accident through examples or the prompt's own style | state the format positively; audit example length; prompt style begets output style |
| Ignores a constraint | the constraint lacks its why, or conflicts with another line | attach the motivation; resolve the contradiction — reasoning models burn effort reconciling conflicts |
| Confident wrong facts | no permission to not know; data described instead of provided | add the uncertainty line; paste the material in tags; quotes-first on long documents |
| Stops early, or asks too many questions | no done condition; effort too low | state done and the check; raise effort rather than writing "keep going" |
| Too much reasoning, or refusals about reasoning | "think step by step" / "show your thinking" on a thinking model | delete the scaffold; lower effort; ask for a rationale in the answer instead |
| The same instruction typed every turn | a system-layer rule living in the user layer | move it up: project instructions, CLAUDE.md, a skill, or the system prompt (§7) |
| Re-asks facts you already gave | the facts live in your head or a past session, not in any layer the agent loads | persist them where every session loads them (CLAUDE.md, project instructions) and give a default: "state your assumption in one line and proceed; ask only when two readings lead to materially different work" |
| A one-off need written into the system prompt | the wrong layer the other way | move it down to the turn that needs it, or into a skill loaded on demand |

Then run the main loop (SKILL.md 4B) on the result — cut, rewrite, add, restructure, move — where **move** includes moving across layers.

## 6. Operator moves at the user boundary

For developers building on the API, the layer split is also a trust and caching tool (mechanics, headers, and model coverage: provider-claude.md §6):

- **Mark pasted and third-party text as data.** Opus 5.5 guidance: wrap user-pasted text in `<pasted_content id="ab12">…</pasted_content id="ab12">` with a random per-block id, and tell the model in the system prompt that text inside those tags is untrusted. Anthropic documents this for text the user pastes; the same wrapping is the natural treatment for any free text an end user supplies. Tool output and retrieved documents stay in `tool_result` blocks — never in a `system` message.
- **Change behavior mid-conversation without editing the prefix**: append a `system`-role message (operator authority, cache kept) for instructions that become relevant later; a turn-scoped one for a one-turn nudge. The user's own mid-task words still go in the user turn, as a text block after the last `tool_result` — on Sonnet 5.5 and Haiku 5.5 a system message placed right after a tool result can be treated as untrusted text and ignored.
- **Never put user-authored text inside a `tool_result`** (documented for Sonnet 5.5); keep it in the user turn.
- **Order for the cache**: tools → `system` → history, stable content first; changing instructions as appended system messages at the end; the date rendered once per conversation.
- **Zero-exception rules live in the harness, in an API app too.** Claude Code has hooks; an API app has output validators and gating checks (a language detector, a banned-term regex, "a lookup tool call happened before any shipping answer") that fail closed — retry once, then a canned fallback. The prompt states the rule with its why; the check guarantees it, since the newest models reject forced `tool_choice` (provider file §6).

## 7. User-controlled system layers in Anthropic products

Users own a system layer too. Anthropic's scoping, by surface:

| Surface | Put here | Not here |
|---|---|---|
| claude.ai account instructions / preferences | preferred methods, common terms, typical scenarios, communication preferences — they apply everywhere | project- or task-specific rules |
| Project instructions | standing tone, format, approach, workflow, a role — for every chat in the project | one-off requests (stay in the chat); reference documents (go in project knowledge — chats share nothing else) |
| CLAUDE.md (Claude Code) | build / test / lint commands, conventions, a short architecture summary, hard constraints, known gotchas; rules you would otherwise repeat each session; under ~200 lines, reviewed quarterly ("outdated instructions are worse than none") | full API docs, changelogs, anything obvious from the file tree; this task's outcome, error, paths, and acceptance criteria — those are the prompt |
| Skills | repeatable procedures, tone / format presets, domain reference loaded on demand | always-on rules (system prompt, CLAUDE.md) and zero-exception rules (hooks) |

Graduation heuristic (this skill's, consistent with the scoping above): the second time you type the same instruction, move it up one layer; when a system-layer line is needed only for some tasks, move it down into a skill. A line you keep adding emphasis to belongs in a hook, not in any prompt layer — the mechanism is the harness's (Claude Code hooks, settings deny rules), not this skill's.

## 8. Testing across layers

- Evaluate the system layer with the user layer varied: a fixed system prompt plus a set of golden user turns ("even a set of 10 golden examples is enough to start") catches regressions when either layer changes; run each task more than once.
- Success criteria first — specific, measurable, usually multidimensional (quality, latency, cost). Evals task-specific with edge cases (irrelevant, overlong, ambiguous, hostile input), automated where possible, volume over hand-grading, graded by a different model than the one under test.
- Re-sweep effort and prompt lines per model: Anthropic measured each model-named technique on that model, so a user-turn fix tuned on one model may be noise on the next.
- When a user-turn eval keeps failing on the same point across many turns, the fix is a system-layer line. A system-layer line that only helps one eval case is a user-turn fix in the wrong place.
