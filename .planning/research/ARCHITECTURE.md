# Architecture Research

**Domain:** Claude-skill-orchestrated translation review tool — adding URL ingestion + Slack output
**Researched:** 2026-04-29
**Confidence:** HIGH

---

## Standard Architecture

### System Overview

The existing system is a single-skill orchestrator. v1.3 adds two entry-point modes (URL and CSV-drop)
that converge at the same pipeline, and two new output channels (Notion "task follow up" column + Slack).

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Entry Points                                │
│                                                                     │
│   [URL mode]                           [CSV-drop mode — unchanged]  │
│   User pastes BO admin URL             User drops CSV / attaches    │
│         │                                         │                 │
│         ▼                                         │                 │
│  scripts/extract_bo_page.py                       │                 │
│  (Playwright — NEW)                               │                 │
│  Auth: .playwright/auth/bo_state.json             │                 │
│         │                                         │                 │
│         │  emits named CSV(s) → samples/          │                 │
│         └──────────────────┬──────────────────────┘                 │
│                            │                                        │
│              CONVERGENCE POINT: samples/[name].csv                  │
└────────────────────────────┼────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│               Existing Review Pipeline (UNCHANGED)                  │
│                                                                     │
│  .claude/commands/review-translations.md                            │
│  Step 0: Parse args / detect mode                                   │
│  Step 1: Health check + CSV parse + notification ID extraction      │
│  Step 2: scripts/structural_validator.py                            │
│  Step 3: Load learned rules (corrections/rules_summary.json)        │
│  Step 4: AI review (Haiku Tier 2 / Sonnet Tier 1)                   │
│  Step 5: Merge structural + AI findings                             │
│  Step 6: Generate .md report + Notion publish                       │
│           └─ EXTENDED: write "task follow up" column (NEW)          │
│  Step 7: Feedback loop                                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                       Output Channels                               │
│                                                                     │
│  reports/review-[id]-YYYY-MM-DD.md  (existing, unchanged)           │
│  Notion Reports DB page             (existing + task follow up NEW) │
│  Slack group channel message        (NEW — post-publish)            │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Component Responsibilities

| Component | Responsibility | Status |
|-----------|---------------|--------|
| `.claude/commands/review-translations.md` | Orchestrates the entire review from entry to output. Detects URL vs CSV mode in Step 0. | Existing — modify Step 0 and Step 6 |
| `scripts/extract_bo_page.py` | Playwright script: opens BO URL with persisted auth, navigates email/SMS tabs, extracts translation grids, writes named CSV(s) to `samples/` | New file |
| `.playwright/auth/bo_state.json` | Persisted Playwright storage state (cookies + localStorage). Created once by a one-time login script. Reloaded on every extraction run. | New (gitignored) |
| `scripts/_setup_bo_auth.py` | One-time interactive login script: launches headed Playwright, user logs in manually, saves context to `.playwright/auth/bo_state.json`. Never called from the review skill. | New file (run once by hand) |
| `scripts/structural_validator.py` | Deterministic structural checks on the CSV. Entry point: `python3 scripts/structural_validator.py --input ... --output ...` | Existing — no changes needed |
| `scripts/_build_report.py` | Report building helper called from skill. | Existing — no changes needed |
| `scripts/_prep_notion.py` | Notion payload prep helper. | Existing — may need minor extension for task-follow-up column |
| `corrections/corrections_log.json` | Learning system. | Existing — no changes |
| Notion MCP (`mcp__claude_ai_Notion__*`) | Publishes report page to Reports DB. Step 6 of skill calls this already. v1.3 adds writing the "task follow up" property on the same `notion-create-pages` call. | Existing — Step 6 property payload extended |
| `scripts/_notify_slack.py` | Minimal stdlib `urllib.request` POST to a Slack incoming webhook URL. Called from skill at the end of Step 6, after Notion publish. | New file |

---

## Recommended Project Structure Changes

Only additions and modifications — everything else stays exactly as-is.

