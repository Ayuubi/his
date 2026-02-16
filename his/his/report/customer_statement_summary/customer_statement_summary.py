# Copyright (c) 2025, Rasiin Tech and contributors
# For license information, please see license.txt
# Copyright (c) 2025, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.report.general_ledger.general_ledger import execute as gl_execute
from collections import defaultdict

from datetime import datetime

his_settings = frappe.get_doc("HIS Settings", "HIS Settings")
INCLUDE_SI_DISCOUNTS = bool(his_settings.add_si)
# frappe.errprint(INCLUDE_SI_DISCOUNTS)
# 👉 Toggle: include Sales Invoice header discounts in this report?
# INCLUDE_SI_DISCOUNTS = False  # set to True if you want SI discounts back

def execute(filters=None):
    company = filters.get("company")
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    if filters.get("party"):
        filters.party = frappe.parse_json(filters.get("party"))

    customer = filters.get("party")


    if not company or not from_date or not to_date:
        frappe.throw(_("Company, From Date, and To Date are mandatory fields."))

    # if not customer:
    #     frappe.throw(_("Customer is a mandatory filter."))

    gl_filters = frappe._dict({
        "company": company,
        "party_type": "Customer",
        "party": customer,
        "from_date": from_date,
        "to_date": to_date,
        "group_by": "Group by Voucher (Consolidated)",
        "show_opening_entries": 1,
        "show_cancelled_entries": 0
    })

    gl_columns, gl_data = gl_execute(gl_filters)

    columns = get_columns()

    transformed_data, total_discount_si, total_discount_pe, opening_discount_total, opening_payment_discount_total = transform_data_with_balance(gl_data, from_date, customer)
    data = group_by_item_group(transformed_data, total_discount_si, total_discount_pe, opening_discount_total, opening_payment_discount_total, include_si_discounts=INCLUDE_SI_DISCOUNTS)
    return columns, data
    
