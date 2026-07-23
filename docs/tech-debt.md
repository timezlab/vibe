# Tech Debt

Add entries below using the schema in the comment — one `##` section per
item, newest last. Undecided product choices are not debt; they belong in
[roadmap decision gates](product/roadmap.md#open-decision-gates).

<!--
Entry schema — copy for each new item:

## TD-NNN: <short title>
- **Where:** <file/module path>
- **Symptom:** <what you observe when it bites>
- **Why deferred:** <the reason it wasn't fixed now>
- **Trigger to fix:** <the signal that makes fixing it worthwhile>
- **Created:** YYYY-MM-DD
-->

## TD-001: Windows backup path is documented-only
- **Where:** `hooks/learned/lib/learned_store.py` (`_data_home`)
- **Symptom:** `%LOCALAPPDATA%\vibe\backup\` resolution is untested on a real Windows host; a path or permission quirk would surface as a silent backup miss (backup is best-effort).
- **Why deferred:** no Windows CI in the repo; the feature targets Linux/macOS first (plan.md Technical Context).
- **Trigger to fix:** first Windows user of the learned pack, or Windows CI landing.
- **Created:** 2026-07-23

## TD-002: Instinct confidence is informational, never updated
- **Where:** `hooks/learned/` (instinct `confidence` field)
- **Symptom:** confidence is set once at creation from evidence count (2 → 0.5, 3–5 → 0.7, >5 → 0.85) and never moves on confirm/contradict; readers may over-trust a stale number.
- **Why deferred:** deliberate (research.md D4): the ECC reference implements confidence updates as prompt text with zero enforcing code, and the human review verdict is the actual quality gate. An update mechanism needs real usage data to design.
- **Trigger to fix:** evidence that recency-first selection misranks instincts, or a follow-up feature wiring deterministic updates to review events.
- **Created:** 2026-07-23

## TD-003: Secret-scrub patterns duplicated across hook packs
- **Where:** `hooks/learned/lib/learned_store.py` and `hooks/security/protect-secrets.py`
- **Symptom:** the credential-shape regex list exists in both packs (copied with a provenance comment so each pack stays independently copyable); a pattern added to one can be missed in the other.
- **Why deferred:** packs are distributed by copying directories; a shared import would couple them (ADR 0005 — no plugin distribution for shared code).
- **Trigger to fix:** `vibe sync` gaining a build step that can inject a single pattern source into both packs.
- **Created:** 2026-07-23
