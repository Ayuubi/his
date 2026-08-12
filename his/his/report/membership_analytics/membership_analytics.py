# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, getdate


MEMBERSHIP_DOCTYPE = "Membership Registration"
FAMILY_CHILD_DOCTYPE = "Family Members"


def execute(filters=None):
    filters = frappe._dict(filters or {})
    view_type = filters.get("view_type") or "Membership Summary"

    if view_type == "Membership Summary":
        columns = get_membership_summary_columns()
        data = get_membership_summary(filters)

    elif view_type == "Old vs New Detail":
        columns = get_old_new_detail_columns()
        data = get_old_new_detail(filters)

    elif view_type == "Usage Summary":
        columns = get_usage_summary_columns()
        data = get_usage_summary(filters)

    elif view_type == "Usage Detail":
        columns = get_usage_detail_columns()
        data = get_usage_detail(filters)

    else:
        columns = get_membership_summary_columns()
        data = get_membership_summary(filters)

    report_summary = get_report_summary(filters)
    chart = get_chart(filters, view_type, data)

    return columns, data, None, chart, report_summary


# -------------------------------------------------------------------------
# Core membership patient list
# -------------------------------------------------------------------------

def get_membership_patients(filters):
    """
    Returns all patients linked to membership registration:
    1. Parent head_patient
    2. Child family_members.patient

    Important:
    Sales Invoice only has patient, so this is the master list used
    to identify membership usage.
    """

    conditions = []
    values = {}

    if filters.get("membership_status"):
        conditions.append("mr.status = %(membership_status)s")
        values["membership_status"] = filters.get("membership_status")

    if filters.get("discount_level"):
        conditions.append("mr.discount_level = %(discount_level)s")
        values["discount_level"] = filters.get("discount_level")

    if filters.get("card_number"):
        conditions.append("mr.card_number = %(card_number)s")
        values["card_number"] = filters.get("card_number")

    if filters.get("patient"):
        conditions.append("x.patient = %(patient)s")
        values["patient"] = filters.get("patient")

    condition_sql = ""
    if conditions:
        condition_sql = " AND " + " AND ".join(conditions)

    sql = """
        SELECT
            x.membership_registration,
            x.card_number,
            x.discount_level,
            x.status,
            x.registeration_date,
            x.start_date,
            x.end_date,
            x.patient,
            x.member_name,
            x.member_type,
            x.membership_creation,
            p.creation AS patient_creation,
            p.customer,
            p.mobile_no,
            p.sex,
            p.territory,
            CASE
                WHEN DATE(p.creation) < DATE(x.membership_creation)
                    THEN 'Old Patient'
                ELSE 'New Patient'
            END AS patient_type
        FROM (
            SELECT
                mr.name AS membership_registration,
                mr.card_number,
                mr.discount_level,
                mr.status,
                mr.registeration_date,
                mr.start_date,
                mr.end_date,
                mr.head_patient AS patient,
                mr.family_head_person AS member_name,
                'Family Head' AS member_type,
                mr.creation AS membership_creation
            FROM `tabMembership Registration` mr
            WHERE IFNULL(mr.head_patient, '') != ''

            UNION ALL

            SELECT
                mr.name AS membership_registration,
                mr.card_number,
                mr.discount_level,
                mr.status,
                mr.registeration_date,
                mr.start_date,
                mr.end_date,
                fm.patient AS patient,
                fm.full_name AS member_name,
                IFNULL(fm.member_type, 'Family Member') AS member_type,
                mr.creation AS membership_creation
            FROM `tabMembership Registration` mr
            INNER JOIN `tabFamily Members` fm
                ON fm.parent = mr.name
                AND fm.parenttype = 'Membership Registration'
                AND fm.parentfield = 'family_members'
            WHERE IFNULL(fm.patient, '') != ''
        ) x
        INNER JOIN `tabMembership Registration` mr
            ON mr.name = x.membership_registration
        LEFT JOIN `tabPatient` p
            ON p.name = x.patient
        WHERE 1 = 1
        {condition_sql}
        ORDER BY x.card_number, x.patient
    """.format(condition_sql=condition_sql)

    rows = frappe.db.sql(sql, values, as_dict=True)

    # Avoid duplicate patient rows if the same patient was added twice
    # Keep the newest membership record for that patient.
    unique = {}
    for row in rows:
        key = row.patient
        if not key:
            continue

        old = unique.get(key)
        if not old:
            unique[key] = row
            continue

        if str(row.membership_creation or "") >= str(old.membership_creation or ""):
            unique[key] = row

    return list(unique.values())


