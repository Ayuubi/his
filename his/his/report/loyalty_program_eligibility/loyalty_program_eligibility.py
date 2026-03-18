import frappe
from frappe.utils import getdate, add_days, nowdate, flt, cint

PATIENT_FIELD = "patient"  # change if your fieldname differs


def execute(filters=None):
    filters = filters or {}

    days_window = cint(filters.get("days_window") or 180)
    to_date = getdate(filters.get("to_date") or nowdate())
    from_date = getdate(filters.get("from_date") or add_days(to_date, -days_window))

    points_per_visit = cint(filters.get("points_per_visit") or 2)
    min_visit_days = cint(filters.get("min_visit_days") or 25)
    min_spending = flt(filters.get("min_spending") or 2000)
    eligibility_mode = (filters.get("eligibility_mode") or "OR").upper()

    only_submitted = cint(filters.get("only_submitted") or 1)
    company = filters.get("company")
    patient = filters.get("patient")
    customer = filters.get("customer")

    # --- Conditions ---
    cond = []
    values = {
        "from_date": from_date,
        "to_date": to_date,
    }

    cond.append("si.posting_date BETWEEN %(from_date)s AND %(to_date)s")
    cond.append("si.is_return = 0")

    if only_submitted:
        cond.append("si.docstatus = 1")
    else:
        cond.append("si.docstatus IN (0,1)")

    if company:
        cond.append("si.company = %(company)s")
        values["company"] = company

    if patient:
        cond.append(f"si.{PATIENT_FIELD} = %(patient)s")
        values["patient"] = patient

    if customer:
        cond.append("si.customer = %(customer)s")
        values["customer"] = customer

    where_clause = " AND ".join(cond)

    # --- Group per patient/customer ---
    # Visit Days = distinct posting_date (so multiple invoices same day count as 1 visit day)
    rows = frappe.db.sql(
        f"""
        SELECT
            si.customer,
            si.{PATIENT_FIELD} AS patient,
            COUNT(DISTINCT si.posting_date) AS visit_days,
            SUM(si.grand_total) AS total_spending
        FROM `tabSales Invoice` si
        WHERE {where_clause}
        GROUP BY si.customer, si.{PATIENT_FIELD}
        ORDER BY total_spending DESC
        """,
        values,
        as_dict=True
    )

    # --- Get patient name + mobile in bulk (avoid N+1) ---
    patient_ids = [r.get("patient") for r in rows if r.get("patient")]

    patient_map = {}
    if patient_ids:
        pdata = frappe.db.sql(
            """
            SELECT name, patient_name, mobile_no
            FROM `tabPatient`
            WHERE name IN %(names)s
            """,
            {"names": tuple(set(patient_ids))},
            as_dict=True,
        )
        patient_map = {p["name"]: p for p in pdata}

    columns = get_columns()

    data = []
    for r in rows:
        visit_days = cint(r.get("visit_days") or 0)
        total_spending = flt(r.get("total_spending") or 0)
        points = visit_days * points_per_visit

        by_visits = visit_days >= min_visit_days
        by_spending = total_spending >= min_spending

        if eligibility_mode == "AND":
            eligible = by_visits and by_spending
        else:
            eligible = by_visits or by_spending

        if by_visits and by_spending:
            eligible_by = "Both"
        elif by_visits:
            eligible_by = "Visits"
        elif by_spending:
            eligible_by = "Spending"
        else:
            eligible_by = "None"

        patient_id = r.get("patient")
        p = patient_map.get(patient_id) if patient_id else {}
        patient_name = (p or {}).get("patient_name")
        mobile = (p or {}).get("mobile_no")

        data.append({
            "patient": patient_id,
            "patient_name": patient_name,
            "customer": r.get("customer"),
            "mobile": mobile,
            "visit_days": visit_days,
            "points": points,
            "total_spending": total_spending,
            "eligible_by": eligible_by,
            "status": "✅ ELIGIBLE" if eligible else "❌ NOT ELIGIBLE",
            "period": f"{from_date} to {to_date}",
        })

    return columns, data


def get_columns():
    return [
        {"label": "Patient ID", "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 140},
        {"label": "Patient Name", "fieldname": "patient_name", "fieldtype": "Data", "width": 200},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 200},
        {"label": "Mobile", "fieldname": "mobile", "fieldtype": "Data", "width": 140},

        {"label": "Visit Days", "fieldname": "visit_days", "fieldtype": "Int", "width": 90},
        {"label": "Points", "fieldname": "points", "fieldtype": "Int", "width": 80},

        {"label": "Total Spending", "fieldname": "total_spending", "fieldtype": "Currency", "width": 130},
        {"label": "Eligible By", "fieldname": "eligible_by", "fieldtype": "Data", "width": 110},

        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 130},
        {"label": "Period", "fieldname": "period", "fieldtype": "Data", "width": 200},
    ]

