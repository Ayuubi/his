# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
    filters = frappe._dict(filters or {})

    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_report_summary(data)

    return columns, data, None, chart, summary


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _has_field(doctype: str, fieldname: str) -> bool:
    try:
        return frappe.get_meta(doctype).has_field(fieldname)
    except Exception:
        return False


def cint_safe(v):
    try:
        return int(v or 0)
    except Exception:
        return 0


def get_ipd_status_sets():
    admitted_statuses = {
        "Admitted",
        "Admission Scheduled",
        "Active",
        "Occupied",
        "Open",
        "In Progress",
        "Discharge Scheduled",
    }

    discharged_statuses = {
        "Discharged",
        "Completed",
        "Closed",
        "Checked Out",
    }

    return admitted_statuses, discharged_statuses


# ------------------------------------------------------------
# Columns
# ------------------------------------------------------------

def get_columns():
    return [
        {
            "label": _("Party Type"),
            "fieldname": "party_type",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": _("Party"),
            "fieldname": "party",
            "fieldtype": "Dynamic Link",
            "options": "party_type",
            "width": 170,
        },
        {
            "label": _("Party Name"),
            "fieldname": "party_name",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": _("Customer Group"),
            "fieldname": "customer_group",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Patient"),
            "fieldname": "patient",
            "fieldtype": "Link",
            "options": "Patient",
            "width": 130,
        },
        {
            "label": _("Patient Name"),
            "fieldname": "patient_name",
            "fieldtype": "Data",
            "width": 210,
        },
        {
            "label": _("Patient Customer"),
            "fieldname": "patient_customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 170,
        },
        {
            "label": _("Billing Category"),
            "fieldname": "billing_category",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Current Patient IPD Status"),
            "fieldname": "current_ipd_status",
            "fieldtype": "Data",
            "width": 170,
        },
        {
            "label": _("Current Patient Inpatient Record"),
            "fieldname": "current_inpatient_record",
            "fieldtype": "Link",
            "options": "Inpatient Record",
            "width": 190,
        },
        {
            "label": _("Latest Discharge Date"),
            "fieldname": "last_discharge_date",
            "fieldtype": "Datetime",
            "width": 170,
        },
        {
            "label": _("Ledger Balance On Discharge Date"),
            "fieldname": "balance_at_discharge",
            "fieldtype": "Currency",
            "width": 220,
        },
        {
            "label": _("Current Ledger Balance"),
            "fieldname": "current_ledger_balance",
            "fieldtype": "Currency",
            "width": 180,
        },
        {
            "label": _("Movement After Discharge"),
            "fieldname": "post_discharge_movement",
            "fieldtype": "Currency",
            "width": 190,
        },
        {
            "label": _("Receivable State"),
            "fieldname": "receivable_state",
            "fieldtype": "Data",
            "width": 180,
        },
    ]


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def get_data(filters):
    party_type = (filters.get("party_type") or "Customer").strip()

    gl_rows = get_party_balances(filters, party_type)
    if not gl_rows:
        return []

    row_map = build_row_map(gl_rows)
    enrich_party_master_data(row_map, party_type)

    if party_type == "Customer":
        enrich_customer_patient_mapping(row_map)
        enrich_customer_billing_category(row_map, filters)

    elif party_type == "Employee":
        enrich_employee_patient_mapping(row_map, filters)
        for d in row_map.values():
            d["billing_category"] = "Employee Ledger"

    enrich_current_ipd(row_map)
    enrich_last_discharge(row_map)
    enrich_balance_at_discharge(row_map, filters)

    return finalize_rows(row_map, filters, party_type)


# ------------------------------------------------------------
# Accounts / GL source
# ------------------------------------------------------------

