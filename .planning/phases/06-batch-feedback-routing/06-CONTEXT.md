# Phase 6: Batch Feedback Routing - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning

<domain>
## Phase Boundary

The user can paste a batch of N feedback comments in a single Step 7 input. The system analyzes and routes each comment to the correct config file (corrections_log.json, label_patterns.json, tone_guidelines.json) or flags it for manual action (Variables.csv). After the user confirms which items to apply, all confirmed actions are executed in one pass.

Batch input is session-independent — no active report or numbered items required.

</domain>

<decisions>
## Implementation Decisions

### Batch Input Format
- **D-01:** Input uses a structured language + issue format, NOT report item numbers.
  ```
  Language: es_AR
  Issue: "vos" is Rioplatense standard, not an error

  Language: ar
  Issue: @TPL_MATIERE_DE_MATIERE@ inside <TPL_LOOP_ANNONCES> is correct here

  Language: de
  Issue: "du" is brand standard — tone flagged as informal is correct
  ```
- **D-02:** The system should document this format as a collection template for the employee who gathers native speaker feedback. Include the template in the Step 7 prompt or as a reference in the skill.
- **D-03:** Input is session-independent — works in a fresh session without an active report.

### Routing Suggestion Display
- **D-04:** Routing suggestions are shown as a **block list** — one entry per item with: item number, language, issue summary, destination file, rationale, and conflict status.
  ```
  #1 — es_AR: "vos" tone issue
    → Routes to: tone_guidelines.json
    → Rationale: formality classification update for es_AR
    → Conflict: none

  #2 — ar: variable placement
    → Routes to: label_patterns.json
    → Rationale: subject_variable_usage_rules clarification
    → Conflict: ⚠️ Conflicts with existing rule [description]
  ```
- **D-05:** Items with conflicts are **excluded from the apply batch** until resolved. They block the batch.

### Conflict Resolution
- **D-06:** When a conflict is detected, the system shows the full conflict detail (new rule vs existing rule/config entry) and discusses it with Juan collaboratively to reach a resolution — no fixed menu of choices.
- **D-07:** Resolution options that emerge from discussion may include: write the new rule (override), discard this item, or update the existing config/rule instead.

### Confirmation Flow
- **D-08:** User **types the item numbers** they want to apply, e.g. `1, 3, 4`. Only listed items are written.
- **D-09:** Items not listed in the confirmation reply are silently discarded. No pending queue.
- **D-10:** After confirmation, all listed items are written in one pass. System reports what changed.

### Variables.csv Routing
- **D-11:** Feedback that touches a variable not in Variables.csv routes as a **flag only** — no automatic write.
- **D-12:** System outputs: `⚠️ Variable @TPL_X@ may be missing from Variables.csv. Verify against BO before adding manually.`
- **D-13:** Variables.csv is treated as read-only by this system. It is sourced from BO and must not drift out of sync via manual edits.

### Claude's Discretion
- How to detect which destination file a feedback item belongs to (routing classification logic)
- Exact wording of the collection template to give the employee
- How to parse the Language + Issue format (handling typos, missing fields, extra whitespace)
- How Step 7 announces the batch flow vs. the existing single-item flow

</decisions>

<specifics>
## Specific Ideas

- The feedback pipeline is: native speakers → employee collects + structures → Juan reviews → Juan pastes into chat. The system should acknowledge this workflow and provide a format the employee can use.
- The employee-facing collection format should be simple enough that non-technical people can fill it out correctly without training.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Step 7 (the extension point)
- `.claude/commands/review-translations.md` §Step 7 — Full existing feedback loop: prompt, conflict check (7a), write logic (7b), config file updates (7c), rules rebuild (7d), session confirm (7e). Phase 6 extends this, not replaces it.

### Feedback data structures
- `corrections/corrections_log.json` — Schema: 8-field correction entry. Language is always a single string per entry. `corrections` array is source of truth.
- `corrections/rules_summary.json` — Derived access layer, rebuilt from corrections_log after each session.

### Config files that are valid routing destinations
- `config/label_patterns.json` — `subject_variable_usage_rules` section: per-language variable routing rules
- `config/tone_guidelines.json` — `formality_rules`, `informal_standard_languages`, `formal_vous_languages`

### Config files that are read-only for this phase
- `config/Variables.csv` — 788 @TPL_*@ variable catalog. Flag-only destination (D-11 through D-13).

### Prior phase decisions
- `.planning/STATE.md` — All D-## decisions from Phase 3 (D-07 through D-20) governing corrections schema and conflict detection remain in force.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Step 7a conflict check**: Already implements a 3-way conflict detection against `review-translations.md`, `label_patterns.json`, and `tone_guidelines.json`. Phase 6 reuses this logic per batch item before display.
- **Step 7b write logic**: Already handles one-entry-per-market schema, confidence assignment (D-08), and 8-field structure. Phase 6 calls this per confirmed item.
- **Step 7c config update logic**: Already handles `label_patterns.json` and `tone_guidelines.json` updates when rules touch variable usage or formality.
- **Step 7d rules_summary rebuild**: Already does a full rebuild from corrections_log. Reused after batch apply.

### Established Patterns
- One entry per market per feedback item (never an array for `language` field)
- Conflict detection is silent on happy path, only surfaces on actual contradiction
- Step 7 is a sub-workflow within the skill — Phase 6 extends Step 7, not the skill's outer flow

### Integration Points
- Phase 6 modifies Step 7 in `.claude/commands/review-translations.md`
- The batch flow branches at the Step 7 prompt: if user pastes N items in Language+Issue format → batch routing mode; if user types report numbers (#N) → existing single-item mode
- After batch apply, 7d (rules_summary rebuild) still runs once at the end

</code_context>

<deferred>
## Deferred Ideas

- Importing feedback directly from Notion page comments — future milestone
- Automated CSV correction (tool proposes fixes, humans apply) — explicitly out of scope per REQUIREMENTS.md
- Pending queue for skipped batch items — not needed; items are checked before submission

</deferred>

---

*Phase: 06-batch-feedback-routing*
*Context gathered: 2026-04-10*
