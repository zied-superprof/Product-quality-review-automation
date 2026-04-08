# Phase 3: Feedback Loop Strengthening - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Restructure `corrections_log.json` with a machine-readable schema and surface the most relevant past rules per language at review time. This phase does NOT implement translation generation — it structures the data so a future generation milestone can use it. The output is a cleaner corrections store and smarter rule retrieval, nothing more.

</domain>

<decisions>
## Implementation Decisions

### Schema migration (FBK-01)

- **D-01:** Migrate the 3 existing entries in-place to the new schema — rename fields, add missing ones with defaults. Do not leave a mixed-schema file.
- **D-02:** New schema has exactly 8 fields: `language`, `notification_type`, `issue_category`, `original`, `corrected`, `rule_extracted`, `confidence`, `date`
- **D-03:** `notification_type` stores the BO notification ID (e.g., `"reco-val-prof-bo"`, `"relance_3"`) — not a human-readable category label
- **D-04:** Field mapping for migration: `category` → `issue_category`, `notification_id` → `notification_type`, `original_text` → `original`, `corrected_text` → `corrected`, `extracted_rule` → `rule_extracted`
- **D-05:** Missing `confidence` field on migrated entries: `high` for the 2 empty-translation entries (objectively correct, seen in 2 markets), `medium` for the Lithuanian declension entry (its own description flags it as "needs native speaker verification")
- **D-06:** False-positive corrections (user dismissing a finding that was wrong): `original` = the flagged finding text, `corrected` = the dismissal reason/explanation

### Feedback session writes (FBK-02)

- **D-07:** One corrections entry per market per feedback item — 20 feedback items in one session = 20 rows, each with a single `language` field at the top level (enables reliable language-based filtering)
- **D-08:** Claude sets `confidence` automatically based on objective signals:
  - `high`: user explicitly confirmed the correction, or it's a clear structural fact (empty translation, wrong variable for language)
  - `medium`: correction is valid but context-dependent, or involves linguistic nuance
  - `low`: flagged as speculative, needs native speaker verification, or inferred from ambiguous feedback

### rules_summary.json (FBK-03)

- **D-09:** `rules_summary` array is removed from `corrections_log.json` — `rules_summary.json` is the single source of truth
- **D-10:** Full rebuild after each feedback session — recalculated from all corrections entries from scratch. No append logic.
- **D-11:** Duplicate rules (same pattern seen in multiple notifications) are merged into one entry with `occurrence_count` incremented. Matching is by language + issue_category + semantic similarity of `rule_extracted`.
- **D-12:** After saving, announce to user in one line: `"Rules summary updated: N rules across M languages → corrections/rules_summary.json"`

### Top-3 rule retrieval (FBK-04)

- **D-13:** Relevance score formula: `occurrence_count × recency_weight × confidence_score`
  - `confidence_score`: high=1.0, medium=0.75, low=0.5
  - `recency_weight`: 1.0 for rules updated within 30 days, 0.8 for 31–90 days, 0.6 for 90+ days
- **D-14:** Surface top-3 per language. If a language has fewer than 3 language-specific rules, pad with highest-scoring `"all"` language rules to reach 3.
- **D-15:** Rules loaded silently — no per-language announcement. Applied as context without user-visible output.
- **D-16:** Load all rules upfront at Step 3 (one file read), capped at top-5 per language loaded into context. If rules_summary.json exceeds 150 total rules, log a one-line warning: `"rules_summary.json has grown large (N rules) — consider pruning low-confidence entries."`

### Pre-write conflict detection (FBK-02 addition)

- **D-17:** Before writing any new rule or correction, Claude reads `review-translations.md` and the relevant config files to check for contradictions
- **D-18:** If no conflict: write silently, confirm in one line as normal
- **D-19:** If conflict detected: do NOT write. Show a conflict block and ask the user to decide:
  ```
  ⚠️ Conflict detected before writing:

  New rule:      "[extracted rule]"
  Conflicts with: [file] [section] — "[existing process]"

  Which takes precedence?
  1. Write the new rule anyway
  2. Discard the new rule
  3. Update the existing process instead
  ```
- **D-20:** Only pause when a conflict is actually detected — no confirmation prompt on the happy path

### Claude's Discretion

- Exact recency_weight calculation (days since `last_seen` on the rule entry)
- Schema for rules_summary.json entries (should include: `rule`, `language`, `issue_category`, `occurrence_count`, `confidence`, `first_seen`, `last_seen`)
- Migration script approach (inline Python or Claude-written transformation)

</decisions>

<specifics>
## Specific Ideas

- The scoring formula (`occurrence_count × recency_weight × confidence_score`) was explicitly chosen over simpler approaches — do not simplify it during planning/implementation
- The 150-rule warning threshold is a soft guard against context bloat — it is a log line, not a hard cap
- rules_summary.json is designed to be loadable by a future translation generation tool — keep the schema clean and self-describing

</specifics>

<canonical_refs>
## Canonical References

### Current corrections store
- `corrections/corrections_log.json` — existing file with 3 entries to migrate; also contains the `rules_summary` array to be extracted into its own file
- `corrections/` — target directory for both `corrections_log.json` and new `rules_summary.json`

### Review skill (Step 3 and Step 7)
- `.claude/commands/review-translations.md` §Step 3 — current rule loading logic (reads `rules_summary` from corrections_log.json, filters by language, no ranking or cap)
- `.claude/commands/review-translations.md` §Step 7 — current feedback loop (writes to `corrections_log.json > rules_summary`, freeform)

### Config files (for context on what rules reference)
- `config/label_patterns.json` — variable syntax rules; some feedback updates this file alongside corrections_log.json
- `config/tone_guidelines.json` — formality rules per language; some feedback updates this file alongside corrections_log.json

### Requirements
- `.planning/REQUIREMENTS.md` §Feedback Loop — FBK-01 through FBK-04 with exact success criteria

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/structural_validator.py`: Python stdlib JSON read/write pattern — reuse for any migration script (no pip dependencies)
- `corrections_log.json._schema` block: already documents the intended schema — use as the authoritative field list during migration

### Established Patterns
- All file writes in this project are done by Claude inline (not by Python scripts run in bash), except structural_validator.py — Step 7 is a Claude-driven write operation, keep it that way
- Config files (`label_patterns.json`, `tone_guidelines.json`) are updated alongside corrections_log.json when feedback touches variable or tone rules — this coupling must be preserved in the new Step 7

### Integration Points
- Step 3 in `review-translations.md`: replace the current `rules_summary` read with a read of `rules_summary.json`, apply top-5-per-language cap and scoring
- Step 7 in `review-translations.md`: replace freeform write with structured per-market entries + trigger rules_summary.json rebuild
- Both steps are in the same skill file — changes are co-located

</code_context>

<deferred>
## Deferred Ideas

- Pruning UI for low-confidence rules — user asked about keeping an eye on rules; the 150-rule warning covers this for now; a dedicated pruning command is Phase 4 territory or beyond
- Backup of corrections_log.json before writes — listed as QUA-03 in v2 requirements, out of scope for this phase

</deferred>

---

*Phase: 03-feedback-loop-strengthening*
*Context gathered: 2026-04-08*