def get_customer_receivable_accounts(filters):
    values = {}
    company_condition = ""

    if filters.get("company") and _has_field("Account", "company"):
        company_condition = " AND company = %(company)s "
        values["company"] = filters.get("company")

    rows = frappe.db.sql(
        f"""
        SELECT name
        FROM `tabAccount`
        WHERE is_group = 0
          AND account_type = 'Receivable'
          {company_condition}
        ORDER BY name
        """,
        values,
        as_dict=True,
    )

    return [r.name for r in rows]


def get_employee_payable_accounts(filters):
    values = {}
    company_condition = ""

    if filters.get("company") and _has_field("Account", "company"):
        company_condition = " AND company = %(company)s "
        values["company"] = filters.get("company")

    rows = frappe.db.sql(
        f"""
        SELECT name
        FROM `tabAccount`
        WHERE is_group = 0
          AND account_type = 'Payable'
          {company_condition}
        ORDER BY name
        """,
        values,
        as_dict=True,
    )

    return [r.name for r in rows]


def get_party_balances(filters, party_type):
    if party_type == "Customer":
        accounts = get_customer_receivable_accounts(filters)
    elif party_type == "Employee":
        accounts = get_employee_payable_accounts(filters)
    else:
        return []

    if not accounts:
        return []

    values = {
        "party_type": party_type,
        "accounts": tuple(accounts),
    }

    conditions = [
        "gle.is_cancelled = 0",
        "gle.party_type = %(party_type)s",
        "IFNULL(gle.party, '') != ''",
        "gle.account IN %(accounts)s",
    ]

    if filters.get("company") and _has_field("GL Entry", "company"):
        conditions.append("gle.company = %(company)s")
        values["company"] = filters.get("company")

    if filters.get("to_date") and _has_field("GL Entry", "posting_date"):
        conditions.append("gle.posting_date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")

    if filters.get("party"):
        conditions.append("gle.party = %(party)s")
        values["party"] = filters.get("party")

    rows = frappe.db.sql(
        f"""
        SELECT
            gle.party_type,
            gle.party,
            SUM(IFNULL(gle.debit, 0) - IFNULL(gle.credit, 0)) AS current_ledger_balance
        FROM `tabGL Entry` gle
        WHERE {" AND ".join(conditions)}
        GROUP BY gle.party_type, gle.party
        HAVING ABS(SUM(IFNULL(gle.debit, 0) - IFNULL(gle.credit, 0))) > 0.0001
        ORDER BY gle.party
        """,
        values,
        as_dict=True,
    )

    return rows


# ------------------------------------------------------------
# Base row map
# ------------------------------------------------------------

def build_row_map(gl_rows):
    row_map = {}

    for r in gl_rows:
        key = f"{r.party_type}::{r.party}"
        row_map[key] = {
            "party_type": r.party_type,
            "party": r.party,
            "party_name": "",
            "customer_group": "",
            "patient": "",
            "patient_name": "",
            "patient_customer": "",
            "billing_category": "",
            "current_ipd_status": "",
            "current_inpatient_record": "",
            "last_discharge_date": None,
            "balance_at_discharge": 0.0,
            "current_ledger_balance": flt(r.current_ledger_balance),
            "post_discharge_movement": 0.0,
            "receivable_state": "",
        }

    return row_map


# ------------------------------------------------------------
# Party master enrichment
# ------------------------------------------------------------

def enrich_party_master_data(row_map, party_type):
    if not row_map:
        return

    parties = [d["party"] for d in row_map.values() if d.get("party")]
    if not parties:
        return

    if party_type == "Customer":
        fields = ["name", "customer_name"]
        if _has_field("Customer", "customer_group"):
            fields.append("customer_group")

        rows = frappe.get_all(
            "Customer",
            filters={"name": ["in", parties]},
            fields=fields,
            limit_page_length=0,
        )

        master = {r.name: r for r in rows}

        for d in row_map.values():
            m = master.get(d["party"])
            if not m:
                d["party_name"] = d["party"]
                continue

            d["party_name"] = m.get("customer_name") or d["party"]
            d["customer_group"] = m.get("customer_group") or ""

    elif party_type == "Employee":
        fields = ["name"]
        if _has_field("Employee", "employee_name"):
            fields.append("employee_name")

        rows = frappe.get_all(
            "Employee",
            filters={"name": ["in", parties]},
            fields=fields,
            limit_page_length=0,
        )

        master = {r.name: r for r in rows}

        for d in row_map.values():
            m = master.get(d["party"])
            if not m:
                d["party_name"] = d["party"]
                continue

            d["party_name"] = m.get("employee_name") or d["party"]


