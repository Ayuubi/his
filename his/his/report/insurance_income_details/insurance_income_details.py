# Copyright (c) 2026, Shaafi Hospital
# For license information, please see license.txt

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt, getdate


# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------

INSURANCE_CUSTOMER_GROUP = "Insurance"

# Custom fields
SALES_INVOICE_INSURANCE_FIELD = "insurance"
JOURNAL_ENTRY_INVOICE_FIELD = "sales_invoice"


def execute(filters=None):
    filters = frappe._dict(filters or {})

    validate_filters(filters)
    validate_required_fields()

    view = filters.get("view") or "Income Summary"

    invoice_rows = get_insurance_invoice_items(filters)
    journal_maps = get_journal_entry_maps(filters)

    attach_journal_information(invoice_rows, journal_maps)

    unallocated_rows = get_unallocated_journals(
        filters=filters,
        journal_entries=journal_maps.get("journal_entries", {}),
    )

    report_summary = get_report_summary(
        invoice_rows=invoice_rows,
        unallocated_rows=unallocated_rows,
    )

    if view == "Income Summary":
        columns, data = build_income_summary(invoice_rows)

    elif view == "Item Group Summary":
        columns, data = build_item_group_summary(invoice_rows)

    elif view == "Invoice Details":
        columns = get_invoice_detail_columns()
        data = build_invoice_details(invoice_rows, filters)

    elif view == "Unallocated Journals":
        columns = get_unallocated_journal_columns()
        data = build_unallocated_journal_details(unallocated_rows, filters)

    else:
        frappe.throw(_("Unsupported report view: {0}").format(view))

    chart = build_chart(invoice_rows, view)

    return columns, data, None, chart, report_summary


# -------------------------------------------------------------------------
# Validation
# -------------------------------------------------------------------------

def validate_filters(filters):
    if not filters.get("from_date"):
        frappe.throw(_("From Date is required."))

    if not filters.get("to_date"):
        frappe.throw(_("To Date is required."))

    if getdate(filters.from_date) > getdate(filters.to_date):
        frappe.throw(_("From Date cannot be after To Date."))


def validate_required_fields():
    missing = []

    if not frappe.get_meta("Sales Invoice").has_field(
        SALES_INVOICE_INSURANCE_FIELD
    ):
        missing.append(
            "Sales Invoice.{0}".format(SALES_INVOICE_INSURANCE_FIELD)
        )

    if not frappe.get_meta("Journal Entry").has_field(
        JOURNAL_ENTRY_INVOICE_FIELD
    ):
        missing.append(
            "Journal Entry.{0}".format(JOURNAL_ENTRY_INVOICE_FIELD)
        )

    if missing:
        frappe.throw(
            _(
                "The following required custom fields do not exist:<br>{0}"
            ).format("<br>".join(missing))
        )


# -------------------------------------------------------------------------
# Insurance invoice items
# -------------------------------------------------------------------------

