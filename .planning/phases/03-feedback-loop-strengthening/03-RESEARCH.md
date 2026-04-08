# Phase 3: Feedback Loop Strengthening - Research

**Researched:** 2026-04-08
**Domain:** JSON schema design, rule ranking algorithms, Claude-inline file writes, skill prompt engineering
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Schema migration (FBK-01)**
- D-01: Migrate existing entries in-place to the new schema — rename fields, add missing ones with defaults. Do not leave a mixed-schema file.
- D-02: New schema has exactly 8 fields: `language`, `notification_type`, `issue_category`, `original`, `corrected`, `rule_extracted`, `confidence`, `date`
- D-03: `notification_type` stores the BO notification ID (e.g., `"reco-val-prof-bo"`, `"relance_3"`) — not a human-readable category label
- D-04: Field mapping for migration: `category` → `issue_category`, `notification_id` → `notification_type`, `original_text` → `original`, `corrected_text` → `corrected`, `extracted_rule` → `rule_extracted`
- D-05: Missing `confidence` field on migrated entries: `high` for the 2 empty-translation entries (objectively correct, seen in 2 markets), `medium` for the Lithuanian declension entry (its own description flags it as "needs native speaker verification")
- D-06: False-positive corrections (user dismissing a finding that was wrong): `original` = the flagged finding text, `corrected` = the dismissal reason/explanation

**Feedback session writes (FBK-02)**
- D-07: One corrections entry per market per feedback item — 20 feedback items in one session = 20 rows, each with a single `language` field at the top level
- D-08: Claude sets `confidence` automatically: `high` = user explicitly confirmed, or clear structural fact; `medium` = valid but context-dependent or linguistic nuance; `low` = speculative, needs native speaker verification, or inferred from ambiguous feedback

**rules_summary.json (FBK-03)**
- D-09: `rules_summary` array is removed from `corrections_log.json` — `rules_summary.json` is the single source of truth
- D-10: Full rebuild after each feedback session — recalculated from all corrections entries from scratch. No append logic.
- D-11: Duplicate rules (same pattern, multiple notifications) merged into one entry with `occurrence_count` incremented. Matching by language + issue_category + semantic similarity of `rule_extracted`.
- D-12: After saving, announce: `"Rules summary updated: N rules across M languages → corrections/rules_summary.json"`

**Top-3 rule retrieval (FBK-04)**
- D-13: Relevance score = `occurrence_count × recency_weight × confidence_score`. confidence_score: high=1.0, medium=0.75, low=0.5. recency_weight: 1.0 ≤30 days, 0.8 31–90 days, 0.6 90+ days.
- D-14: Surface top-3 per language. Pad with highest-scoring `"all"` language rules if fewer than 3 language-specific rules exist.
- D-15: Rules loaded silently — no per-language announcement.
- D-16: Load all rules upfront at Step 3 (one file read), cap at top-5 per language in context. If rules_summary.json exceeds 150 total rules, log: `"rules_summary.json has grown large (N rules) — consider pruning low-confidence entries."`

**Pre-write conflict detection (FBK-02 addition)**
- D-17: Before writing any new rule, Claude reads `review-translations.md` and relevant config files to check for contradictions.
- D-18: No conflict → write silently, confirm in one line.
- D-19: Conflict detected → do NOT write. Show conflict block with 3 options: write anyway / discard / update existing process instead.
- D-20: Only pause when conflict actually detected — no confirmation prompt on happy path.

### Claude's Discretion
- Exact recency_weight calculation (days since `last_seen` on the rule entry)
- Schema for rules_summary.json entries (should include: `rule`, `language`, `issue_category`, `occurrence_count`, `confidence`, `first_seen`, `last_seen`)
- Migration script approach (inline Python or Claude-written transformation)

