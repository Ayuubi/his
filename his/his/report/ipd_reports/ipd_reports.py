# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}

    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    report_summary = get_report_summary(data)
    skip_total_rows = 0
    message = {}

    return columns, data, message, chart, report_summary, skip_total_rows


def build_conditions(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    practitioner = filters.get("practitioner")
    department = filters.get("department")
    status = filters.get("status")

    conditions = []
    values = {}

    if from_date and to_date:
        conditions.append("DATE(ipr.creation) BETWEEN %(from_date)s AND %(to_date)s")
        values["from_date"] = from_date
        values["to_date"] = to_date

    if practitioner:
        conditions.append("ipr.admission_practitioner = %(practitioner)s")
        values["practitioner"] = practitioner

    if department:
        conditions.append("hp.department = %(department)s")
        values["department"] = department

    if status:
        conditions.append("ipr.status = %(status)s")
        values["status"] = status

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    return where_clause, values


def get_data(filters):
    where_clause, values = build_conditions(filters)

    return frappe.db.sql(
        f"""
        SELECT
            COALESCE(NULLIF(TRIM(ipr.admission_practitioner), ''), 'No Doctor Assigned') AS practitioner,
            COALESCE(hp.department, 'No Department') AS department,
            SUM(CASE WHEN ipr.status = 'Admission Scheduled' THEN 1 ELSE 0 END) AS admission_scheduled,
            SUM(CASE WHEN ipr.status = 'Admitted' THEN 1 ELSE 0 END) AS admitted,
            SUM(CASE WHEN ipr.status = 'Discharge Scheduled' THEN 1 ELSE 0 END) AS discharge_scheduled,
            SUM(CASE WHEN ipr.status = 'Discharged' THEN 1 ELSE 0 END) AS discharged,
            SUM(CASE WHEN ipr.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled,
            COUNT(*) AS total_patients
        FROM `tabInpatient Record` ipr
        LEFT JOIN `tabHealthcare Practitioner` hp
            ON hp.name = ipr.admission_practitioner
        WHERE {where_clause}
        GROUP BY
            COALESCE(NULLIF(TRIM(ipr.admission_practitioner), ''), 'No Doctor Assigned'),
            COALESCE(hp.department, 'No Department')
        ORDER BY total_patients DESC, practitioner ASC
        """,
        values=values,
        as_dict=True,
    )


def get_columns():
    return [
        {
            "label": _("Doctor"),
            "fieldname": "practitioner",
            "fieldtype": "Data",
            "width": 300,
        },
        {
            "label": _("Department"),
            "fieldname": "department",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("Admission Scheduled"),
            "fieldname": "admission_scheduled",
            "fieldtype": "Int",
            "width": 170,
        },
        {
            "label": _("Admitted"),
            "fieldname": "admitted",
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "label": _("Discharge Scheduled"),
            "fieldname": "discharge_scheduled",
            "fieldtype": "Int",
            "width": 170,
        },
        {
            "label": _("Discharged"),
            "fieldname": "discharged",
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "label": _("Cancelled"),
            "fieldname": "cancelled",
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "label": _("Total Patients"),
            "fieldname": "total_patients",
            "fieldtype": "Int",
            "width": 130,
        },
    ]


def get_chart(data):
    if not data:
        return None

    total_admission_scheduled = sum(d.get("admission_scheduled", 0) for d in data)
    total_admitted = sum(d.get("admitted", 0) for d in data)
    total_discharge_scheduled = sum(d.get("discharge_scheduled", 0) for d in data)
    total_discharged = sum(d.get("discharged", 0) for d in data)
    total_cancelled = sum(d.get("cancelled", 0) for d in data)

    values = [
        total_admission_scheduled,
        total_admitted,
        total_discharge_scheduled,
        total_discharged,
        total_cancelled,
    ]

    if not any(values):
        return None

    return {
        "data": {
            "labels": [
                "Admission Scheduled",
                "Admitted",
                "Discharge Scheduled",
                "Discharged",
                "Cancelled",
            ],
            "datasets": [
                {
                    "name": "Patients",
                    "values": values,
                }
            ],
        },
        "type": "pie",
        "height": 300,
    }


def get_report_summary(data):
    total_doctors = len(data)
    total_admission_scheduled = sum(d.get("admission_scheduled", 0) for d in data)
    total_admitted = sum(d.get("admitted", 0) for d in data)
    total_discharge_scheduled = sum(d.get("discharge_scheduled", 0) for d in data)
    total_discharged = sum(d.get("discharged", 0) for d in data)
    total_cancelled = sum(d.get("cancelled", 0) for d in data)
    total_patients = sum(d.get("total_patients", 0) for d in data)

    return [
        {
            "label": _("Total Doctors"),
            "value": total_doctors,
            "datatype": "Int",
            "indicator": "Blue",
        },
        {
            "label": _("Admission Scheduled"),
            "value": total_admission_scheduled,
            "datatype": "Int",
            "indicator": "Orange",
        },
        {
            "label": _("Admitted"),
            "value": total_admitted,
            "datatype": "Int",
            "indicator": "Blue",
        },
        {
            "label": _("Discharge Scheduled"),
            "value": total_discharge_scheduled,
            "datatype": "Int",
            "indicator": "Purple",
        },
        {
            "label": _("Discharged"),
            "value": total_discharged,
            "datatype": "Int",
            "indicator": "Green",
        },
        {
            "label": _("Cancelled"),
            "value": total_cancelled,
            "datatype": "Int",
            "indicator": "Red",
        },
        {
            "label": _("Total IPD Patients"),
            "value": total_patients,
            "datatype": "Int",
            "indicator": "Dark Blue",
        },
    ]