import frappe

TABLE_FIELD = "credit_limits"
TARGET_FIELD = "credit_limit"


def _patient_customer_fieldname():
    try:
        meta = frappe.get_meta("Patient")
    except Exception:
        return None

    # common possibilities (Healthcare / HIS customizations)
    for f in ("customer", "linked_customer", "customer_name"):
        if meta.has_field(f):
            return f
    return None


def execute(filters=None):
    filters = frappe._dict(filters or {})

    patient_customer_field = _patient_customer_fieldname()

    columns = [
        {"label": "Changed On", "fieldname": "changed_on", "fieldtype": "Datetime", "width": 160},
        {"label": "Changed By", "fieldname": "changed_by", "fieldtype": "Link", "options": "User", "width": 200},
        {"label": "Changed By Name", "fieldname": "changed_by_name", "fieldtype": "Data", "width": 180},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 260},
        {"label": "Patient ID", "fieldname": "patient_id", "fieldtype": "Link", "options": "Patient", "width": 140},
        {"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 200},
        {"label": "Old Credit Limit", "fieldname": "old_limit", "fieldtype": "Data", "width": 140},
        {"label": "New Credit Limit", "fieldname": "new_limit", "fieldtype": "Data", "width": 140},
        {"label": "Row #", "fieldname": "row_idx", "fieldtype": "Int", "width": 70},
        {"label": "Credit Limit Row", "fieldname": "row_id", "fieldtype": "Link", "options": "Customer Credit Limit", "width": 170},
        {"label": "Version", "fieldname": "version_name", "fieldtype": "Link", "options": "Version", "width": 120},
    ]

    cond = ["v.ref_doctype = 'Customer'"]
    values = {}

    if filters.get("from_date"):
        cond.append("v.creation >= %(from_date)s")
        values["from_date"] = filters.from_date

    if filters.get("to_date"):
        cond.append("v.creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)")
        values["to_date"] = filters.to_date

    if filters.get("changed_by"):
        cond.append("v.owner = %(changed_by)s")
        values["changed_by"] = filters.changed_by

    if filters.get("customer"):
        cond.append("v.docname = %(customer)s")
        values["customer"] = filters.customer

    values["like_row_changed"] = '%"row_changed"%'
    where_clause = " AND ".join(cond)

    # Patient join (only if we can identify the correct link field)
    patient_join = ""
    patient_select = "NULL AS patient_id"
    patient_where = ""

    if patient_customer_field:
        patient_join = f"""
            LEFT JOIN `tabPatient` p
                ON p.`{patient_customer_field}` = c.name
        """
        patient_select = "p.name AS patient_id"
        if filters.get("patient_id"):
            patient_where = " AND p.name = %(patient_id)s"
            values["patient_id"] = filters.patient_id
    else:
        if filters.get("patient_id"):
            return columns, []

    # IMPORTANT: keep limit reasonable (you can increase if needed)
    limit = int(filters.get("limit") or 2000)

    versions = frappe.db.sql(f"""
        SELECT
            v.name AS version_name,
            v.creation AS changed_on,
            v.owner AS changed_by,
            u.full_name AS changed_by_name,
            v.docname AS customer,
            {patient_select},
            v.data
        FROM `tabVersion` v
        LEFT JOIN `tabCustomer` c ON c.name = v.docname
        {patient_join}
        LEFT JOIN `tabUser` u ON u.name = v.owner
        WHERE {where_clause}
          AND v.data LIKE %(like_row_changed)s
          {patient_where}
        ORDER BY v.creation DESC
        LIMIT {limit}
    """, values, as_dict=True)

    if not versions:
        return columns, []

    # ---------- PERFORMANCE FIX ----------
    # Parse versions ONCE, collect row_ids we need company for, then bulk fetch companies
    parsed = []
    row_ids = set()

    for v in versions:
        payload = frappe.parse_json(v.data) or {}
        row_changed = payload.get("row_changed") or []
        if not row_changed:
            continue

        for entry in row_changed:
            if not entry or len(entry) < 4:
                continue
            table_field, row_idx, row_id, changes = entry[0], entry[1], entry[2], entry[3]
            if table_field != TABLE_FIELD:
                continue
            if not isinstance(changes, list):
                continue

            # store for later processing
            parsed.append((v, row_idx, row_id, changes))
            row_ids.add(row_id)

    if not parsed:
        return columns, []

    # Bulk company fetch in ONE query (instead of N queries)
    company_by_row = {}
    if row_ids:
        rows = frappe.db.sql("""
            SELECT name, company
            FROM `tabCustomer Credit Limit`
            WHERE name IN %(names)s
        """, {"names": tuple(row_ids)}, as_dict=True)
        company_by_row = {r["name"]: r["company"] for r in rows}

    out = []
    for v, row_idx, row_id, changes in parsed:
        company = company_by_row.get(row_id)

        if filters.get("company") and company != filters.company:
            continue

        for ch in changes:
            if not ch or len(ch) < 3:
                continue
            fieldname, old, new = ch[0], ch[1], ch[2]
            if fieldname == TARGET_FIELD:
                out.append({
                    "changed_on": v.changed_on,
                    "changed_by": v.changed_by,
                    "changed_by_name": v.changed_by_name,
                    "customer": v.customer,
                    "patient_id": v.patient_id,
                    "company": company,
                    "old_limit": old,
                    "new_limit": new,
                    "row_idx": row_idx,
                    "row_id": row_id,
                    "version_name": v.version_name,
                })

    return columns, out