### Deferred Ideas (OUT OF SCOPE)
- Pruning UI for low-confidence rules — the 150-rule warning covers this for now; dedicated pruning command is Phase 4 territory or beyond
- Backup of corrections_log.json before writes — listed as QUA-03 in v2 requirements, out of scope for this phase
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FBK-01 | corrections_log.json schema is structured with explicit fields: `language`, `notification_type`, `issue_category`, `original`, `corrected`, `rule_extracted`, `confidence`, `date` | Schema design, migration approach documented below |
| FBK-02 | Step 7 feedback workflow extracts structured rules and appends them with the above schema (not freeform text) | Step 7 rewrite pattern documented; conflict detection approach documented |
| FBK-03 | A `rules_summary.json` export is generated after each feedback session — flat list of extracted rules by language | rules_summary.json schema and rebuild algorithm documented below |
| FBK-04 | Review skill loads and surfaces the top 3 most relevant past rules per language at the start of each AI review | Relevance scoring algorithm and Step 3 injection pattern documented below |
</phase_requirements>

---

## Summary

Phase 3 is a pure skill-file and data-structure phase. No Python scripts are being written or modified — all logic lives inside `.claude/commands/review-translations.md` as Claude-executed instructions. The two deliverables are: (1) a structured `corrections_log.json` with a fixed 8-field schema, and (2) a derived `rules_summary.json` that Step 3 reads for per-language rule injection.

The current `corrections_log.json` has empty `corrections` and `rules_summary` arrays plus a `_schema` block that documents the old field names. This means there is zero data to migrate — the file needs a schema replacement (old `_schema` → new `_schema` matching the 8-field spec) but no row-by-row migration work. The CONTEXT.md references "3 existing entries" but the file as it stands today is empty; the planner should treat migration as a schema-definition task, not a data-transformation task.

The primary engineering challenge in this phase is the Step 7 rewrite: replacing one-line freeform `corrections_log.json > rules_summary` writes with per-market structured entries plus a full `rules_summary.json` rebuild, wrapped in pre-write conflict detection against the live skill file and config files.

**Primary recommendation:** Implement the two plans as specified in ROADMAP.md — 03-01 covers schema migration and Step 7 structured writes (FBK-01 + FBK-02); 03-02 covers rules_summary.json generation and Step 3 top-3 injection (FBK-03 + FBK-04). All changes are co-located in `review-translations.md` plus two JSON files in `corrections/`.

---

## Standard Stack

### Core (this project uses no external libraries for the feedback loop)

| Component | Format | Purpose | Why |
|-----------|--------|---------|-----|
| corrections_log.json | JSON, stdlib | Structured corrections store | Already established; Claude reads/writes directly |
| rules_summary.json | JSON, stdlib | Derived flat rules index | New file; same pattern as corrections_log.json |
| review-translations.md | Markdown skill | All Step 3 and Step 7 logic | Established project pattern — all review logic lives here |

### No new dependencies

This phase introduces no new Python packages, no new scripts, and no pip installs. All logic is Claude-inline instruction in the skill file. The established project constraint (stdlib only, no pip for functional logic) holds.

**Installation:** Nothing to install.

---

## Architecture Patterns

### Current State (what exists today)

```
corrections/
└── corrections_log.json         # { corrections: [], rules_summary: [], _schema: {...old fields...} }

.claude/commands/
└── review-translations.md       # Step 3: reads rules_summary from corrections_log.json
                                 # Step 7: freeform append to corrections_log.json > rules_summary
```

### Target State (after Phase 3)

```
corrections/
├── corrections_log.json         # { corrections: [...8-field entries], _schema: {...new fields...} }
└── rules_summary.json           # { generated: "ISO date", total_rules: N, rules: [...] }

.claude/commands/
└── review-translations.md       # Step 3: reads rules_summary.json, scores, injects top-3 per language
                                 # Step 7: structured per-market entries + rebuild + conflict detection
```

### Pattern 1: 8-Field Corrections Entry Schema

**What:** Each correction written by Step 7 must conform to exactly these 8 fields.
**When to use:** Every time a user provides feedback in Step 7.

```json
{
  "language": "lt",
  "notification_type": "relance_3",
  "issue_category": "grammar",
  "original": "The flagged text or finding description",
  "corrected": "The corrected text or dismissal reason",
  "rule_extracted": "Lithuanian nouns use accusative case after preposition 'po' — do not flag as grammar error",
  "confidence": "medium",
  "date": "2026-04-08"
}
```

