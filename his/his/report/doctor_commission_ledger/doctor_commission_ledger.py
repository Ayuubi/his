from __future__ import annotations

import frappe
from frappe.utils import getdate

# -----------------------------
# CONFIG (your schema)
# -----------------------------
RADIOLOGY_DOCTYPE = "Radiology"
RAD_INVOICE_FIELD = "reff_invoice"
RAD_SII_FIELD = "sales_invoice_item"
RAD_PRACT_FIELD = "practitioner"
RAD_DATE_FIELD = "date"

CP_DOCTYPE = "Clinical Procedure"
CP_INVOICE_FIELD = "sales_invoice"
CP_SII_FIELD = "sales_invoice_item"
CP_PRACT_FIELD = "practitioner"
CP_DATE_FIELD = "start_date"

LAB_DOCTYPE = "Lab Result"
LAB_INVOICE_FIELD = "sales_invoice"
LAB_PRACT_FIELD = "practitioner"
LAB_DATE_FIELD = "date"
LAB_PARENT_SII_FIELD = "sales_invoice_item"  # if exists

# Lab Result child doctype (you are using doctype name here)
LAB_CHILD_TABLE = "Normal Test Result"
LAB_CHILD_SII_FIELD = "sales_invoice_item"

# Commission child doctype table name
COMM_REF_TABLE = "`tabCommisions Reference`"

# Roles that can see all doctors
PRIV_ROLES = {"System Manager", "Accounts Manager"}


# -----------------------------
# Permission helpers
# -----------------------------
def user_has_any_role(roles, user=None) -> bool:
    user = user or frappe.session.user
    user_roles = set(frappe.get_roles(user) or [])
    return any(r in user_roles for r in roles)

def _get_practitioner_for_user(user=None):
    """
    Try both common fieldnames:
      - Healthcare Practitioner.user_id
      - Healthcare Practitioner.user
    """
    user = user or frappe.session.user
    pr = frappe.db.get_value("Healthcare Practitioner", {"user_id": user}, "name")
    if pr:
        return pr
    return frappe.db.get_value("Healthcare Practitioner", {"user": user}, "name")

def _restrict_to_doctor(filters):
    """
    System Manager / Accounts Manager: see all
    Others: forced to their own practitioner (blocks if not mapped).
    """
    if user_has_any_role(PRIV_ROLES):
        return

    pr = filters.get("practitioner") or _get_practitioner_for_user()
    if pr:
        filters["practitioner"] = pr
    else:
        filters["practitioner"] = "__no_such_practitioner__"


# -----------------------------
# Commission group helpers
# -----------------------------
def _get_invoice_commission_item_groups():
    """
    HIS Settings child table: invoice_commission_item_groups (fieldname)
    """
    hs = frappe.get_doc("HIS Settings", "HIS Settings")
    rows = hs.get("invoice_commission_item_groups") or []
    return {(r.item_group or "").strip() for r in rows if (r.item_group or "").strip()}

def _get_practitioner_commission_item_groups(practitioner: str):
    """
    Healthcare Practitioner child table: commission (fieldname)
    """
    if not practitioner:
        return set()
    hpr = frappe.get_doc("Healthcare Practitioner", practitioner)
    return {(r.item_group or "").strip() for r in (hpr.commission or []) if (r.item_group or "").strip()}


