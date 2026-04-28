# Strategic Overview: Translation Quality Review Automation

**Maintained as:** Living doc. Three-phase scope sections are stable; the Phase 1 Status section + STR-02 checklist update at the end of each milestone via `/gsd:complete-milestone` (per D-14).

**Date:** 2026-04-28
**Owner:** Juan

---

## Purpose

This document is the single capstone for the project's three-phase vision. It tells a reader:
1. What each of the three phases delivers, with scope boundaries that determine where a new idea belongs.
2. How phase transitions work (the two-stage Orange-Light / Green-Light gate pattern).
3. What concrete conditions must be true before Phase 1 (Audit & Tune) gives way to Phase 2 (AI Translation Generation) — the STR-02 checklist.
4. Where to file a new idea — the routing rubric.

This is a routing layer over existing GSD primitives (`/gsd:add-backlog`, `/gsd:plant-seed`, `/gsd:insert-phase`, `/gsd:add-phase`, `/gsd:complete-milestone`), not a replacement for them. The future `/gsd:submit-idea` skill (Phase 13, deferred) will read this document to dispatch.

For source-of-truth detail beyond the inline summaries below, follow the linked artifacts.

---

## Phase 1: Audit & Tune

### Goal

Tune the existing review pipeline (structural validator + AI reviewer + Notion publishing + corrections loop) until every run produces a reliable, actionable report — fast enough and cheap enough to run on every translation batch. This is the phase the project is currently in.

### Deliverables

- Structural validator (`scripts/structural_validator.py`) covering variable presence, block placement, emoji preservation, encoding, France-row detection.
- Two-tier AI review (Tier 2 Haiku spot-check for clean markets, Tier 1 Sonnet full review for flagged markets).
- Notion publishing pipeline (review reports → Reports DB).
- Corrections learning loop (`corrections/corrections_log.json` → `corrections/rules_summary.json`).
- README + CLAUDE.md sufficient for a new maintainer to run a review unaided.
- Audit + fix cycles closing IC items (see [`.planning/AUDIT.md`](AUDIT.md), [`.planning/v1.2-MILESTONE-AUDIT.md`](v1.2-MILESTONE-AUDIT.md)).

See [`.planning/PROJECT.md`](PROJECT.md) and [`.planning/REQUIREMENTS.md`](REQUIREMENTS.md) (v1.1 + v1.2 sections) for the validated requirement list.

### Scope boundary

- IN: anything that improves trust, cost, or actionability of the *current* review pipeline.
- OUT: generating translations from scratch (Phase 2); embedding in the Superprof BO (Phase 3).

### Open questions resolved when phase begins

- Already in flight. Open items are tracked as IC entries in [`.planning/v1.2-MILESTONE-AUDIT.md`](v1.2-MILESTONE-AUDIT.md).

---

## Phase 2: AI Translation Generation

### Goal

Use the rules accumulated in Phase 1 (`corrections/rules_summary.json` + `config/*`) to *produce* first-draft translations from a French source — not just review human ones. The reviewer becomes a writer.

### Deliverables

- `generate-translation` skill (REQ: GEN-02) — accepts French source + target language, returns first-draft translation conditioned on accumulated rules.
- Rules-as-context loader (REQ: GEN-01) — loads `rules_summary.json` into the generation skill at runtime.
- Self-validation pass (REQ: GEN-03) — generated translations run through the same structural + reference document checks that human translations do.

See [`.planning/REQUIREMENTS.md`](REQUIREMENTS.md) § "Future Requirements (v2+)" → Translation Generation for current REQ stubs.

### Scope boundary

- IN: anything that turns French source + accumulated rules into a vetted first-draft translation in any target language.
- OUT: integrating that draft into the BO (Phase 3); reviewing human translations (still Phase 1).

### Open questions resolved when phase begins

- Which Claude model tier per generation step (cost vs. quality trade-off).
- Where the generation skill lives — local `.claude/commands/` vs. global `~/.claude/get-shit-done/`.
- How rules are merged when `rules_summary.json` and `config/tone_guidelines.json` disagree.
- Whether generated drafts go straight to the existing review pipeline or have a dedicated gate first.
- How French-source fidelity is measured (no human reference exists by definition).

