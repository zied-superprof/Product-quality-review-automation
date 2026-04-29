# Retrospective — Translation Quality Review Automation

## Milestone: v1.1 — Notion Publishing & Batch Feedback Routing

**Shipped:** 2026-04-14
**Phases:** 6 active (1–3, 5–7) + 1 deferred (4) | **Plans:** 11

### What Was Built

1. Step 4c silent accumulation — eliminated 5k–30k tokens of per-market JSON echo per run
2. `--summary` flag on structural_validator.py — 80–90% token reduction on Step 2 output, wired into call site via Phase 07 after Phase 01 built the flag
3. Reference doc reliability — Variables.csv hard-fail, Step 1 health check, formality deviation flagging
4. 8-field corrections log schema + top-3 per-language rule surfacing with relevance scoring
5. Notion auto-publish on review completion; HTML output removed entirely
6. Batch feedback routing — N comments → routing suggestion per item → one-pass confirmed writes

### What Worked

- **Incremental hardening order**: Token optimization first (unblocked cheaper runs), then reference reliability (unblocked trustworthy output), then feedback loop structure (unblocked generation milestone). Dependency order meant each phase had a clean foundation.
- **Audit-driven gap closure**: The v1.1 audit surfaced FINDING-01 (argparse crash on `--type` flag) that none of the phase verifiers caught. Integration checker as a separate audit step caught what static grep couldn't.
- **Batch feedback as Step 7 extension**: Adding batch mode as a branch inside the existing Step 7 (rather than a new skill) meant single-item feedback was preserved untouched and users got batch support without context switching.
- **Soft-fail on Notion publish**: Wrapping the MCP call in soft-fail (Step 6 continues if Notion is down) was the right default — review output can't be held hostage to Notion availability.

### What Was Inefficient

- **TOK-02 two-phase realization**: The `--summary` flag was built in Phase 01 but not wired into Step 2 until Phase 07 (a 7-phase gap). The Phase 01 verifier noted "wired but not called" but didn't block — this drifted into tech debt. A verify-then-wire pattern (build the flag AND wire it in the same plan) would have closed the loop immediately.
- **`--type` flag ghost**: The Step 2 bash command contained `--type [per-notification|full-database]` which was never implemented in argparse. This caused argparse crashes on every review run and wasn't caught until the integration checker ran. Phase verifiers only grep-checked their specific changes, not the surrounding command.
- **SUMMARY.md frontmatter gap**: None of the 11 SUMMARY.md files have `requirements-completed` YAML frontmatter. The 3-source cross-reference fell back to 2 sources for the entire milestone. Not a blocker, but a consistent documentation pattern miss.

### Patterns Established

- **Integration checker as audit step**: Running an integration checker subagent at milestone audit time catches cross-phase wiring issues that per-phase verification misses. Standardize this as part of every milestone audit.
- **Tech debt closure as a formal phase**: Phase 7 (Tech Debt Cleanup) was a clean pattern — one phase to close all audit gaps before archiving. Better than deferred items floating into the next milestone.
- **Argparse safety**: Before adding flags to a bash command in a skill, verify the flag exists in the script's argparse definition. A quick grep catches this before it becomes a runtime crash.

### Key Lessons

1. **Verify the full command, not just the changed line**: Phase verifiers that only check their specific diff miss pre-existing issues in surrounding code.
2. **Wire features at build time**: If a flag is built in Phase N, wire it into all call sites in the same plan — don't leave it for a future phase to discover.
3. **Audit files are living documents**: The `gaps_found` → `tech_debt` → final state cycle on v1.1-MILESTONE-AUDIT.md was correct but required multiple edit passes. A single-pass audit that stays open until gaps are closed would be cleaner.

### Cost Observations

- Sessions: ~12 across 7 days
- Model: Sonnet 4.6 throughout (orchestration + execution)
- Notable: Integration checker subagent (Explore agent) caught the argparse crash that 6 phase verifiers missed — cost of one subagent invocation vs. cost of a broken pipeline in production

---

## Milestone: v1.2 — Audit, Fix & Strategic Overview

