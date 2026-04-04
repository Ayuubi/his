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


def _table_exists(table_name: str) -> bool:
    try:
        return frappe.db.table_exists(table_name)
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
            "width": 180,
        },
        {
            "label": _("Customer Name"),
            "fieldname": "customer_name",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": _("Customer Group"),
            "fieldname": "customer_group",
            "fieldtype": "Link",
            "options": "Customer Group",
            "width": 150,
        },
        {
            "label": _("Territory"),
            "fieldname": "territory",
            "fieldtype": "Link",
            "options": "Territory",
            "width": 140,
        },
        {
            "label": _("Credit Limit"),
            "fieldname": "credit_limit",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Opening Balance"),
            "fieldname": "opening_balance",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Period Debit"),
            "fieldname": "period_debit",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Period Credit"),
            "fieldname": "period_credit",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Closing Balance"),
            "fieldname": "closing_balance",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Available Credit"),
            "fieldname": "available_credit",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Over Limit By"),
            "fieldname": "over_limit_by",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Unallocated Credit"),
            "fieldname": "unallocated_credit",
            "fieldtype": "Currency",
            "width": 140,
        },
    ]


# ------------------------------------------------------------
# Main Data
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
    only_with_balance = cint(filters.get("only_with_balance"))
    only_over_limit = cint(filters.get("only_over_limit"))

    receivable_accounts = _get_receivable_accounts(company)
    if not receivable_accounts:
        return []

    si_has_inpatient_record = _has_field("Sales Invoice", "inpatient_record")
    customer_has_credit_limit = _has_field("Customer", "credit_limit")

    values = {
        "from_date": from_date,
        "to_date": to_date,
        "company": company,
        "customer": customer,
        "customer_group": customer_group,
        "territory": territory,
        "receivable_accounts": tuple(receivable_accounts),
    }

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

    company_sql = ""
    if company:
        company_sql = " AND gle.company = %(company)s"

    # Important logic:
    # 1. Sales Invoice rows -> classify directly using gle.voucher_no
    # 2. Payment Entry / Journal Entry rows -> classify using against_voucher if linked to Sales Invoice
    # 3. Unallocated credits (not linked to Sales Invoice) cannot safely be classified as OPD/IPD,
    #    so we keep them separately in "Unallocated Credit" and exclude them from OPD closing balance.
    #
    # This makes the statement accurate for OPD invoice-linked movements.

    inpatient_condition_direct = "1 = 1"
    inpatient_condition_against = "1 = 1"
    if si_has_inpatient_record:
        inpatient_condition_direct = "IFNULL(si_direct.inpatient_record, '') = ''"
        inpatient_condition_against = "IFNULL(si_against.inpatient_record, '') = ''"

    credit_limit_sql = "IFNULL(cust.credit_limit, 0)" if customer_has_credit_limit else "0"

    rows = frappe.db.sql(
        f"""
        SELECT
            cust.name AS customer,
            cust.customer_name,
            cust.customer_group,
            cust.territory,
            {credit_limit_sql} AS credit_limit,

            /* Opening: all OPD-linked GL before from_date */
            SUM(
                CASE
                    WHEN gle.posting_date < %(from_date)s
                     AND (
                            (gle.voucher_type = 'Sales Invoice' AND {inpatient_condition_direct})
                            OR
                            (gle.voucher_type != 'Sales Invoice'
                             AND gle.against_voucher_type = 'Sales Invoice'
                             AND {inpatient_condition_against})
                         )
                    THEN (IFNULL(gle.debit, 0) - IFNULL(gle.credit, 0))
                    ELSE 0
                END
            ) AS opening_balance,

            /* Period debit: OPD-linked movements in range */
            SUM(
                CASE
                    WHEN gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
                     AND (
                            (gle.voucher_type = 'Sales Invoice' AND {inpatient_condition_direct})
                            OR
                            (gle.voucher_type != 'Sales Invoice'
                             AND gle.against_voucher_type = 'Sales Invoice'
                             AND {inpatient_condition_against})
                         )
                    THEN IFNULL(gle.debit, 0)
                    ELSE 0
                END
            ) AS period_debit,

            /* Period credit: OPD-linked movements in range */
            SUM(
                CASE
                    WHEN gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
                     AND (
                            (gle.voucher_type = 'Sales Invoice' AND {inpatient_condition_direct})
                            OR
                            (gle.voucher_type != 'Sales Invoice'
                             AND gle.against_voucher_type = 'Sales Invoice'
                             AND {inpatient_condition_against})
                         )
                    THEN IFNULL(gle.credit, 0)
                    ELSE 0
                END
            ) AS period_credit,

            /* Closing: all OPD-linked GL up to to_date */
            SUM(
                CASE
                    WHEN gle.posting_date <= %(to_date)s
                     AND (
                            (gle.voucher_type = 'Sales Invoice' AND {inpatient_condition_direct})
                            OR
                            (gle.voucher_type != 'Sales Invoice'
                             AND gle.against_voucher_type = 'Sales Invoice'
                             AND {inpatient_condition_against})
                         )
                    THEN (IFNULL(gle.debit, 0) - IFNULL(gle.credit, 0))
                    ELSE 0
                END
            ) AS closing_balance,

            /* Unallocated credits up to to_date:
               credit GL rows for customer not linked to Sales Invoice */
            SUM(
                CASE
                    WHEN gle.posting_date <= %(to_date)s
                     AND IFNULL(gle.credit, 0) > 0
                     AND gle.voucher_type != 'Sales Invoice'
                     AND IFNULL(gle.against_voucher_type, '') != 'Sales Invoice'
                    THEN IFNULL(gle.credit, 0)
                    ELSE 0
                END
            ) AS unallocated_credit

        FROM `tabGL Entry` gle
        INNER JOIN `tabCustomer` cust
            ON cust.name = gle.party
        LEFT JOIN `tabSales Invoice` si_direct
            ON si_direct.name = gle.voucher_no
           AND gle.voucher_type = 'Sales Invoice'
        LEFT JOIN `tabSales Invoice` si_against
            ON si_against.name = gle.against_voucher
           AND gle.against_voucher_type = 'Sales Invoice'

        WHERE
            gle.party_type = 'Customer'
            AND IFNULL(gle.party, '') != ''
            AND IFNULL(gle.is_cancelled, 0) = 0
            AND gle.account IN %(receivable_accounts)s
            {company_sql}
            {customer_sql}

        GROUP BY
            cust.name, cust.customer_name, cust.customer_group, cust.territory, credit_limit

        ORDER BY
            closing_balance DESC, cust.customer_name ASC
        """,
        values,
        as_dict=True,
    )

    result = []
    for row in rows:
        row.opening_balance = flt(row.opening_balance)
        row.period_debit = flt(row.period_debit)
        row.period_credit = flt(row.period_credit)
        row.closing_balance = flt(row.closing_balance)
        row.credit_limit = flt(row.credit_limit)
        row.unallocated_credit = flt(row.unallocated_credit)

        row.available_credit = row.credit_limit - row.closing_balance if row.credit_limit else 0
        row.over_limit_by = row.closing_balance - row.credit_limit if row.credit_limit and row.closing_balance > row.credit_limit else 0

        if only_with_balance and abs(row.closing_balance) < 0.0001:
            continue

        if only_over_limit and row.over_limit_by <= 0:
            continue

        result.append(row)

    return result


