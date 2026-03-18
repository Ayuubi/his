# Copyright (c) 2026
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}

    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_report_summary(data)

    return columns, data, None, chart, summary


# ------------------------------------------------------------
# Config helpers
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
            "label": _("Patient"),
            "fieldname": "patient",
            "fieldtype": "Link",
            "options": "Patient",
            "width": 140,
        },
        {
            "label": _("Patient Name"),
            "fieldname": "patient_name",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 160,
        },
        {
            "label": _("Billing Source"),
            "fieldname": "billing_source",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": _("Receivable Party Type"),
            "fieldname": "receivable_party_type",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Receivable Party"),
            "fieldname": "receivable_party",
            "fieldtype": "Dynamic Link",
            "options": "receivable_party_type",
            "width": 180,
        },
        {
            "label": _("Current IPD Status"),
            "fieldname": "current_ipd_status",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": _("Current IPD Record"),
            "fieldname": "current_inpatient_record",
            "fieldtype": "Link",
            "options": "Inpatient Record",
            "width": 160,
        },
        {
            "label": _("Last Discharge Date"),
            "fieldname": "last_discharge_date",
            "fieldtype": "Date",
            "width": 130,
        },
        {
            "label": _("OPD Invoice Outstanding"),
            "fieldname": "opd_invoice_outstanding",
            "fieldtype": "Currency",
            "width": 170,
        },
        {
            "label": _("IPD Admitted Invoice Outstanding"),
            "fieldname": "ipd_admitted_invoice_outstanding",
            "fieldtype": "Currency",
            "width": 190,
        },
        {
            "label": _("IPD Discharged Invoice Outstanding"),
            "fieldname": "ipd_discharged_invoice_outstanding",
            "fieldtype": "Currency",
            "width": 200,
        },
        {
            "label": _("Classified Invoice Total"),
            "fieldname": "classified_invoice_total",
            "fieldtype": "Currency",
            "width": 170,
        },
        {
            "label": _("Ledger Receivable Balance"),
            "fieldname": "ledger_receivable_balance",
            "fieldtype": "Currency",
            "width": 170,
        },
        {
            "label": _("Difference"),
            "fieldname": "difference",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Receivable State"),
            "fieldname": "receivable_state",
            "fieldtype": "Data",
            "width": 220,
        },
    ]


# ------------------------------------------------------------
# Main data
# ------------------------------------------------------------

def get_data(filters):
    invoice_rows = get_invoice_classification_rows(filters)
    patient_map = build_patient_map(invoice_rows)

    enrich_patient_customer_map(patient_map)
    enrich_with_current_ipd(patient_map)
    enrich_with_last_discharge(patient_map)
    enrich_with_ledger_balance(patient_map, filters)

    return finalize_rows(patient_map, filters)


# ------------------------------------------------------------
# Query 1: Invoice classification
# ------------------------------------------------------------

def get_invoice_classification_rows(filters):
    conditions = [
        "si.docstatus = 1",
        "IFNULL(si.is_return, 0) = 0",
        "IFNULL(si.outstanding_amount, 0) != 0",
    ]

    if _has_field("Sales Invoice", "company") and filters.get("company"):
        conditions.append("si.company = %(company)s")

    # Receivable should be as-of date
    if _has_field("Sales Invoice", "posting_date") and filters.get("to_date"):
        conditions.append("si.posting_date <= %(to_date)s")

    if _has_field("Sales Invoice", "patient") and filters.get("patient"):
        conditions.append("si.patient = %(patient)s")

    if _has_field("Sales Invoice", "customer") and filters.get("customer"):
        conditions.append("si.customer = %(customer)s")

    query = """
        SELECT
            si.name AS sales_invoice,
            si.patient,
            si.patient_name,
            si.customer,
            si.inpatient_record,
            IFNULL(si.outstanding_amount, 0) AS outstanding_amount,
            IFNULL(si.is_insurance, 0) AS is_insurance,
            si.insurance,
            IFNULL(si.bill_to_employee, 0) AS bill_to_employee,
            si.employee,
            IFNULL(si.is_inpatient, 0) AS is_inpatient,
            si.bill_to_patient,
            ip.status AS inpatient_status,
            ip.discharge_datetime
        FROM `tabSales Invoice` si
        LEFT JOIN `tabInpatient Record` ip
            ON ip.name = si.inpatient_record
        WHERE {conditions}
        ORDER BY si.patient, si.posting_date, si.name
    """.format(conditions=" AND ".join(conditions))

    return frappe.db.sql(query, filters, as_dict=True)


