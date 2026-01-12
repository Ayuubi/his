# apps/his/his/api/lis.py
import re
import math
import frappe
from datetime import datetime
from io import BytesIO

# =========================
# Helpers & small utilities
# =========================

def _iter_dept_groups(doc):
    """Yield (dept, [tests]) for the child table, accepting multiple fieldname variants."""
    rows = getattr(doc, "lab_test", None) or getattr(doc, "lab_tests", None) or []
    if not rows:
        frappe.throw("No Lab Tests on this Sample.")
    grouped = {}
    for r in rows:
        dept = (
            getattr(r, "lab_department", None)
            or getattr(r, "lab__department", None)
            or getattr(r, "department", None)
            or "UNKNOWN"
        )
        dept = str(dept).strip()
        test = (getattr(r, "lab_test", None) or getattr(r, "item", None) or "")
        test = str(test).strip()
        if not test:
            continue
        grouped.setdefault(dept, []).append(test)
    return grouped.items()

def _lab_number_from_name(doc_name: str) -> str:
    """SAM-00009-CARD -> Lab-00009; if no digits, fall back to doc_name."""
    m = re.search(r'(\d+)', doc_name or "")
    return f"Lab-{m.group(1)}" if m else (doc_name or "")

def _digits_only_from_name(doc_name: str) -> str:
    """SAM-00009-CARD -> 00009 (barcode payload)."""
    m = re.search(r'(\d+)', doc_name or "")
    return m.group(1) if m else (doc_name or "")

def _normalize_pid(pid_raw) -> str:
    """Ensure PID shows as 'PID-#####' if a value exists."""
    if not pid_raw:
        return ""
    s = str(pid_raw).strip()
    return s if s.upper().startswith("PID-") else f"PID-{s}"

def _get_token(doc, dept: str = "") -> str:
    """Return a token/queue number if present on the parent doc."""
    return (
        getattr(doc, "token_no", None)
        or getattr(doc, "token_number", None)
        or getattr(doc, "token_no_for_cbc", None)
        or ""
    )

# Single numeric barcode on all labels (no suffixes)
USE_SUFFIX = False   # we’re using digits-only from doc.name

# =========================
# ZPL (Zebra) label version
# =========================

# Label logical width in dots and centered text block width (keep in sync with ^PW and ^FB)
_ZPL_PW = 400
_ZPL_LEFT_MARGIN = 20
_ZPL_CENTER_WIDTH = 360  # we center text inside this box starting at x=20

# Barcode visuals (module width in dots, height in dots)
_ZPL_BAR_W = 2     # ^BY w (2 dots per module ~ good on 203dpi Zebra)
_ZPL_BAR_H = 70    # ^BC height

# Small centering tweak (positive moves the barcode RIGHT)
_ZPL_BAR_CENTER_ADJ = 10  # try 0..10; set to 0 if you like the math-only centering

def _estimate_code128_width_dots(value: str, w: int) -> int:
    """
    Rough width estimation for Code128 in 'modules':
      - Each data symbol: 11 modules
      - Start + Checksum: 2 symbols -> 22 modules
      - Stop: 13 modules
      - Quiet zones: ~10 modules each side (conservative)
    Total modules ≈ 11*len(value) + 22 + 13 + 20
    Width (dots) = modules * w
    """
    n = len(value or "")
    modules = 11 * n + 22 + 13 + 16  # quiet zones total ≈ 16 (slightly tighter than before)
    return modules * w

def _zpl_label(barcode_value, patient_name, pid_display, lab_no, dept, token_no):
    company = frappe.db.get_single_value('Global Defaults', 'default_company') or 'LAB'

    # center barcode inside the same 360-dot box as text
    bar_w_dots = _estimate_code128_width_dots(barcode_value, _ZPL_BAR_W)
    inner_left = _ZPL_LEFT_MARGIN
    inner_w = _ZPL_CENTER_WIDTH
    x_bar = inner_left + max(0, int((inner_w - bar_w_dots) / 2)) + _ZPL_BAR_CENTER_ADJ

    return f"""^XA
^CI28
^PW{_ZPL_PW}
^LH0,0
^FO{_ZPL_LEFT_MARGIN},15^A0N,26,26^FB{_ZPL_CENTER_WIDTH},1,0,C^FD{company} LAB^FS
^FO{_ZPL_LEFT_MARGIN},43^A0N,26,26^FB{_ZPL_CENTER_WIDTH},1,0,C^FD{patient_name}^FS
^FO{_ZPL_LEFT_MARGIN},69^A0N,24,24^FB{_ZPL_CENTER_WIDTH},1,0,C^FD{pid_display} / {lab_no}^FS
^BY{_ZPL_BAR_W}
^FO{x_bar},100^BCN,{_ZPL_BAR_H},N,N,N^FD{barcode_value}^FS
^FO{_ZPL_LEFT_MARGIN},178^A0N,22,22^FB{_ZPL_CENTER_WIDTH},1,0,C^FD{dept.upper()} / NO: {token_no}^FS
^XZ"""