# ------------------------------------------------------------
# Chart
# ------------------------------------------------------------

def get_chart(data):
    if not data:
        return None

    total_balance = sum(flt(d.get("closing_balance")) for d in data)
    total_available = sum(max(flt(d.get("available_credit")), 0) for d in data)
    total_over_limit = sum(flt(d.get("over_limit_by")) for d in data)

    return {
        "data": {
            "labels": [_("Closing Balance"), _("Available Credit"), _("Over Limit")],
            "datasets": [
                {
                    "name": _("Amount"),
                    "values": [total_balance, total_available, total_over_limit],
                }
            ],
        },
        "type": "donut",
        "height": 280,
    }


# ------------------------------------------------------------
# Report Summary
# ------------------------------------------------------------

def get_report_summary(data):
    total_customers = len(data)
    total_opening = sum(flt(d.get("opening_balance")) for d in data)
    total_debit = sum(flt(d.get("period_debit")) for d in data)
    total_credit = sum(flt(d.get("period_credit")) for d in data)
    total_closing = sum(flt(d.get("closing_balance")) for d in data)
    total_unallocated_credit = sum(flt(d.get("unallocated_credit")) for d in data)
    total_over_limit = sum(flt(d.get("over_limit_by")) for d in data)

    return [
        {
            "label": _("Customers"),
            "value": total_customers,
            "indicator": "Blue",
        },
        {
            "label": _("Opening Balance"),
            "value": total_opening,
            "indicator": "Orange" if total_opening else "Blue",
        },
        {
            "label": _("Period Debit"),
            "value": total_debit,
            "indicator": "Red" if total_debit else "Blue",
        },
        {
            "label": _("Period Credit"),
            "value": total_credit,
            "indicator": "Green" if total_credit else "Blue",
        },
        {
            "label": _("Closing Balance"),
            "value": total_closing,
            "indicator": "Red" if total_closing > 0 else "Green",
        },
        {
            "label": _("Unallocated Credit"),
            "value": total_unallocated_credit,
            "indicator": "Green" if total_unallocated_credit else "Blue",
        },
        {
            "label": _("Over Limit"),
            "value": total_over_limit,
            "indicator": "Red" if total_over_limit else "Green",
        },
    ]


def cint(value):
    try:
        return int(value or 0)
    except Exception:
        return 0