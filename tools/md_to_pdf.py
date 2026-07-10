#!/usr/bin/env python3
"""md_to_pdf.py — Convert Markdown → styled A4 PDF via Playwright + Chromium."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import markdown  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

DEFAULT_CSS = """
@page { size: A4; margin: 2cm; }
body { font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; font-size: 10.5pt; line-height: 1.5; color: #222; }
h1 { font-size: 20pt; color: #1a1a2e; border-bottom: 3px solid #c9a961; padding-bottom: 8px; margin-top: 0; }
h2 { font-size: 14pt; color: #2c2c2c; border-bottom: 2px solid #e0e0e0; padding-bottom: 6px; margin-top: 28px; page-break-after: avoid; }
h3 { font-size: 12pt; color: #333; margin-top: 20px; page-break-after: avoid; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 14px; font-size: 10pt; page-break-inside: avoid; }
th { background: #1a1a2e; color: #fff; text-align: left; padding: 8px 10px; font-weight: 600; }
td { border: 1px solid #ddd; padding: 7px 10px; vertical-align: top; }
tr:nth-child(even) { background: #fafafa; }
code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; font-family: "Consolas", "Monaco", monospace; font-size: 9.5pt; }
pre { background: #f4f4f4; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 9pt; line-height: 1.4; }
blockquote { border-left: 4px solid #c9a961; padding: 10px 14px; margin: 12px 0; background: #fdfbf6; color: #444; font-size: 10pt; page-break-inside: avoid; }
ul, ol { margin-top: 6px; margin-bottom: 10px; padding-left: 22px; }
li { margin-bottom: 4px; }
hr { border: none; border-top: 1px solid #ddd; margin: 24px 0; }
"""


def convert(md_path: str | Path, pdf_path: str | Path | None = None, css: str | None = None) -> Path:
    src = Path(md_path)
    if not src.exists():
        raise FileNotFoundError(f"Markdown file not found: {src}")

    dst = Path(pdf_path) if pdf_path else src.with_suffix(".pdf")
    css = css or DEFAULT_CSS

    md_content = src.read_text(encoding="utf-8")
    html_body = markdown.markdown(md_content, extensions=["tables", "fenced_code", "codehilite"])
    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <style>{css}</style>
</head>
<body>
{html_body}
</body>
</html>"""

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_template, wait_until="domcontentloaded")
        page.pdf(
            path=str(dst),
            format="A4",
            margin={"top": "2cm", "bottom": "2cm", "left": "2cm", "right": "2cm"},
            print_background=True,
        )
        browser.close()

    print(f"PDF generado: {dst}")
    return dst


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        print("\nUsage:")
        print("  memento-md-to-pdf <input.md> [output.pdf]")
        return 1 if len(sys.argv) < 2 else 0

    convert(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