```
product-quality-review-automation/
├── .claude/
│   └── commands/
│       └── review-translations.md        # MODIFY: Step 0 (URL mode detection) + Step 6 (task follow up + Slack)
├── .playwright/
│   └── auth/
│       └── bo_state.json                 # NEW (gitignored) — persisted Playwright session
├── config/
│   └── v1.3.json                         # NEW — Slack webhook URL, BO base URL, selectors (env-level config)
├── scripts/
│   ├── structural_validator.py           # UNCHANGED
│   ├── _build_report.py                  # UNCHANGED
│   ├── _prep_notion.py                   # UNCHANGED (or trivial extension)
│   ├── extract_bo_page.py                # NEW — Playwright extraction entrypoint
│   ├── _setup_bo_auth.py                 # NEW — one-time interactive auth setup
│   └── _notify_slack.py                  # NEW — Slack POST via stdlib urllib
├── samples/                              # UNCHANGED — extraction deposits CSVs here
├── reports/                              # UNCHANGED
├── corrections/                          # UNCHANGED
└── .gitignore                            # MODIFY: add .playwright/auth/
```

### Structure Rationale

- **`scripts/extract_bo_page.py`** is a sibling of `structural_validator.py`, not inside a sub-package. Consistent with the project's flat `scripts/` convention (functional style, no classes, snake_case).
- **`scripts/_setup_bo_auth.py`** uses the `_` prefix (private-helper convention already established by `_build_report.py`, `_prep_notion.py`). It is never called from the skill — it is a human-run setup tool.
- **`.playwright/auth/bo_state.json`** lives in `.playwright/` (mirroring the Playwright community convention of keeping auth state in a dedicated directory) rather than in `config/` because it contains session secrets, not domain config. Must be gitignored.
- **`config/v1.3.json`** holds the BO base URL, Playwright selectors, and Slack webhook URL. Keeping secrets (webhook URL) in config rather than hardcoded makes rotation easy. Alternatively this can be a comment in `CLAUDE.md` and read at runtime — decided in the discuss-phase.
- **`scripts/_notify_slack.py`** is stdlib-only (`urllib.request` + `json`). Preserves the "no pip install" constraint. A Slack incoming webhook POST is a simple HTTPS JSON call — no SDK needed.

---

## Architectural Patterns

### Pattern 1: Parallel Entry Points Converging at the CSV Boundary

**What:** Two distinct entry paths (URL extraction and CSV-drop) produce the same artifact — a named `.csv` file in `samples/` — before the pipeline sees them. The skill's Step 0 determines which path to take, then rejoins at Step 1 once the CSV exists on disk.

**When to use:** Any time a new input source must be added without modifying downstream logic. The CSV is the contract between extraction and review.

**Trade-offs:** CSV writing is a side effect with a real file on disk (not an in-memory handoff). This is intentional: it lets the user inspect the extracted data before the review runs, and it means the CSV-drop path is not special-cased — it is just the path where the extraction step already happened.

```
Step 0 of review-translations.md:

IF arg matches https:// (URL mode):
  → call extract_bo_page.py [url]
  → await CSV path returned to stdout
  → use that path as [CSV_PATH] for Step 1
ELSE (CSV mode — existing logic):
  → resolve CSV path as before (file path, samples/ lookup, attachment)

→ Step 1 onward: identical for both modes
```

### Pattern 2: Playwright Storage State for BO Auth

**What:** Playwright's `browser_context.storage_state(path=...)` captures cookies + localStorage to a JSON file after an interactive login. Subsequent headless runs load that file via `browser.new_context(storage_state=...)`. No credentials are stored in code.

**When to use:** Any web app using session cookie auth (which the Superprof BO admin does). This is Playwright's documented "reuse signed-in state" pattern.

**Trade-offs:**
- State file expires when the BO session expires (typically days to weeks). When it does, `extract_bo_page.py` will land on the login page instead of the target. The script must detect this (check if the current URL contains `/login` after navigation) and exit with a clear error: `BO session expired — rerun _setup_bo_auth.py`.
- The state file contains live session cookies. It must never be committed (`gitignore` it). This is documented as a hard requirement by Playwright.

```python
# _setup_bo_auth.py (one-time, run manually)
from playwright.sync_api import sync_playwright
import json, pathlib

STATE_PATH = pathlib.Path(".playwright/auth/bo_state.json")
STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto("https://admin.superprof.fr/...")  # BO login URL from config
    input("Log in manually, then press Enter to save session...")
    ctx.storage_state(path=str(STATE_PATH))
    browser.close()
print(f"Session saved to {STATE_PATH}")
```

