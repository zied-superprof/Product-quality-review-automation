# Phase 5: Notion Publishing — Research

**Researched:** 2026-04-09
**Domain:** Notion MCP integration, Notion-flavored Markdown, skill modification
**Confidence:** HIGH (core technical approach), MEDIUM (exact MCP tool signature)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** Pages published as sub-pages under parent page `33dd6418695a8097998fcf373ed18bf5` (Reports hub, superprof workspace)
**D-02:** New sub-page per review run — no overwrite of existing pages
**D-03:** Publishing happens after Step 6 (report written to disk), before Step 7 feedback prompt
**D-04:** .md file written to `reports/` first (local backup), then Notion publish runs
**D-05:** Title format: `Translation Review — [notification_id] — [YYYY-MM-DD]` (sanitized ID from Step 1)
**D-06:** Native Notion blocks — not a markdown dump
  - H2 headers → `heading_2` blocks
  - Tables → `table` blocks
  - Bullets → `bulleted_list_item` blocks
  - Bold text → `rich_text` with `bold: true`
  - Template variables (`@TPL_*@`) → `code` inline spans
  - Horizontal rules (`---`) → `divider` blocks
**D-07:** `--format` flag default changes from `html` to `md`; HTML no longer valid option
**D-08:** `--format pdf` still generates .html as intermediate (not announced)
**D-09:** Step 6 output announcement: .md path + Notion page URL (success), or .md path only (failure)
**D-10:** Notion publish failure is soft warn — do NOT abort
**D-11:** On failure: `Warning: Notion publish failed: [error]. Report saved locally: reports/[filename].md`
**D-12:** After warning, continue directly to Step 7

### Claude's Discretion

- Exact block-by-block parsing logic for the report markdown
- How to handle French body text containing HTML markup (`<strong>`, `<TPL_LOOP_ANNONCES>`) — wrap in `code` block or `rich_text` as appropriate
- Whether grouped market sections use `heading_2` or `heading_3` (choose whichever renders cleanest)

### Deferred Ideas (OUT OF SCOPE)

- Updating the Notion page after Step 7 feedback is captured
- Notion comments → corrections import
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NTIO-01 | Report is automatically published to Notion upon completion — no extra command or user confirmation required | MCP tool call embedded in Step 6 completion block; no user prompt needed |
| NTIO-02 | The Notion page mirrors the .md report structure — all markets, same section order, same content | Enhanced markdown format passes .md content to MCP; section order preserved |
| NTIO-03 | Notion page title includes notification ID and review date | Title format `Translation Review — [id] — [YYYY-MM-DD]` constructed from Step 1 ID + today's date |
| NTIO-04 | HTML output format removed; .md file retained on disk as local backup | Remove html write block from Step 6; remove `html` from `--format` valid options in Step 0 |
</phase_requirements>

---

## Summary

Phase 5 requires two code changes to `review-translations.md`: (1) add a Notion publish block at the end of Step 6, and (2) update the `--format` flag in Step 0. No new scripts, no new config files.

The key technical finding is that the MCP tool `mcp__claude_ai_Notion__notion-create-pages` accepts **Notion-flavored Markdown as a string** — not raw JSON block arrays. This aligns the implementation approach with the existing .md report: the skill passes its .md content (minimally adapted) directly as the page body. Block-by-block JSON construction is not required.

The report structure for the largest real-world run (87 markets, 563 lines, ~42KB) is well within all Notion API limits. The 2000-character rich_text limit and 100-block-per-call JSON limit are irrelevant when using the markdown endpoint. Template variables (`@TPL_*@`) and HTML-like tags (`[TITRE]`, `[BOUTON]`) must be wrapped in backtick code spans to prevent Notion from mangling them.

**Primary recommendation:** Use `mcp__claude_ai_Notion__notion-create-pages` with the `page_content` parameter set to the full .md report content (adapted for Notion-flavored Markdown escaping), plus `title` and `parent_page_id` string parameters. Do not pass a JSON `children` array.

---

## Standard Stack