Architecture sketches and additional REQs (GEN-04, GEN-05, …) are deferred to Phase 2's own discuss-phase (per D-02a).

---

## Phase 3: Backoffice Integration

### Goal

Make the translation generation agent reachable from inside the Superprof backoffice — one click per market, draft applied directly without leaving the BO.

### Deliverables

- BO-side integration surface (REQ: INT-01) — generation agent invoked from within the BO admin per market.
- Apply-in-place flow (REQ: INT-02) — generated translation written to the target market without leaving the BO.
- (Hint: backlog Phase 999.1 — URL-driven translation review — is an early Phase 3 deliverable shape.)

See [`.planning/REQUIREMENTS.md`](REQUIREMENTS.md) § "Future Requirements (v2+)" → Backoffice Integration for current REQ stubs, and [`.planning/ROADMAP.md`](ROADMAP.md) § "Backlog → Phase 999.1" for the closest-to-real Phase 3 backlog entry.

### Scope boundary

- IN: anything that lives inside or directly hooks into the Superprof BO admin UI.
- OUT: improving the generator itself (Phase 2); improving the review pipeline (Phase 1).

### Open questions resolved when phase begins

- Auth flow for BO (session cookie, SSO, login script).
- Playwright vs. native API for BO interaction (per backlog 999.1 decision: Playwright).
- Notion / Slack notification wiring for completed BO runs.
- Rate limits and retry behavior on BO write failures.
- Where the BO-side button / entry point lives in the existing admin UI.

Architecture sketches are deferred to Phase 3's own discuss-phase (per D-02a).

---

## Two-Stage Gate Pattern

This pattern governs every phase transition in this project — Phase 1 → 2 AND Phase 2 → 3. Phase 1 is the worked example; later phases reuse the template.

### The gates

- **Orange Light** — All *must-have* criteria for the current phase are green.
  - **What it unlocks:** the next phase's exploration **spikes** — throwaway, time-boxed, isolated to `scripts/spikes/` or `experiments/`. Never to production code paths (per D-05).
  - **What it does NOT unlock:** the next phase proper. Current-phase work continues to close should-haves.

- **Green Light** — All *must-have* AND *should-have* criteria are green, AND ≥ 1 spike has produced commit-worthy learnings (per D-03).
  - **What it unlocks:** the next phase proper begins. A new milestone opens; current-phase work archives.

### Spike governance (during the orange-light period)

- Spikes live under `scripts/spikes/` or `experiments/` — never in `scripts/` (D-05).
- Each spike is added as a small phase via `/gsd:add-phase`, named `Phase X.Y: Spike — [topic]` (D-06).
- Deliverables per spike: 1-page PLAN.md + 1-page LEARNINGS.md. No VERIFY.md (D-06).
- Time-box: ≤ 1 week of work (D-07).
- Outcome at close: either *promote to a real phase* or *park, lessons captured* (D-07).

### Visual

```
                       MUST-HAVES green
   Phase N work  ────────────────────────►  ORANGE LIGHT
                                            │
                                            ▼
                          spikes allowed in scripts/spikes/
                          (≤ 1 week each, throwaway)
                                            │
                  SHOULD-HAVES green + ≥1 spike commit-worthy
                                            │
                                            ▼
                                       GREEN LIGHT
                                            │
                                            ▼
                                  Phase N+1 proper begins
```

### Why two stages, not one

A single hard cut forces all exploration into a future phase, blocking learning that could redirect should-haves. A trigger-based gate ("after 3 noisy runs") makes the transition reactive, not deliberate. The two-stage gate keeps Phase N focused on its should-haves while letting Phase N+1 gather grounded evidence — and forces at least one spike to actually produce something before a milestone change.

---

## Phase 1 Readiness Checklist (STR-02)

This is the concrete instance of the must-have / should-have pattern for the current Phase 1 → Phase 2 transition.