# ------------------------------------------------------------
# Customer -> Patient mapping
# ------------------------------------------------------------

def enrich_customer_patient_mapping(row_map):
    if not row_map or not _has_field("Patient", "customer"):
        return

    customer_parties = [d["party"] for d in row_map.values() if d.get("party")]
    if not customer_parties:
        return

    patient_fields = ["name", "customer"]
    if _has_field("Patient", "patient_name"):
        patient_fields.append("patient_name")
    if _has_field("Patient", "inpatient_record"):
        patient_fields.append("inpatient_record")
    if _has_field("Patient", "inpatient_status"):
        patient_fields.append("inpatient_status")

    patient_rows = frappe.get_all(
        "Patient",
        filters={"customer": ["in", customer_parties]},
        fields=patient_fields,
        limit_page_length=0,
    )

    customer_to_patient = {}
    for r in patient_rows:
        if r.customer not in customer_to_patient:
            customer_to_patient[r.customer] = r

    for d in row_map.values():
        prow = customer_to_patient.get(d["party"])
        if not prow:
            continue

        d["patient"] = prow.name
        d["patient_name"] = prow.get("patient_name") or ""
        d["patient_customer"] = prow.customer or ""
        d["current_inpatient_record"] = prow.get("inpatient_record") or ""
        d["current_ipd_status"] = prow.get("inpatient_status") or ""


def enrich_customer_billing_category(row_map, filters):
    if not row_map:
        return

    insurance_groups = {
        "insurance",
        "insurance company",
        "tpa",
        "corporate insurance",
    }

    for d in row_map.values():
        customer_group = (d.get("customer_group") or "").strip().lower()

        # direct patient mapping first
        if d.get("patient"):
            d["billing_category"] = "Patient Ledger"
            continue

        # customer group-based insurance detection
        if customer_group in insurance_groups or "insurance" in customer_group:
            d["billing_category"] = "Insurance Ledger"
            continue

        d["billing_category"] = "Unmapped Customer Ledger"

    # best-effort fallback from invoice history for insurance
    parties = [d["party"] for d in row_map.values() if d.get("party")]
    if not parties:
        return

    values = {"parties": tuple(parties)}
    conditions = [
        "si.docstatus = 1",
        "IFNULL(si.is_insurance, 0) = 1",
        "si.insurance IN %(parties)s",
    ]

    if filters.get("company") and _has_field("Sales Invoice", "company"):
        conditions.append("si.company = %(company)s")
        values["company"] = filters.get("company")

    if filters.get("to_date") and _has_field("Sales Invoice", "posting_date"):
        conditions.append("si.posting_date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")

    rows = frappe.db.sql(
        f"""
        SELECT DISTINCT si.insurance
        FROM `tabSales Invoice` si
        WHERE {" AND ".join(conditions)}
        """,
        values,
        as_dict=True,
    )

    insurance_parties = {r.insurance for r in rows if r.insurance}

    for d in row_map.values():
        if d.get("patient"):
            continue
        if d["party"] in insurance_parties:
            d["billing_category"] = "Insurance Ledger"


# ------------------------------------------------------------
# Employee -> Patient mapping (best effort)
# ------------------------------------------------------------

