# Phase 11: Loop-Variable Structural Check - Context

**Gathered:** 2026-04-24
**Status:** Ready for planning
**Gap closure:** Closes IC-01 from v1.2-MILESTONE-AUDIT.md — completes the partially-satisfied FIX-06 scope (AUDIT finding [#8] wrong-loop-variable check was skipped silently in Phase 9).

<domain>
## Phase Boundary

Teach `scripts/structural_validator.py` to flag when a template variable appears in a different structural block than the French reference places it. The two known error patterns from CLAUDE.md (both observed in Arabic markets) must be caught by the deterministic layer instead of relying on the AI reviewer:

1. `@TPL_MATIERE_DE_MATIERE@` placed inside `<TPL_LOOP_ANNONCES>` when it should be `@TPL_ANNONCE_AFFICHE_QUI_CONNECTE@`
2. `@TPL_ANNONCE_AFFICHE_QUI_CONNECTE@` placed inside `<TPL_IF_LISTE_AVIS>` when it should be `@TPL_LISTE_AVIS@`

**Block semantics (confirmed 2026-04-24):**
- `<TPL_LOOP_ANNONCES>...</TPL_LOOP_ANNONCES>` — ad-group block: renders the group of ads that appear in the notification (NOT "once per ad").
- `<TPL_IF_LISTE_AVIS>...</TPL_IF_LISTE_AVIS>` — conditional block: renders only when the ad listing being shown in the notification has reviews.

Out of scope: rewriting existing checks, adding new checks beyond block placement, changing the report template or the skill orchestration (except the optional fail-fast stretch, see D-06).

</domain>

<decisions>
## Implementation Decisions

### Rule model
- **D-01:** **Hybrid**: French reference is the primary source of truth for block-context. For each `@TPL_*@` variable that appears in the French cell, its block-context (innermost enclosing `<TPL_LOOP_*>` / `<TPL_IF_*>` / `<TPL_ELSE_*>` or `body`) is recorded; the translation must match. No global per-variable block-scope list is authored in config — this avoids false positives when future notifications legitimately use a variable in a new block.
- **D-02:** **Optional per-language overrides** live in `label_patterns.json` under a new top-level key `block_scope_overrides` so grammatical exemptions can be declared without touching code. Empty at launch. Minimal schema the planner can refine:
  ```
  "block_scope_overrides": {
    "<lang_code>": {
      "<TPL_VAR>": { "allowed_blocks": ["body", "TPL_LOOP_ANNONCES"] }
    }
  }
  ```
  When a variable occurrence in the translation is inside a block listed in the override's `allowed_blocks` for that language, it is NOT flagged even if the French reference used a different block.

### Coverage
- **D-03:** Coverage is derived automatically from whatever variables the French reference uses in a given notification. No hand-authored list of variables to track. Every `@TPL_*@` that appears in French is in scope; those that do not appear in French fall back to the existing `variable_extra` check.

### Block definition
- **D-04:** Tags that count as a block boundary:
  - `<TPL_LOOP_*>...</TPL_LOOP_*>`
  - `<TPL_IF_*>...</TPL_IF_*>`
  - `<TPL_ELSE_*>...</TPL_ELSE_*>`
  - The implicit "body" context (anything not inside one of the above).
  Custom markup (`[LIEN]`, `[BOUTON]`, `[TITRE]`, etc.) does NOT count as a block boundary — those are presentation markers, not semantic scope.
- **D-05:** Block-context is the **innermost** enclosing block. Nested blocks are handled by a stack-based scan (implementation detail for planner).

### Severity and reporting
- **D-06:** Severity: **error**. Check name: `variable_block_mismatch` (single check, one message shape, regardless of whether the mismatched block is a loop, if, or else).
- **D-07:** Issue dict must include `variable`, and `detail` with `ref_block` and `trans_block` so the report can say "expected inside `<TPL_LOOP_ANNONCES>`, found inside `<TPL_IF_LISTE_AVIS>`".
- **D-08:** **Stretch goal (planner decides Phase 11 scope):** the review skill surfaces `variable_block_mismatch` errors before the full AI review fires, so these deterministic breaks are visible early rather than buried in the post-AI report. If deferred, capture as a follow-up.

### Comparison semantics
- **D-09:** When a variable appears multiple times in French (e.g. once in body, once in loop), compare the **multiset of block-contexts per variable** between French and translation. A translator who legitimately uses `@TPL_X@` in two places must place both correctly; a translator who reorders paragraphs within the same block is NOT flagged.
- **D-10:** When a variable appears in the translation but not in the French reference at all, the existing `variable_extra` check handles it — Phase 11's new check does not duplicate that. It only fires when a variable exists in both sides and its block-context differs.

### Claude's Discretion (delegated to planner/researcher)
- Exact Python mechanism for the scan (regex + stack, state machine, or other stdlib-only approach)
- Whether to refactor common parsing helpers or build the scan inline in a new `check_variable_block_placement()` function
- Message wording exactness — as long as it satisfies D-07
- Placement of the new check within `validate_entry()` ordering

</decisions>

<specifics>
## Specific Ideas

- The existing `check_subject_variable_variant()` function (line 751 of `structural_validator.py`) is the closest precedent in shape: deterministic, loads rules from `label_patterns.json`, emits `error`-severity findings with `variable` and `detail` fields. The new check should follow the same scaffolding.
- `label_patterns.json` already has `template_syntax.conditional_if` and `template_syntax.custom_markup` sections describing the tag grammar — the block-scope parser can reuse those patterns rather than redefining them.
- The two Arabic-market examples from CLAUDE.md are the golden test fixtures — whatever the planner designs must catch both of them exactly.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and scope
- `.planning/REQUIREMENTS.md` — FIX-06 (reset to pending on 2026-04-23, reassigned to Phase 11)
- `.planning/ROADMAP.md` §Phase 11 — 3 success criteria the implementation must satisfy
- `.planning/v1.2-MILESTONE-AUDIT.md` §IC-01 — material gap description and expected solution shape

### Codebase to modify
- `scripts/structural_validator.py` — add new `check_variable_block_placement()` (or similarly named) function and wire into `validate_entry()` at line 874. Model after `check_subject_variable_variant()` at line 751.
- `config/label_patterns.json` — add new top-level `block_scope_overrides` key (empty object at launch, schema in D-02 above). Planner may also declare the canonical block-tag families here if that keeps the validator code simpler.

### Reference material (do not modify — read for context)
- `CLAUDE.md` §"Recurring errors to watch for" — source of the two golden-example error patterns
- `.claude/commands/review-translations.md` — skill definition; relevant only if the D-08 stretch (fail-fast surfacing) is taken in scope
- `.planning/phases/09-fixes/` — prior phase that touched `structural_validator.py` and `label_patterns.json`; shows Phase 9 baseline

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `check_subject_variable_variant()` (structural_validator.py:751) — closest pattern match: deterministic check, loads from `label_patterns.json`, emits error-severity findings with `variable` + `detail`.
- `load_subject_variable_rules()` (structural_validator.py:189) — config-load pattern to model after for loading `block_scope_overrides`.
- `RE_IF_OPEN` / `RE_IF_CLOSE` / `RE_ELSE_OPEN` / `RE_ELSE_CLOSE` / `RE_VALUE_VAR` (structural_validator.py:30-46) — existing regex patterns the new scan can reuse. Only `<TPL_LOOP_*>` tags need a new regex.
- `validate_entry()` (structural_validator.py:874) — single call site for wiring the new check; accepts optional config dict parameters already.
- `get_language_code()` (structural_validator.py:720) — returns normalized lang code or None; used to look up overrides in D-02.

### Established Patterns
- Every check function returns `list[dict]` with fields `check`, `severity`, `category`, `message`, optional `variable`, optional `detail`. Tagged with `country` in `validate_entry()`. New check must follow this shape.
- Config loads are "soft-fail" (return None if file missing, validator continues) — override loader should follow this convention.
- Ambiguous language codes (`get_language_code()` returns `None`) skip language-specific logic. Overrides would therefore only apply to unambiguous markets — this is a known and acceptable limitation matching existing behavior.

### Integration Points
- New check runs AFTER the existing variable-presence checks (`check_variables`) so that "variable missing" and "variable extra" are already handled; placement check only fires on variables present in both sides.
- Report generation downstream in `.claude/commands/review-translations.md` groups findings by `check` name — using a single `variable_block_mismatch` keeps grouping clean.
- `label_patterns.json` is loaded once per run by `load_subject_variable_rules()` style helpers — the same-style loader for `block_scope_overrides` should not add a second file read.

</code_context>

<deferred>
## Deferred Ideas

- Broader global block-scope rule authoring (per-variable `allowed_blocks` in config across the board) — not needed now; French-reference parity covers the cases that matter. Reopen if a class of notifications emerges where French itself is inconsistent.
- Extending block detection to custom markup (`[LIEN]`, `[BOUTON]`) — out of scope; not a semantic boundary.
- Populating `block_scope_overrides` with known grammatical exemptions — launch empty; fill in as real cases appear in reviewer feedback.
- Retroactive re-scoring of past reports to find notifications where this bug was missed by the AI reviewer — useful but a separate one-shot task, not Phase 11.
- Promoting the D-08 fail-fast behavior to a hard early-exit (abort the whole run on any `variable_block_mismatch`) — too aggressive for first rollout; reviewer should see all findings together.

</deferred>

---

*Phase: 11-loop-variable-check*
*Context gathered: 2026-04-24*
