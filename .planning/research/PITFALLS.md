# Pitfalls Research

**Domain:** Adding Playwright BO scraping + Notion column write + Slack notifier to an existing stdlib-only Python review pipeline
**Researched:** 2026-04-29
**Confidence:** HIGH (auth/secrets, Notion MCP bugs), MEDIUM (selector brittleness, CSV coexistence), LOW (BO-specific selectors — unverifiable without BO access)

---

## Critical Pitfalls

### Pitfall 1: BO Session Cookie Committed to Git

**What goes wrong:**
Playwright's `storageState()` serializes all cookies, local storage, and IndexedDB to a JSON file. If `playwright/.auth/state.json` (or any equivalent) is not in `.gitignore` before it is first written, a git add -A or a careless commit captures the BO admin session — a live credential granting admin access to Superprof's notification back-office.

**Why it happens:**
Developers create the auth file during a spike ("just testing"), commit to see progress, then add .gitignore later. The file is already tracked by then, and git does not retroactively untrack it. The mistake is invisible until a git log or GitHub push exposes it.

**How to avoid:**
Add `playwright/.auth/` and any `*.storageState.json` pattern to `.gitignore` as the very first commit of the Playwright phase — before any auth code is written. Store the BO account password in macOS Keychain or a `.env` file that is also in `.gitignore`. Never store credentials in `config/` or any tracked directory.

**Warning signs:**
- `git status` shows a `.json` file inside `playwright/` or `scripts/` that contains `"cookies"` as a top-level key
- Any committed file whose contents include `"httpOnly": true` or `"sameSite"`

**Phase to address:**
Phase A (Playwright extraction) — first task, before any Playwright code is written. Non-negotiable gate.

---

### Pitfall 2: Playwright Breaks the "No pip Install" Contract

**What goes wrong:**
The core pipeline has a hard constraint: stdlib-only, no pip, zero setup beyond Python 3.x. Playwright requires `pip install playwright` and a separate `playwright install` step to download browser binaries (~300 MB per browser). If the Playwright scraper script is placed inside `scripts/` alongside `structural_validator.py`, a new reviewer following the README will run `python scripts/structural_validator.py` and get an ImportError they did not expect. The stdlib-only contract breaks silently for the new user.

**Why it happens:**
Both the old code and the new Playwright code live under `scripts/`. The README says "no pip install required." The new code is never tested by someone following only the README.

**How to avoid:**
Isolate the Playwright scraper in `scripts/scraper/` or `scripts/bo_scraper.py` and add a separate "Prerequisites for URL-driven mode" section to the README that is visually distinct from the existing "no pip install" section. The two modes (CSV-drop vs. URL-driven) have different setup requirements; document them as separate tracks. Verify during Phase A that the old review flow works with a clean Python environment (no playwright installed).

**Warning signs:**
- Playwright imports appear inside `structural_validator.py` or `scripts/review_runner.py`
- README does not mention `pip install playwright` anywhere despite URL-driven mode being live
- A test run with a fresh venv (no playwright) of the old CSV-drop flow throws ImportError

**Phase to address:**
Phase A (Playwright extraction) — isolate the scraper module at creation time. Phase B (CSV generation) — verify CSV-drop still works without playwright installed.

---

### Pitfall 3: BO Auth Is More Fragile Than It Looks

**What goes wrong:**
Three auth approaches are possible — (a) login script (Playwright fills the login form), (b) session cookie injection (copy a live browser cookie into storageState), (c) SSO/OAuth redirect. In every case, the session eventually expires. If the scraper has no explicit re-auth path, it silently returns a 200-status login page instead of the BO page, extracts nothing meaningful, and writes a blank or malformed CSV. The review pipeline then runs on garbage input with no error raised.

**Why it happens:**
Developers test the happy path (fresh session) during development but do not test what happens after cookie expiry. The BO likely uses short-lived session cookies (hours, not weeks) given it is an admin portal. A silent 200 redirect is the hardest failure to detect.