The criteria below govern the Phase 1 → Phase 2 transition (per the Two-Stage Gate Pattern above). Each band mixes quantitative, qualitative, and audit-derived gates (per D-08).

### Must-Have Gates (Orange Light — unlocks Phase 2 spikes)

- [ ] **Audit — zero open critical findings.** All `critical` items in [`.planning/AUDIT.md`](AUDIT.md) either resolved or explicitly downgraded with a recorded rationale.
- [ ] **Audit — all v1.2 IC items closed.** [`.planning/v1.2-MILESTONE-AUDIT.md`](v1.2-MILESTONE-AUDIT.md) shows IC-01 ✓ (closed Phase 11) AND IC-02 closed (Phase 12).
- [ ] **Maintainer onboarding — qualitative.** A new maintainer can run a full review and interpret the report using only `README.md` + `CLAUDE.md`, without asking Juan a clarifying question.
- [ ] **Recurring-error category stability — qualitative.** No new recurring-error category surfaced in 2 consecutive review sessions. (A "category" is a pattern shared by ≥ 2 markets, distinct from those already documented in `CLAUDE.md`.)

### Should-Have Gates (Green Light — unlocks Phase 2 proper)

- [ ] All Must-Have gates above remain green.
- [ ] **Token cost — quantitative.** Per-run token usage stays within ±20% of the v1.1 baseline (recorded in milestone notes at v1.1 archival).
- [ ] **Tier-2 routing — quantitative.** Tier-2 (Haiku spot-check) covers ≥ 60% of markets per typical run. Measured over the last 3 runs.
- [ ] **Notion publish quality — qualitative.** Reports published to Notion require zero manual cleanup before sharing.
- [ ] **Phase 2 spike — process.** ≥ 1 Phase 2 spike (under `scripts/spikes/` per the Two-Stage Gate Pattern) has produced commit-worthy learnings recorded in its `LEARNINGS.md`.

### How this section gets updated

Tick boxes on this list at the end of each milestone via `/gsd:complete-milestone`. When all Must-Haves are green: open the orange-light state in `STATE.md` and start spikes. When all Should-Haves are green and ≥ 1 spike is commit-worthy: green-light, open Phase 2 proper.

---

## Phase 2 Readiness Checklist

To be filled when Phase 2 enters its own readiness milestone — populate using the same must-have / should-have pattern documented above (per D-10). Not detailed in this phase.

---

## Phase 3 Readiness Checklist

To be filled when Phase 3 enters its own readiness milestone — same pattern.

---

## Routing Rubric: Where Does This Idea Belong?

> **PLACEHOLDER — TASK 3 FILLS THIS SECTION.**
> Markdown table with columns `Signal | Destination | GSD primitive`. Rows from D-12. Stable structure — future `/gsd:submit-idea` skill consumes this table.

---

## Maintenance

- Three-phase scope sections (Phase 1 / 2 / 3 above): stable. Update only when scope itself shifts (rare).
- Phase 1 Readiness Checklist: living. Updated at the end of each milestone via `/gsd:complete-milestone`.
- Phase 2 / Phase 3 Readiness Checklists: filled in when those phases enter their own readiness milestones.
- Routing Rubric: stable. Update when a new GSD primitive lands or a phase boundary shifts.

---

## References

- [`.planning/PROJECT.md`](PROJECT.md) — current truth on validated/active/out-of-scope requirements.
- [`.planning/REQUIREMENTS.md`](REQUIREMENTS.md) — STR-01, STR-02; GEN-01..03; INT-01..02.
- [`.planning/ROADMAP.md`](ROADMAP.md) — phase status, milestone history, backlog.
- [`.planning/AUDIT.md`](AUDIT.md) — Phase 8 findings; feeds audit-derived gates below.
- [`.planning/v1.2-MILESTONE-AUDIT.md`](v1.2-MILESTONE-AUDIT.md) — IC-01 (closed Phase 11), IC-02 (open, Phase 12).
- [`CLAUDE.md`](../CLAUDE.md) — recurring error patterns; tone constraints.

---

*Created: 2026-04-28 (Phase 10 — Strategic Overview)*