def get_insurance_invoice_items(filters):
    conditions = [
        "si.docstatus = 1",
        "si.posting_date BETWEEN %(from_date)s AND %(to_date)s",
        "IFNULL(si.`{insurance_field}`, '') != ''".format(
            insurance_field=SALES_INVOICE_INSURANCE_FIELD
        ),
    ]

    params = {
        "from_date": filters.from_date,
        "to_date": filters.to_date,
    }

    if filters.get("company"):
        conditions.append("si.company = %(company)s")
        params["company"] = filters.company

    if filters.get("insurance"):
        conditions.append(
            "si.`{insurance_field}` = %(insurance)s".format(
                insurance_field=SALES_INVOICE_INSURANCE_FIELD
            )
        )
        params["insurance"] = filters.insurance

    if filters.get("item_group"):
        conditions.append("sii.item_group = %(item_group)s")
        params["item_group"] = filters.item_group

    if filters.get("income_account"):
        conditions.append("sii.income_account = %(income_account)s")
        params["income_account"] = filters.income_account

    if filters.get("patient"):
        conditions.append("si.patient = %(patient)s")
        params["patient"] = filters.patient

    if filters.get("sales_invoice"):
        conditions.append("si.name = %(sales_invoice)s")
        params["sales_invoice"] = filters.sales_invoice

    query = """
        SELECT
            si.name AS sales_invoice,
            si.posting_date,
            DATE_FORMAT(si.posting_date, '%%Y-%%m') AS month_key,
            DATE_FORMAT(si.posting_date, '%%M %%Y') AS month_label,

            si.company,
            si.customer,
            si.customer_name,

            si.patient,
            si.patient_name,

            si.`{insurance_field}` AS insurance,

            si.is_return,
            si.return_against,

            sii.name AS sales_invoice_item,
            sii.idx,
            sii.item_code,
            sii.item_name,
            sii.item_group,
            sii.income_account,
            sii.qty,
            sii.rate,
            sii.net_rate,
            sii.amount,
            sii.net_amount,

            CASE
                WHEN si.is_return = 1 THEN 'Return'
                ELSE 'Sales Invoice'
            END AS transaction_type

        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii
            ON sii.parent = si.name
            AND sii.parenttype = 'Sales Invoice'
            AND sii.parentfield = 'items'

        WHERE {conditions}

        ORDER BY
            si.posting_date,
            si.name,
            sii.idx
    """.format(
        insurance_field=SALES_INVOICE_INSURANCE_FIELD,
        conditions=" AND ".join(conditions),
    )

    rows = frappe.db.sql(query, params, as_dict=True)

    for row in rows:
        row.qty = flt(row.qty)
        row.rate = flt(row.rate)
        row.net_rate = flt(row.net_rate)
        row.amount = flt(row.amount)
        row.net_amount = flt(row.net_amount)

        # We use net_amount as the income amount.
        # Return Sales Invoices normally already contain negative net amounts.
        row.report_amount = flt(row.net_amount)

        row.journal_entries = []
        row.journal_entry = None
        row.transfer_status = "Not Transferred"
        row.transferred_amount = 0

    return rows


# -------------------------------------------------------------------------
# Journal Entries
# -------------------------------------------------------------------------

def get_journal_entry_maps(filters):
    conditions = [
        "je.docstatus = 1",
        "je.posting_date BETWEEN %(from_date)s AND %(to_date)s",
    ]

    params = {
        "from_date": filters.from_date,
        "to_date": filters.to_date,
    }

    if filters.get("company"):
        conditions.append("je.company = %(company)s")
        params["company"] = filters.company

    if filters.get("journal_entry"):
        conditions.append("je.name = %(journal_entry)s")
        params["journal_entry"] = filters.journal_entry

    journal_entries = frappe.db.sql(
        """
        SELECT
            je.name,
            je.posting_date,
            je.company,
            je.voucher_type,
            je.user_remark,
            je.`{invoice_field}` AS sales_invoice
        FROM `tabJournal Entry` je
        WHERE {conditions}
        ORDER BY je.posting_date, je.name
        """.format(
            invoice_field=JOURNAL_ENTRY_INVOICE_FIELD,
            conditions=" AND ".join(conditions),
        ),
        params,
        as_dict=True,
    )

    journal_names = [row.name for row in journal_entries]

    if not journal_names:
        return {
            "journal_entries": {},
            "accounts_by_journal": {},
            "journals_by_invoice": {},
        }

    account_rows = frappe.get_all(
        "Journal Entry Account",
        filters={
            "parent": ["in", journal_names],
            "parenttype": "Journal Entry",
            "parentfield": "accounts",
        },
        fields=[
            "parent",
            "idx",
            "account",
            "account_type",
            "party_type",
            "party",
            "debit",
            "credit",
            "debit_in_account_currency",
            "credit_in_account_currency",
            "user_remark",
        ],
        order_by="parent, idx",
    )

    customer_names = list(
        {
            row.party
            for row in account_rows
            if row.party_type == "Customer" and row.party
        }
    )

    customer_groups = {}

    if customer_names:
        customer_rows = frappe.get_all(
            "Customer",
            filters={"name": ["in", customer_names]},
            fields=["name", "customer_name", "customer_group"],
        )

        customer_groups = {
            row.name: row
            for row in customer_rows
        }

    accounts_by_journal = defaultdict(list)

    for row in account_rows:
        customer = customer_groups.get(row.party)

        row.customer_group = (
            customer.customer_group
            if customer
            else None
        )

        row.party_name = (
            customer.customer_name
            if customer
            else row.party
        )

        accounts_by_journal[row.parent].append(row)

    journal_entry_map = {
        row.name: row
        for row in journal_entries
    }

    journals_by_invoice = defaultdict(list)

    for journal in journal_entries:
        invoice_name = clean_text(journal.sales_invoice)

        if not invoice_name:
            continue

        journals_by_invoice[invoice_name].append(journal)

    return {
        "journal_entries": journal_entry_map,
        "accounts_by_journal": accounts_by_journal,
        "journals_by_invoice": journals_by_invoice,
    }