def get_columns():
    return [
        # {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        # {"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 120},
        # {"label": _("Voucher No"), "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 150},
        {"label": _("Account"), "fieldname": "account", "fieldtype": "Link", "options": "Account", "width": 200},
        # {"label": _("Party"), "fieldname": "party", "fieldtype": "Link", "options": "Customer", "width": 120},
        # {"label": _("Against"), "fieldname": "against", "fieldtype": "Data", "width": 120},
        # {"label": _("Items"), "fieldname": "items", "fieldtype": "Data", "width": 200},  # New column
        {"label": _("Item Groups"), "fieldname": "item_groups", "fieldtype": "Data", "width": 180},  # New column
        {"label": _("Income Accounts"), "fieldname": "income_accounts", "fieldtype": "Data", "width": 180},  # New column
        {"label": _("Debit"), "fieldname": "debit", "fieldtype": "Currency", "width": 100},
        {"label": _("Credit"), "fieldname": "credit", "fieldtype": "Currency", "width": 100},
        {"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "width": 100},
        {"label": _("Discounts Made"), "fieldname": "discount_made", "fieldtype": "Currency", "width": 120},
    ]


def m2(v):
    # money to 2 decimals (always)
    return flt(v or 0, 2)
	
def group_by_item_group(data, total_discount_si, total_discount_pe, opening_discount_total, opening_payment_discount_total,include_si_discounts=True,):
    
    grouped = defaultdict(lambda: {"debit": 0.0, "credit": 0.0, "discount_made": 0.0})
    opening_rows = []
    grouped_rows = []
    ending_rows = []


    for row in data:
        account = (row.get("account") or "").strip().strip("'").strip('"')
        voucher_no = (row.get("voucher_no") or "").strip().strip("'").strip('"')
        voucher_type = row.get("voucher_type") or ""

        # if account == "Opening" or voucher_no == "Opening":
        #     row["balance"] = row.get("debit", 0.0) - row.get("credit", 0.0)
        #     row["discount_made"] = opening_discount_total + opening_payment_discount_total
        #     opening_rows.append(row)
        #     continue

        # elif account == "Total":
        #     row["balance"] = row.get("debit", 0.0) - row.get("credit", 0.0)
        #     row["discount_made"] = total_discount_si + total_discount_pe
        #     ending_rows.append(row)
        #     continue

        # elif account == "Closing (Opening + Total)":
        #     row["balance"] = row.get("debit", 0.0) - row.get("credit", 0.0)
        #     row["discount_made"] = opening_discount_total + total_discount_pe + total_discount_si + opening_payment_discount_total
        #     ending_rows.append(row)
        #     continue

        if account == "Opening" or voucher_no == "Opening":
            row["balance"] = round(row.get("debit", 0.0), 2) - round(row.get("credit", 0.0),2)
            # Only include SI discounts if enabled
            row["discount_made"] = (
                opening_discount_total + opening_payment_discount_total
                if include_si_discounts
                else opening_payment_discount_total
            )
            opening_rows.append(row)
            continue

        elif account == "Total":
            row["balance"] = round(row.get("debit", 0.0), 2) - round(row.get("credit", 0.0), 2)
            row["discount_made"] = (
                total_discount_si + total_discount_pe
                if include_si_discounts
                else total_discount_pe
            )
            ending_rows.append(row)
            continue

        elif account == "Closing (Opening + Total)":
            row["balance"] = round(row.get("debit", 0.0), 2) - round(row.get("credit", 0.0), 2)
            row["discount_made"] = (
                opening_discount_total + total_discount_pe + total_discount_si + opening_payment_discount_total
                if include_si_discounts
                else opening_payment_discount_total + total_discount_pe
            )
            ending_rows.append(row)
            continue


        item_group = row.get("item_groups")
        income_account = row.get("income_accounts")

        if not item_group:
            item_group = (
                "Unallocated Journal" if voucher_type == "Journal Entry"
                else "Unallocated Payment" if voucher_type == "Payment Entry"
                else "Unallocated"
            )

        if not income_account:
            income_account = (
                "Unallocated Journal" if voucher_type == "Journal Entry"
                else "Unallocated Payment" if voucher_type == "Payment Entry"
                else "Unallocated"
            )

        key = (item_group, income_account)

        grouped[key]["debit"] += row.get("debit", 0.0)
        grouped[key]["credit"] += row.get("credit", 0.0)
        # if voucher_type == "Sales Invoice":
        #     grouped[key]["discount_made"] += row.get("discount_made", 0.0)

        # Only aggregate SI discounts into the group if flag is on
        if voucher_type == "Sales Invoice" and include_si_discounts:
            grouped[key]["discount_made"] += row.get("discount_made", 0.0)



    for (item_group, income_account), totals in grouped.items():
        balance = round(totals["debit"], 2) - round(totals["credit"], 2)
        grouped_rows.append({
            "posting_date": "",
            "voucher_type": "",
            "voucher_no": "",
            "account": "",
            "party": "",
            "against": "",
            "items": "",
            "item_groups": item_group,
            "income_accounts": income_account,
            "debit": totals["debit"],
            "credit": totals["credit"],
            "balance": balance,
            "discount_made": totals["discount_made"]
        })

    # Add PE discount summary row
    discount_rows = [
        {
            "account": "",
            "item_groups": "Payment Entry Discount Made",
            "income_accounts": "",
            "debit": 0.0,
            "credit": 0.0,
            "discount_made": total_discount_pe,
            "balance": 0.0
        }
    ]


    return opening_rows + grouped_rows + discount_rows + ending_rows


def get_sales_invoice_items(voucher_no):
    items = frappe.db.get_all(
        "Sales Invoice Item",
        filters={"parent": voucher_no},
        fields=["item_name", "item_group", "income_account"],
        order_by="idx asc"
    )
    item_names = [d.item_name for d in items]
    item_groups = list({d.item_group for d in items if d.item_group})  # Deduplicated
    income_accounts = list({d.income_account for d in items if d.income_account})  # Deduplicated
    return ", ".join(item_names), ", ".join(item_groups), ", ".join(income_accounts)

def get_payment_entry_invoice_data(payment_entry):
    # First check if Payment Entry directly references Sales Invoices
    references = frappe.db.get_all(
        "Payment Entry Reference",
        filters={"parent": payment_entry, "reference_doctype": "Sales Invoice"},
        fields=["reference_name"]
    )

    item_names = set()
    item_groups = set()
    income_accounts = set()

    # Handle direct Sales Invoice references in Payment Entry
    for ref in references:
        invoice = ref.reference_name
        items = frappe.db.get_all(
            "Sales Invoice Item",
            filters={"parent": invoice},
            fields=["item_name", "item_group", "income_account"]
        )
        for item in items:
            if item.item_name:
                item_names.add(item.item_name)
            if item.item_group:
                item_groups.add(item.item_group)
            if item.income_account:
                income_accounts.add(item.income_account)

    # Now also check if Payment Entry references Journal Entries
    journal_entries = frappe.db.get_all(
        "Payment Entry Reference",
        filters={"parent": payment_entry, "reference_doctype": "Journal Entry"},
        fields=["reference_name"]
    )

    # For each Journal Entry, fetch the Sales Invoices it references
    for journal_ref in journal_entries:
        journal_entry = journal_ref.reference_name
        invoice = (
            frappe.db.get_value("Journal Entry", journal_entry, "sales_invoice")
            or frappe.db.get_value("Journal Entry", journal_entry, "reference_invoice")
        )

        if invoice:
            # Get item details from the referenced Sales Invoice
            items = frappe.db.get_all(
                "Sales Invoice Item",
                filters={"parent": invoice},
                fields=["item_name", "item_group", "income_account"]
            )
            for item in items:
                if item.item_name:
                    item_names.add(item.item_name)
                if item.item_group:
                    item_groups.add(item.item_group)
                if item.income_account:
                    income_accounts.add(item.income_account)

    return ", ".join(item_names), ", ".join(item_groups), ", ".join(income_accounts)


def get_invoice_from_journal_entry(journal_entry):
    return (
        frappe.db.get_value("Journal Entry", journal_entry, "sales_invoice") or
        frappe.db.get_value("Journal Entry", journal_entry, "reference_invoice")
    )

def get_journal_entry_invoice_data(journal_entry):
    invoice = get_invoice_from_journal_entry(journal_entry)
    if not invoice:
        return "", "", ""

    items = frappe.db.get_all(
        "Sales Invoice Item",
        filters={"parent": invoice},
        fields=["item_name", "item_group", "income_account"]
    )

    item_names = {d.item_name for d in items if d.item_name}
    item_groups = {d.item_group for d in items if d.item_group}
    income_accounts = {d.income_account for d in items if d.income_account}

    return ", ".join(item_names), ", ".join(item_groups), ", ".join(income_accounts)


def transform_data_with_balance(gl_data, from_date, customer):
    # Convert from_date to date object if it's a string
    if isinstance(from_date, str):
        from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
    # If it's a list, use the first item
    if isinstance(customer, list):
        customer = customer[0] if customer else None

    data = []
    running_balance = 0.0
    total_discount_si = 0.0
    total_discount_pe = 0.0

    # STEP 1: Collect all relevant voucher numbers
    sales_invoices = set()
    payment_entries = set()
    journal_entries = set()

    for row in gl_data:
        voucher_type = row.get("voucher_type")
        voucher_no = row.get("voucher_no")

        # Ensure posting_date is a datetime.date
        posting_date = row.get("posting_date")
        if isinstance(posting_date, str):
            posting_date = datetime.strptime(posting_date, "%Y-%m-%d").date()
            row["posting_date"] = posting_date

        if voucher_type == "Sales Invoice":
            sales_invoices.add(voucher_no)
        elif voucher_type == "Payment Entry":
            payment_entries.add(voucher_no)
        elif voucher_type == "Journal Entry":
            journal_entries.add(voucher_no)



    opening_sales_invoices = frappe.db.get_all(
        "Sales Invoice",
        filters={
            "posting_date": ["<", from_date],
            "customer": customer,
            "docstatus": 1,
        },
        fields=["name", "discount_amount"]
    )

    if opening_sales_invoices:
        opening_si_vouchers = {inv.name for inv in opening_sales_invoices}
        opening_discount_total = sum(inv.discount_amount for inv in opening_sales_invoices)
    else:
        opening_si_vouchers = set()
        opening_discount_total = 0.0


    opening_discount_total = sum(
        d.discount_amount
        for d in frappe.db.get_all(
            "Sales Invoice",
            filters={"name": ["in", list(opening_si_vouchers)]},
            fields=["name", "discount_amount"]
        )
    )


    opening_payment_deductions = frappe.db.get_all(
        "Payment Entry Deduction",
        filters={
            "parent": ["in", frappe.db.get_all(
                "Payment Entry",
                filters={
                    "posting_date": ["<", from_date],
                    "party_type": "Customer",
                    "party": customer,
                    "docstatus": 1
                },
                pluck="name"
            )]
        },
        fields=["amount"]
    )

    opening_payment_discount_total = sum(d.amount for d in opening_payment_deductions)

    # STEP 2: Batch fetch related data
    invoice_items = frappe.db.get_all(
        "Sales Invoice Item",
        filters={"parent": ["in", list(sales_invoices)]},
        fields=["parent", "item_name", "item_group", "income_account", "base_net_amount"]
    )

    invoice_discount_map = {
        d.name: d.discount_amount
        for d in frappe.db.get_all(
            "Sales Invoice",
            filters={"name": ["in", list(sales_invoices)]},
            fields=["name", "discount_amount"]
        )
    }

    payment_refs = frappe.db.get_all(
        "Payment Entry Reference",
        filters={"parent": ["in", list(payment_entries)]},
        fields=["parent", "reference_doctype", "reference_name"]
    )

    pe_deductions = frappe.db.get_all(
        "Payment Entry Deduction",
        filters={"parent": ["in", list(payment_entries)]},
        fields=["parent", "amount"]
    )

    journal_invoice_map = {
        d.name: (d.sales_invoice or d.reference_invoice)
        for d in frappe.db.get_all(
            "Journal Entry",
            filters={"name": ["in", list(journal_entries)]},
            fields=["name", "sales_invoice", "reference_invoice"]
        )
    }

    # STEP 3: Build in-memory lookup maps
    invoice_item_map = defaultdict(list)
    for item in invoice_items:
        invoice_item_map[item["parent"]].append(item)

    payment_ref_map = defaultdict(list)
    for ref in payment_refs:
        payment_ref_map[ref["parent"]].append(ref)

    pe_deduction_map = defaultdict(float)
    for ded in pe_deductions:
        pe_deduction_map[ded["parent"]] += flt(ded["amount"])

    # STEP 4: Process GL rows
    for row in gl_data:

        
        voucher_type = row.get("voucher_type")
        voucher_no = row.get("voucher_no")
        account = (row.get("account") or "").strip().strip("'").strip('"')

        if account == "Opening":
            opening_debit = flt(row.get("debit", 0))
            opening_credit = flt(row.get("credit", 0))
            running_balance = opening_debit - opening_credit
            # opening_debit = sum(flt(r['debit']) for r in gl_data if r.get('posting_date') and r['posting_date'] < from_date)
            # opening_credit = sum(flt(r['credit']) for r in gl_data if r.get('posting_date') and r['posting_date'] < from_date)
            # running_balance = opening_debit - opening_credit
            data.append({
                "posting_date": "",
                "voucher_type": "",
                "voucher_no": "Opening",
                "account": "Opening",
                "party": "",
                "against": "",
                "items": "",
                "item_groups": "",
                "income_accounts": "",
                "debit": opening_debit,
                "credit": opening_credit,
                "balance": running_balance,
                # "discount_made": opening_discount_total + opening_payment_discount_total
                "discount_made": (
                    opening_discount_total + opening_payment_discount_total
                    if INCLUDE_SI_DISCOUNTS
                    else opening_payment_discount_total
                )
            })
            continue

        debit = flt(row.get("debit", 0))
        credit = flt(row.get("credit", 0))
        item_rows = []
        discount_amount_si = 0.0
        discount_amount_pe = 0.0
        total_amount = 0.0
        proportions = []
        debit_splits = []
        credit_splits = []
        discount_splits = []

        if voucher_type == "Sales Invoice" and voucher_no:
            item_rows = invoice_item_map.get(voucher_no, [{}])

            if INCLUDE_SI_DISCOUNTS:
                discount_amount_si = invoice_discount_map.get(voucher_no, 0.0)
                total_discount_si += discount_amount_si
            else:
                discount_amount_si = 0.0

            total_amount = sum(flt(i.get("base_net_amount")) for i in item_rows if i.get("base_net_amount"))

            proportions = [flt(i.get("base_net_amount")) / total_amount if total_amount else 0 for i in item_rows]
            debit_splits = [round(debit * p, 2) for p in proportions]
            credit_splits = [round(credit * p, 2) for p in proportions]

            if INCLUDE_SI_DISCOUNTS:
                discount_splits = [round(discount_amount_si * p, 2) for p in proportions]
            else:
                discount_splits = [0.0 for _ in proportions]

            if debit:
                debit_splits[-1] += round(debit - sum(debit_splits), 2)
            if credit:
                credit_splits[-1] += round(credit - sum(credit_splits), 2)
            if INCLUDE_SI_DISCOUNTS and discount_amount_si:
                discount_splits[-1] += round(discount_amount_si - sum(discount_splits), 2)


        # if voucher_type == "Sales Invoice" and voucher_no:
        #     item_rows = invoice_item_map.get(voucher_no, [{}])
        #     discount_amount_si = invoice_discount_map.get(voucher_no, 0.0)
        #     total_discount_si += discount_amount_si
        #     total_amount = sum(flt(i.get("base_net_amount")) for i in item_rows if i.get("base_net_amount"))

        #     proportions = [flt(i.get("base_net_amount")) / total_amount if total_amount else 0 for i in item_rows]
        #     debit_splits = [round(debit * p, 2) for p in proportions]
        #     credit_splits = [round(credit * p, 2) for p in proportions]
        #     discount_splits = [round(discount_amount_si * p, 2) for p in proportions]

        #     if debit:
        #         debit_splits[-1] += round(debit - sum(debit_splits), 2)
        #     if credit:
        #         credit_splits[-1] += round(credit - sum(credit_splits), 2)
        #     if discount_amount_si:
        #         discount_splits[-1] += round(discount_amount_si - sum(discount_splits), 2)

        elif voucher_type == "Payment Entry" and voucher_no:
            items = []
            for ref in payment_ref_map.get(voucher_no, []):
                if ref["reference_doctype"] == "Sales Invoice":
                    items += invoice_item_map.get(ref["reference_name"], [])
                elif ref["reference_doctype"] == "Journal Entry":
                    inv = journal_invoice_map.get(ref["reference_name"])
                    if inv:
                        items += invoice_item_map.get(inv, [])
            item_rows = items or [{}]
            discount_amount_pe = pe_deduction_map.get(voucher_no, 0.0)
            total_discount_pe += discount_amount_pe

            total_amount = sum(flt(i.get("base_net_amount")) for i in item_rows if i.get("base_net_amount"))
            proportions = [flt(i.get("base_net_amount")) / total_amount if total_amount else 0 for i in item_rows]
            debit_splits = [round(debit * p, 2) for p in proportions]
            credit_splits = [round(credit * p, 2) for p in proportions]

            if debit:
                debit_splits[-1] += round(debit - sum(debit_splits), 2)
            if credit:
                credit_splits[-1] += round(credit - sum(credit_splits), 2)

        elif voucher_type == "Journal Entry" and voucher_no:
            invoice = journal_invoice_map.get(voucher_no)
            item_rows = invoice_item_map.get(invoice, [{}]) if invoice else [{}]
            total_amount = sum(flt(i.get("base_net_amount")) for i in item_rows if i.get("base_net_amount"))
            proportions = [flt(i.get("base_net_amount")) / total_amount if total_amount else 0 for i in item_rows]
            debit_splits = [round(debit * p, 2) for p in proportions]
            credit_splits = [round(credit * p, 2) for p in proportions]

            if debit:
                debit_splits[-1] += round(debit - sum(debit_splits), 2)
            if credit:
                credit_splits[-1] += round(credit - sum(credit_splits), 2)

        if not item_rows:
            item_rows = [{}]

        running_balance += debit - credit

        for idx, item in enumerate(item_rows):
            discount_value = 0.0
            row_debit = 0.0
            row_credit = 0.0

            if voucher_type == "Sales Invoice":
                # discount_value = discount_splits[idx]
                discount_value = discount_splits[idx] if INCLUDE_SI_DISCOUNTS else 0.0
                row_debit = debit_splits[idx]
                row_credit = credit_splits[idx]
            elif voucher_type == "Payment Entry":
                discount_value = discount_amount_pe if idx == 0 else 0.0
                row_debit = debit_splits[idx] if idx < len(debit_splits) else 0.0
                row_credit = credit_splits[idx] if idx < len(credit_splits) else 0.0
            elif voucher_type == "Journal Entry":
                row_debit = debit_splits[idx] if idx < len(debit_splits) else 0.0
                row_credit = credit_splits[idx] if idx < len(credit_splits) else 0.0
            elif idx == 0:
                row_debit = debit
                row_credit = credit

            data.append({
                "posting_date": row.get("posting_date"),
                "voucher_type": voucher_type,
                "voucher_no": voucher_no,
                "account": row.get("account"),
                "party": row.get("party"),
                "against": row.get("against"),
                "items": item.get("item_name", ""),
                "item_groups": item.get("item_group", ""),
                "income_accounts": item.get("income_account", ""),
                "debit": row_debit,
                "credit": row_credit,
                "balance": running_balance if idx == 0 else "",
                "discount_made": discount_value
            })
  
    return data, total_discount_si, total_discount_pe, opening_discount_total, opening_payment_discount_total

