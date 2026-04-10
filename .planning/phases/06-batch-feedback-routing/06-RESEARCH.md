# Phase 6: Batch Feedback Routing - Research

**Researched:** 2026-04-10
**Domain:** Claude skill modification — Step 7 extension for batch input parsing, routing classification, conflict detection, and multi-file write
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01 — Batch Input Format**
Input uses a structured language + issue format, NOT report item numbers:
```
Language: es_AR
Issue: "vos" is Rioplatense standard, not an error

Language: ar
Issue: @TPL_MATIERE_DE_MATIERE@ inside <TPL_LOOP_ANNONCES> is correct here
```

**D-02 — Collection Template**
The system must document this format as a collection template for the employee who gathers native speaker feedback. Include the template in the Step 7 prompt or as a reference in the skill.

**D-03 — Session Independence**
Batch input is session-independent — works in a fresh session without an active report.

**D-04 — Routing Suggestion Display**
Shown as a block list — one entry per item: item number, language, issue summary, destination file, rationale, conflict status.

**D-05 — Conflict Blocking**
Items with conflicts are excluded from the apply batch until resolved.

**D-06 — Conflict Resolution**
Collaborative discussion to resolve conflicts — no fixed menu. Possible outcomes: write new rule (override), discard, or update existing config.

**D-07 — Confirmation by Number**
User types item numbers to confirm, e.g. `1, 3, 4`.

**D-08 — Confirmed-Only Apply**
Only listed items are written. Unlisted items are silently discarded. No pending queue.

**D-09 — One-Pass Write**
All confirmed items written in one pass with a change summary.

**D-10 — Variables.csv Read-Only**
Variables.csv is read-only for this system. Flag-only destination.

**D-11 — Variables.csv Flag Format**
`⚠️ Variable @TPL_X@ may be missing from Variables.csv. Verify against BO before adding manually.`

**D-12 — Variables.csv Not Written**
Variables.csv is sourced from BO — must not drift via manual edits.

**D-13 — Variables.csv Routing Flag**
Feedback touching a variable not in Variables.csv routes as a flag only.

### Claude's Discretion

- How to detect which destination file a feedback item belongs to (routing classification logic)
- Exact wording of the collection template to give the employee
- How to parse the Language + Issue format (handling typos, missing fields, extra whitespace)
- How Step 7 announces the batch flow vs. the existing single-item flow

### Deferred Ideas (OUT OF SCOPE)

- Importing feedback directly from Notion page comments — future milestone
- Automated CSV correction — explicitly out of scope per REQUIREMENTS.md
- Pending queue for skipped batch items — not needed; items are checked before submission
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FBK-05 | User can submit a batch of feedback comments in one go (not one-by-one) | Batch detection pattern at Step 7 entry point; Language+Issue format parsing |
| FBK-06 | For each comment the system analyzes and suggests routing action with rationale and conflict flag | Routing classification logic; conflict check reuse from Step 7a |
| FBK-07 | User confirms or rejects each suggestion; confirmed actions applied to correct file immediately | Number-based confirmation; write sequence reusing 7b/7c/7d |
</phase_requirements>

---

## Summary

Phase 6 is a pure skill modification — there are no new Python scripts, no new config files, and no new dependencies. The deliverable is a new section inside `.claude/commands/review-translations.md` that extends Step 7 with a batch input branch.

The existing Step 7 already implements: conflict detection (7a), structured correction writes (7b), config file updates (7c), and rules_summary rebuild (7d). Phase 6 wraps these into a loop — running the same logic for each batch item — then gates writes behind a single number-based confirmation. The architecture is additive, not a rewrite.

The routing classification problem (which destination file does a feedback item belong to?) is the main design question left to Claude's discretion. Research shows four clear destination buckets with well-defined routing signals: (1) corrections_log.json for language-specific translation quality rules, (2) label_patterns.json for variable usage rules, (3) tone_guidelines.json for formality/register changes, and (4) Variables.csv as a flag-only destination for unknown variable mentions.