**Shipped:** 2026-04-29
**Phases:** 5 (8–12) | **Plans:** 8

### What Was Built

1. 34-finding project audit (5 critical, 14 medium, 15 low, 3 none) covering dead code, workflow brittleness, scope gaps, and config contradictions (Phase 8)
2. Critical fixes: France row content search, `unicodedata.category()` emoji detection, corrections backup-before-write, zh_TW/zh_HK BCP-47 normalization (Phase 9)
3. README rewritten with the full zero-to-running-a-review onboarding journey (Phase 9)
4. `STRATEGIC-OVERVIEW.md` capstone — 3-phase vision, two-stage Orange/Green gate pattern, Phase 1 readiness checklist (4 must-have + 5 should-have), parseable routing rubric (Phase 10)
5. Deterministic `variable_block_mismatch` check — multiset block comparison against the French reference; live-verified across 12 non-Arabic languages plus a Nigéria IF→ELSE catch (Phase 11, closes IC-01)
6. zh-HK orphaned correction rule merged into zh-TW; `_build_report.py` drift discovered and aligned with canonical `structural_validator.py:684` mapping (Phase 12, closes IC-02)

### What Worked

- **Audit-first sequencing** — Phase 8 produced a prioritized 34-finding scope before Phase 9 implemented; FIX-06 was scoped against critical findings #19 and #27, not a rough hunch.
- **Gap-closure phases as first-class scope** — when the v1.2-MILESTONE-AUDIT (run 2026-04-23) flagged IC-01 and IC-02 as material, Phases 11 and 12 were added to ROADMAP.md as decimal-ish gap-closure phases rather than letting them slip into v1.3. Both shipped before milestone close.
- **Live-run verification on real CSVs** — Phase 11 surfaced that the wrong-loop-variable bug class wasn't Arabic-specific (12 non-Arabic languages produced findings, plus Nigéria IF→ELSE). Theoretical golden-case unit tests would have shipped a narrower check.
- **Backup-before-write extended to script edits** — Phase 12 backed up `_build_report.py` alongside the corrections JSONs, treating FIX-05's intent (no accumulated work lost) as a principle, not a JSON-only rule.
- **Planning checker catching cross-file drift** — `_build_report.py` had silently diverged from `structural_validator.py:684` (`'Hong-Kong': 'zh-HK'` vs `'zh-TW'`). The Phase 12 planning checker's project-wide grep caught this; the file was added to scope before execution rather than discovered post-hoc.

### What Was Inefficient

