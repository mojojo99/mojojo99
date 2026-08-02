"""PDF generation for quotations/proposals and invoices (reportlab)."""

import re
from datetime import date, timedelta

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from . import config

_ACCENT = colors.HexColor("#1a3c6e")
_LIGHT = colors.HexColor("#eef2f8")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "client"


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("DocTitle", parent=ss["Title"], textColor=_ACCENT, alignment=0))
    ss.add(ParagraphStyle("Small", parent=ss["Normal"], fontSize=8, textColor=colors.grey))
    ss.add(ParagraphStyle("H", parent=ss["Heading2"], textColor=_ACCENT))
    return ss


def _header(story, ss, doc_title: str, ref: str):
    story.append(Paragraph(config.COMPANY_NAME, ss["DocTitle"]))
    contact = " · ".join(
        x for x in (config.COMPANY_ADDRESS, config.COMPANY_PHONE, config.COMPANY_EMAIL, config.COMPANY_WEBSITE) if x
    )
    story.append(Paragraph(contact, ss["Small"]))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(doc_title, ss["H"]))
    story.append(Paragraph(f"Ref: {ref} &nbsp;&nbsp; Date: {date.today().isoformat()}", ss["Normal"]))
    story.append(Spacer(1, 4 * mm))


def _items_table(items: list[dict], ss) -> tuple[Table, float]:
    """items: [{description, quantity, unit_price}] → (table, total)."""
    rows = [["Description", "Qty", f"Unit ({config.CURRENCY})", f"Amount ({config.CURRENCY})"]]
    total = 0.0
    for it in items:
        qty = float(it.get("quantity", 1))
        unit = float(it.get("unit_price", 0))
        amount = qty * unit
        total += amount
        rows.append([Paragraph(str(it.get("description", "")), ss["Normal"]),
                     f"{qty:g}", f"{unit:,.2f}", f"{amount:,.2f}"])
    rows.append(["", "", Paragraph("<b>Total</b>", ss["Normal"]),
                 Paragraph(f"<b>{total:,.2f}</b>", ss["Normal"])])
    t = Table(rows, colWidths=[95 * mm, 15 * mm, 30 * mm, 30 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, _LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c8d2e0")),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t, total


def create_proposal_pdf(client_name: str, client_company: str, summary: str,
                        items: list[dict], notes: str = "") -> tuple[str, str]:
    """Returns (filename, absolute_path)."""
    ref = f"P-{date.today().strftime('%Y%m%d')}-{_slug(client_company or client_name)}"
    filename = f"{ref}.pdf"
    path = config.DOCUMENTS_DIR / filename
    ss = _styles()
    story = []
    _header(story, ss, "Training Proposal", ref)

    story.append(Paragraph(f"<b>Prepared for:</b> {client_name}"
                           + (f", {client_company}" if client_company else ""), ss["Normal"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Overview", ss["H"]))
    story.append(Paragraph(summary, ss["Normal"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Investment", ss["H"]))
    table, _ = _items_table(items, ss)
    story.append(table)
    story.append(Spacer(1, 4 * mm))
    if notes:
        story.append(Paragraph("Notes", ss["H"]))
        story.append(Paragraph(notes, ss["Normal"]))
        story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Terms: 50% deposit to confirm; balance due 7 days before the event. "
        "Prices exclude GST/VAT unless stated. Proposal valid for 30 days.", ss["Small"]))

    SimpleDocTemplate(str(path), pagesize=A4,
                      topMargin=18 * mm, bottomMargin=18 * mm).build(story)
    return filename, str(path)


def create_invoice_pdf(client_name: str, client_company: str, client_email: str,
                       items: list[dict], notes: str = "") -> tuple[str, str]:
    """Returns (filename, absolute_path)."""
    ref = f"INV-{date.today().strftime('%Y%m%d')}-{_slug(client_company or client_name)}"
    filename = f"{ref}.pdf"
    path = config.DOCUMENTS_DIR / filename
    ss = _styles()
    story = []
    _header(story, ss, "Invoice", ref)

    bill_to = f"<b>Bill to:</b> {client_name}"
    if client_company:
        bill_to += f", {client_company}"
    if client_email:
        bill_to += f" ({client_email})"
    story.append(Paragraph(bill_to, ss["Normal"]))
    story.append(Paragraph(f"<b>Due date:</b> {(date.today() + timedelta(days=14)).isoformat()}", ss["Normal"]))
    story.append(Spacer(1, 4 * mm))
    table, _ = _items_table(items, ss)
    story.append(table)
    story.append(Spacer(1, 4 * mm))
    if notes:
        story.append(Paragraph(notes, ss["Normal"]))
        story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        f"Please make payment to {config.COMPANY_NAME}. "
        "Payment terms: 14 days from invoice date.", ss["Small"]))

    SimpleDocTemplate(str(path), pagesize=A4,
                      topMargin=18 * mm, bottomMargin=18 * mm).build(story)
    return filename, str(path)