### Core
| Tool | Type | Purpose | Why Standard |
|------|------|---------|--------------|
| `mcp__claude_ai_Notion__notion-create-pages` | MCP tool | Create Notion page with content | Already configured, tested 2026-04-09, pre-approved in settings.json |
| `mcp__claude_ai_Notion__notion-fetch` | MCP tool | Verify parent page exists (optional) | Pre-approved, available for pre-flight check |

### No New Libraries Needed
The implementation lives entirely inside `review-translations.md`. No Python scripts, no npm packages, no pip installs.

---

## Architecture Patterns

### How the MCP Tool Works

The `mcp__claude_ai_Notion__notion-create-pages` tool is the **Claude.ai hosted Notion MCP integration** — distinct from the community `@notionhq/notion-mcp-server` npm package. Based on web search findings and the confirmed working test on 2026-04-09:

**Tool parameters (MEDIUM confidence — inferred from multiple sources):**

```json
{
  "title": "Translation Review — message-nouveau — 2026-04-09",
  "parent_page_id": "33dd6418695a8097998fcf373ed18bf5",
  "page_content": "## Summary\n\n| Country | Language | ...\n\n---\n\n## French reference..."
}
```

Key points:
- `title` — flat string (not a properties object)
- `parent_page_id` — flat string (not a nested `{"type": "page_id", "page_id": "..."}` object)
- `page_content` — Notion-flavored Markdown string (not a `children` JSON array)

The flat string parameters are critical: a January–February 2026 bug in the community MCP server serialized nested object params as strings and broke `parent`. The Claude.ai hosted tool uses flat string params to avoid this entirely. The CONTEXT.md confirms the tool was tested successfully on 2026-04-09.

### Notion-Flavored Markdown Format

Notion uses an enhanced Markdown spec for its MCP/markdown-content endpoints. Key differences from standard Markdown relevant to this report:

| Report Element | Standard Markdown | Notion-Flavored Markdown |
|----------------|------------------|--------------------------|
| H2 section headers | `## Heading` | `## Heading` (same) |
| H3 sub-headers | `### Heading` | `### Heading` (same) |
| Tables | `| col | col |` | `<table><tr><td>` HTML structure |
| Bullet lists | `- item` | `- item` (same) |
| Bold text | `**bold**` | `**bold**` (same) |
| Inline code | `` `code` `` | `` `code` `` (same) |
| Horizontal rule | `---` | `---` (same) |
| Blockquote | `> text` | `> text` (same) |
| Escape `@` in vars | not needed | wrap in `` `@TPL_*@` `` code span |
| HTML-like tags | literal text | wrap in `` ` `` code span |

**The summary table** (90+ market rows) uses standard Markdown pipe syntax in the .md report but Notion-flavored Markdown requires `<table>` HTML structure for tables. This is the main conversion the skill must do.

### Step 6 Integration Point

Current Step 6 structure:
```
1. Generate .md content
2. Write .md to reports/
3. Convert .md → .html (for html/pdf formats)
4. Write .html
5. Announce file paths
```

New Step 6 structure:
```
1. Generate .md content
2. Write .md to reports/
3. [html write removed]
4. Publish to Notion:
   a. Construct page title from sanitized ID + today's date
   b. Adapt .md content for Notion-flavored Markdown (table conversion, template var escaping)
   c. Call mcp__claude_ai_Notion__notion-create-pages
   d. On success: capture returned page URL
   e. On failure: capture error message
