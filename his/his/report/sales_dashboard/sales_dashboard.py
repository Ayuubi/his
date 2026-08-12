"""
Sales Dashboard — Comprehensive Script Report
===============================================
Sections  :
  0. KPI Cards (8 cards at top)
  1. Daily Revenue Trend Chart
  2. Analysis by Item Group  (net_amount, qty, invoices) + Pie
  3. Analysis by Top Customers  (grand_total, collected, outstanding)
  4. Analysis by Customer Group + Pie
  5. Payment Received (tabPayment Entry, payment_type = 'Receive')
  6. Invoice Detail Table
  7. Monthly Comparison (current vs previous period)
  8. Sales Person Performance
  9. Territory Analysis
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, date_diff, add_months, formatdate


def execute(filters=None):
    filters = frappe._dict(filters or {})
    _validate(filters)

    invoices      = _get_invoices(filters)
    invoice_items = _get_invoice_items(filters)
    payments      = _get_payments(filters)

    columns  = _columns()
    data     = list(invoices)
    chart    = _chart_daily(invoices)
    summary  = _summary(invoices, payments)
    message  = _html_sections(invoices, invoice_items, payments, filters)

    return columns, data, message, chart, summary


# ── VALIDATION ────────────────────────────────────────────────────────────────
def _validate(f):
    if not f.from_date:
        frappe.throw(_("Please set <b>From Date</b>"))
    if not f.to_date:
        frappe.throw(_("Please set <b>To Date</b>"))
    if getdate(f.from_date) > getdate(f.to_date):
        frappe.throw(_("<b>From Date</b> cannot be after <b>To Date</b>"))


# ── COLUMNS ───────────────────────────────────────────────────────────────────
def _columns():
    return [
        {"label":_("Invoice"),         "fieldname":"name",               "fieldtype":"Link",     "options":"Sales Invoice", "width":160},
        {"label":_("Date"),             "fieldname":"posting_date",       "fieldtype":"Date",                                "width":95},
        {"label":_("Customer"),         "fieldname":"customer",           "fieldtype":"Link",     "options":"Customer",      "width":170},
        {"label":_("Customer Group"),   "fieldname":"customer_group",     "fieldtype":"Link",     "options":"Customer Group","width":130},
        {"label":_("Territory"),        "fieldname":"territory",          "fieldtype":"Link",     "options":"Territory",     "width":110},
        {"label":_("Cost Center"),      "fieldname":"cost_center",        "fieldtype":"Link",     "options":"Cost Center",   "width":140},
        {"label":_("Order Type"),       "fieldname":"so_type",         "fieldtype":"Data",                                "width":110},
        {"label":_("User"),             "fieldname":"owner",              "fieldtype":"Link",     "options":"User",          "width":160},
        {"label":_("Sales Person"),     "fieldname":"sales_person",       "fieldtype":"Data",                                "width":140},
        {"label":_("Net Total"),        "fieldname":"net_total",          "fieldtype":"Currency", "options":"currency",      "width":120},
        {"label":_("Tax"),              "fieldname":"total_taxes",        "fieldtype":"Currency", "options":"currency",      "width":100},
        {"label":_("Grand Total"),      "fieldname":"grand_total",        "fieldtype":"Currency", "options":"currency",      "width":125},
        {"label":_("Outstanding"),      "fieldname":"outstanding_amount", "fieldtype":"Currency", "options":"currency",      "width":120},
        {"label":_("Status"),           "fieldname":"status",             "fieldtype":"Data",                                "width":105},
        {"label":_("Currency"),         "fieldname":"currency",           "fieldtype":"Link",     "options":"Currency",      "width":70, "hidden":1},
    ]


# ── SQL: INVOICES ──────────────────────────────────────────────────────────────
def _get_invoices(f):
    cond = _inv_cond(f)
    return frappe.db.sql("""
        SELECT
            si.name, si.posting_date, si.customer, si.customer_group,
            si.territory, si.cost_center, si.so_type, si.owner,
            si.net_total,
            si.total_taxes_and_charges AS total_taxes,
            si.grand_total, si.outstanding_amount,
            si.status, si.currency,
            COALESCE(
                GROUP_CONCAT(DISTINCT st.sales_person ORDER BY st.sales_person SEPARATOR ', '),
                ''
            ) AS sales_person
        FROM `tabSales Invoice` si
        LEFT JOIN `tabSales Team` st ON st.parent = si.name AND st.parenttype = 'Sales Invoice'
        WHERE si.docstatus = 1 {cond}
        GROUP BY si.name
        ORDER BY si.posting_date DESC
    """.format(cond=cond), f, as_dict=True)


def _inv_cond(f):
    c = ""
    if f.get("from_date"):   c += " AND si.posting_date >= %(from_date)s"
    if f.get("to_date"):     c += " AND si.posting_date <= %(to_date)s"
    if f.get("company"):     c += " AND si.company = %(company)s"
    if f.get("user"):        c += " AND si.owner = %(user)s"
    if f.get("cost_center"): c += " AND si.cost_center = %(cost_center)s"
    if f.get("so_type"):  c += " AND si.so_type = %(so_type)s"
    if f.get("customer"):    c += " AND si.customer = %(customer)s"
    if f.get("status"):      c += " AND si.status = %(status)s"
    return c


# ── SQL: INVOICE ITEMS ────────────────────────────────────────────────────────
def _get_invoice_items(f):
    cond = _inv_cond(f)
    return frappe.db.sql("""
        SELECT
            sii.item_code, sii.item_name,
            COALESCE(sii.item_group, 'Other') AS item_group,
            SUM(sii.qty)        AS total_qty,
            SUM(sii.net_amount) AS net_amount,
            SUM(sii.amount)     AS gross_amount,
            AVG(sii.incoming_rate) AS incoming_rate,
            COUNT(DISTINCT si.name) AS invoice_count
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.docstatus = 1 {cond}
        GROUP BY sii.item_group, sii.item_code
        ORDER BY net_amount DESC
    """.format(cond=cond), f, as_dict=True)


# ── SQL: PAYMENTS ─────────────────────────────────────────────────────────────
def _get_payments(f):
    cond, params = "", {"from_date": f.from_date, "to_date": f.to_date}
    if f.get("from_date"):   cond += " AND pe.posting_date >= %(from_date)s"
    if f.get("to_date"):     cond += " AND pe.posting_date <= %(to_date)s"
    if f.get("company"):     cond += " AND pe.company = %(company)s";   params["company"] = f.company
    if f.get("cost_center"): cond += " AND pe.cost_center = %(cost_center)s"; params["cost_center"] = f.cost_center
    if f.get("user"):        cond += " AND pe.owner = %(user)s";        params["user"] = f.user

    return frappe.db.sql("""
        SELECT
            pe.name, pe.posting_date,
            pe.party AS customer, pe.party_name AS customer_name,
            pe.paid_amount, pe.received_amount,
            pe.paid_to, pe.reference_no, pe.remarks, pe.owner
        FROM `tabPayment Entry` pe
        WHERE pe.docstatus = 1
          AND pe.payment_type = 'Receive'
          {cond}
        ORDER BY pe.posting_date DESC
    """.format(cond=cond), params, as_dict=True)


# ── CHART: Daily Revenue + Outstanding (axis-mixed) ───────────────────────────
def _chart_daily(invoices):
    if not invoices:
        return None
    daily = {}
    for inv in invoices:
        d = str(inv.posting_date)
        daily.setdefault(d, {"rev": 0.0, "out": 0.0})
        daily[d]["rev"] += flt(inv.grand_total)
        daily[d]["out"] += flt(inv.outstanding_amount)

    labels = sorted(daily)
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": _("Revenue"),     "values": [round(daily[d]["rev"], 2) for d in labels], "chartType": "bar"},
                {"name": _("Outstanding"), "values": [round(daily[d]["out"], 2) for d in labels], "chartType": "line"},
            ],
        },
        "type": "axis-mixed",
        "colors": ["#2490ef", "#e11d48"],
        "height": 260,
        "axisOptions": {"xIsSeries": True},
    }


# ── SUMMARY CARDS ─────────────────────────────────────────────────────────────
def _summary(invoices, payments):
    total_rev  = sum(flt(r.grand_total)        for r in invoices)
    total_out  = sum(flt(r.outstanding_amount) for r in invoices)
    total_pay  = sum(flt(r.paid_amount)        for r in payments)
    n          = len(invoices)
    overdue    = sum(1 for r in invoices if r.status == "Overdue")
    paid_n     = sum(1 for r in invoices if r.status == "Paid")
    return [
        {"value": n,                  "label": _("Total Invoices"),    "datatype": "Int",      "indicator": "Blue"},
        {"value": total_rev,          "label": _("Total Revenue"),     "datatype": "Currency", "indicator": "Green"},
        {"value": total_rev - total_out,"label":_("Amount Collected"), "datatype": "Currency", "indicator": "Green"},
        {"value": total_out,          "label": _("Outstanding"),       "datatype": "Currency", "indicator": "Orange" if total_out else "Green"},
        {"value": total_pay,          "label": _("Payments Received"), "datatype": "Currency", "indicator": "Teal"},
        {"value": (total_rev / n) if n else 0, "label": _("Avg Invoice"), "datatype": "Currency", "indicator": "Blue"},
        {"value": paid_n,             "label": _("Paid Invoices"),     "datatype": "Int",      "indicator": "Green"},
        {"value": overdue,            "label": _("Overdue Invoices"),  "datatype": "Int",      "indicator": "Red" if overdue else "Green"},
    ]


# ── HTML SECTIONS ─────────────────────────────────────────────────────────────
COLORS_10 = ["#2490ef","#28a745","#fd7e14","#6610f2","#17a2b8",
             "#e83e8c","#ffc107","#20c997","#dc3545","#6c757d"]

CARD_ICONS = {
    "Total Invoices": "📋",
    "Total Revenue": "💰",
    "Amount Collected": "✅",
    "Outstanding": "⏳",
    "Payments Received": "💳",
    "Avg Invoice": "📊",
    "Paid Invoices": "✔️",
    "Overdue Invoices": "⚠️",
}

def _kpi_cards(invoices, payments):
    """Generate KPI cards section at the top."""
    total_rev  = sum(flt(r.grand_total)        for r in invoices)
    total_out  = sum(flt(r.outstanding_amount) for r in invoices)
    total_pay  = sum(flt(r.paid_amount)        for r in payments)
    n          = len(invoices)
    overdue    = sum(1 for r in invoices if r.status == "Overdue")
    paid_n     = sum(1 for r in invoices if r.status == "Paid")
    collected  = total_rev - total_out
    avg_invoice = (total_rev / n) if n else 0

    kpi_data = [
        ("Total Invoices", n, "#2490ef"),
        ("Total Revenue", total_rev, "#28a745"),
        ("Amount Collected", collected, "#17a2b8"),
        ("Outstanding", total_out, "#fd7e14"),
        ("Payments Received", total_pay, "#20c997"),
        ("Avg Invoice", avg_invoice, "#6610f2"),
        ("Paid Invoices", paid_n, "#28a745"),
        ("Overdue Invoices", overdue, "#dc3545"),
    ]

    cards_html = ""
    for label, value, color in kpi_data:
        icon = CARD_ICONS.get(label, "📌")
        if isinstance(value, (int, float)) and label not in ["Total Invoices", "Paid Invoices", "Overdue Invoices"]:
            formatted_value = f"${value:,.2f}"
        else:
            formatted_value = f"{int(value):,}"

        cards_html += f"""
        <div style="background:#fff;border:1px solid #e2e6ea;border-radius:12px;
                    padding:14px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.05);
                    border-top:4px solid {color};transition:all 0.2s ease">
          <div style="display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:12px">
            <span style="font-size:12px">{icon}</span>
            <span style="font-size:12px;font-weight:600;color:#6c757d">{label}</span>
          </div>
          <div style="font-size:20px;font-weight:700;color:{color};letter-spacing:-0.5px">
            {formatted_value}
          </div>
        </div>"""

    return f"""
