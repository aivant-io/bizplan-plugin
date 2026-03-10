---
name: ecommerce-document-export
description: >
  Converts a markdown business plan into a professionally styled Word document
  (.docx) using Pandoc with a custom reference template. Handles heading promotion,
  citation conversion, cover page styling, table of contents, and section page
  breaks. Optional — falls back to markdown delivery if Pandoc is not available.
context: fork
model: haiku
allowed-tools: Read, Write, Glob, Grep, Bash
---

# Ecommerce Document Export

## Overview

This skill converts the markdown business plan (from the ecommerce-business-plan skill) into a professionally styled Word document. It is **optional** — if Pandoc is not installed, deliver the plan as markdown instead.

## File Inputs & Outputs

This skill is invoked with the store name as its argument: `$ARGUMENTS`

**Read from the current working directory:**
- `{StoreName}_Business_Plan.md` — markdown business plan (using the store name from `$ARGUMENTS`)

**Read from the skill directory:**
- `${CLAUDE_SKILL_DIR}/scripts/export_docx.py` — main export script
- `${CLAUDE_SKILL_DIR}/scripts/create_reference_doc.py` — template generator
- `${CLAUDE_SKILL_DIR}/templates/reference.docx` — Pandoc reference template
- `${CLAUDE_SKILL_DIR}/requirements.txt` — Python dependencies (python-docx)

**Write to the current working directory:**
- `{StoreName}_Business_Plan.docx` — styled Word document

**Scripts:**
- [scripts/export_docx.py](scripts/export_docx.py) — Main export script (preprocessing + Pandoc + post-processing)
- [scripts/create_reference_doc.py](scripts/create_reference_doc.py) — Regenerates the reference template

**Template:** [templates/reference.docx](templates/reference.docx) — defines fonts, colors, margins, heading styles.

## Prerequisites

```bash
pandoc --version          # Required for DOCX conversion
pip install python-docx   # Required for cover page post-processing
```

If Pandoc is not available, skip DOCX export and deliver the markdown plan directly.

## Export Process

### Preferred: Use the Export Script

Run the export script directly — it handles all preprocessing, conversion, and post-processing:

```bash
python scripts/export_docx.py <input.md> <output.docx> --title "StoreName" [--date "March 2026"]
```

Example:
```bash
python scripts/export_docx.py \
  Terra_Tide_Business_Plan.md \
  Terra_Tide_Business_Plan.docx \
  --title "Terra & Tide" \
  --date "March 2026"
```

The script performs these steps automatically:

### Step 1: Strip Document Header

Remove the existing markdown header block (H1 title, H2 subtitle, italicized date, horizontal rule) since these are replaced by YAML front matter for the cover page.

### Step 2: Promote Headings

The business plan writer produces `## 1. Executive Summary` (H2 with numbers). The reference template only sets `page_break_before` on H1 style. The export script promotes all headings:

- `## N. Section Name` → `# Section Name` (H1 — triggers page break, strips section numbers)
- `### Subsection` → `## Subsection` (H2)
- `#### Detail` → `### Detail` (H3)

### Step 3: Convert Citations to Superscript

Convert `[N]` bracket citations to Pandoc superscript syntax `^[N]^`. Only matches 1-3 digit numbers. Avoids markdown links `[text](url)`.

### Step 3b: Convert Bracketed URLs to Clickable Links

Convert plain-text URLs in brackets `[https://...]` to proper markdown links `[url](url)` so Pandoc renders them as blue, clickable hyperlinks in the DOCX output.

### Step 4: Ensure Blank Lines Before Lists

Pandoc requires a blank line before bulleted/numbered lists. The script inserts them automatically.

### Step 5: Remove Horizontal Rules

Strip `---` separators — not needed since H1 page breaks handle section separation.

### Step 6: Generate YAML Front Matter and TOC

Prepend YAML metadata (title, subtitle, date) for the cover page, followed by a static Table of Contents generated from the H1 headings.