@frappe.whitelist()
def print_barcodes(sample: str):
    """Generate ZPL with one label per department. Barcode = digits-only from doc.name (centered)."""
    doc = frappe.get_doc("Sample Collection", sample)

    accession     = getattr(doc, "sample_id", None) or doc.name
    pid_display   = _normalize_pid(getattr(doc, "patient", None) or getattr(doc, "patient_id", "") or "")
    patient_name  = getattr(doc, "patient_name", "") or ""
    lab_no        = _lab_number_from_name(doc.name)
    token_no      = _get_token(doc, "")

    barcode_numeric = _digits_only_from_name(doc.name)

    zpl_labels = []
    for dept, _tests in _iter_dept_groups(doc):
        zpl_labels.append(_zpl_label(barcode_numeric, patient_name, pid_display, lab_no, dept, token_no))

    content = "\n".join(zpl_labels).encode("utf-8")
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": f"{accession}_labels.zpl",
        "is_private": 1,
        "content": content
    }).insert(ignore_permissions=True)
    return {"file_url": file_doc.file_url}

# ===============================
# PDF (ReportLab) label version
# ===============================

@frappe.whitelist()
def print_barcodes_pdf(sample: str):
    """Generate a PDF with one label per department; center all text and barcode."""
    doc = frappe.get_doc("Sample Collection", sample)

    accession    = getattr(doc, "sample_id", None) or doc.name
    pid_display  = _normalize_pid(getattr(doc, "patient", None) or getattr(doc, "patient_id", "") or "")
    patient_name = getattr(doc, "patient_name", "") or ""
    lab_no       = _lab_number_from_name(doc.name)
    token_no     = _get_token(doc, "")
    collected_dt = getattr(doc, "collection_datetime", None) or datetime.now()

    barcode_numeric = _digits_only_from_name(doc.name)

    try:
        from reportlab.pdfgen import canvas
        from reportlab.graphics.barcode import code128
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        #  from reportlab.lib.units import mm
    except Exception:
        frappe.throw("ReportLab is required. Run: bench pip install reportlab")

    company = frappe.db.get_single_value('Global Defaults', 'default_company') or 'LAB'
    buf = BytesIO()
    page_w, page_h = A4
    c = canvas.Canvas(buf, pagesize=A4)

    # Label size (adjust if your physical label differs)
    margin  = 12 * mm
    # margin  = 12 * mm
    # label_w = 80 * mm
    label_w = 50 * mm
    # label_h = 42 * mm
    label_h = 43 * mm
    gap_y   = 6 * mm

    x = margin
    y = page_h - margin - label_h

    def cx():
        return x + label_w / 2.0  # center X inside the label

    def draw_centered(text: str, y_pos: float, font: str, size: float):
        c.setFont(font, size)
        w = c.stringWidth(text, font, size)
        c.drawString(cx() - w / 2.0, y_pos, text)

    def draw_label(dept):
        nonlocal x, y
        c.roundRect(x, y, label_w, label_h, 2 * mm, stroke=1, fill=0)

        draw_centered(f"{company} LAB",            y + label_h - 6.0 * mm,  "Helvetica-Bold", 10)
        draw_centered(patient_name[:42],           y + label_h - 13.5 * mm, "Helvetica-Bold", 9.5)
        draw_centered(f"{pid_display} / {lab_no}", y + label_h - 20.0 * mm, "Helvetica",      8.5)

        # Barcode (centered, no human-readable line)
        b = code128.Code128(barcode_numeric, barWidth=0.36 * mm, barHeight=14 * mm, humanReadable=False)
        try:
            bx = cx() - (b.width / 2.0)
        except Exception:
            bx = x + 3 * mm
        by = y + 7 * mm
        b.drawOn(c, bx, by)

        # Bottom centered line
        draw_centered(f"{dept.upper()} / NO: {token_no}", y + 3.0 * mm, "Helvetica", 8.5)

        # Next slot
        new_y = y - (label_h + gap_y)
        if new_y < margin:
            c.showPage()
            y = page_h - margin - label_h
        else:
            y = new_y

    for dept, _tests in _iter_dept_groups(doc):
        draw_label(dept)

    c.save()
    pdf_bytes = buf.getvalue()
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": f"{accession}_labels.pdf",
        "is_private": 1,
        "content": pdf_bytes
    }).insert(ignore_permissions=True)
    return {"file_url": file_doc.file_url}

# ===============================
# Demo API for your Windows listener
# ===============================

@frappe.whitelist()
def get_for_instrument(sample_id: str, instrument: str):
    """
    Simple demo API so your Windows listener can test the round-trip.
    Replace later with real lookups and analyzer-code mapping.
    """
    bench_tests = {
        "SEROLOGY": ["HCVAB", "HBSAG", "RVI"],
        "HEMATOLOGY": ["ABO GROUP/RH", "CBC"],
        "COAG": ["APTT", "PT", "INR"],
    }
    tests = bench_tests.get((instrument or "").upper(), [])
    base_id = sample_id.split("-")[0] if sample_id else ""
    return {
        "sample_id": sample_id,
        "base_id": base_id,
        "instrument": instrument,
        "patient_name": "Demo Patient",
        "pid": "PID-000123",
        "tests": [{"code": t} for t in tests],
    }