# ------------------------------------------------------------
# Receivable owner resolution
# ------------------------------------------------------------

def resolve_receivable_owner(row):
    patient_customer = row.get("customer")

    if cint_safe(row.get("is_insurance")) and row.get("insurance"):
        return {
            "billing_source": "Insurance",
            "receivable_party_type": "Customer",
            "receivable_party": row.get("insurance"),
        }

    if cint_safe(row.get("bill_to_employee")) and row.get("employee"):
        return {
            "billing_source": "Employee",
            "receivable_party_type": "Employee",
            "receivable_party": row.get("employee"),
        }

    if cint_safe(row.get("is_inpatient")) and row.get("bill_to_patient"):
        target_customer = frappe.db.get_value("Patient", row.get("bill_to_patient"), "customer")
        return {
            "billing_source": "Patient Transfer",
            "receivable_party_type": "Customer",
            "receivable_party": target_customer,
        }

    return {
        "billing_source": "Patient",
        "receivable_party_type": "Customer",
        "receivable_party": patient_customer,
    }


def build_patient_map(invoice_rows):
    admitted_statuses, discharged_statuses = get_ipd_status_sets()
    patient_map = {}

    for r in invoice_rows:
        patient = r.get("patient")
        customer = r.get("customer")

        if not patient and not customer:
            continue

        key = patient or f"CUSTOMER::{customer}"

        owner = resolve_receivable_owner(r)

        if key not in patient_map:
            patient_map[key] = {
                "patient": patient,
                "patient_name": r.get("patient_name"),
                "customer": customer,
                "billing_source": owner.get("billing_source") or "",
                "receivable_party_type": owner.get("receivable_party_type") or "",
                "receivable_party": owner.get("receivable_party") or "",
                "opd_invoice_outstanding": 0.0,
                "ipd_admitted_invoice_outstanding": 0.0,
                "ipd_discharged_invoice_outstanding": 0.0,
                "classified_invoice_total": 0.0,
                "ledger_receivable_balance": 0.0,
                "difference": 0.0,
                "receivable_state": "",
                "current_ipd_status": "",
                "current_inpatient_record": "",
                "last_discharge_date": None,
            }

        row = patient_map[key]

        if not row.get("patient_name") and r.get("patient_name"):
            row["patient_name"] = r.get("patient_name")
        if not row.get("customer") and r.get("customer"):
            row["customer"] = r.get("customer")
        if not row.get("billing_source") and owner.get("billing_source"):
            row["billing_source"] = owner.get("billing_source")
        if not row.get("receivable_party_type") and owner.get("receivable_party_type"):
            row["receivable_party_type"] = owner.get("receivable_party_type")
        if not row.get("receivable_party") and owner.get("receivable_party"):
            row["receivable_party"] = owner.get("receivable_party")

        outstanding = flt(r.get("outstanding_amount"))
        if outstanding <= 0:
            continue

        inpatient_record = r.get("inpatient_record")
        ipd_status = (r.get("inpatient_status") or "").strip()
        discharge_datetime = r.get("discharge_datetime")

        if not inpatient_record:
            row["opd_invoice_outstanding"] += outstanding
        else:
            if ipd_status in discharged_statuses:
                row["ipd_discharged_invoice_outstanding"] += outstanding
            elif ipd_status in admitted_statuses:
                row["ipd_admitted_invoice_outstanding"] += outstanding
            else:
                if discharge_datetime:
                    row["ipd_discharged_invoice_outstanding"] += outstanding
                else:
                    row["ipd_admitted_invoice_outstanding"] += outstanding

        row["classified_invoice_total"] = (
            flt(row["opd_invoice_outstanding"])
            + flt(row["ipd_admitted_invoice_outstanding"])
            + flt(row["ipd_discharged_invoice_outstanding"])
        )

    return patient_map


# ------------------------------------------------------------
# Patient enrichment
# ------------------------------------------------------------