# import frappe

# TABLE_FIELD = "credit_limits"
# TARGET_FIELD = "credit_limit"


# def _patient_customer_fieldname():
#     """Find the fieldname in Patient that links to Customer."""
#     try:
#         meta = frappe.get_meta("Patient")
#     except Exception:
#         return None

#     # common possibilities (Healthcare / HIS customizations)
#     candidates = ["customer", "linked_customer", "customer_name"]
#     for f in candidates:
#         if meta.has_field(f):
#             return f

#     return None


# def execute(filters=None):
#     filters = frappe._dict(filters or {})

#     # Detect Patient->Customer link field
#     patient_customer_field = _patient_customer_fieldname()

#     columns = [
#         {"label": "Changed On", "fieldname": "changed_on", "fieldtype": "Datetime", "width": 160},

#         {"label": "Changed By", "fieldname": "changed_by", "fieldtype": "Link", "options": "User", "width": 200},
#         {"label": "Changed By Name", "fieldname": "changed_by_name", "fieldtype": "Data", "width": 180},

#         {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 260},

#         # Patient ID should be the Patient.name (like SHP-547681)
#         {"label": "Patient ID", "fieldname": "patient_id", "fieldtype": "Link", "options": "Patient", "width": 140},

#         {"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 200},

#         # these are strings from Version like "$ 0.01"
#         {"label": "Old Credit Limit", "fieldname": "old_limit", "fieldtype": "Data", "width": 140},
#         {"label": "New Credit Limit", "fieldname": "new_limit", "fieldtype": "Data", "width": 140},

#         {"label": "Row #", "fieldname": "row_idx", "fieldtype": "Int", "width": 70},
#         {"label": "Credit Limit Row", "fieldname": "row_id", "fieldtype": "Link", "options": "Customer Credit Limit", "width": 170},
#         {"label": "Version", "fieldname": "version_name", "fieldtype": "Link", "options": "Version", "width": 120},
#     ]

#     cond = ["v.ref_doctype = 'Customer'"]
#     values = {}

#     if filters.get("from_date"):
#         cond.append("v.creation >= %(from_date)s")
#         values["from_date"] = filters.from_date

#     if filters.get("to_date"):
#         cond.append("v.creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)")
#         values["to_date"] = filters.to_date

#     if filters.get("changed_by"):
#         cond.append("v.owner = %(changed_by)s")
#         values["changed_by"] = filters.changed_by

#     if filters.get("customer"):
#         cond.append("v.docname = %(customer)s")
#         values["customer"] = filters.customer

#     # LIKE param to avoid % formatting crash
#     values["like_row_changed"] = '%"row_changed"%'

#     where_clause = " AND ".join(cond)

#     # Patient join (best effort)
#     # If patient_customer_field is not found, we still run report without patient_id.
#     patient_join = ""
#     patient_select = "NULL AS patient_id"
#     patient_where = ""

#     if patient_customer_field:
#         # Join Patient where Patient.<field> == Customer.name
#         patient_join = f"""
#             LEFT JOIN `tabPatient` p
#                 ON p.`{patient_customer_field}` = c.name
#         """
#         patient_select = "p.name AS patient_id"

#         # Patient ID filter: by Patient.name
#         if filters.get("patient_id"):
#             patient_where = " AND p.name = %(patient_id)s"
#             values["patient_id"] = filters.patient_id
#     else:
#         # if user filters by patient_id but we can't join, return empty safely
#         if filters.get("patient_id"):
#             return columns, []

#     versions = frappe.db.sql(f"""
#         SELECT
#             v.name AS version_name,
#             v.creation AS changed_on,
#             v.owner AS changed_by,
#             u.full_name AS changed_by_name,
#             v.docname AS customer,
#             {patient_select},
#             v.data
#         FROM `tabVersion` v
#         LEFT JOIN `tabCustomer` c
#             ON c.name = v.docname
#         {patient_join}
#         LEFT JOIN `tabUser` u
#             ON u.name = v.owner
#         WHERE {where_clause}
#           AND v.data LIKE %(like_row_changed)s
#           {patient_where}
#         ORDER BY v.creation DESC
#         LIMIT 5000
#     """, values, as_dict=True)

#     out = []
#     for v in versions:
#         payload = frappe.parse_json(v.data) or {}
#         row_changed = payload.get("row_changed") or []

#         for entry in row_changed:
#             if not entry or len(entry) < 4:
#                 continue

#             table_field, row_idx, row_id, changes = entry[0], entry[1], entry[2], entry[3]

#             if table_field != TABLE_FIELD:
#                 continue

#             if not isinstance(changes, list):
#                 continue

#             company = frappe.db.get_value("Customer Credit Limit", row_id, "company")
#             if filters.get("company") and company != filters.company:
#                 continue

#             for ch in changes:
#                 if not ch or len(ch) < 3:
#                     continue

#                 fieldname, old, new = ch[0], ch[1], ch[2]
#                 if fieldname == TARGET_FIELD:
#                     out.append({
#                         "changed_on": v.changed_on,
#                         "changed_by": v.changed_by,
#                         "changed_by_name": v.changed_by_name,
#                         "customer": v.customer,
#                         "patient_id": v.patient_id,   # Patient.name (SHP-...)
#                         "company": company,
#                         "old_limit": old,
#                         "new_limit": new,
#                         "row_idx": row_idx,
#                         "row_id": row_id,
#                         "version_name": v.version_name,
#                     })

#     return columns, out