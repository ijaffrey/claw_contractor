"""RFP builder — generate a pre-populated RFP document from pipeline data.

Reads dob_output/{slug}/result.json and takeoff.json. If no takeoff exists,
falls back to Tier 1 (permit-only) RFP.

Outputs: rfps/{slug}_rfp.pdf and rfps/{slug}_rfp.html.
"""
from __future__ import annotations

import datetime
import html as html_mod
import json
import logging
from pathlib import Path
from typing import Any

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
)

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DOB_OUTPUT = REPO_ROOT / "dob_output"
RFPS_DIR = REPO_ROOT / "rfps"

PAYMENT_TERMS = "10% mobilization / 40% rough completion / 40% substantial completion / 10% final"
CONTRACTOR_REQS = (
    "All contractors must be licensed and insured in New York State, "
    "registered with NYC Department of Buildings, and carry a minimum "
    "$1M general liability and $2M umbrella policy."
)


def _usd(v: float | None) -> str:
    try:
        return f"${float(v):,.0f}"
    except (TypeError, ValueError):
        return "—"


def build_rfp(address_slug: str, firm_info: dict | None = None) -> dict[str, Any]:
    """Build RFP PDF + HTML for *address_slug*.

    Returns ``{pdf_path, html_path, sections_populated, confidence, tier}``.
    """
    firm_info = firm_info or {}
    slug = address_slug

    # Load data
    result_path = DOB_OUTPUT / slug / "result.json"
    takeoff_path = DOB_OUTPUT / slug / "takeoff.json"

    result_data = _load_json(result_path)
    takeoff = _load_json(takeoff_path)

    tier = "3" if takeoff else "1"

    # Build context
    resolved = (takeoff or {}).get("resolved", {})
    address = (
        (takeoff or {}).get("input_address")
        or (result_data or {}).get("input_address")
        or slug.replace("_", " ").title()
    )
    project = {
        "address": address,
        "year_built": resolved.get("year_built") or (result_data or {}).get("year_built"),
        "sqft": resolved.get("bldg_area_sqft") or (result_data or {}).get("bldg_area_sqft"),
        "floors": resolved.get("num_floors") or (result_data or {}).get("num_floors"),
        "job_type": (takeoff or {}).get("job_type") or resolved.get("job_type") or "Alteration",
        "permit_cost": resolved.get("initial_cost_usd"),
    }

    trades = []
    if takeoff:
        for t in takeoff.get("trades", []):
            trades.append({
                "name": (t.get("name") or "").replace("_", " ").title(),
                "line_items": t.get("line_items", []),
                "total": t.get("pricing", {}).get("total", 0),
                "confidence": t.get("confidence", "medium"),
            })

    firm_name = firm_info.get("firm_name") or "—"
    firm_logo = firm_info.get("logo_url")
    date_str = datetime.date.today().strftime("%B %d, %Y")

    # Output paths
    RFPS_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = RFPS_DIR / f"{slug}_rfp.pdf"
    html_path = RFPS_DIR / f"{slug}_rfp.html"

    # Build HTML
    html_content = _build_html(project, trades, firm_name, firm_logo, date_str, tier)
    html_path.write_text(html_content, encoding="utf-8")

    # Build PDF
    _build_pdf(pdf_path, project, trades, firm_name, date_str, tier)

    sections = ["cover", "project_overview", "scope", "bid_form", "requirements", "payment", "submission"]
    return {
        "pdf_path": str(pdf_path),
        "html_path": str(html_path),
        "sections_populated": sections,
        "confidence": "high" if tier == "3" else "low",
        "tier": tier,
    }


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------------------
# HTML builder
# ---------------------------------------------------------------------------