**Primary recommendation:** Implement Phase 6 as a single-plan modification to Step 7. Add a batch mode branch that detects the Language+Issue format, loops the existing 7a conflict check per item, presents the block list display, collects number confirmation, then calls 7b/7c/7d once per confirmed item followed by a single 7d rebuild.

---

## Standard Stack

### Core

| Asset | Location | Purpose | Why Standard |
|-------|----------|---------|--------------|
| Step 7 in review-translations.md | `.claude/commands/review-translations.md` | The extension point — batch mode branches here | All feedback loop logic lives here per CONTEXT.md §code_context |
| corrections_log.json | `corrections/corrections_log.json` | Primary write target for correction entries | 8-field schema already defined; Phase 3 established it |
| rules_summary.json | `corrections/rules_summary.json` | Rebuilt after each batch apply; derived read layer | Full rebuild pattern already in Step 7d |
| label_patterns.json | `config/label_patterns.json` | Config update target for variable usage rules | `subject_variable_usage_rules` section is the write target |
| tone_guidelines.json | `config/tone_guidelines.json` | Config update target for formality/register rules | `formal_vous_languages`, `informal_standard_languages` are write targets |
| Variables.csv | `config/Variables.csv` | Read-only reference; flag-only routing destination | Sourced from BO; D-10 through D-13 prohibit writes |

### No New Dependencies

This phase installs nothing. It edits one Markdown file. No pip, npm, or MCP changes required.

---

## Architecture Patterns

### Integration Point: Step 7 Branch Detection

The batch flow and the existing single-item flow diverge at the Step 7 prompt. The branch condition is:

- **Batch mode trigger:** User input contains one or more blocks matching the pattern:
  ```
  Language: [code]
  Issue: [text]
  ```
  (Two or more items = batch mode. One item may also use this format and should be treated as a batch of one for consistency.)

- **Existing single-item mode trigger:** User types report item numbers (`#3 this variable is valid`) — the format used after a full review session.

The skill must detect which format was received and route accordingly. If the input is ambiguous, default to existing mode and ask for clarification.

### Pattern 1: Batch Mode Entry (Session-Independent)

The batch mode must work without an active report. This means Step 7 must be reachable as a standalone entry point — not just after Step 6.

**Implementation approach:** Add a new top-level prompt at the skill level, OR add a standalone invocation note at the start of Step 7. The simplest path is a brief note at the top of Step 7 saying:

> "This step can also be reached in a fresh session — just paste feedback items in the Language+Issue format and the system will route them."

No structural change to the skill's Step 0–6 is needed for session independence.

### Pattern 2: Routing Classification Logic

Each feedback item maps to exactly one destination. The routing signals are:

| Signal in Issue text | Destination | Write action |
|---------------------|-------------|--------------|
| Mentions a variable (`@TPL_*@`), its correct/incorrect placement, or which variable to use for a language | `label_patterns.json` | Update `subject_variable_usage_rules` for that language |
| Mentions formality, register, tone, "informal is correct", "vos/du/tu is brand standard", "formal address required" | `tone_guidelines.json` | Update `formality_rules` (add/move language between lists) |
| Variable name not found in Variables.csv | `Variables.csv` (flag only) | No write — output warning per D-11 |
| All other translation quality issues (grammar, cultural, emoji, phrasing, false positive) | `corrections_log.json` | Write structured entry per 7b schema |

**Disambiguation rule:** An item can produce writes to multiple destinations — e.g., a grammar correction also needs a formality note. In this case, the primary destination is the most specific one (label_patterns.json > tone_guidelines.json > corrections_log.json). The routing display shows the primary destination and notes secondary updates in the rationale.

### Pattern 3: Block List Display Format

Per D-04, the display format is:

```
#1 — es_AR: "vos" tone issue
  → Routes to: tone_guidelines.json
  → Rationale: formality classification update — es_AR should move to informal_standard_languages or get a market_note
  → Conflict: none

#2 — ar: variable placement
  → Routes to: label_patterns.json
  → Rationale: subject_variable_usage_rules — clarify correct variable inside TPL_LOOP_ANNONCES context
  → Conflict: ⚠️ Conflicts with existing rule in subject_variable_usage_rules.TPL_MATIERE_DE_MATIERE.use_for (ar is already listed)

#3 — de: "du" informal is brand standard
  → Routes to: tone_guidelines.json (and corrections_log.json)
  → Rationale: de is already in informal_standard_languages — this is a FALSE POSITIVE confirmation, not a new rule
  → Conflict: none
```