def execute(filters=None):
    filters = frappe._dict(filters or {})
    _restrict_to_doctor(filters)

    from_date = getdate(filters.get("from_date")) if filters.get("from_date") else None
    to_date = getdate(filters.get("to_date")) if filters.get("to_date") else None

    practitioner = filters.get("practitioner")
    source_order = (filters.get("source_order") or "").strip()
    item_group = (filters.get("item_group") or "").strip()
    status = (filters.get("status") or "").strip()
    work_doctype = (filters.get("work_doctype") or "").strip()

    # -----------------------------
    # Build UNION of work lines
    # -----------------------------
    union_parts = []
    union_params = []

    # Radiology
    rad_where = ["r.docstatus = 1"]
    rad_params = []
    if practitioner:
        rad_where.append(f"r.`{RAD_PRACT_FIELD}` = %s")
        rad_params.append(practitioner)
    if from_date:
        rad_where.append(f"r.`{RAD_DATE_FIELD}` >= %s")
        rad_params.append(from_date)
    if to_date:
        rad_where.append(f"r.`{RAD_DATE_FIELD}` <= %s")
        rad_params.append(to_date)

    rad_sql = f"""
      SELECT
        '{RADIOLOGY_DOCTYPE}' AS work_doctype,
        r.name AS work_name,
        r.`{RAD_PRACT_FIELD}` AS practitioner,
        r.`{RAD_DATE_FIELD}` AS work_date,
        r.`{RAD_INVOICE_FIELD}` AS sales_invoice,
        r.`{RAD_SII_FIELD}` AS sales_invoice_item
      FROM `tab{RADIOLOGY_DOCTYPE}` r
      WHERE {" AND ".join(rad_where)}
    """
    union_parts.append(rad_sql)
    union_params += rad_params

    # Clinical Procedure
    cp_where = ["c.docstatus = 1"]
    cp_params = []
    if practitioner:
        cp_where.append(f"c.`{CP_PRACT_FIELD}` = %s")
        cp_params.append(practitioner)
    if from_date:
        cp_where.append(f"c.`{CP_DATE_FIELD}` >= %s")
        cp_params.append(from_date)
    if to_date:
        cp_where.append(f"c.`{CP_DATE_FIELD}` <= %s")
        cp_params.append(to_date)

    cp_sql = f"""
      SELECT
        '{CP_DOCTYPE}' AS work_doctype,
        c.name AS work_name,
        c.`{CP_PRACT_FIELD}` AS practitioner,
        c.`{CP_DATE_FIELD}` AS work_date,
        c.`{CP_INVOICE_FIELD}` AS sales_invoice,
        c.`{CP_SII_FIELD}` AS sales_invoice_item
      FROM `tab{CP_DOCTYPE}` c
      WHERE {" AND ".join(cp_where)}
    """
    union_parts.append(cp_sql)
    union_params += cp_params

    # Lab Result - child rows
    lab_child_where = [
        "l.docstatus = 1",
        f"IFNULL(TRIM(l.`{LAB_INVOICE_FIELD}`),'') != ''",
        f"IFNULL(TRIM(li.`{LAB_CHILD_SII_FIELD}`),'') != ''",
        f"IFNULL(TRIM(l.`{LAB_PARENT_SII_FIELD}`),'') = ''",   # ✅ group labs: ignore children
    ]

    lab_child_params = []
    if practitioner:
        lab_child_where.append(f"l.`{LAB_PRACT_FIELD}` = %s")
        lab_child_params.append(practitioner)
    if from_date:
        lab_child_where.append(f"l.`{LAB_DATE_FIELD}` >= %s")
        lab_child_params.append(from_date)
    if to_date:
        lab_child_where.append(f"l.`{LAB_DATE_FIELD}` <= %s")
        lab_child_params.append(to_date)

    lab_child_sql = f"""
        SELECT
            '{LAB_DOCTYPE}' AS work_doctype,
            l.name AS work_name,
            l.`{LAB_PRACT_FIELD}` AS practitioner,
            l.`{LAB_DATE_FIELD}` AS work_date,
            l.`{LAB_INVOICE_FIELD}` AS sales_invoice,
            NULLIF(TRIM(li.`{LAB_CHILD_SII_FIELD}`), '') AS sales_invoice_item
        FROM `tab{LAB_DOCTYPE}` l
        JOIN `tab{LAB_CHILD_TABLE}` li ON li.parent = l.name
        WHERE {" AND ".join(lab_child_where)}
        """
    union_parts.append(lab_child_sql)
    union_params += lab_child_params

    # Lab Result - parent row (optional)
    lab_meta = frappe.get_meta(LAB_DOCTYPE)
    if lab_meta.has_field(LAB_PARENT_SII_FIELD):
        lab_where = [
            "l.docstatus = 1",
            f"IFNULL(TRIM(l.`{LAB_INVOICE_FIELD}`),'') != ''",
            f"IFNULL(TRIM(l.`{LAB_PARENT_SII_FIELD}`),'') != ''",
        ]
        lab_params = []
        if practitioner:
            lab_where.append(f"l.`{LAB_PRACT_FIELD}` = %s")
            lab_params.append(practitioner)
        if from_date:
            lab_where.append(f"l.`{LAB_DATE_FIELD}` >= %s")
            lab_params.append(from_date)
        if to_date:
            lab_where.append(f"l.`{LAB_DATE_FIELD}` <= %s")
            lab_params.append(to_date)

        lab_parent_sql = f"""
          SELECT
            '{LAB_DOCTYPE}' AS work_doctype,
            l.name AS work_name,
            l.`{LAB_PRACT_FIELD}` AS practitioner,
            l.`{LAB_DATE_FIELD}` AS work_date,
            l.`{LAB_INVOICE_FIELD}` AS sales_invoice,
            l.`{LAB_PARENT_SII_FIELD}` AS sales_invoice_item
          FROM `tab{LAB_DOCTYPE}` l
          WHERE {" AND ".join(lab_where)}
        """
        union_parts.append(lab_parent_sql)
        union_params += lab_params

    # Sales Invoice commission lines (ONLY eligible groups)
    invoice_groups = _get_invoice_commission_item_groups()
    if practitioner:
        pr_groups = _get_practitioner_commission_item_groups(practitioner)
        invoice_groups = invoice_groups.intersection(pr_groups)

    if invoice_groups:
        placeholders = ", ".join(["%s"] * len(invoice_groups))

        si_where = ["si.docstatus = 1", "si.is_return = 0", "si.ref_practitioner IS NOT NULL"]
        si_params = []

        # VERY IMPORTANT: params order MUST match placeholder order in SQL
        if practitioner:
            si_where.append("si.ref_practitioner = %s")
            si_params.append(practitioner)

        if from_date:
            si_where.append("si.posting_date >= %s")
            si_params.append(from_date)

        if to_date:
            si_where.append("si.posting_date <= %s")
            si_params.append(to_date)

        # IN list placeholders appear LAST -> params added LAST
        si_params.extend(list(invoice_groups))

        si_sql = f"""
          SELECT
            'Sales Invoice' AS work_doctype,
            si.name AS work_name,
            si.ref_practitioner AS practitioner,
            si.posting_date AS work_date,
            si.name AS sales_invoice,
            sii.name AS sales_invoice_item
          FROM `tabSales Invoice` si
          JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
          WHERE {" AND ".join(si_where)}
            AND sii.item_group IN ({placeholders})
        """
        union_parts.append(si_sql)
        union_params += si_params

    union_sql = " UNION ALL ".join(union_parts)

    # -----------------------------
    # Join to invoice/item and paid commission
    # -----------------------------
    sql = f"""
      WITH sent AS (
        {union_sql}
      ),
      paid AS (
        SELECT
          cr.sales_invoice_item,
          SUM(cr.commission) AS commission_amount,
          MAX(je.posting_date) AS last_je_date,
          GROUP_CONCAT(DISTINCT je.name) AS journal_entries
        FROM `tabJournal Entry` je
        JOIN {COMM_REF_TABLE} cr ON cr.parent = je.name
        WHERE je.docstatus = 1
        GROUP BY cr.sales_invoice_item
      )
      SELECT
        s.work_date,
        s.practitioner,
        hp.employee,
        s.work_doctype,
        s.work_name,

        si.name AS sales_invoice,
        si.posting_date AS invoice_date,
        si.docstatus AS invoice_docstatus,
        si.source_order,

        sii.name AS sales_invoice_item,
        sii.item_code,
        sii.item_group,
        sii.net_amount,

        COALESCE(p.commission_amount, 0) AS commission_amount,
        p.journal_entries,
        p.last_je_date
      FROM sent s
      LEFT JOIN `tabSales Invoice Item` sii ON sii.name = s.sales_invoice_item
      LEFT JOIN `tabSales Invoice` si ON si.name = COALESCE(sii.parent, s.sales_invoice)
      LEFT JOIN `tabHealthcare Practitioner` hp ON hp.name = s.practitioner
      LEFT JOIN paid p ON p.sales_invoice_item = s.sales_invoice_item
      WHERE 1=1
    """

    q_params = list(union_params)

    if practitioner:
        sql += " AND s.practitioner = %s"
        q_params.append(practitioner)

    if source_order:
        sql += " AND si.source_order = %s"
        q_params.append(source_order)

    if item_group:
        sql += " AND sii.item_group = %s"
        q_params.append(item_group)

    if work_doctype:
        sql += " AND s.work_doctype = %s"
        q_params.append(work_doctype)

    rows = frappe.db.sql(sql, tuple(q_params), as_dict=True)

    # -----------------------------
    # Derive status
    # -----------------------------
    data = []
    for r in rows:
        inv_ds = r.get("invoice_docstatus")
        comm = float(r.get("commission_amount") or 0)

        if not r.get("sales_invoice") or not r.get("sales_invoice_item"):
            r["status"] = "Not Billed"
        elif inv_ds == 2:
            r["status"] = "Cancelled"
        elif inv_ds == 0:
            r["status"] = "Draft"
        elif inv_ds == 1 and comm > 0:
            r["status"] = "Paid"
        elif inv_ds == 1 and comm == 0:
            r["status"] = "Pending"
        elif inv_ds == 1 and comm < 0:
            r["status"] = "Reversed"
        else:
            r["status"] = "Unknown"

        if status and r["status"] != status:
            continue

        data.append(r)

    columns = [
        {"label": "Work Date", "fieldname": "work_date", "fieldtype": "Date", "width": 95},
        {"label": "Practitioner", "fieldname": "practitioner", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 170},
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 150},

        {"label": "Work DocType", "fieldname": "work_doctype", "fieldtype": "Data", "width": 120},
        {"label": "Work Document", "fieldname": "work_name", "fieldtype": "Dynamic Link", "options": "work_doctype", "width": 160},

        {"label": "Sales Invoice", "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 150},
        {"label": "Invoice Date", "fieldname": "invoice_date", "fieldtype": "Date", "width": 95},
        {"label": "Invoice Docstatus", "fieldname": "invoice_docstatus", "fieldtype": "Int", "width": 110},
        {"label": "Source Order", "fieldname": "source_order", "fieldtype": "Data", "width": 90},

        {"label": "Sales Invoice Item", "fieldname": "sales_invoice_item", "fieldtype": "Link", "options": "Sales Invoice Item", "width": 160},
        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 120},

        {"label": "Net Amount", "fieldname": "net_amount", "fieldtype": "Currency", "width": 110},
        {"label": "Commission", "fieldname": "commission_amount", "fieldtype": "Currency", "width": 110},

        {"label": "Journal Entries", "fieldname": "journal_entries", "fieldtype": "Data", "width": 180},
        {"label": "Last JE Date", "fieldname": "last_je_date", "fieldtype": "Date", "width": 95},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]

    # Better chart: Count + Commission Total per status
    status_order = ["Not Billed", "Draft", "Pending", "Paid", "Cancelled", "Reversed", "Unknown"]
    count_by = {k: 0 for k in status_order}
    comm_by = {k: 0.0 for k in status_order}

    for r in data:
        st = r.get("status") or "Unknown"
        if st not in count_by:
            count_by[st] = 0
            comm_by[st] = 0.0
        count_by[st] += 1
        comm_by[st] += float(r.get("commission_amount") or 0)

    labels = [k for k in status_order if count_by.get(k)]
    chart = {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Count", "values": [count_by[k] for k in labels]},
                {"name": "Commission Total", "values": [comm_by[k] for k in labels]},
            ],
        },
        "type": "bar",
    }

    return columns, data, None, chart
