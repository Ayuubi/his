# Copyright (c) 2026
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, today, flt


def execute(filters=None):
    filters = filters or {}

    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart(data, filters)
    report_summary = get_report_summary(filters)

    return columns, data, None, chart, report_summary


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


def _user_permission_value_sql(user_expr: str, allow_value: str) -> str:
    return f"""
        (
            SELECT up.for_value
            FROM `tabUser Permission` up
            WHERE up.user = {user_expr}
              AND up.allow = '{allow_value}'
            ORDER BY IFNULL(up.is_default, 0) DESC, up.creation ASC
            LIMIT 1
        )
    """


def _pos_profile_cost_center_sql(user_expr: str) -> str:
    if _table_exists("tabPOS Profile User") and _table_exists("tabPOS Profile"):
        return f"""
            (
                SELECT pp.cost_center
                FROM `tabPOS Profile User` ppu
                INNER JOIN `tabPOS Profile` pp ON pp.name = ppu.parent
                WHERE ppu.user = {user_expr}
                  AND IFNULL(pp.disabled, 0) = 0
                ORDER BY pp.modified DESC, pp.creation DESC
                LIMIT 1
            )
        """

    if _table_exists("tabPOS Profile") and _has_field("POS Profile", "user"):
        return f"""
            (
                SELECT pp.cost_center
                FROM `tabPOS Profile` pp
                WHERE pp.user = {user_expr}
                  AND IFNULL(pp.disabled, 0) = 0
                ORDER BY pp.modified DESC, pp.creation DESC
                LIMIT 1
            )
        """

    return "NULL"


def _resolved_company_sql(user_expr: str) -> str:
    return _user_permission_value_sql(user_expr, "Company")


def _resolved_sales_type_sql(user_expr: str) -> str:
    return _user_permission_value_sql(user_expr, "Sales Type")


def _resolved_cost_center_sql(user_expr: str) -> str:
    return f"""
        COALESCE(
            {_user_permission_value_sql(user_expr, "Cost Center")},
            {_pos_profile_cost_center_sql(user_expr)}
        )
    """