### Step 7: Run Pandoc

```bash
pandoc -f markdown -t docx --reference-doc=templates/reference.docx -o output.docx input.md
```

### Step 8: Post-Process Cover Page

Uses python-docx to style the cover page:
- **Title**: centered, pushed ~2.5 inches down the page (Pt(180) space before)
- **Subtitle**: centered, tight below title (Pt(12) space before)
- **Date**: centered, pushed to bottom of page (Pt(300) space before)

## Reference Template

The reference.docx defines the professional styling applied by Pandoc:

| Style | Font | Size | Color | Notes |
|-------|------|------|-------|-------|
| Title | Times New Roman | 44pt Bold | #1A365D (navy) | Cover page business name |
| Subtitle | Times New Roman | 24pt Italic | #2E5C8A (blue) | Cover page subtitle |
| Date | Times New Roman | 14pt | #333333 (gray) | Cover page date |
| Heading 1 | Times New Roman | 24pt Bold | #1A365D (navy) | `page_break_before=True` |
| Heading 2 | Times New Roman | 18pt Bold | #2E5C8A (blue) | Subsection headings |
| Heading 3 | Times New Roman | 14pt Bold | #3D85C6 (light blue) | Minor headings |
| Heading 4 | Times New Roman | 12pt Bold Italic | #333333 (gray) | Detail headings |
| Body | Times New Roman | 11pt | #333333 (gray) | 1.15 line spacing |
| Hyperlink | — | — | #0563C1 (blue) | Underlined |

**Margins:** 1 inch all sides. **Page size:** 8.5" x 11" (US Letter).

To regenerate the reference template:
```bash
python scripts/create_reference_doc.py
```

## Document Structure

The final .docx has this structure:

1. **Cover Page**: Business name (44pt, centered), "Business Plan" subtitle, date
2. **Table of Contents**: Bullet list of section headings (new page)
3. **Executive Summary** (new page)
4. **Business Overview** (new page)
5. **Market Opportunity** (new page)
6. **Go-to-Market Strategy** (new page)
7. **Operations** (new page)
8. **Financial Plan** (new page)
9. **Appendix** (new page)
   - Financial Projections Table
   - Sources Cited
   - Key Assumptions

Each H1 heading triggers a page break (configured in reference.docx).

## Fallback: Markdown Delivery

If Pandoc is not available, deliver the markdown file directly:

```
output/BusinessPlan.md
```

Inform the user:
> "The business plan has been saved as markdown. For a professionally styled Word document, install Pandoc (`brew install pandoc` on macOS or `apt install pandoc` on Linux) and re-run the export."

## Citation Rendering

Citations appear differently in markdown vs. Word:

| Format | Markdown | Word (.docx) |
|--------|----------|---------------|
| In-text | `[1]` | ^[1]^ (superscript) |
| Sources | Numbered list | Numbered list |

The conversion from `[1]` to `^[1]^` happens before Pandoc processes the file.

## Critical Rules

1. **Pandoc is optional** — always have a markdown fallback
2. **Always use the export script** — `scripts/export_docx.py` handles all preprocessing and post-processing
3. **Promote headings before Pandoc** — `## N.` → `#` so H1 page breaks work
4. **Strip section numbers** — "1. Executive Summary" becomes "Executive Summary" in the DOCX
5. **Remove horizontal rules** — `---` separators are replaced by H1 page breaks
6. **Post-process cover page** — python-docx centers title/subtitle/date with proper spacing
7. **Escape bracket citations** — convert `[N]` to `^[N]^` before Pandoc
8. **Blank lines before lists** — Pandoc requires them or lists won't render
9. **Cover page is YAML front matter** — title, subtitle, date fields
10. **Page breaks via H1** — reference.docx configures `page_break_before` on Heading 1
11. **Timeout**: Allow up to 60 seconds for Pandoc conversion
12. **To regenerate template**: Run `scripts/create_reference_doc.py` — never manually edit `reference.docx`