5. Announce .md path + Notion URL (success) OR .md path + warning (failure)
```

### Step 0 Integration Point

Current Step 0 `--format` flag:
```
--format html|md|pdf — Default: html
```

New Step 0 `--format` flag:
```
--format md|pdf — Default: md
```

Changes:
- Remove `html` as valid option from the valid options list
- Change default from `html` to `md`
- Update error message: `Unknown format "[value]". Valid options: md, pdf`
- The pdf path still generates .html as intermediate — this is internal behavior, not announced as output

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Publishing to Notion | Custom Python script using requests + Notion REST API | `mcp__claude_ai_Notion__notion-create-pages` | MCP is already configured, authenticated, tested |
| Converting .md to Notion blocks | JSON block builder | Notion-flavored Markdown string parameter | MCP accepts markdown string directly — no block array needed |
| Tracking parent page | Dynamic lookup | Hardcode parent ID `33dd6418695a8097998fcf373ed18bf5` | ID is stable; D-01 locks this |

---

## Common Pitfalls

### Pitfall 1: Template Variables Break in Notion
**What goes wrong:** `@TPL_EXPEDITEUR_PRENOM@` and similar strings contain `@` and `_` characters. Notion may render `@` as mention syntax, and backtick sequences without escaping may be parsed incorrectly.
**Why it happens:** Notion-flavored Markdown escapes `@` inside inline code spans. Outside code spans, `@` can trigger mention UI.
**How to avoid:** Wrap every `@TPL_*@` occurrence in backtick code spans: `` `@TPL_MATIERE_DE_MATIERE@` ``. The Notion enhanced-markdown spec explicitly states: no escaping needed inside code blocks.
**Warning signs:** Notion page shows @-mentions or broken text instead of variable names.

### Pitfall 2: Table Conversion Required
**What goes wrong:** The report's Summary table (Markdown pipe syntax) does not render as a Notion table block when using the enhanced markdown endpoint — the endpoint expects `<table>` HTML structure for table blocks.
**Why it happens:** Notion-flavored Markdown extends standard Markdown but uses HTML table syntax specifically.
**How to avoid:** When constructing the `page_content` string, convert the pipe-syntax Markdown table to `<table><tr><th>...</th></tr><tr><td>...</td></tr></table>` HTML. The summary table (90 rows × 5 columns) needs this conversion. The undefined variables table (variable × markets, if present) also needs it.
**Warning signs:** Notion page shows raw pipe characters instead of a formatted table.

### Pitfall 3: HTML-Like Template Tags in Body Text
**What goes wrong:** Translation bodies contain tags like `[TITRE]`, `[LIEN]`, `[BOUTON]`, `[/BOUTON]`. Notion's markdown parser may partially interpret these as HTML-like elements or strip them.
**Why it happens:** Notion-flavored Markdown uses `<callout>`, `<columns>` etc. as special tags. Square bracket tags `[TITRE]` are not valid HTML but could still be ambiguous.
**How to avoid:** Wrap translation body content (in "Current text" and "Proposed text" sections) in code blocks (triple backticks) rather than inline code spans, since they can contain newlines and may be long.
**Warning signs:** Translation body text appears malformed or stripped of structural tags.

### Pitfall 4: The `--format html` Removal Must Cover All Branches
**What goes wrong:** The html format is referenced in multiple places in Step 6 — the output behavior table, the announcement logic, and the MD-to-HTML conversion code block. Missing any of them leaves the skill in an inconsistent state.
**Why it happens:** The current skill has three separate references: (1) `--format html|md|pdf`, (2) the output behavior bullet list, (3) the Python conversion code block.
**How to avoid:** The plan must list ALL three locations as edit targets:
  - Step 0: change `--format html|md|pdf` to `--format md|pdf`, change default, update error message
  - Step 6 output behavior table: remove `html (default)` row entirely
  - Step 6 Python conversion block: remove entirely (it only runs for `html` and `pdf`; `pdf` still needs it — see D-08)
**Warning signs:** Running `/review-translations` with no `--format` flag still produces an .html file.

### Pitfall 5: PDF Format Still Needs HTML Intermediate
**What goes wrong:** Removing the HTML conversion Python block breaks `--format pdf` because weasyprint requires an HTML input file.
**Why it happens:** D-08 explicitly states the pdf path still generates .html as intermediate — but this is not announced to the user.
**How to avoid:** Keep the Python conversion block for the `pdf` path. The change is: (a) it no longer runs for the `md` (new default) path, and (b) the .html file it produces is not mentioned in the output announcement.
**Warning signs:** `--format pdf` fails with a missing .html error.

### Pitfall 6: Notion Publish Failure Must Not Block Step 7
**What goes wrong:** An unhandled MCP exception propagates up and aborts the session before Step 7 runs.
**Why it happens:** MCP tool calls can raise errors if the token is expired, the parent page was deleted, or a transient API issue occurs.
**How to avoid:** Wrap the MCP call in explicit try/catch language (skill instructions use conditional: "If the call returns an error..."). Per D-10/D-11/D-12, failure path: print warning, preserve .md path announcement, proceed directly to Step 7.
**Warning signs:** Session ends after a Notion error instead of proceeding to feedback prompt.

---

## Code Examples

### MCP Tool Call Pattern

```
Call mcp__claude_ai_Notion__notion-create-pages with:
- title: "Translation Review — [notification_id] — [YYYY-MM-DD]"
- parent_page_id: "33dd6418695a8097998fcf373ed18bf5"
- page_content: [adapted_markdown_string]

