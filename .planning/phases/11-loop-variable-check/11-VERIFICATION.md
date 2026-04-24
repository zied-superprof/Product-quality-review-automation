---
phase: 11-loop-variable-check
verified: 2026-04-24T00:00:00Z
status: passed
score: 5/5 must-haves verified
---

# Phase 11: Loop-Variable Structural Check Verification Report

**Phase Goal:** Close IC-01 / complete FIX-06 — teach `scripts/structural_validator.py` to flag when a template variable appears in a different structural block than the French reference places it, catching the recurring wrong-loop-variable errors deterministically.

**Verified:** 2026-04-24
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Arabic CSV with `@TPL_MATIERE_DE_MATIERE@` inside `<TPL_LOOP_ANNONCES>` (absent in French loop) produces `variable_block_mismatch` error | VERIFIED | Inline Python test against `check_variable_block_placement` with an Arabie Saoudite row flagged `MATIERE_DE_MATIERE` as expected. |
| 2 | Arabic CSV with `@TPL_ANNONCE_AFFICHE_QUI_CONNECTE@` inside `<TPL_IF_LISTE_AVIS>` (French has it inside `<TPL_LOOP_ANNONCES>`) produces `variable_block_mismatch` | VERIFIED | Same inline test flagged `ANNONCE_AFFICHE_QUI_CONNECTE` with `ref_block=TPL_LOOP_ANNONCES` vs `trans_block=TPL_IF_LISTE_AVIS`. |
| 3 | Translation with identical block placement to French produces zero `variable_block_mismatch` findings | VERIFIED | Inline test on matched `@TPL_X@` + `<TPL_LOOP_A>@TPL_Y@</TPL_LOOP_A>` pair returned `[]`. |
| 4 | When language+variable listed in `block_scope_overrides`, the check does NOT flag, even if block differs from French | VERIFIED | Inline override test: 1 finding without override, 0 findings with `{'ar': {'X': {'allowed_blocks': ['TPL_LOOP_A']}}}`. |
| 5 | Variable present only in translation (not in French) is NOT flagged as `variable_block_mismatch` (D-10) | VERIFIED | Inline test with translation-only `@TPL_X@` returned `[]`. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/structural_validator.py` — `check_variable_block_placement()` | function wired into `validate_entry()` | VERIFIED | Defined at line 928; call-site at line 1063 inside `validate_entry`. |
| `scripts/structural_validator.py` — `scan_block_contexts()` | stack-based innermost-block scanner | VERIFIED | Defined at line 768; unit-tested via `scan_block_contexts('hello @TPL_X@ <TPL_LOOP_A>@TPL_Y@</TPL_LOOP_A>')` returning `{'X': ['body'], 'Y': ['TPL_LOOP_A']}`. |
| `scripts/structural_validator.py` — `load_block_scope_overrides()` | soft-fail loader matching `load_subject_variable_rules` convention | VERIFIED | Defined at line 210; returns `cfg.get('block_scope_overrides')`; live call returned dict with `_note` key. |
| `scripts/structural_validator.py` — `_fmt_block()` helper | renders `the body` vs `<TAG>` in messages | VERIFIED | Defined at line 923 immediately above `check_variable_block_placement`. |
| `scripts/structural_validator.py` — LOOP regex | `RE_LOOP_OPEN`, `RE_LOOP_CLOSE`, `RE_LOOP_NAME` | VERIFIED | Lines 41, 42, 45. |
| `scripts/structural_validator.py` — `RE_BLOCK_OR_VAR` unified scanner regex | alternation over close/open/var | VERIFIED | Line 761. |
| `config/label_patterns.json` — `block_scope_overrides` top-level key | empty object with `_note` at launch | VERIFIED | `json.load` confirms key present, type=dict, length=1 (contains `_note`). |
| `validate_entry` signature accepts `block_overrides: dict | None = None` | wired parameter | VERIFIED | Line 1048. |
| CLI `main()` loads overrides once per run | `load_block_scope_overrides(config_dir)` + passed to `validate_entry` | VERIFIED | Line 1079 loads, line 1119 passes `block_overrides=block_overrides`. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `validate_entry()` | `check_variable_block_placement()` | `all_issues.extend(check_variable_block_placement(ref_entry, entry, block_overrides))` | WIRED | Matched at line 1063. |
| `main()` / CLI | `load_block_scope_overrides()` | `block_overrides = load_block_scope_overrides(config_dir)` | WIRED | Matched at line 1079. |
| `check_variable_block_placement()` | `get_language_code()` | `lang = get_language_code(entry.get('country', ''))` | WIRED | Matched at line 953 inside the check body. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|------------|-------------|-------------|--------|----------|
| FIX-06 | 11-01-PLAN.md | Highest-priority critical findings from the AUD phase are implemented (scope confirmed after audit) | SATISFIED | REQUIREMENTS.md marks `[x] FIX-06 … completed 2026-04-24 via Phase 11`. Live validator run produced 12 `variable_block_mismatch` findings across 12 markets (Turquie, Nigéria, Croatie, Slovénie, Lettonie, Albanie, Vietnam, Estonie, Serbie, Roumanie, Moldavie, Monténégro) on 2 samples — proves AUDIT finding [#8] class of bug is now caught deterministically. Plan declared only FIX-06; no orphaned requirement IDs for Phase 11. |

### Regression Gate

| Test | Status | Details |
|------|--------|---------|
| `scripts/test_summary_flag.py` | PASS | 7/7 tests passed (exit 0). |
| `scripts/test_subject_variable_variant.py` | PASS | 17/17 tests passed (exit 0). |
| `python3 scripts/structural_validator.py --help` | PASS | exit 0; CLI parses. |
| Live-run regression sample A (`annonce-demande-recos.csv`) | PASS | Exits 0, 99 errors / 93 warnings / 85 info across 101 countries; existing `variable_missing`, `variable_extra`, emoji, subject variable, conditional checks still fire. |
| Live-run regression sample B (`profil_engagement_relance_2.csv`) | PASS | Exits 0, 118 errors / 112 warnings / 0 info across 101 countries. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | — | — | No blocker / warning patterns. The only `TODO`/`FIXME` grep hits are inside the pre-existing `check_empty_placeholder()` function (lines 471–521) which intentionally scans for those strings as placeholder markers — not stubs in new code. |

### Live-Run Evidence (confirms human-verify checkpoint claim)

Against must_have: "Live run against real samples produces `variable_block_mismatch` findings (verified during human-verify checkpoint — 12 findings across 12 different languages on 2 samples)."

- `samples/annonce-demande-recos.csv`: 7 `variable_block_mismatch` findings across 7 distinct markets — Albanie, Croatie, Lettonie, Nigéria[Groupement], Slovénie, Turquie, Vietnam. Includes the Nigéria IF→ELSE legit catch (`MEMBRE_NB_RECOS ref=TPL_IF_MEMBRE_RECOS trans=TPL_ELSE_MEMBRE_RECOS`) noted in SUMMARY.
- `samples/profil_engagement_relance_2.csv`: 5 `variable_block_mismatch` findings across 5 distinct markets — Estonie, Moldavie, Monténégro, Roumanie, Serbie.
- **Total: 12 findings across 12 distinct markets on 2 samples** — matches the claim in the must_haves and in `11-01-SUMMARY.md` exactly.

### Commit Verification

| Commit | Purpose | Status |
|--------|---------|--------|
| `7750d94` | feat(11-01): add block_scope_overrides config key and LOOP regex primitives | Present in git log |
| `67028f7` | feat(11-01): add check_variable_block_placement and wire into validate_entry | Present in git log |

### Human Verification Required

None outstanding. The human-verify checkpoint (Task 3) was completed during phase execution; its claim (12 findings across 12 languages on 2 samples) was re-reproduced in this verification pass with identical numbers.

### Gaps Summary

No gaps. All 5 observable truths verified, all 9 required artifacts present and wired, all 3 key links connected, both regression test suites pass, live runs on 2 real samples reproduce the human-verify evidence exactly, and FIX-06 is marked complete in REQUIREMENTS.md with matching implementation evidence.

One minor note (not a gap, not a blocker): the SUMMARY captures a deliberately-kept quirk where same-block count-mismatch findings (e.g. Estonie `MATIERE_DE_MATIERE` ref=body trans=body) produce messages that read awkwardly because both blocks are `body`. The user explicitly decided during Task 3 to keep this behavior; it is correct (multiset mismatch) and was reproduced in today's run. Captured in SUMMARY "Follow-ups / Noted Considerations" as a future UX consideration, not a verification gap.

---

*Verified: 2026-04-24*
*Verifier: Claude (gsd-verifier)*
