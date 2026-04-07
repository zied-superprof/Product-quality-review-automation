"""Generate PDF from the by-country review markdown report."""
import markdown
import subprocess
import sys
from pathlib import Path

REPORTS_DIR = Path(__file__).parent.parent / "reports"
md_path = REPORTS_DIR / "review-by-country-2026-04-03.md"
html_path = REPORTS_DIR / "review-by-country-2026-04-03.html"
pdf_path = REPORTS_DIR / "review-by-country-2026-04-03.pdf"

content = md_path.read_text(encoding="utf-8")

body = markdown.markdown(content, extensions=["tables", "fenced_code"])

html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Translation Quality Review - By Country</title>
<style>
  body {{
    font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.65;
    color: #1a1a2e;
    max-width: 800px;
    margin: 0 auto;
    padding: 32px 40px;
  }}
  h1 {{
    font-size: 20pt;
    font-weight: 700;
    color: #0f3460;
    border-bottom: 3px solid #e94560;
    padding-bottom: 8px;
    margin-top: 0;
  }}
  h2 {{
    font-size: 13pt;
    font-weight: 700;
    color: #ffffff;
    background: #0f3460;
    padding: 6px 12px;
    margin-top: 24px;
    border-radius: 3px;
  }}
  h3 {{
    font-size: 11pt;
    font-weight: 600;
    color: #0f3460;
    margin-top: 16px;
    border-left: 4px solid #e94560;
    padding-left: 8px;
  }}
  h4 {{
    font-size: 10pt;
    font-weight: 600;
    color: #333;
    font-style: italic;
    margin-top: 12px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9pt;
    margin: 12px 0;
  }}
  th {{
    background: #0f3460;
    color: white;
    padding: 5px 8px;
    text-align: left;
    font-weight: 600;
  }}
  td {{
    padding: 4px 8px;
    border-bottom: 1px solid #e0e0e0;
    vertical-align: top;
  }}
  tr:nth-child(even) td {{
    background: #f8f9fc;
  }}
  blockquote {{
    border-left: 3px solid #e94560;
    margin: 10px 0;
    padding: 5px 12px;
    background: #fff5f5;
    color: #555;
    font-style: italic;
  }}
  code {{
    background: #f0f0f0;
    padding: 1px 4px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 9pt;
  }}
  pre {{
    background: #f6f8fa;
    padding: 12px;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 9pt;
  }}
  strong {{
    color: #0f3460;
  }}
  hr {{
    border: none;
    border-top: 1px solid #ddd;
    margin: 16px 0;
  }}
  ol, ul {{
    padding-left: 20px;
  }}
  li {{
    margin-bottom: 4px;
  }}
  @media print {{
    body {{ max-width: 100%; padding: 0; }}
    h2 {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    th {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    tr:nth-child(even) td {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  }}
</style>
</head>
<body>
{body}
</body>
</html>"""

html_path.write_text(html, encoding="utf-8")
print(f"HTML written: {html_path}")

# Try weasyprint
try:
    from weasyprint import HTML as WP_HTML
    WP_HTML(filename=str(html_path)).write_pdf(str(pdf_path))
    print(f"PDF created via weasyprint: {pdf_path}")
    sys.exit(0)
except Exception as e:
    print(f"weasyprint failed: {e}", file=sys.stderr)

# Try cupsfilter
try:
    result = subprocess.run(
        ["cupsfilter", str(html_path)],
        capture_output=True, timeout=30
    )
    if result.returncode == 0 and result.stdout:
        pdf_path.write_bytes(result.stdout)
        print(f"PDF created via cupsfilter: {pdf_path}")
        sys.exit(0)
    else:
        print(f"cupsfilter failed: {result.stderr.decode()}", file=sys.stderr)
except Exception as e:
    print(f"cupsfilter error: {e}", file=sys.stderr)

print("Could not generate PDF automatically.", file=sys.stderr)
print(f"HTML report is available at: {html_path}", file=sys.stderr)
sys.exit(1)
