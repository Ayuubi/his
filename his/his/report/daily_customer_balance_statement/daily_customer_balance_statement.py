 # Copyright (c) 2026
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, flt


def execute(filters=None):
    filters = filters or {}

    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_report_summary(data)

    return columns, data, None, chart, summary


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _has_field(doctype: str, fieldname: str) -> bool:
    try:
        return frappe.get_meta(doctype).has_field(fieldname)
    except Exception:
        return False


def _get_receivable_accounts(company=None):
    conditions = ["account_type = 'Receivable'"]
    values = {}

    if company:
        conditions.append("company = %(company)s")
        values["company"] = company

    return frappe.db.sql(
        f"""
        SELECT name
        FROM `tabAccount`
        WHERE {' AND '.join(conditions)}
        """,
        values,
        pluck=True,
    )


def cint(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


# ------------------------------------------------------------
# Columns
# ------------------------------------------------------------

def get_columns():
    return [
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 170,
        },
        {
            "label": _("Customer Name"),
            "fieldname": "customer_name",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": _("Opening Balance"),
            "fieldname": "opening_balance",
            "fieldtype": "Currency",
            "width": 135,
        },
        {
            "label": _("OPD"),
            "fieldname": "opd",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": _("IPD"),
            "fieldname": "ipd",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": _("Total Credit"),
            "fieldname": "total_credit",
            "fieldtype": "Currency",
            "width": 125,
        },
        {
            "label": _("Today Balance"),
            "fieldname": "today_balance",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Closing Balance"),
            "fieldname": "closing_balance",
            "fieldtype": "Currency",
            "width": 135,
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 160,
        },
    ]


# ------------------------------------------------------------
# Data
# ------------------------------------------------------------

