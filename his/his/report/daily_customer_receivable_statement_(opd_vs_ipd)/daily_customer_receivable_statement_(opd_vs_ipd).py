# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

# import frappe


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
            "width": 130,
        },
        {
            "label": _("Opening OPD"),
            "fieldname": "opening_opd",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Opening IPD"),
            "fieldname": "opening_ipd",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Opening Total"),
            "fieldname": "opening_total",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Period OPD Debit"),
            "fieldname": "period_opd_debit",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Period OPD Credit"),
            "fieldname": "period_opd_credit",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Period IPD Debit"),
            "fieldname": "period_ipd_debit",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Period IPD Credit"),
            "fieldname": "period_ipd_credit",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Closing OPD"),
            "fieldname": "closing_opd",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Closing IPD"),
            "fieldname": "closing_ipd",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Total Receivable"),
            "fieldname": "closing_total",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Unallocated Credit"),
            "fieldname": "unallocated_credit",
            "fieldtype": "Currency",
            "width": 145,
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
    receivable_type = filters.get("receivable_type") or "All"
    only_with_balance = cint(filters.get("only_with_balance"))
    only_with_unallocated_credit = cint(filters.get("only_with_unallocated_credit"))

    receivable_accounts = _get_receivable_accounts(company)
    if not receivable_accounts:
        return []

    si_has_inpatient_record = _has_field("Sales Invoice", "inpatient_record")

    # if inpatient_record field does not exist, treat everything as OPD
    opd_direct_condition = "1 = 1"
    ipd_direct_condition = "1 = 0"
    opd_against_condition = "1 = 1"
    ipd_against_condition = "1 = 0"

    if si_has_inpatient_record:
        opd_direct_condition = "IFNULL(si_direct.inpatient_record, '') = ''"
        ipd_direct_condition = "IFNULL(si_direct.inpatient_record, '') != ''"
        opd_against_condition = "IFNULL(si_against.inpatient_record, '') = ''"
        ipd_against_condition = "IFNULL(si_against.inpatient_record, '') != ''"

    values = {
        "from_date": from_date,
        "to_date": to_date,
        "company": company,
        "customer": customer,
        "customer_group": customer_group,
        "territory": territory,
        "receivable_accounts": tuple(receivable_accounts),
    }

    company_sql = ""
    if company:
        company_sql = " AND gle.company = %(company)s"

    customer_sql_parts = []
    if customer:
        customer_sql_parts.append("cust.name = %(customer)s")
    if customer_group:
        customer_sql_parts.append("cust.customer_group = %(customer_group)s")
    if territory:
        customer_sql_parts.append("cust.territory = %(territory)s")

    customer_sql = ""
    if customer_sql_parts:
        customer_sql = " AND " + " AND ".join(customer_sql_parts)

    rows = frappe.db.sql(
        f"""
        SELECT
            cust.name AS customer,
            cust.customer_name,
            cust.customer_group,
            cust.territory,

            /* Opening OPD */
            SUM(
                CASE
                    WHEN gle.posting_date < %(from_date)s
                     AND (
                            (gle.voucher_type = 'Sales Invoice' AND {opd_direct_condition})
                            OR
                            (gle.voucher_type != 'Sales Invoice'
                             AND gle.against_voucher_type = 'Sales Invoice'
                             AND {opd_against_condition})
                         )
                    THEN (IFNULL(gle.debit, 0) - IFNULL(gle.credit, 0))
                    ELSE 0
                END
            ) AS opening_opd,

            /* Opening IPD */
            SUM(
                CASE
                    WHEN gle.posting_date < %(from_date)s
                     AND (
                            (gle.voucher_type = 'Sales Invoice' AND {ipd_direct_condition})
                            OR
                            (gle.voucher_type != 'Sales Invoice'
                             AND gle.against_voucher_type = 'Sales Invoice'
                             AND {ipd_against_condition})
                         )
                    THEN (IFNULL(gle.debit, 0) - IFNULL(gle.credit, 0))
                    ELSE 0
                END
            ) AS opening_ipd,

            /* Period OPD debit */
            SUM(
                CASE
                    WHEN gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
                     AND (
                            (gle.voucher_type = 'Sales Invoice' AND {opd_direct_condition})
                            OR
                            (gle.voucher_type != 'Sales Invoice'
                             AND gle.against_voucher_type = 'Sales Invoice'
                             AND {opd_against_condition})
                         )
                    THEN IFNULL(gle.debit, 0)
                    ELSE 0
                END
            ) AS period_opd_debit,

            /* Period OPD credit */
            SUM(
                CASE
                    WHEN gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
                     AND (
                            (gle.voucher_type = 'Sales Invoice' AND {opd_direct_condition})
                            OR
                            (gle.voucher_type != 'Sales Invoice'
                             AND gle.against_voucher_type = 'Sales Invoice'
                             AND {opd_against_condition})
                         )
                    THEN IFNULL(gle.credit, 0)
                    ELSE 0
                END
            ) AS period_opd_credit,

            /* Period IPD debit */
            SUM(
                CASE
                    WHEN gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
                     AND (
                            (gle.voucher_type = 'Sales Invoice' AND {ipd_direct_condition})
                            OR
                            (gle.voucher_type != 'Sales Invoice'
                             AND gle.against_voucher_type = 'Sales Invoice'
                             AND {ipd_against_condition})
                         )
                    THEN IFNULL(gle.debit, 0)
                    ELSE 0
                END
            ) AS period_ipd_debit,

            /* Period IPD credit */
            SUM(
                CASE
                    WHEN gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
                     AND (
                            (gle.voucher_type = 'Sales Invoice' AND {ipd_direct_condition})
                            OR
                            (gle.voucher_type != 'Sales Invoice'
                             AND gle.against_voucher_type = 'Sales Invoice'
                             AND {ipd_against_condition})
                         )
                    THEN IFNULL(gle.credit, 0)
                    ELSE 0
                END
            ) AS period_ipd_credit,

            /* Closing OPD */
            SUM(
                CASE
                    WHEN gle.posting_date <= %(to_date)s
                     AND (
                            (gle.voucher_type = 'Sales Invoice' AND {opd_direct_condition})
                            OR
                            (gle.voucher_type != 'Sales Invoice'
                             AND gle.against_voucher_type = 'Sales Invoice'
                             AND {opd_against_condition})
                         )
                    THEN (IFNULL(gle.debit, 0) - IFNULL(gle.credit, 0))
                    ELSE 0
                END
            ) AS closing_opd,

            /* Closing IPD */
            SUM(
                CASE
                    WHEN gle.posting_date <= %(to_date)s
                     AND (
                            (gle.voucher_type = 'Sales Invoice' AND {ipd_direct_condition})
                            OR
                            (gle.voucher_type != 'Sales Invoice'
                             AND gle.against_voucher_type = 'Sales Invoice'
                             AND {ipd_against_condition})
                         )
                    THEN (IFNULL(gle.debit, 0) - IFNULL(gle.credit, 0))
                    ELSE 0
                END
            ) AS closing_ipd,

            /* Payments / credits not linked to invoice, cannot classify OPD/IPD safely */
            SUM(
                CASE
                    WHEN gle.posting_date <= %(to_date)s
                     AND gle.voucher_type != 'Sales Invoice'
                     AND IFNULL(gle.against_voucher_type, '') != 'Sales Invoice'
                     AND IFNULL(gle.credit, 0) > 0
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
            cust.name, cust.customer_name, cust.customer_group, cust.territory

        ORDER BY
            cust.customer_name ASC
        """,
        values,
        as_dict=True,
    )

    result = []
    for row in rows:
        row.opening_opd = max(flt(row.opening_opd), 0)
        row.opening_ipd = max(flt(row.opening_ipd), 0)
        row.period_opd_debit = flt(row.period_opd_debit)
        row.period_opd_credit = flt(row.period_opd_credit)
        row.period_ipd_debit = flt(row.period_ipd_debit)
        row.period_ipd_credit = flt(row.period_ipd_credit)
        row.closing_opd = max(flt(row.closing_opd), 0)
        row.closing_ipd = max(flt(row.closing_ipd), 0)
        row.unallocated_credit = flt(row.unallocated_credit)

        row.opening_total = row.opening_opd + row.opening_ipd
        row.closing_total = row.closing_opd + row.closing_ipd

        if receivable_type == "OPD" and row.closing_opd <= 0:
            continue
        if receivable_type == "IPD" and row.closing_ipd <= 0:
            continue

        if only_with_balance and row.closing_total <= 0:
            continue

        if only_with_unallocated_credit and row.unallocated_credit <= 0:
            continue

        result.append(row)

    # sort biggest debtors first
    result.sort(key=lambda d: (flt(d.get("closing_total")) * -1, d.get("customer_name") or ""))

    return result


# ------------------------------------------------------------
# Chart
# ------------------------------------------------------------

def get_chart(data):
    if not data:
        return None

    total_opd = sum(flt(d.get("closing_opd")) for d in data)
    total_ipd = sum(flt(d.get("closing_ipd")) for d in data)
    total_unallocated = sum(flt(d.get("unallocated_credit")) for d in data)

    return {
        "data": {
            "labels": [_("OPD Receivable"), _("IPD Receivable"), _("Unallocated Credit")],
            "datasets": [
                {
                    "name": _("Amount"),
                    "values": [total_opd, total_ipd, total_unallocated],
                }
            ],
        },
        "type": "donut",
        "height": 280,
    }


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

def get_report_summary(data):
    total_customers = len(data)
    total_opening_opd = sum(flt(d.get("opening_opd")) for d in data)
    total_opening_ipd = sum(flt(d.get("opening_ipd")) for d in data)
    total_period_opd_debit = sum(flt(d.get("period_opd_debit")) for d in data)
    total_period_opd_credit = sum(flt(d.get("period_opd_credit")) for d in data)
    total_period_ipd_debit = sum(flt(d.get("period_ipd_debit")) for d in data)
    total_period_ipd_credit = sum(flt(d.get("period_ipd_credit")) for d in data)
    total_closing_opd = sum(flt(d.get("closing_opd")) for d in data)
    total_closing_ipd = sum(flt(d.get("closing_ipd")) for d in data)
    total_closing = sum(flt(d.get("closing_total")) for d in data)
    total_unallocated_credit = sum(flt(d.get("unallocated_credit")) for d in data)

    return [
        {
            "label": _("Customers"),
            "value": total_customers,
            "indicator": "Blue",
        },
        {
            "label": _("Opening OPD"),
            "value": total_opening_opd,
            "indicator": "Orange" if total_opening_opd else "Blue",
        },
        {
            "label": _("Opening IPD"),
            "value": total_opening_ipd,
            "indicator": "Orange" if total_opening_ipd else "Blue",
        },
        {
            "label": _("OPD Debit"),
            "value": total_period_opd_debit,
            "indicator": "Red" if total_period_opd_debit else "Blue",
        },
        {
            "label": _("OPD Credit"),
            "value": total_period_opd_credit,
            "indicator": "Green" if total_period_opd_credit else "Blue",
        },
        {
            "label": _("IPD Debit"),
            "value": total_period_ipd_debit,
            "indicator": "Red" if total_period_ipd_debit else "Blue",
        },
        {
            "label": _("IPD Credit"),
            "value": total_period_ipd_credit,
            "indicator": "Green" if total_period_ipd_credit else "Blue",
        },
        {
            "label": _("Closing OPD"),
            "value": total_closing_opd,
            "indicator": "Red" if total_closing_opd else "Blue",
        },
        {
            "label": _("Closing IPD"),
            "value": total_closing_ipd,
            "indicator": "Red" if total_closing_ipd else "Blue",
        },
        {
            "label": _("Total Receivable"),
            "value": total_closing,
            "indicator": "Red" if total_closing else "Green",
        },
        {
            "label": _("Unallocated Credit"),
            "value": total_unallocated_credit,
            "indicator": "Green" if total_unallocated_credit else "Blue",
        },
    ]
