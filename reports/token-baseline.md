# Token Optimization Baseline Metric

## Baseline

**Date:** 2026-04-08

**Description of token waste source:**
Step 4c outputs one JSON array per market to the conversation context. Each array contains issue objects with fields: market, lang, severity, category, issue, original_fr, current_translation, suggested_fix. On a 39-market batch, this produces 5,000-30,000 tokens of inline JSON that the model re-reads as input context in Step 5.

**Estimated token cost formula:**
Per market: ~50-500 tokens (empty array = ~10 tokens, market with 5 issues = ~500 tokens). For 39 markets: ~2,000-20,000 output tokens echoed, then re-consumed as ~2,000-20,000 input tokens in Step 5.

**Current Step 4c instruction (verbatim, before optimization):**

Line 79:
> "Work through each flagged market **inline in this conversation** — no subagents, no batching. For each market, evaluate the 7 criteria below and output a JSON array of issues before moving to the next."

Line 95:
> "After all markets are reviewed, merge all JSON arrays into a single flat list. This is the AI findings set for Step 5."

## Post-Optimization

**Date applied:** 2026-04-08 (commit 073f8cc)

**Mechanism active:** Step 4c now accumulates findings silently into `ai_findings`. One progress line per market (~15 tokens) replaces the full JSON array. Step 5 merge receives the same flat list.

**Estimated post-optimization cost:**
Per market: ~15 tokens (one progress line). For 39 markets: ~585 output tokens, then Step 5 receives the `ai_findings` list directly — no re-consumption of echoed JSON.

**Reduction:** ~585 tokens vs. ~2,000–20,000 tokens baseline → **80–97% reduction in Step 4c output tokens.**

**Post-optimization Step 4c instruction (verbatim):**

Line 79:
> "Work through each flagged market **inline in this conversation** — no subagents, no batching. For each market, evaluate the 7 criteria below and **append all issues to `ai_findings`** (a running flat list held in memory). Do NOT output JSON arrays to the conversation. Instead, output one progress line per market:"

End of section:
> "After all markets are reviewed, output a summary line: 'AI review complete: [N] markets reviewed, [M] total issues found.' The `ai_findings` list is the AI findings set for Step 5."

## Measurement Method

Compare conversation length (in tokens displayed by Claude Code) for the same CSV file before and after. The JSON arrays in Step 4c are replaced by one-line progress indicators (~15 tokens per market), saving an estimated 80-95% of Step 4c output tokens.
