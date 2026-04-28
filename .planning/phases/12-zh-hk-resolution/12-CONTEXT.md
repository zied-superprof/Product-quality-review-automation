# Phase 12: zh-HK Language Code Resolution - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning
**Gap closure:** Closes IC-02 from `.planning/v1.2-MILESTONE-AUDIT.md` — the Hong Kong correction learning loop is broken because the `zh-HK` rule added in Phase 9 Plan 02 is orphaned: `structural_validator.py:684` maps `Hong-Kong → zh-TW`, and no other config (`languages.json`, `tone_guidelines.json`, `label_patterns.json`, `review_rules_compact.md`) carries a `zh-HK` entry. The lookup never matches.

<domain>
## Phase Boundary

Resolve the orphaned `zh-HK` rule by **merging** it into the existing `zh-TW` rule set. After this phase:

1. The two `zh-HK` correction entries are removed from `corrections/corrections_log.json` and `corrections/rules_summary.json`.
2. `Hong-Kong → zh-TW` in `scripts/structural_validator.py:684` remains unchanged (already correct under the merge direction).
3. A live or static check confirms `zh-HK` no longer appears anywhere in active config or corrections data.
4. The merge decision is recorded in the Phase 12 summary so future readers understand why HK is folded under zh-TW.

**Out of scope:**
- Splitting HK into its own end-to-end code path (rejected — every other config already treats HK as zh-TW; sample CSVs show identical Traditional Chinese content; the orphan was an unintended Phase-9 side-effect, not a deliberate split).
- Broader language-database review (deferred — see Deferred Ideas).
- Backwards-edit of historical artifacts in `.planning/phases/09-fixes/` or `corrections/backups/` (preserved as audit trail).

</domain>

<decisions>
## Implementation Decisions

### Direction
- **D-01:** **Merge into zh-TW.** Delete the orphaned `zh-HK` rule rather than building it out across all four configs + the validator map. Rationale: Hong-Kong CSV columns already carry Traditional Chinese content effectively identical to Taïwan's; `languages.json` already lists `["TW", "HK"]` as countries under the `zh-TW` entry; tone, label, and review-rules configs are all keyed to `zh-TW` only. The Phase-9 normalization (zh_TW → zh-TW) accidentally created a separate `zh-HK` learning entry; merging restores consistency with the rest of the system.

### Cleanup scope
- **D-02:** **Delete only.** Remove the two `zh-HK` records from `corrections/corrections_log.json` (the entry beginning at line 43) and `corrections/rules_summary.json` (the entry beginning at line 41). Do NOT add Python comments or metadata notes elsewhere. The user is planning a broader review of the language database, rules, and variables in a later phase; this phase keeps the diff small and focused on closing IC-02.
- **D-03:** Do NOT modify `structural_validator.py:684` — `'Hong-Kong': 'zh-TW'` is the correct mapping under the merge direction and is already in place. No code comment is added at this site.
- **D-04:** Do NOT modify `config/languages.json`, `config/tone_guidelines.json`, `config/label_patterns.json`, or `config/review_rules_compact.md`. None of these contain `zh-HK` today; under the merge direction, they should not.
- **D-05:** Backup-before-write rule (FIX-05 from Phase 9) still applies — before either corrections file is rewritten, a timestamped backup must be produced per the existing skill convention.

### Verification
- **D-06:** **Static grep verification is the floor.** After the deletes, `grep -r "zh-HK\|zh_HK" config/ corrections/ scripts/ .claude/commands/` must return zero hits outside archived/historical files (`.planning/phases/`, `corrections/backups/`, `scripts/archive/`). Live run on a real Hong-Kong-bearing CSV (e.g. `samples/Relance-1.csv`) is **optional** — the planner may include it as an additional verification step but it is not blocking.

### Recording the decision
- **D-07:** Phase 12's `12-01-SUMMARY.md` (or equivalent) must record that the merge direction was chosen and why (Roadmap success criterion #3). Brief — one paragraph citing IC-02, the two CSV evidence points, and the deferred broader review.

### Claude's Discretion (delegated to planner/executor)
- Exact Python/jq/sed mechanism for the JSON deletes — whatever keeps the surrounding structure intact and writes valid JSON.
- Whether to package the two file edits into one plan or two — likely one plan, but planner decides.
- Whether to spot-check `samples/Relance-1.csv` for the post-merge end-to-end behavior or rely on grep alone.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and scope
- `.planning/ROADMAP.md` §"Phase 12: zh-HK Language Code Resolution" — 3 success criteria the implementation must satisfy
- `.planning/v1.2-MILESTONE-AUDIT.md` §IC-02 (lines 137-147) — orphan description, downstream consumers, root cause
- `.planning/v1.2-MILESTONE-AUDIT.md` §"End-to-End Flows" line 163 — broken-flow record this phase closes
- `.planning/v1.2-MILESTONE-AUDIT.md` §"Resolution Paths" lines 197-211 — three options; this phase picks 12-A (merge variant)
- `.planning/REQUIREMENTS.md` — gap-closure phase, no new REQ; ties back to FIX-06 / AUD-05 traceability

