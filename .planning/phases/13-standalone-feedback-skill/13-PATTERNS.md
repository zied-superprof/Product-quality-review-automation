# Phase 13: Standalone Feedback Skill - Pattern Map

**Mapped:** 2026-05-04
**Files analyzed:** 3 (1 create skill, 1 create doc, 1 modify skill); plus 3 system-internal data files derived from existing analogs
**Analogs found:** 6 / 6 — every new/modified file has a strong existing analog inside this repo

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `.claude/commands/submit-feedback.md` (CREATE) | command/skill (Claude-driven inline workflow) | event-driven · interactive (request → multi-turn dialog → file writes) | `.claude/commands/review-translations.md` Step 7 (lines 470–814) | exact (this is literally Step 7 lifted out) |
| `config/variables_guide.md` (CREATE) | human-readable documentation reference | static reference · read-by-human, written-by-promotion-flow | `config/label_patterns.json` `variable_categories` block (lines 49–181) + `config/Variables.csv` (rows 1–816) | role-match (no human-readable doc analog exists yet — closest is the structured `variable_categories` JSON) |
| `.claude/commands/review-translations.md` (MODIFY) | command/skill — surgical deletion + 1-line insert at end of Step 6 | n/a (edit only) | self (lines 388–469 = Step 6 tail; 470–814 = Step 7 to delete) | exact (file is its own analog) |
| `corrections/_promotion_offers.json` (CREATE, system-internal) | tracking/log JSON (per-rule decision history) | append-on-decline · read-on-session-start | `corrections/rules_summary.json` (top-level wrapper + per-rule array) | role-match (both are derived index files keyed by rule_id-like keys) |
| `corrections/archive/rules_archive.json` (CREATE, system-internal) | append-only archive JSON | append-on-prune / append-on-merge · never auto-read | `corrections/corrections_log.json` (`{ "corrections": [...] }` envelope, lines 1–2) | role-match (same envelope-of-records shape) |
| `corrections/_tier3_advisory.md` (CREATE, system-internal, conditional) | per-session advisory snapshot | written-on-session-end-if-candidates-exist | `reports/review-*.md` style emit (no exact analog — closest is the report generation in Step 6) | weak — see "No Analog Found" below |

## Pattern Assignments

### `.claude/commands/submit-feedback.md` (command/skill, event-driven interactive)

**Analog:** `.claude/commands/review-translations.md` (whole file, with Step 7 lines 470–814 as the dominant pattern source)

**Frontmatter pattern** (lines 1–3 of analog) — the skill needs the same YAML block at top:
```markdown
---
description: Review translation quality for Superprof notifications. Parses CSV, runs structural validation, performs AI quality review, and generates reports grouped by country and by notification.
---

# Translation Quality Review
```
Apply: write a 1-sentence `description:` for `/submit-feedback` (e.g. "Submit translation correction feedback. Tags entries with notification_type from a report path or 'adhoc', detects conflicts, and routes promotions across the three-tier rule lifecycle."), then H1 title.

**Step 0 / argument parsing pattern** (lines 9–23 of analog):
```markdown
## Step 0: Parse arguments

The user's message after the command may contain:
- A file path — the CSV to review (can be an absolute path, relative path, or filename only)
- `--languages XX,YY` — optional, only review these language codes
...

**Resolving the file path** (try in order):
1. If the user passed a path and it exists — use it directly.
2. ...
```
Apply: Step 0 of `/submit-feedback` parses an optional report path. When present and resolvable → run notification_type extraction (D-04). When absent → tag as `"adhoc"`. Mirror the numbered-resolution-order style.

**Hard-fail / abort pattern** (lines 46–48 of analog):
```markdown
**If any file fails to load or is missing, abort immediately** with:
`ABORT: [filename] not found or failed to parse. Cannot proceed with review.`
Do NOT continue to Step 2.
```
Apply: D-05 hard-fail uses the same imperative `ABORT:` style. Exact message per D-05: `Could not extract notification_type from <path>. Expected '**Notification**: <id>' in header of a review report. Fix the report or rerun without a path (will tag as adhoc).`