def get_data(filters):
    from_date = getdate(filters.get("from_date")) if filters.get("from_date") else getdate()
    to_date = getdate(filters.get("to_date")) if filters.get("to_date") else getdate()

    if from_date > to_date:
        frappe.throw(_("From Date cannot be greater than To Date"))

    company = filters.get("company")
    customer = filters.get("customer")
    customer_group = filters.get("customer_group")
    territory = filters.get("territory")
    status_filter = filters.get("status") or "All"
    only_with_activity = cint(filters.get("only_with_activity"))
    only_non_zero_balance = cint(filters.get("only_non_zero_balance"))

    receivable_accounts = _get_receivable_accounts(company)
    if not receivable_accounts:
        return []

    si_has_inpatient_record = _has_field("Sales Invoice", "inpatient_record")

    values = {
        "from_date": from_date,
        "to_date": to_date,
        "company": company,
        "customer": customer,
        "customer_group": customer_group,
        "territory": territory,
        "receivable_accounts": tuple(receivable_accounts),
    }

    company_gl_sql = " AND gle.company = %(company)s" if company else ""
    company_si_sql = " AND si.company = %(company)s" if company else ""

    customer_conditions = []
    if customer:
        customer_conditions.append("cust.name = %(customer)s")
    if customer_group:
        customer_conditions.append("cust.customer_group = %(customer_group)s")
    if territory:
        customer_conditions.append("cust.territory = %(territory)s")

    customer_sql = ""
    if customer_conditions:
        customer_sql = " AND " + " AND ".join(customer_conditions)

    # ------------------------------------------------------------
    # STRICT CUSTOMER UNIVERSE:
    # only customers that appear in SI / PE / JE
    # ------------------------------------------------------------
    active_customer_rows = frappe.db.sql(
        f"""
        SELECT DISTINCT
            cust.name AS customer,
            cust.customer_name
        FROM `tabGL Entry` gle
        INNER JOIN `tabCustomer` cust
            ON cust.name = gle.party
        WHERE
            gle.party_type = 'Customer'
            AND IFNULL(gle.party, '') != ''
            AND IFNULL(gle.is_cancelled, 0) = 0
            AND gle.account IN %(receivable_accounts)s
            AND gle.voucher_type IN ('Sales Invoice', 'Payment Entry', 'Journal Entry')
            {company_gl_sql}
            {customer_sql}
        """,
        values,
        as_dict=True,
    )

    if not active_customer_rows:
        return []

    active_customers = {d.customer for d in active_customer_rows}
    customer_name_map = {d.customer: d.customer_name for d in active_customer_rows}

    # ------------------------------------------------------------
    # Opening balance:
    # all GL before from_date, but only for active customers
    # ------------------------------------------------------------
    opening_rows = frappe.db.sql(
        f"""
        SELECT
            gle.party AS customer,
            SUM(IFNULL(gle.debit, 0) - IFNULL(gle.credit, 0)) AS opening_balance
        FROM `tabGL Entry` gle
        WHERE
            gle.party_type = 'Customer'
            AND IFNULL(gle.party, '') != ''
            AND IFNULL(gle.is_cancelled, 0) = 0
            AND gle.posting_date < %(from_date)s
            AND gle.account IN %(receivable_accounts)s
            AND gle.party IN %(active_customers)s
            {company_gl_sql}
        GROUP BY gle.party
        """,
        {**values, "active_customers": tuple(active_customers)},
        as_dict=True,
    )
    opening_map = {d.customer: flt(d.opening_balance) for d in opening_rows}

    # ------------------------------------------------------------
    # OPD/IPD invoice debit during selected period
    # ------------------------------------------------------------
    if si_has_inpatient_record:
        invoice_rows = frappe.db.sql(
            f"""
            SELECT
                cust.name AS customer,
                cust.customer_name,
                SUM(
                    CASE
                        WHEN IFNULL(si.inpatient_record, '') = ''
                        THEN IFNULL(gle.debit, 0)
                        ELSE 0
                    END
                ) AS opd_invoice,
                SUM(
                    CASE
                        WHEN IFNULL(si.inpatient_record, '') != ''
                        THEN IFNULL(gle.debit, 0)
                        ELSE 0
                    END
                ) AS ipd
            FROM `tabGL Entry` gle
            INNER JOIN `tabSales Invoice` si
                ON si.name = gle.voucher_no
               AND gle.voucher_type = 'Sales Invoice'
            INNER JOIN `tabCustomer` cust
                ON cust.name = gle.party
            WHERE
                gle.party_type = 'Customer'
                AND IFNULL(gle.party, '') != ''
                AND IFNULL(gle.is_cancelled, 0) = 0
                AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND gle.account IN %(receivable_accounts)s
                AND IFNULL(gle.debit, 0) > 0
                AND gle.party IN %(active_customers)s
                {company_gl_sql}
                {company_si_sql}
                {customer_sql}
            GROUP BY cust.name, cust.customer_name
            """,
            {**values, "active_customers": tuple(active_customers)},
            as_dict=True,
        )
    else:
        invoice_rows = frappe.db.sql(
            f"""
            SELECT
                cust.name AS customer,
                cust.customer_name,
                SUM(IFNULL(gle.debit, 0)) AS opd_invoice,
                0 AS ipd
            FROM `tabGL Entry` gle
            INNER JOIN `tabSales Invoice` si
                ON si.name = gle.voucher_no
               AND gle.voucher_type = 'Sales Invoice'
            INNER JOIN `tabCustomer` cust
                ON cust.name = gle.party
            WHERE
                gle.party_type = 'Customer'
                AND IFNULL(gle.party, '') != ''
                AND IFNULL(gle.is_cancelled, 0) = 0
                AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND gle.account IN %(receivable_accounts)s
                AND IFNULL(gle.debit, 0) > 0
                AND gle.party IN %(active_customers)s
                {company_gl_sql}
                {company_si_sql}
                {customer_sql}
            GROUP BY cust.name, cust.customer_name
            """,
            {**values, "active_customers": tuple(active_customers)},
            as_dict=True,
        )

    invoice_map = {d.customer: d for d in invoice_rows}

    # ------------------------------------------------------------
    # Other debit during period (non Sales Invoice debit)
    # Business rule: treat other debits as OPD
    # only include JE / PE here if they produce debit rows
    # ------------------------------------------------------------
    other_debit_rows = frappe.db.sql(
        f"""
        SELECT
            gle.party AS customer,
            SUM(IFNULL(gle.debit, 0)) AS other_opd_debit
        FROM `tabGL Entry` gle
        WHERE
            gle.party_type = 'Customer'
            AND IFNULL(gle.party, '') != ''
            AND IFNULL(gle.is_cancelled, 0) = 0
            AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND gle.account IN %(receivable_accounts)s
            AND IFNULL(gle.debit, 0) > 0
            AND gle.voucher_type IN ('Journal Entry', 'Payment Entry')
            AND gle.party IN %(active_customers)s
            {company_gl_sql}
        GROUP BY gle.party
        """,
        {**values, "active_customers": tuple(active_customers)},
        as_dict=True,
    )
    other_debit_map = {d.customer: flt(d.other_opd_debit) for d in other_debit_rows}

    # ------------------------------------------------------------
    # Total Credit during period
    # only from SI / PE / JE
    # ------------------------------------------------------------
    credit_rows = frappe.db.sql(
        f"""
        SELECT
            gle.party AS customer,
            SUM(IFNULL(gle.credit, 0)) AS total_credit
        FROM `tabGL Entry` gle
        WHERE
            gle.party_type = 'Customer'
            AND IFNULL(gle.party, '') != ''
            AND IFNULL(gle.is_cancelled, 0) = 0
            AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND gle.account IN %(receivable_accounts)s
            AND IFNULL(gle.credit, 0) > 0
            AND gle.voucher_type IN ('Sales Invoice', 'Payment Entry', 'Journal Entry')
            AND gle.party IN %(active_customers)s
            {company_gl_sql}
        GROUP BY gle.party
        """,
        {**values, "active_customers": tuple(active_customers)},
        as_dict=True,
    )
    credit_map = {d.customer: flt(d.total_credit) for d in credit_rows}

    data = []
    for cust in active_customers:
        invoice_row = invoice_map.get(cust) or {}

        opening_balance = flt(opening_map.get(cust))
        opd_invoice = flt(invoice_row.get("opd_invoice"))
        ipd = flt(invoice_row.get("ipd"))
        other_opd_debit = flt(other_debit_map.get(cust))
        total_credit = flt(credit_map.get(cust))

        opd = opd_invoice + other_opd_debit
        today_balance = opd + ipd - total_credit
        closing_balance = opening_balance + today_balance

        if closing_balance > 0:
            status = "Customer Owes Us"
        elif closing_balance < 0:
            status = "We Owe Customer"
        else:
            status = "Settled"

        if status_filter == "Customer Owes Us" and closing_balance <= 0:
            continue
        if status_filter == "We Owe Customer" and closing_balance >= 0:
            continue
        if status_filter == "Settled" and abs(closing_balance) > 0.0001:
            continue

        if only_with_activity and not (opd or ipd or total_credit):
            continue

        if only_non_zero_balance and abs(closing_balance) < 0.0001:
            continue

        row = frappe._dict({
            "customer": cust,
            "customer_name": customer_name_map.get(cust) or cust,
            "opening_balance": opening_balance,
            "opd": opd,
            "ipd": ipd,
            "total_credit": total_credit,
            "today_balance": today_balance,
            "closing_balance": closing_balance,
            "status": status,
        })
        data.append(row)

    data.sort(key=lambda d: (-flt(d.closing_balance), d.customer_name or ""))
    return data


