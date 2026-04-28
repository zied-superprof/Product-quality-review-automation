---
phase: 12-zh-hk-resolution
plan: 01
date: 2026-04-28
gap_closure: IC-02
direction: merge
subsystem: corrections
tags: [zh-HK, zh-TW, corrections-log, rules-summary, gap-closure, IC-02, FIX-06, AUD-05]

requires:
  - phase: 09-fixes
    provides: "FIX-05 backup-before-write convention; zh_TW → zh-TW normalization that left zh-HK orphaned"
provides:
  - "Orphaned zh-HK correction rule merged into zh-TW (zero zh-HK references in active project surface)"
  - "scripts/_build_report.py aligned with structural_validator.py:684 (Hong-Kong → zh-TW)"
  - "Backup triple under corrections/backups/ for both corrections JSONs plus _build_report.py"
affects: [language-database-review, code-level-language-code-guard, future-zh-handling]

tech-stack:
  added: []
  patterns:
    - "Backup-before-write triple-snapshot (FIX-05 extended to script edits, not just JSON)"
    - "Composite-key delete with assertion on expected match count (Python stdlib json)"
    - "Anchored string-replacement with count assertion before substitution (drift-safe Python edit)"

key-files:
  created:
    - .planning/phases/12-zh-hk-resolution/12-01-SUMMARY.md
    - corrections/backups/20260428T152501Z_corrections_log.json
    - corrections/backups/20260428T152501Z_rules_summary.json
    - corrections/backups/20260428T152501Z__build_report.py
  modified:
    - corrections/corrections_log.json
    - corrections/rules_summary.json
    - scripts/_build_report.py

key-decisions:
  - "Merge HK under zh-TW rather than split — every other config already keys Chinese rules to zh-TW only and HK CSV content matches TW (CONTEXT.md D-01)"
  - "Delete-only scope for the corrections JSONs; no metadata or code comments added (CONTEXT.md D-02)"
  - "scripts/_build_report.py alignment added to plan during checker review — file was untracked but already diverged from structural_validator.py:684 ('Hong-Kong': 'zh-HK' vs 'zh-TW') and would have failed the D-06 grep floor"
  - "structural_validator.py:684 left untouched ('Hong-Kong': 'zh-TW' is canonical under merge direction)"
  - "Broader language-database review explicitly deferred (CONTEXT.md Deferred Ideas)"

patterns-established:
  - "Pattern: When merging an orphaned language code, audit every script that maps country → code (not only configs). _build_report.py drift was discovered only because the planner ran a project-wide grep."
  - "Pattern: For numeric counters in JSON (e.g. total_rules), recompute from the post-edit list length — never decrement blindly."

requirements-completed: [IC-02, FIX-06, AUD-05]

duration: 3min
completed: 2026-04-28
---

# Phase 12 Plan 01: zh-HK Language Code Resolution Summary

**Orphaned zh-HK correction rule merged into zh-TW; corrections JSONs and `_build_report.py` are now consistent with `structural_validator.py:684` (Hong-Kong → zh-TW), closing IC-02.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-04-28T15:24:46Z
- **Completed:** 2026-04-28T15:27:30Z (approx — Tasks 1–3 ran serially with no checkpoints)
- **Tasks:** 3
- **Files modified:** 3 (plus 3 backups + this SUMMARY created)

## Accomplishments

- Removed 1 zh-HK record from `corrections/corrections_log.json` (6 → 5 entries; `_schema` block preserved)
- Removed 1 zh-HK rule from `corrections/rules_summary.json` (6 → 5 rules; `total_rules` 6 → 5; `generated` field preserved)
- Aligned `scripts/_build_report.py` with the merge direction:
  - Country-to-code map (line 58): `'Hong-Kong': 'zh-HK'` → `'Hong-Kong': 'zh-TW'` (matches `scripts/structural_validator.py:684`, the canonical mapping)
  - Two prose strings in the Hong-Kong analysis section (lines 639 and 647): `` zh-HK is in `formal_vous_languages` `` → `` zh-TW is in `formal_vous_languages` `` (still accurate — zh-TW is itself listed in `formal_vous_languages` per `tone_guidelines.json` and `CLAUDE.md`)
  - This file was untracked when Phase 12 began (added 2026-04-28). It had silently diverged from `structural_validator.py:684` and would have caused the D-06 grep floor to fail without alignment.