After the block list, show the confirmation prompt:

```
Enter the item numbers you want to apply, separated by commas (e.g. 1, 3).
Items with ⚠️ conflicts must be resolved before they can be included.
Items not listed will be discarded.
```

### Pattern 4: Conflict Check Per Item (Reuse of Step 7a)

The existing 7a conflict check reads three sources:
- `.claude/commands/review-translations.md` — Steps 4c and 3
- `config/label_patterns.json` — `subject_variable_usage_rules`
- `config/tone_guidelines.json` — `formality_rules`

For batch mode, run this check for each item BEFORE displaying the block list. Items with conflicts get the `⚠️ Conflict` flag in the display. They are excluded from the confirmation batch per D-05.

**Key difference from single-item flow:** In the existing Step 7a, a conflict blocks and asks immediately. In batch mode, conflicts are surfaced in the display, not as blocking prompts — so the user can confirm clean items and then address conflicts separately.

### Pattern 5: One-Pass Write After Confirmation

After the user types confirmed numbers:

1. For each confirmed item (in order): run 7b write (corrections_log.json entry), then 7c config update if applicable.
2. After all items written: run 7d once (single rules_summary rebuild).
3. Output the 7e summary listing exactly what changed.

This mirrors the existing single-item flow's write sequence, just batched.

### Pattern 6: Employee Collection Template