def get_columns(filters):
    if filters.get("view_type") == "Detailed":
        return [
            {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
            {"label": _("Invoice"), "fieldname": "invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 170},
            {"label": _("User"), "fieldname": "owner", "fieldtype": "Link", "options": "User", "width": 190},
            {"label": _("User Name"), "fieldname": "user_name", "fieldtype": "Data", "width": 220},
            {"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 180},
            {"label": _("Sales Type"), "fieldname": "sales_type", "fieldtype": "Data", "width": 120},
            {"label": _("Cost Center"), "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 180},
            {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 200},
            {"label": _("Patient"), "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 170},
            {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
            {"label": _("Is Return"), "fieldname": "is_return", "fieldtype": "Check", "width": 90},
            {"label": _("Return Against"), "fieldname": "return_against", "fieldtype": "Link", "options": "Sales Invoice", "width": 170},
            {"label": _("Document Status"), "fieldname": "docstatus_label", "fieldtype": "Data", "width": 130},
        ]

    return [
        {"label": _("User"), "fieldname": "owner", "fieldtype": "Link", "options": "User", "width": 190},
        {"label": _("User Name"), "fieldname": "user_name", "fieldtype": "Data", "width": 220},
        {"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 180},
        {"label": _("Sales Type"), "fieldname": "sales_type", "fieldtype": "Data", "width": 120},
        {"label": _("Cost Center"), "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 180},
        {"label": _("Transactions"), "fieldname": "transactions", "fieldtype": "Int", "width": 130},
        {"label": _("Returns"), "fieldname": "returns", "fieldtype": "Int", "width": 100},
    ]


def get_conditions(filters):
    conditions = []
    values = {
        "from_date": getdate(filters.get("from_date") or today()),
        "to_date": getdate(filters.get("to_date") or today()),
    }

    owner_expr = "si.owner"
    company_sql = _resolved_company_sql(owner_expr)
    sales_type_sql = _resolved_sales_type_sql(owner_expr)
    cost_center_sql = _resolved_cost_center_sql(owner_expr)

    conditions.append("si.posting_date BETWEEN %(from_date)s AND %(to_date)s")

    if filters.get("user"):
        conditions.append("si.owner = %(user)s")
        values["user"] = filters.get("user")

    if filters.get("company"):
        conditions.append(f"{company_sql} = %(company)s")
        values["company"] = filters.get("company")

    if filters.get("cost_center"):
        conditions.append(f"{cost_center_sql} = %(cost_center)s")
        values["cost_center"] = filters.get("cost_center")

    if filters.get("sales_type"):
        conditions.append(f"{sales_type_sql} = %(sales_type)s")
        values["sales_type"] = filters.get("sales_type")

    if filters.get("status"):
        if filters.get("status") == "Draft":
            conditions.append("si.docstatus = 0")
        elif filters.get("status") == "Cancelled":
            conditions.append("si.docstatus = 2")
        else:
            conditions.append("si.status = %(status)s")
            values["status"] = filters.get("status")

    if not filters.get("include_draft"):
        conditions.append("si.docstatus != 0")

    if not filters.get("include_cancelled"):
        conditions.append("si.docstatus != 2")

    if filters.get("return_only"):
        conditions.append("IFNULL(si.is_return, 0) = 1")

    return " AND ".join(conditions), values


def get_data(filters):
    return get_detail(filters) if filters.get("view_type") == "Detailed" else get_summary(filters)


def get_summary(filters):
    conditions, values = get_conditions(filters)

    owner_expr = "si.owner"
    company_sql = _resolved_company_sql(owner_expr)
    sales_type_sql = _resolved_sales_type_sql(owner_expr)
    cost_center_sql = _resolved_cost_center_sql(owner_expr)

    data = frappe.db.sql(
        f"""
        SELECT
            si.owner AS owner,
            COALESCE(u.full_name, si.owner) AS user_name,
            {company_sql} AS company,
            {sales_type_sql} AS sales_type,
            {cost_center_sql} AS cost_center,
            COUNT(si.name) AS transactions,
            SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN 1 ELSE 0 END) AS returns
        FROM `tabSales Invoice` si
        LEFT JOIN `tabUser` u
            ON u.name = si.owner
        WHERE {conditions}
        GROUP BY
            si.owner,
            COALESCE(u.full_name, si.owner),
            {company_sql},
            {sales_type_sql},
            {cost_center_sql}
        ORDER BY transactions DESC, si.owner ASC
        """,
        values,
        as_dict=1,
    )

    return data


def get_detail(filters):
    conditions, values = get_conditions(filters)

    owner_expr = "si.owner"
    company_sql = _resolved_company_sql(owner_expr)
    sales_type_sql = _resolved_sales_type_sql(owner_expr)
    cost_center_sql = _resolved_cost_center_sql(owner_expr)

    data = frappe.db.sql(
        f"""
        SELECT
            si.posting_date,
            si.name AS invoice,
            si.owner AS owner,
            COALESCE(u.full_name, si.owner) AS user_name,
            {company_sql} AS company,
            {sales_type_sql} AS sales_type,
            {cost_center_sql} AS cost_center,
            si.customer,
            si.patient,
            si.status,
            IFNULL(si.is_return, 0) AS is_return,
            si.return_against,
            CASE
                WHEN si.docstatus = 0 THEN 'Draft'
                WHEN si.docstatus = 1 THEN 'Submitted'
                WHEN si.docstatus = 2 THEN 'Cancelled'
                ELSE ''
            END AS docstatus_label
        FROM `tabSales Invoice` si
        LEFT JOIN `tabUser` u
            ON u.name = si.owner
        WHERE {conditions}
        ORDER BY si.posting_date DESC, si.creation DESC
        """,
        values,
        as_dict=1,
    )

    return data


def get_chart(data, filters):
    if not data:
        return None

    # Best chart for summary view
    if filters.get("view_type") == "Summary":
        top_rows = data[:10]
        labels = [row.get("user_name") or row.get("owner") for row in top_rows]
        values = [flt(row.get("transactions")) for row in top_rows]

        return {
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "name": "Transactions",
                        "values": values
                    }
                ]
            },
            "type": "bar",
            "height": 280,
            "barOptions": {
                "spaceRatio": 0.25
            }
        }

    # Detailed view chart by status
    status_count = {}
    for row in data:
        key = row.get("docstatus_label") or row.get("status") or "Unknown"
        status_count[key] = status_count.get(key, 0) + 1

    labels = list(status_count.keys())
    values = list(status_count.values())

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Transactions",
                    "values": values
                }
            ]
        },
        "type": "donut",
        "height": 280
    }


def get_report_summary(filters):
    conditions, values = get_conditions(filters)

    summary = frappe.db.sql(
        f"""
        SELECT
            COUNT(si.name) AS total_transactions,
            COUNT(DISTINCT si.owner) AS total_users,
            SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN 1 ELSE 0 END) AS total_returns,
            SUM(CASE WHEN si.docstatus = 0 THEN 1 ELSE 0 END) AS total_drafts,
            SUM(CASE WHEN si.docstatus = 2 THEN 1 ELSE 0 END) AS total_cancelled
        FROM `tabSales Invoice` si
        WHERE {conditions}
        """,
        values,
        as_dict=1,
    )[0]

    total_transactions = flt(summary.get("total_transactions"))
    total_users = flt(summary.get("total_users"))
    total_returns = flt(summary.get("total_returns"))
    total_drafts = flt(summary.get("total_drafts"))
    total_cancelled = flt(summary.get("total_cancelled"))

    return [
        {
            "value": total_transactions,
            "label": _("Total Transactions"),
            "datatype": "Int",
            "indicator": "Blue",
        },
        {
            "value": total_users,
            "label": _("Active Users"),
            "datatype": "Int",
            "indicator": "Green",
        },
        {
            "value": total_returns,
            "label": _("Returns"),
            "datatype": "Int",
            "indicator": "Orange",
        },
        {
            "value": total_drafts,
            "label": _("Drafts"),
            "datatype": "Int",
            "indicator": "Yellow",
        },
        {
            "value": total_cancelled,
            "label": _("Cancelled"),
            "datatype": "Int",
            "indicator": "Red",
        },
    ]