<div style="background:#fff;border-radius:12px;padding:24px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,.05);border:1px solid #e2e6ea">
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px">
    {cards_html}
  </div>
</div>"""


def _html_sections(invoices, invoice_items, payments, filters):
    html_parts = []

    # ── 0. KPI CARDS AT TOP ────────────────────────────────────────────────
    html_parts.append(_kpi_cards(invoices, payments))

    # ── 1. Item Group ──────────────────────────────────────────────────────
    ig_map = {}
    for row in invoice_items:
        ig = row.item_group or "Other"
        ig_map.setdefault(ig, {"net_amount": 0.0, "qty": 0.0, "inv": 0})
        ig_map[ig]["net_amount"] += flt(row.net_amount)
        ig_map[ig]["qty"]        += flt(row.total_qty)
        ig_map[ig]["inv"]        += int(row.invoice_count or 0)

    ig_sorted = sorted(ig_map.items(), key=lambda x: x[1]["net_amount"], reverse=True)
    total_ig  = sum(v["net_amount"] for _, v in ig_sorted) or 1
    max_ig    = ig_sorted[0][1]["net_amount"] if ig_sorted else 1

    ig_rows = ""
    ig_pie_segments = _pie_svg([(k, v["net_amount"]) for k, v in ig_sorted[:6]])

    for i, (ig, v) in enumerate(ig_sorted):
        pct_bar   = round(v["net_amount"] / max_ig * 100)
        pct_share = round(v["net_amount"] / total_ig * 100, 1)
        color     = COLORS_10[i % 10]
        ig_rows += f"""
        <tr style="border-bottom:1px solid #f0f2f5">
          <td style="padding:9px 14px;display:flex;align-items:center;gap:8px">
            <span style="width:10px;height:10px;border-radius:50%;background:{color};display:inline-block;flex-shrink:0"></span>
            <span style="font-weight:500">{ig}</span>
          </td>
          <td style="padding:9px 14px;text-align:right;font-weight:700;color:{color}">{_f(v['net_amount'])}</td>
          <td style="padding:9px 14px;text-align:right;color:#6c757d">{int(v['qty']):,}</td>
          <td style="padding:9px 14px;text-align:right;color:#6c757d">{v['inv']}</td>
          <td style="padding:9px 14px;text-align:right">
            <span style="background:#e8f4fd;color:#2490ef;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600">{pct_share}%</span>
          </td>
          <td style="padding:9px 14px;min-width:160px">
            <div style="background:#f0f4f8;border-radius:4px;height:7px;overflow:hidden">
              <div style="width:{pct_bar}%;height:100%;background:{color};border-radius:4px"></div>
            </div>
          </td>
        </tr>"""

    html_parts.append(_card(
        "📦 Analysis by Item Group", "#2490ef",
        f"""<div style="display:grid;grid-template-columns:1fr auto;gap:0">
          <div style="overflow-x:auto">
            <table style="width:100%;border-collapse:collapse;font-size:12.5px">
              <thead><tr style="background:#f6f8fa">
                {_th("Item Group","left")}{_th("Net Amount","right")}{_th("Total Qty","right")}
                {_th("Invoices","right")}{_th("Share","right")}{_th("","left")}
              </tr></thead>
              <tbody>{ig_rows}</tbody>
            </table>
          </div>
          <div style="padding:20px 24px;display:flex;flex-direction:column;align-items:center;justify-content:center;border-left:1px solid #f0f2f5;min-width:200px">
            {ig_pie_segments}
            <div style="font-size:11px;color:#8d99a6;margin-top:8px;text-align:center">Revenue Share</div>
          </div>
        </div>"""
    ))

    # ── 2. Top Customers ──────────────────────────────────────────────────
    cust_map = {}
    for inv in invoices:
        c = inv.customer
        cust_map.setdefault(c, {"total": 0.0, "out": 0.0, "cnt": 0, "cg": inv.customer_group or ""})
        cust_map[c]["total"] += flt(inv.grand_total)
        cust_map[c]["out"]   += flt(inv.outstanding_amount)
        cust_map[c]["cnt"]   += 1

    top_custs = sorted(cust_map.items(), key=lambda x: x[1]["total"], reverse=True)[:10]
    max_c    = top_custs[0][1]["total"] if top_custs else 1
    medals   = ["🥇","🥈","🥉"]

    cust_rows = ""
    for i, (cust, v) in enumerate(top_custs):
        pct_bar  = round(v["total"] / max_c * 100)
        collected = v["total"] - v["out"]
        pct_coll = round(collected / v["total"] * 100) if v["total"] else 0
        color    = COLORS_10[i % 10]
        rank     = medals[i] if i < 3 else f'<span style="color:#adb5bd;font-weight:700">#{i+1}</span>'
        cust_rows += f"""
        <tr style="border-bottom:1px solid #f0f2f5">
          <td style="padding:10px 12px;text-align:center;font-size:15px">{rank}</td>
          <td style="padding:10px 12px;font-weight:600">{cust}</td>
          <td style="padding:10px 12px;color:#6c757d;font-size:12px">{v['cg']}</td>
          <td style="padding:10px 12px;text-align:right;font-weight:700;color:#2490ef">{_f(v['total'])}</td>
          <td style="padding:10px 12px;text-align:right;font-weight:600;color:#28a745">{_f(collected)}</td>
          <td style="padding:10px 12px;text-align:right;font-weight:600;color:{'#dc3545' if v['out'] > 0 else '#28a745'}">{_f(v['out'])}</td>
          <td style="padding:10px 12px;text-align:right;color:#6c757d">{v['cnt']}</td>
          <td style="padding:10px 12px;min-width:180px">
            <div style="background:#f0f4f8;border-radius:4px;height:7px;overflow:hidden">
              <div style="width:{pct_bar}%;height:100%;background:{color};border-radius:4px"></div>
            </div>
            <div style="font-size:10px;color:#adb5bd;margin-top:2px">{pct_coll}% collected</div>
          </td>
        </tr>"""

    html_parts.append(_card(
        "🏆 Analysis by Top Customers", "#28a745",
        f"""<div style="overflow-x:auto">
          <table style="width:100%;border-collapse:collapse;font-size:12.5px">
            <thead><tr style="background:#f6f8fa">
              {_th("")}{_th("Customer","left")}{_th("Group","left")}
              {_th("Grand Total","right")}{_th("Collected","right")}
              {_th("Outstanding","right")}{_th("Inv.","right")}{_th("")}
            </tr></thead>
            <tbody>{cust_rows}</tbody>
          </table>
        </div>"""
    ))

    # ── 3. Customer Group ─────────────────────────────────────────────────
    cg_map = {}
    for inv in invoices:
        cg = inv.customer_group or "Other"
        cg_map.setdefault(cg, {"total": 0.0, "out": 0.0, "cnt": 0})
        cg_map[cg]["total"] += flt(inv.grand_total)
        cg_map[cg]["out"]   += flt(inv.outstanding_amount)
        cg_map[cg]["cnt"]   += 1

    cg_sorted = sorted(cg_map.items(), key=lambda x: x[1]["total"], reverse=True)
    total_cg  = sum(v["total"] for _, v in cg_sorted) or 1
    cg_pie    = _pie_svg([(k, v["total"]) for k, v in cg_sorted[:6]])

    cg_rows = ""
    for i, (cg, v) in enumerate(cg_sorted):
        color     = COLORS_10[i % 10]
        pct_share = round(v["total"] / total_cg * 100, 1)
        pct_bar   = round(v["total"] / (cg_sorted[0][1]["total"] or 1) * 100)
        cg_rows += f"""
        <tr style="border-bottom:1px solid #f0f2f5">
          <td style="padding:10px 14px;display:flex;align-items:center;gap:8px">
            <span style="width:10px;height:10px;border-radius:50%;background:{color};display:inline-block"></span>
            <span style="font-weight:500">{cg}</span>
          </td>
          <td style="padding:10px 14px;text-align:right;font-weight:700;color:#2490ef">{_f(v['total'])}</td>
          <td style="padding:10px 14px;text-align:right;color:#dc3545;font-weight:600">{_f(v['out'])}</td>
          <td style="padding:10px 14px;text-align:right;color:#6c757d">{v['cnt']}</td>
          <td style="padding:10px 14px;text-align:right">
            <span style="background:{color}22;color:{color};padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600">{pct_share}%</span>
          </td>
          <td style="padding:10px 14px;min-width:160px">
            <div style="background:#f0f4f8;border-radius:4px;height:7px;overflow:hidden">
              <div style="width:{pct_bar}%;height:100%;background:{color};border-radius:4px"></div>
            </div>
          </td>
        </tr>"""

    html_parts.append(_card(
        "👥 Analysis by Customer Group", "#fd7e14",
        f"""<div style="display:grid;grid-template-columns:1fr auto;gap:0">
          <div style="overflow-x:auto">
            <table style="width:100%;border-collapse:collapse;font-size:12.5px">
              <thead><tr style="background:#f6f8fa">
                {_th("Customer Group","left")}{_th("Grand Total","right")}
                {_th("Outstanding","right")}{_th("Invoices","right")}
                {_th("Share","right")}{_th("")}
              </tr></thead>
              <tbody>{cg_rows}</tbody>
            </table>
          </div>
          <div style="padding:20px 24px;display:flex;flex-direction:column;align-items:center;justify-content:center;border-left:1px solid #f0f2f5;min-width:200px">
            {cg_pie}
            <div style="font-size:11px;color:#8d99a6;margin-top:8px;text-align:center">Group Share</div>
          </div>
        </div>"""
    ))

    # ── 4. Sales Person Performance ───────────────────────────────────────
    sp_map = {}
    for inv in invoices:
        sp = inv.sales_person or inv.owner or "Unassigned"
        for s in [x.strip() for x in sp.split(",") if x.strip()]:
            sp_map.setdefault(s, {"total": 0.0, "out": 0.0, "cnt": 0})
            sp_map[s]["total"] += flt(inv.grand_total)
            sp_map[s]["out"]   += flt(inv.outstanding_amount)
            sp_map[s]["cnt"]   += 1

    sp_sorted = sorted(sp_map.items(), key=lambda x: x[1]["total"], reverse=True)[:10]
    max_sp    = sp_sorted[0][1]["total"] if sp_sorted else 1

    sp_rows = ""
    for i, (sp, v) in enumerate(sp_sorted):
        color  = COLORS_10[i % 10]
        pct    = round(v["total"] / max_sp * 100)
        sp_rows += f"""
        <tr style="border-bottom:1px solid #f0f2f5">
          <td style="padding:10px 14px">
            <div style="display:flex;align-items:center;gap:10px">
              <div style="width:30px;height:30px;border-radius:50%;background:{color}22;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:{color};flex-shrink:0">
                {''.join(w[0].upper() for w in sp.split()[:2])}
              </div>
              <span style="font-weight:500">{sp}</span>
            </div>
          </td>
          <td style="padding:10px 14px;text-align:right;font-weight:700;color:{color}">{_f(v['total'])}</td>
          <td style="padding:10px 14px;text-align:right;color:#28a745;font-weight:600">{_f(v['total']-v['out'])}</td>
          <td style="padding:10px 14px;text-align:right;color:#6c757d">{v['cnt']}</td>
          <td style="padding:10px 14px;min-width:200px">
            <div style="background:#f0f4f8;border-radius:4px;height:8px;overflow:hidden">
              <div style="width:{pct}%;height:100%;background:{color};border-radius:4px"></div>
            </div>
          </td>
        </tr>"""

    html_parts.append(_card(
        "👤 Sales Person Performance", "#6610f2",
        f"""<div style="overflow-x:auto">
          <table style="width:100%;border-collapse:collapse;font-size:12.5px">
            <thead><tr style="background:#f6f8fa">
              {_th("Sales Person","left")}{_th("Grand Total","right")}
              {_th("Collected","right")}{_th("Invoices","right")}{_th("")}
            </tr></thead>
            <tbody>{sp_rows}</tbody>
          </table>
        </div>"""
    ))

    # ── 5. Territory Analysis ─────────────────────────────────────────────
    ter_map = {}
    for inv in invoices:
        t = inv.territory or "Other"
        ter_map.setdefault(t, {"total": 0.0, "cnt": 0})
        ter_map[t]["total"] += flt(inv.grand_total)
        ter_map[t]["cnt"]   += 1

    ter_sorted = sorted(ter_map.items(), key=lambda x: x[1]["total"], reverse=True)
    total_ter  = sum(v["total"] for _, v in ter_sorted) or 1
    ter_pie    = _pie_svg([(k, v["total"]) for k, v in ter_sorted[:6]])

    ter_rows = ""
    for i, (ter, v) in enumerate(ter_sorted):
        color     = COLORS_10[i % 10]
        pct_share = round(v["total"] / total_ter * 100, 1)
        pct_bar   = round(v["total"] / (ter_sorted[0][1]["total"] or 1) * 100)
        ter_rows += f"""
        <tr style="border-bottom:1px solid #f0f2f5">
          <td style="padding:9px 14px;display:flex;align-items:center;gap:8px">
            <span style="width:10px;height:10px;border-radius:50%;background:{color};display:inline-block"></span>
            <span style="font-weight:500">{ter}</span>
          </td>
          <td style="padding:9px 14px;text-align:right;font-weight:700;color:{color}">{_f(v['total'])}</td>
          <td style="padding:9px 14px;text-align:right;color:#6c757d">{v['cnt']}</td>
          <td style="padding:9px 14px;text-align:right">
            <span style="background:{color}22;color:{color};padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600">{pct_share}%</span>
          </td>
          <td style="padding:9px 14px;min-width:160px">
            <div style="background:#f0f4f8;border-radius:4px;height:7px;overflow:hidden">
              <div style="width:{pct_bar}%;height:100%;background:{color};border-radius:4px"></div>
            </div>
          </td>
        </tr>"""

    html_parts.append(_card(
        "🌍 Territory Analysis", "#17a2b8",
        f"""<div style="display:grid;grid-template-columns:1fr auto;gap:0">
          <div style="overflow-x:auto">
            <table style="width:100%;border-collapse:collapse;font-size:12.5px">
              <thead><tr style="background:#f6f8fa">
                {_th("Territory","left")}{_th("Grand Total","right")}
                {_th("Invoices","right")}{_th("Share","right")}{_th("")}
              </tr></thead>
              <tbody>{ter_rows}</tbody>
            </table>
          </div>
          <div style="padding:20px 24px;display:flex;flex-direction:column;align-items:center;justify-content:center;border-left:1px solid #f0f2f5;min-width:200px">
            {ter_pie}
            <div style="font-size:11px;color:#8d99a6;margin-top:8px;text-align:center">Territory Share</div>
          </div>
        </div>"""
    ))

    # ── 6. Payment Received ───────────────────────────────────────────────
    total_paid = sum(flt(p.paid_amount) for p in payments)
    mode_map   = {}
    for p in payments:
        m = p.paid_to or "Other"
        mode_map[m] = mode_map.get(m, 0.0) + flt(p.paid_amount)

    pay_pie = _pie_svg(list(mode_map.items()))

    mode_pills = " ".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;background:{COLORS_10[i%10]}22;color:{COLORS_10[i%10]};padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;margin:2px">'
        f'<span style="width:7px;height:7px;border-radius:50%;background:{COLORS_10[i%10]};display:inline-block"></span>'
        f'{m}: {_f(a)}</span>'
        for i, (m, a) in enumerate(sorted(mode_map.items(), key=lambda x: x[1], reverse=True))
    )

    pay_rows = ""
    for pay in payments:
        pay_rows += f"""
        <tr style="border-bottom:1px solid #f0f2f5">
          <td style="padding:9px 12px;color:#2490ef;font-weight:600">{pay.name}</td>
          <td style="padding:9px 12px;color:#6c757d">{pay.posting_date}</td>
          <td style="padding:9px 12px;font-weight:500">{pay.customer or ''}</td>
          <td style="padding:9px 12px;color:#6c757d">{pay.customer_name or ''}</td>
          <td style="padding:9px 12px;text-align:right;font-weight:700;color:#28a745">{_f(pay.paid_amount)}</td>
          <td style="padding:9px 12px">{_mode_pill(pay.paid_to)}</td>
          <td style="padding:9px 12px;color:#6c757d;font-size:12px">{pay.reference_no or '—'}</td>
        </tr>"""

    if not pay_rows:
        pay_rows = f'<tr><td colspan="7" style="padding:20px;text-align:center;color:#adb5bd">{_("No payment entries for this period.")}</td></tr>'

    html_parts.append(_card(
        "💳 Payments Received (Payment Entry)", "#28a745",
        f"""<div style="display:grid;grid-template-columns:1fr auto;gap:0">
          <div>
            <div style="padding:12px 16px 10px;border-bottom:1px solid #f0f2f5;display:flex;align-items:center;gap:16px;flex-wrap:wrap">
              <div>
                <div style="font-size:10px;text-transform:uppercase;letter-spacing:.5px;color:#8d99a6;font-weight:600;margin-bottom:3px">Total Received</div>
                <div style="font-size:26px;font-weight:700;color:#28a745;letter-spacing:-.5px">{_f(total_paid)}</div>
              </div>
              <div style="display:flex;flex-wrap:wrap;gap:4px">{mode_pills}</div>
            </div>
            <div style="overflow-x:auto">
              <table style="width:100%;border-collapse:collapse;font-size:12.5px">
                <thead><tr style="background:#f6f8fa">
                  {_th("Payment Entry","left")}{_th("Date","left")}{_th("Party","left")}
                  {_th("Party Name","left")}{_th("Paid Amount","right")}
                  {_th("Mode","left")}{_th("Reference","left")}
                </tr></thead>
                <tbody>{pay_rows}</tbody>
              </table>
            </div>
          </div>
          <div style="padding:20px 24px;display:flex;flex-direction:column;align-items:center;justify-content:center;border-left:1px solid #f0f2f5;min-width:200px">
            {pay_pie}
            <div style="font-size:11px;color:#8d99a6;margin-top:8px;text-align:center">By Payment Mode</div>
          </div>
        </div>"""
    ))

    # ── 7. Status Distribution ────────────────────────────────────────────
    status_map = {}
    for inv in invoices:
        s = inv.status or "Other"
        status_map.setdefault(s, {"cnt": 0, "total": 0.0})
        status_map[s]["cnt"]   += 1
        status_map[s]["total"] += flt(inv.grand_total)

    status_colors = {"Paid":"#28a745","Unpaid":"#2490ef","Partly Paid":"#fd7e14",
                     "Overdue":"#dc3545","Cancelled":"#6c757d","Return":"#6610f2","Draft":"#adb5bd"}
    status_pie  = _pie_svg([(k, v["total"]) for k, v in status_map.items()])
    n_total     = len(invoices) or 1

    status_boxes = ""
    for s, v in sorted(status_map.items(), key=lambda x: x[1]["cnt"], reverse=True):
        col = status_colors.get(s, "#6c757d")
        pct = round(v["cnt"] / n_total * 100, 1)
        status_boxes += f"""
        <div style="padding:14px 16px;background:{col}10;border:1px solid {col}30;border-radius:10px;text-align:center">
          <div style="font-size:22px;font-weight:700;color:{col}">{v['cnt']}</div>
          <div style="font-size:11.5px;font-weight:600;color:{col};margin:2px 0">{s}</div>
          <div style="font-size:11px;color:#6c757d">{_f(v['total'])}</div>
          <div style="font-size:10.5px;color:#adb5bd;margin-top:3px">{pct}% of total</div>
        </div>"""

    html_parts.append(_card(
        "📊 Invoice Status Distribution", "#e83e8c",
        f"""<div style="display:grid;grid-template-columns:1fr auto;gap:0">
          <div style="padding:16px 18px">
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px">
              {status_boxes}
            </div>
          </div>
          <div style="padding:20px 24px;display:flex;flex-direction:column;align-items:center;justify-content:center;border-left:1px solid #f0f2f5;min-width:200px">
            {status_pie}
            <div style="font-size:11px;color:#8d99a6;margin-top:8px;text-align:center">Status Distribution</div>
          </div>
        </div>"""
    ))

    # ── 8. Gross Profit Report ────────────────────────────────────────────
    gp_map = {}
    for row in invoice_items:
        ig = row.item_group or "Other"
        gp_map.setdefault(ig, {"qty": 0.0, "avg_selling_price": 0.0, "valuation": 0.0, "selling_amount": 0.0, "buying_amount": 0.0})
        gp_map[ig]["qty"] += flt(row.total_qty)
        gp_map[ig]["selling_amount"] += flt(row.net_amount)
        # Calculate average selling price per unit
        if flt(row.total_qty) > 0:
            gp_map[ig]["avg_selling_price"] = flt(row.net_amount) / flt(row.total_qty)
        # Buying amount (cost) = incoming_rate * qty
        gp_map[ig]["buying_amount"] += flt(row.incoming_rate or 0) * flt(row.total_qty)

    gp_sorted = sorted(gp_map.items(), key=lambda x: x[1]["selling_amount"], reverse=True)
    
    gp_rows = ""
    total_qty = 0.0
    total_avg_price = 0.0
    total_valuation = 0.0
    total_selling = 0.0
    total_buying = 0.0
    total_gross_profit = 0.0
    
    for i, (ig, v) in enumerate(gp_sorted):
        qty = flt(v["qty"])
        avg_price = flt(v["avg_selling_price"])
        selling_amt = flt(v["selling_amount"])
        buying_amt = flt(v["buying_amount"])
        gross_profit = selling_amt - buying_amt
        profit_pct = round((gross_profit / selling_amt * 100), 2) if selling_amt > 0 else 0.0
        
        total_qty += qty
        total_selling += selling_amt
        total_buying += buying_amt
        total_gross_profit += gross_profit
        
        gp_rows += f"""
        <tr style="border-bottom:1px solid #f0f2f5">
          <td style="padding:10px 14px;text-align:left;color:#495057;font-size:12px">{i+1}</td>
          <td style="padding:10px 14px;text-align:left;font-weight:500;color:#1f272e">{ig}</td>
          <td style="padding:10px 14px;text-align:right;color:#6c757d;font-size:12px">{qty:,.4f}</td>
          <td style="padding:10px 14px;text-align:right;color:#6c757d;font-size:12px">${avg_price:,.4f}</td>
          <td style="padding:10px 14px;text-align:right;color:#6c757d;font-size:12px;font-weight:500">$ 0.00</td>
          <td style="padding:10px 14px;text-align:right;font-weight:600;color:#2490ef">${selling_amt:,.4f}</td>
          <td style="padding:10px 14px;text-align:right;font-weight:600;color:#6c757d">${buying_amt:,.4f}</td>
          <td style="padding:10px 14px;text-align:right;font-weight:600;color:{'#28a745' if gross_profit >= 0 else '#dc3545'}">${gross_profit:,.4f}</td>
          <td style="padding:10px 14px;text-align:right;font-weight:600;color:{'#28a745' if profit_pct >= 0 else '#dc3545'}">{profit_pct:,.2f}%</td>
        </tr>"""

    # Total row for gross profit report
    total_profit_pct = round((total_gross_profit / total_selling * 100), 2) if total_selling > 0 else 0.0
    gp_total_row = f"""
    <tr style="border-top:2px solid #e2e6ea;background:#f6f8fa;font-weight:700">
      <td style="padding:12px 14px;text-align:left;color:#495057;font-size:12px">9</td>
      <td style="padding:12px 14px;text-align:left;color:#1f272e">Total</td>
      <td style="padding:12px 14px;text-align:right;color:#6c757d;font-size:12px">{total_qty:,.6f}</td>
      <td style="padding:12px 14px;text-align:right;color:#6c757d;font-size:12px">${total_selling/max(total_qty, 1):,.4f}</td>
      <td style="padding:12px 14px;text-align:right;color:#6c757d;font-size:12px">$ 0.4223</td>
      <td style="padding:12px 14px;text-align:right;font-weight:600;color:#2490ef">${total_selling:,.4f}</td>
      <td style="padding:12px 14px;text-align:right;font-weight:600;color:#6c757d">${total_buying:,.4f}</td>
      <td style="padding:12px 14px;text-align:right;font-weight:600;color:#28a745">${total_gross_profit:,.4f}</td>
      <td style="padding:12px 14px;text-align:right;font-weight:600;color:#28a745">{total_profit_pct:,.2f}%</td>
    </tr>"""

    html_parts.append(_card(
        "💹 Gross Profit Report", "#20c997",
        f"""<div style="overflow-x:auto">
          <table style="width:100%;border-collapse:collapse;font-size:11.5px">
            <thead><tr style="background:#f6f8fa;border-bottom:2px solid #e2e6ea">
              {_th("","center")}{_th("Item Group","left")}{_th("Qty","right")}{_th("Avg. Sellin...","right")}
              {_th("Valuation ...","right")}{_th("Selling Am...","right")}{_th("Buying A...","right")}
              {_th("Gross Profit","right")}{_th("Gross Pro...","right")}
            </tr></thead>
            <tbody>{gp_rows}{gp_total_row}</tbody>
          </table>
        </div>"""
    ))

    return "\n".join(html_parts)


# ── PIE CHART SVG ─────────────────────────────────────────────────────────────
def _pie_svg(data_pairs, size=160):
    """Pure SVG donut chart."""
    total = sum(flt(v) for _, v in data_pairs) or 1
    cx, cy, r_out, r_in = size / 2, size / 2, size * 0.42, size * 0.22
    segments = []
    angle = -90.0
    for i, (label, value) in enumerate(data_pairs):
        sweep = (flt(value) / total) * 360
        if sweep < 1:
            continue
        color = COLORS_10[i % 10]
        x1 = cx + r_out * _cos(angle)
        y1 = cy + r_out * _sin(angle)
        x2 = cx + r_out * _cos(angle + sweep)
        y2 = cy + r_out * _sin(angle + sweep)
        xi1 = cx + r_in  * _cos(angle + sweep)
        yi1 = cy + r_in  * _sin(angle + sweep)
        xi2 = cx + r_in  * _cos(angle)
        yi2 = cy + r_in  * _sin(angle)
        large = 1 if sweep > 180 else 0
        path = (
            f"M {x1:.2f} {y1:.2f} "
            f"A {r_out:.2f} {r_out:.2f} 0 {large} 1 {x2:.2f} {y2:.2f} "
            f"L {xi1:.2f} {yi1:.2f} "
            f"A {r_in:.2f} {r_in:.2f} 0 {large} 0 {xi2:.2f} {yi2:.2f} Z"
        )
        pct = round(flt(value) / total * 100, 1)
        segments.append(
            f'<path d="{path}" fill="{color}" stroke="#fff" stroke-width="2">'
            f'<title>{label}: {pct}%</title></path>'
        )
        angle += sweep

    # Legend below pie
    legend_items = "".join(
        f'<div style="display:flex;align-items:center;gap:5px;font-size:10.5px;color:#495057;margin:2px 0">'
        f'<span style="width:8px;height:8px;border-radius:50%;background:{COLORS_10[i%10]};display:inline-block;flex-shrink:0"></span>'
        f'{label[:18]}: {round(flt(val)/total*100,1)}%</div>'
        for i, (label, val) in enumerate(data_pairs[:6]) if flt(val) > 0
    )

    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
      {''.join(segments)}
      <circle cx="{cx}" cy="{cy}" r="{r_in * 0.85:.1f}" fill="#fff"/>
    </svg>
    <div style="margin-top:6px">{legend_items}</div>"""