def attach_journal_information(invoice_rows, journal_maps):
    journals_by_invoice = journal_maps.get("journals_by_invoice", {})
    accounts_by_journal = journal_maps.get("accounts_by_journal", {})

    invoice_names = list(
        {
            row.sales_invoice
            for row in invoice_rows
            if row.sales_invoice
        }
    )

    valid_invoices = set()

    if invoice_names:
        valid_invoices = set(
            frappe.get_all(
                "Sales Invoice",
                filters={"name": ["in", invoice_names]},
                pluck="name",
            )
        )

    for row in invoice_rows:
        if row.sales_invoice not in valid_invoices:
            row.transfer_status = "Invalid Invoice"
            continue

        linked_journals = journals_by_invoice.get(row.sales_invoice, [])

        valid_transfer_journals = []
        total_transferred = 0

        for journal in linked_journals:
            journal_accounts = accounts_by_journal.get(journal.name, [])

            transfer_info = analyze_insurance_transfer(
                journal_accounts,
                expected_insurance=row.insurance,
            )

            if not transfer_info.is_transfer:
                continue

            valid_transfer_journals.append(journal.name)
            total_transferred += flt(transfer_info.insurance_debit)

        row.journal_entries = valid_transfer_journals
        row.journal_entry = ", ".join(valid_transfer_journals)
        row.transferred_amount = total_transferred

        if valid_transfer_journals:
            row.transfer_status = "Allocated"
        else:
            row.transfer_status = "Not Transferred"


def analyze_insurance_transfer(accounts, expected_insurance=None):
    result = frappe._dict(
        {
            "is_transfer": False,
            "insurance_parties": [],
            "other_customer_parties": [],
            "insurance_debit": 0,
            "insurance_credit": 0,
            "other_customer_debit": 0,
            "other_customer_credit": 0,
        }
    )

    for account in accounts:
        if account.party_type != "Customer" or not account.party:
            continue

        is_insurance = (
            account.customer_group == INSURANCE_CUSTOMER_GROUP
        )

        if expected_insurance:
            is_expected_insurance = account.party == expected_insurance
        else:
            is_expected_insurance = is_insurance

        if is_insurance and is_expected_insurance:
            result.insurance_parties.append(account.party)
            result.insurance_debit += flt(account.debit)
            result.insurance_credit += flt(account.credit)

        elif not is_insurance:
            result.other_customer_parties.append(account.party)
            result.other_customer_debit += flt(account.debit)
            result.other_customer_credit += flt(account.credit)

    result.insurance_parties = unique_list(result.insurance_parties)
    result.other_customer_parties = unique_list(
        result.other_customer_parties
    )

    result.is_transfer = bool(
        result.insurance_parties
        and result.other_customer_parties
    )

    return result


# -------------------------------------------------------------------------
# Unallocated Journal Entries
# -------------------------------------------------------------------------