def enrich_patient_customer_map(patient_map):
    if not patient_map or not _has_field("Patient", "customer"):
        return

    patient_names = [d["patient"] for d in patient_map.values() if d.get("patient")]
    if not patient_names:
        return

    rows = frappe.get_all(
        "Patient",
        filters={"name": ["in", patient_names]},
        fields=["name", "customer"],
        limit_page_length=0,
    )

    customer_map = {r["name"]: r.get("customer") for r in rows}

    for d in patient_map.values():
        patient = d.get("patient")
        patient_customer = customer_map.get(patient) if patient else None

        if patient and not d.get("customer"):
            d["customer"] = patient_customer

        if d.get("billing_source") == "Patient" and not d.get("receivable_party"):
            d["receivable_party_type"] = "Customer"
            d["receivable_party"] = patient_customer


def enrich_with_current_ipd(patient_map):
    if not patient_map:
        return

    patient_names = [d["patient"] for d in patient_map.values() if d.get("patient")]
    if not patient_names:
        return

    has_patient_ipr = _has_field("Patient", "inpatient_record")
    has_patient_ips = _has_field("Patient", "inpatient_status")

    if not has_patient_ipr and not has_patient_ips:
        return

    fields = ["name"]
    if has_patient_ipr:
        fields.append("inpatient_record")
    if has_patient_ips:
        fields.append("inpatient_status")

    patient_rows = frappe.get_all(
        "Patient",
        filters={"name": ["in", patient_names]},
        fields=fields,
        limit_page_length=0,
    )

    pmap = {r["name"]: r for r in patient_rows}

    for d in patient_map.values():
        patient = d.get("patient")
        if not patient or patient not in pmap:
            continue

        prow = pmap[patient]
        if has_patient_ipr:
            d["current_inpatient_record"] = prow.get("inpatient_record") or ""
        if has_patient_ips:
            d["current_ipd_status"] = prow.get("inpatient_status") or ""


def enrich_with_last_discharge(patient_map):
    if not patient_map:
        return

    patient_names = [d["patient"] for d in patient_map.values() if d.get("patient")]
    if not patient_names:
        return

    if not _has_field("Inpatient Record", "patient"):
        return

    if not _has_field("Inpatient Record", "discharge_datetime"):
        return

    _, discharged_statuses = get_ipd_status_sets()

    rows = frappe.get_all(
        "Inpatient Record",
        filters={
            "patient": ["in", patient_names],
            "status": ["in", list(discharged_statuses)],
        },
        fields=["patient", "max(discharge_datetime) as last_discharge_date"],
        group_by="patient",
        limit_page_length=0,
    )

    dmap = {r["patient"]: r.get("last_discharge_date") for r in rows}

    for d in patient_map.values():
        patient = d.get("patient")
        if patient in dmap:
            d["last_discharge_date"] = dmap[patient]


# ------------------------------------------------------------
# Ledger balance helpers
# ------------------------------------------------------------

def get_customer_receivable_accounts(filters):
    company = filters.get("company")

    if company == "Shaafi Hospital" or not company:
        return ["1310 - Debtors - SH"]

    values = {}
    company_condition = ""
    if company and _has_field("Account", "company"):
        company_condition = "AND company = %(company)s"
        values["company"] = company

    rows = frappe.db.sql(
        """
        SELECT name
        FROM `tabAccount`
        WHERE is_group = 0
          AND account_type = 'Receivable'
          AND name LIKE '%Debtors%'
          {company_condition}
        """.format(company_condition=company_condition),
        values,
        as_dict=True,
    )

    return [r.name for r in rows]


def get_employee_creditor_accounts(filters):
    company = filters.get("company")
    abbr = None

    if company and _has_field("Company", "abbr"):
        abbr = frappe.db.get_value("Company", company, "abbr")

    if abbr:
        return [f"2110 - Creditors - {abbr}"]

    values = {}
    company_condition = ""
    if company and _has_field("Account", "company"):
        company_condition = "AND company = %(company)s"
        values["company"] = company

    rows = frappe.db.sql(
        """
        SELECT name
        FROM `tabAccount`
        WHERE is_group = 0
          AND name LIKE '2110 - Creditors -%'
          {company_condition}
        """.format(company_condition=company_condition),
        values,
        as_dict=True,
    )

    return [r.name for r in rows]


