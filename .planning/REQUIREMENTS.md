# Requirements: v1.3 — End-to-End Review Automation

**Defined:** 2026-04-29
**Core Value:** Every review run must produce a reliable, actionable report — fast enough and cheap enough to run on every translation batch.

## v1.3 Requirements

Three independent threads. Each requirement is user-centric, atomic, and testable.

### INGEST — Playwright BO extraction

- [ ] **INGEST-01**: User can paste a Superprof BO notification admin URL and the extractor produces 1–2 named CSVs in `samples/` (email tab → `_email.csv`, SMS tab → `_sms.csv`)
- [ ] **INGEST-02**: CSV filenames are derived from the page information block on the BO page (no manual naming)
- [ ] **INGEST-03**: Existing CSV-drop flow (`/review-translations samples/foo.csv`) continues to work identically at every phase
- [ ] **INGEST-04**: User authenticates the BO once via a headed setup script (`scripts/_setup_bo_auth.py`); subsequent extractions use the persisted Playwright `storage_state` headless
- [ ] **INGEST-05**: When the BO page has neither email nor SMS data, the extractor hard-fails with `"No translation grid found at this URL — verify the page has at least an Email or SMS tab."` and writes no CSV
- [ ] **INGEST-06**: When the saved BO session has expired, the extractor exits with `BOAuthExpiredError: rerun scripts/_setup_bo_auth.py to re-login` (detected via post-navigation URL/title check)
- [ ] **INGEST-07**: BO session credentials never enter git — `.playwright/auth/` is gitignored as the first commit of the BO extraction phase, before any auth code is written

### PARALLEL — Skill update for parallel reviews

- [ ] **PARALLEL-01**: `/review-translations` Step 0 detects whether the argument is a URL or a file path; URL mode invokes the extractor and receives a list of CSV paths
- [ ] **PARALLEL-02**: When the extractor returns 2 CSVs, the skill runs Steps 1–6 concurrently for both channels
- [ ] **PARALLEL-03**: Each channel runs as an independent transaction — one channel's failure does not abort the other
- [ ] **PARALLEL-04**: The final summary block shows per-channel status with a retry hint (CSV path for direct rerun via the existing CSV-drop flow)
- [ ] **PARALLEL-05**: Errors are classified by stage — BO/Playwright (extraction), Validator (Step 2), AI review (Step 4c), Notion publish (Step 6), and a catch-all "Other" — with the category visible in the summary
- [ ] **PARALLEL-06**: Step 7 (and 7a/7b/7c/7d/7e variants, lines 470–814 of the v1.2 skill) is removed entirely from `review-translations.md`; Step 6 ends by pointing the user at `/submit-feedback`
- [ ] **PARALLEL-07**: A single-CSV invocation produces output identical to v1.2 behavior (the parallel branch is skipped)

### FEEDBACK — Standalone /submit-feedback skill

- [ ] **FEEDBACK-01**: User invokes `/submit-feedback` (with or without a report path argument) to open a feedback session independently of any review session
- [ ] **FEEDBACK-02**: When the user references a report, every correction in the session is tagged with the real `notification_type` extracted from the report; when no report is referenced, fallback is `"adhoc"` (replaces the misleading `"batch-feedback"` label)
- [ ] **FEEDBACK-03**: All four writable files (`corrections_log.json`, `rules_summary.json`, `label_patterns.json`, `tone_guidelines.json`) are backed up before the session's first write, to `corrections/backups/YYYYMMDDTHHMMSSZ_<filename>`
- [ ] **FEEDBACK-04**: When multiple feedback items conflict with existing rules, all conflicts surface in one consolidated numbered list with a per-item `replace / append / dismiss` menu; the user resolves all conflicts in one answer line
- [ ] **FEEDBACK-05**: Selecting `append` on a conflict triggers a focused sub-dialogue (contradictory? different contexts? boundary?) that produces a draft merged rule; both an agent self-check and a user clarity check must approve before the write happens; the original two rules are archived (not deleted) to `corrections/archive/`; merged-rule confidence auto-downgrades by one tier
- [ ] **FEEDBACK-06**: At the end of every session, after writes, the skill scans `rules_summary.json` for pruning candidates — surfacing any rule that matches at least one of: `last_seen` more than 30 days ago, `occurrence_count == 1`, `confidence == low`, or superseded by a newer rule for the same `language` + `issue_category`
- [ ] **FEEDBACK-07**: Pruning candidates are reviewed one at a time with a `keep / archive / edit text / show full record` menu; nothing auto-archives; archived rules go to `corrections/archive/rules_archive.json` (recoverable)
- [ ] **FEEDBACK-08**: After pruning, the skill scans for promotion candidates (Tier 1 → Tier 2) — rules where `occurrence_count >= 3` AND `confidence == high` AND no contradicting feedback in the last 30 days
- [ ] **FEEDBACK-09**: User reviews each promotion candidate with `promote / not yet / never (lock at Tier 1) / show full record`; on promote, the skill drafts the config update (target file determined by the routing tree), the user approves text, and the write happens with the target file backed up first
- [ ] **FEEDBACK-10**: For mechanically-checkable rules with false-negative history, the skill flags them as Tier 2 → Tier 3 promotion candidates in advisory output only; the skill never edits `scripts/structural_validator.py` (Tier 2→3 is human-coded)

