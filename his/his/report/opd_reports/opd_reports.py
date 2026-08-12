# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}

    columns = get_columns()
    data = get_data(filters)
    gender_data = get_gender_data(filters)
    chart = get_chart(data)
    report_summary = get_report_summary(data)
    skip_total_rows = 0

    message = {
        "gender_data": gender_data
    }

    return columns, data, message, chart, report_summary, skip_total_rows


def build_conditions(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    practitioner = filters.get("practitioner")
    department = filters.get("department")

    conditions = []
    values = {}

    if from_date and to_date:
        conditions.append("q.date BETWEEN %(from_date)s AND %(to_date)s")
        values["from_date"] = from_date
        values["to_date"] = to_date

    if practitioner:
        conditions.append("q.practitioner = %(practitioner)s")
        values["practitioner"] = practitioner

    if department:
        conditions.append("q.department = %(department)s")
        values["department"] = department

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    return where_clause, values


def get_data(filters):
    where_clause, values = build_conditions(filters)

    return frappe.db.sql(
        f"""
        SELECT
            q.practitioner,
            q.department,
            SUM(CASE WHEN q.que_type = 'New Patient' THEN 1 ELSE 0 END) AS new_patient,
            SUM(CASE WHEN q.que_type = 'Follow Up' THEN 1 ELSE 0 END) AS follow_up,
            SUM(CASE WHEN q.que_type = 'Refer' THEN 1 ELSE 0 END) AS refer,
            SUM(CASE WHEN q.que_type = 'Revisit' THEN 1 ELSE 0 END) AS revisit,
            COUNT(*) AS total_cases,
            SUM(CASE WHEN q.status = 'Open' THEN 1 ELSE 0 END) AS open_cases,
            SUM(CASE WHEN q.status = 'Closed' THEN 1 ELSE 0 END) AS closed_cases
        FROM `tabQue` q
        WHERE {where_clause}
        GROUP BY q.practitioner, q.department
        ORDER BY total_cases DESC, q.practitioner ASC
        """,
        values=values,
        as_dict=True,
    )


def get_gender_data(filters):
    where_clause, values = build_conditions(filters)

    result = frappe.db.sql(
        f"""
        SELECT
            SUM(CASE WHEN q.gender = 'Male' THEN 1 ELSE 0 END) AS male,
            SUM(CASE WHEN q.gender = 'Female' THEN 1 ELSE 0 END) AS female
        FROM `tabQue` q
        WHERE {where_clause}
        """,
        values=values,
        as_dict=True,
    )

    if result and result[0]:
        return {
            "male": result[0].get("male") or 0,
            "female": result[0].get("female") or 0,
        }

    return {
        "male": 0,
        "female": 0,
    }


def get_columns():
    return [
        {
            "label": _("Practitioner"),
            "fieldname": "practitioner",
            "fieldtype": "Link",
            "options": "Healthcare Practitioner",
            "width": 400,
        },
        {
            "label": _("Department"),
            "fieldname": "department",
            "fieldtype": "Link",
            "options": "Medical Department",
            "width": 190,
        },
        {
            "label": _("New Patients"),
            "fieldname": "new_patient",
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "label": _("Follow Up"),
            "fieldname": "follow_up",
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "label": _("Refer"),
            "fieldname": "refer",
            "fieldtype": "Int",
            "width": 90,
        },
        {
            "label": _("Revisit"),
            "fieldname": "revisit",
            "fieldtype": "Int",
            "width": 90,
        },
        {
            "label": _("Total Cases"),
            "fieldname": "total_cases",
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "label": _("Pending Patients"),
            "fieldname": "open_cases",
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "label": _("Completed Patients"),
            "fieldname": "closed_cases",
            "fieldtype": "Int",
            "width": 150,
        },
    ]


def get_chart(data):
    if not data:
        return None

    labels = [d.get("practitioner") for d in data]
    new_patients = [d.get("new_patient", 0) for d in data]
    follow_up = [d.get("follow_up", 0) for d in data]
    refer = [d.get("refer", 0) for d in data]

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "New Patients",
                    "values": new_patients,
                },
                {
                    "name": "Follow Up",
                    "values": follow_up,
                },
                {
                    "name": "Refer",
                    "values": refer,
                },
            ],
        },
        "type": "bar",
        "height": 320,
        "barOptions": {
            "stacked": False
        },
    }


def get_report_summary(data):
    total_new = sum(d.get("new_patient", 0) for d in data)
    total_follow_up = sum(d.get("follow_up", 0) for d in data)
    total_refer = sum(d.get("refer", 0) for d in data)
    total_cases = sum(d.get("total_cases", 0) for d in data)
    total_open = sum(d.get("open_cases", 0) for d in data)
    total_closed = sum(d.get("closed_cases", 0) for d in data)

    return [
        {
            "label": _("New Patients"),
            "value": total_new,
            "datatype": "Int",
            "indicator": "Blue",
        },
        {
            "label": _("Follow Up"),
            "value": total_follow_up,
            "datatype": "Int",
            "indicator": "Orange",
        },
        {
            "label": _("Refer"),
            "value": total_refer,
            "datatype": "Int",
            "indicator": "Purple",
        },
        {
            "label": _("Pending Patients"),
            "value": total_open,
            "datatype": "Int",
            "indicator": "Red" if total_open else "Green",
        },
        {
            "label": _("Completed Patients"),
            "value": total_closed,
            "datatype": "Int",
            "indicator": "Green",
        },
        {
            "label": _("Total Patients"),
            "value": total_cases,
            "datatype": "Int",
            "indicator": "Dark Blue",
        },
    ]