```python
# extract_bo_page.py (called from skill via Bash)
from playwright.sync_api import sync_playwright

STATE_PATH = ".playwright/auth/bo_state.json"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=STATE_PATH)
    page = ctx.new_page()
    page.goto(url)
    # Check for redirect to login
    if "/login" in page.url:
        print("ERROR: BO session expired — rerun scripts/_setup_bo_auth.py", file=sys.stderr)
        sys.exit(1)
    # ... extract grids, write CSVs ...
```

### Pattern 3: Stdlib-Only Slack Notification

**What:** A single-function module posts a JSON payload to a Slack incoming webhook URL using `urllib.request`. No `requests`, no `slack_sdk`. Called from the skill via Bash after the Notion publish step.

**When to use:** When the "no pip install" constraint must be maintained. Slack incoming webhooks accept a plain HTTPS POST with `{"text": "..."}` — no authentication header needed beyond the secret embedded in the webhook URL.

**Trade-offs:** No retry logic by default (can be added with a simple loop). Webhook URL is a secret — store in `config/v1.3.json` or as an environment variable, never hardcoded in the script.

```python
# scripts/_notify_slack.py
#!/usr/bin/env python3
"""Post a completion notification to Slack. Stdlib only."""
import json, sys, urllib.request

def notify(webhook_url: str, message: str) -> None:
    payload = json.dumps({"text": message}).encode()
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Slack returned {resp.status}")

if __name__ == "__main__":
    # Called as: python3 scripts/_notify_slack.py "<webhook_url>" "<message>"
    notify(sys.argv[1], sys.argv[2])
```

---

## Data Flow

### URL Mode Flow (New Path)

```
User: /review-translations https://admin.superprof.fr/notifications/123/edit
         │
         ▼ (Step 0 — URL detected)
review-translations.md
         │
         ▼ Bash call
scripts/extract_bo_page.py <url>
         │  Playwright opens URL with .playwright/auth/bo_state.json
         │  Extracts "Email" tab grid → samples/[name]_email.csv
         │  Extracts "SMS" tab grid  → samples/[name]_sms.csv   (if SMS tab exists)
         │  Prints CSV path(s) to stdout
         │
         ▼ Step 0 receives path(s)
[CSV_PATH] = samples/[name]_email.csv   (or user-selected if both)
         │
         ▼ Step 1 onward — IDENTICAL to CSV-drop mode
```

### CSV-Drop Mode Flow (Unchanged)

```
User: /review-translations samples/relance_3.csv
         │
         ▼ (Step 0 — file path detected, no extraction)
[CSV_PATH] = samples/relance_3.csv
         │
         ▼ Step 1 onward — identical
```

### Notion Task Follow-Up Write (Modified Step 6)

```
Step 6: Generate .md report
         │
         ▼
Step 6b: Adapt for Notion
         │
         ▼
Step 6c: notion-create-pages call — EXTENDED payload:
  {
    "properties": {
      "Name": "Translation Review — [notification_id] — YYYY-MM-DD",
      "task follow up": "[notification_id]"   ← NEW property
    },
    "content": "..."
  }
         │
         ▼
Step 6d: Capture result → announce URL
         │
         ▼ NEW: Post-publish step
scripts/_notify_slack.py <webhook_url> "Review complete: [notification_id] — [notion_url]"
```

### Auth Setup Flow (One-Time, Manual)

```
Developer (once):
  python3 scripts/_setup_bo_auth.py
    → Chromium opens (headed)
    → Developer logs into BO manually
    → Presses Enter
    → .playwright/auth/bo_state.json written
    → Done until session expires
```

---

## Integration Points

### External Services

| Service | Integration Pattern | Auth | Notes |
|---------|---------------------|------|-------|
| Superprof BO Admin | Playwright headless browser with `storage_state` session reuse | Session cookie in `.playwright/auth/bo_state.json` | Must detect session expiry and fail-fast with actionable message |
| Notion Reports DB | Existing Notion MCP (`mcp__claude_ai_Notion__notion-create-pages`) | MCP OAuth (already configured) | Extend `properties` payload to add "task follow up" property — property type (text/select/relation) must be confirmed in discuss-phase |
| Slack group channel | Outbound HTTPS POST to incoming webhook URL | Secret embedded in webhook URL | Soft-fail: if Slack POST fails, log warning but do not abort the review session |

### Internal Boundaries