def get_unallocated_journals(filters, journal_entries):
    if not journal_entries:
        return []

    journal_names = list(journal_entries.keys())

    account_rows = frappe.get_all(
        "Journal Entry Account",
        filters={
            "parent": ["in", journal_names],
            "parenttype": "Journal Entry",
            "parentfield": "accounts",
        },
        fields=[
            "parent",
            "idx",
            "account",
            "party_type",
            "party",
            "debit",
            "credit",
            "user_remark",
        ],
        order_by="parent, idx",
    )

    customer_names = list(
        {
            row.party
            for row in account_rows
            if row.party_type == "Customer" and row.party
        }
    )

    customers = {}

    if customer_names:
        customer_rows = frappe.get_all(
            "Customer",
            filters={"name": ["in", customer_names]},
            fields=["name", "customer_name", "customer_group"],
        )

        customers = {
            row.name: row
            for row in customer_rows
        }

    accounts_by_journal = defaultdict(list)

    for row in account_rows:
        customer = customers.get(row.party)

        row.customer_group = (
            customer.customer_group
            if customer
            else None
        )

        row.party_name = (
            customer.customer_name
            if customer
            else row.party
        )

        accounts_by_journal[row.parent].append(row)

    entered_invoice_names = list(
        {
            clean_text(journal.sales_invoice)
            for journal in journal_entries.values()
            if clean_text(journal.sales_invoice)
        }
    )

    valid_invoice_names = set()

    if entered_invoice_names:
        valid_invoice_names = set(
            frappe.get_all(
                "Sales Invoice",
                filters={"name": ["in", entered_invoice_names]},
                pluck="name",
            )
        )

    output = []

    for journal_name, journal in journal_entries.items():
        accounts = accounts_by_journal.get(journal_name, [])

        transfer_info = analyze_insurance_transfer(accounts)

        if not transfer_info.is_transfer:
            continue

        entered_invoice = clean_text(journal.sales_invoice)

        # A valid Sales Invoice means it is allocated.
        if entered_invoice and entered_invoice in valid_invoice_names:
            continue

        reason = (
            "No Sales Invoice"
            if not entered_invoice
            else "Invalid Sales Invoice"
        )

        insurance_rows = []
        other_customer_rows = []

        for account in accounts:
            if account.party_type != "Customer" or not account.party:
                continue

            if account.customer_group == INSURANCE_CUSTOMER_GROUP:
                insurance_rows.append(account)
            else:
                other_customer_rows.append(account)

        insurance_names = unique_list(
            [
                row.party_name or row.party
                for row in insurance_rows
            ]
        )

        insurance_ids = unique_list(
            [row.party for row in insurance_rows]
        )

        other_customer_names = unique_list(
            [
                row.party_name or row.party
                for row in other_customer_rows
            ]
        )

        other_customer_ids = unique_list(
            [row.party for row in other_customer_rows]
        )

        insurance_debit = sum(
            flt(row.debit)
            for row in insurance_rows
        )

        insurance_credit = sum(
            flt(row.credit)
            for row in insurance_rows
        )

        other_debit = sum(
            flt(row.debit)
            for row in other_customer_rows
        )

        other_credit = sum(
            flt(row.credit)
            for row in other_customer_rows
        )

        transfer_amount = max(
            insurance_debit,
            insurance_credit,
            other_debit,
            other_credit,
        )

        output.append(
            frappe._dict(
                {
                    "posting_date": journal.posting_date,
                    "journal_entry": journal.name,
                    "company": journal.company,
                    "insurance": ", ".join(insurance_ids),
                    "insurance_name": ", ".join(insurance_names),
                    "other_customer": ", ".join(
                        other_customer_ids
                    ),
                    "other_customer_name": ", ".join(
                        other_customer_names
                    ),
                    "insurance_debit": insurance_debit,
                    "insurance_credit": insurance_credit,
                    "other_customer_debit": other_debit,
                    "other_customer_credit": other_credit,
                    "amount": transfer_amount,
                    "reference_entered": entered_invoice,
                    "reason": reason,
                    "user_remark": journal.user_remark,
                }
            )
        )

    output = apply_unallocated_filters(output, filters)

    return sorted(
        output,
        key=lambda row: (
            row.posting_date,
            row.journal_entry,
        ),
    )