- **FIX-06 scope narrowed silently in Phase 9** — AUDIT prescribed [#8] (wrong-loop-variable check) as priority #2 of FIX-06; Phase 9 shipped FIX-06 marked complete without [#8] and without a deferral record. The per-phase verifier checked what the plan claimed, not what AUDIT.md prescribed. Caught only when v1.2-MILESTONE-AUDIT ran cross-phase integration check (IC-01). Phase 11 had to be added retroactively.
- **zh-HK orphan introduced by Phase 9** — the `zh_TW → zh-TW` normalization in Phase 9 Plan 02 accidentally created a separate `zh-HK` learning entry that no config or country-code map referenced. The orphan was invisible to per-phase verification because it was internally consistent within `corrections/`. Caught only by IC-02 cross-reference. Phase 12 closed it.
- **Audit ran mid-milestone, not at the start** — `v1.2-MILESTONE-AUDIT.md` was created 2026-04-23, after Phases 8 and 9 shipped, then re-read after Phases 10/11/12 closed the gaps. The audit document carried `status: gaps_found` through to milestone close even though all gaps were demonstrably closed; it was never re-run. Pattern: run a final audit pass after gap-closure phases, not just rely on the gap-closure phases' own SUMMARY.md citations.
- **STR-01/STR-02 placeholder for 2 weeks** — Phase 10 was scoped from the start of v1.2 but didn't start until 2026-04-28 (a 14-day gap behind Phases 8/9). The STRATEGIC-OVERVIEW.md capstone took ~12 minutes to write once started. Pattern: documentation phases can run earlier in parallel with code phases when they don't depend on the code state.

### Patterns Established

- **Decimal-ish gap-closure phases** — when a milestone audit surfaces material integration gaps, add explicitly-scoped phases (Phase 11 closes IC-01, Phase 12 closes IC-02) rather than retrofitting fixes into existing phases or deferring to the next milestone. ROADMAP.md gets clean traceability; SUMMARY.md cites the closed IC.
- **Strategic overview as a sibling of PROJECT.md** — STRATEGIC-OVERVIEW.md lives at `.planning/STRATEGIC-OVERVIEW.md`, peer to PROJECT.md/REQUIREMENTS.md/ROADMAP.md. Survives milestone archival because it spans the multi-milestone vision, not the current scope.
- **Two-stage Orange/Green gate as a reusable template** — Phase 1 is the worked example, but the pattern (must-have gates unlock spikes; should-have gates unlock the next phase proper) is now a reusable transition contract for any future milestone-to-milestone hop.
- **Routing rubric as a parseable structure** — `Signal | Destination | GSD primitive` column contract is locked so a future `/gsd:submit-idea` skill can read it without re-parsing prose.
- **Backup convention extends beyond JSON** — Phase 12 backed up a Python script alongside JSON files using the same FIX-05 timestamp pattern. Generalize: any pre-edit snapshot that protects accumulated state belongs under `corrections/backups/{timestamp}_{filename}`.

### Key Lessons

1. **Per-phase verification doesn't catch cross-phase drift.** v1.1 retrospective made this point about argparse; v1.2 doubled down with FIX-06 scope narrowing (IC-01) and the zh-HK orphan (IC-02). The remedy is a milestone-level integration check that compares prescribed scope (AUDIT.md, REQUIREMENTS.md) against shipped artifacts, not just a per-phase verifier.
2. **Run the final audit pass after gap-closure phases, not before.** If the audit document still says `gaps_found` at milestone close, even after gap-closure phases shipped, downstream readers can't tell whether the gaps are open or closed without reading every SUMMARY.md. A re-audit produces a single source of truth.
3. **A grep floor is a mechanical guard worth keeping.** Phase 12's D-06 grep floor (`zh-HK\|zh_HK` returning zero hits across `config/`, `corrections/`, `scripts/`, `.claude/commands/`) is what surfaced `_build_report.py` drift. The pattern generalizes: any merge/cleanup phase should declare a project-wide grep floor as part of its acceptance criteria.
4. **Untracked files can drift.** `_build_report.py` was untracked when Phase 12 began but had silently diverged from the canonical mapping. Untracked ≠ unimportant. Future audit phases should include `git ls-files --others --exclude-standard` in their scope to surface untracked-but-active code.

### Cost Observations

- Sessions: ~10–12 across 15 days (calendar time, not active time — much of the gap was idle)
- Model mix: predominantly Sonnet 4.6; planning checker and integration checker were the highest-value subagent invocations.
- Notable: Two material defects (IC-01, IC-02) were caught by milestone audit / planning checker, not by per-phase verification. Each cost ~one subagent invocation; each prevented either deferred tech debt to v1.3 or a broken correction-loop in production.

### Patterns Worth Stealing for v1.3

- Gap-closure phases as first-class scope (don't defer)
- Project-wide grep floor on cleanup/merge phases
- Strategic overview as multi-milestone sibling, not a per-milestone artifact
- Re-run audit after gap closure to get a clean final verdict

---

## Cross-Milestone Trends

| Milestone | Phases | Plans | Timeline | Active Reqs | Deferred / Gap |
|-----------|--------|-------|----------|-------------|----------------|
| v1.1 | 6 active | 11 | 7 days | 20/20 | 3 (HND → v1.2) |
| v1.2 | 5 | 8 | 15 days (calendar) | 13/13 | IC-03 accepted; broader language-database review + code-level lang-code guard → v1.3+ |

*Recurring theme:* per-phase verification misses cross-phase drift. v1.1 caught it via the integration checker (argparse `--type` ghost); v1.2 caught it via milestone audit (IC-01 FIX-06 narrowing, IC-02 zh-HK orphan). The integration check is now load-bearing — keep it as part of every milestone close, not optional.