def _build_html(
    project: dict,
    trades: list,
    firm_name: str,
    firm_logo: str | None,
    date_str: str,
    tier: str,
) -> str:
    h = html_mod.escape

    logo_html = ""
    if firm_logo:
        logo_html = f'<img src="{h(firm_logo)}" alt="Firm logo" style="max-height:60px;margin-bottom:12px;">'

    tier_notice = ""
    if tier == "1":
        tier_notice = (
            '<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;'
            'padding:12px;margin:16px 0;color:#92400E;font-size:13px;">'
            "<strong>Preliminary scope</strong> — subject to revision upon document review."
            "</div>"
        )

    # Trade scope rows
    scope_rows = ""
    bid_rows = ""
    grand_total = 0
    for trade in trades:
        total = trade.get("total", 0)
        grand_total += total
        scope_rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB;">{h(trade['name'])}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB;text-align:right;">{_usd(total)}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #E5E7EB;text-align:center;">
            <span style="background:#F3F4F6;padding:2px 8px;border-radius:12px;font-size:11px;">{h(trade.get('confidence','medium'))}</span>
          </td>
        </tr>"""
        for li in trade.get("line_items", []):
            item_name = (li.get("item") or "").replace("_", " ").title()
            bid_rows += f"""
            <tr>
              <td style="padding:6px 12px;border-bottom:1px solid #F3F4F6;">{h(item_name)}</td>
              <td style="padding:6px 12px;border-bottom:1px solid #F3F4F6;text-align:right;">{li.get('quantity', 0):,.0f}</td>
              <td style="padding:6px 12px;border-bottom:1px solid #F3F4F6;">{h(li.get('unit', 'EA'))}</td>
              <td style="padding:6px 12px;border-bottom:1px solid #F3F4F6;text-align:right;">{_usd(li.get('unit_rate'))}</td>
              <td style="padding:6px 12px;border-bottom:1px solid #F3F4F6;text-align:right;">{_usd(li.get('subtotal'))}</td>
            </tr>"""

    if not trades:
        scope_rows = '<tr><td colspan="3" style="padding:12px;color:#9CA3AF;">Scope to be determined from document review.</td></tr>'
        bid_rows = '<tr><td colspan="5" style="padding:12px;color:#9CA3AF;">Line items pending takeoff analysis.</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RFP — {h(project['address'])}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1A1A2E; margin: 0; padding: 24px; background: #F4F5F7; }}
  .rfp {{ max-width: 800px; margin: 0 auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); overflow: hidden; }}
  .cover {{ background: #1A1A2E; color: #fff; padding: 40px; }}
  .cover h1 {{ font-size: 24px; margin: 0 0 8px; }}
  .cover .firm {{ color: rgba(255,255,255,0.7); font-size: 14px; }}
  .cover .date {{ color: rgba(255,255,255,0.5); font-size: 12px; margin-top: 12px; }}
  .cover .prepared {{ color: #E8621A; font-size: 11px; margin-top: 16px; text-transform: uppercase; letter-spacing: 0.05em; }}
  section {{ padding: 24px 40px; border-bottom: 1px solid #E5E7EB; }}
  section:last-child {{ border-bottom: none; }}
  h2 {{ font-size: 16px; color: #1A1A2E; margin: 0 0 12px; }}
  .detail-row {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #F3F4F6; font-size: 13px; }}
  .detail-label {{ color: #6B7280; }}
  .detail-value {{ font-weight: 600; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; padding: 8px 12px; background: #F9FAFB; border-bottom: 1px solid #E5E7EB; font-size: 11px; text-transform: uppercase; color: #6B7280; }}
  .grand-total {{ font-size: 18px; font-weight: 700; text-align: right; padding: 16px 12px; }}
  .note {{ font-size: 13px; color: #6B7280; line-height: 1.6; }}
</style>
</head>
<body>
<div class="rfp">
  <!-- Cover -->
  <div class="cover">
    {logo_html}
    <h1>Request for Proposal</h1>
    <div style="font-size:18px;margin:8px 0;">{h(project['address'])}</div>
    <div class="firm">Prepared for: {h(firm_name)}</div>
    <div class="date">{h(date_str)}</div>
    <div class="prepared">Prepared by Drafted</div>
  </div>

  {tier_notice}

  <!-- Project Overview -->
  <section>
    <h2>Project Overview</h2>
    <div class="detail-row"><span class="detail-label">Address</span><span class="detail-value">{h(project['address'])}</span></div>
    <div class="detail-row"><span class="detail-label">Year Built</span><span class="detail-value">{project.get('year_built') or '—'}</span></div>
    <div class="detail-row"><span class="detail-label">Building Area</span><span class="detail-value">{'{:,.0f}'.format(project.get('sqft') or 0)} sqft</span></div>
    <div class="detail-row"><span class="detail-label">Floors</span><span class="detail-value">{project.get('floors') or '—'}</span></div>
    <div class="detail-row"><span class="detail-label">Job Type</span><span class="detail-value">{h(project.get('job_type') or '—')}</span></div>
    <div class="detail-row"><span class="detail-label">Estimated Project Cost</span><span class="detail-value">{_usd(project.get('permit_cost'))}</span></div>
  </section>

  <!-- Scope of Work -->
  <section>
    <h2>Scope of Work</h2>
    <table>
      <thead><tr><th>Trade</th><th style="text-align:right;">Estimated Value</th><th style="text-align:center;">Confidence</th></tr></thead>
      <tbody>{scope_rows}</tbody>
    </table>
    <div class="grand-total">Total Estimate: {_usd(grand_total)}</div>
  </section>

  <!-- Bid Form -->
  <section>
    <h2>Bid Form</h2>
    <table>
      <thead><tr><th>Item</th><th style="text-align:right;">Qty</th><th>Unit</th><th style="text-align:right;">Unit Cost</th><th style="text-align:right;">Total</th></tr></thead>
      <tbody>{bid_rows}</tbody>
    </table>
  </section>

  <!-- Contractor Requirements -->
  <section>
    <h2>Contractor Requirements</h2>
    <p class="note">{h(CONTRACTOR_REQS)}</p>
  </section>

  <!-- Payment Terms -->
  <section>
    <h2>Payment Terms</h2>
    <p class="note">{h(PAYMENT_TERMS)}</p>
  </section>

  <!-- Submission Instructions -->
  <section>
    <h2>Submission Instructions</h2>
    <p class="note">Please submit your bid by <strong>[DEADLINE]</strong> to <strong>[CONTACT]</strong>.</p>
    <p class="note">Accepted formats: PDF, Excel. Include proof of insurance and NYC DOB registration.</p>
  </section>
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

def _build_pdf(
    out_path: Path,
    project: dict,
    trades: list,
    firm_name: str,
    date_str: str,
    tier: str,
) -> None:
    """Generate RFP PDF using ReportLab."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(out_path), pagesize=LETTER,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmallGray", parent=styles["BodyText"], fontSize=9, textColor=colors.gray))

    story = []

    # Cover
    story.append(Paragraph("Request for Proposal", styles["Title"]))
    story.append(Paragraph(project["address"], styles["Heading2"]))
    story.append(Paragraph(f"Prepared for: {firm_name}", styles["SmallGray"]))
    story.append(Paragraph(f"{date_str} — Prepared by Drafted", styles["SmallGray"]))
    story.append(Spacer(1, 24))

    if tier == "1":
        story.append(Paragraph(
            "<i>Preliminary scope — subject to revision upon document review.</i>",
            styles["SmallGray"],
        ))
        story.append(Spacer(1, 12))

    # Project overview
    story.append(Paragraph("Project Overview", styles["Heading2"]))
    overview_data = [
        ["Address", project["address"]],
        ["Year Built", str(project.get("year_built") or "—")],
        ["Building Area", f"{(project.get('sqft') or 0):,.0f} sqft"],
        ["Floors", str(project.get("floors") or "—")],
        ["Job Type", project.get("job_type") or "—"],
        ["Estimated Cost", _usd(project.get("permit_cost"))],
    ]
    t = Table(overview_data, colWidths=[2 * inch, 4.5 * inch])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.gray),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.Color(0.9, 0.9, 0.9)),
    ]))
    story.append(t)
    story.append(Spacer(1, 18))

    # Scope of work
    if trades:
        story.append(Paragraph("Scope of Work", styles["Heading2"]))
        scope_data = [["Trade", "Estimated Value", "Confidence"]]
        grand = 0
        for trade in trades:
            total = trade.get("total", 0)
            grand += total
            scope_data.append([trade["name"], _usd(total), trade.get("confidence", "medium")])
        scope_data.append(["TOTAL", _usd(grand), ""])
        t = Table(scope_data, colWidths=[3 * inch, 2 * inch, 1.5 * inch])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.96, 0.96, 0.96)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.Color(0.9, 0.9, 0.9)),
            ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ]))
        story.append(t)
        story.append(Spacer(1, 18))

    # Bid form
    if trades:
        story.append(Paragraph("Bid Form", styles["Heading2"]))
        bid_data = [["Item", "Qty", "Unit", "Unit Cost", "Total"]]
        for trade in trades:
            for li in trade.get("line_items", []):
                item_name = (li.get("item") or "").replace("_", " ").title()
                bid_data.append([
                    item_name,
                    f"{li.get('quantity', 0):,.0f}",
                    li.get("unit", "EA"),
                    _usd(li.get("unit_rate")),
                    _usd(li.get("subtotal")),
                ])
        t = Table(bid_data, colWidths=[2.5 * inch, 0.8 * inch, 0.6 * inch, 1.2 * inch, 1.4 * inch])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.96, 0.96, 0.96)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.Color(0.95, 0.95, 0.95)),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("ALIGN", (3, 0), (4, -1), "RIGHT"),
        ]))
        story.append(t)
        story.append(Spacer(1, 18))

    # Requirements + terms
    story.append(Paragraph("Contractor Requirements", styles["Heading2"]))
    story.append(Paragraph(CONTRACTOR_REQS, styles["BodyText"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Payment Terms", styles["Heading2"]))
    story.append(Paragraph(PAYMENT_TERMS, styles["BodyText"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Submission Instructions", styles["Heading2"]))
    story.append(Paragraph(
        "Please submit your bid by <b>[DEADLINE]</b> to <b>[CONTACT]</b>. "
        "Accepted formats: PDF, Excel. Include proof of insurance and NYC DOB registration.",
        styles["BodyText"],
    ))

    doc.build(story)