def get_membership_patient_map(filters):
    rows = get_membership_patients(filters)
    return {d.patient: d for d in rows if d.patient}


# -------------------------------------------------------------------------
# Membership Summary
# -------------------------------------------------------------------------

def get_membership_summary_columns():
    return [
        {"label": "Metric", "fieldname": "metric", "fieldtype": "Data", "width": 260},
        {"label": "Value", "fieldname": "value", "fieldtype": "Float", "width": 160},
    ]


def get_membership_summary(filters):
    members = get_membership_patients(filters)
    usage = get_usage_totals(filters)

    total_members = len(members)
    old_members = len([d for d in members if d.patient_type == "Old Patient"])
    new_members = len([d for d in members if d.patient_type == "New Patient"])

    return [
        {"metric": "Total Membership Patients", "value": total_members},
        {"metric": "Old Patients Given Membership", "value": old_members},
        {"metric": "New Patients Created From Membership", "value": new_members},
        {"metric": "Membership Patients Used Services", "value": usage.get("used_patients", 0)},
        {"metric": "Membership Invoices", "value": usage.get("invoice_count", 0)},
        {"metric": "Gross Amount", "value": usage.get("gross_amount", 0)},
        {"metric": "Net Revenue", "value": usage.get("net_revenue", 0)},
        {"metric": "Discount Given", "value": usage.get("discount_amount", 0)},
    ]


# -------------------------------------------------------------------------
# Old vs New Detail
# -------------------------------------------------------------------------

def get_old_new_detail_columns():
    return [
        {"label": "Patient Type", "fieldname": "patient_type", "fieldtype": "Data", "width": 130},
        {"label": "Card Number", "fieldname": "card_number", "fieldtype": "Int", "width": 110},
        {"label": "Membership", "fieldname": "membership_registration", "fieldtype": "Link", "options": "Membership Registration", "width": 170},
        {"label": "Patient", "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 130},
        {"label": "Member Name", "fieldname": "member_name", "fieldtype": "Data", "width": 190},
        {"label": "Member Type", "fieldname": "member_type", "fieldtype": "Data", "width": 120},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 130},
        {"label": "Discount Level", "fieldname": "discount_level", "fieldtype": "Data", "width": 110},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 90},
        {"label": "Membership Date", "fieldname": "registeration_date", "fieldtype": "Date", "width": 120},
        {"label": "Patient Created On", "fieldname": "patient_creation", "fieldtype": "Datetime", "width": 170},
        {"label": "Membership Created On", "fieldname": "membership_creation", "fieldtype": "Datetime", "width": 170},
        {"label": "Used Invoices", "fieldname": "used_invoices", "fieldtype": "Int", "width": 110},
        {"label": "Net Revenue", "fieldname": "net_revenue", "fieldtype": "Currency", "width": 130},
        {"label": "Discount Given", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 130},
    ]


def get_old_new_detail(filters):
    members = get_membership_patients(filters)
    usage_by_patient = get_usage_by_patient(filters)

    data = []

    for d in members:
        usage = usage_by_patient.get(d.patient, frappe._dict())

        used_invoices = usage.get("invoice_count", 0)
        if filters.get("show_only_used") and not used_invoices:
            continue

        data.append({
            "patient_type": d.patient_type,
            "card_number": d.card_number,
            "membership_registration": d.membership_registration,
            "patient": d.patient,
            "member_name": d.member_name,
            "member_type": d.member_type,
            "customer": d.customer,
            "discount_level": d.discount_level,
            "status": d.status,
            "registeration_date": d.registeration_date,
            "patient_creation": d.patient_creation,
            "membership_creation": d.membership_creation,
            "used_invoices": used_invoices,
            "net_revenue": usage.get("net_revenue", 0),
            "discount_amount": usage.get("discount_amount", 0),
        })

    return data


# -------------------------------------------------------------------------
# Usage Summary
# -------------------------------------------------------------------------

def get_usage_summary_columns():
    return [
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": "Used Patients", "fieldname": "used_patients", "fieldtype": "Int", "width": 120},
        {"label": "Invoices", "fieldname": "invoice_count", "fieldtype": "Int", "width": 100},
        {"label": "Gross Amount", "fieldname": "gross_amount", "fieldtype": "Currency", "width": 140},
        {"label": "Net Revenue", "fieldname": "net_revenue", "fieldtype": "Currency", "width": 140},
        {"label": "Discount Given", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 140},
        {"label": "Average Discount %", "fieldname": "avg_discount_percent", "fieldtype": "Percent", "width": 140},
    ]