def apply_unallocated_filters(rows, filters):
    output = []

    for row in rows:
        if filters.get("insurance"):
            insurance_parties = [
                value.strip()
                for value in (row.insurance or "").split(",")
                if value.strip()
            ]

            if filters.insurance not in insurance_parties:
                continue

        if filters.get("journal_entry"):
            if row.journal_entry != filters.journal_entry:
                continue

        output.append(row)

    return output


# -------------------------------------------------------------------------
# Income Summary
# -------------------------------------------------------------------------

def build_income_summary(invoice_rows):
    insurance_names = get_insurance_names(invoice_rows)

    columns = [
        {
            "label": _("Month"),
            "fieldname": "month",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": _("Income Account"),
            "fieldname": "income_account",
            "fieldtype": "Link",
            "options": "Account",
            "width": 260,
        },
    ]

    insurance_field_map = {}

    for index, insurance in enumerate(insurance_names, start=1):
        fieldname = "insurance_{0}".format(index)
        insurance_field_map[insurance] = fieldname

        columns.append(
            {
                "label": insurance,
                "fieldname": fieldname,
                "fieldtype": "Currency",
                "width": 140,
            }
        )

    columns.append(
        {
            "label": _("Grand Total"),
            "fieldname": "grand_total",
            "fieldtype": "Currency",
            "width": 150,
        }
    )

    monthly_accounts = defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(float)
        )
    )

    month_labels = {}

    for row in invoice_rows:
        month_key = row.month_key
        month_labels[month_key] = row.month_label

        income_account = (
            row.income_account
            or _("No Income Account")
        )

        monthly_accounts[month_key][income_account][
            row.insurance
        ] += flt(row.report_amount)

    data = []
    grand_totals = defaultdict(float)

    for month_key in sorted(monthly_accounts.keys()):
        account_map = monthly_accounts[month_key]

        month_totals = defaultdict(float)

        for insurance_map in account_map.values():
            for insurance, amount in insurance_map.items():
                month_totals[insurance] += flt(amount)

        month_row = {
            "month": month_labels.get(month_key) or month_key,
            "income_account": None,
            "indent": 0,
            "is_month_total": 1,
        }

        month_grand_total = 0

        for insurance in insurance_names:
            amount = flt(month_totals.get(insurance))
            month_row[insurance_field_map[insurance]] = amount
            month_grand_total += amount
            grand_totals[insurance] += amount

        month_row["grand_total"] = month_grand_total
        data.append(month_row)

        for income_account in sorted(account_map.keys()):
            row_data = {
                "month": "",
                "income_account": income_account,
                "indent": 1,
            }

            row_total = 0

            for insurance in insurance_names:
                amount = flt(
                    account_map[income_account].get(insurance)
                )

                row_data[insurance_field_map[insurance]] = amount
                row_total += amount

            row_data["grand_total"] = row_total
            data.append(row_data)

    if data:
        grand_row = {
            "month": _("Grand Total"),
            "income_account": None,
            "indent": 0,
            "is_grand_total": 1,
        }

        overall_total = 0

        for insurance in insurance_names:
            amount = flt(grand_totals.get(insurance))
            grand_row[insurance_field_map[insurance]] = amount
            overall_total += amount

        grand_row["grand_total"] = overall_total
        data.append(grand_row)

    return columns, data


# -------------------------------------------------------------------------
# Item Group Summary
# -------------------------------------------------------------------------