# ------------------------------------------------------------
# Chart
# ------------------------------------------------------------

def get_chart(data):
    if not data:
        return None

    total_customer_owes = sum(flt(d.closing_balance) for d in data if flt(d.closing_balance) > 0)
    total_we_owe = abs(sum(flt(d.closing_balance) for d in data if flt(d.closing_balance) < 0))
    settled_count = len([d for d in data if abs(flt(d.closing_balance)) < 0.0001])

    return {
        "data": {
            "labels": [_("Customer Owes Us"), _("We Owe Customer"), _("Settled Count")],
            "datasets": [
                {
                    "name": _("Amount"),
                    "values": [total_customer_owes, total_we_owe, total_settled_count_to_number(settled_count)],
                }
            ],
        },
        "type": "donut",
        "height": 280,
    }


def total_settled_count_to_number(value):
    return flt(value or 0)


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

def get_report_summary(data):
    total_customers = len(data)
    total_opening_balance = sum(flt(d.opening_balance) for d in data)
    total_opd = sum(flt(d.opd) for d in data)
    total_ipd = sum(flt(d.ipd) for d in data)
    total_credit = sum(flt(d.total_credit) for d in data)
    total_today_balance = sum(flt(d.today_balance) for d in data)
    total_closing_balance = sum(flt(d.closing_balance) for d in data)

    total_customer_owes = sum(flt(d.closing_balance) for d in data if flt(d.closing_balance) > 0)
    total_we_owe = abs(sum(flt(d.closing_balance) for d in data if flt(d.closing_balance) < 0))
    settled_count = len([d for d in data if abs(flt(d.closing_balance)) < 0.0001])

    return [
        {
            "label": _("Customers"),
            "value": total_customers,
            "indicator": "Blue",
        },
        {
            "label": _("Opening Balance"),
            "value": total_opening_balance,
            "indicator": "Orange" if total_opening_balance else "Blue",
        },
        {
            "label": _("OPD"),
            "value": total_opd,
            "indicator": "Red" if total_opd else "Blue",
        },
        {
            "label": _("IPD"),
            "value": total_ipd,
            "indicator": "Red" if total_ipd else "Blue",
        },
        {
            "label": _("Total Credit"),
            "value": total_credit,
            "indicator": "Green" if total_credit else "Blue",
        },
        {
            "label": _("Today Balance"),
            "value": total_today_balance,
            "indicator": "Orange" if total_today_balance else "Blue",
        },
        {
            "label": _("Closing Balance"),
            "value": total_closing_balance,
            "indicator": "Orange" if total_closing_balance else "Blue",
        },
        {
            "label": _("Customer Owes Us"),
            "value": total_customer_owes,
            "indicator": "Red" if total_customer_owes else "Blue",
        },
        {
            "label": _("We Owe Customer"),
            "value": total_we_owe,
            "indicator": "Green" if total_we_owe else "Blue",
        },
        {
            "label": _("Settled Count"),
            "value": settled_count,
            "indicator": "Blue",
        },
    ]