## Future Requirements (v1.4+)

Acknowledged but deferred:

### Output integrations (handled separately by user, not via GSD)

- **NOTION-01**: Notion "task follow up" column populated on every report publish
- **SLACK-01**: Completion notifier posted to a Slack group channel
- **SLACK-02**: Slack message contains Notion page URL and run summary

### Beyond v1.3

- **DELTA-01**: Diff/delta detection — review only what changed since last run
- **MULTIURL-01**: Multi-URL batch extraction (more than one BO URL per invocation)
- **BOWRITE-01**: BO write-back — push confirmed corrections back into the BO
- **TIER3-AUTO**: Skill auto-drafting validator code for Tier 2→3 promotions

## Out of Scope

| Feature | Reason |
|---------|--------|
| Notion "task follow up" column write | Notifications handled separately by the user; v1.3 stays focused on input automation + feedback refactor |
| Slack notifier | Same as above |
| Skill editing `scripts/structural_validator.py` | Tier 2→3 promotion is a human architectural decision (Phase-11 pattern). Skill stays advisory. |
| Multi-URL batch mode | One URL per invocation; explicit boundary to keep error handling simple |
| Auto-archiving prune/promotion candidates | Low tolerance for losing useful rules — every change is user-reviewed |
| Test infrastructure / unit tests | Existing project constraint (PROJECT.md: "Test suite — out of scope") |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGEST-01 | Phase 14 | Pending |
| INGEST-02 | Phase 14 | Pending |
| INGEST-03 | Phase 14 | Pending |
| INGEST-04 | Phase 14 | Pending |
| INGEST-05 | Phase 14 | Pending |
| INGEST-06 | Phase 14 | Pending |
| INGEST-07 | Phase 14 | Pending |
| PARALLEL-01 | Phase 15 | Pending |
| PARALLEL-02 | Phase 15 | Pending |
| PARALLEL-03 | Phase 15 | Pending |
| PARALLEL-04 | Phase 15 | Pending |
| PARALLEL-05 | Phase 15 | Pending |
| PARALLEL-06 | Phase 15 | Pending |
| PARALLEL-07 | Phase 15 | Pending |
| FEEDBACK-01 | Phase 13 | Pending |
| FEEDBACK-02 | Phase 13 | Pending |
| FEEDBACK-03 | Phase 13 | Pending |
| FEEDBACK-04 | Phase 13 | Pending |
| FEEDBACK-05 | Phase 13 | Pending |
| FEEDBACK-06 | Phase 13 | Pending |
| FEEDBACK-07 | Phase 13 | Pending |
| FEEDBACK-08 | Phase 13 | Pending |
| FEEDBACK-09 | Phase 13 | Pending |
| FEEDBACK-10 | Phase 13 | Pending |

**Coverage:**
- v1.3 requirements: 24 total
- Mapped to phases: 24 (Phase 13: 10, Phase 14: 7, Phase 15: 7)
- Unmapped: 0 ✓

---

*Requirements defined: 2026-04-29*
*Last updated: 2026-04-29 — traceability table filled after roadmap creation*