**Conflict-detection pattern** (lines 706–736 of analog — Step 7a-single):
```markdown
### 7a-single — Pre-write conflict check (per D-17 through D-20)

Before writing any correction or rule, read these files and check for contradictions:
- `.claude/commands/review-translations.md` — Steps 4c and 3 sections
- `config/label_patterns.json` — if the rule touches variable usage (check `subject_variable_usage_rules`)
- `config/tone_guidelines.json` — if the rule touches formality (check `formality_rules`)

**What counts as a conflict:**
- New rule says "do NOT flag X for language Y" but skill Step 4c says "always flag X" (or vice versa)
- New rule says "use variable A for language Z" but label_patterns.json `subject_variable_usage_rules` says use variable B
- ...

**If conflict detected** — do NOT write. Show:
```
Conflict detected before writing:

New rule:       "[extracted rule text]"
Conflicts with: [filename] [section] — "[existing rule or behavior text]"
...
```
Apply verbatim, then ADD a fourth file to the read-list per Phase 13 D-11: `config/variables_guide.md` (when the rule touches a specific variable's section).

**Consolidated numbered-list pattern** (lines 540–569 of analog — Step 7a-batch):
```markdown
Batch analysis complete — [N] items parsed:

#1 — [language_code]: [brief issue summary, max 10 words]
  → Routes to: [corrections_log.json | label_patterns.json | tone_guidelines.json | Variables.csv (flag only)]
  → Rationale: [one line — what will change and where]
  → Conflict: [none | ⚠️ Conflicts with [file] [section] — "[existing rule text]"]
...

After the block list, show the confirmation prompt:
Enter the item numbers you want to apply, separated by commas (e.g. 1, 3).
Items marked ⚠️ must be resolved before they can be included.
```
Apply: this IS the FEEDBACK-04 "all conflicts in one consolidated numbered list" UX. Lift verbatim, extend per-item action menu to `replace / append / dismiss` (D-12 — replaces the binary apply/discard with a tri-state per FEEDBACK-04).

**Backup pattern** (lines 584–592 + 778–781 of analog):
```bash
cp corrections/corrections_log.json "corrections/corrections_log.backup.$(date +%Y%m%d-%H%M%S).json"
```
**REPLACE** with the new convention (already in use under `corrections/backups/` — see existing files `20260428T152501Z_corrections_log.json` and `20260428T152501Z_rules_summary.json`):
```bash
TS=$(date -u +%Y%m%dT%H%M%SZ)
cp corrections/corrections_log.json "corrections/backups/${TS}_corrections_log.json"
cp corrections/rules_summary.json "corrections/backups/${TS}_rules_summary.json"
cp config/label_patterns.json "corrections/backups/${TS}_label_patterns.json"
cp config/tone_guidelines.json "corrections/backups/${TS}_tone_guidelines.json"
cp config/variables_guide.md "corrections/backups/${TS}_variables_guide.md"
```
The `T...Z` UTC stamp matches files already on disk (FEEDBACK-03). Run **once per session, before the first write only** (analog comment: "This backup runs once per feedback session, before the first write. Do NOT backup before each individual item write." — keep that exact note in the new skill).

**8-field write pattern** (lines 738–769 of analog — Step 7b):
```markdown
For each feedback item, write ONE entry per market to `corrections/corrections_log.json` > `corrections` array. If a feedback item applies to 5 markets, that is 5 separate entries — each with a single `language` string value (per D-07).

Each entry has exactly these 8 fields:
{
  "language": "[market ISO code — string, not array, e.g. 'ar', 'lt', 'es_AR']",
  "notification_type": "[BO notification ID from this review session, e.g. 'relance_3']",
  "issue_category": "[one of: grammar | tone | label | cultural | emoji | encoding | format]",
  "original": "[the flagged finding text from the report]",
  "corrected": "[the corrected text, OR dismissal reason if false-positive per D-06]",
  "rule_extracted": "[generalized rule for future reviews — what should Claude remember]",
  "confidence": "[high | medium | low — set automatically per D-08]",
  "date": "[today's date as YYYY-MM-DD]"
}

**Confidence assignment (D-08):**
- `high`: user explicitly confirmed the correction, OR it is a clear structural fact ...
- `medium`: correction is valid but context-dependent ...
- `low`: flagged as speculative ...
```
Reuse verbatim. Only the `notification_type` value source changes per D-04/D-05 — extracted from report header, or `"adhoc"` if no path. No more `"batch-feedback"` literal (which was the old Step 7a-batch convention at line 566).

**Routing decision-tree pattern** (lines 515–528 of analog — Step 7a-batch route_each_item):
```markdown
For each parsed item (language, issue_text), determine the routing destination using this decision tree:

