# Phase 13: Standalone Feedback Skill - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-04
**Phase:** 13-standalone-feedback-skill
**Areas discussed:** Skill file shape & Step 7 fate, notification_type extraction, Config file architecture (variables_guide.md), Append sub-dialogue, Promotion routing & decline tracking

---

## Skill file shape & Step 7 fate

### Q1: Skill file location

| Option | Description | Selected |
|--------|-------------|----------|
| `.claude/commands/submit-feedback.md` (slash command) | Self-contained slash-command file matching `review-translations.md` pattern. | ✓ |
| `.claude/skills/submit-feedback/SKILL.md` (skill folder) | Auto-trigger skill with separate reference files. Pattern not used elsewhere in repo. | |
| `.claude/commands/submit-feedback.md + helpers` | Skill file plus shared `_feedback-helpers.md` reference. Adds indirection without an immediate caller. | |

**User's choice:** `.claude/commands/submit-feedback.md`
**Notes:** User initially asked whether the skill would be shared if they share the project folder. Clarified that all three options ship with the repo since `.claude/` is committed. The slash-command pattern matches FEEDBACK-01's `/submit-feedback` invocation requirement.

### Q2: Step 7 fate

| Option | Description | Selected |
|--------|-------------|----------|
| Pull Step 7 removal into Phase 13 | Phase 13 ships `/submit-feedback` AND deletes Step 7. PARALLEL-06 moves from Phase 15 to Phase 13. | ✓ |
| Keep Phase 15 sequencing | Step 7 stays in `review-translations.md` until Phase 15 deletes it. | |
| Soft-deprecate in Phase 13, hard-delete in Phase 15 | Banner on top of Step 7 plus standalone skill, then full deletion in Phase 15. | |

**User's choice:** Pull Step 7 removal into Phase 13
**Notes:** User flagged this in the initial multi-select — "If this skill is active we won't need the feedback request after doing a translation review." This is a scope change requiring REQUIREMENTS.md and ROADMAP.md updates by the planner.

### Q3: Helper extraction

| Option | Description | Selected |
|--------|-------------|----------|
| Inline everything in submit-feedback.md | Self-contained skill file. Step 7 is gone — no overlap. | ✓ |
| Extract shared helpers to a referenced file | `_feedback-helpers.md` for future reuse. | |
| Inline now, extract later if needed | Defer to a future phase if a second consumer appears. | |

**User's choice:** Inline everything in submit-feedback.md

---

## notification_type extraction

### Q1: Source of truth

| Option | Description | Selected |
|--------|-------------|----------|
| Header line `**Notification**: <id>` | Parse from report content. Filename is path-only. | ✓ |
| Filename pattern `review-{id}-DATE.md` | Parse from filename. Faster but less canonical. | |
| Header first, fallback to filename | Most resilient. | |

**User's choice:** Header line is source of truth

### Q2: Extraction failure behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Hard fail with actionable error | User must re-invoke. Prevents silent mistagging. | ✓ |
| Warn and fall back to adhoc | Flow continues, corrections get honest fallback tag. | |
| Ask user inline | Interactive prompt for the value. | |

**User's choice:** Hard fail with actionable error

### Q3: Format strictness

| Option | Description | Selected |
|--------|-------------|----------|
| Strict regex on header line + content sniff | Match header pattern AND verify H1 is `# Translation Quality Review`. | ✓ |
| Strict regex only | Match header pattern. Trust the user. | |
| Loose match (first `Notification:` occurrence) | Forgiving but risks body-text false positives. | |

**User's choice:** Strict regex + content sniff

### Q4: Tagging surface

| Option | Description | Selected |
|--------|-------------|----------|
| `corrections_log.json.notification_type` field only | Per Phase 3 D-03. Smallest blast radius. | ✓ |
| Also surface in session header | Banner so user can verify the right report was selected. | |

**User's choice:** `corrections_log.json` field only

---

## Config file architecture (variables_guide.md addition)

This area emerged from a free-form reflection prompted by the user, not from the original gray-area selection. The user noted that several config files (Variables.csv, label_patterns.json, tone_guidelines.json) were intended as human guidelines but in practice rarely got updated. The reflection led to a scope addition.

### Q1: Variables.csv update behavior

User asked: "What if I have a new variable, the variables file doesn't get updated?" — confirmed by reading the skill that `Variables.csv` is read-only by design (Phase 6 D-13). User then proposed a mix: keep `Variables.csv` read-only, but create a new human-readable `.md` file that the skill CAN write to.

**Decision:** Create new `config/variables_guide.md`. New requirement FEEDBACK-11 added. Initial seed derived from `Variables.csv` analysis + existing `label_patterns.json.variable_categories` (10 categories). Planner produces the seed file as part of the phase's plan.

### Q2: Trigger for writing to variables_guide.md

| Option | Description | Selected |
|--------|-------------|----------|
| Any feedback mentioning a variable's behavior | Wider write surface; guide actually grows. | |
| Only when a new variable is detected | Strict gate; guide grows slowly. | |
| Both | Auto-prompt on detect, opt-in route on usage feedback. | |