**Field constraints:**
- `language`: ISO language code string (e.g., `"lt"`, `"ar"`, `"es_AR"`). Single value — no arrays.
- `notification_type`: BO notification ID from the review session (e.g., `"relance_3"`). NOT a category label.
- `issue_category`: One of: `grammar`, `tone`, `label`, `cultural`, `emoji`, `encoding`, `format`
- `confidence`: One of: `high`, `medium`, `low` — set by Claude, not user
- `date`: ISO 8601 date only, no time (e.g., `"2026-04-08"`)

### Pattern 2: rules_summary.json Schema (Claude's Discretion — Recommendation)

**What:** A flat, language-keyed array rebuilt after each feedback session.
**Design principle:** Self-describing — a future generation tool must be able to load this without reading corrections_log.json.

```json
{
  "generated": "2026-04-08",
  "total_rules": 12,
  "rules": [
    {
      "rule": "Lithuanian nouns use accusative case after preposition 'po' — do not flag as grammar error",
      "language": "lt",
      "issue_category": "grammar",
      "occurrence_count": 1,
      "confidence": "medium",
      "first_seen": "2026-04-08",
      "last_seen": "2026-04-08"
    },
    {
      "rule": "Empty translations in Kazakhstan and Thailand require full AI-generated content",
      "language": "all",
      "issue_category": "encoding",
      "occurrence_count": 2,
      "confidence": "high",
      "first_seen": "2026-04-08",
      "last_seen": "2026-04-08"
    }
  ]
}
```

**Key design choices:**
- `language` field may be `"all"` for universal rules (patterns seen across multiple markets where language is not the discriminating factor)
- `occurrence_count` starts at 1 and increments when a rule is merged (same language + issue_category + semantic match)
- `first_seen` and `last_seen` enable the recency_weight calculation in D-13
- `generated` and `total_rules` enable quick validation without parsing the full array

### Pattern 3: Relevance Scoring Algorithm (for Step 3)

**What:** Ranks rules per language to surface top-3 at review time.
**Formula (D-13):** `score = occurrence_count × recency_weight × confidence_score`

```
confidence_score mapping:
  high   → 1.0
  medium → 0.75
  low    → 0.5

recency_weight mapping (days since last_seen):
  0–30 days  → 1.0
  31–90 days → 0.8
  91+ days   → 0.6
```

**Algorithm:**
1. Load all rules from rules_summary.json upfront (one read at Step 3 start)
2. For each language being reviewed:
   a. Filter rules where `rule.language == target_language`
   b. Score each rule: `occurrence_count × recency_weight × confidence_score`
   c. Sort descending by score, take top-3
   d. If fewer than 3 language-specific rules: pad with top-scoring `"all"` language rules (scored same formula) until 3 reached
3. Cap at top-5 per language loaded into context (D-16)
4. If rules_summary.json has more than 150 total rules: log warning line

**Context injection (Step 3):**
The rules are injected silently into the review criteria for the language, not announced to the user. They appear as additional criteria within the existing 7-point review checklist (criterion 7: "Past corrections").

### Pattern 4: Pre-Write Conflict Detection (Step 7)

**What:** Before writing a new corrections entry, Claude checks whether the extracted rule contradicts anything in the live skill file or config files.

**Conflict targets to check:**
- `.claude/commands/review-translations.md` — criterion definitions, existing process steps
- `config/label_patterns.json` — `subject_variable_usage_rules` and `validation_rules`
- `config/tone_guidelines.json` — `formality_rules` lists

**Conflict signal:** A new rule says "do not flag X for language Y" but the skill's Step 4c says "always flag X" — or vice versa. A new rule says "use variable A for language Z" but label_patterns.json `use_for` list says variable B.

**Detection approach:** Claude reads the relevant section of the target file and compares the extracted rule text against it semantically. This is not a string match — it is an inference step. The instruction in Step 7 must be explicit: "Before writing, read [file] section [section] and check whether the new rule contradicts any existing behavior. If yes, stop and show the conflict block."

**Conflict block format (D-19):**
```
Conflict detected before writing:

New rule:       "[extracted rule]"
Conflicts with: [file] [section] — "[existing process]"

Which takes precedence?
1. Write the new rule anyway
2. Discard the new rule
3. Update the existing process instead
```