1. **Variable mention check**: Does issue_text mention a `@TPL_*@` variable name?
   - YES: Read `config/Variables.csv` and check if the variable exists ...
     - Variable NOT in Variables.csv → destination: `Variables.csv (flag only)`. Output: `⚠️ Variable @TPL_X@ may be missing from Variables.csv. Verify against BO before adding manually.`
     - Variable IS in Variables.csv AND issue is about which variable to use ... → destination: `label_patterns.json`. Write target: `subject_variable_usage_rules.[VARIABLE_NAME]`.
     - Variable IS in Variables.csv AND issue is about translation quality around a variable (grammar, phrasing) → destination: `corrections_log.json`.
   - NO: continue to step 2.

2. **Formality/tone check**: Does issue_text mention formality, register, tone ...
   - YES → destination: `tone_guidelines.json`. ...

3. **Default** → destination: `corrections_log.json`. Write as a standard 8-field entry via 7b.
```
Apply per Phase 13 D-11 routing tree: this is the **Tier 1** decision tree — every item lands in `corrections_log.json` + `rules_summary.json` first. Reuse the YES/continue branching style. ADD a Tier 2 destination row for promotion-time only: per-language variable rules can ALSO write to `variables_guide.md` (drafted by Claude, user approves text per file before the per-file backup runs).

**Rebuild-once pattern** (lines 621–628 of analog — Step 7d-batch):
```markdown
After ALL confirmed items have been written, run the 7d rebuild logic exactly once:
- Read ALL entries in `corrections/corrections_log.json` > `corrections`
- Rebuild `corrections/rules_summary.json` from scratch (full rebuild, not append)
- Follow the same deduplication and scoring logic as the existing 7d section

Do NOT run 7d after each item — run it once at the end (avoiding Pitfall 2 from RESEARCH.md).
```
Reuse verbatim. The "rebuild once" cadence is the canonical pattern — also fits the post-pruning and post-promotion phases.

**rules_summary.json rebuild schema** (lines 783–810 of analog):
```markdown
For each correction entry:
1. Check if a rule already exists in the rebuild with same `language` + same `issue_category` + semantically similar `rule_extracted` (per D-11)
2. If match: increment `occurrence_count`, update `last_seen` to the later date, update `confidence` to the highest level seen (high > medium > low)
3. If no match: create new rule entry:
{
  "rule": "[the rule_extracted text]",
  "language": "[language code, or 'all' for universal patterns]",
  "issue_category": "[category]",
  "occurrence_count": 1,
  "confidence": "[confidence level]",
  "first_seen": "[date from correction]",
  "last_seen": "[date from correction]"
}

Write the full file:
{
  "generated": "[today's date YYYY-MM-DD]",
  "total_rules": [N],
  "rules": [... all rule entries ...]
}
```
Reuse verbatim. The fields `occurrence_count`, `confidence`, `last_seen` ARE the inputs to the FEEDBACK-08 promotion gate (`occ ≥ 3 AND confidence == high AND 30d stable`).

**Output-summary pattern** (lines 632–643 of analog):
```markdown
Batch feedback applied:
- [N] corrections written to corrections_log.json
- [M] config updates: [list of files updated, e.g. "label_patterns.json (2 rules), tone_guidelines.json (1 rule)"]
- rules_summary.json rebuilt: [total_rules] rules across [languages] languages
- [K] items discarded (not confirmed)
- [J] items flagged as Variables.csv warnings (informational only)
```
Apply: extend with new lines for the new phases — `[A] rules archived (pruning)`, `[B] rules promoted to Tier 2 ([destinations])`, `[C] Tier 3 advisory candidates surfaced`.

**Collaborative resolution pattern** (lines 645–679 of analog — Step 7c-batch):
```markdown
After the batch apply (7b-batch) completes, if any items were marked with ⚠️ conflicts in the block list:

For each conflicted item, show the full conflict context:

Conflict — Item #[N] ([language]: [brief issue]):

New rule:       "[the rule that would be written]"
Conflicts with: [filename] [section] — "[existing rule or config value]"

Let's discuss — what should we do with this conflict?