**How to avoid:**
After `page.goto(bo_url)`, assert that the resulting URL still contains an admin path (not a login redirect). Add a post-navigation check: if the page title or URL contains "login" or "sign-in", raise a clear error like `BOAuthExpiredError`. Store session state in a named file (`playwright/.auth/bo_session.json`) and surface its creation date at scrape time so Juan knows when to refresh it. Prefer the login script approach over manual cookie injection — it is automatable and self-renewing.

**Warning signs:**
- The scraper returns a CSV with one row and no language columns
- CSV is written with a filename derived from the BO page title, but the title is "Connexion — Superprof" or similar
- No assertion follows `page.goto()` to confirm landing on the admin page

**Phase to address:**
Phase A spike — auth is the highest-risk unknown; validate in a time-boxed spike before committing to the approach. Phase A proper — auth error detection as a required task.

---

### Pitfall 4: Selector Brittleness on a Live Admin UI

**What goes wrong:**
BO admin interfaces are internal tools with no stability guarantee. Class names, element IDs, and DOM structure change whenever the backend team ships a UI update. A Playwright scraper using CSS class selectors or positional selectors (`nth-child(3)`) breaks silently on the next deploy. The script still runs, but `locator.all_text_contents()` returns empty lists or wrong data. The generated CSV looks structurally valid but contains garbage content.

**Why it happens:**
Internal tools use generated class names (from CSS-in-JS, Tailwind purge, etc.) or position-based layouts that drift. There are no `data-testid` attributes on internal tools not built for automated testing.

**How to avoid:**
Use text-content selectors and ARIA role selectors as the primary strategy — these survive layout changes better than CSS classes. For example: `page.get_by_role("tab", name="Email")` is more stable than `page.locator(".tab-item:nth-child(1)")`. For the page information block, locate by heading text, not by container class. Add an explicit assertion that the expected number of language rows was extracted before writing any CSV — a partial extraction is worse than a failed extraction because it passes downstream validation.

**Warning signs:**
- Selectors are `.css-hash-xyz` style class names or positional (`nth-child`)
- No assertion on row count after extraction
- CSV appears to write successfully but has fewer language rows than expected

**Phase to address:**
Phase A (Playwright extraction) — selector strategy decided upfront. The spike LEARNINGS.md should document which selector approach proved stable on the actual BO page.

---

### Pitfall 5: Notion "task follow up" Column Write Fails Silently by Type Mismatch