The template must be simple enough for a non-technical employee to fill out without training. Recommended wording (Claude's discretion — finalized in plan):

```
TRANSLATION FEEDBACK TEMPLATE
Fill in one block per issue. Copy-paste as many blocks as needed.

Language: [ISO code — e.g. es_AR, ar, de, fr]
Issue: [Describe what the AI reviewer got wrong. Was it a false positive? Wrong variable? Wrong tone?]

Language:
Issue:
```

Include this template as a comment or reference box inside the Step 7 prompt, OR as a collapsible note at the start of the batch flow branch.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Conflict detection | Custom checker | Reuse existing Step 7a logic verbatim | Already handles all three source files; proven in Phase 3 |
| Structured correction write | Custom schema builder | Reuse existing Step 7b pattern verbatim | 8-field schema is fixed; one-entry-per-market rule established in Phase 3 |
| Config file update | New update logic | Reuse existing Step 7c logic | Already handles both label_patterns.json and tone_guidelines.json |
| Rules summary rebuild | Incremental merge | Reuse existing Step 7d full rebuild | Full rebuild from source of truth avoids drift; pattern established in Phase 3 |
| Input parsing | Regex engine | Claude natural language understanding | The Language+Issue format is simple enough for inline string matching; no parser needed |

---

## Common Pitfalls

### Pitfall 1: Conflict Items Blocking Clean Items
**What goes wrong:** A conflict in item #2 blocks the entire batch — user cannot apply #1 and #3.
**Why it happens:** Porting the single-item blocking behavior directly to batch mode.
**How to avoid:** Surface conflicts in the display but only exclude those specific items from the confirmation set. Clean items proceed independently (D-05 specifies this explicitly).
**Warning signs:** If the implementation asks the user to resolve a conflict before showing the full block list, it has ported the wrong behavior.

### Pitfall 2: Running 7d (Rules Rebuild) Per Confirmed Item
**What goes wrong:** rules_summary.json is rebuilt N times — once after each write — producing redundant work and potential race conditions if something fails mid-batch.
**Why it happens:** Directly copying the single-item flow which runs 7d after each item.
**How to avoid:** Run 7b and 7c for all confirmed items first, then run 7d exactly once at the end.

### Pitfall 3: Treating Variables.csv as a Write Target
**What goes wrong:** System writes an unknown variable to Variables.csv as part of batch apply.
**Why it happens:** Over-extending the routing logic to include all four "destinations" as write targets.
**How to avoid:** Variables.csv routing always produces only the flag output (D-11). It is never included in the confirmed-items write pass.

### Pitfall 4: Requiring an Active Report for Batch Mode
**What goes wrong:** The batch mode calls code that references `ai_findings` or the report item index, which only exist after Step 6.
**Why it happens:** Step 7 was originally written as a post-report step; batch mode is session-independent.
**How to avoid:** The batch flow must not reference `ai_findings`, the numbered report index, or any session variable set by Steps 1–6. It reads only config files and corrections_log.json.

### Pitfall 5: Silently Merging Multi-Market Issues into One Corrections_Log Entry
**What goes wrong:** A batch item says "this variable is wrong for Arabic and Hebrew" — system writes one entry with `"language": ["ar", "he"]`.
**Why it happens:** The issue description mentions two markets; system treats it as one combined entry.
**How to avoid:** Per established D-07 from Phase 3, language is always a single string. Multi-market issues produce multiple entries, one per market. Batch parsing must split these.

### Pitfall 6: Discarding Conflict Context After Resolution Discussion
**What goes wrong:** After collaborative conflict resolution discussion (D-06), the item is re-queued but the resolved action is lost — user must re-confirm.
**Why it happens:** No mechanism to carry the resolved decision forward.
**How to avoid:** After conflict resolution, re-show the updated block list entry with conflict status changed to "resolved" and include it in a new confirmation prompt. Alternatively, apply it immediately if the user's resolution message is unambiguous.

---

## Code Examples

### Routing Classification Decision Tree

```
Given a batch item (language, issue_text):

1. Does issue_text mention a @TPL_*@ variable name?
   YES → Check Variables.csv:
     - Variable NOT in Variables.csv → route: Variables.csv (flag only, D-11)
     - Variable in Variables.csv AND issue is about WHICH variable to use / placement → route: label_patterns.json
     - Variable in Variables.csv AND issue is about translation quality around a variable → route: corrections_log.json
   NO → continue

2. Does issue_text mention formality, register, tone address form (vos/du/tu/vous/Sie/usted/Lei)?
   YES → route: tone_guidelines.json (and also corrections_log.json if there is a rule_extracted)
   NO → continue

3. Default → route: corrections_log.json
```

### Step 7 Entry Point Detection

```
At the start of Step 7, examine the incoming user input:

IF user input matches pattern:
  Line starting with "Language:" followed by a line starting with "Issue:"
  (one or more such blocks)
THEN → batch mode

ELSE IF user input contains "#N" pattern (report item numbers)
THEN → existing single-item mode

ELSE → ask for clarification: "Are you giving feedback on specific report items (#1, #2...) or submitting new feedback in Language+Issue format?"
```

### Block List Entry (per D-04)

```
#[N] — [language_code]: [brief issue summary, max 10 words]
  → Routes to: [corrections_log.json | label_patterns.json | tone_guidelines.json | Variables.csv (flag only)]
  → Rationale: [one line — what will change and where]
  → Conflict: [none | ⚠️ Conflicts with [file] [section] — "[existing rule text]"]
```

### Write Sequence (per confirmed items)

```
For item in confirmed_items:
  If item.destination == "corrections_log.json":
    Execute 7b write (one entry per market if issue spans multiple markets)
  If item.destination in ["label_patterns.json", "tone_guidelines.json"]:
    Execute 7c config update for that specific file
  If item.secondary_destination exists:
    Execute additional 7b or 7c write for secondary destination

After all items written:
  Execute 7d (rules_summary full rebuild — once only)
  Execute 7e summary
```

---

## Data Structure Reference

### corrections_log.json entry (8-field schema — unchanged from Phase 3)

```json
{
  "language": "es_AR",
  "notification_type": "batch-feedback",
  "issue_category": "tone",
  "original": "vos flagged as informal error",
  "corrected": "FALSE POSITIVE — vos is Rioplatense brand standard for es_AR",
  "rule_extracted": "es_AR: 'vos' is the confirmed brand standard (Rioplatense Spanish). Do not flag as informal.",
  "confidence": "high",
  "date": "2026-04-10"
}
```

Note: when batch feedback is not tied to a specific notification_type, use `"batch-feedback"` as the notification_type value. This distinguishes batch-sourced rules from session-specific ones in rules_summary.json.

### tone_guidelines.json update targets

- `formality_rules.informal_standard_languages.languages` — add market code here if feedback confirms informal is brand standard
- `formality_rules.formal_vous_languages.languages` — add market code here if feedback confirms formal is required
- `formality_rules.informal_standard_languages.market_notes` — add market-specific note (e.g., es_AR vos pattern)

### label_patterns.json update target

- `subject_variable_usage_rules.[VARIABLE_NAME].use_for` — add language code
- `subject_variable_usage_rules.[VARIABLE_NAME].do_not_use_for` — add language code
- `subject_variable_usage_rules.[VARIABLE_NAME].language_notes` — add language-specific note

---

## Plan Structure Recommendation

This phase is a single-plan modification. There is no dependency split warranting two plans.

**Recommended: one plan — 06-01**

Tasks:
1. Add batch mode detection branch to Step 7 (session-independent entry + format detection)
2. Implement routing classification logic (4-bucket decision tree)
3. Implement block list display with conflict flags (per D-04/D-05)
4. Add confirmation prompt and number parsing (per D-07/D-08)
5. Implement one-pass write sequence reusing 7b/7c; single 7d rebuild after all writes
6. Add employee collection template text to the Step 7 prompt (per D-02)
7. Test: verify existing single-item mode is undisturbed (branch detection must not break existing flow)

---

## Open Questions

1. **notification_type for batch entries**
   - What we know: The 8-field schema requires a `notification_type`. Batch feedback is not tied to a specific CSV review.
   - What's unclear: Should it be `"batch-feedback"`, `"general"`, or derived from whatever the user mentions?
   - Recommendation: Use `"batch-feedback"` as a sentinel value — makes batch-sourced entries distinguishable when auditing corrections_log.json.

2. **Partial conflict resolution mid-batch**
   - What we know: D-05 says conflicts block the item; D-06 says resolution is collaborative.
   - What's unclear: After resolving a conflict in discussion, does the resolved item get added to the apply set automatically, or does the user re-confirm?
   - Recommendation: After resolution, re-show that item with updated status and ask the user to include it in the confirmation number list if they want it applied. This keeps the confirmation step as the single apply gate.

3. **Multi-market batch items**
   - What we know: D-07 from Phase 3 mandates one entry per market in corrections_log.json.
   - What's unclear: The collection template asks for one language per block — but a user might write "Language: ar, he" or describe an issue affecting multiple markets.
   - Recommendation: If the language field contains multiple codes (comma-separated or listed), the skill should split them and create one entry per market automatically, announcing the split: "Item #2 applies to 2 markets — writing 2 entries."

---

## Sources

### Primary (HIGH confidence)
- `.claude/commands/review-translations.md` — Full Step 7 implementation read directly; Steps 7a through 7e documented
- `corrections/corrections_log.json` — 8-field schema confirmed from file; `_schema` object present
- `config/label_patterns.json` — `subject_variable_usage_rules` section read at line 182; routing targets confirmed
- `config/tone_guidelines.json` — `formality_rules` structure read; all three lists confirmed
- `.planning/phases/06-batch-feedback-routing/06-CONTEXT.md` — All D-01 through D-13 decisions and deferred items read

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` — FBK-05, FBK-06, FBK-07 requirements confirmed
- `.planning/STATE.md` — Phase 3 decisions D-07 through D-20 remain in force; confirmed from state file

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all files read directly; no external dependencies
- Architecture: HIGH — extension points, schemas, and branch conditions all verified from source
- Pitfalls: HIGH — derived from explicit schema constraints (D-07) and behavioral rules (D-05, D-20) read from canonical files
- Routing classification: MEDIUM — logic is Claude's discretion per CONTEXT.md; the four-bucket model is well-supported by file structure but exact wording is planner/implementer decision

**Research date:** 2026-04-10
**Valid until:** 2026-05-10 (stable domain — config file structure and Step 7 schema are unlikely to change without a new phase)
