import frappe


def execute(filters=None):
    filters = filters or {}

    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    report_type = filters.get("report_type") or "Detail"
    customer_group = filters.get("customer_group")
    item_group = filters.get("item_group")

    user_roles = frappe.get_roles(frappe.session.user)

    can_see_all = (
        "System Manager" in user_roles
        or "Accounts Manager" in user_roles
        or "Accounts User" in user_roles
        or "Auditor" in user_roles
    )

    is_crm = (
        "CRM" in user_roles
        or "Marketing" in user_roles
    )

    excluded_item_groups = []

    if is_crm and not can_see_all:
        excluded_item_groups = [
            "OT",
            "Drug",
            "Consultation",
            "Anesthesia",
            "ENT Procedure",
            "Services"
        ]

    conditions = """
        si.docstatus = 1
        AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
        AND IFNULL(sii.amount, 0) > IFNULL(sii.net_amount, 0)
    """

    values = {
        "from_date": from_date,
        "to_date": to_date
    }

    if not can_see_all:
        if is_crm:
            conditions += " AND c.customer_group IN ('Membership', 'Corporate')"
        else:
            conditions += " AND c.customer_group = 'Membership'"

    if customer_group:
        conditions += " AND c.customer_group = %(customer_group)s"
        values["customer_group"] = customer_group

    if item_group:
        if excluded_item_groups and item_group in excluded_item_groups:
            conditions += " AND 1 = 0"
        else:
            conditions += " AND sii.item_group = %(item_group)s"
            values["item_group"] = item_group
    else:
        if excluded_item_groups:
            conditions += " AND sii.item_group NOT IN %(excluded_item_groups)s"
            values["excluded_item_groups"] = tuple(excluded_item_groups)

    if report_type == "Summary":
        columns = [
            {"label": "Customer Group", "fieldname": "customer_group", "fieldtype": "Data", "width": 180},
            {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Data", "width": 180},
            {"label": "Invoices", "fieldname": "invoice_count", "fieldtype": "Int", "width": 100},
            {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 100},
            {"label": "Original Amount", "fieldname": "original_amount", "fieldtype": "Currency", "width": 160},
            {"label": "Billed Amount", "fieldname": "billed_amount", "fieldtype": "Currency", "width": 160},
            {"label": "Discount Amount", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 170},
            {"label": "Discount %", "fieldname": "discount_percentage", "fieldtype": "Percent", "width": 120},
        ]

        data = frappe.db.sql("""
            SELECT
                c.customer_group,
                sii.item_group,
                COUNT(DISTINCT si.name) AS invoice_count,
                SUM(sii.qty) AS qty,
                SUM(sii.amount) AS original_amount,
                SUM(sii.net_amount) AS billed_amount,
                SUM(sii.amount - sii.net_amount) AS discount_amount,
                CASE
                    WHEN SUM(sii.amount) > 0
                    THEN ROUND((SUM(sii.amount - sii.net_amount) / SUM(sii.amount)) * 100, 2)
                    ELSE 0
                END AS discount_percentage
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si
                ON si.name = sii.parent
            LEFT JOIN `tabCustomer` c
                ON c.name = si.customer
            WHERE {conditions}
            GROUP BY c.customer_group, sii.item_group
            ORDER BY c.customer_group, discount_amount DESC
        """.format(conditions=conditions), values, as_dict=True)

    else:
        columns = [
            {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 120},
            {"label": "Invoice", "fieldname": "invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 190},
            {"label": "Customer", "fieldname": "customer_name", "fieldtype": "Data", "width": 260},
            {"label": "Customer Group", "fieldname": "customer_group", "fieldtype": "Data", "width": 170},
            {"label": "Item", "fieldname": "item_name", "fieldtype": "Data", "width": 320},
            {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Data", "width": 160},
            {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 80},
            {"label": "Original Amount", "fieldname": "original_amount", "fieldtype": "Currency", "width": 150},
            {"label": "Billed Amount", "fieldname": "billed_amount", "fieldtype": "Currency", "width": 150},
            {"label": "Discount Amount", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 160},
            {"label": "Discount %", "fieldname": "discount_percentage", "fieldtype": "Percent", "width": 120},
        ]

        data = frappe.db.sql("""
            SELECT
                si.posting_date AS date,
                si.name AS invoice,
                si.customer_name,
                c.customer_group,
                sii.item_name,
                sii.item_group,
                sii.qty,
                sii.amount AS original_amount,
                sii.net_amount AS billed_amount,
                (sii.amount - sii.net_amount) AS discount_amount,
                CASE
                    WHEN IFNULL(sii.amount, 0) > 0
                    THEN ROUND(((sii.amount - sii.net_amount) / sii.amount) * 100, 2)
                    ELSE 0
                END AS discount_percentage
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si
                ON si.name = sii.parent
            LEFT JOIN `tabCustomer` c
                ON c.name = si.customer
            WHERE {conditions}
            ORDER BY si.posting_date, si.name, sii.idx
        """.format(conditions=conditions), values, as_dict=True)

    return columns, data