# item_wise_sales_register_patient.py
import frappe
from frappe.utils import getdate
from frappe.utils import cint


def _has_field(doctype: str, fieldname: str) -> bool:
    try:
        return frappe.get_meta(doctype).has_field(fieldname)
    except Exception:
        return False


def execute(filters=None):
    filters = frappe._dict(filters or {})

    # -----------------------------
    # Filters / View
    # -----------------------------
    view = (filters.get("view") or "Detail").strip()  # Detail | Summary
    group_by = (filters.get("group_by") or "Item Group").strip()

    from_date = getdate(filters.get("from_date")) if filters.get("from_date") else None
    to_date = getdate(filters.get("to_date")) if filters.get("to_date") else None

    exclude_inpatient = cint(filters.get("exclude_inpatient") or 0)

    age_from = filters.get("age_from")  # treated as YEARS
    age_to = filters.get("age_to")      # treated as YEARS

    # -----------------------------
    # Detect fieldnames (safe)
    # -----------------------------
    inv_patient_field = "patient" if _has_field("Sales Invoice", "patient") else None

    inv_ref_prac_field = "ref_practitioner" if _has_field("Sales Invoice", "ref_practitioner") else (
        "referring_practitioner" if _has_field("Sales Invoice", "referring_practitioner") else None
    )

    # Inpatient Record field on Sales Invoice (customizations vary)
    inv_inpatient_field = "inpatient_record" if _has_field("Sales Invoice", "inpatient_record") else (
        "custom_inpatient_record" if _has_field("Sales Invoice", "custom_inpatient_record") else None
    )

    patient_name_field = "patient_name" if _has_field("Patient", "patient_name") else "name"
    patient_age_field = "p_age" if _has_field("Patient", "p_age") else ("age" if _has_field("Patient", "age") else None)
    patient_age_type_field = "age_type" if _has_field("Patient", "age_type") else None  # values: Year/Month/Day

    sii_net_amount_field = "net_amount" if _has_field("Sales Invoice Item", "net_amount") else "amount"

    # -----------------------------
    # WHERE conditions (shared)
    # -----------------------------
    cond = ["si.docstatus = 1"]
    vals = {}

    if from_date:
        cond.append("si.posting_date >= %(from_date)s")
        vals["from_date"] = from_date
    if to_date:
        cond.append("si.posting_date <= %(to_date)s")
        vals["to_date"] = to_date

    if filters.get("company"):
        cond.append("si.company = %(company)s")
        vals["company"] = filters["company"]

    if filters.get("customer"):
        cond.append("si.customer = %(customer)s")
        vals["customer"] = filters["customer"]

    if filters.get("item_code"):
        cond.append("sii.item_code = %(item_code)s")
        vals["item_code"] = filters["item_code"]

    if filters.get("item_group"):
        cond.append("sii.item_group = %(item_group)s")
        vals["item_group"] = filters["item_group"]

    if filters.get("patient") and inv_patient_field:
        cond.append(f"si.{inv_patient_field} = %(patient)s")
        vals["patient"] = filters["patient"]

    if filters.get("ref_practitioner") and inv_ref_prac_field:
        cond.append(f"si.{inv_ref_prac_field} = %(ref_practitioner)s")
        vals["ref_practitioner"] = filters["ref_practitioner"]

    # Exclude inpatient invoices when checked
    if exclude_inpatient and inv_inpatient_field:
        cond.append(f"IFNULL(si.{inv_inpatient_field}, '') = ''")

    where_sql = " AND ".join(cond)

    # -----------------------------
    # Patient join + Age filtering
    # - Age From/To are interpreted as YEARS
    # - We normalize patient's (age + age_type) into years before comparing
    # -----------------------------
    patient_join = ""
    patient_select = "NULL AS patient_id, NULL AS patient_name, NULL AS age, NULL AS age_type, NULL AS age_years"
    age_cond = ""

    if inv_patient_field:
        patient_join = f"LEFT JOIN `tabPatient` p ON p.name = si.{inv_patient_field}"

        age_expr = f"p.{patient_age_field}" if patient_age_field else "NULL"
        age_type_expr = f"p.{patient_age_type_field}" if patient_age_type_field else "NULL"

        # normalize age to YEARS (Year/Month/Day)
        if patient_age_field and patient_age_type_field:
            age_years_expr = f"""
            CASE
                WHEN p.{patient_age_type_field} = 'Year'  THEN p.{patient_age_field}
                WHEN p.{patient_age_type_field} = 'Month' THEN (p.{patient_age_field} / 12)
                WHEN p.{patient_age_type_field} = 'Day'   THEN (p.{patient_age_field} / 365)
                ELSE p.{patient_age_field}
            END
            """
        else:
            age_years_expr = "NULL"

        patient_select = f"""
            si.{inv_patient_field} AS patient_id,
            p.{patient_name_field} AS patient_name,
            {age_expr} AS age,
            {age_type_expr} AS age_type,
            ({age_years_expr}) AS age_years
        """

        # Apply Age From/To on age_years_expr if available
        if patient_age_field and patient_age_type_field:
            if age_from is not None and str(age_from).strip() != "":
                vals["age_from"] = float(age_from)
                age_cond += f" AND ({age_years_expr}) >= %(age_from)s"

            if age_to is not None and str(age_to).strip() != "":
                vals["age_to"] = float(age_to)
                age_cond += f" AND ({age_years_expr}) <= %(age_to)s"

    # Ref practitioner select
    ref_prac_select = f"si.{inv_ref_prac_field} AS ref_practitioner" if inv_ref_prac_field else "NULL AS ref_practitioner"

    # Inpatient record select (column)
    inpatient_select = f"si.{inv_inpatient_field} AS inpatient_record" if inv_inpatient_field else "NULL AS inpatient_record"

    # -----------------------------
    # Summary Mode (Insights)
    # -----------------------------
    if view == "Summary":
        view_map = {
            "Item": ("sii.item_code", "Item", "Link", "Item"),
            "Item Group": ("sii.item_group", "Item Group", "Link", "Item Group"),
            "Customer": ("si.customer", "Customer", "Link", "Customer"),
            "Invoice": ("si.name", "Sales Invoice", "Link", "Sales Invoice"),
            "Posting Date": ("si.posting_date", "Posting Date", "Date", None),
        }

        if inv_patient_field:
            view_map["Patient"] = (f"si.{inv_patient_field}", "Patient", "Link", "Patient")
        if inv_ref_prac_field:
            view_map["Practitioner"] = (f"si.{inv_ref_prac_field}", "Ref Practitioner", "Link", "Healthcare Practitioner")
        if inv_inpatient_field:
            view_map["Inpatient Record"] = (f"si.{inv_inpatient_field}", "Inpatient Record", "Link", "Inpatient Record")

        group_expr, group_label, group_fieldtype, group_options = view_map.get(group_by, view_map["Item Group"])

        columns = [
            {"label": group_label, "fieldname": "group_key", "fieldtype": group_fieldtype, "options": group_options, "width": 220},
            {"label": "Invoices", "fieldname": "invoice_count", "fieldtype": "Int", "width": 90},
            {"label": "Lines", "fieldname": "line_count", "fieldtype": "Int", "width": 80},
            {"label": "Qty", "fieldname": "qty_sum", "fieldtype": "Float", "width": 90},
            {"label": "Net Amount", "fieldname": "net_amount_sum", "fieldtype": "Currency", "width": 130},
        ]

        data = frappe.db.sql(
            f"""
            SELECT
                {group_expr} AS group_key,
                COUNT(DISTINCT si.name) AS invoice_count,
                COUNT(*) AS line_count,
                COALESCE(SUM(sii.qty),0) AS qty_sum,
                COALESCE(SUM(sii.{sii_net_amount_field}),0) AS net_amount_sum
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            {patient_join}
            WHERE {where_sql} {age_cond}
            GROUP BY {group_expr}
            ORDER BY net_amount_sum DESC
            """,
            vals,
            as_dict=True,
        )

        totals = frappe.db.sql(
            f"""
            SELECT
                COUNT(DISTINCT si.name) AS invoices,
                COUNT(*) AS lines_count,
                COALESCE(SUM(sii.qty),0) AS qty,
                COALESCE(SUM(sii.{sii_net_amount_field}),0) AS net_amount
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            {patient_join}
            WHERE {where_sql} {age_cond}
            """,
            vals,
            as_dict=True,
        )[0]

        report_summary = [
            {"label": "Net Amount", "value": totals.get("net_amount") or 0, "indicator": "Green"},
            {"label": "Invoices", "value": totals.get("invoices") or 0, "indicator": "Blue"},
            {"label": "Lines", "value": totals.get("lines_count") or 0, "indicator": "Orange"},
            {"label": "Qty", "value": totals.get("qty") or 0, "indicator": "Purple"},
        ]

        top = data[:10]
        chart = {
            "data": {
                "labels": [str(r.get("group_key") or "N/A") for r in top],
                "datasets": [{"name": "Net Amount", "values": [float(r.get("net_amount_sum") or 0) for r in top]}],
            },
            "type": "bar",
        }

        return columns, data, None, chart, report_summary

    # -----------------------------
    # Detail Mode (Line-level)
    # -----------------------------
    columns = [
        {"label": "Sales Invoice", "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 160},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 105},
        {"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 140},


        {"label": "Patient ID", "fieldname": "patient_id", "fieldtype": "Link", "options": "Patient", "width": 140},
        {"label": "Patient Name", "fieldname": "patient_name", "fieldtype": "Data", "width": 200},

        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 200, "hidden": 1},

        {"label": "Age", "fieldname": "age", "fieldtype": "Int", "width": 60},
        {"label": "Age Type", "fieldname": "age_type", "fieldtype": "Data", "width": 80},
        {"label": "Age (Years)", "fieldname": "age_years", "fieldtype": "Float", "width": 95, "hidden": 1},

        {"label": "Ref Practitioner", "fieldname": "ref_practitioner", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 170},

        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 140},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 220, "hidden": 1},
        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 140},

        {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 70},
        {"label": "Rate", "fieldname": "rate", "fieldtype": "Currency", "width": 90},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 100},
        {"label": "Discount Amount", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 120, "hidden": 1},
        {"label": "Net Amount", "fieldname": "net_amount", "fieldtype": "Currency", "width": 110},

        {"label": "Income Account", "fieldname": "income_account", "fieldtype": "Link", "options": "Account", "width": 160, "hidden": 1},
        {"label": "Cost Center", "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 140, "hidden": 1},
        {"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 120, "hidden": 1},
        {"label": "Inpatient Record", "fieldname": "inpatient_record", "fieldtype": "Link", "options": "Inpatient Record", "width": 160},
    ]

    data = frappe.db.sql(
        f"""
        SELECT
            si.name AS sales_invoice,
            si.posting_date AS posting_date,
            si.company AS company,

            {inpatient_select},

            {patient_select},
            si.customer AS customer,

            {ref_prac_select},

            sii.item_code AS item_code,
            sii.item_name AS item_name,
            sii.item_group AS item_group,

            sii.qty AS qty,
            sii.rate AS rate,
            sii.amount AS amount,
            sii.discount_amount AS discount_amount,
            sii.{sii_net_amount_field} AS net_amount,

            sii.income_account AS income_account,
            sii.cost_center AS cost_center,
            sii.project AS project
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        {patient_join}
        WHERE {where_sql} {age_cond}
        ORDER BY si.posting_date DESC, si.name DESC, sii.idx ASC
        """,
        vals,
        as_dict=True,
    )

    return columns, data

# # # =========================================================================
# # # 
# # # =========================================================================

# # item_wise_sales_register_patient.py
# import frappe
# from frappe.utils import getdate


# def _has_field(doctype: str, fieldname: str) -> bool:
#     try:
#         return frappe.get_meta(doctype).has_field(fieldname)
#     except Exception:
#         return False


# def execute(filters=None):
#     filters = frappe._dict(filters or {})

#     # -----------------------------
#     # Filters / View
#     # -----------------------------
#     view = (filters.get("view") or "Detail").strip()  # Detail | Summary
#     group_by = (filters.get("group_by") or "Item Group").strip()

#     from_date = getdate(filters.get("from_date")) if filters.get("from_date") else None
#     to_date = getdate(filters.get("to_date")) if filters.get("to_date") else None

#     # -----------------------------
#     # Detect fieldnames (safe)
#     # -----------------------------
#     inv_patient_field = "patient" if _has_field("Sales Invoice", "patient") else None

#     inv_ref_prac_field = "ref_practitioner" if _has_field("Sales Invoice", "ref_practitioner") else (
#         "referring_practitioner" if _has_field("Sales Invoice", "referring_practitioner") else None
#     )

#     patient_name_field = "patient_name" if _has_field("Patient", "patient_name") else "name"
#     patient_age_field = "p_age" if _has_field("Patient", "p_age") else ("age" if _has_field("Patient", "age") else None)
#     patient_age_type_field = "age_type" if _has_field("Patient", "age_type") else None

#     sii_net_amount_field = "net_amount" if _has_field("Sales Invoice Item", "net_amount") else "amount"

#     # -----------------------------
#     # WHERE conditions (shared)
#     # -----------------------------
#     cond = ["si.docstatus = 1"]
#     vals = {}

#     if from_date:
#         cond.append("si.posting_date >= %(from_date)s")
#         vals["from_date"] = from_date
#     if to_date:
#         cond.append("si.posting_date <= %(to_date)s")
#         vals["to_date"] = to_date

#     if filters.get("company"):
#         cond.append("si.company = %(company)s")
#         vals["company"] = filters["company"]

#     if filters.get("customer"):
#         cond.append("si.customer = %(customer)s")
#         vals["customer"] = filters["customer"]

#     if filters.get("item_code"):
#         cond.append("sii.item_code = %(item_code)s")
#         vals["item_code"] = filters["item_code"]

#     if filters.get("item_group"):
#         cond.append("sii.item_group = %(item_group)s")
#         vals["item_group"] = filters["item_group"]

#     if filters.get("patient") and inv_patient_field:
#         cond.append(f"si.{inv_patient_field} = %(patient)s")
#         vals["patient"] = filters["patient"]

#     if filters.get("ref_practitioner") and inv_ref_prac_field:
#         cond.append(f"si.{inv_ref_prac_field} = %(ref_practitioner)s")
#         vals["ref_practitioner"] = filters["ref_practitioner"]

#     where_sql = " AND ".join(cond)

#     # -----------------------------
#     # Summary Mode (Insights)
#     # -----------------------------
#     if view == "Summary":
#         # Map group_by choices to SQL expressions (only safe known options)
#         # IMPORTANT: Patient/Practitioner require fields to exist; fallback to Customer/Item Group.
#         view_map = {
#             "Item": ("sii.item_code", "Item", "Link", "Item"),
#             "Item Group": ("sii.item_group", "Item Group", "Link", "Item Group"),
#             "Customer": ("si.customer", "Customer", "Link", "Customer"),
#             "Invoice": ("si.name", "Sales Invoice", "Link", "Sales Invoice"),
#             "Posting Date": ("si.posting_date", "Posting Date", "Date", None),
#         }

#         if inv_patient_field:
#             view_map["Patient"] = (f"si.{inv_patient_field}", "Patient", "Link", "Patient")
#         if inv_ref_prac_field:
#             view_map["Practitioner"] = (f"si.{inv_ref_prac_field}", "Ref Practitioner", "Link", "Healthcare Practitioner")

#         group_expr, group_label, group_fieldtype, group_options = view_map.get(
#             group_by, view_map["Item Group"]
#         )

#         columns = [
#             {"label": group_label, "fieldname": "group_key", "fieldtype": group_fieldtype, "options": group_options, "width": 220},
#             {"label": "Invoices", "fieldname": "invoice_count", "fieldtype": "Int", "width": 90},
#             {"label": "Lines", "fieldname": "line_count", "fieldtype": "Int", "width": 80},
#             {"label": "Qty", "fieldname": "qty_sum", "fieldtype": "Float", "width": 90},
#             {"label": "Net Amount", "fieldname": "net_amount_sum", "fieldtype": "Currency", "width": 130},
#         ]

#         data = frappe.db.sql(
#             f"""
#             SELECT
#                 {group_expr} AS group_key,
#                 COUNT(DISTINCT si.name) AS invoice_count,
#                 COUNT(*) AS line_count,
#                 COALESCE(SUM(sii.qty),0) AS qty_sum,
#                 COALESCE(SUM(sii.{sii_net_amount_field}),0) AS net_amount_sum
#             FROM `tabSales Invoice Item` sii
#             INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
#             WHERE {where_sql}
#             GROUP BY {group_expr}
#             ORDER BY net_amount_sum DESC
#             """,
#             vals,
#             as_dict=True,
#         )

#         totals = frappe.db.sql(
#             f"""
#             SELECT
#                 COUNT(DISTINCT si.name) AS invoices,
#                 COUNT(*) AS lines_count,
#                 COALESCE(SUM(sii.qty),0) AS qty,
#                 COALESCE(SUM(sii.{sii_net_amount_field}),0) AS net_amount
#             FROM `tabSales Invoice Item` sii
#             INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
#             WHERE {where_sql}
#             """,
#             vals,
#             as_dict=True,
#         )[0]

#         report_summary = [
#             {"label": "Net Amount", "value": totals.get("net_amount") or 0, "indicator": "Green"},
#             {"label": "Invoices", "value": totals.get("invoices") or 0, "indicator": "Blue"},
#             {"label": "Lines", "value": totals.get("lines_count") or 0, "indicator": "Orange"},
#             {"label": "Qty", "value": totals.get("qty") or 0, "indicator": "Purple"},
#         ]

#         # Bar chart: Top 10 by Net Amount
#         top = data[:10]
#         chart = {
#             "data": {
#                 "labels": [str(r.get("group_key") or "N/A") for r in top],
#                 "datasets": [
#                     {"name": "Net Amount", "values": [float(r.get("net_amount_sum") or 0) for r in top]}
#                 ],
#             },
#             "type": "bar",
#         }

#         return columns, data, None, chart, report_summary

#     # -----------------------------
#     # Detail Mode (Line-level)
#     # -----------------------------
#     columns = [
#         {"label": "Sales Invoice", "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 160},
#         {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 105},
#         {"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 140},

#         {"label": "Patient ID", "fieldname": "patient_id", "fieldtype": "Link", "options": "Patient", "width": 140},
#         {"label": "Patient Name", "fieldname": "patient_name", "fieldtype": "Data", "width": 200},

#         {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 200},

#         {"label": "Age", "fieldname": "age", "fieldtype": "Int", "width": 60},
#         {"label": "Age Type", "fieldname": "age_type", "fieldtype": "Data", "width": 80},

#         {"label": "Ref Practitioner", "fieldname": "ref_practitioner", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 170},

#         {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 140},
#         {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 220},
#         {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 140},

#         {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 70},
#         {"label": "Rate", "fieldname": "rate", "fieldtype": "Currency", "width": 90},
#         {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 100},
#         {"label": "Discount Amount", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 120},
#         {"label": "Net Amount", "fieldname": "net_amount", "fieldtype": "Currency", "width": 110},

#         {"label": "Income Account", "fieldname": "income_account", "fieldtype": "Link", "options": "Account", "width": 160},
#         {"label": "Cost Center", "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 140},
#         {"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 120},
#     ]

#     patient_join = ""
#     patient_select = "NULL AS patient_id, NULL AS patient_name, NULL AS age, NULL AS age_type"

#     if inv_patient_field:
#         patient_join = f"LEFT JOIN `tabPatient` p ON p.name = si.{inv_patient_field}"
#         age_expr = f"p.{patient_age_field}" if patient_age_field else "NULL"
#         age_type_expr = f"p.{patient_age_type_field}" if patient_age_type_field else "NULL"
#         patient_select = f"""
#             si.{inv_patient_field} AS patient_id,
#             p.{patient_name_field} AS patient_name,
#             {age_expr} AS age,
#             {age_type_expr} AS age_type
#         """

#     ref_prac_select = f"si.{inv_ref_prac_field} AS ref_practitioner" if inv_ref_prac_field else "NULL AS ref_practitioner"

#     data = frappe.db.sql(
#         f"""
#         SELECT
#             si.name AS sales_invoice,
#             si.posting_date AS posting_date,
#             si.company AS company,

#             {patient_select},
#             si.customer AS customer,

#             {ref_prac_select},

#             sii.item_code AS item_code,
#             sii.item_name AS item_name,
#             sii.item_group AS item_group,

#             sii.qty AS qty,
#             sii.rate AS rate,
#             sii.amount AS amount,
#             sii.discount_amount AS discount_amount,
#             sii.{sii_net_amount_field} AS net_amount,

#             sii.income_account AS income_account,
#             sii.cost_center AS cost_center,
#             sii.project AS project
#         FROM `tabSales Invoice Item` sii
#         INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
#         {patient_join}
#         WHERE {where_sql}
#         ORDER BY si.posting_date DESC, si.name DESC, sii.idx ASC
#         """,
#         vals,
#         as_dict=True,
#     )

#     return columns, data

# # # =========================================================================
# # # 
# # # =========================================================================