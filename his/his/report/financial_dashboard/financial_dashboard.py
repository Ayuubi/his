"""
Financial Dashboard — Frappe Script Report
===========================================
Module      : Accounts
Ref DocType : Sales Invoice

Sections:
  1.  P&L Summary Cards  (Income · Expense · Net Profit)
  2.  P&L Monthly Bar+Line Chart  (Income / Expense / Net Profit per month)
  3.  P&L Accounts Breakdown Chart  (top income & expense accounts)
  4.  Bank & Cash Balances  (opening, debit, credit, closing balance per account)
  5.  Accounts Receivable Summary Card
  6.  Top 10 Accounts Receivable Table  (customer, invoiced, paid, outstanding, ageing)
        — sourced from GL Entry grouped by party (covers journal + payment entries)
  7.  Accounts Payable Summary Card
  8.  Top 10 Accounts Payable Table     (supplier, billed, paid, outstanding, ageing)
        — sourced from GL Entry grouped by party (covers journal + payment entries)

Removed sections (by request):
  - 💹 Gross Profit Report — by Item Group
  - 💳 Payments Received
  - 📊 Invoice Status Distribution
  - 👤 Sales Person Performance
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate, fmt_money
import math


# ─────────────────────────────────────────────────────────────────────────────
def execute(filters=None):
    filters = frappe._dict(filters or {})
    _validate(filters)

    # ── Fetch all raw data ──
    invoices     = _get_invoices(filters)
    gl_income    = _get_gl_income(filters)
    gl_expense   = _get_gl_expense(filters)
    gl_ar        = _get_gl_ar_by_party(filters)
    gl_ap        = _get_gl_ap_by_party(filters)
    income_accs  = _get_income_accounts(filters)
    expense_accs = _get_expense_accounts(filters)
    gl_bank_cash = _get_bank_cash_accounts(filters)

    # ── Build report outputs ──
    columns = _columns()
    data    = list(invoices)
    chart   = _chart_monthly_pnl(gl_income, gl_expense)
    summary = _summary_cards(invoices, gl_income, gl_expense, gl_ar, gl_bank_cash)
    message = _build_html(
        invoices, gl_income, gl_expense,
        gl_ar, gl_ap, income_accs, expense_accs, gl_bank_cash, filters
    )

    return columns, data, message, chart, summary


# ─────────────────────────────────────────────────────────────────────────────
#  VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
def _validate(f):
    if not f.from_date:
        frappe.throw(_("Please set <b>From Date</b>"))
    if not f.to_date:
        frappe.throw(_("Please set <b>To Date</b>"))
    if getdate(f.from_date) > getdate(f.to_date):
        frappe.throw(_("<b>From Date</b> cannot be after <b>To Date</b>"))
    if not f.company:
        frappe.throw(_("Please set <b>Company</b>"))


# ─────────────────────────────────────────────────────────────────────────────
#  CURRENCY
# ─────────────────────────────────────────────────────────────────────────────
def _get_currency(f):
    """Resolve currency for money formatting (Company's default currency,
    falling back to the site's global default)."""
    if f.get("company"):
        company_currency = frappe.get_cached_value("Company", f.company, "default_currency")
        if company_currency:
            return company_currency
    return frappe.defaults.get_global_default("currency") or "USD"


# ─────────────────────────────────────────────────────────────────────────────
#  COLUMNS  (Invoice detail table shown at the bottom)
# ─────────────────────────────────────────────────────────────────────────────
def _columns():
    return [
        {"label": _("Invoice"),        "fieldname": "name",               "fieldtype": "Link",     "options": "Sales Invoice", "width": 160},
        {"label": _("Date"),           "fieldname": "posting_date",       "fieldtype": "Date",                                 "width": 95},
        {"label": _("Customer"),       "fieldname": "customer",           "fieldtype": "Link",     "options": "Customer",      "width": 170},
        {"label": _("Customer Group"), "fieldname": "customer_group",     "fieldtype": "Link",     "options": "Customer Group","width": 130},
        {"label": _("Cost Center"),    "fieldname": "cost_center",        "fieldtype": "Link",     "options": "Cost Center",   "width": 140},
        {"label": _("Sales Type"),     "fieldname": "so_type",            "fieldtype": "Data",                                 "width": 110},
        {"label": _("User"),           "fieldname": "owner",              "fieldtype": "Link",     "options": "User",          "width": 150},
        {"label": _("Net Total"),      "fieldname": "net_total",          "fieldtype": "Currency", "options": "currency",      "width": 120},
        {"label": _("Tax"),            "fieldname": "total_taxes",        "fieldtype": "Currency", "options": "currency",      "width": 100},
        {"label": _("Grand Total"),    "fieldname": "grand_total",        "fieldtype": "Currency", "options": "currency",      "width": 125},
        {"label": _("Outstanding"),    "fieldname": "outstanding_amount", "fieldtype": "Currency", "options": "currency",      "width": 120},
        {"label": _("Status"),         "fieldname": "status",             "fieldtype": "Data",                                 "width": 105},
        {"label": _("Currency"),       "fieldname": "currency",           "fieldtype": "Link",     "options": "Currency",      "width": 70,  "hidden": 1},
    ]


# ─────────────────────────────────────────────────────────────────────────────
#  SQL — Sales Invoices
# ─────────────────────────────────────────────────────────────────────────────
def _get_invoices(f):
    cond = ""
    if f.get("from_date"):   cond += " AND si.posting_date >= %(from_date)s"
    if f.get("to_date"):     cond += " AND si.posting_date <= %(to_date)s"
    if f.get("company"):     cond += " AND si.company = %(company)s"
    if f.get("cost_center"): cond += " AND si.cost_center = %(cost_center)s"

    return frappe.db.sql("""
        SELECT
            si.name, si.posting_date, si.customer, si.customer_group,
            si.territory, si.cost_center,
            si.so_type,
            si.owner,
            si.net_total,
            si.total_taxes_and_charges AS total_taxes,
            si.grand_total,
            si.outstanding_amount,
            si.status,
            si.currency,
            DATEDIFF(CURDATE(), si.due_date) AS due_days
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1 {cond}
        ORDER BY si.posting_date DESC
    """.format(cond=cond), f, as_dict=True)


# ─────────────────────────────────────────────────────────────────────────────
#  SQL — GL Income  (monthly totals)
# ─────────────────────────────────────────────────────────────────────────────
def _get_gl_income(f):
    cond = " AND gle.company = %(company)s"
    if f.get("from_date"):    cond += " AND gle.posting_date >= %(from_date)s"
    if f.get("to_date"):      cond += " AND gle.posting_date <= %(to_date)s"
    if f.get("cost_center"):  cond += " AND gle.cost_center = %(cost_center)s"
    if f.get("finance_book"):
        cond += (" AND (gle.finance_book = %(finance_book)s"
                 " OR gle.finance_book IS NULL OR gle.finance_book = '')")

    return frappe.db.sql("""
        SELECT
            DATE_FORMAT(gle.posting_date, '%%Y-%%m') AS ym,
            SUM(gle.credit - gle.debit)              AS amount
        FROM `tabGL Entry` gle
        INNER JOIN `tabAccount` acc ON acc.name = gle.account
        WHERE gle.is_cancelled = 0
          AND acc.root_type = 'Income'
          {cond}
        GROUP BY ym
        ORDER BY ym
    """.format(cond=cond), f, as_dict=True)


# ─────────────────────────────────────────────────────────────────────────────
#  SQL — GL Expense  (monthly totals)
# ─────────────────────────────────────────────────────────────────────────────
def _get_gl_expense(f):
    cond = " AND gle.company = %(company)s"
    if f.get("from_date"):    cond += " AND gle.posting_date >= %(from_date)s"
    if f.get("to_date"):      cond += " AND gle.posting_date <= %(to_date)s"
    if f.get("cost_center"):  cond += " AND gle.cost_center = %(cost_center)s"
    if f.get("finance_book"):
        cond += (" AND (gle.finance_book = %(finance_book)s"
                 " OR gle.finance_book IS NULL OR gle.finance_book = '')")

    return frappe.db.sql("""
        SELECT
            DATE_FORMAT(gle.posting_date, '%%Y-%%m') AS ym,
            SUM(gle.debit - gle.credit)              AS amount
        FROM `tabGL Entry` gle
        INNER JOIN `tabAccount` acc ON acc.name = gle.account
        WHERE gle.is_cancelled = 0
          AND acc.root_type = 'Expense'
          {cond}
        GROUP BY ym
        ORDER BY ym
    """.format(cond=cond), f, as_dict=True)


# ─────────────────────────────────────────────────────────────────────────────
#  SQL — Income Accounts Breakdown  (for P&L accounts chart)
# ─────────────────────────────────────────────────────────────────────────────
def _get_income_accounts(f):
    """
    Returns per-account income totals so we can render a breakdown chart/table.
    Groups by the leaf account name.
    """
    cond = " AND gle.company = %(company)s"
    if f.get("from_date"):    cond += " AND gle.posting_date >= %(from_date)s"
    if f.get("to_date"):      cond += " AND gle.posting_date <= %(to_date)s"
    if f.get("cost_center"):  cond += " AND gle.cost_center = %(cost_center)s"
    if f.get("finance_book"):
        cond += (" AND (gle.finance_book = %(finance_book)s"
                 " OR gle.finance_book IS NULL OR gle.finance_book = '')")

    return frappe.db.sql("""
        SELECT
            gle.account                          AS account,
            acc.account_name                     AS account_name,
            SUM(gle.credit - gle.debit)          AS amount
        FROM `tabGL Entry` gle
        INNER JOIN `tabAccount` acc ON acc.name = gle.account
        WHERE gle.is_cancelled = 0
          AND acc.root_type = 'Income'
          {cond}
        GROUP BY gle.account
        HAVING amount > 0
        ORDER BY amount DESC
    """.format(cond=cond), f, as_dict=True)


# ─────────────────────────────────────────────────────────────────────────────
#  SQL — Expense Accounts Breakdown  (for P&L accounts chart)
# ─────────────────────────────────────────────────────────────────────────────
def _get_expense_accounts(f):
    cond = " AND gle.company = %(company)s"
    if f.get("from_date"):    cond += " AND gle.posting_date >= %(from_date)s"
    if f.get("to_date"):      cond += " AND gle.posting_date <= %(to_date)s"
    if f.get("cost_center"):  cond += " AND gle.cost_center = %(cost_center)s"
    if f.get("finance_book"):
        cond += (" AND (gle.finance_book = %(finance_book)s"
                 " OR gle.finance_book IS NULL OR gle.finance_book = '')")

    return frappe.db.sql("""
        SELECT
            gle.account                          AS account,
            acc.account_name                     AS account_name,
            SUM(gle.debit - gle.credit)          AS amount
        FROM `tabGL Entry` gle
        INNER JOIN `tabAccount` acc ON acc.name = gle.account
        WHERE gle.is_cancelled = 0
          AND acc.root_type = 'Expense'
          {cond}
        GROUP BY gle.account
        HAVING amount > 0
        ORDER BY amount DESC
    """.format(cond=cond), f, as_dict=True)


# ─────────────────────────────────────────────────────────────────────────────
#  SQL — Bank & Cash Accounts  (opening balance + period debit/credit + closing)
#
#  Logic:
#    Bank/Cash accounts (acc.account_type IN ('Bank', 'Cash'))
#    Opening balance  = SUM(debit - credit) for all entries BEFORE from_date
#    Period debit/credit = SUM(debit), SUM(credit) between from_date and to_date
#    Closing balance  = opening + period_debit - period_credit
# ─────────────────────────────────────────────────────────────────────────────
def _get_bank_cash_accounts(f):
    base_cond = " AND gle.company = %(company)s"
    if f.get("cost_center"):  base_cond += " AND gle.cost_center = %(cost_center)s"
    if f.get("finance_book"):
        base_cond += (" AND (gle.finance_book = %(finance_book)s"
                      " OR gle.finance_book IS NULL OR gle.finance_book = '')")

    # Opening balance: everything posted strictly before the from_date
    opening_rows = frappe.db.sql("""
        SELECT
            gle.account                    AS account,
            SUM(gle.debit - gle.credit)    AS opening
        FROM `tabGL Entry` gle
        INNER JOIN `tabAccount` acc ON acc.name = gle.account
        WHERE gle.is_cancelled = 0
          AND acc.account_type IN ('Bank', 'Cash')
          AND gle.posting_date < %(from_date)s
          {cond}
        GROUP BY gle.account
    """.format(cond=base_cond), f, as_dict=True)
    opening_map = {r.account: flt(r.opening) for r in opening_rows}

    # Period movement
    period_cond = base_cond
    if f.get("from_date"): period_cond += " AND gle.posting_date >= %(from_date)s"
    if f.get("to_date"):   period_cond += " AND gle.posting_date <= %(to_date)s"

    period_rows = frappe.db.sql("""
        SELECT
            gle.account         AS account,
            acc.account_name    AS account_name,
            acc.account_type    AS account_type,
            acc.account_currency AS account_currency,
            SUM(gle.debit)      AS debit,
            SUM(gle.credit)     AS credit
        FROM `tabGL Entry` gle
        INNER JOIN `tabAccount` acc ON acc.name = gle.account
        WHERE gle.is_cancelled = 0
          AND acc.account_type IN ('Bank', 'Cash')
          {cond}
        GROUP BY gle.account
        ORDER BY acc.account_type, gle.account
    """.format(cond=period_cond), f, as_dict=True)

    # Also pick up bank/cash accounts that have an opening balance but ZERO
    # movement in the selected period, so they still show up with their balance.
    seen = {r.account for r in period_rows}
    zero_movement_accounts = [a for a in opening_map if a not in seen]
    extra_rows = []
    if zero_movement_accounts:
        extra_rows = frappe.db.sql("""
            SELECT name AS account, account_name, account_type, account_currency
            FROM `tabAccount`
            WHERE name IN %(accounts)s
        """, {"accounts": zero_movement_accounts}, as_dict=True)

    result = []
    for r in list(period_rows) + list(extra_rows):
        opening = opening_map.get(r.account, 0.0)
        debit   = flt(r.get("debit"))
        credit  = flt(r.get("credit"))
        closing = opening + debit - credit
        result.append(frappe._dict({
            "account"          : r.account,
            "account_name"     : r.account_name,
            "account_type"     : r.account_type,
            "account_currency" : r.get("account_currency"),
            "opening"          : opening,
            "debit"            : debit,
            "credit"           : credit,
            "balance"          : closing,
        }))

    result.sort(key=lambda x: (x.account_type or "", -abs(flt(x.balance))))
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  SQL — AR from GL Entry grouped by party
#
#  Logic:
#    Receivable accounts (root_type = 'Asset', account_type = 'Receivable')
#    For each party:
#      outstanding = SUM(debit) - SUM(credit)   [net debit = still owed]
#    We also pull the total invoiced from Sales Invoice for context.
# ─────────────────────────────────────────────────────────────────────────────
def _get_gl_ar_by_party(f):
    cond = " AND gle.company = %(company)s"
    if f.get("from_date"):    cond += " AND gle.posting_date >= %(from_date)s"
    if f.get("to_date"):      cond += " AND gle.posting_date <= %(to_date)s"
    if f.get("cost_center"):  cond += " AND gle.cost_center = %(cost_center)s"
    if f.get("finance_book"):
        cond += (" AND (gle.finance_book = %(finance_book)s"
                 " OR gle.finance_book IS NULL OR gle.finance_book = '')")

    return frappe.db.sql("""
        SELECT
            gle.party                                       AS party,
            MAX(cus.customer_name)                          AS party_name,
            gle.party_type                                  AS party_type,
            SUM(gle.debit)                                  AS total_debit,
            SUM(gle.credit)                                 AS total_credit,
            SUM(gle.debit  - gle.credit)                    AS outstanding,
            MAX(DATEDIFF(CURDATE(), gle.posting_date))      AS max_age_days
        FROM `tabGL Entry` gle
        INNER JOIN `tabAccount` acc
               ON acc.name = gle.account
        LEFT JOIN `tabCustomer` cus
               ON cus.name = gle.party
        WHERE gle.is_cancelled  = 0
          AND gle.party_type    = 'Customer'
          AND gle.party        IS NOT NULL
          AND gle.party        != ''
          AND acc.account_type  = 'Receivable'
          {cond}
        GROUP BY gle.party, gle.party_type
        HAVING outstanding > 0.005
        ORDER BY outstanding DESC
    """.format(cond=cond), f, as_dict=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SQL — AP from GL Entry grouped by party
#
#  Payable accounts (account_type = 'Payable')
#    outstanding = SUM(credit) - SUM(debit)   [net credit = still owed to supplier]
# ─────────────────────────────────────────────────────────────────────────────
def _get_gl_ap_by_party(f):
    cond = " AND gle.company = %(company)s"
    if f.get("from_date"):    cond += " AND gle.posting_date >= %(from_date)s"
    if f.get("to_date"):      cond += " AND gle.posting_date <= %(to_date)s"
    if f.get("cost_center"):  cond += " AND gle.cost_center = %(cost_center)s"
    if f.get("finance_book"):
        cond += (" AND (gle.finance_book = %(finance_book)s"
                 " OR gle.finance_book IS NULL OR gle.finance_book = '')")

    return frappe.db.sql("""
        SELECT
            gle.party                                       AS party,
           
            gle.party_type                                  AS party_type,
            SUM(gle.credit)                                 AS total_credit,
            SUM(gle.debit)                                  AS total_debit,
            SUM(gle.credit - gle.debit)                     AS outstanding,
            MAX(DATEDIFF(CURDATE(), gle.posting_date))      AS max_age_days
        FROM `tabGL Entry` gle
        INNER JOIN `tabAccount` acc
               ON acc.name = gle.account
        WHERE gle.is_cancelled  = 0
          AND gle.party_type    = 'Supplier'
          AND gle.party        IS NOT NULL
          AND gle.party        != ''
          AND acc.account_type  = 'Payable'
          {cond}
        GROUP BY gle.party
        HAVING outstanding > 0.005
        ORDER BY outstanding DESC
    """.format(cond=cond), f, as_dict=True)


# ─────────────────────────────────────────────────────────────────────────────
#  CHART  — Monthly P&L (axis-mixed)
# ─────────────────────────────────────────────────────────────────────────────
def _chart_monthly_pnl(gl_income, gl_expense):
    inc_map = {r.ym: flt(r.amount) for r in gl_income}
    exp_map = {r.ym: flt(r.amount) for r in gl_expense}
    all_yms = sorted(set(list(inc_map.keys()) + list(exp_map.keys())))

    if not all_yms:
        return None

    labels  = []
    income  = []
    expense = []
    profit  = []

    for ym in all_yms:
        try:
            y, m = ym.split("-")
            import calendar
            label = calendar.month_abbr[int(m)] + " " + y
        except Exception:
            label = ym
        labels.append(label)
        inc = flt(inc_map.get(ym, 0))
        exp = flt(exp_map.get(ym, 0))
        income.append(round(inc, 2))
        expense.append(round(exp, 2))
        profit.append(round(inc - exp, 2))

    return {
        "data": {
            "labels"  : labels,
            "datasets": [
                {"name": _("Income"),         "values": income,  "chartType": "bar"},
                {"name": _("Expense"),        "values": expense, "chartType": "bar"},
                {"name": _("Net Profit/Loss"),"values": profit,  "chartType": "line"},
            ],
        },
        "type"       : "axis-mixed",
        "colors"     : ["#2563eb", "#dc2626", "#10b981"],
        "height"     : 300,
        "barOptions" : {"stacked": 0},
        "axisOptions": {"xIsSeries": True},
        "lineOptions": {"hideDots": 0, "regionFill": 0},
    }


# ─────────────────────────────────────────────────────────────────────────────
#  SUMMARY CARDS
# ─────────────────────────────────────────────────────────────────────────────
def _summary_cards(invoices, gl_income, gl_expense, gl_ar, gl_bank_cash):
    total_income  = sum(flt(r.amount) for r in gl_income)
    total_expense = sum(flt(r.amount) for r in gl_expense)
    net_profit    = total_income - total_expense
    total_ar      = sum(flt(r.outstanding) for r in gl_ar)
    total_revenue = sum(flt(r.grand_total) for r in invoices)
    overdue_count = sum(1 for r in invoices if r.status == "Overdue")
    total_bank_cash = sum(flt(r.balance) for r in gl_bank_cash)

    return [
        {"value": total_income,     "label": _("Total Income"),        "datatype": "Currency", "indicator": "Blue"},
        {"value": total_expense,    "label": _("Total Expense"),       "datatype": "Currency", "indicator": "Red"},
        {"value": net_profit,       "label": _("Net Profit"),          "datatype": "Currency", "indicator": "Green" if net_profit >= 0 else "Red"},
        {"value": total_revenue,    "label": _("Sales Revenue"),       "datatype": "Currency", "indicator": "Green"},
        {"value": total_bank_cash,  "label": _("Bank & Cash Balance"), "datatype": "Currency", "indicator": "Teal" if total_bank_cash >= 0 else "Red"},
        {"value": total_ar,         "label": _("Total AR (GL)"),       "datatype": "Currency", "indicator": "Orange" if total_ar else "Green"},
        {"value": overdue_count,    "label": _("Overdue Invoices"),    "datatype": "Int",      "indicator": "Red" if overdue_count else "Green"},
    ]


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN HTML BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def _build_html(invoices, gl_income, gl_expense, gl_ar, gl_ap,
                income_accs, expense_accs, gl_bank_cash, filters):
    parts = []
    currency = _get_currency(filters)

    # ─────────────────────────────────────────────────────────────────────
    # SECTION 1 — P&L Summary 3 Cards
    # ─────────────────────────────────────────────────────────────────────
    total_income  = sum(flt(r.amount) for r in gl_income)
    total_expense = sum(flt(r.amount) for r in gl_expense)
    net_profit    = total_income - total_expense
    profit_color  = "#059669" if net_profit >= 0 else "#dc2626"
    profit_arrow  = "↑" if net_profit >= 0 else "↓"

    parts.append(f"""
<div style="background:#fff;border:1px solid #e4e8ef;border-radius:12px;
            overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.05);margin-bottom:16px">
  <div style="padding:12px 18px;border-bottom:1px solid #f0f2f5;background:#f8f9fb;
              border-left:4px solid #2563eb;display:flex;align-items:center;justify-content:space-between">
    <span style="font-size:14px;font-weight:700;color:#111827">📊 Profit &amp; Loss Summary</span>
    <span style="font-size:12px;color:#6b7280">
      {formatdate(filters.from_date)} → {formatdate(filters.to_date)}
    </span>
  </div>
  <div style="display:grid;grid-template-columns:1fr 48px 1fr 48px 1fr">

    <div style="padding:22px 24px;border-top:3px solid #2563eb">
      <div style="font-size:12px;font-weight:500;color:#6b7280;margin-bottom:6px;
                  display:flex;align-items:center;gap:6px">
        <span style="width:8px;height:8px;border-radius:50%;background:#2563eb;display:inline-block"></span>
        Total Income
      </div>
      <div style="font-family:'Cairo', sans-serif; font-size:28px;font-weight:700;
                  color:#2563eb;letter-spacing:-.5px;line-height:1;margin-bottom:8px">
        $ {total_income:,.2f}
      </div>
      <span style="display:inline-flex;align-items:center;gap:4px;padding:2px 9px;
                   border-radius:20px;font-size:11.5px;font-weight:600;
                   background:#eff6ff;color:#1d4ed8">↑ From GL Entries</span>
    </div>

    <div style="display:flex;align-items:center;justify-content:center;
                background:#f8f9fb;font-size:24px;color:#9ca3af;font-weight:300">−</div>

    <div style="padding:22px 24px;border-top:3px solid #dc2626">
      <div style="font-size:12px;font-weight:500;color:#6b7280;margin-bottom:6px;
                  display:flex;align-items:center;gap:6px">
        <span style="width:8px;height:8px;border-radius:50%;background:#dc2626;display:inline-block"></span>
        Total Expense
      </div>
      <div style="font-family:'Cairo', sans-serif; font-size:28px;font-weight:700;
                  color:#dc2626;letter-spacing:-.5px;line-height:1;margin-bottom:8px">
        $ {total_expense:,.2f}
      </div>
      <span style="display:inline-flex;align-items:center;gap:4px;padding:2px 9px;
                   border-radius:20px;font-size:11.5px;font-weight:600;
                   background:#fef2f2;color:#991b1b">↑ From GL Entries</span>
    </div>

    <div style="display:flex;align-items:center;justify-content:center;
                background:#f8f9fb;font-size:24px;color:#9ca3af;font-weight:300">=</div>

    <div style="padding:22px 24px;border-top:3px solid {profit_color}">
      <div style="font-size:12px;font-weight:500;color:#6b7280;margin-bottom:6px;
                  display:flex;align-items:center;gap:6px">
        <span style="width:8px;height:8px;border-radius:50%;background:{profit_color};display:inline-block"></span>
        Net Profit / Loss
      </div>
      <div style="font-family:'Cairo', sans-serif;font-size:28px;font-weight:700;
                  color:{profit_color};letter-spacing:-.5px;line-height:1;margin-bottom:8px">
        $ {net_profit:,.2f}
      </div>
      <span style="display:inline-flex;align-items:center;gap:4px;padding:2px 9px;
                   border-radius:20px;font-size:11.5px;font-weight:600;
                   background:{'#ecfdf5' if net_profit >= 0 else '#fef2f2'};
                   color:{'#065f46' if net_profit >= 0 else '#991b1b'}">
        {profit_arrow} Net Result
      </span>
    </div>
  </div>
</div>""")

    # ─────────────────────────────────────────────────────────────────────
    # SECTION 2 — P&L Accounts Breakdown (Income & Expense by account)
    # ─────────────────────────────────────────────────────────────────────
    # Build income rows
    income_rows_html = ""
    top_income = income_accs[:15]
    inc_max = flt(top_income[0].amount) if top_income else 1

    for i, row in enumerate(top_income):
        amt   = flt(row.amount)
        pct   = round(amt / total_income * 100, 1) if total_income else 0
        bar_w = round(amt / inc_max * 100)
        color = COLORS_10[i % len(COLORS_10)]
        income_rows_html += f"""
        <tr style="border-bottom:1px solid #f0f2f5">
          <td style="padding:9px 12px;display:flex;align-items:center;gap:8px">
            <span style="width:8px;height:8px;border-radius:50%;background:{color};
                         display:inline-block;flex-shrink:0"></span>
            <span style="font-weight:500;font-size:12.5px;color:#111827">{row.account_name}</span>
            <span style="font-size:10.5px;color:#9ca3af;font-family:monospace">{row.account}</span>
          </td>
          <td style="padding:9px 12px;text-align:right;font-weight:700;color:#2563eb;
                     font-family:'Cairo', sans-serif;font-size:12px;white-space:nowrap">
            $ {amt:,.2f}
          </td>
          <td style="padding:9px 12px;text-align:right;font-size:11.5px;color:#6b7280;
                     white-space:nowrap">{pct}%</td>
          <td style="padding:9px 24px 9px 8px;min-width:160px">
            <div style="background:#eff6ff;border-radius:3px;height:6px;overflow:hidden">
              <div style="width:{bar_w}%;height:100%;background:{color};border-radius:3px"></div>
            </div>
          </td>
        </tr>"""

    # Build expense rows
    expense_rows_html = ""
    top_expense = expense_accs[:15]
    exp_max = flt(top_expense[0].amount) if top_expense else 1

    for i, row in enumerate(top_expense):
        amt   = flt(row.amount)
        pct   = round(amt / total_expense * 100, 1) if total_expense else 0
        bar_w = round(amt / exp_max * 100)
        color = EXP_COLORS[i % len(EXP_COLORS)]
        expense_rows_html += f"""
        <tr style="border-bottom:1px solid #f0f2f5">
          <td style="padding:9px 12px;display:flex;align-items:center;gap:8px">
            <span style="width:8px;height:8px;border-radius:50%;background:{color};
                         display:inline-block;flex-shrink:0"></span>
            <span style="font-weight:500;font-size:12.5px;color:#111827">{row.account_name}</span>
            <span style="font-size:10.5px;color:#9ca3af;font-family:monospace">{row.account}</span>
          </td>
          <td style="padding:9px 12px;text-align:right;font-weight:700;color:#dc2626;
                     font-family:'Cairo', sans-serif;font-size:12px;white-space:nowrap">
            $ {amt:,.2f}
          </td>
          <td style="padding:9px 12px;text-align:right;font-size:11.5px;color:#6b7280;
                     white-space:nowrap">{pct}%</td>
          <td style="padding:9px 24px 9px 8px;min-width:160px">
            <div style="background:#fef2f2;border-radius:3px;height:6px;overflow:hidden">
              <div style="width:{bar_w}%;height:100%;background:{color};border-radius:3px"></div>
            </div>
          </td>
        </tr>"""

    inc_pie  = _pie_svg([(r.account_name, flt(r.amount)) for r in top_income[:8]])
    exp_pie  = _pie_svg([(r.account_name, flt(r.amount)) for r in top_expense[:8]], palette=EXP_COLORS)

    no_inc = '<tr><td colspan="4" style="padding:20px;text-align:center;color:#9ca3af">No income GL entries for this period.</td></tr>'
    no_exp = '<tr><td colspan="4" style="padding:20px;text-align:center;color:#9ca3af">No expense GL entries for this period.</td></tr>'

    parts.append(f"""
<div style="background:#fff;border:1px solid #e4e8ef;border-radius:12px;
            overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.05);margin-bottom:16px">
  <div style="padding:12px 18px;border-bottom:1px solid #f0f2f5;background:#f8f9fb;
              border-left:4px solid #7c3aed">
    <span style="font-size:14px;font-weight:700;color:#111827">🔍 P&amp;L Accounts Breakdown</span>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:0;border-bottom:none">

    <!-- Income side -->
    <div style="border-right:1px solid #f0f2f5">
      <div style="padding:10px 14px;background:#eff6ff;border-bottom:1px solid #dbeafe;
                  display:flex;align-items:center;justify-content:space-between">
        <span style="font-size:12px;font-weight:700;color:#1d4ed8">💰 Income Accounts</span>
        <span style="font-family:'Cairo', sans-serif;font-size:13px;font-weight:700;color:#1d4ed8">
          $ {total_income:,.2f}
        </span>
      </div>
      <div style="display:grid;grid-template-columns:1fr auto">
        <div style="overflow-x:auto">
          <table style="width:100%;border-collapse:collapse;font-size:12px">
            <thead><tr style="background:#f8f9fb">
              {_th("Account","left")}{_th("Amount","right")}
              {_th("%","right")}{_th("","left")}
            </tr></thead>
            <tbody>{income_rows_html or no_inc}</tbody>
          </table>
        </div>
        <div style="padding:16px;display:flex;flex-direction:column;align-items:center;
                    justify-content:center;border-left:1px solid #f0f2f5;min-width:180px">
          {inc_pie}
          <div style="font-size:10px;color:#9ca3af;margin-top:6px;text-align:center">
            Income Share
          </div>
        </div>
      </div>
    </div>

    <!-- Expense side -->
    <div>
      <div style="padding:10px 14px;background:#fef2f2;border-bottom:1px solid #fecaca;
                  display:flex;align-items:center;justify-content:space-between">
        <span style="font-size:12px;font-weight:700;color:#991b1b">📤 Expense Accounts</span>
        <span style="font-family:'Cairo', sans-serif;font-size:13px;font-weight:700;color:#991b1b">
          $ {total_expense:,.2f}
        </span>
      </div>
      <div style="display:grid;grid-template-columns:1fr auto">
        <div style="overflow-x:auto">
          <table style="width:100%;border-collapse:collapse;font-size:12px">
            <thead><tr style="background:#f8f9fb">
              {_th("Account","left")}{_th("Amount","right")}
              {_th("%","right")}{_th("","left")}
            </tr></thead>
            <tbody>{expense_rows_html or no_exp}</tbody>
          </table>
        </div>
        <div style="padding:16px;display:flex;flex-direction:column;align-items:center;
                    justify-content:center;border-left:1px solid #f0f2f5;min-width:180px">
          {exp_pie}
          <div style="font-size:10px;color:#9ca3af;margin-top:6px;text-align:center">
            Expense Share
          </div>
        </div>
      </div>
    </div>

  </div>
</div>""")

    # ─────────────────────────────────────────────────────────────────────
    # SECTION 3 — Bank & Cash Balances  (NEW)
    # ─────────────────────────────────────────────────────────────────────
    total_bank_opening = sum(flt(r.opening) for r in gl_bank_cash if r.account_type == "Bank")
    total_bank_debit   = sum(flt(r.debit)   for r in gl_bank_cash if r.account_type == "Bank")
    total_bank_credit  = sum(flt(r.credit)  for r in gl_bank_cash if r.account_type == "Bank")
    total_bank_balance = sum(flt(r.balance) for r in gl_bank_cash if r.account_type == "Bank")

    total_cash_opening = sum(flt(r.opening) for r in gl_bank_cash if r.account_type == "Cash")
    total_cash_debit   = sum(flt(r.debit)   for r in gl_bank_cash if r.account_type == "Cash")
    total_cash_credit  = sum(flt(r.credit)  for r in gl_bank_cash if r.account_type == "Cash")
    total_cash_balance = sum(flt(r.balance) for r in gl_bank_cash if r.account_type == "Cash")

    grand_balance = total_bank_balance + total_cash_balance

    bc_rows = ""
    for row in gl_bank_cash:
        is_bank = row.account_type == "Bank"
        type_bg, type_fg, type_icon = ("#eff6ff", "#1d4ed8", "🏦") if is_bank else ("#ecfdf5", "#059669", "💵")
        bal_color = "#059669" if flt(row.balance) >= 0 else "#dc2626"

        bc_rows += f"""
        <tr style="border-bottom:1px solid #f0f2f5">
          <td style="padding:10px 12px">
            <span style="display:inline-flex;align-items:center;gap:4px;padding:2px 9px;
                         border-radius:20px;font-size:11px;font-weight:600;
                         background:{type_bg};color:{type_fg}">{type_icon} {row.account_type}</span>
          </td>
          <td style="padding:10px 12px;font-weight:600;color:#111827">{row.account_name}</td>
          <td style="padding:10px 12px;color:#6b7280;font-size:12px;font-family:monospace">{row.account}</td>
          <td style="padding:10px 12px;text-align:right;color:#374151;
                     font-family:'Cairo', sans-serif;font-size:12px">
            {_f(row.opening, currency)}
          </td>
          <td style="padding:10px 12px;text-align:right;font-weight:600;color:#2563eb;
                     font-family:'Cairo', sans-serif;font-size:12px">
            {_f(row.debit, currency)}
          </td>
          <td style="padding:10px 12px;text-align:right;font-weight:600;color:#dc2626;
                     font-family:'Cairo', sans-serif;font-size:12px">
            {_f(row.credit, currency)}
          </td>
          <td style="padding:10px 12px;text-align:right;font-weight:700;color:{bal_color};
                     font-family:'Cairo', sans-serif;font-size:12.5px">
            {_f(row.balance, currency)}
          </td>
        </tr>"""

    bc_total_row = f"""
    <tr style="background:#f8f9fb;border-top:2px solid #e4e8ef;font-weight:700">
      <td colspan="3" style="padding:10px 12px">Total</td>
      <td style="padding:10px 12px;text-align:right;font-family:'Cairo', sans-serif;font-size:12px;color:#374151">
        {_f(total_bank_opening + total_cash_opening, currency)}
      </td>
      <td style="padding:10px 12px;text-align:right;font-family:'Cairo', sans-serif;font-size:12px;color:#2563eb">
        {_f(total_bank_debit + total_cash_debit, currency)}
      </td>
      <td style="padding:10px 12px;text-align:right;font-family:'Cairo', sans-serif;font-size:12px;color:#dc2626">
        {_f(total_bank_credit + total_cash_credit, currency)}
      </td>
      <td style="padding:10px 12px;text-align:right;font-family:'Cairo', sans-serif;font-size:12.5px;
                 color:{'#059669' if grand_balance >= 0 else '#dc2626'}">
        {_f(grand_balance, currency)}
      </td>
    </tr>"""

    no_bc = _empty_row(7, "No Bank/Cash accounts with GL activity found for this period.")

    parts.append(f"""
<div style="background:#fff;border:1px solid #e4e8ef;border-radius:12px;
            overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.05);margin-bottom:16px">
  <div style="padding:12px 18px;border-bottom:1px solid #f0f2f5;background:#f8f9fb;
              border-left:4px solid #059669;display:flex;align-items:center;justify-content:space-between">
    <span style="font-size:14px;font-weight:700;color:#111827">🏦 Bank &amp; Cash Balances</span>
    <span style="font-size:11px;color:#9ca3af">Opening balance as of {formatdate(filters.from_date)}, movement through {formatdate(filters.to_date)}</span>
  </div>

  <div style="padding:16px 18px;display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;
              border-bottom:1px solid #f0f2f5">
    <div style="padding:14px;background:#eff6ff;border-radius:10px">
      <div style="font-size:11px;font-weight:600;color:#1d4ed8;margin-bottom:4px">🏦 Bank Balance</div>
      <div style="font-family:'Cairo', sans-serif;font-size:20px;font-weight:700;color:#1d4ed8">
        {_f(total_bank_balance, currency)}
      </div>
    </div>
    <div style="padding:14px;background:#ecfdf5;border-radius:10px">
      <div style="font-size:11px;font-weight:600;color:#059669;margin-bottom:4px">💵 Cash Balance</div>
      <div style="font-family:'Cairo', sans-serif;font-size:20px;font-weight:700;color:#059669">
        {_f(total_cash_balance, currency)}
      </div>
    </div>
    <div style="padding:14px;background:#f8f9fb;border-radius:10px;border:1px solid #e4e8ef">
      <div style="font-size:11px;font-weight:600;color:#111827;margin-bottom:4px">Total Bank + Cash</div>
      <div style="font-family:'Cairo', sans-serif;font-size:20px;font-weight:700;
                  color:{'#059669' if grand_balance >= 0 else '#dc2626'}">
        {_f(grand_balance, currency)}
      </div>
    </div>
  </div>

  <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:collapse;font-size:12.5px">
      <thead><tr style="background:#f8f9fb">
        {_th("Type","left")}{_th("Account","left")}{_th("Account ID","left")}
        {_th("Opening Balance","right")}{_th("Debit","right")}
        {_th("Credit","right")}{_th("Closing Balance","right")}
      </tr></thead>
      <tbody>{bc_rows or no_bc}</tbody>
      <tfoot>{bc_total_row if gl_bank_cash else ""}</tfoot>
    </table>
  </div>
</div>""")

    # ─────────────────────────────────────────────────────────────────────
    # SECTION 4 — AR Summary Card  (GL-based)
    # ─────────────────────────────────────────────────────────────────────
    total_ar_outstanding = sum(flt(r.outstanding)   for r in gl_ar)
    total_ar_debit       = sum(flt(r.total_debit)   for r in gl_ar)
    total_ar_credit      = sum(flt(r.total_credit)  for r in gl_ar)
    ar_party_count       = len(gl_ar)

    # Overdue: use the invoice table for overdue flag, but total from GL
    overdue_inv    = [r for r in invoices if r.status == "Overdue"]
    overdue_amount = sum(flt(r.outstanding_amount) for r in overdue_inv)
    paid_count     = sum(1 for r in invoices if r.status == "Paid")

    coll_pct = round(total_ar_credit / total_ar_debit * 100, 1) if total_ar_debit else 0

    parts.append(f"""
<div style="background:#fff;border:1px solid #e4e8ef;border-radius:12px;
            overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.05);margin-bottom:16px">
  <div style="padding:12px 18px;border-bottom:1px solid #f0f2f5;background:#f8f9fb;
              border-left:4px solid #2563eb">
    <span style="font-size:14px;font-weight:700;color:#111827">📥 Accounts Receivable Summary</span>
    <span style="font-size:11px;color:#9ca3af;margin-left:8px">— sourced from GL Entry (includes journals &amp; payments without invoice reference)</span>
  </div>
  <div style="padding:20px 24px">
    <div style="display:grid;grid-template-columns:auto 1fr 1fr 1fr 1fr 1fr;gap:24px;align-items:center">
      <div>
        <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;
                    color:#9ca3af;margin-bottom:4px">Total Outstanding</div>
        <div style="font-family:'Cairo', sans-serif;font-size:30px;font-weight:500;
                    color:#2563eb;letter-spacing:-1px;line-height:1">
          $ {total_ar_outstanding:,.2f}
        </div>
        <div style="height:4px;background:#e4e8ef;border-radius:2px;overflow:hidden;margin-top:8px;width:160px">
          <div style="height:100%;width:{min(coll_pct,100):.0f}%;background:#2563eb;border-radius:2px"></div>
        </div>
        <div style="font-size:11px;color:#6b7280;margin-top:3px">{coll_pct}% collected</div>
      </div>
      <div style="padding:14px;background:#eff6ff;border-radius:10px;text-align:center">
        <div style="font-size:20px;font-weight:700;color:#2563eb;font-family:'DM Mono',monospace">
          {ar_party_count}
        </div>
        <div style="font-size:11px;color:#6b7280;font-weight:500;margin-top:2px">Customers w/ Balance</div>
      </div>
      <div style="padding:14px;background:#ecfdf5;border-radius:10px;text-align:center">
        <div style="font-size:20px;font-weight:700;color:#059669;font-family:'DM Mono',monospace">
          $ {total_ar_credit:,.0f}
        </div>
        <div style="font-size:11px;color:#6b7280;font-weight:500;margin-top:2px">Total Received (GL)</div>
      </div>
      <div style="padding:14px;background:#fef2f2;border-radius:10px;text-align:center">
        <div style="font-size:20px;font-weight:700;color:#dc2626;font-family:'DM Mono',monospace">
          {len(overdue_inv)}
        </div>
        <div style="font-size:11px;color:#6b7280;font-weight:500;margin-top:2px">Overdue Invoices</div>
      </div>
      <div style="padding:14px;background:#fef2f2;border-radius:10px;text-align:center">
        <div style="font-size:20px;font-weight:700;color:#dc2626;font-family:'DM Mono',monospace">
          $ {overdue_amount:,.0f}
        </div>
        <div style="font-size:11px;color:#6b7280;font-weight:500;margin-top:2px">Overdue Amount</div>
      </div>
      <div style="padding:14px;background:#ecfdf5;border-radius:10px;text-align:center">
        <div style="font-size:20px;font-weight:700;color:#059669;font-family:'DM Mono',monospace">
          {paid_count}
        </div>
        <div style="font-size:11px;color:#6b7280;font-weight:500;margin-top:2px">Paid Invoices</div>
      </div>
    </div>
  </div>
</div>""")

    # ─────────────────────────────────────────────────────────────────────
    # SECTION 5 — Top 10 AR Table  (from GL)
    # ─────────────────────────────────────────────────────────────────────
    medals = ["🥇", "🥈", "🥉"]
    ar_rows = ""

    for i, row in enumerate(gl_ar[:10]):
        rank      = medals[i] if i < 3 else f"<span style='color:#9ca3af;font-weight:700'>#{i+1}</span>"
        debit     = flt(row.total_debit)
        credit    = flt(row.total_credit)
        out       = flt(row.outstanding)
        coll_p    = round(credit / debit * 100) if debit else 0
        bar_col   = "#059669" if coll_p >= 80 else ("#d97706" if coll_p >= 50 else "#dc2626")
        age_days  = int(row.max_age_days or 0)
        age_html  = _age_pill(age_days)
        name_disp = row.party_name or row.party

        ar_rows += f"""
        <tr style="border-bottom:1px solid #f0f2f5">
          <td style="padding:10px 12px;text-align:center;font-size:15px">{rank}</td>
          <td style="padding:10px 12px;font-weight:600;color:#111827">{name_disp}</td>
          <td style="padding:10px 12px;color:#6b7280;font-size:12px">{row.party}</td>
          <td style="padding:10px 12px;text-align:right;font-weight:600;
                     font-family:'Cairo', sans-serif;font-size:12px;color:#2563eb">
            $ {debit:,.2f}
          </td>
          <td style="padding:10px 12px;text-align:right;font-weight:700;
                     font-family:'Cairo', sans-serif;font-size:12px;color:#059669">
            $ {credit:,.2f}
          </td>
          <td style="padding:10px 12px;text-align:right;font-weight:700;
                     font-family:'Cairo', sans-serif;font-size:12px;
                     color:{'#dc2626' if out > 0 else '#059669'}">
            $ {out:,.2f}
          </td>
          <td style="padding:10px 12px">{age_html}</td>
          <td style="padding:10px 12px;min-width:140px">
            <div style="display:flex;align-items:center;gap:8px">
              <div style="flex:1;background:#f0f4f8;border-radius:3px;height:6px;overflow:hidden">
                <div style="width:{coll_p}%;height:100%;background:{bar_col};border-radius:3px"></div>
              </div>
              <span style="font-size:11px;font-weight:700;color:{bar_col};width:34px;text-align:right">
                {coll_p}%
              </span>
            </div>
          </td>
        </tr>"""

    ar_tot_debit  = sum(flt(r.total_debit)  for r in gl_ar[:10])
    ar_tot_credit = sum(flt(r.total_credit) for r in gl_ar[:10])
    ar_tot_out    = sum(flt(r.outstanding)  for r in gl_ar[:10])

    parts.append(_card(
        "🏆 Top 10 Accounts Receivable", "#2563eb",
        f"""<div style="overflow-x:auto">
          <table style="width:100%;border-collapse:collapse;font-size:12.5px">
            <thead><tr style="background:#f8f9fb">
              {_th("")}{_th("Party Name","left")}{_th("Party ID","left")}
              {_th("Total Debited","right")}{_th("Total Credited","right")}
              {_th("Outstanding","right")}{_th("Ageing","left")}
              {_th("Collection %","left")}
            </tr></thead>
            <tbody>{ar_rows if ar_rows else _empty_row(8, "No AR balances found in GL for this period.")}</tbody>
            <tfoot>
              <tr style="background:#f8f9fb;border-top:2px solid #e4e8ef">
                <td colspan="3" style="padding:10px 12px;font-weight:700">Total (Top 10)</td>
                <td style="padding:10px 12px;text-align:right;font-weight:700;
                           font-family:'Cairo', sans-serif;font-size:12px;color:#2563eb">
                  $ {ar_tot_debit:,.2f}
                </td>
                <td style="padding:10px 12px;text-align:right;font-weight:700;
                           font-family:'Cairo', sans-serif;font-size:12px;color:#059669">
                  $ {ar_tot_credit:,.2f}
                </td>
                <td style="padding:10px 12px;text-align:right;font-weight:700;
                           font-family:'Cairo', sans-serif;font-size:12px;color:#dc2626">
                  $ {ar_tot_out:,.2f}
                </td>
                <td colspan="2"></td>
              </tr>
            </tfoot>
          </table>
        </div>"""
    ))

    # ─────────────────────────────────────────────────────────────────────
    # SECTION 6 — AP Summary Card  (GL-based)
    # ─────────────────────────────────────────────────────────────────────
    total_ap_outstanding = sum(flt(r.outstanding)   for r in gl_ap)
    total_ap_credit      = sum(flt(r.total_credit)  for r in gl_ap)
    total_ap_debit       = sum(flt(r.total_debit)   for r in gl_ap)
    ap_party_count       = len(gl_ap)
    ap_pay_pct           = round(total_ap_debit / total_ap_credit * 100, 1) if total_ap_credit else 0

    # overdue AP from purchase invoices via invoices table isn't available here,
    # but we can derive from gl_ap max_age_days > 0 as a proxy
    overdue_ap_count  = sum(1 for r in gl_ap if int(r.max_age_days or 0) > 30)
    overdue_ap_amount = sum(flt(r.outstanding) for r in gl_ap if int(r.max_age_days or 0) > 30)

    parts.append(f"""
<div style="background:#fff;border:1px solid #e4e8ef;border-radius:12px;
            overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.05);margin-bottom:16px">
  <div style="padding:12px 18px;border-bottom:1px solid #f0f2f5;background:#f8f9fb;
              border-left:4px solid #dc2626">
    <span style="font-size:14px;font-weight:700;color:#111827">📤 Accounts Payable Summary</span>
    <span style="font-size:11px;color:#9ca3af;margin-left:8px">— sourced from GL Entry (includes journals &amp; payments without bill reference)</span>
  </div>
  <div style="padding:20px 24px">
    <div style="display:grid;grid-template-columns:auto 1fr 1fr 1fr 1fr 1fr;gap:24px;align-items:center">
      <div>
        <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;
                    color:#9ca3af;margin-bottom:4px">Total Outstanding</div>
        <div style="font-family:'Cairo', sans-serif;font-size:30px;font-weight:500;
                    color:#dc2626;letter-spacing:-1px;line-height:1">
          $ {total_ap_outstanding:,.2f}
        </div>
        <div style="height:4px;background:#e4e8ef;border-radius:2px;overflow:hidden;margin-top:8px;width:160px">
          <div style="height:100%;width:{min(ap_pay_pct,100):.0f}%;background:#dc2626;border-radius:2px"></div>
        </div>
        <div style="font-size:11px;color:#6b7280;margin-top:3px">{ap_pay_pct}% paid</div>
      </div>
      <div style="padding:14px;background:#fef2f2;border-radius:10px;text-align:center">
        <div style="font-size:20px;font-weight:700;color:#dc2626;font-family:'DM Mono',monospace">
          {ap_party_count}
        </div>
        <div style="font-size:11px;color:#6b7280;font-weight:500;margin-top:2px">Suppliers w/ Balance</div>
      </div>
      <div style="padding:14px;background:#ecfdf5;border-radius:10px;text-align:center">
        <div style="font-size:20px;font-weight:700;color:#059669;font-family:'DM Mono',monospace">
          $ {total_ap_debit:,.0f}
        </div>
        <div style="font-size:11px;color:#6b7280;font-weight:500;margin-top:2px">Total Paid (GL)</div>
      </div>
      <div style="padding:14px;background:#fef2f2;border-radius:10px;text-align:center">
        <div style="font-size:20px;font-weight:700;color:#dc2626;font-family:'DM Mono',monospace">
          {overdue_ap_count}
        </div>
        <div style="font-size:11px;color:#6b7280;font-weight:500;margin-top:2px">Aged &gt; 30d</div>
      </div>
      <div style="padding:14px;background:#fef2f2;border-radius:10px;text-align:center">
        <div style="font-size:20px;font-weight:700;color:#dc2626;font-family:'DM Mono',monospace">
          $ {overdue_ap_amount:,.0f}
        </div>
        <div style="font-size:11px;color:#6b7280;font-weight:500;margin-top:2px">Aged &gt; 30d Amount</div>
      </div>
      <div style="padding:14px;background:#ecfdf5;border-radius:10px;text-align:center">
        <div style="font-size:20px;font-weight:700;color:#059669;font-family:'DM Mono',monospace">
          $ {total_ap_credit:,.0f}
        </div>
        <div style="font-size:11px;color:#6b7280;font-weight:500;margin-top:2px">Total Billed (GL)</div>
      </div>
    </div>
  </div>
</div>""")

    # ─────────────────────────────────────────────────────────────────────
    # SECTION 7 — Top 10 AP Table  (from GL)
    # ─────────────────────────────────────────────────────────────────────
    ap_rows = ""

    for i, row in enumerate(gl_ap[:10]):
        rank      = medals[i] if i < 3 else f"<span style='color:#9ca3af;font-weight:700'>#{i+1}</span>"
        credit    = flt(row.total_credit)
        debit     = flt(row.total_debit)
        out       = flt(row.outstanding)
        pay_p     = round(debit / credit * 100) if credit else 0
        bar_c     = "#059669" if pay_p >= 80 else ("#d97706" if pay_p >= 50 else "#dc2626")
        age_days  = int(row.max_age_days or 0)
        age       = _age_pill(age_days)
        name_disp = row.party_name or row.party

        ap_rows += f"""
        <tr style="border-bottom:1px solid #f0f2f5">
          <td style="padding:10px 12px;text-align:center;font-size:15px">{rank}</td>
          <td style="padding:10px 12px;font-weight:600;color:#111827">{name_disp}</td>
          <td style="padding:10px 12px;color:#6b7280;font-size:12px">{row.party}</td>
          <td style="padding:10px 12px;text-align:right;font-weight:600;
                     font-family:'Cairo', sans-serif;font-size:12px;color:#374151">
            $ {credit:,.2f}
          </td>
          <td style="padding:10px 12px;text-align:right;font-weight:700;
                     font-family:'Cairo', sans-serif;font-size:12px;color:#059669">
            $ {debit:,.2f}
          </td>
          <td style="padding:10px 12px;text-align:right;font-weight:700;
                     font-family:'Cairo', sans-serif;font-size:12px;
                     color:{'#dc2626' if out > 0 else '#059669'}">
            $ {out:,.2f}
          </td>
          <td style="padding:10px 12px">{age}</td>
          <td style="padding:10px 12px;min-width:140px">
            <div style="display:flex;align-items:center;gap:8px">
              <div style="flex:1;background:#f0f4f8;border-radius:3px;height:6px;overflow:hidden">
                <div style="width:{pay_p}%;height:100%;background:{bar_c};border-radius:3px"></div>
              </div>
              <span style="font-size:11px;font-weight:700;color:{bar_c};width:34px;text-align:right">
                {pay_p}%
              </span>
            </div>
          </td>
        </tr>"""

    ap_tot_credit = sum(flt(r.total_credit) for r in gl_ap[:10])
    ap_tot_debit  = sum(flt(r.total_debit)  for r in gl_ap[:10])
    ap_tot_out    = sum(flt(r.outstanding)  for r in gl_ap[:10])

    parts.append(_card(
        "🏢 Top 10 Accounts Payable", "#dc2626",
        f"""<div style="overflow-x:auto">
          <table style="width:100%;border-collapse:collapse;font-size:12.5px">
            <thead><tr style="background:#f8f9fb">
              {_th("")}{_th("Party Name","left")}{_th("Party ID","left")}
              {_th("Total Billed","right")}{_th("Total Paid","right")}
              {_th("Outstanding","right")}{_th("Ageing","left")}
              {_th("Payment %","left")}
            </tr></thead>
            <tbody>{ap_rows if ap_rows else _empty_row(8, "No AP balances found in GL for this period.")}</tbody>
            <tfoot>
              <tr style="background:#f8f9fb;border-top:2px solid #e4e8ef">
                <td colspan="3" style="padding:10px 12px;font-weight:700">Total (Top 10)</td>
                <td style="padding:10px 12px;text-align:right;font-weight:700;
                           font-family:'Cairo', sans-serif;font-size:12px;color:#374151">
                  $ {ap_tot_credit:,.2f}
                </td>
                <td style="padding:10px 12px;text-align:right;font-weight:700;
                           font-family:'Cairo', sans-serif;font-size:12px;color:#059669">
                  $ {ap_tot_debit:,.2f}
                </td>
                <td style="padding:10px 12px;text-align:right;font-weight:700;
                           font-family:'Cairo', sans-serif;font-size:12px;color:#dc2626">
                  $ {ap_tot_out:,.2f}
                </td>
                <td colspan="2"></td>
              </tr>
            </tfoot>
          </table>
        </div>"""
    ))

    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
#  COLOUR PALETTES
# ─────────────────────────────────────────────────────────────────────────────
COLORS_10 = [
    "#2563eb", "#0891b2", "#7c3aed", "#0d9488", "#65a30d",
    "#d97706", "#db2777", "#6366f1", "#059669", "#6b7280",
]

EXP_COLORS = [
    "#dc2626", "#ea580c", "#b45309", "#7c2d12", "#c2410c",
    "#9a3412", "#e11d48", "#be123c", "#991b1b", "#7f1d1d",
]


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _f(val, currency=None):
    """Format a number as money using Frappe's currency-aware formatter."""
    return fmt_money(flt(val), currency=currency or frappe.defaults.get_global_default("currency") or "USD")


def _age_pill(days):
    if days <= 0:
        return ('<span style="display:inline-flex;align-items:center;gap:4px;'
                'padding:2px 9px;border-radius:20px;font-size:11px;font-weight:600;'
                'background:#ecfdf5;color:#065f46">✓ Current</span>')
    if days <= 15:
        return (f'<span style="display:inline-flex;align-items:center;gap:4px;'
                f'padding:2px 9px;border-radius:20px;font-size:11px;font-weight:600;'
                f'background:#fffbeb;color:#92400e">{days}d</span>')
    if days <= 30:
        return (f'<span style="display:inline-flex;align-items:center;gap:4px;'
                f'padding:2px 9px;border-radius:20px;font-size:11px;font-weight:600;'
                f'background:#fff7ed;color:#c2410c">{days}d</span>')
    return (f'<span style="display:inline-flex;align-items:center;gap:4px;'
            f'padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700;'
            f'background:#fef2f2;color:#991b1b">⚠ {days}d</span>')


def _pie_svg(data_pairs, size=160, palette=None):
    colors = palette or COLORS_10
    total = sum(flt(v) for _, v in data_pairs) or 1
    cx = cy = size / 2
    r_out = size * 0.42
    r_in  = size * 0.22
    segs  = []
    angle = -90.0

    for i, (label, value) in enumerate(data_pairs):
        sweep = flt(value) / total * 360
        if sweep < 1:
            continue
        color = colors[i % len(colors)]
        x1  = cx + r_out * math.cos(math.radians(angle))
        y1  = cy + r_out * math.sin(math.radians(angle))
        x2  = cx + r_out * math.cos(math.radians(angle + sweep))
        y2  = cy + r_out * math.sin(math.radians(angle + sweep))
        xi1 = cx + r_in  * math.cos(math.radians(angle + sweep))
        yi1 = cy + r_in  * math.sin(math.radians(angle + sweep))
        xi2 = cx + r_in  * math.cos(math.radians(angle))
        yi2 = cy + r_in  * math.sin(math.radians(angle))
        lg  = 1 if sweep > 180 else 0
        path = (f"M {x1:.2f} {y1:.2f} "
                f"A {r_out:.2f} {r_out:.2f} 0 {lg} 1 {x2:.2f} {y2:.2f} "
                f"L {xi1:.2f} {yi1:.2f} "
                f"A {r_in:.2f} {r_in:.2f} 0 {lg} 0 {xi2:.2f} {yi2:.2f} Z")
        pct = round(flt(value) / total * 100, 1)
        segs.append(
            f'<path d="{path}" fill="{color}" stroke="#fff" stroke-width="2">'
            f'<title>{label}: {pct}%</title></path>'
        )
        angle += sweep

    legend = "".join(
        f'<div style="display:flex;align-items:center;gap:5px;font-size:10.5px;'
        f'color:#374151;margin:2px 0">'
        f'<span style="width:8px;height:8px;border-radius:50%;background:{colors[i % len(colors)]};'
        f'display:inline-block;flex-shrink:0"></span>'
        f'{str(label)[:18]}: {round(flt(val) / total * 100, 1)}%</div>'
        for i, (label, val) in enumerate(data_pairs[:6]) if flt(val) > 0
    )

    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
      {''.join(segs)}
      <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r_in * 0.85:.1f}" fill="#fff"/>
    </svg>
    <div style="margin-top:6px">{legend}</div>"""


def _th(label, align="left"):
    return (f'<th style="padding:8px 14px;text-align:{align};font-size:10px;'
            f'font-weight:700;text-transform:uppercase;letter-spacing:.6px;'
            f'color:#9ca3af;border-bottom:1px solid #e4e8ef;white-space:nowrap">'
            f'{label}</th>')


def _card(title, accent, body_html):
    return f"""
<div style="background:#fff;border:1px solid #e4e8ef;border-radius:12px;
            overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.05);margin-bottom:16px">
  <div style="padding:12px 18px;border-bottom:1px solid #f0f2f5;background:#f8f9fb;
              border-left:4px solid {accent};display:flex;align-items:center;gap:10px">
    <span style="font-size:14px;font-weight:700;color:#111827">{title}</span>
  </div>
  <div style="overflow-x:auto">{body_html}</div>
</div>"""


def _empty_row(colspan, msg="No data."):
    return (f'<tr><td colspan="{colspan}" '
            f'style="padding:20px;text-align:center;color:#9ca3af">{msg}</td></tr>')