def enrich_employee_patient_mapping(row_map, filters):
    if not row_map:
        return

    employee_parties = [d["party"] for d in row_map.values() if d.get("party")]
    if not employee_parties:
        return

    conditions = [
        "si.docstatus = 1",
        "IFNULL(si.bill_to_employee, 0) = 1",
        "si.employee IN %(employees)s",
    ]
    values = {"employees": tuple(employee_parties)}

    if filters.get("company") and _has_field("Sales Invoice", "company"):
        conditions.append("si.company = %(company)s")
        values["company"] = filters.get("company")

    if filters.get("to_date") and _has_field("Sales Invoice", "posting_date"):
        conditions.append("si.posting_date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")

    order_fields = ["si.employee"]
    if _has_field("Sales Invoice", "posting_date"):
        order_fields.append("si.posting_date DESC")
    order_fields.append("si.modified DESC")

    rows = frappe.db.sql(
        f"""
        SELECT
            si.employee,
            si.patient,
            si.patient_name
        FROM `tabSales Invoice` si
        WHERE {" AND ".join(conditions)}
        ORDER BY {", ".join(order_fields)}
        """,
        values,
        as_dict=True,
    )

    emp_map = {}
    for r in rows:
        if r.employee not in emp_map:
            emp_map[r.employee] = r

    patient_customer_map = {}
    patient_names = [r.patient for r in emp_map.values() if r.get("patient")]
    if patient_names and _has_field("Patient", "customer"):
        prs = frappe.get_all(
            "Patient",
            filters={"name": ["in", patient_names]},
            fields=["name", "customer"],
            limit_page_length=0,
        )
        patient_customer_map = {p.name: p.customer for p in prs}

    for d in row_map.values():
        info = emp_map.get(d["party"])
        if not info:
            continue

        d["patient"] = info.get("patient") or ""
        d["patient_name"] = info.get("patient_name") or ""
        d["patient_customer"] = patient_customer_map.get(info.get("patient")) or ""


# ------------------------------------------------------------
# Current IPD + discharge
# ------------------------------------------------------------

def enrich_current_ipd(row_map):
    if not row_map:
        return

    patient_names = [d["patient"] for d in row_map.values() if d.get("patient")]
    if not patient_names:
        return

    fields = ["name"]
    if _has_field("Patient", "inpatient_record"):
        fields.append("inpatient_record")
    if _has_field("Patient", "inpatient_status"):
        fields.append("inpatient_status")
    if _has_field("Patient", "patient_name"):
        fields.append("patient_name")
    if _has_field("Patient", "customer"):
        fields.append("customer")

    patient_rows = frappe.get_all(
        "Patient",
        filters={"name": ["in", patient_names]},
        fields=fields,
        limit_page_length=0,
    )

    pmap = {r.name: r for r in patient_rows}

    for d in row_map.values():
        patient = d.get("patient")
        if not patient or patient not in pmap:
            continue

        prow = pmap[patient]
        d["patient_name"] = d.get("patient_name") or prow.get("patient_name") or ""
        d["patient_customer"] = d.get("patient_customer") or prow.get("customer") or ""
        d["current_inpatient_record"] = prow.get("inpatient_record") or ""
        d["current_ipd_status"] = prow.get("inpatient_status") or ""


def enrich_last_discharge(row_map):
    if not row_map:
        return

    patient_names = [d["patient"] for d in row_map.values() if d.get("patient")]
    if not patient_names:
        return

    if not _has_field("Inpatient Record", "patient") or not _has_field("Inpatient Record", "discharge_datetime"):
        return

    rows = frappe.get_all(
        "Inpatient Record",
        filters={
            "patient": ["in", patient_names],
            "discharge_datetime": ["is", "set"],
        },
        fields=["patient", "max(discharge_datetime) as last_discharge_date"],
        group_by="patient",
        limit_page_length=0,
    )

    discharge_map = {r.patient: r.get("last_discharge_date") for r in rows}

    for d in row_map.values():
        patient = d.get("patient")
        if patient in discharge_map:
            d["last_discharge_date"] = discharge_map.get(patient)