### Files to modify
- `corrections/corrections_log.json` — delete the `zh-HK` record (currently lines 43-52, the relance-1 / @TPL_MATIERE_DE_MATIERE@ rule)
- `corrections/rules_summary.json` — delete the `zh-HK` record (currently lines 41-49, same rule mirrored)

### Files NOT to modify (under merge direction)
- `scripts/structural_validator.py:684` — `'Hong-Kong': 'zh-TW'` is already correct
- `config/languages.json` — already lists `["TW", "HK"]` under zh-TW
- `config/tone_guidelines.json`, `config/label_patterns.json`, `config/review_rules_compact.md` — none contain `zh-HK` today; merge direction means none should
- `.claude/commands/review-translations.md` — skill orchestration unaffected by the merge
- `.planning/phases/09-fixes/` and `corrections/backups/` — frozen historical artifacts; preserve as audit trail

### Reference material (read for context, do not modify)
- `samples/Relance-1.csv` — real CSV with `Hong-Kong` and `Taïwan` columns; the Traditional Chinese content used to confirm merge is appropriate
- `.planning/PROJECT.md` §"Validated in Phase 9" — HND-* and QUA-* requirements that produced the zh-TW normalization which left zh-HK orphaned
- `CLAUDE.md` §"Subject variable rules" — confirms `@TPL_MATIERE_DE_MATIERE@` rules that the zh-TW (and folded HK) rule covers

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- The corrections JSON files are simple list-of-objects under a top-level `corrections` / `rules` key — straightforward delete via standard JSON load → filter → write. No new helper needed.
- `structural_validator.py:660-690` (the `country_to_code` dict) is the single source of truth for CSV-column → language-code mapping; `Hong-Kong` already routes to `zh-TW`, so no validator code change is needed under the merge direction.
- Phase 9's backup-before-write convention (FIX-05) is already part of the skill — the merge edit must follow it (snapshot the two files before modifying).

### Established Patterns
- Corrections are added/edited as discrete records keyed by `language` + `notification_type` + `issue_category`. Removing a record is symmetric to adding one — no schema change.
- Audit-trail discipline: never rewrite `corrections/backups/*.json` or planning-history files. Strike-through / append, never overwrite, when a decision supersedes a prior one in live planning docs.

### Integration Points
- After the two deletes, the next `/review-translations` run on a Hong-Kong-bearing CSV will continue to look up `zh-TW` rules (unchanged) and the `zh-HK` lookup that was previously orphaned simply ceases to exist. No skill-level wiring changes.
- The same files were touched in Phase 9 Plan 02 — that phase's plan is the closest precedent for editing the corrections store with a backup step.

</code_context>

<specifics>
## Specific Ideas

- The user's framing: "we can remove this rule, eventually we have to review the whole language database, the rules and the variables." Phase 12 does the narrow merge now; the broader review is intentionally a separate, future phase.
- Sample evidence used to justify merge: `samples/Relance-1.csv` contains both `Taïwan` and `Hong-Kong` columns. The HK content uses Traditional Chinese with the same template variables as TW — no formal/informal divergence visible at the CSV layer, no Cantonese-specific morphology in the existing translations.

</specifics>

<deferred>
## Deferred Ideas

- **Broader language-database review.** Full audit of `config/languages.json`, `config/tone_guidelines.json`, `config/label_patterns.json`, `config/review_rules_compact.md`, `corrections/rules_summary.json`, and `config/Variables.csv` for stale, redundant, or inconsistent entries. The orphaned `zh-HK` is the symptom that surfaced; the user wants a sweep across the whole rule + variable surface in a future phase. Out of scope for Phase 12 — captured here so it's not lost.
- **Hardening the merge with a code-level guard.** A unit-style assertion or pre-commit check that fails if a language code appears in `corrections/*.json` without a matching entry in at least one config (`languages.json` / `tone_guidelines.json` / `label_patterns.json`). Would have caught IC-02 mechanically. Future milestone.
- **Live-run verification as the default.** A Phase-12 follow-up could establish a one-line smoke test (run skill on `samples/Relance-1.csv` and grep the report for `zh-HK`) so future merge/split decisions are validated end-to-end automatically. Not mandatory for this phase.

</deferred>

---

*Phase: 12-zh-hk-resolution*
*Context gathered: 2026-04-28*