**Happy path:** No conflict detected → write the entry, confirm in one line (D-18, D-20).

### Anti-Patterns to Avoid

- **Do not keep rules_summary inside corrections_log.json**: D-09 is a hard split. The old `rules_summary` array in corrections_log.json must be removed and the file must contain only `corrections` and `_schema`.
- **Do not write a single multi-language entry**: D-07 mandates one entry per market per feedback item. An entry with `"language": ["ar", "ar_DZ"]` is wrong.
- **Do not incrementally append to rules_summary.json**: D-10 requires a full rebuild from all corrections entries. Append logic will miss merges and produce duplicate rules.
- **Do not prompt the user on every write**: D-20 — conflict detection is silent on the happy path. Prompting every write would break the UX.
- **Do not load full corrections_log.json into context in Step 3**: Load only rules_summary.json. The corrections_log.json can grow large; the derived summary file is the access layer.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON schema validation | Custom field-presence checker in Python | Claude's inline read-and-verify during Step 7 write | Step 7 is already a Claude-driven write; schema conformance is enforced at write time by instruction, not by a separate validator |
| Semantic similarity for rule merging | Vector embedding or fuzzy string match | Claude judgment during rules_summary rebuild | The rebuild is executed by Claude; semantic merge detection is a natural language inference task, not a string algorithm task |
| Rule ranking UI | Separate script or command | Inline scoring in Step 3 via rules_summary.json | All review logic lives in review-translations.md; adding a separate script breaks the established pattern |

**Key insight:** This project's architecture deliberately keeps all intelligence in the Claude skill file. Python scripts handle structural validation (mechanical, deterministic). Everything requiring judgment — including rule merging, conflict detection, and relevance ranking — stays as Claude-executed instructions. Don't break this boundary.

---

## Common Pitfalls

### Pitfall 1: Migrating Data That Doesn't Exist
**What goes wrong:** The planner writes a migration task assuming there are 3 existing entries to transform. The current `corrections_log.json` has empty arrays — there is nothing to migrate row by row.
**Why it happens:** CONTEXT.md references "3 existing entries" based on a prior state; the file was cleared.
**How to avoid:** The migration task is a schema redefinition task only: replace the `_schema` block with the new 8-field spec, remove the `rules_summary` array, leave `corrections` as `[]`.
**Warning signs:** Any plan step that iterates over existing corrections entries — this will be a no-op and should be simplified.

### Pitfall 2: Overloading Step 3 with Full corrections_log.json
**What goes wrong:** Step 3 loads corrections_log.json (which will grow) instead of the derived rules_summary.json. Context bloat on large logs.
**Why it happens:** Current Step 3 already reads corrections_log.json directly; it's the path of least resistance.
**How to avoid:** Step 3 must be updated to read rules_summary.json exclusively. The corrections_log.json is write-only from Step 3's perspective.
**Warning signs:** Any plan task that says "Step 3 reads corrections_log.json" — this is the old behavior.

### Pitfall 3: Conflict Detection Blocking Legitimate Writes
**What goes wrong:** Conflict detection is too aggressive — it halts on every new rule that mentions a variable or language, even when there's no actual contradiction.
**Why it happens:** The detection instruction is written too broadly ("check if any mention of X exists").
**How to avoid:** The conflict check is directional: does the new rule say "do NOT do X" when the skill says "DO X", or vice versa? Additive rules (new language-specific guidance not covered by existing rules) are not conflicts.
**Warning signs:** Users reporting that every feedback session triggers a conflict prompt.

### Pitfall 4: rules_summary.json "all" Language Rules Crowding Out Language-Specific Ones
**What goes wrong:** Top-3 padding from `"all"` rules fills all 3 slots for a language that has 0 specific rules. High-scoring general rules always win.
**Why it happens:** Padding is applied before checking if language-specific rules exist at all.
**How to avoid:** The algorithm is: score language-specific rules first, take top-N, then pad remaining slots from `"all"` rules. Language-specific rules always fill first, `"all"` rules only pad remaining slots.
**Warning signs:** A language with known specific rules (e.g., Arabic loop variable error) not having those rules surfaced.