def get_customer_party_balances(parties, filters):
    if not parties:
        return {}

    accounts = get_customer_receivable_accounts(filters)
    if not accounts:
        return {}

    values = {
        "parties": tuple(parties),
        "accounts": tuple(accounts),
    }

    company_condition = ""
    if filters.get("company") and _has_field("GL Entry", "company"):
        company_condition = "AND gle.company = %(company)s"
        values["company"] = filters.get("company")

    to_date_condition = ""
    if filters.get("to_date") and _has_field("GL Entry", "posting_date"):
        to_date_condition = "AND gle.posting_date <= %(to_date)s"
        values["to_date"] = filters.get("to_date")

    rows = frappe.db.sql(
        """
        SELECT
            gle.party,
            SUM(IFNULL(gle.debit, 0) - IFNULL(gle.credit, 0)) AS balance
        FROM `tabGL Entry` gle
        WHERE gle.party_type = 'Customer'
          AND gle.is_cancelled = 0
          AND gle.party IN %(parties)s
          AND gle.account IN %(accounts)s
          {company_condition}
          {to_date_condition}
        GROUP BY gle.party
        """.format(
            company_condition=company_condition,
            to_date_condition=to_date_condition,
        ),
        values,
        as_dict=True,
    )

    return {r.party: flt(r.balance) for r in rows}


def get_employee_party_balances(parties, filters):
    if not parties:
        return {}

    accounts = get_employee_creditor_accounts(filters)
    if not accounts:
        return {}

    values = {
        "parties": tuple(parties),
        "accounts": tuple(accounts),
    }

    company_condition = ""
    if filters.get("company") and _has_field("GL Entry", "company"):
        company_condition = "AND gle.company = %(company)s"
        values["company"] = filters.get("company")

    to_date_condition = ""
    if filters.get("to_date") and _has_field("GL Entry", "posting_date"):
        to_date_condition = "AND gle.posting_date <= %(to_date)s"
        values["to_date"] = filters.get("to_date")

    rows = frappe.db.sql(
        """
        SELECT
            gle.party,
            SUM(IFNULL(gle.debit, 0) - IFNULL(gle.credit, 0)) AS balance
        FROM `tabGL Entry` gle
        WHERE gle.party_type = 'Employee'
          AND gle.is_cancelled = 0
          AND gle.party IN %(parties)s
          AND gle.account IN %(accounts)s
          {company_condition}
          {to_date_condition}
        GROUP BY gle.party
        """.format(
            company_condition=company_condition,
            to_date_condition=to_date_condition,
        ),
        values,
        as_dict=True,
    )

    # employee case is on creditors; present as positive due amount
    return {r.party: abs(flt(r.balance)) for r in rows}


def enrich_with_ledger_balance(patient_map, filters):
    if not patient_map:
        return

    customer_parties = list({
        d.get("receivable_party")
        for d in patient_map.values()
        if d.get("receivable_party_type") == "Customer" and d.get("receivable_party")
    })

    employee_parties = list({
        d.get("receivable_party")
        for d in patient_map.values()
        if d.get("receivable_party_type") == "Employee" and d.get("receivable_party")
    })

    customer_balance_map = get_customer_party_balances(customer_parties, filters)
    employee_balance_map = get_employee_party_balances(employee_parties, filters)

    for d in patient_map.values():
        ptype = d.get("receivable_party_type")
        party = d.get("receivable_party")

        if ptype == "Customer":
            d["ledger_receivable_balance"] = flt(customer_balance_map.get(party))
        elif ptype == "Employee":
            d["ledger_receivable_balance"] = flt(employee_balance_map.get(party))
        else:
            d["ledger_receivable_balance"] = 0.0

        d["difference"] = flt(d["ledger_receivable_balance"]) - flt(d["classified_invoice_total"])


# ------------------------------------------------------------
# Final shaping
# ------------------------------------------------------------

def determine_receivable_state(row):
    opd = flt(row.get("opd_invoice_outstanding"))
    adm = flt(row.get("ipd_admitted_invoice_outstanding"))
    dis = flt(row.get("ipd_discharged_invoice_outstanding"))
    classified = flt(row.get("classified_invoice_total"))
    ledger = flt(row.get("ledger_receivable_balance"))
    diff = flt(row.get("difference"))

    non_zero_buckets = sum(1 for x in [opd, adm, dis] if abs(x) > 0.0001)

    if abs(classified) <= 0.0001 and abs(ledger) > 0.0001:
        return "Unclassified Ledger Balance"

    if abs(classified) > 0.0001 and abs(diff) > 0.0001:
        if non_zero_buckets <= 1:
            if adm > 0:
                return "IPD Admitted / Reconciliation Issue"
            if dis > 0:
                return "IPD Discharged / Reconciliation Issue"
            if opd > 0:
                return "OPD / Reconciliation Issue"
        return "Mixed / Reconciliation Issue"

    if non_zero_buckets > 1:
        return "Mixed"
    if adm > 0:
        return "IPD Admitted"
    if dis > 0:
        return "IPD Discharged"
    if opd > 0:
        return "OPD"

    return "Zero"


