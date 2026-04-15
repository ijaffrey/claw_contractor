"""Render a bid-proposal PDF from a takeoff + contractor profile."""

import datetime
import logging
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)

from . import scope_writer

log = logging.getLogger(__name__)


def _usd(x: float) -> str:
    try:
        return f"${float(x):,.2f}"
    except (TypeError, ValueError):
        return "-"


def _pct(x: float) -> str:
    try:
        return f"{float(x) * 100:.0f}%"
    except (TypeError, ValueError):
        return "-"


def build_proposal_pdf(
    takeoff: dict,
    contractor: dict,
    out_path: Path,
) -> Path:
    """Write a full bid proposal PDF for the given takeoff and contractor."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Small", parent=styles["BodyText"], fontSize=8, leading=10
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2b",
            parent=styles["Heading2"],
            spaceBefore=12,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Mono",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
        )
    )

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=LETTER,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title=f"{contractor.get('name','')} Proposal",
        author=contractor.get("name", ""),
    )

    story: list = []

    # --- Header ---
    header_tbl = Table(
        [
            [
                Paragraph(
                    f"<b><font size=16>{contractor.get('name','')}</font></b>",
                    styles["BodyText"],
                ),
                Paragraph(
                    "<b>BID PROPOSAL</b>",
                    ParagraphStyle(
                        "hrt",
                        parent=styles["BodyText"],
                        alignment=2,
                        fontSize=14,
                    ),
                ),
            ],
            [
                Paragraph(
                    (
                        f"{contractor.get('address','')}<br/>"
                        f"License: {contractor.get('license','')}<br/>"
                        f"{contractor.get('contact','')} — {contractor.get('phone','')}<br/>"
                        f"{contractor.get('email','')}"
                    ),
                    styles["Small"],
                ),
                Paragraph(
                    (
                        f"Date: {datetime.date.today().isoformat()}<br/>"
                        f"Valid for: {contractor.get('proposal_validity_days', 30)} days"
                    ),
                    ParagraphStyle(
                        "hrr",
                        parent=styles["Small"],
                        alignment=2,
                    ),
                ),
            ],
        ],
        colWidths=[4.0 * inch, 3.0 * inch],
    )
    header_tbl.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, -1), (-1, -1), 1.2, colors.black),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(header_tbl)
    story.append(Spacer(1, 0.2 * inch))

    # --- Project block ---
    resolved = takeoff.get("resolved", {}) or {}
    summary = takeoff.get("scope_summary", {}) or {}
    hvp = summary.get("highest_value_permit") or {}

    project_rows = [
        ["Project Address:", takeoff.get("input_address", "-")],
        ["BIN / BBL:", f"{resolved.get('bin','-')}  /  {resolved.get('bbl','-')}"],
        ["Building:", f"{int(resolved.get('num_floors') or 0)}-story, "
                      f"{int(resolved.get('bldg_area_sqft') or 0):,} sqft, "
                      f"built {resolved.get('year_built','-')}, "
                      f"class {resolved.get('bldg_class','-')}"],
        ["Reference Job Filing:", hvp.get("job_filing_number", "(not specified)")],
        ["Reference Scope:", (hvp.get("job_description") or "(not specified)")[:300]],
    ]
    project_tbl = Table(project_rows, colWidths=[1.6 * inch, 5.4 * inch])
    project_tbl.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(project_tbl)
    story.append(Spacer(1, 0.18 * inch))

    # --- Scope of Work ---
    story.append(Paragraph("Scope of Work", styles["H2b"]))
    story.append(Paragraph(scope_writer.build_scope_paragraph(takeoff), styles["BodyText"]))
    story.append(Spacer(1, 0.1 * inch))

    # --- Line items table ---
    story.append(Paragraph("Line Items", styles["H2b"]))
    line_rows = [
        [
            Paragraph("<b>Trade</b>", styles["Small"]),
            Paragraph("<b>Description</b>", styles["Small"]),
            Paragraph("<b>Qty</b>", styles["Small"]),
            Paragraph("<b>Unit</b>", styles["Small"]),
            Paragraph("<b>Unit Price</b>", styles["Small"]),
            Paragraph("<b>Total</b>", styles["Small"]),
        ]
    ]
    flagged_marker = "*"
    footnotes: list = []
    for trade in takeoff.get("trades", []):
        if not trade.get("applicable"):
            continue
        tname = trade["name"].replace("_", " ").title()
        for li in trade.get("line_items", []):
            if (li.get("quantity") or 0) <= 0:
                continue
            desc = li["item"].replace("_", " ").title()
            low_conf = li.get("confidence") == "low"
            marker = flagged_marker if low_conf else ""
            if low_conf:
                footnotes.append(f"{desc} ({trade['name']}): {li.get('basis','')}")
            line_rows.append(
                [
                    Paragraph(tname, styles["Small"]),
                    Paragraph(desc + marker, styles["Small"]),
                    Paragraph(f"{li['quantity']:,.0f}", styles["Small"]),
                    Paragraph(li.get("unit", ""), styles["Small"]),
                    Paragraph(_usd(li.get("unit_rate", 0)), styles["Small"]),
                    Paragraph(_usd(li.get("subtotal", 0)), styles["Small"]),
                ]
            )
    if len(line_rows) == 1:
        line_rows.append(
            [
                Paragraph("—", styles["Small"]),
                Paragraph("No priceable line items — see flags", styles["Small"]),
                "", "", "", "",
            ]
        )

    # Totals block from grand_total
    gt = takeoff.get("estimated_total_cost", {}) or {}
    line_rows.extend(
        [
            ["", "", "", "", Paragraph("<b>Subtotal</b>", styles["Small"]), Paragraph(_usd(gt.get("subtotal", 0)), styles["Small"])],
            ["", "", "", "", Paragraph(f"Overhead ({_pct(gt.get('overhead_pct',0))})", styles["Small"]), Paragraph(_usd(gt.get("overhead", 0)), styles["Small"])],
            ["", "", "", "", Paragraph(f"Profit ({_pct(gt.get('profit_pct',0))})", styles["Small"]), Paragraph(_usd(gt.get("profit", 0)), styles["Small"])],
            ["", "", "", "", Paragraph(f"Contingency ({_pct(gt.get('contingency_pct',0))})", styles["Small"]), Paragraph(_usd(gt.get("contingency", 0)), styles["Small"])],
            ["", "", "", "", Paragraph("<b>TOTAL</b>", styles["Small"]), Paragraph(f"<b>{_usd(gt.get('total',0))}</b>", styles["Small"])],
        ]
    )
    lt = Table(
        line_rows,
        colWidths=[0.9 * inch, 2.6 * inch, 0.7 * inch, 0.55 * inch, 1.0 * inch, 1.15 * inch],
    )
    lt.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -6), 0.25, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("LINEABOVE", (4, -5), (-1, -5), 0.5, colors.black),
                ("LINEABOVE", (4, -1), (-1, -1), 1.0, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(lt)
    story.append(Spacer(1, 0.1 * inch))

    # --- Footnotes for low-confidence items ---
    if footnotes:
        story.append(Paragraph("Footnotes", styles["H2b"]))
        story.append(
            Paragraph(
                "Items marked with * are low-confidence estimates requiring "
                "verification at walkthrough:",
                styles["Small"],
            )
        )
        for fn in footnotes:
            story.append(Paragraph(f"* {fn}", styles["Small"]))
        story.append(Spacer(1, 0.1 * inch))

    # --- Exclusions ---
    story.append(Paragraph("Exclusions", styles["H2b"]))
    excl_items = "<br/>".join(f"• {e}" for e in scope_writer.EXCLUSIONS)
    story.append(Paragraph(excl_items, styles["BodyText"]))
    story.append(Spacer(1, 0.1 * inch))

    # --- Terms ---
    pt = contractor.get("payment_terms", {}) or {}
    story.append(Paragraph("Payment Terms", styles["H2b"]))
    terms_text = (
        f"{_pct(pt.get('deposit_pct', 0.10))} deposit upon contract signing. "
        f"{_pct(pt.get('mobilization_pct', 0.40))} upon mobilization. "
        f"{_pct(pt.get('progress_pct', 0.40))} progress payments during work. "
        f"{_pct(pt.get('completion_pct', 0.10))} upon substantial completion. "
        "Net 15 on all invoices. Change orders billed separately at cost + overhead and profit."
    )
    story.append(Paragraph(terms_text, styles["BodyText"]))
    story.append(Spacer(1, 0.2 * inch))

    # --- Signature block ---
    story.append(Paragraph("Acceptance", styles["H2b"]))
    sig_tbl = Table(
        [
            [
                Paragraph(
                    f"<b>{contractor.get('name','')}</b><br/>"
                    f"By: {contractor.get('contact','')}<br/>"
                    f"_______________________________<br/>"
                    f"Signature / Date",
                    styles["Small"],
                ),
                Paragraph(
                    "<b>Client</b><br/>"
                    "By: _______________________________<br/>"
                    "Title: _______________________________<br/>"
                    "_______________________________<br/>"
                    "Signature / Date",
                    styles["Small"],
                ),
            ]
        ],
        colWidths=[3.4 * inch, 3.4 * inch],
    )
    sig_tbl.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(sig_tbl)

    doc.build(story)
    log.info("Wrote proposal PDF to %s", out_path)
    return out_path