def build_item_group_summary(invoice_rows):
    insurance_names = get_insurance_names(invoice_rows)

    columns = [
        {
            "label": _("Month"),
            "fieldname": "month",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": _("Item Group"),
            "fieldname": "item_group",
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 220,
        },
    ]

    insurance_field_map = {}

    for index, insurance in enumerate(insurance_names, start=1):
        fieldname = "insurance_{0}".format(index)
        insurance_field_map[insurance] = fieldname

        columns.append(
            {
                "label": insurance,
                "fieldname": fieldname,
                "fieldtype": "Currency",
                "width": 140,
            }
        )

    columns.append(
        {
            "label": _("Grand Total"),
            "fieldname": "grand_total",
            "fieldtype": "Currency",
            "width": 150,
        }
    )

    monthly_groups = defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(float)
        )
    )

    month_labels = {}

    for row in invoice_rows:
        month_key = row.month_key
        month_labels[month_key] = row.month_label

        item_group = (
            row.item_group
            or _("No Item Group")
        )

        monthly_groups[month_key][item_group][
            row.insurance
        ] += flt(row.report_amount)

    data = []
    grand_totals = defaultdict(float)

    for month_key in sorted(monthly_groups.keys()):
        group_map = monthly_groups[month_key]

        month_totals = defaultdict(float)

        for insurance_map in group_map.values():
            for insurance, amount in insurance_map.items():
                month_totals[insurance] += flt(amount)

        month_row = {
            "month": month_labels.get(month_key) or month_key,
            "item_group": None,
            "indent": 0,
            "is_month_total": 1,
        }

        month_grand_total = 0

        for insurance in insurance_names:
            amount = flt(month_totals.get(insurance))
            month_row[insurance_field_map[insurance]] = amount
            month_grand_total += amount
            grand_totals[insurance] += amount

        month_row["grand_total"] = month_grand_total
        data.append(month_row)

        for item_group in sorted(group_map.keys()):
            row_data = {
                "month": "",
                "item_group": item_group,
                "indent": 1,
            }

            row_total = 0

            for insurance in insurance_names:
                amount = flt(
                    group_map[item_group].get(insurance)
                )

                row_data[insurance_field_map[insurance]] = amount
                row_total += amount

            row_data["grand_total"] = row_total
            data.append(row_data)

    if data:
        grand_row = {
            "month": _("Grand Total"),
            "item_group": None,
            "indent": 0,
            "is_grand_total": 1,
        }

        overall_total = 0

        for insurance in insurance_names:
            amount = flt(grand_totals.get(insurance))
            grand_row[insurance_field_map[insurance]] = amount
            overall_total += amount

        grand_row["grand_total"] = overall_total
        data.append(grand_row)

    return columns, data


# -------------------------------------------------------------------------
# Invoice Details
# -------------------------------------------------------------------------