# ------------------------------------------------------------
# Historical balance at discharge
# ------------------------------------------------------------

def get_balance_as_of(filters, party_type, party, as_of_date):
    if not party or not as_of_date:
        return 0.0

    if party_type == "Customer":
        accounts = get_customer_receivable_accounts(filters)
    elif party_type == "Employee":
        accounts = get_employee_payable_accounts(filters)
    else:
        return 0.0

    if not accounts:
        return 0.0

    values = {
        "party_type": party_type,
        "party": party,
        "accounts": tuple(accounts),
        "as_of_date": getdate(as_of_date),
    }

    conditions = [
        "gle.is_cancelled = 0",
        "gle.party_type = %(party_type)s",
        "gle.party = %(party)s",
        "gle.account IN %(accounts)s",
        "gle.posting_date <= %(as_of_date)s",
    ]

    if filters.get("company") and _has_field("GL Entry", "company"):
        conditions.append("gle.company = %(company)s")
        values["company"] = filters.get("company")

    result = frappe.db.sql(
        f"""
        SELECT
            SUM(IFNULL(gle.debit, 0) - IFNULL(gle.credit, 0)) AS balance
        FROM `tabGL Entry` gle
        WHERE {" AND ".join(conditions)}
        """,
        values,
        as_dict=True,
    )

    return flt(result[0].balance) if result and result[0].balance is not None else 0.0


def enrich_balance_at_discharge(row_map, filters):
    if not row_map:
        return

    admitted_statuses, _ = get_ipd_status_sets()

    for d in row_map.values():
        current_status = (d.get("current_ipd_status") or "").strip()
        current_ipr = d.get("current_inpatient_record")
        discharge_dt = d.get("last_discharge_date")

        if current_ipr and current_status in admitted_statuses:
            d["balance_at_discharge"] = 0.0
            d["post_discharge_movement"] = 0.0
            continue

        if not discharge_dt:
            d["balance_at_discharge"] = 0.0
            d["post_discharge_movement"] = 0.0
            continue

        bal_at_discharge = get_balance_as_of(
            filters=filters,
            party_type=d.get("party_type"),
            party=d.get("party"),
            as_of_date=discharge_dt,
        )

        d["balance_at_discharge"] = flt(bal_at_discharge)
        d["post_discharge_movement"] = flt(d.get("current_ledger_balance")) - flt(bal_at_discharge)


# ------------------------------------------------------------
# Final classification
# ------------------------------------------------------------

def determine_receivable_state(row, party_type):
    admitted_statuses, _ = get_ipd_status_sets()

    current_status = (row.get("current_ipd_status") or "").strip()
    current_ipr = row.get("current_inpatient_record")
    has_discharge = row.get("last_discharge_date")
    has_patient = bool(row.get("patient"))
    category = row.get("billing_category") or ""

    if party_type == "Employee":
        if has_patient and current_ipr and current_status in admitted_statuses:
            return "Employee / IPD Admitted"
        if has_patient and has_discharge:
            return "Employee / IPD Discharged"
        if has_patient:
            return "Employee / OPD"
        return "Employee Ledger"

    if has_patient and current_ipr and current_status in admitted_statuses:
        return "IPD Admitted"

    if has_patient and has_discharge:
        return "IPD Discharged"

    if has_patient:
        return "OPD"

    if category == "Insurance Ledger":
        return "Insurance"

    return "Unmapped Customer"


