import frappe
from frappe import _

ALL_SOURCE_ORDER_NAME = "All"  # from your list

def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    if not from_date or not to_date:
        frappe.throw(_("Please set From Date and To Date."))

    practitioner = filters.get("practitioner")
    source_order = filters.get("source_order")
    item_group = filters.get("item_group")

    sql = """
        SELECT
            cp.start_date AS posting_date,
            cp.name AS service_dn,
            cp.patient AS patient,

            COALESCE(si.source_order, %(all_source_order)s) AS service_source_order,

            cp.practitioner AS practitioner,
            hp.practitioner_name AS practitioner_name,

            sii.item_group AS item_group,
            COALESCE(sii.net_amount, sii.amount, 0) AS base_amount,

            -- pick BEST matching commission percent (exact source_order wins over All)
            COALESCE((
                SELECT cr.percent
                FROM `tabCommission` cr
                WHERE cr.parent = hp.name
                  AND cr.parenttype = 'Healthcare Practitioner'
                  AND cr.parentfield = 'commission'
                  AND cr.item_group = sii.item_group
                  AND (cr.source_order = COALESCE(si.source_order, %(all_source_order)s)
                       OR cr.source_order = %(all_source_order)s)
                ORDER BY (cr.source_order = COALESCE(si.source_order, %(all_source_order)s)) DESC
                LIMIT 1
            ), 0) AS commission_percent,

            -- same logic for showing which rule source_order got applied
            (
                SELECT cr.source_order
                FROM `tabCommission` cr
                WHERE cr.parent = hp.name
                  AND cr.parenttype = 'Healthcare Practitioner'
                  AND cr.parentfield = 'commission'
                  AND cr.item_group = sii.item_group
                  AND (cr.source_order = COALESCE(si.source_order, %(all_source_order)s)
                       OR cr.source_order = %(all_source_order)s)
                ORDER BY (cr.source_order = COALESCE(si.source_order, %(all_source_order)s)) DESC
                LIMIT 1
            ) AS rule_source_order,

            (
              COALESCE(sii.net_amount, sii.amount, 0) *
              (COALESCE((
                SELECT cr.percent
                FROM `tabCommission` cr
                WHERE cr.parent = hp.name
                  AND cr.parenttype = 'Healthcare Practitioner'
                  AND cr.parentfield = 'commission'
                  AND cr.item_group = sii.item_group
                  AND (cr.source_order = COALESCE(si.source_order, %(all_source_order)s)
                       OR cr.source_order = %(all_source_order)s)
                ORDER BY (cr.source_order = COALESCE(si.source_order, %(all_source_order)s)) DESC
                LIMIT 1
              ), 0) / 100.0)
            ) AS commission_amount,

            cp.sales_invoice AS sales_invoice
        FROM `tabClinical Procedure` cp
        LEFT JOIN `tabSales Invoice` si ON si.name = cp.sales_invoice
        LEFT JOIN `tabSales Invoice Item` sii ON sii.name = cp.sales_invoice_item
        JOIN `tabHealthcare Practitioner` hp ON hp.name = cp.practitioner
        WHERE cp.status = 'Completed'
          AND DATE(cp.start_date) BETWEEN %(from_date)s AND %(to_date)s
          AND sii.item_group IS NOT NULL
          {practitioner_clause}
          {source_order_clause}
          {item_group_clause}
        ORDER BY cp.start_date, cp.name
    """.format(
        practitioner_clause=" AND cp.practitioner = %(practitioner)s " if practitioner else "",
        source_order_clause=" AND COALESCE(si.source_order, %(all_source_order)s) = %(source_order)s " if source_order else "",
        item_group_clause=" AND sii.item_group = %(item_group)s " if item_group else "",
    )

    data = frappe.db.sql(sql, {
        "from_date": from_date,
        "to_date": to_date,
        "practitioner": practitioner,
        "source_order": source_order,
        "item_group": item_group,
        "all_source_order": ALL_SOURCE_ORDER_NAME,
    }, as_dict=True)

    columns = [
        {"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Datetime", "width": 140},
        {"label": _("Service"), "fieldname": "service_dn", "fieldtype": "Link", "options": "Clinical Procedure", "width": 180},
        {"label": _("Patient"), "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 140},
        {"label": _("Source Order"), "fieldname": "service_source_order", "fieldtype": "Link", "options": "Source Order", "width": 110},
        {"label": _("Doctor"), "fieldname": "practitioner", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 170},
        {"label": _("Doctor Name"), "fieldname": "practitioner_name", "fieldtype": "Data", "width": 180},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 140},
        {"label": _("Rule Source Order"), "fieldname": "rule_source_order", "fieldtype": "Link", "options": "Source Order", "width": 120},
        {"label": _("Percent"), "fieldname": "commission_percent", "fieldtype": "Float", "width": 80},
        {"label": _("Base Amount"), "fieldname": "base_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Commission"), "fieldname": "commission_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Sales Invoice"), "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 160},
    ]

    total_comm = sum(float(d.get("commission_amount") or 0) for d in data) if data else 0
    summary = [{"label": _("Total Commission"), "value": total_comm, "indicator": "green" if total_comm else "gray"}]

    return columns, data, None, None, summary
