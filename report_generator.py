# =============================================================================
# report_generator.py — ReportLab PDF report builder
# Smart Battery Reuse Identification System
# =============================================================================

import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)

# ─── Colour palette ───────────────────────────────────────────────────────────

C_PRIMARY   = colors.HexColor("#0f3460")   # dark navy — header, headings
C_ACCENT    = colors.HexColor("#1a6b9a")   # mid-blue  — rule underlines
C_LIGHT_BG  = colors.HexColor("#f5f7fa")   # off-white — alternating rows
C_BORDER    = colors.HexColor("#d0d7de")   # grey      — grid lines
C_TEXT      = colors.HexColor("#1f2328")   # near-black
C_MUTED     = colors.HexColor("#656d76")   # grey text — footer, subtitle

C_GREEN     = colors.HexColor("#2e7d32")
C_YELLOW    = colors.HexColor("#e65100")
C_RED       = colors.HexColor("#c62828")

GRADE_COLOR = {"A": C_GREEN, "B": C_YELLOW, "C": C_RED}
GRADE_LABEL = {
    "A": "Grade A  —  Healthy / Reusable",
    "B": "Grade B  —  Usable with Caution",
    "C": "Grade C  —  Not Fit for Reuse",
}


# ─── Style helpers ────────────────────────────────────────────────────────────

def _make_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "DocTitle",
            parent=base["Normal"],
            fontSize=17,
            fontName="Helvetica-Bold",
            textColor=C_PRIMARY,
            alignment=TA_CENTER,
            spaceAfter=3,
        ),
        "subtitle": ParagraphStyle(
            "DocSubtitle",
            parent=base["Normal"],
            fontSize=10,
            fontName="Helvetica",
            textColor=C_MUTED,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Normal"],
            fontSize=11,
            fontName="Helvetica-Bold",
            textColor=C_PRIMARY,
            spaceBefore=16,
            spaceAfter=6,
        ),
        "footer": ParagraphStyle(
            "Footer",
            parent=base["Normal"],
            fontSize=8,
            fontName="Helvetica",
            textColor=C_MUTED,
            alignment=TA_CENTER,
        ),
    }