def get_usage_summary(filters):
    patient_map = get_membership_patient_map(filters)
    patients = list(patient_map.keys())

    if not patients:
        return []

    conditions, values = get_sales_invoice_conditions(filters, patients)

    sql = """
        SELECT
            si.posting_date,
            COUNT(DISTINCT si.patient) AS used_patients,
            COUNT(DISTINCT si.name) AS invoice_count,
            SUM(si.total) AS gross_amount,
            SUM(si.net_total) AS net_revenue,
            SUM(si.total - si.net_total) AS discount_amount
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
            {conditions}
        GROUP BY si.posting_date
        ORDER BY si.posting_date
    """.format(conditions=conditions)

    rows = frappe.db.sql(sql, values, as_dict=True)

    for d in rows:
        d.gross_amount = flt(d.gross_amount)
        d.net_revenue = flt(d.net_revenue)
        d.discount_amount = flt(d.discount_amount)

        if d.gross_amount:
            d.avg_discount_percent = (d.discount_amount / d.gross_amount) * 100
        else:
            d.avg_discount_percent = 0

    return rows


# -------------------------------------------------------------------------
# Usage Detail
# -------------------------------------------------------------------------

def get_usage_detail_columns():
    return [
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
        {"label": "Sales Invoice", "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 170},
        {"label": "Card Number", "fieldname": "card_number", "fieldtype": "Int", "width": 110},
        {"label": "Discount Level", "fieldname": "discount_level", "fieldtype": "Data", "width": 110},
        {"label": "Patient Type", "fieldname": "patient_type", "fieldtype": "Data", "width": 120},
        {"label": "Patient", "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 130},
        {"label": "Patient Name", "fieldname": "patient_name", "fieldtype": "Data", "width": 180},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 130},
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 140},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 190},
        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 130},
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 80},
        {"label": "Gross Amount", "fieldname": "gross_amount", "fieldtype": "Currency", "width": 130},
        {"label": "Net Revenue", "fieldname": "net_revenue", "fieldtype": "Currency", "width": 130},
        {"label": "Discount Given", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 130},
        {"label": "Actual Discount %", "fieldname": "actual_discount_percent", "fieldtype": "Percent", "width": 130},
        {"label": "Membership", "fieldname": "membership_registration", "fieldtype": "Link", "options": "Membership Registration", "width": 170},
    ]


def get_usage_detail(filters):
    patient_map = get_membership_patient_map(filters)
    patients = list(patient_map.keys())

    if not patients:
        return []

    conditions, values = get_sales_invoice_conditions(filters, patients, include_item_group=True)

    sql = """
        SELECT
            si.posting_date,
            si.name AS sales_invoice,
            si.patient,
            si.patient_name,
            si.customer,
            sii.item_code,
            sii.item_name,
            sii.item_group,
            sii.qty,
            sii.amount AS gross_amount,
            sii.net_amount AS net_revenue,
            (sii.amount - sii.net_amount) AS discount_amount
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii
            ON sii.parent = si.name
        WHERE si.docstatus = 1
            {conditions}
        ORDER BY si.posting_date, si.name, sii.idx
    """.format(conditions=conditions)

    rows = frappe.db.sql(sql, values, as_dict=True)

    data = []
    for d in rows:
        membership = patient_map.get(d.patient)

        gross_amount = flt(d.gross_amount)
        net_revenue = flt(d.net_revenue)
        discount_amount = flt(d.discount_amount)

        actual_discount_percent = 0
        if gross_amount:
            actual_discount_percent = (discount_amount / gross_amount) * 100

        data.append({
            "posting_date": d.posting_date,
            "sales_invoice": d.sales_invoice,
            "card_number": membership.card_number if membership else None,
            "discount_level": membership.discount_level if membership else None,
            "patient_type": membership.patient_type if membership else None,
            "patient": d.patient,
            "patient_name": d.patient_name,
            "customer": d.customer,
            "item_code": d.item_code,
            "item_name": d.item_name,
            "item_group": d.item_group,
            "qty": d.qty,
            "gross_amount": gross_amount,
            "net_revenue": net_revenue,
            "discount_amount": discount_amount,
            "actual_discount_percent": actual_discount_percent,
            "membership_registration": membership.membership_registration if membership else None,
        })

    return data


# -------------------------------------------------------------------------
# Usage helpers
# -------------------------------------------------------------------------