Discuss the conflict with the user. There is no fixed menu — the resolution emerges from discussion. Common outcomes include:
- **Write the new rule anyway** (override the existing config): proceed with 7b/7c write for this item, then rebuild 7d.
- **Discard this item**: skip it entirely. Acknowledge: "Item #[N] discarded."
- **Update the existing config instead** ...
```
Apply per FEEDBACK-04 / D-12: REPLACE the open-ended discussion with a fixed `replace / append / dismiss` tri-state action menu. The "append" branch then runs the FEEDBACK-05 sub-dialogue (D-12 adaptive questions, D-13 merged-rule preview, D-14 self-check block).

---

### `config/variables_guide.md` (documentation, static reference)

**Analog:** `config/label_patterns.json` `variable_categories` block (lines 49–181) — same 10 categories, same per-variable structure. Plus `config/Variables.csv` for the rest of the catalog data.

**Category-list pattern** — the 10 categories in `variable_categories` (label_patterns.json lines 49–181) become the H2 headings in `variables_guide.md`. Verbatim list per D-08:
1. `general` (lines 50–63)
2. `category` (lines 65–77)
3. `subject` (lines 79–89) — **most-trafficked** for the AI reviewer; densest H3 section
4. `article_contractions` (lines 91–113)
5. `compound_phrases` (lines 114–124) — **the `TPL_MATIERE_DE_MATIERE` family lives here**
6. `city` (lines 125–135)
7. `department` (lines 137–146)
8. `region` (lines 148–156)
9. `level` (lines 158–170)
10. `landing` (lines 172–180)

**Per-variable structure pattern** (label_patterns.json lines 81–89, the `subject` category):
```json
{"name": "TPL_MATIERE", "notes": "Subject name (e.g., Histoire)"},
{"name": "TPL_MATIERE_MINUS_SMART", "notes": "Subject name all lowercase — all-caps words (e.g. ESOL) left untouched"},
{"name": "TPL_MATIERE_FIRST_MAJUS_SMART", "notes": "Subject name first letter capitalized, rest lowercase — all-caps words (e.g. ESOL) left untouched"}
```
Convert each entry to an H3 + four bold labels per D-08:
```markdown
### `@TPL_MATIERE_MINUS_SMART@`

**Purpose:** Subject name all lowercase. Smart variant — all-caps words like `ESOL`/`TEFL` are left untouched.

**Valid for:** pl, sk, cs, ro, ru, uk, bg, sr, hr, sl, el, hu, lt, lv, et, no, es (and es_AR) mid-sentence

**Do NOT use for:** en, de, nl, sv, da, fi (use `@TPL_MATIERE_FIRST_MAJUS_SMART@` instead in title position)

**Notes:** Preferred over `@TPL_MATIERE_MINUS@` and `@TPL_MATIERE_NOM@` for declension languages. Norwegian: confirmed brand standard 2026-04-20.
```

**`use_for` / `do_not_use_for` pattern** — pull directly from `label_patterns.json.subject_variable_usage_rules` (lines 182–212). Example for `TPL_MATIERE_DE_MATIERE` (lines 184–192):
```json
"TPL_MATIERE_DE_MATIERE": {
  "description": "Article + subject name compound (e.g. 'd'histoire', 'de matemáticas'). Valid for any language that uses grammatical declension or article+noun constructions configured in the BO subject settings.",
  "use_for": ["fr", "pt", "it", "ar", "pl", "sk", "cs", "ro", "ru", "uk", "bg", "sr", "hr", "sl", "el", "hu", "lt", "lv", "et"],
  "do_not_use_for": ["en", "es", "de", "nl", "sv", "no", "da", "fi", "tr", "ko", "ja", "zh", "zh-TW", "th", "vi", "id", "ms", "he"],
  "important": "NOT limited to French. ...",
  "language_notes": { "lt": "Lithuanian uses genitive case ..." }
}
```
For variables that have a `subject_variable_usage_rules` entry → render the `use_for` / `do_not_use_for` arrays into the H3 section directly. For variables that do NOT have one yet → leave `**Valid for:** _(BO-configurable; see Variables.csv for default)_` as the seed placeholder. Promotions populate this over time.

**Variables.csv enrichment pattern** (Variables.csv lines 1–25):
```csv
Variable,Aide,Exemple de valeur
@TPL_ANNONCE_PRIX_DEVISE@,Prix de l'annonce formatté avec la devise,40€
@TPL_ANNONCE_TITRE@,Titre de l'annonce,Adasdas jdnasd ...
@TPL_ANNONCE_URL_EDITE@,Url d'edition de l'annonce,https://www.superprof.com/dashboard.html/my-listings/listing/14182587
```
For each H3 section, the `Aide` column → seeds `**Purpose:**` and the `Exemple de valeur` column → seeds the description tail. The 816 rows means the seed file is large — the planner should sequence the seed generation by category, not all-at-once.

**Important boundary** (D-09 / D-10): `variables_guide.md` is **NEVER** edited by a single feedback session. The skill writes to it ONLY through the Tier 1 → Tier 2 promotion path, and only after a per-file backup + per-file user approval of drafted text.

---

### `.claude/commands/review-translations.md` (modification — surgical edit)

**Analog:** the file itself. Two edits:

**Edit 1 — Insert pointer at end of Step 6** (insert after line 468):

Existing line 468:
```markdown
After the announcement, proceed to Step 7 regardless of Notion success or failure.
```
Replace with:
```markdown
For corrections, run /submit-feedback.
```
(Per D-03 verbatim — one line, no preamble, no formatting.)

**Edit 2 — Delete Step 7 entirely** (delete lines 470–814):

Existing block to delete starts at:
```markdown
## Step 7: Feedback loop