| Boundary | Communication | Contract |
|----------|---------------|----------|
| `extract_bo_page.py` → skill | Script writes CSVs to `samples/`, prints absolute path(s) to stdout, exits 0 on success / non-zero on error | Skill reads stdout line(s) as CSV path(s) |
| `_notify_slack.py` → skill | Called via Bash with webhook URL + message string as CLI args, exits 0 on success | Skill treats non-zero exit as soft failure (logs, does not abort) |
| Notion MCP → skill | Existing MCP tool call pattern — already in place. Only the `properties` object changes. | `"task follow up"` property value = `notification_id` string |
| `_setup_bo_auth.py` → `extract_bo_page.py` | Shared file path `.playwright/auth/bo_state.json` | If file is absent, `extract_bo_page.py` exits with: `BO auth file missing — run scripts/_setup_bo_auth.py first` |

---

## New vs. Modified Components (Explicit List)

### New Files

| File | Type | Purpose |
|------|------|---------|
| `scripts/extract_bo_page.py` | New script | Playwright extraction — URL to CSV(s) |
| `scripts/_setup_bo_auth.py` | New script (run manually) | One-time interactive auth setup |
| `scripts/_notify_slack.py` | New script | Stdlib Slack webhook notifier |
| `.playwright/auth/bo_state.json` | New artifact (gitignored) | Persisted Playwright session state |
| `config/v1.3.json` | New config | BO base URL, Playwright selectors, Slack webhook URL |

### Modified Files

| File | What Changes |
|------|-------------|
| `.claude/commands/review-translations.md` | Step 0: add URL mode detection + extraction call. Step 6c: extend `properties` payload for "task follow up". Step 6d: add Slack notification call. |
| `.gitignore` | Add `.playwright/auth/` |
| `CLAUDE.md` | Add v1.3 entry points, auth setup instructions, Slack config pointer |

### Unchanged Files (Explicit)

| File | Reason Not Touched |
|------|-------------------|
| `scripts/structural_validator.py` | CSV is the convergence point — validator sees no difference between URL-extracted and manually-dropped CSVs |
| `scripts/_build_report.py` | Report building is downstream of CSV — no changes |
| `scripts/_prep_notion.py` | If Notion page property extension is done inline in the skill (most likely), this helper is untouched |
| All `config/*.json` / `config/*.md` | Domain rules unchanged |
| `corrections/` | Learning system unchanged |

---

## Build Order (Respects CSV-Drop Coexistence)

The constraint is: at no point during v1.3 rollout should the existing CSV-drop flow break. This means the extraction path is fully additive — it is built alongside the existing pipeline without touching it until the final integration step.

### Phase A — Playwright Extraction (URL → CSV on disk)

Build and test `extract_bo_page.py` in complete isolation. Output is just CSVs in `samples/`. The skill is NOT modified at all in this phase.

Deliverables:
- `scripts/_setup_bo_auth.py` — run once, document result
- `.playwright/auth/bo_state.json` — confirmed working
- `scripts/extract_bo_page.py` — URL → CSV(s), tested manually by running `python3 scripts/extract_bo_page.py <url>` and inspecting `samples/`
- `.gitignore` updated

Coexistence status: CSV-drop works exactly as before. URL path is buildable and testable without touching the skill.

### Phase B — Skill Integration (URL Mode in Step 0)

Add URL mode detection to Step 0 of `review-translations.md`. When a URL is detected, call `extract_bo_page.py` via Bash, receive CSV path(s), then hand off to Step 1.

Deliverables:
- `.claude/commands/review-translations.md` Step 0 extended
- End-to-end test: paste BO URL → skill extracts CSV → reviews it → generates report (same output as if CSV was manually dropped)

Coexistence status: CSV-drop path is structurally unchanged in Step 0 (existing resolution logic is now the `else` branch). Both modes produce `[CSV_PATH]` and proceed identically from Step 1.

### Phase C — Notion Task Follow-Up Column

Extend Step 6c to include the "task follow up" property in the `notion-create-pages` call. Requires confirming the Notion column type in the discuss-phase (text vs. select vs. rich_text).

Deliverables:
- `review-translations.md` Step 6c properties payload extended
- Notion DB page verified to show the column populated after a test run

Coexistence status: Notion publish was already optional (soft-fail). This change only adds a property — it does not alter report generation or the CSV-drop flow.