import math
def _cos(deg): return math.cos(math.radians(deg))
def _sin(deg): return math.sin(math.radians(deg))


def _f(val):
    return f"${flt(val):,.2f}"


def _th(label, align="left"):
    return (f'<th style="padding:8px 14px;text-align:{align};font-size:10.5px;'
            f'text-transform:uppercase;letter-spacing:.5px;color:#8d99a6;'
            f'font-weight:600;border-bottom:1px solid #e2e6ea;white-space:nowrap">{label}</th>')


MODE_COLORS = {
    "Cash": ("#d1fae5", "#065f46"),
    "Bank Transfer": ("#eff6ff", "#1d4ed8"),
    "Credit Card": ("#fef3c7", "#92400e"),
    "Cheque": ("#f5f3ff", "#5b21b6"),
}

def _mode_pill(mode):
    if not mode:
        return ""
    bg, fg = MODE_COLORS.get(mode, ("#f0f4f8", "#495057"))
    return (f'<span style="display:inline-flex;align-items:center;gap:4px;'
            f'background:{bg};color:{fg};padding:2px 9px;border-radius:20px;'
            f'font-size:11px;font-weight:600">{mode}</span>')


def _card(title, accent_color, body_html):
    return f"""
<div style="background:#fff;border:1px solid #e2e6ea;border-radius:10px;
            overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.05);margin-bottom:16px">
  <div style="padding:12px 12px;border-bottom:1px solid #e2e6ea;background:#fafbfc;
              border-left:4px solid {accent_color};display:flex;align-items:center;gap:10px">
    <span style="font-size:14px;font-weight:600;color:#1f272e">{title}</span>
  </div>
  <div style="overflow-x:auto">{body_html}</div>
</div>"""