> **Batch mode available**: This step also works in a fresh session ...
```
…through end-of-file (line 814):
```markdown
"Updated [N] rules. Config files updated: [list or 'none']."
```
Delete the entire 345-line span. Resulting file shrinks from 814 → ~469 lines.

**Coupling rule:** Per FEEDBACK-12 (added by planner) and `.planning/REQUIREMENTS.md` §PARALLEL — `PARALLEL-06` MOVES from Phase 15 to Phase 13. Planner must touch `.planning/REQUIREMENTS.md` and `.planning/ROADMAP.md` to reflect the move.

---

### `corrections/_promotion_offers.json` (system-internal tracking, append-on-decline)

**Analog:** `corrections/rules_summary.json` (lines 1–13 envelope shape).

**Envelope pattern** (rules_summary.json lines 1–4):
```json
{
  "generated": "2026-04-14",
  "total_rules": 5,
  "rules": [
```
Apply (D-17 schema):
```json
{
  "generated": "2026-05-04",
  "total_offers": 0,
  "offers": [
    {
      "rule_id": "<id>",
      "last_offered_at": "<ISO>",
      "decision": "not_yet",
      "criteria_at_offer": {
        "occurrence_count": 3,
        "confidence": "high",
        "last_seen": "<ISO>"
      }
    }
  ]
}
```
Underscore prefix on filename = system-internal convention (D-17). Read at session start to filter promotion candidates per D-18 re-surface rule.

**Re-surface logic** (D-18): on every promotion phase, for each rule in `rules_summary.json` that meets the FEEDBACK-08 gate, look up its `rule_id` in `_promotion_offers.json`:
- not present → offer
- `decision == "not_yet"` AND `current.occurrence_count > criteria_at_offer.occurrence_count` → re-offer
- `decision == "not_yet"` AND counts match → suppress
- `decision == "never"` → suppress permanently (manual edit only)

---

### `corrections/archive/rules_archive.json` (system-internal append archive)

**Analog:** `corrections/corrections_log.json` (lines 1–2 envelope).

**Envelope pattern** (corrections_log.json lines 1–2):
```json
{
  "corrections": [
    {
      "language": "hu",
      "notification_type": "relance-1",
      ...
```
Apply:
```json
{
  "archived": [
    {
      "rule_id": "<original_id>",
      "reason": "merged_into:<new_rule_id>" | "pruned:stale" | "pruned:single_occurrence" | "pruned:low_confidence" | "pruned:superseded",
      "archived_at": "<ISO timestamp>",
      "original_record": { ... full pre-archive rule entry ... }
    }
  ]
}
```
Per D-15 — single shared archive for both pruning (FEEDBACK-07) and merge (FEEDBACK-05). The `reason` field is the discriminator. The directory `corrections/archive/` does not exist yet — the skill creates it on first archive write (`mkdir -p corrections/archive`).

---

### `corrections/_tier3_advisory.md` (system-internal, conditional emit)

**No close analog.** This is a small per-session markdown snapshot emitted only when the Tier 2→Tier 3 advisory pass identifies at least one validator-check candidate (FEEDBACK-10, Claude's Discretion item in CONTEXT.md line 100).

**Closest reference** — the report-emit cadence in Step 6 of `review-translations.md` (file path is fixed, contents are session-derived). Apply minimal structure:
```markdown
# Tier 3 Validator Candidates — <ISO timestamp>

## Candidate 1: <rule summary>
**Rule:** <text>
**Languages:** <list>
**Suggested validator check:** <pseudo-code or pattern description>
**Source rule_id:** <id from rules_summary.json>

## Candidate 2: ...
```
The skill never edits `scripts/structural_validator.py` (D-11 absolute, FEEDBACK-10).

---

## Shared Patterns

### Backup convention (FEEDBACK-03)
**Source:** existing files on disk under `corrections/backups/` (e.g. `20260428T152501Z_corrections_log.json`, `20260428T152501Z_rules_summary.json`)
**Apply to:** every writable file in this phase — `corrections_log.json`, `rules_summary.json`, `label_patterns.json`, `tone_guidelines.json`, `variables_guide.md`
**Pattern:**
```bash
TS=$(date -u +%Y%m%dT%H%M%SZ)
cp <source> "corrections/backups/${TS}_$(basename <source>)"
```
Run once per session, before the first write to that specific file. Empty-session = no backups (per CONTEXT.md "Empty-session lifecycle"). When a promotion writes to a new destination mid-session, that destination's backup runs at that point (per-file first-write trigger, not per-session).

### Numbered-list confirmation UX
**Source:** `.claude/commands/review-translations.md` lines 540–569 (Step 7a-batch block list) AND lines 686–702 (Step 7 numbered index for feedback)
**Apply to:** consolidated conflict list (FEEDBACK-04), pruning candidates (FEEDBACK-07, one-by-one), promotion candidates (FEEDBACK-08/09, one-by-one)
**Pattern:** every multi-item dialog uses `#N — <one-line summary>` with action keywords below. Confirmation accepts comma-separated numbers `1, 3, 4` or single-item action keywords (`replace / append / dismiss`, `keep / archive / edit text / show full record`, `promote / not yet / never / show full record`).

### Inline Claude-driven file writes (no helper scripts)
**Source:** `.claude/commands/review-translations.md` lines 738–810 (Step 7b/7c/7d all done inline by Claude, not a Python script)
**Apply to:** all file writes in `/submit-feedback`. The only Python script the project runs is `scripts/structural_validator.py`, which `/submit-feedback` never invokes (D-11). Decision per D-02: **inline all logic** — no shared helper extraction. Reaffirms YAGNI.

### Hard-fail abort with actionable error
**Source:** `.claude/commands/review-translations.md` lines 46–48 (`ABORT: ...`)
**Apply to:** notification_type extraction failure (D-05), invalid promotion offer file (parse error), archive directory creation failure
**Pattern:** single-line `ABORT: <what failed>. <actionable next step>.` then stop. No silent fallback unless explicitly designed (D-05 is explicit: no silent fallback to adhoc when a path was supplied).

### Confidence assignment ladder (D-08 of Phase 3, line 766–769 of analog)
**Source:** `.claude/commands/review-translations.md` lines 766–769
**Apply to:** every new corrections_log.json write in `/submit-feedback`
**Pattern:** unchanged — high (explicit confirmation OR structural fact), medium (context-dependent / linguistic nuance), low (speculative). Append flow per D-15 downgrades the merged rule's confidence one tier from `max(orig_a, orig_b)`.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `corrections/_tier3_advisory.md` | per-session conditional snapshot | written-on-end-of-session | No prior file is conditional + session-stamped + markdown. The Step 6 report path is the closest, but reports are mandatory and language-grouped — different shape. The planner should design the file shape from D-11 + the Claude's Discretion bullet on line 100 of CONTEXT.md, NOT copy from any existing file. |

The append-flow self-check block (D-14) and the merged-rule preview block (D-13) also have no in-codebase analog — they are new UX inventions specific to this phase. The planner should treat the CONTEXT.md fenced code samples in D-13 / D-14 as the canonical templates and embed them verbatim in the skill markdown.

---

## Metadata

**Analog search scope:**
- `.claude/commands/` (1 file: review-translations.md, 814 lines, full read across two passes covering lines 1–100, 385–469, 440–814)
- `config/` (label_patterns.json 237 lines, tone_guidelines.json 44 lines, Variables.csv 816 lines header sample)
- `corrections/` (corrections_log.json head, rules_summary.json head, backups/ directory listing)

**Files scanned:** 8

**Pattern extraction date:** 2026-05-04
