# Phase 12: zh-HK Language Code Resolution - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-28
**Phase:** 12-zh-hk-resolution
**Areas discussed:** Direction (split vs merge), Cleanup scope, Verification

---

## Direction

| Option | Description | Selected |
|--------|-------------|----------|
| Merge into zh-TW | Delete the zh-HK entries from corrections_log.json + rules_summary.json. Keep Hong-Kong → zh-TW in the validator. Lowest risk, smallest change. | ✓ |
| Split — full zh-HK end-to-end | Add zh-HK to languages.json, tone_guidelines.json, label_patterns.json, review_rules_compact.md, and update structural_validator.py:684 (Hong-Kong → zh-HK). HK gets its own rule lookup and can diverge from TW over time. | |
| Discuss trade-offs first | Walk through pros/cons in more detail before committing. | |

**User's choice:** Merge into zh-TW
**Notes:** User accepted the recommended direction without further discussion — the evidence (every other config already treats HK as zh-TW, sample CSVs show identical Traditional Chinese content, Phase-9 origin of the orphan) was sufficient.

---

## Cleanup scope

| Option | Description | Selected |
|--------|-------------|----------|
| Delete + leave a code comment | Delete the two zh-HK entries. Add a comment at structural_validator.py:684 explaining HK is intentionally folded into zh-TW. | |
| Delete only | Just remove the two zh-HK entries. No code comments. Cleanest diff. | ✓ |
| Delete + record decision in a config | Delete entries + update languages.json `notes` field on the zh-TW row to mention HK is folded. | |

**User's choice:** Delete only (effectively — derived from the freeform reply "we can remove this rule, eventually we have to review the whole language database, the rules and the variables")
**Notes:** The user first asked for examples to understand the three options. After concrete examples were shown for each, the user replied that the rule should simply be removed and that a broader review of the language database, rules, and variables will happen in a future phase. Recorded under Deferred Ideas in CONTEXT.md.

---

## Verification

| Option | Description | Selected |
|--------|-------------|----------|
| Live skill run on a real CSV with HK row | Run /review-translations on samples/Relance-1.csv and confirm HK content tagged as zh-TW with no orphaned-rule warnings. | |
| Code-only verification | Grep/diff after the change to confirm zh-HK no longer appears anywhere except in archived/historical files. | (floor) |
| Both — grep + live run | Static check first, then live run on a real HK-bearing CSV. | |

**User's choice:** Deferred — "We will decide later on after I understand the issue"
**Notes:** After the cleanup-scope clarification, the user's broader signal was to keep the change small. CONTEXT.md (D-06) records grep as the verification floor and live run as optional, planner's discretion.

---

## Claude's Discretion

- Exact mechanism for the JSON deletes (jq, Python, sed) — planner/executor decides.
- Whether to package the two file edits in one plan or two — planner decides (likely one).
- Whether to spot-check `samples/Relance-1.csv` post-merge or rely on grep alone — planner decides.

## Deferred Ideas

- Full review of the language database, rules, and variables (user-initiated, future phase).
- Mechanical guard that fails CI if a corrections-file language code has no matching config entry (would have caught IC-02 automatically).
- Establishing a default smoke-test step for future merge/split decisions on language codes.