**What goes wrong:**
The column named "task follow up" exists in the Reports DB but its type is unknown (could be `select`, `multi_select`, `rich_text`, `status`, or a custom type). Writing the wrong payload shape to a Notion property via MCP does not always raise a hard error — the MCP server has a confirmed bug (issue #153 on makenotion/notion-mcp-server) where `notion-update-page` silently fails to update database page properties due to a schema validation bug in the anyOf validator. The column appears unchanged, the run completes, and no one notices.

**Why it happens:**
The property type is not inspected before writing. The MCP abstraction hides the raw API response, so a 400 or silent no-op is swallowed. The existing Notion publish flow (Phase 5, v1.1) only writes the page title and body — it has never needed to set a typed property column, so this failure mode has never been hit before.

**How to avoid:**
Before Phase C (Notion wiring), use `mcp__notion__retrieve-database` (or equivalent) to inspect the Reports DB schema and record the exact type and allowed values of "task follow up" in the phase plan. Write the payload in the format the API requires for that specific type (select: `{name: "value"}`, rich_text: `[{text: {content: "value"}}]`, status: `{name: "value"}`). Add a post-write read-back assertion: after the MCP call, fetch the page and verify the property value matches what was written. If the MCP bug (issue #153) is still present, fall back to a direct HTTP PATCH to the Notion API using the standard `requests` library (or `urllib` to stay closer to stdlib intent).

**Warning signs:**
- MCP call returns success but the column in Notion is still blank
- No read-back verification step after the write
- The phase plan does not document the "task follow up" column type

**Phase to address:**
Phase C (Notion column wiring) — property discovery is the first task of the phase, before any write code is written.

---

### Pitfall 6: CSV-Drop Flow Breaks During Rollout

**What goes wrong:**
While the URL-driven path is being built, a code change in Phase A, B, or C inadvertently modifies the skill's Step 2 invocation of `structural_validator.py`, changes how CSVs are read from `samples/`, or edits shared config that the existing flow depends on. The CSV-drop path stops working. Juan runs a normal review during the rollout period, gets an unexpected error, and has no fallback. This is the highest user-impact risk of the entire v1.3 milestone.

**Why it happens:**
Shared code is modified without running the existing flow as a regression check. The skill definition is long (700+ lines); it is easy to edit the wrong section. Config files shared between the old and new path (e.g., `config/label_patterns.json`, `config/Variables.csv`) are modified for the URL-driven path without considering the existing path.

**How to avoid:**
The coexistence requirement ("CSV-drop flow stays live during rollout") must be encoded as an explicit acceptance criterion on every phase plan in v1.3 — not just a note in the backlog. After every code change that touches `scripts/`, `config/`, or `.claude/commands/review-translations.md`, run a smoke test of the CSV-drop path with a known-good CSV before merging. Keep the Playwright scraper in a separate script that does not share entry points with `structural_validator.py`.

**Warning signs:**
- A phase plan modifies `structural_validator.py` without a smoke test checkpoint
- `review-translations.md` skill is edited in the Step 1–6 sections while URL-driven work is in progress
- `config/label_patterns.json` or `Variables.csv` is changed without verifying the existing flow

**Phase to address:**
All phases (A through D) — coexistence check is a gate on every phase's VERIFY.md.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcoding BO selectors as CSS class strings | Fast to write during spike | Breaks on any BO UI deploy; invisible failure | Never for production code; acceptable in a spike LEARNINGS.md with explicit warning |
| Manual cookie copy-paste into storageState file | Avoids writing a login script | Expires daily/weekly; requires Juan to manually refresh; becomes a forgotten manual step | Only during initial spike to prove the scraping concept; must be replaced by login script before Phase A merges |
| Single Slack webhook URL hardcoded in skill | No secrets management needed for a one-channel notifier | URL is a credential; anyone with repo access can spam the channel; rotation requires code changes | Acceptable if URL is stored in `.env` (not tracked) and the webhook is for an internal team channel; never acceptable in a tracked config file |
| Skipping post-write Notion read-back check | Simpler code | Notion MCP has a confirmed silent-fail bug on property updates; error is invisible without verification | Never acceptable given the confirmed MCP bug |
| Using `networkidle` wait strategy for all tabs | Easy default | Slow for pages with long-polling or websocket traffic; can cause 30s+ hangs | Use only as a fallback; prefer `wait_for_selector` on a known stable element |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Playwright + BO auth | Using `page.wait_for_load_state('networkidle')` globally — admin portals with live-update panels never reach networkidle | Use `page.wait_for_selector(known_stable_element)` after navigation; only use networkidle for static pages |
| Playwright + email/SMS tabs | Clicking a tab and immediately calling `.all_text_contents()` before the tab's content has mounted | After clicking a tab, use `page.wait_for_selector` on a cell in the translation table before extracting; assert row count > 0 |
| Notion MCP + property update | Assuming the MCP `notion-update-page` tool works correctly for database page properties | Known bug: use direct HTTP PATCH via `urllib.request` if MCP fails silently; always read-back the value after writing |
| Notion MCP + API version | Using old API tool names after the 2025-09-03 API migration that introduced data_source_id | Confirm current MCP server version before Phase C; check if `database_id` alone is still sufficient or if `data_source_id` is now required |
| Slack webhook | Storing the webhook URL in a tracked config file | Store in `.env` (gitignored); reference via `os.environ.get('SLACK_WEBHOOK_URL')` |
| Slack webhook + private channel | Using an incoming webhook for a private channel without confirming the webhook was created for that channel | Incoming webhooks are channel-specific at creation time; verify the target channel during Phase D setup, not at send time |
| Playwright storageState | Not adding `playwright/.auth/` to `.gitignore` before the first auth script run | Add to `.gitignore` before writing any auth code; verify with `git check-ignore -v playwright/.auth/state.json` |
| Playwright + pip constraint | Importing `playwright` anywhere in files that `structural_validator.py` might transitively import | Keep the scraper as a fully isolated script; no shared imports with the stdlib core |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Launching a new Playwright browser context per scrape call | Each run takes 10–15 seconds just for browser startup; memory spikes | Reuse a single browser context per run; close it explicitly at the end | From the first run — latency is noticeable immediately |
| Downloading all browser engines (Chromium + Firefox + WebKit) | `playwright install` downloads ~900 MB; blocks first-run on slow connections | Use `playwright install chromium` — Chromium is sufficient for a logged-in internal admin portal | First setup on any machine |
| `wait_for_load_state('networkidle')` on a live-update admin panel | Script hangs for 30 seconds then times out | Use selector-based waits instead | Any BO page with polling or websocket activity |
| Writing the CSV to `samples/` before the extraction assertion | Partial CSV silently enters the pipeline | Assert row count and required columns before writing; use a temp file and rename on success | When the BO page partially renders before a timeout |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Committing `playwright/.auth/state.json` | Live BO admin session leaked to anyone with repo access; session valid for hours or days | Add `playwright/.auth/` to `.gitignore` as the very first commit of Phase A |
| Storing Slack webhook URL in `config/` or skill definition | Anyone with repo access can spam the Slack channel | Store in `.env` (gitignored); document the variable name in README, not the value |
| Storing BO password or login credentials in any tracked file | BO admin access compromised | Use macOS Keychain or `.env`; add `*.env` and `.env` to `.gitignore` |
| Using the existing Notion integration token for Playwright BO auth | Unrelated credential; creates confusion about what each token does | BO auth is a separate credential; keep them isolated |
| Not rotating the storageState after BO password changes | Stale session stops working; no clear error message | Document session refresh procedure in README; surface session file creation date in scraper output |

---

## "Looks Done But Isn't" Checklist

- [ ] **Playwright auth:** The script logs in successfully in isolation — verify it still works when called from the full pipeline (not just standalone), including when `playwright/.auth/` is pre-populated from a previous run
- [ ] **CSV coexistence:** The new URL-driven path writes CSVs to `samples/` — verify the existing `/review-translations samples/file.csv` flow still works on those CSVs without any extra flags
- [ ] **Notion column write:** The MCP call returns without error — verify by reading the page back and asserting the "task follow up" column value is non-empty and matches what was written
- [ ] **Slack notification:** The webhook returns 200 — verify the message actually appears in the correct channel (not a stale test channel), with the correct notification name
- [ ] **BO extraction completeness:** The scraper exits without error — verify the CSV contains the expected number of language rows (compare against a known baseline), not just a structurally valid but partial file
- [ ] **Email vs SMS tabs:** The email tab CSV is written — verify the SMS tab is also scraped as a separate CSV when SMS content exists; the pipeline should handle both, not silently skip SMS
- [ ] **Secrets in `.gitignore`:** `playwright/.auth/`, `.env`, and any `*.storageState.json` are in `.gitignore` — verify with `git check-ignore -v` before the first auth-touching commit

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| BO session cookie committed to git | HIGH | Immediately rotate the BO account password (invalidates committed session); run `git filter-repo` or BFG to purge the file from history; add to `.gitignore` and verify |
| Slack webhook URL committed to git | MEDIUM | Delete the webhook in Slack app settings (URL becomes invalid); create a new webhook; update `.env` |
| Notion column write silently failing | LOW | Inspect the column type via `mcp__notion__retrieve-database`; rewrite the payload in the correct format; re-run the Notion publish step manually |
| CSV-drop flow broken mid-rollout | MEDIUM | Roll back the specific commit that broke the flow (git revert); run the existing CSV-drop flow as a smoke test on the reverted state; re-apply the URL-driven change with the regression fixed |
| Playwright selectors broken after BO deploy | MEDIUM | Update selectors in the scraper script using text/role strategy; run a manual scrape to verify the new selectors; no changes to the core review pipeline needed |
| BO auth expired, scrape returns login page | LOW | Refresh `playwright/.auth/bo_session.json` by running the login script manually; re-run the scraper |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| BO session cookie committed to git | Phase A — first commit | `git check-ignore -v playwright/.auth/state.json` passes before any auth code is written |
| Playwright breaks stdlib-only contract | Phase A (isolation) + Phase B (regression check) | `python scripts/structural_validator.py --help` succeeds in a fresh venv with no playwright installed |
| BO auth fragility / silent login redirect | Phase A spike (auth approach) + Phase A proper (error detection) | Scraper raises `BOAuthExpiredError` when session is manually invalidated before running |
| Selector brittleness | Phase A spike (selector strategy documented in LEARNINGS.md) + Phase A proper | Row count assertion fires correctly when extraction is intentionally interrupted mid-page |
| Notion column type mismatch / MCP silent fail | Phase C — first task is property type discovery | Post-write read-back of "task follow up" column returns the expected value |
| CSV-drop flow breaks during rollout | All phases A–D | Smoke test with a known-good CSV passes after every phase's code changes |
| Slack webhook URL leaked | Phase D — setup | `git check-ignore -v .env` passes; webhook URL absent from all tracked files |
| Partial CSV entering the pipeline | Phase A (extraction) + Phase B (CSV write gate) | Assert on row count before any CSV write; partial extraction raises an error, not a warning |

---

## Sources

- [Playwright official auth docs](https://playwright.dev/docs/auth) — storageState, .gitignore recommendation
- [Playwright Python auth docs](https://playwright.dev/python/docs/auth) — Python-specific storageState API
- [BrowserStack: Playwright storageState](https://www.browserstack.com/guide/playwright-storage-state) — cookie expiry and re-auth
- [Checkly: Authentication in Playwright](https://www.checklyhq.com/docs/learn/playwright/authentication/) — session refresh patterns
- [BrowserStack: Playwright selectors best practices](https://www.browserstack.com/guide/playwright-selectors-best-practices) — role/text selectors vs class selectors
- [makenotion/notion-mcp-server issue #153](https://github.com/makenotion/notion-mcp-server/issues/153) — confirmed critical bug: `notion-update-page` silently fails on database page property updates
- [makenotion/notion-mcp-server issue #67](https://github.com/makenotion/notion-mcp-server/issues/67) — body object parsed as string bug
- [Notion API upgrade guide 2025-09-03](https://developers.notion.com/docs/upgrade-guide-2025-09-03) — data_source_id requirement, breaking changes
- [Slack: Sending messages using incoming webhooks](https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/) — webhook channel lock-in, rate limits
- [Knock: channel_not_found in Slack webhooks](https://knock.app/blog/troubleshooting-channel-not-found-in-slack-incoming-webhooks) — private channel membership requirement
- [Playwright Python installation](https://playwright.dev/python/docs/intro) — pip + browser binary requirements
- [NareshIT: Secure Playwright authentication](https://nareshit.com/blogs/handling-authentication-in-playwright-securely) — token management, .env approach
- Project context: `.planning/PROJECT.md`, `.planning/STRATEGIC-OVERVIEW.md`, `.planning/ROADMAP.md` (Backlog 999.1), `.planning/MILESTONES.md`, `CLAUDE.md`

---
*Pitfalls research for: v1.3 End-to-End Review Automation (Playwright BO scraping + Notion column write + Slack notifier)*
*Researched: 2026-04-29*