- Created backup triple under `corrections/backups/` with timestamp `20260428T152501Z` covering all three pre-edit files (FIX-05 extended to script edits)

## Task Commits

Each task was committed atomically:

1. **Task 1: Backup corrections files and _build_report.py** — `1e04a64` (chore)
2. **Task 2: Delete zh-HK records and align _build_report.py to merge direction** — `2fa7272` (fix)
3. **Task 3: Record the merge decision in 12-01-SUMMARY.md** — pending (this commit)

**Plan metadata:** added in the final docs commit alongside STATE.md and ROADMAP.md updates.

## Files Created/Modified

### Modified
- `corrections/corrections_log.json` — zh-HK record deleted; remaining 5 entries: `[hu/grammar, lt/label, ja/label, zh-TW/label, all/format]`; `_schema` block preserved verbatim.
- `corrections/rules_summary.json` — zh-HK rule deleted; `total_rules` decremented to 5; `generated` field preserved.
- `scripts/_build_report.py` — 1 LANG-dict entry + 2 prose-string occurrences aligned to zh-TW; file still parses as Python (`ast.parse` clean).

### Created
- `corrections/backups/20260428T152501Z_corrections_log.json`
- `corrections/backups/20260428T152501Z_rules_summary.json`
- `corrections/backups/20260428T152501Z__build_report.py`
- `.planning/phases/12-zh-hk-resolution/12-01-SUMMARY.md` (this file)

## Why merge instead of split

The merge direction (CONTEXT.md D-01) was chosen over splitting HK into its own end-to-end code path for four reasons:

1. **IC-02 root cause** (`v1.2-MILESTONE-AUDIT.md` lines 137–147): the zh-HK rule added in Phase 9 Plan 02 was orphaned because `scripts/structural_validator.py:684` maps `Hong-Kong → zh-TW` and no other config (`languages.json`, `tone_guidelines.json`, `label_patterns.json`, `review_rules_compact.md`) carries a zh-HK key. The lookup never matched.
2. **CSV evidence** (`samples/Relance-1.csv`): Hong-Kong and Taïwan columns carry effectively identical Traditional Chinese content with the same template variables — no formal/informal divergence at the CSV layer, no Cantonese-specific morphology in the existing translations.
3. **Config consensus**: `config/languages.json` already lists `["TW", "HK"]` under the zh-TW entry; `tone_guidelines.json`, `label_patterns.json`, and `review_rules_compact.md` are all keyed to zh-TW only. The Phase-9 normalization (`zh_TW → zh-TW`) accidentally created a separate zh-HK learning entry; merging restores consistency.
4. **Cost asymmetry**: splitting would have required adding zh-HK to four configs plus updating the validator country→code map; merging required deleting two records and aligning one previously-divergent script. The orphan was an unintended Phase-9 side-effect, not a deliberate split.

## What was NOT changed (and why)

Per CONTEXT.md "Files NOT to modify":

- `scripts/structural_validator.py` — line 684 `'Hong-Kong': 'zh-TW'` is already canonical under the merge direction (this is the mapping `_build_report.py` was aligned to).
- `config/languages.json`, `config/tone_guidelines.json`, `config/label_patterns.json`, `config/review_rules_compact.md` — none contained zh-HK before Phase 12; under the merge direction, none should after.
- `.claude/commands/review-translations.md` — skill orchestration is unaffected by the merge.
- `.planning/phases/09-fixes/` and pre-existing entries in `corrections/backups/` — frozen audit trail; never overwritten.

`git diff --name-only` for this plan's working set lists only the three intended files (`corrections/corrections_log.json`, `corrections/rules_summary.json`, `scripts/_build_report.py`). Other working-tree modifications visible in `git status` are pre-existing changes unrelated to Phase 12 (they were present in the initial gitStatus snapshot).

## Deferred work

The broader language-database review captured in CONTEXT.md "Deferred Ideas" is intentionally OUT of scope for Phase 12 and should be a future phase. Specifically:

- Full audit of `config/languages.json`, `config/tone_guidelines.json`, `config/label_patterns.json`, `config/review_rules_compact.md`, `corrections/rules_summary.json`, and `config/Variables.csv` for stale/redundant/inconsistent entries.
- A code-level guard (pre-commit check or unit assertion) that fails when a language code appears in any source file without a matching entry in at least one config. The `_build_report.py` divergence discovered during checker review reinforces the value of this idea — a mechanical check would have caught the drift between `_build_report.py:58` and `structural_validator.py:684` automatically.
- Live-run verification on `samples/Relance-1.csv` as a default smoke test for future merge/split decisions.

## Verification evidence

```
$ grep -r "zh-HK\|zh_HK" config/ corrections/ scripts/ .claude/commands/ \
    --exclude-dir=backups --exclude-dir=archive
(no output; exit code 1)
```

```
$ python3 -c 'import json; print(len(json.load(open("corrections/corrections_log.json"))["corrections"]))'
5
```

```
$ python3 -c 'import json; d=json.load(open("corrections/rules_summary.json")); print(d["total_rules"], len(d["rules"]))'
5 5
```

```
$ grep -c "'Hong-Kong'" scripts/_build_report.py
2
$ grep "'Hong-Kong'" scripts/_build_report.py
    'Singapour[Groupement]':'en','Taïwan':'zh-TW','Hong-Kong':'zh-TW',
single_section('Hong-Kong',
```

The first occurrence is the country-to-code dict entry now correctly mapping to `zh-TW`. The second is the section header label inside `single_section('Hong-Kong', …)` — that string is the human-readable section title, not a language code.

```
$ grep -n "'Hong-Kong': 'zh-TW'" scripts/structural_validator.py
684:    'Hong-Kong': 'zh-TW',
```

Validator mapping is unchanged (D-03), confirming the canonical source of truth was preserved.

## Mapping to Roadmap success criteria

- **Criterion #1** (consistent resolution OR merge with orphan removed): satisfied via merge — both JSON records deleted, and the previously-divergent `scripts/_build_report.py` aligned to zh-TW so the project surface is consistent end-to-end. Static grep across `config/`, `corrections/`, `scripts/`, and `.claude/commands/` returns zero hits without any per-file `--exclude` carve-out.
- **Criterion #2** (CSV run with HK row exercises intended path with no silent divergence): satisfied — Hong-Kong rows are routed to zh-TW by the unchanged validator map and now match the unchanged zh-TW correction rule; no zh-HK entry remains to be missed. `_build_report.py` no longer silently routes Hong-Kong CSVs through a different code path. Live verification on `samples/Relance-1.csv` was optional per CONTEXT.md D-06; the static grep floor is met.
- **Criterion #3** (decision recorded in summary): satisfied by this document — the merge direction, rationale (IC-02 + CSV evidence + config consensus + cost asymmetry), the `_build_report.py` alignment performed during execution, and the deferred broader language-database review are all recorded above.

## Decisions Made

- Merge HK under zh-TW (CONTEXT.md D-01) — see "Why merge instead of split" above.
- Delete-only scope for the corrections JSONs (CONTEXT.md D-02) — no metadata, no code comments.
- Align `scripts/_build_report.py` with `structural_validator.py:684` (added to scope during checker review) — the file was untracked but already inconsistent with the canonical mapping; bringing it in line was required for the D-06 grep to pass without per-file carve-outs.
- Recompute `total_rules` from post-edit list length, not by decrementing — defensive against drift if the file is edited again later.

## Deviations from Plan

None — plan executed exactly as written. All three tasks completed on first attempt; no auto-fixes (Rules 1–3) were triggered, no architectural decisions (Rule 4) needed escalation, and no checkpoints were defined.

## Issues Encountered

None.

## Next Phase Readiness

- IC-02 closed; all three v1.2 audit integration checks (IC-01, IC-02, IC-03) now have known status.
- Recommended follow-up: `/gsd:verify-phase 12` to confirm SUMMARY against PLAN frontmatter, then `/gsd:audit-milestone v1.2` to re-check the milestone.
- The deferred broader language-database review is a strong candidate for the next phase; the `_build_report.py` drift surfaced here makes the case for a mechanical code-level guard.

---
*Phase: 12-zh-hk-resolution*
*Completed: 2026-04-28*