def get_invoice_detail_columns():
    return [
        {
            "label": _("Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 105,
        },
        {
            "label": _("Insurance"),
            "fieldname": "insurance",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 180,
        },
        {
            "label": _("Sales Invoice"),
            "fieldname": "sales_invoice",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 190,
        },
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
            "width": 190,
        },
        {
            "label": _("Item"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 160,
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Item Group"),
            "fieldname": "item_group",
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 170,
        },
        {
            "label": _("Income Account"),
            "fieldname": "income_account",
            "fieldtype": "Link",
            "options": "Account",
            "width": 230,
        },
        {
            "label": _("Quantity"),
            "fieldname": "qty",
            "fieldtype": "Float",
            "width": 90,
        },
        {
            "label": _("Amount"),
            "fieldname": "report_amount",
            "fieldtype": "Currency",
            "width": 115,
        },
        {
            "label": _("Journal Entry"),
            "fieldname": "journal_entry",
            "fieldtype": "Data",
            "width": 210,
        },
        {
            "label": _("Transfer Status"),
            "fieldname": "transfer_status",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": _("Transaction Type"),
            "fieldname": "transaction_type",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Return Against"),
            "fieldname": "return_against",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 190,
        },
    ]


def build_invoice_details(invoice_rows, filters):
    status_filter = filters.get("status")

    data = []

    for row in invoice_rows:
        if status_filter and row.transfer_status != status_filter:
            continue

        data.append(
            {
                "posting_date": row.posting_date,
                "insurance": row.insurance,
                "sales_invoice": row.sales_invoice,
                "patient": row.patient,
                "patient_name": row.patient_name,
                "item_code": row.item_code,
                "item_name": row.item_name,
                "item_group": row.item_group,
                "income_account": row.income_account,
                "qty": row.qty,
                "report_amount": row.report_amount,
                "journal_entry": row.journal_entry,
                "transfer_status": row.transfer_status,
                "transaction_type": row.transaction_type,
                "return_against": row.return_against,
            }
        )

    return data


# -------------------------------------------------------------------------
# Unallocated Journal Details
# -------------------------------------------------------------------------

def get_unallocated_journal_columns():
    return [
        {
            "label": _("Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 105,
        },
        {
            "label": _("Journal Entry"),
            "fieldname": "journal_entry",
            "fieldtype": "Link",
            "options": "Journal Entry",
            "width": 200,
        },
        {
            "label": _("Insurance"),
            "fieldname": "insurance",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("Insurance Name"),
            "fieldname": "insurance_name",
            "fieldtype": "Data",
            "width": 190,
        },
        {
            "label": _("Other Customer"),
            "fieldname": "other_customer",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("Other Customer Name"),
            "fieldname": "other_customer_name",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Insurance Debit"),
            "fieldname": "insurance_debit",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Insurance Credit"),
            "fieldname": "insurance_credit",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Amount"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": _("Reference Entered"),
            "fieldname": "reference_entered",
            "fieldtype": "Data",
            "width": 190,
        },
        {
            "label": _("Reason"),
            "fieldname": "reason",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _("User Remark"),
            "fieldname": "user_remark",
            "fieldtype": "Data",
            "width": 300,
        },
    ]


def build_unallocated_journal_details(rows, filters):
    return rows


# -------------------------------------------------------------------------
# Report Summary
# -------------------------------------------------------------------------

def get_report_summary(invoice_rows, unallocated_rows):
    insurance_income = sum(
        flt(row.report_amount)
        for row in invoice_rows
    )

    allocated_income = sum(
        flt(row.report_amount)
        for row in invoice_rows
        if row.transfer_status == "Allocated"
    )

    not_transferred_income = sum(
        flt(row.report_amount)
        for row in invoice_rows
        if row.transfer_status == "Not Transferred"
    )

    unallocated_amount = sum(
        flt(row.amount)
        for row in unallocated_rows
    )

    return [
        {
            "value": insurance_income,
            "indicator": "Blue",
            "label": _("Insurance Income"),
            "datatype": "Currency",
        },
        {
            "value": allocated_income,
            "indicator": "Green",
            "label": _("Allocated Invoice Income"),
            "datatype": "Currency",
        },
        {
            "value": not_transferred_income,
            "indicator": "Orange",
            "label": _("Not Transferred"),
            "datatype": "Currency",
        },
        {
            "value": unallocated_amount,
            "indicator": "Red",
            "label": _("Unallocated Journals"),
            "datatype": "Currency",
        },
    ]


# -------------------------------------------------------------------------
# Chart
# -------------------------------------------------------------------------

def build_chart(invoice_rows, view):
    if view == "Unallocated Journals":
        return None

    insurance_totals = defaultdict(float)

    for row in invoice_rows:
        insurance_totals[row.insurance] += flt(row.report_amount)

    if not insurance_totals:
        return None

    labels = sorted(insurance_totals.keys())

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("Insurance Income"),
                    "values": [
                        flt(insurance_totals[label])
                        for label in labels
                    ],
                }
            ],
        },
        "type": "bar",
        "height": 280,
    }


# -------------------------------------------------------------------------
# Utilities
# -------------------------------------------------------------------------

def get_insurance_names(invoice_rows):
    return sorted(
        {
            row.insurance
            for row in invoice_rows
            if row.insurance
        }
    )


def unique_list(values):
    seen = set()
    output = []

    for value in values:
        if not value or value in seen:
            continue

        seen.add(value)
        output.append(value)

    return output


def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()