### Pitfall 5: Merging Rules Across Languages
**What goes wrong:** The rebuild algorithm merges two entries that have the same issue_category but different languages (e.g., Arabic grammar rule merged with German grammar rule).
**Why it happens:** Merge matching only checks issue_category without also requiring language match.
**How to avoid:** D-11 is explicit: merge matching requires language + issue_category + semantic similarity. All three must match. An `"all"` rule can only merge with another `"all"` rule.
**Warning signs:** A language-specific rule appearing with `"language": "all"` after a rebuild.

---

## Code Examples

### New corrections_log.json Structure (after Plan 03-01)

```json
{
  "corrections": [],
  "_schema": {
    "correction": {
      "language": "ISO language code (string, single value — e.g. 'lt', 'ar', 'es_AR')",
      "notification_type": "BO notification ID (e.g. 'reco-val-prof-bo', 'relance_3')",
      "issue_category": "grammar | tone | label | cultural | emoji | encoding | format",
      "original": "The flagged text or finding description before correction",
      "corrected": "The corrected text or dismissal reason (for false-positive corrections)",
      "rule_extracted": "Generalized rule for future reviews",
      "confidence": "high | medium | low",
      "date": "ISO 8601 date (YYYY-MM-DD)"
    }
  }
}
```

**Changes from old schema:**
- Removed: `country`, `description`, `extracted_rule` → `rule_extracted`, `category` → `issue_category`, `notification_id` → `notification_type`, `original_text` → `original`, `corrected_text` → `corrected`
- Added: `confidence`
- Removed: entire `rules_summary` array (moved to rules_summary.json)

### Step 3 Replacement Logic (skill instruction pattern)

```
## Step 3: Load corrections history

Read `corrections/rules_summary.json`.

If the file does not exist, skip this step silently — no rules to apply.

If `rules_summary.json` has more than 150 total rules (check `total_rules` field),
log: "rules_summary.json has grown large ([N] rules) — consider pruning low-confidence entries."

For each language in the review batch, compute relevance scores:
  confidence_score: high=1.0, medium=0.75, low=0.5
  recency_weight: (days since rule.last_seen) 0-30→1.0, 31-90→0.8, 91+→0.6
  score = occurrence_count × recency_weight × confidence_score

For each language:
  1. Filter rules where rule.language == target_language, score and sort descending, take top-5
  2. If fewer than 3 language-specific rules: pad with top-scoring rules where rule.language == "all"
     until 3 total rules (or all available rules if fewer than 3 exist)
  3. Use the top-3 as additional criteria in Step 4c criterion 7

Apply rules silently — no per-language announcement. Count total rules applied across all languages.
If any rules loaded: "Applying [N] learned rules from previous reviews."
```

### Step 7 Replacement Logic (skill instruction pattern)