def get_sales_invoice_conditions(filters, patients, include_item_group=False):
    conditions = []
    values = {}

    conditions.append("si.patient IN %(patients)s")
    values["patients"] = tuple(patients)

    if filters.get("from_date"):
        conditions.append("si.posting_date >= %(from_date)s")
        values["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions.append("si.posting_date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")

    if filters.get("company"):
        conditions.append("si.company = %(company)s")
        values["company"] = filters.get("company")

    if filters.get("customer"):
        conditions.append("si.customer = %(customer)s")
        values["customer"] = filters.get("customer")

    if filters.get("patient"):
        conditions.append("si.patient = %(patient)s")
        values["patient"] = filters.get("patient")

    if include_item_group and filters.get("item_group"):
        conditions.append("sii.item_group = %(item_group)s")
        values["item_group"] = filters.get("item_group")

    condition_sql = ""
    if conditions:
        condition_sql = " AND " + " AND ".join(conditions)

    return condition_sql, values


def get_usage_totals(filters):
    patient_map = get_membership_patient_map(filters)
    patients = list(patient_map.keys())

    if not patients:
        return frappe._dict({
            "used_patients": 0,
            "invoice_count": 0,
            "gross_amount": 0,
            "net_revenue": 0,
            "discount_amount": 0,
        })

    conditions, values = get_sales_invoice_conditions(filters, patients)

    sql = """
        SELECT
            COUNT(DISTINCT si.patient) AS used_patients,
            COUNT(DISTINCT si.name) AS invoice_count,
            SUM(si.total) AS gross_amount,
            SUM(si.net_total) AS net_revenue,
            SUM(si.total - si.net_total) AS discount_amount
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
            {conditions}
    """.format(conditions=conditions)

    row = frappe.db.sql(sql, values, as_dict=True)

    if not row:
        return frappe._dict()

    return frappe._dict(row[0])


def get_usage_by_patient(filters):
    patient_map = get_membership_patient_map(filters)
    patients = list(patient_map.keys())

    if not patients:
        return {}

    conditions, values = get_sales_invoice_conditions(filters, patients)

    sql = """
        SELECT
            si.patient,
            COUNT(DISTINCT si.name) AS invoice_count,
            SUM(si.total) AS gross_amount,
            SUM(si.net_total) AS net_revenue,
            SUM(si.total - si.net_total) AS discount_amount
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
            {conditions}
        GROUP BY si.patient
    """.format(conditions=conditions)

    rows = frappe.db.sql(sql, values, as_dict=True)

    return {d.patient: d for d in rows}


# -------------------------------------------------------------------------
# Report summary and chart
# -------------------------------------------------------------------------

def get_report_summary(filters):
    members = get_membership_patients(filters)
    usage = get_usage_totals(filters)

    old_members = len([d for d in members if d.patient_type == "Old Patient"])
    new_members = len([d for d in members if d.patient_type == "New Patient"])

    return [
        {
            "value": len(members),
            "label": "Membership Patients",
            "datatype": "Int",
            "indicator": "Blue",
        },
        {
            "value": old_members,
            "label": "Old Patients",
            "datatype": "Int",
            "indicator": "Orange",
        },
        {
            "value": new_members,
            "label": "New Patients",
            "datatype": "Int",
            "indicator": "Green",
        },
        {
            "value": flt(usage.get("used_patients")),
            "label": "Used Patients",
            "datatype": "Int",
            "indicator": "Blue",
        },
        {
            "value": flt(usage.get("net_revenue")),
            "label": "Net Revenue",
            "datatype": "Currency",
            "indicator": "Green",
        },
        {
            "value": flt(usage.get("discount_amount")),
            "label": "Discount Given",
            "datatype": "Currency",
            "indicator": "Red",
        },
    ]


def get_chart(filters, view_type, data):
    if view_type == "Usage Summary" and data:
        return {
            "data": {
                "labels": [str(d.get("posting_date")) for d in data],
                "datasets": [
                    {
                        "name": "Net Revenue",
                        "values": [flt(d.get("net_revenue")) for d in data],
                    },
                    {
                        "name": "Discount Given",
                        "values": [flt(d.get("discount_amount")) for d in data],
                    },
                ],
            },
            "type": "bar",
        }

    if view_type in ("Membership Summary", "Old vs New Detail"):
        members = get_membership_patients(filters)
        old_members = len([d for d in members if d.patient_type == "Old Patient"])
        new_members = len([d for d in members if d.patient_type == "New Patient"])

        return {
            "data": {
                "labels": ["Old Patients", "New Patients"],
                "datasets": [
                    {
                        "name": "Patients",
                        "values": [old_members, new_members],
                    }
                ],
            },
            "type": "donut",
        }

    return None
