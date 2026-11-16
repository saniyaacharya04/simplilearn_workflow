"""
Simplilearn Voiceover Sheet Generator (DOCX & PDF)
Adapted from KPLOR Timestamp Experiments & Simplilearn OSL CE Guidelines.
Produces formatted Voiceover Sheets with exact mm:ss timestamps.
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any

# Word Imports
from docx import Document
from docx.shared import Inches, RGBColor, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

# PDF Imports
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .config import (
    COLORS,
    OPEN_SANS_REGULAR,
    OPEN_SANS_BOLD,
    NOTO_SANS_REGULAR,
    NOTO_SANS_BOLD
)

HEADER_BG_COLOR = "0B3C5D"  # Simplilearn Dark Blue Hex Code

# Register TTF Fonts for PDF
def register_pdf_fonts():
    """Registers OpenSans / NotoSans for PDF generation."""
    try:
        if OPEN_SANS_REGULAR.exists() and OPEN_SANS_BOLD.exists():
            pdfmetrics.registerFont(TTFont("OpenSans", str(OPEN_SANS_REGULAR)))
            pdfmetrics.registerFont(TTFont("OpenSansBold", str(OPEN_SANS_BOLD)))
            return "OpenSans", "OpenSansBold"
    except Exception:
        pass

    try:
        if NOTO_SANS_REGULAR.exists() and NOTO_SANS_BOLD.exists():
            pdfmetrics.registerFont(TTFont("NotoSans", str(NOTO_SANS_REGULAR)))
            pdfmetrics.registerFont(TTFont("NotoSansBold", str(NOTO_SANS_BOLD)))
            return "NotoSans", "NotoSansBold"
    except Exception:
        pass

    return "Helvetica", "Helvetica-Bold"


def format_timestamp(total_seconds: float) -> str:
    """Formats float seconds into standard mm:ss string."""
    mins = int(total_seconds) // 60
    secs = int(total_seconds) % 60
    return f"{mins:02d}:{secs:02d}"


def set_cell_background(cell, hex_color: str):
    """Sets background shading of a docx table cell."""
    tc_pr = cell._element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def add_docx_table_borders(table):
    """Adds standard clean borders to docx table."""
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for border_name in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        border = OxmlElement(f"w:{border_name}")
        border.set(qn("w:val"), "single")
        border.set(qn("w:sz"), "4")
        border.set(qn("w:space"), "0")
        border.set(qn("w:color"), "D3D3D3")
        borders.append(border)
    tbl_pr.append(borders)


# ==============================================================================
# DOCX GENERATOR
# ==============================================================================

def generate_voiceover_docx(
    title: str,
    rows: List[List[str]],
    output_docx_path: str
) -> str:
    """Generates a professional Word Voiceover document."""
    doc = Document()
    for s in doc.sections:
        s.left_margin = Inches(0.5)
        s.right_margin = Inches(0.5)
        s.top_margin = Inches(0.5)
        s.bottom_margin = Inches(0.5)

    heading = doc.add_heading(f"Voiceover Sheet – {title}", level=1)
    for run in heading.runs:
        run.font.name = "Open Sans"
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = RGBColor(11, 60, 93)

    columns = ["S.NO.", "Voiceover / Narration Script", "Time Stamp"]
    col_widths = [Inches(0.7), Inches(5.2), Inches(1.1)]

    table = doc.add_table(rows=1, cols=3)
    table.autofit = False
    add_docx_table_borders(table)

    for i, w in enumerate(col_widths):
        table.columns[i].width = w

    # Header Row
    hdr_cells = table.rows[0].cells
    for i, col_name in enumerate(columns):
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(col_name)
        run.bold = True
        run.font.name = "Open Sans"
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(255, 255, 255)
        set_cell_background(hdr_cells[i], HEADER_BG_COLOR)

    # Data Rows
    for row_data in rows:
        r = table.add_row().cells
        for i, val in enumerate(row_data):
            p = r[i].paragraphs[0]
            if i in (0, 2):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(str(val))
            run.font.name = "Open Sans"
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(64, 64, 64)

    Path(output_docx_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_docx_path)
    print(f"  ✓ DOCX Sheet: {output_docx_path}")
    return output_docx_path


# ==============================================================================
# PDF GENERATOR
# ==============================================================================

def generate_voiceover_pdf(
    title: str,
    rows: List[List[str]],
    output_pdf_path: str
) -> str:
    """Generates a professional PDF Voiceover document."""
    font_reg, font_bold = register_pdf_fonts()

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName=font_bold,
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#0B3C5D"),
        spaceAfter=12
    )
    header_style = ParagraphStyle(
        "HdrStyle",
        fontName=font_bold,
        fontSize=9,
        leading=11,
        textColor=colors.white,
        alignment=1
    )
    body_style = ParagraphStyle(
        "BodyStyle",
        fontName=font_reg,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#404040")
    )
    center_style = ParagraphStyle(
        "CenterStyle",
        fontName=font_reg,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#404040"),
        alignment=1
    )

    elements = [
        Paragraph(f"Voiceover Sheet – {title}", title_style),
        Spacer(1, 8)
    ]

    col_widths = [45, 395, 80]
    table_data = [[
        Paragraph("S.NO.", header_style),
        Paragraph("Voiceover / Narration Script", header_style),
        Paragraph("Time Stamp", header_style)
    ]]

    for row in rows:
        table_data.append([
            Paragraph(row[0], center_style),
            Paragraph(row[1], body_style),
            Paragraph(row[2], center_style)
        ])

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(f"#{HEADER_BG_COLOR}")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D3D3D3")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")])
    ]))

    elements.append(t)
    Path(output_pdf_path).parent.mkdir(parents=True, exist_ok=True)
    doc.build(elements)
    print(f"  ✓ PDF Sheet:  {output_pdf_path}")
    return output_pdf_path


# ==============================================================================
# PIPELINE ENTRY
# ==============================================================================

def create_voiceover_sheets(
    transcript_json: str,
    output_dir: str,
    lesson_title: str = "Lesson"
) -> Dict[str, str]:
    """Loads transcript segments and creates both DOCX and PDF sheets."""
    with open(transcript_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle both list of segments or dict of sections
    segments = []
    if isinstance(data, list):
        segments = data
    elif isinstance(data, dict):
        for k in sorted(data.keys(), key=lambda x: int(x) if x.isdigit() else x):
            segments.extend(data[k])

    rows = []
    s_no = 1
    for item in segments:
        text = item.get("cleaned_text") or item.get("text") or item.get("narration_statement", "")
        if not text.strip():
            continue

        ts_start = item.get("start", 0.0)
        time_str = format_timestamp(ts_start)

        rows.append([str(s_no), text.strip(), time_str])
        s_no += 1

    out_path = Path(output_dir)
    docx_file = out_path / f"Voiceover_Sheet_{lesson_title}.docx"
    pdf_file = out_path / f"Voiceover_Sheet_{lesson_title}.pdf"

    print(f"\n[Voiceover Generator] Exporting {len(rows)} statements for '{lesson_title}'...")
    generate_voiceover_docx(lesson_title, rows, str(docx_file))
    generate_voiceover_pdf(lesson_title, rows, str(pdf_file))

    return {
        "docx": str(docx_file),
        "pdf": str(pdf_file),
        "count": len(rows)
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m pipeline.5_voiceover_doc_generator <transcript_json> <output_dir> [lesson_title]")
        sys.exit(1)
    title = sys.argv[3] if len(sys.argv) > 3 else "Topic"
    create_voiceover_sheets(sys.argv[1], sys.argv[2], title)