def finalize_rows(patient_map, filters):
    rows = list(patient_map.values())

    cleaned = []
    for r in rows:
        if (
            abs(flt(r.get("classified_invoice_total"))) > 0.0001
            or abs(flt(r.get("ledger_receivable_balance"))) > 0.0001
        ):
            r["receivable_state"] = determine_receivable_state(r)
            cleaned.append(r)

    category_filter = filters.get("receivable_state")
    if category_filter:
        cleaned = [r for r in cleaned if r.get("receivable_state") == category_filter]

    billing_source = filters.get("billing_source")
    if billing_source:
        cleaned = [r for r in cleaned if r.get("billing_source") == billing_source]

    only_with_difference = cint_safe(filters.get("only_with_difference"))
    if only_with_difference:
        cleaned = [r for r in cleaned if abs(flt(r.get("difference"))) > 0.0001]

    min_outstanding = flt(filters.get("min_outstanding"))
    if min_outstanding:
        cleaned = [
            r for r in cleaned
            if flt(r.get("classified_invoice_total")) >= min_outstanding
            or flt(r.get("ledger_receivable_balance")) >= min_outstanding
        ]

    sort_by = filters.get("sort_by") or "classified_invoice_total"

    reverse = True
    numeric_fields = {
        "opd_invoice_outstanding",
        "ipd_admitted_invoice_outstanding",
        "ipd_discharged_invoice_outstanding",
        "classified_invoice_total",
        "ledger_receivable_balance",
        "difference",
    }

    try:
        if sort_by in numeric_fields:
            cleaned.sort(key=lambda x: flt(x.get(sort_by)), reverse=reverse)
        else:
            cleaned.sort(key=lambda x: (x.get(sort_by) or ""), reverse=reverse)
    except Exception:
        cleaned.sort(key=lambda x: flt(x.get("classified_invoice_total")), reverse=True)

    return cleaned


# ------------------------------------------------------------
# Chart
# ------------------------------------------------------------

def get_chart(data):
    if not data:
        return None

    opd = sum(flt(d.get("opd_invoice_outstanding")) for d in data)
    adm = sum(flt(d.get("ipd_admitted_invoice_outstanding")) for d in data)
    dis = sum(flt(d.get("ipd_discharged_invoice_outstanding")) for d in data)

    return {
        "data": {
            "labels": ["OPD", "IPD Admitted", "IPD Discharged"],
            "datasets": [
                {
                    "name": "Receivable",
                    "values": [opd, adm, dis],
                }
            ],
        },
        "type": "donut",
        "height": 280,
    }


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

def get_report_summary(data):
    if not data:
        return []

    opd = sum(flt(d.get("opd_invoice_outstanding")) for d in data)
    adm = sum(flt(d.get("ipd_admitted_invoice_outstanding")) for d in data)
    dis = sum(flt(d.get("ipd_discharged_invoice_outstanding")) for d in data)
    classified = sum(flt(d.get("classified_invoice_total")) for d in data)
    ledger = sum(flt(d.get("ledger_receivable_balance")) for d in data)
    diff = sum(flt(d.get("difference")) for d in data)

    return [
        {
            "label": _("OPD"),
            "value": opd,
            "indicator": "Blue",
            "datatype": "Currency",
        },
        {
            "label": _("IPD Admitted"),
            "value": adm,
            "indicator": "Orange",
            "datatype": "Currency",
        },
        {
            "label": _("IPD Discharged"),
            "value": dis,
            "indicator": "Red",
            "datatype": "Currency",
        },
        {
            "label": _("Classified Total"),
            "value": classified,
            "indicator": "Green",
            "datatype": "Currency",
        },
        {
            "label": _("Ledger Total"),
            "value": ledger,
            "indicator": "Purple",
            "datatype": "Currency",
        },
        {
            "label": _("Difference"),
            "value": diff,
            "indicator": "Red" if abs(diff) > 0.0001 else "Green",
            "datatype": "Currency",
        },
    ]