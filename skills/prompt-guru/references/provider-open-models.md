# Provider: Open-weight & other models (Llama, Muse, Mistral, Qwen, DeepSeek, gpt-oss, Gemma, Kimi / GLM / MiniMax, Grok)

What to do differently for open-weight / other-provider models. Sources: official vendor docs and model cards — dev.meta.ai (Llama, Muse Glimmer), docs.mistral.ai, Qwen model cards, api-docs.deepseek.com + DeepSeek-V4 model card, OpenAI harmony guide (gpt-oss), ai.google.dev/gemma, platform.kimi.ai, docs.z.ai, platform.minimax.io, docs.x.ai. Apply on top of the general references.

## Contents
1. Cross-vendor rules of thumb
2. Meta: Llama, Muse Glimmer
3. Mistral
4. Qwen
5. DeepSeek
6. OpenAI gpt-oss
7. Google Gemma 4
8. Kimi, GLM, MiniMax
9. xAI Grok

## 1. Cross-vendor rules of thumb

- **Chat-template fidelity is the #1 lever**: use the vendor's exact special tokens/roles (or the official tokenizer's `apply_chat_template`) — never hand-roll delimiters. Malformed templates silently degrade output.
- **System prompt support varies**: full support on nearly every current family; original DeepSeek R1 weights (Jan 2025) and Gemma 3 have none — put instructions in the first user message. gpt-oss splits a system message (meta) from a developer message (instructions).
- **Reasoning models invert classic advice**: skip few-shot and "think step by step" scaffolding; control depth via the effort parameter and let the model think. Several families can no longer turn reasoning off (Qwen3.8-2.4T, Kimi K3, GLM-5.3, Grok 4.5+).
- **Sampling — take the model card's numbers**: for reasoning modes the convergent value is now **temperature 1.0, top_p 0.95** (Qwen 3.5+, DeepSeek V4, Muse Glimmer, Kimi); exceptions are listed per family. Never use greedy / temperature-0 decoding on open-weight reasoning models — it causes degradation and endless repetition. Hosted reasoning APIs increasingly ignore sampling params (DeepSeek: no error, no effect) or fix them server-side (Kimi K3: omit them).
- **Reasoning in history is per family — check before you strip.** Replay it: Mistral, Qwen 3.8 (default), DeepSeek with tools (400 otherwise), Kimi, GLM preserved thinking, MiniMax, Muse Glimmer (optional), Grok Responses API. Strip it: Gemma 4 (keep between function calls within one turn), gpt-oss after a final answer, DeepSeek without tools (ignored anyway). The old "always strip prior thinking" rule now breaks tool loops.
- Repetition loops are the signature open-weight failure mode — mitigate with non-greedy sampling and `presence_penalty` where the card recommends it, not prompt text.
- Markdown or XML section delimiters are endorsed and safe across all these vendors.
- Re-test prompts on every model version bump — behavior drifts.

## 2. Meta: Llama, Muse Glimmer

- Instruct models need the exact template, and tokens differ per generation: Llama 3.x uses `<|begin_of_text|>`, `<|start_header_id|>role<|end_header_id|>`, `<|eot_id|>`; Llama 4 uses `<|header_start|>role<|header_end|>` and `<|eot|>`. Generate via `apply_chat_template`. Base models take plain text, no role markers.
- **Tools differ by generation**: Llama 4 takes function definitions in the **system** message and returns tool output in the `ipython` role. Llama 3.1 accepts custom tool definitions in the user or system message (test which works); its tool calls emit `<|python_tag|>` + `<|eom_id|>` (continuation expected) vs `<|eot_id|>` (turn done) — Llama 3.x only, so stop-token config must match the generation.
- Custom tool calling is zero-shot, one call per turn; instruct "Return function calls in JSON format."
- **Muse Glimmer** (30B, Apache-2.0, Aug 2026): always use `apply_chat_template`. Depth via `reasoning_strength` low / medium / high / xhigh (default high) — a low `max_tokens` clips it mid-reasoning before the answer. One tool call per turn, no parallel calls. Sampling: temperature 1.0, top_p 0.95, top_k 64. A prior reasoning trace may be replayed via the assistant message's `reasoning_content` (it counts toward context).

## 3. Mistral

- Open with a one-line role + task: "You are a <role>, your task is to <task>." General context in the system prompt, specifics in the user prompt.
- Few-shot examples (inline or as fabricated user/assistant turns); format consistency is the main win.
- Prefer **worded scales** ("Very Low"…"Excellent") over numeric scales for rating/judging tasks.
- Replace vague quantifiers ("too long", "many") with objective measures; never ask the model to count words/characters — supply counts as input.
- Request minimal output; JSON for parseable results.
- **Reasoning** (Small 4, Medium 3.5, Large 4): `reasoning_effort` `none` | `high` (Magistral is retired). Always replay the full assistant message, `ThinkChunk` included — Mistral: stripping it "significantly degrades output quality". Sampling per model card (around 0.7 at high effort).

## 4. Qwen