**User's choice (free text):** "Any feedback mentioned in a variable behavior research but is going to be modified only it has been gone through all the validation process that we set in place before. We were talking about graduating corrections. So keep that in mind"

**Interpretation:** Variable-related feedback first lands in Tier 1 (`corrections_log.json` + `rules_summary.json`). It only graduates to `variables_guide.md` after passing the full Tier 1→Tier 2 promotion gate (FEEDBACK-08/09). This means `variables_guide.md` becomes a high-trust mature reference, never a junk drawer.

### Q3: Structure of variables_guide.md

| Option | Description | Selected |
|--------|-------------|----------|
| Grouped by category, one section per variable | H2 categories, H3 per variable. Matches existing `variable_categories`. | ✓ |
| Flat alphabetical list | Simpler but loses category grouping. | |
| Two-tier: short reference table + detailed notes | Skim-first pattern. | |

**User's choice:** Grouped by category. Notes: "do it group by category. You have the CSV document, analyze it and structure the markdown based on that."

---

## Append sub-dialogue

### Q1: Question structure

| Option | Description | Selected |
|--------|-------------|----------|
| Adaptive — only ask categories that apply | Skip obvious-answer categories. | ✓ |
| Always ask all three in fixed order | Predictable but noisy on simple conflicts. | |
| Free-form discussion guided by the three | Less structured; risks skipping a category. | |

**User's choice:** Adaptive

### Q2: Merged-rule preview format

| Option | Description | Selected |
|--------|-------------|----------|
| Block with rule text + EN+FR examples | Bilingual per memory 2093. | ✓ |
| Rule text only, no examples | Faster but loses bilingual safety net. | |
| Rule + examples in user's choice of languages | Flexible but adds turn. | |

**User's choice:** Block with rule text + EN+FR examples

### Q3: Self-check format

| Option | Description | Selected |
|--------|-------------|----------|
| Inline triple-check block above the draft | Transparent reasoning. ⚠ rows trigger clarifying question before draft. | ✓ |
| Hidden self-check, surface only concerns | Cleaner; loses visibility. | |
| Self-check after draft, before write | Self-check on a concrete proposal. | |

**User's choice:** Inline triple-check block above the draft

### Q4: Append archive location

| Option | Description | Selected |
|--------|-------------|----------|
| `corrections/archive/rules_archive.json` (single file) | Shared with pruning archive. `reason` field disambiguates. | ✓ |
| Separate file: `corrections/archive/rules_merged.json` | Easier audit; more files to manage. | |

**User's choice:** Single archive file

---

## Promotion routing & decline tracking

### Q1: Tier 2 destination selection

| Option | Description | Selected |
|--------|-------------|----------|
| Decision tree: rule type → file | Variable-usage → label_patterns + variables_guide.md. Tone → tone_guidelines. Other → stays in Tier 1 with advisory. | ✓ |
| Always offer all 3 destinations, user picks | Flexible but slower per promotion. | |
| Decision tree + manual override | Tree picks default, override available. | |

**User's choice:** Decision tree

### Q2: Decline tracking location

| Option | Description | Selected |
|--------|-------------|----------|
| `corrections/_promotion_offers.json` | System-internal file with per-rule `last_offered_at`, `decision`, `criteria_at_offer`. | ✓ |
| Inline flag on rules_summary.json entries | Simpler but pollutes runtime file. | |

**User's choice:** `corrections/_promotion_offers.json`

### Q3: Re-surface trigger for `not_yet`

| Option | Description | Selected |
|--------|-------------|----------|
| `occurrence_count` grew by ≥1 since decline | Rule continued earning its keep. | ✓ |
| 30 days passed since the decline | Time-based; risks re-offering stale rules. | |
| Either of above | Most permissive; risks fatigue. | |

**User's choice:** occurrence_count grew

---

## Claude's Discretion

- Empty-session lifecycle: backups skipped on no-write sessions (FEEDBACK-03 says "before first write"); pruning and promotion still run.
- Tier 2→3 advisory output format (FEEDBACK-10): end-of-session console block; persist to `corrections/_tier3_advisory.md` only when at least one candidate exists.
- Conflict-detection scope per item: reuse Phase 3 D-17/D-18/D-19 logic per Tier 1 destination.
- Session order: backup-on-first-write → conflict scan → submission → write → rules_summary rebuild → pruning → promotion → Tier 2→3 advisory.
- Bilingual example sourcing: agent generates EN+FR when not supplied; user verifies in self-check.
- Backup of `variables_guide.md` covered by same first-write convention.

## Deferred Ideas

- BO extractor (Phase 14) auto-sync of `Variables.csv` from BO — closes the catalog drift gap.
- Restructuring `label_patterns.json` / `tone_guidelines.json` sections if promoted rules don't fit existing schema — defer until first concrete promotion happens.
- `/document-variable` standalone skill as alternative path to populate `variables_guide.md` outside promotion flow.
- Phase 15 scope reduction — `PARALLEL-06` moves to Phase 13, leaving Phase 15 as URL detection + parallel reviews only.
