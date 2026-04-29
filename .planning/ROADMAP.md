# Roadmap: Translation Quality Review Automation

## Milestones

- ✅ **v1.1 — Notion Publishing & Batch Feedback Routing** — Phases 1–3 + 5–7 (shipped 2026-04-14)
- ✅ **v1.2 — Audit, Fix & Strategic Overview** — Phases 8–12 (shipped 2026-04-29)
- 🚧 **v1.3 — End-to-End Review Automation** — Phases 13–15 (in progress)

## Phases

<details>
<summary>✅ v1.1 — Notion Publishing & Batch Feedback Routing (Phases 1–3, 5–7) — SHIPPED 2026-04-14</summary>

- [x] Phase 1: Token Optimization (2/2 plans) — completed 2026-04-08
- [x] Phase 2: Reference Reliability + Report Format (2/2 plans) — completed 2026-04-08
- [x] Phase 3: Feedback Loop Strengthening (2/2 plans) — completed 2026-04-09
- [ ] Phase 4: Team Handoff — **deferred to v1.2 (absorbed into Phase 9)**
- [x] Phase 5: Notion Publishing (2/2 plans) — completed 2026-04-09
- [x] Phase 6: Batch Feedback Routing (2/2 plans) — completed 2026-04-10
- [x] Phase 7: Tech Debt Cleanup (1/1 plans) — completed 2026-04-14

Full details: [milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)

</details>

<details>
<summary>✅ v1.2 — Audit, Fix & Strategic Overview (Phases 8–12) — SHIPPED 2026-04-29</summary>

- [x] Phase 8: Project Audit (2/2 plans) — completed 2026-04-16
- [x] Phase 9: Fixes (3/3 plans) — completed 2026-04-16
- [x] Phase 10: Strategic Overview (1/1 plan) — completed 2026-04-28
- [x] Phase 11: Loop-Variable Structural Check (1/1 plan) — completed 2026-04-24 (closes IC-01)
- [x] Phase 12: zh-HK Language Code Resolution (1/1 plan) — completed 2026-04-28 (closes IC-02)

Full details: [milestones/v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md)

</details>

### 🚧 v1.3 — End-to-End Review Automation (In Progress)

**Milestone Goal:** Automate the review pipeline from input (Superprof BO URL) to output (Notion report), with a standalone `/submit-feedback` skill that replaces the in-session Step 7 and adds a full rule lifecycle. The existing CSV-drop flow coexists throughout.

**Phase Ordering Rationale:**
- **Phase 13 first (FEEDBACK):** Thread 3 has zero dependency on Threads 1 and 2. Ships first so the feedback path is available before Step 7 is removed.
- **Phase 14 second (INGEST):** Thread 1 is independent of Thread 3 and must be proven before the skill can wire up URL mode. Includes a mandatory headed-Playwright spike to resolve BO auth (OQ-1) and stable selectors (OQ-4) before any production code is written.
- **Phase 15 last (PARALLEL):** Thread 2 depends on Thread 1 (needs the extractor) and on Thread 3 (Step 7 removal is only safe once `/submit-feedback` is live). Ships last.

- [ ] **Phase 13: Standalone Feedback Skill** - New `/submit-feedback` skill with append flow, rule pruning, and tier promotion
- [ ] **Phase 14: BO Extraction** - Playwright extractor turning a BO URL into named CSVs (includes spike)
- [ ] **Phase 15: Parallel Reviews** - Skill updated for URL mode + concurrent email/SMS execution + Step 7 removal

## Phase Details

### Phase 13: Standalone Feedback Skill
**Goal**: Users can submit translation corrections independently of any review session, with a clean rule lifecycle that keeps the learning system accurate over time.
**Depends on**: Nothing (Thread 3 is independent)
**Requirements**: FEEDBACK-01, FEEDBACK-02, FEEDBACK-03, FEEDBACK-04, FEEDBACK-05, FEEDBACK-06, FEEDBACK-07, FEEDBACK-08, FEEDBACK-09, FEEDBACK-10
**Success Criteria** (what must be TRUE):
  1. User can run `/submit-feedback` (with or without a report path) at any time outside of a review session and submit corrections that are written to the correct config file
  2. When a report path is provided, every correction in the session is tagged with the real `notification_type` from the report header; when skipped, the tag is `"adhoc"` (not the misleading `"batch-feedback"`)
  3. All four writable files (`corrections_log.json`, `rules_summary.json`, `label_patterns.json`, `tone_guidelines.json`) receive a timestamped backup in `corrections/backups/` before the first write of the session
  4. When multiple feedback items conflict with existing rules, all conflicts surface in one numbered list and the user resolves them in a single answer; selecting `append` triggers a sub-dialogue that requires both agent self-check and user clarity check before the write, and archives the original two rules
  5. After every session, the skill surfaces pruning candidates (stale / single-occurrence / low-confidence / superseded rules) one-by-one and promotion candidates (Tier 1 → Tier 2) one-by-one; nothing auto-archives; declined promotions are recorded so they do not re-surface until criteria change