- Thinking mode sampling (3.5+): temperature 1.0, top_p 0.95, top_k 20, presence_penalty 0.0 — **do not use greedy decoding**. Non-thinking: temperature 0.7, top_p 0.8, top_k 20, presence_penalty 1.5 (0–2 against repetition; higher values can cause language mixing).
- Toggle thinking with `chat_template_kwargs: {enable_thinking: false}` (Qwen Cloud: `enable_thinking` directly). The `/think` / `/no_think` soft switches are gone from 3.5 on. Qwen3.8-2.4T-A95B can't disable thinking; it takes `reasoning_effort` instead.
- History: Qwen 3.8 retains thinking from all prior turns by default (`preserve_thinking`; set false to keep only the latest); Qwen 3.6 recommends `preserve_thinking: true` for agents. Older Qwen3 wanted only final answers in history.
- Math: append "Please reason step by step, and put your final answer within \boxed{}." Multiple-choice: force a JSON `"answer": "C"` field.

## 5. DeepSeek

- **System-prompt support depends on generation**: only the original R1 weights (Jan 2025) want no system prompt — all instructions in the user message — and sometimes skip the thinking phase (force the response to begin with `<think>\n`). R1-0528 and later, and the hosted V4 API, support system prompts.
- Hosted API (`deepseek-flash`; the `deepseek-chat` / `deepseek-reasoner` aliases and `deepseek-v4-flash` are retired, and DeepSeek's own pages disagree on whether `deepseek-v4-pro` still serves — check api-docs.deepseek.com/updates): thinking is on by default — toggle with `thinking: {type: enabled|disabled}`; `reasoning_effort` low / high / max (default high). In thinking mode, temperature and penalties are ignored without an error; top_p only applies in thinking mode, range 0.95–1.0.
- **With tools, pass every prior `reasoning_content` back in full** — omitting it returns a 400. Without tools it isn't needed and is ignored.
- Self-hosted V4 weights: temperature 1.0, top_p 0.95 for agentic use (1.0 otherwise); there is no Jinja chat template — use the repo's `encoding` scripts.
- **Zero-shot beats few-shot** for reasoning — the R1 report found few-shot consistently degrades it; describe task and output format directly.
- Math: same `\boxed{}` directive as Qwen.

## 6. OpenAI gpt-oss

- The **harmony** format is mandatory: use the HF chat template or the `openai-harmony` renderer, never hand-built strings.
- System message: identity, dates, and `Reasoning: low|medium|high`; developer message: the instructions and tool definitions.
- Output arrives on channels — `analysis` (chain of thought), `commentary` (tool calls), `final`. Show users only `final`. Keep prior chain of thought through a tool loop; drop it once a final answer is given.
- Sampling: temperature 1.0, top_p 1.0.

## 7. Google Gemma 4

- Turns are wrapped in `<|turn>` … `<turn|>` with roles `system` / `user` / `model` — Gemma 4 has a native system role (Gemma 3 did not; put its system text in the first user turn).
- Enable thinking by placing `<|think|>` in the system instruction (set per conversation). Larger models can still emit a thought channel with thinking off — parse for it.
- Strip prior-turn thoughts from multi-turn history, **except between function calls** in one turn.
- Media go where their placeholders sit (`<|image|>`, audio) in the prompt. Sampling per model card.

## 8. Kimi, GLM, MiniMax

Shared pattern: reasoning-first, and the full assistant message must go back into history unchanged.

- **Kimi K3** (platform.kimi.ai): thinking always on; `reasoning_effort` low / high / max (default max). Return the complete assistant message unchanged, not just `content`, across turns and tool calls. Temperature 1.0 / top_p 0.95 / penalties are fixed — omit them from requests. `tool_choice: "required"` forces a tool call on the first turn.
- **GLM-5.3** (docs.z.ai): forced thinking, interleaved with tool calls by default. Preserved thinking (`clear_thinking: false`; default on the Coding Plan endpoint) requires returning the complete, unmodified `reasoning_content` in its original order.
- **MiniMax-M3** (platform.minimax.io): append the model's full response every turn — every content block (Anthropic SDK) or the whole message with `tool_calls` and `reasoning_details` (OpenAI SDK); dropping thinking breaks the reasoning chain. `reasoning_split` chooses separate `reasoning_details` vs `<think>` tags in `content`.

## 9. xAI Grok

- Grok 4.5 / 4.6 / 4.7 can't disable reasoning; control depth with `reasoning_effort` low / medium / high (default high), plus `xhigh` on 4.6 / 4.7 — not with prompted CoT.
- Do not send `presencePenalty`, `frequencyPenalty`, or `stop` to reasoning models — they error.
- Multi-turn reasoning: on the Responses API, pass reasoning items (encrypted content) back unchanged in the next `input`; Chat Completions has no field for it.
- Thorough, detailed system prompts; delineate sections with XML tags or Markdown headers.
- Provide **specific** context (exact files/paths/dependencies), never whole-codebase dumps — irrelevant context causes deviation. Keep prompt prefixes stable for cache hits.
- `grok-code-fast-1`, `grok-4-fast`, and `grok-3` were retired 2026-05-15 — retarget to Grok 4.5+. No official text prompt-engineering guide was found on docs.x.ai (2026-10).