```
## Step 7: Feedback loop

[... existing menu and item listing unchanged ...]

When the user replies with numbers + notes, for each item:

1. PRE-WRITE CONFLICT CHECK:
   Read `.claude/commands/review-translations.md` (Steps 4c and 3 sections) and the relevant
   config file (label_patterns.json if the rule touches variable usage; tone_guidelines.json
   if it touches formality). Check whether the extracted rule contradicts any existing behavior:
   - A contradiction is: new rule says "do NOT flag X" and skill says "always flag X", or vice versa
   - A contradiction is: new rule says "use variable A for language Y" but config says "use variable B"
   - NOT a contradiction: new rule adds guidance for a case not covered by existing rules

   If conflict detected: STOP, show conflict block, wait for user choice before writing.
   If no conflict: proceed to write.

2. WRITE STRUCTURED ENTRY to corrections/corrections_log.json > corrections array:
   One entry per market per feedback item. Fields:
   - language: the market's ISO code (string, not array)
   - notification_type: the notification ID from this review session
   - issue_category: grammar | tone | label | cultural | emoji | encoding | format
   - original: the flagged finding text
   - corrected: the correction or dismissal reason
   - rule_extracted: generalized rule for future reviews
   - confidence: set automatically (high/medium/low per D-08)
   - date: today's date (YYYY-MM-DD)

3. UPDATE CONFIG FILES if applicable:
   - If rule touches variable usage → also update config/label_patterns.json > subject_variable_usage_rules
   - If rule touches tone/formality → also update config/tone_guidelines.json

4. REBUILD rules_summary.json from scratch:
   Read all entries in corrections_log.json > corrections.
   For each entry: check for an existing rule in rules_summary with same language + issue_category
   + semantically similar rule_extracted. If match: increment occurrence_count, update last_seen,
   update confidence to highest confidence seen. If no match: create new rule entry.
   Write full rebuilt rules_summary.json to corrections/rules_summary.json.
   Announce: "Rules summary updated: [N] rules across [M] languages → corrections/rules_summary.json"

5. CONFIRM session: "Updated [N] rules. Config files updated: [list or 'none']."
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Freeform text in rules_summary | Structured 8-field corrections entries | Phase 3 | Enables machine-readable filtering and scoring |
| rules_summary embedded in corrections_log.json | rules_summary.json as separate file | Phase 3 | Decouples access layer from raw corrections store |
| Load all rules for all languages | Load top-5 per language, score by relevance | Phase 3 | Prevents context bloat as rules accumulate |
| No conflict detection | Pre-write check against skill file and config | Phase 3 | Prevents rules from contradicting established behavior |

---

## Open Questions

1. **What happens if rules_summary.json is absent at Step 3?**
   - What we know: The file won't exist until after the first feedback session following Phase 3 deployment.
   - What's unclear: Should Step 3 abort or skip silently?
   - Recommendation: Skip silently — "If the file does not exist, skip this step silently — no rules to apply." This matches the behavior before Phase 3.

2. **How should the notification_type be determined when the user triggers Step 7?**
   - What we know: The notification ID is resolved in Step 1 and stored as a sanitized string.
   - What's unclear: Is the original unsanitized ID (e.g., `"relance_3"`) available at Step 7, or only the sanitized version (e.g., `"relance-3"`)?
   - Recommendation: Store the original notification ID at Step 1 in a named variable (`notification_id_raw`) and use it in Step 7 entries. If only sanitized is available, use that — the planner should verify in Step 1 what form the ID takes.

3. **Merge confidence: when two entries for the same rule have different confidence levels, which wins?**
   - What we know: D-11 says merge on semantic similarity, increment occurrence_count.
   - What's unclear: D-11 does not specify confidence resolution on merge.
   - Recommendation (Claude's Discretion): Use the highest confidence level seen across merged entries. A `high` confirmation from a later session should upgrade a `medium` initial entry.

---

## Sources

### Primary (HIGH confidence)
- Direct inspection of `.claude/commands/review-translations.md` (249 lines, 2026-04-08) — current Step 3 and Step 7 behavior confirmed
- Direct inspection of `corrections/corrections_log.json` — confirmed empty arrays, old schema present
- Direct inspection of `.planning/phases/03-feedback-loop-strengthening/03-CONTEXT.md` — all decisions D-01 through D-20 read verbatim

### Secondary (MEDIUM confidence)
- `config/label_patterns.json` and `config/tone_guidelines.json` — confirmed structure of conflict detection targets
- `scripts/structural_validator.py` — confirmed stdlib-only pattern for JSON read/write (reuse model for any inline migration)
- `.planning/config.json` — confirmed `nyquist_validation: false` (validation architecture section omitted), `commit_docs: true`

---

## Metadata

**Confidence breakdown:**
- Schema design: HIGH — all field names and types locked in CONTEXT.md D-01 through D-08
- Architecture patterns: HIGH — project conventions confirmed by direct file inspection
- Migration scope: HIGH — corrections_log.json is currently empty; migration is schema-only
- Pitfalls: HIGH — derived from direct reading of current skill behavior and CONTEXT.md constraints
- rules_summary.json schema: MEDIUM — schema fields are Claude's Discretion; recommendation above is derived from D-09 through D-12 requirements

**Research date:** 2026-04-08
**Valid until:** 2026-05-08 (stable domain — pure JSON schema and skill instruction work)