If the call succeeds, capture the returned page URL.
If the call raises an error, capture the error message for the warning.
```

Source: Inferred from Claude.ai Notion MCP pattern + CONTEXT.md confirmed test 2026-04-09. MEDIUM confidence.

### Notion-Flavored Markdown: Template Variable as Code Span

```markdown
**Body**: `[TITRE]`Nouveau message `@TPL_EXPEDITEUR_PRENOM@``[/TITRE]`...
```

Or equivalently for a full body line, use a fenced code block:

````markdown
```
[TITRE]Nouveau message @TPL_EXPEDITEUR_PRENOM@[/TITRE][LIEN]@TPL_MER_URL_DP@|@TPL_EXPEDITEUR_PHOTO@[/LIEN]
```
````

Source: [Notion enhanced markdown spec](https://developers.notion.com/guides/data-apis/enhanced-markdown) — no escaping needed inside code blocks. HIGH confidence.

### Notion-Flavored Markdown: Table Conversion

Original .md report table:
```markdown
| Country | Language | Errors | Warnings | Suggestions |
|---------|----------|--------|----------|-------------|
| France  | fr       | 0      | 0        | 0           |
```

Notion-flavored equivalent:
```html
<table>
<tr><th>Country</th><th>Language</th><th>Errors</th><th>Warnings</th><th>Suggestions</th></tr>
<tr><td>France</td><td>fr</td><td>0</td><td>0</td><td>0</td></tr>
</table>
```

Source: [Notion enhanced markdown spec](https://developers.notion.com/guides/data-apis/enhanced-markdown). HIGH confidence.

### Step 6 Announcement Block (New)

```
On Notion success:
"Report generated at `reports/review-[id]-[date].md`
Published to Notion: [page URL]"

