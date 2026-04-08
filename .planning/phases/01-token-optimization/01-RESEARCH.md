# Phase 1: Token Optimization - Research

**Researched:** 2026-04-08
**Domain:** Claude skill instruction design (review-translations.md) + Python CLI extension (structural_validator.py)
**Confidence:** HIGH

---

## Summary

Phase 1 has two independent work items, both fully constrained to existing files — no new dependencies, no external libraries. The bottleneck is Step 4c of `.claude/commands/review-translations.md`, where every market's AI findings are printed to the conversation as JSON before being merged. On a 39-language batch this floods the context window with raw JSON that the model must re-read during Step 5 merge. The fix is to accumulate findings in a variable (or write to a temp file) instead of printing them inline, then emit only a progress indicator per market.

The second work item adds a `--summary` flag to `scripts/structural_validator.py`. The existing CLI already routes `--output` results to a JSON file and prints a one-line summary to stderr. The `--summary` flag should print only the `by_country` dictionary in a compact human-readable format instead of the full JSON, so the AI reading the output during Step 2 consumes far fewer tokens.

TOK-03 (baseline metric) requires measuring token usage before and after. The baseline must be established before any changes are made and stored as a reference artifact.

**Primary recommendation:** Modify `review-translations.md` to accumulate Step 4c JSON to the report file silently, add `--summary` to the validator's argparse, and record a before/after token count against a reference CSV sample.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TOK-01 | Step 4c uses silent accumulation — AI findings written to report file without being output to conversation | Step 4c currently prints one JSON array per market inline; the fix is to instruct the skill to accumulate all findings into a running list and write to report only at Step 5 |
| TOK-02 | `structural_validator.py` accepts `--summary` flag — prints only market names and issue counts | The validator already builds `by_country` dict in `run_validation()`; argparse just needs a new flag that selects compact output mode |
| TOK-03 | Token baseline metric exists before optimization; post-optimization count shows measurable reduction | Baseline is established by running a review against a reference sample CSV and noting the context window token count, then repeating after changes |
</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `argparse` | 3.x (stdlib) | Add `--summary` flag to structural_validator.py | Already used in the file; no new dependency |
| Python stdlib `json` | 3.x (stdlib) | Format summary output | Already used in the file |

No new dependencies. The project is stdlib-only by design (see CLAUDE.md: "Stdlib only — no pip installs required").

### Supporting

None required for this phase.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Inline argparse extension | Separate CLI script | No reason to add a file; argparse extension is 10-line change |
| Silent accumulation via skill instruction | Subagent with file write | Subagents add latency; instruction-level change is sufficient and cheaper |

**Installation:** None required.

---

## Architecture Patterns

### Recommended Project Structure

No structural changes needed. All changes are in-place edits to existing files:

```
.claude/commands/review-translations.md   # Edit Step 4c instruction
scripts/structural_validator.py            # Add --summary flag to main()
reports/token-baseline.md                  # New artifact: baseline metric record
```

### Pattern 1: Silent Accumulation in Claude Skill (TOK-01)

**What:** Replace the inline "output JSON array per market" instruction in Step 4c with an instruction to append each market's findings to a running list held in memory, then write the full merged list to the report at Step 5 rather than echoing it to the conversation.

**Current behavior (Step 4c):**
```
For each market, evaluate the 7 criteria and output a JSON array of issues before moving to the next.
```
Every JSON array appears in the conversation context. On a 39-market batch, this can be 5,000–30,000 tokens of raw JSON that the model must process again in Step 5.

**Target behavior:**
```
For each market, evaluate the 7 criteria and append findings to an internal findings list — do NOT output JSON to the conversation. Show only a one-line progress indicator: "Reviewed [Country] ([lang]) — [N] issues."
After all markets are done, the findings list is the AI findings set for Step 5.
```

**Key constraint:** The merge in Step 5 already expects "a single flat list." The instruction change must make explicit that the flat list is accumulated silently, not echoed.

### Pattern 2: `--summary` Flag for Compact Validator Output (TOK-02)

**What:** Add a `--summary` argparse flag to `structural_validator.py`. When set, stdout receives only a compact table (market name + error/warning/info counts) instead of the full JSON result.

**Current behavior:**
- With `--output`: writes full JSON to file, prints one-line summary to **stderr**
- Without `--output`: dumps full JSON to **stdout** (this is what the skill reads in Step 2)

**Target behavior with `--summary`:**
```
python3 scripts/structural_validator.py --input file.csv --output reports/structural_results.json --summary
```
- Still writes full JSON to `--output` (Step 5 merge still needs it)
- Prints compact table to stdout/stderr that the AI reading the output consumes:
```
Market              Errors  Warnings  Info
------------------  ------  --------  ----
Germany (de)             0         1     0
Spain (es)               2         0     0
...
Total                    4         8     2
```