def finalize_rows(row_map, filters, party_type):
    rows = list(row_map.values())

    for d in rows:
        d["receivable_state"] = determine_receivable_state(d, party_type)

    if filters.get("patient"):
        rows = [d for d in rows if d.get("patient") == filters.get("patient")]

    if filters.get("billing_category"):
        rows = [d for d in rows if d.get("billing_category") == filters.get("billing_category")]

    if filters.get("receivable_state"):
        rows = [d for d in rows if d.get("receivable_state") == filters.get("receivable_state")]

    if cint_safe(filters.get("only_with_discharge_balance")):
        rows = [d for d in rows if d.get("last_discharge_date")]

    sort_by = filters.get("sort_by") or "current_ledger_balance"
    reverse = True

    numeric_fields = {
        "current_ledger_balance",
        "balance_at_discharge",
        "post_discharge_movement",
    }

    try:
        if sort_by in numeric_fields:
            rows.sort(key=lambda x: flt(x.get(sort_by)), reverse=reverse)
        else:
            rows.sort(key=lambda x: (x.get(sort_by) or ""), reverse=reverse)
    except Exception:
        rows.sort(key=lambda x: flt(x.get("current_ledger_balance")), reverse=True)

    return rows


# ------------------------------------------------------------
# Chart
# ------------------------------------------------------------

def get_chart(data):
    if not data:
        return None

    opd = sum(flt(d.get("current_ledger_balance")) for d in data if d.get("receivable_state") == "OPD")
    ipd_admitted = sum(flt(d.get("current_ledger_balance")) for d in data if d.get("receivable_state") == "IPD Admitted")
    ipd_discharged = sum(flt(d.get("current_ledger_balance")) for d in data if d.get("receivable_state") == "IPD Discharged")
    insurance = sum(flt(d.get("current_ledger_balance")) for d in data if d.get("receivable_state") == "Insurance")
    employee = sum(flt(d.get("current_ledger_balance")) for d in data if "Employee" in (d.get("receivable_state") or ""))

    return {
        "data": {
            "labels": ["OPD", "IPD Admitted", "IPD Discharged", "Insurance", "Employee"],
            "datasets": [
                {
                    "name": "Balance",
                    "values": [opd, ipd_admitted, ipd_discharged, insurance, employee],
                }
            ],
        },
        "type": "donut",
        "height": 300,
    }


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

def get_report_summary(data):
    if not data:
        return []

    total_balance = sum(flt(d.get("current_ledger_balance")) for d in data)
    total_discharge_balance = sum(flt(d.get("balance_at_discharge")) for d in data)
    total_post_discharge = sum(flt(d.get("post_discharge_movement")) for d in data)

    opd = sum(flt(d.get("current_ledger_balance")) for d in data if d.get("receivable_state") == "OPD")
    ipd_admitted = sum(flt(d.get("current_ledger_balance")) for d in data if d.get("receivable_state") == "IPD Admitted")
    ipd_discharged = sum(flt(d.get("current_ledger_balance")) for d in data if d.get("receivable_state") == "IPD Discharged")
    insurance = sum(flt(d.get("current_ledger_balance")) for d in data if d.get("receivable_state") == "Insurance")

    return [
        {
            "label": _("Total Ledger Balance"),
            "value": total_balance,
            "indicator": "Blue",
            "datatype": "Currency",
        },
        {
            "label": _("OPD"),
            "value": opd,
            "indicator": "Green",
            "datatype": "Currency",
        },
        {
            "label": _("IPD Admitted"),
            "value": ipd_admitted,
            "indicator": "Orange",
            "datatype": "Currency",
        },
        {
            "label": _("IPD Discharged"),
            "value": ipd_discharged,
            "indicator": "Red",
            "datatype": "Currency",
        },
        {
            "label": _("Insurance"),
            "value": insurance,
            "indicator": "Purple",
            "datatype": "Currency",
        },
        {
            "label": _("Ledger Balance On Discharge Date"),
            "value": total_discharge_balance,
            "indicator": "Orange",
            "datatype": "Currency",
        },
        {
            "label": _("Movement After Discharge"),
            "value": total_post_discharge,
            "indicator": "Red" if abs(total_post_discharge) > 0.0001 else "Green",
            "datatype": "Currency",
        },
    ]