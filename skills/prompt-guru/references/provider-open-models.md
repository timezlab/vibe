# Provider: Open-weight & other models (Llama, Mistral, Qwen, DeepSeek, Grok)

What to do differently for open-weight / other-provider models. Sources: official vendor docs (llama.com, docs.mistral.ai, Qwen model cards, api-docs.deepseek.com + DeepSeek-R1 usage recommendations, docs.x.ai). Apply on top of the general references.

## Contents
1. Cross-vendor rules of thumb
2. Meta Llama
3. Mistral
4. Qwen
5. DeepSeek
6. xAI Grok

## 1. Cross-vendor rules of thumb

- **Chat-template fidelity is the #1 lever**: use the vendor's exact special tokens/roles (or the official tokenizer's `apply_chat_template`) — never hand-roll delimiters. Malformed templates silently degrade output.
- **System prompt support varies**: full support (Llama, Mistral, Qwen, Grok, DeepSeek R1-0528+ and the hosted V4 API) → actively harmful (original DeepSeek R1 weights only: put everything in the user message). Relocate instructions per family; if no system prompt, concatenate instructions before the query.
- **Reasoning models invert classic advice**: skip few-shot and "think step by step" scaffolding; control depth via API params and let the model think.
- **Never use greedy/temperature-0 decoding on open-weight reasoning models** — ~0.6 temperature with high top_p is the convergent recommendation (Qwen, DeepSeek); greedy decoding causes degradation and endless repetition.
- **Strip prior-turn thinking content from history** for every reasoning family (Qwen `<think>`, DeepSeek `reasoning_content`, Grok traces).
- Repetition loops are the signature open-weight failure mode — mitigate with `presence_penalty` and non-greedy sampling, not prompt text.
- Markdown or XML section delimiters are endorsed and safe across all these vendors.
- Re-test prompts on every model version bump — behavior drifts.

## 2. Meta Llama

- Instruct models need the exact template, and the special tokens differ per generation: Llama 3.x uses `<|begin_of_text|>`, `<|start_header_id|>role<|end_header_id|>`, `<|eot_id|>`; Llama 4 uses `<|header_start|>role<|header_end|>` and `<|eot|>`. Always generate via the official tokenizer's `apply_chat_template` rather than hand-writing tokens. Base models take plain text, no role markers.
- Roles: `system`, `user`, `assistant`, plus `ipython` for returning tool output.
- Custom tool definitions (JSON / `<function>` tags) go in the **user** message, not the system prompt; the system prompt holds `Environment: ipython` + `Tools:` lines for built-in tools.
- Tool calls emit `<|python_tag|>` + `<|eom_id|>` (continuation expected) vs `<|eot_id|>` (turn done) — stop-token config must handle both.
- Custom tool calling is zero-shot, one call per turn; instruct "Return function calls in JSON format."

## 3. Mistral

- Open with a one-line role + task: "You are a <role>, your task is to <task>." General context in the system prompt, specifics in the user prompt.
- Few-shot examples (inline or as fabricated user/assistant turns); format consistency is the main win.
- Prefer **worded scales** ("Very Low"…"Excellent") over numeric scales for rating/judging tasks.
- Replace vague quantifiers ("too long", "many") with objective measures; never ask the model to count words/characters — supply counts as input.
- Request minimal output; JSON for parseable results.

## 4. Qwen

- Thinking mode sampling: Temperature 0.6, TopP 0.95, TopK 20 — **do not use greedy decoding**. Non-thinking: Temperature 0.7, TopP 0.8; tune `presence_penalty` 0–2 against repetition.
- Hybrid thinking toggles via `enable_thinking` or `/think` `/no_think` tags; pick sampling per mode.
- Multi-turn history must contain only final answers — strip `<think>` content from prior assistant turns.
- Math: append "Please reason step by step, and put your final answer within \boxed{}." Multiple-choice: force a JSON `"answer": "C"` field.

## 5. DeepSeek

- **System-prompt support depends on generation**: only the original R1 weights (Jan 2025) want no system prompt — all instructions in the user message — and sometimes skip the thinking phase (force the response to begin with `<think>\n`). R1-0528 and later officially support system prompts and need no `<think>` forcing; the hosted V4 API fully supports them.
- Hosted API: thinking mode toggles via `thinking: {type: enabled}` / `reasoning_effort`; in thinking mode the API rejects sampling params (temperature, top_p, presence/frequency penalties) outright. Legacy aliases `deepseek-chat` / `deepseek-reasoner` sunset on 2026-07-24 — target the v4 model names.
- Self-hosted weights: Temperature 0.5–0.7 (0.6 recommended) against repetition/incoherence.
- **Zero-shot beats few-shot** — the R1 report found few-shot consistently degrades reasoning, and this remains current vendor guidance; describe task and output format directly.
- Never feed `reasoning_content` back into history.
- Math: same `\boxed{}` directive as Qwen.

## 6. xAI Grok

- Reasoning always on; control depth with `reasoning_effort` (low/medium/high), not prompted CoT.
- Do not send `presencePenalty`, `frequencyPenalty`, or `stop` to reasoning models — they error.
- Thorough, detailed system prompts; delineate sections with XML tags or Markdown headers.
- Provide **specific** context (exact files/paths/dependencies), never whole-codebase dumps — irrelevant context causes deviation.
- Iterate cheaply with fast retry loops (grok-code-fast-1); keep prompt prefixes stable for cache hits.
- Don't reuse reasoning traces across turns; use encrypted `reasoning_content` passthrough if required.