**Implementation location:** `main()` function, after `results = run_validation(...)`. The data already exists in `results['summary']['by_country']`.

**Flag design:**
```python
parser.add_argument('--summary', action='store_true',
    help='Print compact market/count table instead of full JSON to stdout')
```

### Pattern 3: Token Baseline Metric (TOK-03)

**What:** Before making any code changes, run a review against a real sample CSV and record the approximate context window token cost. After changes, run the same review and record the new cost.

**Baseline artifact:** `reports/token-baseline.md` — a short record containing:
- Reference file name
- Date of baseline run
- Approximate input + output token count (visible in Claude's API response metadata or estimated from output length)
- Description of what produced the tokens (Step 4c JSON arrays)

**Measurement method:** Claude Code displays token usage at the end of each message. Capture this before and after for the same sample file. Even an estimate (word count of JSON arrays × 1.3 tokens/word) is sufficient to demonstrate reduction.

### Anti-Patterns to Avoid

- **Removing the full JSON output entirely from Step 5 merge:** The full findings list is still needed for Step 5 and Step 6 — only the per-market inline echo during Step 4c is eliminated.
- **Making `--summary` replace `--output`:** The skill still needs the full JSON written to `reports/structural_results.json` for Step 2's merge. `--summary` is additive output control, not a replacement.
- **Breaking the Step 2 summary line:** Step 2 currently reads "Structural validation complete: [X] errors..." — this comes from stderr. Don't route the new summary to the same channel in a way that breaks parsing.
- **Adding pip dependencies:** The project explicitly requires stdlib only for the validator.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token counting | Custom token counter | Use word count × ~1.3 as estimate, or read Claude Code's displayed usage | Exact token counting requires tiktoken (external dep); estimates are sufficient for TOK-03 |
| Compact table formatting | Custom table renderer | Python f-string with ljust/rjust, or simple tab-separated output | The summary table is 3 columns — no library needed |

**Key insight:** Both changes are surgical edits to existing files. No new files, no new dependencies, no new abstractions.

---

## Common Pitfalls

### Pitfall 1: Breaking the Step 5 merge by removing JSON output too aggressively

**What goes wrong:** If the instruction change in Step 4c says "don't output JSON at all," the AI may not maintain the findings list in working memory across 39 markets. Long conversations cause context drift.

**Why it happens:** Claude skill instructions are interpreted, not compiled. An instruction to "accumulate silently" might be interpreted as "discard."

**How to avoid:** The revised Step 4c instruction must explicitly state that findings are accumulated into a named variable/list (e.g., "append to `ai_findings`") and that this list is used directly in Step 5. The progress indicator ("Reviewed X — N issues") confirms the market was processed.

**Warning signs:** Step 5 merge produces fewer findings than expected, or the report is missing markets that were reviewed.

### Pitfall 2: `--summary` flag outputs to wrong channel

**What goes wrong:** The compact summary goes to stderr while Step 2's instruction reads stdout, or vice versa, causing the AI to read an empty response.

**Why it happens:** The current code already sends one summary line to stderr when `--output` is set. If `--summary` also uses stderr, the existing "complete" line and the new table both appear on stderr but the skill instruction may be looking at stdout.

**How to avoid:** Decision: when `--summary` is used with `--output`, print the compact table to **stdout** (not stderr). This replaces the empty stdout with a readable summary. The existing one-line stderr message can remain as-is.

**Warning signs:** Step 2 says "Structural validation complete: 0 errors, 0 warnings" when there are known issues, or the AI can't find the summary table.

### Pitfall 3: Baseline measurement taken after partial changes

**What goes wrong:** TOK-03 baseline is measured after TOK-01 or TOK-02 is already applied, making the "before" number invalid.

**Why it happens:** Baseline establishment is Plan 01-01's second task, and implementation is its first — there's a temptation to do them in the same step.

**How to avoid:** Plan 01-01 must explicitly establish the baseline FIRST (on the current unmodified skill), THEN apply the TOK-01 changes. The baseline artifact must be committed before any skill edits.

### Pitfall 4: argparse `--summary` conflicts with existing flags

**What goes wrong:** `--summary` is passed alongside `--output` and the code tries to write both full JSON and compact output in a way that conflicts.

**Why it happens:** The current `main()` has a single output branch — no flag composition.

**How to avoid:** `--summary` is purely additive. Full logic: if `--output` → write JSON to file; if `--summary` → also print compact table to stdout; if neither → print full JSON to stdout (unchanged default).

---

## Code Examples

Verified patterns from the existing codebase:

### Existing argparse structure in structural_validator.py (lines 641–674)

The current `main()` already handles `--output` and `--pretty`. Adding `--summary` follows the same pattern:

```python
# Source: scripts/structural_validator.py lines 641-674
parser.add_argument('--summary', action='store_true',
    help='Print compact market/count table to stdout instead of full JSON')

# After run_validation():
if args.summary:
    by_country = results['summary'].get('by_country', {})
    header = f"{'Market':<30} {'Errors':>6} {'Warnings':>8} {'Info':>5}"
    print(header)
    print('-' * len(header))
    for country, counts in sorted(by_country.items()):
        print(f"{country:<30} {counts.get('errors', 0):>6} {counts.get('warnings', 0):>8} {counts.get('infos', 0):>5}")
    s = results['summary']
    print(f"{'TOTAL':<30} {s['errors']:>6} {s['warnings']:>8} {s['info']:>5}")
```

### `by_country` dict structure (already produced by run_validation())

```python
# Source: scripts/structural_validator.py lines 613-617
by_country = defaultdict(lambda: {'errors': 0, 'warnings': 0, 'infos': 0})
for issue in all_issues:
    severity_key = issue['severity'] + 's' if issue['severity'] != 'info' else 'infos'
    by_country[issue['country']][severity_key] += 1
```

The keys are `errors`, `warnings`, `infos` (note: `infos` not `info`). The summary-level key is `info` (singular). Don't confuse the two when rendering.

### Step 4c instruction structure (current, lines 76–95 of review-translations.md)

The critical instruction to change is:
```
For each market, evaluate the 7 criteria below and output a JSON array of issues before moving to the next.
```
And the closing:
```
After all markets are reviewed, merge all JSON arrays into a single flat list.
```

Target replacement pattern:
```
For each market, evaluate the 7 criteria below and append all issues to `ai_findings` (a running flat list).
Do NOT output JSON to the conversation. Instead, output one line per market:
"Reviewed [Country] ([lang]) — [N] issues found."

After all markets are reviewed, `ai_findings` is the AI findings set for Step 5.
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Print all intermediate results inline | Silent accumulation with progress indicators | Phase 1 (now) | Eliminates 5,000–30,000 tokens of JSON echo per review run |
| Full JSON to stdout for triage | `--summary` compact table | Phase 1 (now) | Reduces Step 2 context load from ~10KB JSON to ~40-line table |

**Deprecated/outdated after this phase:**
- Per-market inline JSON output in Step 4c: replaced by progress line + silent accumulation
- Running structural validator without `--summary` during triage: still valid for programmatic use, but `--summary` becomes the recommended human-facing invocation

---

## Open Questions

1. **Where exactly is the token cost incurred — input or output?**
   - What we know: Step 4c outputs JSON arrays; these appear in the conversation and are re-read as input on the next turn
   - What's unclear: Whether the dominant cost is output tokens (echoing JSON) or input tokens (re-reading it in Step 5)
   - Recommendation: The baseline metric should capture both input and output token counts separately if possible. Either way, the fix addresses both: less output from Step 4c = less input to Step 5.

2. **Should the progress indicator in Step 4c include a running total?**
   - What we know: "Reviewed X — N issues" is minimal but sufficient
   - What's unclear: Whether the user wants to see real-time signal during a long review
   - Recommendation: Keep the per-market line, add a final summary line: "AI review complete: [N] markets, [M] total issues." This replaces the old "merge all JSON arrays" confirmation.

3. **Should `--summary` be usable without `--output`?**
   - What we know: Without `--output`, the current default is full JSON to stdout
   - What's unclear: Whether any calling code depends on that stdout JSON when `--summary` is set
   - Recommendation: When `--summary` is given without `--output`, print the compact table to stdout. The full JSON is not written anywhere. This is a valid use case for quick human triage from the terminal.

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `scripts/structural_validator.py` — full 678-line read, all argparse/output logic confirmed
- Direct code inspection: `.claude/commands/review-translations.md` — full 249-line read, Step 4c instruction confirmed
- Direct document inspection: `.planning/REQUIREMENTS.md` — TOK-01/02/03 requirements read verbatim
- Direct document inspection: `.planning/ROADMAP.md` — plan breakdown confirmed (2 plans for Phase 1)

### Secondary (MEDIUM confidence)
- `CLAUDE.md` project instructions — confirms stdlib-only constraint for validator, two-tier model routing strategy
- `.planning/STATE.md` — confirms project phase and key file inventory

### Tertiary (LOW confidence)
- None — all findings are based on direct code inspection, no web research needed for this phase

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — stdlib only, confirmed by code inspection
- Architecture: HIGH — both change targets read in full, patterns are clear
- Pitfalls: HIGH — derived from direct code analysis, not speculation

**Research date:** 2026-04-08
**Valid until:** 2026-05-08 (stable codebase, no external dependencies)