# import frappe
# from frappe.utils import getdate, add_days, nowdate, flt, cint

# PATIENT_FIELD = "patient"  # change if your fieldname differs

# def execute(filters=None):
#     filters = filters or {}

#     days_window = cint(filters.get("days_window") or 180)
#     to_date = getdate(filters.get("to_date") or nowdate())
#     from_date = getdate(filters.get("from_date") or add_days(to_date, -days_window))

#     points_per_visit = cint(filters.get("points_per_visit") or 2)
#     min_visit_days = cint(filters.get("min_visit_days") or 25)
#     min_spending = flt(filters.get("min_spending") or 2000)
#     eligibility_mode = (filters.get("eligibility_mode") or "OR").upper()

#     only_submitted = cint(filters.get("only_submitted") or 1)
#     company = filters.get("company")
#     patient = filters.get("patient")
#     customer = filters.get("customer")

#     # --- Conditions ---
#     cond = []
#     values = {
#         "from_date": from_date,
#         "to_date": to_date,
#     }

#     cond.append("si.posting_date BETWEEN %(from_date)s AND %(to_date)s")
#     cond.append("si.is_return = 0")

#     if only_submitted:
#         cond.append("si.docstatus = 1")
#     else:
#         cond.append("si.docstatus IN (0,1)")

#     if company:
#         cond.append("si.company = %(company)s")
#         values["company"] = company

#     if patient:
#         cond.append(f"si.{PATIENT_FIELD} = %(patient)s")
#         values["patient"] = patient

#     if customer:
#         cond.append("si.customer = %(customer)s")
#         values["customer"] = customer

#     where_clause = " AND ".join(cond)

#     # --- Group per patient/customer ---
#     # Visit Days = distinct posting_date (so multiple invoices same day count as 1 visit day)
#     rows = frappe.db.sql(
#         f"""
#         SELECT
#             si.customer,
#             si.{PATIENT_FIELD} AS patient,
#             COUNT(DISTINCT si.posting_date) AS visit_days,
#             SUM(si.grand_total) AS total_spending
#         FROM `tabSales Invoice` si
#         WHERE {where_clause}
#         GROUP BY si.customer, si.{PATIENT_FIELD}
#         ORDER BY total_spending DESC
#         """,
#         values,
#         as_dict=True
#     )

#     # Optional: get patient name in bulk (avoid N+1)
#     patient_ids = [r.get("patient") for r in rows if r.get("patient")]
#     patient_name_map = {}
#     if patient_ids:
#         patient_name_map = dict(
#             frappe.db.sql(
#                 """
#                 SELECT name, patient_name
#                 FROM `tabPatient`
#                 WHERE name IN %(names)s
#                 """,
#                 {"names": tuple(set(patient_ids))},
#             )
#         )

#     columns = get_columns()

#     data = []
#     for r in rows:
#         visit_days = cint(r.get("visit_days") or 0)
#         total_spending = flt(r.get("total_spending") or 0)
#         points = visit_days * points_per_visit

#         by_visits = visit_days >= min_visit_days
#         by_spending = total_spending >= min_spending

#         if eligibility_mode == "AND":
#             eligible = by_visits and by_spending
#         else:
#             eligible = by_visits or by_spending

#         if by_visits and by_spending:
#             eligible_by = "Both"
#         elif by_visits:
#             eligible_by = "Visits"
#         elif by_spending:
#             eligible_by = "Spending"
#         else:
#             eligible_by = "None"

#         patient_id = r.get("patient")
#         patient_name = patient_name_map.get(patient_id) if patient_id else None

#         data.append({
#             "patient": patient_id,
#             "patient_name": patient_name,
#             "customer": r.get("customer"),
#             "visit_days": visit_days,
#             "points": points,
#             "total_spending": total_spending,
#             "eligible_by": eligible_by,
#             "status": "✅ ELIGIBLE" if eligible else "❌ NOT ELIGIBLE",
#             "period": f"{from_date} to {to_date}",
#         })

#     return columns, data


# def get_columns():
#     return [
#         {"label": "Patient ID", "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 140},
#         {"label": "Patient Name", "fieldname": "patient_name", "fieldtype": "Data", "width": 200},
#         {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 200},

#         {"label": "Visit Days", "fieldname": "visit_days", "fieldtype": "Int", "width": 100},
#         {"label": "Points", "fieldname": "points", "fieldtype": "Int", "width": 90},

#         {"label": "Total Spending", "fieldname": "total_spending", "fieldtype": "Currency", "width": 130},
#         {"label": "Eligible By", "fieldname": "eligible_by", "fieldtype": "Data", "width": 110},

#         {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 130},
#         {"label": "Period", "fieldname": "period", "fieldtype": "Data", "width": 200},
#     ]