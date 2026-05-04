# Phase 13: Standalone Feedback Skill - Context

**Gathered:** 2026-05-04
**Status:** Ready for planning

<domain>
## Phase Boundary

A new slash-command skill `/submit-feedback` lets the user submit translation corrections independently of any review session. The skill:

1. **Tags corrections with the real `notification_type`** when a report path is provided (extracted from the report header), or `"adhoc"` when no path is given.
2. **Backs up all four writable files** (`corrections_log.json`, `rules_summary.json`, `label_patterns.json`, `tone_guidelines.json`) and the new `variables_guide.md` before the session's first write.
3. **Surfaces all conflicts in one consolidated numbered list** with per-item `replace / append / dismiss`. The append branch runs a focused two-tier validation flow (agent self-check + user clarity check) before any write.
4. **Runs a pruning phase** at session end (stale / single-occurrence / low-confidence / superseded candidates), one-by-one, with `keep / archive / edit text / show full record`.
5. **Runs a Tier 1→Tier 2 promotion phase** for rules that meet `occ ≥ 3 AND confidence == high AND 30d stable`, one-by-one, with `promote / not yet / never / show full record`. Declined offers are tracked so they don't re-surface until criteria change.
6. **Surfaces Tier 2→Tier 3 candidates as advisory output only** — never edits `scripts/structural_validator.py`.

**Phase 13 also deletes the existing Step 7 block (lines 470–814)** from `.claude/commands/review-translations.md`, replacing it with a single pointer at the end of Step 6: `For corrections, run /submit-feedback`. This pulls the `PARALLEL-06` (Step 7 deletion) requirement forward from Phase 15.

</domain>

<decisions>
## Implementation Decisions

### Skill File Shape & Step 7 Fate

- **D-01:** Skill lives at `.claude/commands/submit-feedback.md` as a slash command (matches `review-translations.md` pattern). FEEDBACK-01 mandates `/submit-feedback` invocation.
- **D-02:** Inline all logic (conflict check, write logic, rules rebuild) in the skill file — no shared helper extraction. Step 7 is being deleted in this same phase, so there is no second consumer to justify a helper file. YAGNI.
- **D-03:** **SCOPE CHANGE** — Pull Step 7 removal forward into Phase 13. Phase 13 ships `/submit-feedback` AND deletes Step 7 (lines 470–814) from `review-translations.md`, replacing it with a one-line pointer at the end of Step 6: `For corrections, run /submit-feedback`. The existing `PARALLEL-06` requirement (Step 7 deletion) moves from Phase 15 to Phase 13. The planner adds a new requirement **FEEDBACK-12: Step 7 block removed from review-translations.md and replaced with pointer to /submit-feedback** and updates `.planning/REQUIREMENTS.md` and `.planning/ROADMAP.md` accordingly.

### `notification_type` Extraction (FEEDBACK-02)

- **D-04:** The report header line `**Notification**: <id>` is the **single source of truth** for `notification_type`. Strict regex `^\*\*Notification\*\*:\s*(\S+)` plus a content sniff requiring H1 `# Translation Quality Review`. Filename is path-only — never parsed for the value.
- **D-05:** When extraction fails (file unreadable, missing header, malformed value, wrong H1), **hard-fail with an actionable error**: `Could not extract notification_type from <path>. Expected '**Notification**: <id>' in header of a review report. Fix the report or rerun without a path (will tag as adhoc).` User must re-invoke. **No silent fallback to adhoc** when a path was supplied.
- **D-06:** Extracted `notification_type` is written to the `notification_type` field in `corrections_log.json` only (per Phase 3 D-03). No surfacing in session header, banner, or other config files.

### Config File Architecture (Routing Tree)

