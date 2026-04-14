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

## Cross-Milestone Trends

| Milestone | Phases | Plans | Timeline | Active Reqs | Deferred |
|-----------|--------|-------|----------|-------------|---------|
| v1.1 | 6 active | 11 | 7 days | 20/20 | 3 (HND) |

*More milestones will populate this table over time.*