**Plans**: TBD

Plans:
- [ ] 13-01: TBD

### Phase 14: BO Extraction
**Goal**: Users can paste a Superprof BO notification admin URL and receive 1–2 correctly named CSVs in `samples/` ready for review, with one-time auth setup and clear error messages for expired sessions or missing data.
**Depends on**: Nothing (Thread 1 is independent of Thread 3)
**Requirements**: INGEST-01, INGEST-02, INGEST-03, INGEST-04, INGEST-05, INGEST-06, INGEST-07
**Note on spike**: The first task of this phase is a 1–2 hour headed-Playwright inspection session on the actual BO page. This resolves OQ-1 (BO auth mechanism) and OQ-4 (stable CSS/ARIA selectors). No production code is written until a LEARNINGS document records the answers. The coexistence gate (existing CSV-drop flow still works) must pass before the phase is complete.
**Success Criteria** (what must be TRUE):
  1. User runs `python scripts/_setup_bo_auth.py` once and the BO session is persisted; subsequent calls to `scripts/extract_bo_page.py <URL>` succeed headlessly without re-authenticating
  2. Pasting a BO notification URL produces 1–2 CSVs in `samples/` with filenames derived from the page information block (email tab → `_email.csv`, SMS tab → `_sms.csv`), matching what a manual export would produce
  3. When a URL points to a page with no translation data, the extractor exits with the exact error message `"No translation grid found at this URL — verify the page has at least an Email or SMS tab."` and writes no file
  4. When the saved BO session has expired, the extractor exits with `BOAuthExpiredError: rerun scripts/_setup_bo_auth.py to re-login`; `git check-ignore -v .playwright/auth/` confirms the directory is gitignored
  5. The existing CSV-drop flow (`/review-translations samples/foo.csv`) produces identical output to v1.2 behavior after all Phase 14 changes are committed
**Plans**: TBD

Plans:
- [ ] 14-01: TBD

### Phase 15: Parallel Reviews
**Goal**: When a BO URL produces both an email and an SMS CSV, the skill reviews them concurrently with independent error handling; the old in-session Step 7 is gone and users are directed to `/submit-feedback` instead.
**Depends on**: Phase 14 (needs the extractor output), Phase 13 (Step 7 removal is only safe once `/submit-feedback` is live)
**Requirements**: PARALLEL-01, PARALLEL-02, PARALLEL-03, PARALLEL-04, PARALLEL-05, PARALLEL-06, PARALLEL-07
**Success Criteria** (what must be TRUE):
  1. `/review-translations <BO_URL>` detects the URL, invokes the extractor, and fans out to review 1 or 2 channels; `/review-translations samples/foo.csv` continues to work identically to v1.2 (single-CSV path is unchanged)
  2. When both email and SMS CSVs are produced, both review runs execute concurrently and both reports appear in `reports/` and Notion when they succeed
  3. Forcing a failure in one channel (e.g. malformed CSV for SMS) leaves the other channel completing normally; the final summary shows per-channel status with the error category and a retry hint (`/review-translations samples/foo_sms.csv`)
  4. Step 7 (and all 7a/7b/7c/7d/7e variants) is entirely absent from `review-translations.md`; Step 6 ends with a pointer to `/submit-feedback`
**Plans**: TBD

Plans:
- [ ] 15-01: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Token Optimization | v1.1 | 2/2 | Complete | 2026-04-08 |
| 2. Reference Reliability + Report Format | v1.1 | 2/2 | Complete | 2026-04-08 |
| 3. Feedback Loop Strengthening | v1.1 | 2/2 | Complete | 2026-04-09 |
| 4. Team Handoff | v1.1 | 0/1 | Deferred | - |
| 5. Notion Publishing | v1.1 | 2/2 | Complete | 2026-04-09 |
| 6. Batch Feedback Routing | v1.1 | 2/2 | Complete | 2026-04-10 |
| 7. Tech Debt Cleanup | v1.1 | 1/1 | Complete | 2026-04-14 |
| 8. Project Audit | v1.2 | 2/2 | Complete | 2026-04-16 |
| 9. Fixes | v1.2 | 3/3 | Complete | 2026-04-16 |
| 10. Strategic Overview | v1.2 | 1/1 | Complete | 2026-04-28 |
| 11. Loop-Variable Structural Check | v1.2 | 1/1 | Complete | 2026-04-24 |
| 12. zh-HK Language Code Resolution | v1.2 | 1/1 | Complete | 2026-04-28 |
| 13. Standalone Feedback Skill | v1.3 | 0/TBD | Not started | - |
| 14. BO Extraction | v1.3 | 0/TBD | Not started | - |
| 15. Parallel Reviews | v1.3 | 0/TBD | Not started | - |

---

*Roadmap created: 2026-04-08*
*v1.1 shipped: 2026-04-14*
*v1.2 shipped: 2026-04-29*
*v1.3 roadmap added: 2026-04-29 — Phases 13–15 (FEEDBACK → INGEST → PARALLEL)*