- **D-07:** **SCOPE ADDITION** — Create new file `config/variables_guide.md`, a human-readable per-variable documentation guide that complements the BO-sourced `Variables.csv` catalog. The planner adds a new requirement **FEEDBACK-11: variables_guide.md created and maintained as Tier 2 destination for variable-related rule promotions**.
- **D-08:** `variables_guide.md` initial structure: H2 categories grouped from `Variables.csv` (816 rows) analysis + the existing 10 categories already present in `label_patterns.json.variable_categories` (`general`, `category`, `subject`, `article_contractions`, `compound_phrases`, `city`, `department`, `region`, `level`, `landing`). H3 per variable with: `**Purpose:**`, `**Valid for:**`, `**Do NOT use for:**`, `**Notes:**`. The planner produces an initial seed file by analyzing `Variables.csv` and the existing `label_patterns.json.variable_categories` — the file ships populated, then grows via promotions.
- **D-09:** `Variables.csv` stays **read-only**. Phase 6 D-13 remains in force. `/submit-feedback` does NOT add new variables to `Variables.csv` — that gap is closed in Phase 14 by the BO extractor (deferred, see below).
- **D-10:** Variable-related feedback NEVER writes directly to `variables_guide.md` from a single feedback session. Writes happen only through the **Tier 1 → Tier 2 promotion path** (FEEDBACK-08/09), gated by `occ ≥ 3 AND confidence == high AND 30d stable AND user-approves`.
- **D-11:** **Routing tree (post-Phase-13)**:
  - **Variable-usage feedback** → Tier 1 (`corrections_log.json` + `rules_summary.json`) every session.
  - **Promotion** to Tier 2 (decision tree by rule type, see D-15):
    - Per-language variable rule → `label_patterns.json.subject_variable_usage_rules` (machine-readable) **AND/OR** `variables_guide.md` (human-readable, in the variable's H3 section). Claude drafts both writes when a rule is per-language AND describes variable behavior; user approves drafted text per file.
    - Formality / tone rule → `tone_guidelines.json.formality_rules` (and/or `brand_voice` / `common_issues`).
    - Other (e.g. Arabic word order in CTAs, language-general phrasing) → stays in Tier 1; surface in advisory output that no Tier 2 destination matches.
  - **Tier 2 → Tier 3** → advisory output only (FEEDBACK-10). Never auto-writes to `scripts/structural_validator.py`.
  - **New variable detected in translations but missing from `Variables.csv`** → flag-only at review time (status quo per Phase 6 D-11/D-12). Phase 14 BO extractor handles the catalog refresh.

### Append Sub-Dialogue (FEEDBACK-05)

- **D-12:** Append sub-dialogue questions are **adaptive**. Memory 2094 names three categories (contradictory? / different contexts? / boundary?). The agent inspects the two conflicting rules and asks ONLY the categories where the answer isn't obvious from the rule text. Skips obvious-answer categories. Fewer turns on simple conflicts; full depth when the conflict is genuine.
- **D-13:** Merged-rule preview format = **block with rule text + bilingual EN+FR examples** (per memory 2093). Display:
  ```
  **Merged rule:** [one sentence]
  **Why merged:** [one line]
  **Example (EN):** [example sentence]
  **Example (FR):** [example sentence]
  **Replaces:** rule_id_a, rule_id_b (will be archived)
  ```
  User confirms `clear` or types corrections.
- **D-14:** Agent self-check format = **inline triple-check block above the draft**:
  ```
  Self-check:
    ✓ Boundary explicit ([what's clear])
    ✓ Variable scope clear ([what's clear])
    ⚠ Edge case: [concern] — needs your input
  ```
  If any `⚠` rows: agent asks one targeted clarifying question BEFORE drafting the merged rule. The self-check is visible to the user — transparent reasoning over hidden internal validation.
- **D-15:** On successful append: archive both originals to **`corrections/archive/rules_archive.json`** (single archive file shared with pruning per FEEDBACK-07). Each archived entry stamps:
  - `reason: "merged_into:<new_rule_id>"`
  - `archived_at: <ISO timestamp>`
  - full original record
  Merged rule gets a new `rule_id`. Confidence = `max(orig_a.confidence, orig_b.confidence)` then downgraded one tier (per FEEDBACK-05 — `high → medium`, `medium → low`, `low` stays `low`).

### Promotion Routing & Decline Tracking (FEEDBACK-08/09)

- **D-16:** Tier 2 destination is selected by a **decision tree by rule type** (see D-11 routing tree). Claude drafts the write text for each destination; user approves text per file before write happens. Backups for the target file run before write, per FEEDBACK-03.
- **D-17:** Declined promotions are recorded in **`corrections/_promotion_offers.json`**. Schema per rule_id:
  ```json
  {
    "rule_id": "<id>",
    "last_offered_at": "<ISO>",
    "decision": "not_yet" | "never",
    "criteria_at_offer": {
      "occurrence_count": <n>,
      "confidence": "high",
      "last_seen": "<ISO>"
    }
  }
  ```
  The underscore prefix marks the file as system-internal.
- **D-18:** Re-surface trigger for `not_yet` decisions: **`current_occurrence_count > criteria_at_offer.occurrence_count`** (rule continued accumulating since the decline). `never` decisions are permanent — locked at Tier 1 unless the user manually clears the entry from `_promotion_offers.json`.

### Claude's Discretion

- **Empty-session lifecycle** — when user opens `/submit-feedback`, dismisses everything, and writes nothing: backups are skipped (FEEDBACK-03 says "before first write" — no write means no backup). Pruning and promotion phases still run since they're independent of new writes.
- **Tier 2→3 advisory output format (FEEDBACK-10)** — end-of-session console block listing candidate rules with their suggested validator-check pattern. No persisted file unless the user explicitly asks; recommendation: emit a `corrections/_tier3_advisory.md` snapshot only when at least one candidate exists, so the user can review later without rerunning the session.
- **Conflict-detection scope per item** — apply Phase 3 D-17/D-18/D-19 conflict logic per Tier 1 destination (`corrections_log.json` for same language + same `issue_category` + semantic similarity). The consolidated numbered list (FEEDBACK-04) groups conflicts across items in one display.
- **Session order**: backup-on-first-write → conflict scan → submission → write → rules_summary rebuild → pruning phase → promotion phase → Tier 2→3 advisory.
- **Bilingual example sourcing**: when feedback doesn't include EN+FR examples, the agent generates them from the rule and surfaces them in the self-check for user verification before they're written.
- **Backup of `variables_guide.md`** — covered by the same first-write backup convention as the four JSON files: `corrections/backups/YYYYMMDDTHHMMSSZ_variables_guide.md`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap

- `.planning/REQUIREMENTS.md` §FEEDBACK — FEEDBACK-01 through FEEDBACK-10 (locked acceptance criteria for the skill).
- `.planning/REQUIREMENTS.md` §PARALLEL — PARALLEL-06 (Step 7 deletion) — **moves from Phase 15 to Phase 13** per D-03; planner updates this file.
- `.planning/ROADMAP.md` §Phase 13 — current phase scope; planner updates to reflect D-03, D-07, and the new FEEDBACK-11/FEEDBACK-12 requirements.
- `.planning/PROJECT.md` — project core value statement; constraints (stdlib-only Python, no test infrastructure).

### Existing Skill (the file being rewritten)

- `.claude/commands/review-translations.md` §Step 7 (lines 470–814) — full existing feedback flow (single + batch). Source of behavior to lift into `/submit-feedback`. **Deleted in this phase**, replaced by a one-line pointer at end of Step 6.
- `.claude/commands/review-translations.md` §Step 0 — variable detection logic and `Variables.csv` reference.
- `.claude/commands/review-translations.md` §Step 3 — rules loading from `rules_summary.json` (top-3 per language, scoring formula).

### Prior Phase Decisions (still in force)

- `.planning/phases/03-feedback-loop-strengthening/03-CONTEXT.md` — Phase 3 D-01–D-20: 8-field corrections schema, one-entry-per-market rule, confidence assignment, pre-write conflict detection.
- `.planning/phases/06-batch-feedback-routing/06-CONTEXT.md` — Phase 6 D-01–D-13: batch input format `Language: / Issue:`, item-number confirmation, Variables.csv read-only flag-only routing, conflict block resolution flow.

### Data Files (writable by `/submit-feedback`)

- `corrections/corrections_log.json` — 8-field schema per entry: `language, notification_type, issue_category, original, corrected, rule_extracted, confidence, date`. One entry per market per feedback item (D-07 of Phase 3).
- `corrections/rules_summary.json` — derived index, full rebuild after each session (D-10 of Phase 3). Top-3 per language injected into AI reviewer at Step 3.
- `config/label_patterns.json` — `subject_variable_usage_rules` section is the Tier 2 destination for per-language variable-usage rules. Other top-level sections: `template_syntax`, `validation_rules`, `variable_patterns`, `variable_categories`, `block_scope_overrides`, `compound_phrases`.
- `config/tone_guidelines.json` — `formality_rules` is the Tier 2 destination for tone/formality rules. Sub-keys: `formal_vous_languages.languages`, `informal_standard_languages.languages`, `neutral_languages.languages`. Also: `brand_voice`, `common_issues`.

### Data Files (Tier 2 destinations / new in this phase)

- `config/variables_guide.md` — **NEW (created in this phase)**. Human-readable per-variable documentation. Tier 2 destination for variable-related rule promotions. Initial seed analyzed from `Variables.csv` + `label_patterns.json.variable_categories` by the planner.

### Data Files (read-only by `/submit-feedback`)

- `config/Variables.csv` — 816 rows (`Variable, Aide, Exemple de valeur`). Catalog source-of-truth from BO. Flag-only routing per Phase 6 D-13. Phase 14 (BO extractor) is the natural future write path.
- `scripts/structural_validator.py` — Tier 3 destination, advisory only (FEEDBACK-10). `/submit-feedback` never edits this file.
- `config/review_rules_compact.md` — read by `review-translations.md` Step 4; informs which rules the AI reviewer applies.

### Backup / Archive Locations

- `corrections/backups/YYYYMMDDTHHMMSSZ_<filename>` — per-session pre-write backups (FEEDBACK-03). Now also covers `variables_guide.md`.
- `corrections/archive/rules_archive.json` — single archive file for both pruning archives (FEEDBACK-07) AND merge archives (FEEDBACK-05 per D-15). `reason` field disambiguates.
- `corrections/_promotion_offers.json` — system-internal tracking of declined Tier 1→2 promotions (D-17).

### Memory & Architectural Decisions

- Memory 2093 — bilingual EN+FR examples requirement on grammar/language rules (encoded in D-13).
- Memory 2094 — bidirectional clarity check on append flow (encoded in D-12, D-14).
- Memory 2095 — three-tier rule lifecycle architecture (Tier 1 / Tier 2 / Tier 3).
- Memory 2096 — full v1.3 thread plan, including the three-tier promotion model.
- Memory 2098 — atomic FEEDBACK requirements 01–10.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- **Step 7a conflict check** (`review-translations.md` lines 532–536): three-way conflict detection against `corrections_log.json`, `label_patterns.json`, `tone_guidelines.json`. Lift into `/submit-feedback` and extend to also check `variables_guide.md` for promoted rules.
- **Step 7b write logic** (lines 599–619): per-market structured entry write with 8-field schema; confidence auto-assignment per Phase 3 D-08. Reuse verbatim.
- **Step 7c config update logic** (lines 609–617): updates `label_patterns.json` and `tone_guidelines.json`. Reuse and extend with `variables_guide.md` write path for D-11.
- **Step 7d rules_summary rebuild** (line 624): full rebuild from `corrections_log.json` after batch apply. Reuse as the post-write step.
- **Backup pattern** (line 586): `cp corrections/corrections_log.json corrections/corrections_log.backup.<TS>.json` — extend to four JSON files + `variables_guide.md` with the new `corrections/backups/YYYYMMDDTHHMMSSZ_<filename>` naming convention (FEEDBACK-03).

### Established Patterns

- All file writes are Claude-driven inline (not Python scripts run via Bash), except `structural_validator.py`. Preserve this in `/submit-feedback`.
- Config updates (`label_patterns.json`, `tone_guidelines.json`) are coupled with `corrections_log.json` writes — same coupling preserved in promotion writes.
- Batch input format `Language: / Issue:` (Phase 6 D-01) — keep as the user-facing input pattern in `/submit-feedback`.
- User confirmation by item-number list `1, 3, 4` (Phase 6 D-08) — reuse for the consolidated conflict resolution UX (FEEDBACK-04) and for promotion candidate selection.

### Integration Points

- `/submit-feedback` is a fresh skill file but logically replaces Step 7 in `review-translations.md`. The cut between the two: Step 6 ends with `For corrections, run /submit-feedback`. Lines 470–814 of `review-translations.md` are deleted in this phase.
- `variables_guide.md` is read at Step 0 of `review-translations.md`? — **no**, this is a human-facing reference. The AI reviewer continues to read `rules_summary.json` (Step 3) and `tone_guidelines.json` / `label_patterns.json` (Steps 1, 4). `variables_guide.md` is documentation, not runtime input.
- `_promotion_offers.json` is read at the start of every `/submit-feedback` session to know which rules NOT to re-offer.

</code_context>

<specifics>
## Specific Ideas

- The `variables_guide.md` initial seed should be derived from `Variables.csv` analysis. The planner is responsible for producing the first version of the file as part of this phase's plan. Categories must align with `label_patterns.json.variable_categories` keys.
- The "transparent self-check" pattern (D-14) was specifically requested over hidden internal validation — make sure the self-check block is always shown above the draft, even when all checks pass (`✓ ✓ ✓` is informative).
- Bilingual EN+FR examples are mandatory on append-flow rule previews (D-13). When feedback doesn't supply them, the agent generates them and lets the user verify in the self-check pass.
- "Never" decline (D-18) is the user's explicit "lock at Tier 1" signal — must remain permanent; do not add an automatic re-surface trigger for `never`.
- Phase 14 will be the natural place to close the `Variables.csv` drift gap (BO sync). Don't try to solve it in Phase 13.

</specifics>

<deferred>
## Deferred Ideas

- **BO extractor (Phase 14) auto-syncs `Variables.csv` from BO** — closes the catalog drift gap that Phase 6 D-13 was preserving. This is the natural place; surface as a Phase 14 planning input.
- **Restructuring `label_patterns.json` / `tone_guidelines.json` sections** if promoted rules don't fit existing schema — defer until first concrete promotion happens; revisit only if structure proves limiting.
- **`/document-variable` standalone skill** — alternative path to populate `variables_guide.md` outside the promotion flow. Not needed if promotions flow consistently; revisit if the guide stays stale.
- **Phase 15 scope reduction** — once `PARALLEL-06` (Step 7 deletion) moves to Phase 13, Phase 15 is now strictly URL detection + parallel reviews (PARALLEL-01 through PARALLEL-05, PARALLEL-07). Planner of Phase 15 should reflect this when re-scoping.

</deferred>

---

*Phase: 13-standalone-feedback-skill*
*Context gathered: 2026-05-04*