def _base_table_style():
    """Standard table styling: navy header, alternating rows, light grid."""
    return [
        ("BACKGROUND",       (0, 0), (-1, 0),  C_PRIMARY),
        ("TEXTCOLOR",        (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",         (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",         (0, 0), (-1, -1), 9.5),
        ("ALIGN",            (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",           (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",       (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",    (0, 0), (-1, -1), 7),
        ("LEFTPADDING",      (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",     (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS",   (0, 1), (-1, -1), [C_LIGHT_BG, colors.white]),
        ("GRID",             (0, 0), (-1, -1), 0.4, C_BORDER),
        ("LINEBELOW",        (0, 0), (-1, 0),  1.2, C_ACCENT),
    ]


# ─── Main entry point ─────────────────────────────────────────────────────────

def generate_report(
    battery_id: str,
    voltage: float,
    preprocessing_steps: list,
    defects: list,
    grade: str,
    recommendation: str,
) -> str:
    """
    Build a PDF report and save it to the /reports directory.

    Returns the path to the generated file.
    """
    ts        = datetime.now()
    report_id = f"RPT-{ts.strftime('%Y%m%d%H%M%S')}"
    safe_id   = "".join(c for c in battery_id if c.isalnum() or c in "-_")
    filename  = f"battery_report_{safe_id}_{ts.strftime('%Y%m%d_%H%M%S')}.pdf"
    out_dir   = "reports"
    os.makedirs(out_dir, exist_ok=True)
    filepath  = os.path.join(out_dir, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
    )

    st    = _make_styles()
    story = []

    # ── Page header ───────────────────────────────────────────────────────────
    story.append(Paragraph("SMART BATTERY REUSE IDENTIFICATION SYSTEM", st["title"]))
    story.append(Paragraph("Battery Condition Analysis Report", st["subtitle"]))
    story.append(Paragraph(
        f"Report ID: {report_id}   ·   {ts.strftime('%d %B %Y,  %H:%M:%S')}",
        st["subtitle"]
    ))
    story.append(HRFlowable(
        width="100%", thickness=2, color=C_PRIMARY,
        spaceBefore=8, spaceAfter=4
    ))

    # ── Section 1 — Battery details ───────────────────────────────────────────
    story.append(Paragraph("1.  BATTERY DETAILS", st["section"]))

    det_data = [
        ["Parameter",          "Value"],
        ["Battery ID",          battery_id],
        ["Measured Voltage",    f"{voltage:.2f} V"],
        ["Analysis Date",       ts.strftime("%d %B %Y")],
        ["Analysis Time",       ts.strftime("%H:%M:%S")],
        ["Report ID",           report_id],
    ]
    det_tbl = Table(det_data, colWidths=[6.5 * cm, 10.7 * cm])
    det_tbl.setStyle(TableStyle(_base_table_style()))
    story.append(det_tbl)

    # ── Section 2 — Preprocessing steps ──────────────────────────────────────
    story.append(Paragraph("2.  IMAGE PREPROCESSING STEPS", st["section"]))

    prep_data = [["#", "Processing Step", "Status"]]
    for i, step in enumerate(preprocessing_steps, 1):
        if "simulated" in step.lower():
            label  = step.split("[")[0].strip()
            status = "SIMULATED"
        else:
            label  = step.split("[")[0].strip()
            status = "COMPLETED"
        prep_data.append([str(i), label, status])

    prep_tbl   = Table(prep_data, colWidths=[1.0 * cm, 13.0 * cm, 3.2 * cm])
    prep_style = _base_table_style()
    prep_style += [
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
    ]
    for i, row in enumerate(prep_data[1:], 1):
        col = C_YELLOW if row[2] == "SIMULATED" else C_GREEN
        prep_style.append(("TEXTCOLOR", (2, i), (2, i), col))
        prep_style.append(("FONTNAME",  (2, i), (2, i), "Helvetica-Bold"))
    prep_tbl.setStyle(TableStyle(prep_style))
    story.append(prep_tbl)

    # ── Section 3 — Defect analysis ───────────────────────────────────────────
    story.append(Paragraph("3.  DEFECT ANALYSIS", st["section"]))

    def_data = [["Defect Type", "Status", "Severity", "Confidence"]]
    for d in defects:
        status = "DETECTED" if d["detected"] else "CLEAR"
        sev    = d.get("severity") or "—"
        conf   = f"{d['confidence']}%" if d["detected"] else "—"
        def_data.append([d["name"], status, sev, conf])

    def_tbl   = Table(def_data, colWidths=[5.2 * cm, 3.5 * cm, 3.5 * cm, 5.0 * cm])
    def_style = _base_table_style()
    def_style += [
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]
    for i, d in enumerate(defects, 1):
        if d["detected"]:
            def_style += [
                ("TEXTCOLOR",  (1, i), (1, i),  C_RED),
                ("FONTNAME",   (1, i), (1, i),  "Helvetica-Bold"),
                ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fff0f0")),
            ]
        else:
            def_style += [
                ("TEXTCOLOR",  (1, i), (1, i), C_GREEN),
                ("FONTNAME",   (1, i), (1, i), "Helvetica-Bold"),
            ]
    def_tbl.setStyle(TableStyle(def_style))
    story.append(def_tbl)

    # ── Section 4 — Classification result ────────────────────────────────────
    story.append(Paragraph("4.  CLASSIFICATION RESULT", st["section"]))

    gc  = GRADE_COLOR.get(grade, C_PRIMARY)
    lbl = GRADE_LABEL.get(grade, f"Grade {grade}")

    res_data = [
        ["Classification Grade", lbl],
        ["Recommendation",       recommendation],
    ]
    res_tbl   = Table(res_data, colWidths=[5.5 * cm, 11.7 * cm])
    res_style = [
        ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",      (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("TEXTCOLOR",     (0, 0), (0, -1),  C_PRIMARY),
        ("TEXTCOLOR",     (1, 0), (1,  0),  gc),
        ("FONTNAME",      (1, 0), (1,  0),  "Helvetica-Bold"),
        ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("BACKGROUND",    (0, 0), (-1, -1), C_LIGHT_BG),
        ("BOX",           (0, 0), (-1, -1), 2.0, gc),
        ("LINEBELOW",     (0, 0), (-1,  0), 0.5, C_BORDER),
    ]
    res_tbl.setStyle(TableStyle(res_style))
    story.append(res_tbl)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.2 * cm))
    story.append(HRFlowable(
        width="100%", thickness=0.8, color=C_BORDER, spaceAfter=8
    ))
    story.append(Paragraph(
        "This report was generated by the Smart Battery Reuse Identification System. "
        "Results are based on image analysis and voltage measurements. "
        "Final reuse decisions must be confirmed by a qualified engineer.",
        st["footer"]
    ))

    doc.build(story)
    return filepath