### Phase D — Slack Completion Notifier

Add `scripts/_notify_slack.py` and wire it into Step 6d. Called after the Notion publish announcement. Soft-fail: if the webhook call fails, log and continue.

Deliverables:
- `scripts/_notify_slack.py`
- `config/v1.3.json` (or equivalent config location) with webhook URL
- Step 6d Bash call added
- Test run confirms Slack message arrives in the group channel

Coexistence status: fully additive. Slack notification is a post-publish side effect that does not touch any existing review logic.

---

## Anti-Patterns

### Anti-Pattern 1: Modifying the Skill Before the Extractor Is Proven

**What people do:** Add URL mode to Step 0 in the same commit that adds `extract_bo_page.py`, before Playwright extraction has been validated end-to-end.

**Why it's wrong:** If the extraction fails (wrong selectors, session issues), Step 0 now errors on URL input but also risks breaking the developer's mental model of when CSV-drop works. The coexistence constraint is harder to hold when both changes land together.

**Do this instead:** Build Phase A entirely before touching the skill. The CSV-drop flow never sees Phase A work. Only after extraction is proven (CSVs in `samples/` look correct) does Phase B modify Step 0.

### Anti-Pattern 2: Committing `.playwright/auth/bo_state.json`

**What people do:** Add the state file to git (it's auto-generated, easy to forget to exclude).

**Why it's wrong:** The file contains live session cookies that can impersonate a logged-in BO admin. Playwright's own documentation flags this as a security risk.

**Do this instead:** Add `.playwright/auth/` to `.gitignore` in Phase A before the file is ever created. Document that every developer must run `_setup_bo_auth.py` once locally.

### Anti-Pattern 3: Hard-Failing on Slack or Notion Errors

**What people do:** Let a Slack POST failure or Notion publish failure abort the skill with an exception.

**Why it's wrong:** The review and report are the primary deliverables. A transient Slack or Notion error should never lose the review results. The existing skill already soft-fails on Notion (`⚠️ Notion publish failed ... Report saved locally`). Slack must follow the same pattern.

**Do this instead:** Both Slack and Notion calls are post-report-generation side effects. Wrap both in try/soft-fail blocks. The `.md` file on disk is always the canonical deliverable.

### Anti-Pattern 4: Bypassing the CSV Boundary (Passing Raw Scraped Data Directly to the Validator)

**What people do:** Have `extract_bo_page.py` return parsed data structures in memory (or stdout JSON) and have the skill feed that directly to the structural validator, skipping CSV writing.

**Why it's wrong:** It creates a separate code path for URL-mode data through the structural validator, requiring the validator to accept a new input format. The CSV boundary is the convergence point precisely to avoid this. It also removes the user's ability to inspect extracted data before the review.

**Do this instead:** `extract_bo_page.py` always writes to `samples/[name].csv`. The path it prints to stdout is what Step 0 uses as `[CSV_PATH]`. The validator and all downstream steps see zero difference.

---

## Scaling Considerations

This tool runs on one person's laptop for one team. Scaling is not a relevant concern for v1.3. The one relevant resource constraint is Playwright memory: launching a headed Chromium instance takes ~150 MB RAM. Running headless reduces this to ~80 MB. The `extract_bo_page.py` script must always use `headless=True` (except `_setup_bo_auth.py` which needs headed mode for manual login). Both scripts close the browser context after extraction.

---

## Sources

- [Playwright Python Authentication docs](https://playwright.dev/python/docs/auth) — storage_state pattern, MEDIUM confidence (verified against official docs)
- [Playwright Python BrowserContext API](https://playwright.dev/python/docs/api/class-browsercontext) — `storage_state()` method, MEDIUM confidence
- [Slack Incoming Webhooks Python SDK](https://slack.dev/python-slack-sdk/webhook/index.html) — stdlib alternative confirmed viable via websearch
- Existing skill definition: `.claude/commands/review-translations.md` — HIGH confidence (primary source)
- Existing project structure: `.planning/codebase/STRUCTURE.md` — HIGH confidence (primary source)
- Backlog 999.1 confirmed decisions: `.planning/ROADMAP.md` — HIGH confidence (primary source)

---

*Architecture research for: v1.3 End-to-End Review Automation — URL ingestion + Slack output*
*Researched: 2026-04-29*