On Notion failure:
"Report generated at `reports/review-[id]-[date].md`
Warning: Notion publish failed: [error]. Report saved locally."
```

Source: D-09, D-11 from CONTEXT.md. HIGH confidence (locked decision).

---

## Notion API Limits (Reference)

Confirmed via official Notion API docs. All are non-blocking for this phase given the markdown-endpoint approach:

| Limit | Value | Impact on Phase 5 |
|-------|-------|-------------------|
| Rich text content per text object | 2000 chars | N/A — using markdown endpoint, not block JSON |
| Block children per API call | 100 blocks | N/A — using markdown endpoint |
| API payload size | 500 KB | Reports are 32–42 KB — well within limit |
| Rate limit | ~3 req/sec | One publish per review run — not a concern |
| Markdown param | Mutually exclusive with `children` | Use `page_content` (markdown), do NOT also pass `children` |

Source: [Notion API request limits](https://developers.notion.com/reference/request-limits). HIGH confidence.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw JSON block arrays for page creation | Notion-flavored Markdown string | 2024–2025 (MCP launch) | Dramatically simpler implementation |
| `parent: {"type":"page_id","page_id":"..."}` object | `parent_page_id: "..."` flat string | Claude.ai MCP integration | Avoids the Feb 2026 object serialization bug |

**Known bug (resolved for this project):**
- Community `@notionhq/notion-mcp-server` had a `parent` object serialization bug (Feb 15–24, 2026) where nested object params were received as strings. This affected the community npm package. The Claude.ai hosted MCP (`mcp__claude_ai_Notion`) uses flat string parameters and was confirmed working on 2026-04-09 in this project.

---

## Open Questions

1. **Exact `page_content` parameter name**
   - What we know: The tool accepts a markdown string for page body content; confirmed working as of 2026-04-09
   - What's unclear: Whether the parameter is named `page_content`, `content`, or `markdown`
   - Recommendation: The planner should instruct the implementer to call the tool with the content string and observe the actual parameter name in the tool schema at call time. If the first attempt fails, try alternate names. The fallback (soft warn + continue) handles failure gracefully.

2. **Markdown table vs pipe-table support**
   - What we know: The enhanced markdown spec documents `<table>` HTML structure for tables
   - What's unclear: Whether the Claude.ai MCP `notion-create-pages` tool also accepts standard pipe-syntax tables (some Notion markdown parsers do)
   - Recommendation: Default to `<table>` HTML conversion per spec. The report has one large summary table — conversion is straightforward. If the tool renders pipe-tables correctly, the conversion is unnecessary but harmless.

3. **Returned page URL format**
   - What we know: Notion API returns the page `id` and `url` on creation
   - What's unclear: Whether `notion-create-pages` returns the URL directly in the tool response, and what its format is
   - Recommendation: Capture whatever URL is returned in the tool response. If no URL is in the response, construct it as `https://www.notion.so/[page_id_without_hyphens]`.

---

## Sources

### Primary (HIGH confidence)
- [Notion API request limits](https://developers.notion.com/reference/request-limits) — 2000 char rich_text limit, 100-block array limit, 500KB payload limit
- [Notion enhanced markdown spec](https://developers.notion.com/guides/data-apis/enhanced-markdown) — table HTML syntax, block type coverage, escaping rules, code block behavior
- [Notion create page reference](https://developers.notion.com/reference/post-page) — page creation endpoint, 100-item children limit
- [Notion block reference](https://developers.notion.com/reference/block) — table, table_row, heading_2, bulleted_list_item, divider block structures
- [Notion rich text reference](https://developers.notion.com/reference/rich-text) — annotations including `code: true` for inline code spans
- `.planning/phases/05-notion-publishing/05-CONTEXT.md` — locked decisions D-01 through D-12

### Secondary (MEDIUM confidence)
- [Notion MCP blog post](https://www.notion.com/blog/notions-hosted-mcp-server-an-inside-look) — confirms `create-pages` tool uses Notion-flavored Markdown, accepts string input
- [Claude Code issue #25865](https://github.com/anthropics/claude-code/issues/25865) — documents Feb 2026 object serialization bug in community MCP; Claude.ai hosted MCP uses flat string params
- [Claude Code issue #28223](https://github.com/anthropics/claude-code/issues/28223) — confirms `notion-create-pages` listed as working ✅ as of Feb 2026
- `~/.claude/settings.json` permissions — confirms `mcp__claude_ai_Notion__notion-create-pages` is pre-approved

### Tertiary (LOW confidence)
- WebSearch result citing `create_page(parentPageId, title, content)` flat-param pattern — consistent with observed tool behavior but not directly verified against Claude.ai MCP schema

---

## Metadata

**Confidence breakdown:**
- MCP tool call approach (markdown string, flat params): MEDIUM — confirmed working 2026-04-09, parameter names inferred from multiple sources
- Table conversion requirement: HIGH — verified against Notion enhanced markdown spec
- Template variable escaping: HIGH — verified, code blocks protect all special chars
- --format flag changes: HIGH — locked decisions in CONTEXT.md
- Step 6 insertion point: HIGH — clear from existing skill structure

**Research date:** 2026-04-09
**Valid until:** 2026-05-09 (stable API, but MCP tool schema could change with Notion updates)
