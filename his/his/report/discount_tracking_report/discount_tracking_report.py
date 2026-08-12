# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


HIS_SETTINGS = "HIS Settings"

IGNORE_CHILD_TABLE_FIELD = "discount_ignore_item_groups"
IGNORE_ITEM_GROUP_FIELD = "item_group"


def execute(filters=None):
    filters = frappe._dict(filters or {})

    raw_data = []
    voucher_type = filters.get("voucher_type") or "All"

    if voucher_type in ("All", "Payment Entry"):
        raw_data.extend(get_payment_entry_discounts(filters))

    # Enable later if needed
    # if voucher_type in ("All", "Sales Invoice"):
    #     raw_data.extend(get_sales_invoice_discounts(filters))

    if voucher_type in ("All", "Journal Entry"):
        raw_data.extend(get_journal_entry_discounts(filters))

    # IMPORTANT FIX:
    # First calculate all groups including ignored groups.
    # Then remove ignored groups and redistribute their discount.
    raw_data = redistribute_ignored_item_group_discounts(raw_data, filters)

    view_type = filters.get("view_type") or "Management Summary"

    if view_type == "Detail":
        columns = get_detail_columns()
        data = raw_data

    elif view_type == "Item Wise":
        columns = get_item_wise_columns()
        data = build_summary(
            raw_data,
            group_fields=["item_code", "item_name", "item_group", "source", "discount_account"]
        )

    elif view_type == "Item Group Summary":
        columns = get_item_group_summary_columns()
        data = build_summary(
            raw_data,
            group_fields=["item_group", "source", "discount_account"]
        )

    else:
        columns = get_management_summary_columns()
        data = build_summary(
            raw_data,
            group_fields=["source", "discount_account"]
        )

    chart = get_chart(raw_data, filters)
    report_summary = get_report_summary(raw_data)

    return columns, data, None, chart, report_summary


# ---------------------------------------------------------------------
# COLUMNS
# ---------------------------------------------------------------------

def get_management_summary_columns():
    return [
        {"label": "Source", "fieldname": "source", "fieldtype": "Data", "width": 150},
        {"label": "Discount Account", "fieldname": "discount_account", "fieldtype": "Link", "options": "Account", "width": 220},
        {"label": "Voucher Count", "fieldname": "voucher_count", "fieldtype": "Int", "width": 120},
        {"label": "Invoice Count", "fieldname": "invoice_count", "fieldtype": "Int", "width": 120},
        {"label": "Customer Count", "fieldname": "customer_count", "fieldtype": "Int", "width": 130},
        {"label": "Eligible Amount", "fieldname": "eligible_amount", "fieldtype": "Currency", "width": 150},
        {"label": "Discount Amount", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 160},
    ]


def get_item_group_summary_columns():
    return [
        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 180},
        {"label": "Source", "fieldname": "source", "fieldtype": "Data", "width": 140},
        {"label": "Discount Account", "fieldname": "discount_account", "fieldtype": "Link", "options": "Account", "width": 200},
        {"label": "Voucher Count", "fieldname": "voucher_count", "fieldtype": "Int", "width": 120},
        {"label": "Invoice Count", "fieldname": "invoice_count", "fieldtype": "Int", "width": 120},
        {"label": "Customer Count", "fieldname": "customer_count", "fieldtype": "Int", "width": 130},
        {"label": "Eligible Amount", "fieldname": "eligible_amount", "fieldtype": "Currency", "width": 150},
        {"label": "Discount Amount", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 160},
    ]


def get_item_wise_columns():
    return [
        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 170},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 220},
        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 160},
        {"label": "Source", "fieldname": "source", "fieldtype": "Data", "width": 140},
        {"label": "Discount Account", "fieldname": "discount_account", "fieldtype": "Link", "options": "Account", "width": 200},
        {"label": "Voucher Count", "fieldname": "voucher_count", "fieldtype": "Int", "width": 120},
        {"label": "Invoice Count", "fieldname": "invoice_count", "fieldtype": "Int", "width": 120},
        {"label": "Customer Count", "fieldname": "customer_count", "fieldtype": "Int", "width": 130},
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 100},
        {"label": "Eligible Amount", "fieldname": "eligible_amount", "fieldtype": "Currency", "width": 150},
        {"label": "Discount Amount", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 160},
    ]


def get_detail_columns():
    return [
        {"label": "Source", "fieldname": "source", "fieldtype": "Data", "width": 130},
        {"label": "Voucher Type", "fieldname": "voucher_type", "fieldtype": "Data", "width": 130},
        {"label": "Voucher", "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 180},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
        {"label": "Sales Invoice", "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 180},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 160},
        {"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 190},
        {"label": "Customer Group", "fieldname": "customer_group", "fieldtype": "Link", "options": "Customer Group", "width": 150},
        {"label": "Patient", "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 140},
        {"label": "Patient Name", "fieldname": "patient_name", "fieldtype": "Data", "width": 180},
        {"label": "Doctor", "fieldname": "doctor", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 180},
        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 160},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 220},
        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 150},
        {"label": "Discount Account", "fieldname": "discount_account", "fieldtype": "Link", "options": "Account", "width": 190},
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 90},
        {"label": "Invoice Net Amount", "fieldname": "invoice_net_amount", "fieldtype": "Currency", "width": 150},
        {"label": "Eligible Amount", "fieldname": "eligible_amount", "fieldtype": "Currency", "width": 150},
        {"label": "Discount Amount", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 150},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120},
        {"label": "Remarks", "fieldname": "remarks", "fieldtype": "Data", "width": 300},
    ]


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def get_ignored_item_groups():
    ignored = set()

    if not frappe.db.exists(HIS_SETTINGS, HIS_SETTINGS):
        return ignored

    settings = frappe.get_doc(HIS_SETTINGS, HIS_SETTINGS)

    for row in settings.get(IGNORE_CHILD_TABLE_FIELD) or []:
        item_group = row.get(IGNORE_ITEM_GROUP_FIELD)
        if item_group:
            ignored.add(item_group)

    return ignored


def get_invoice_doc(name):
    try:
        return frappe.get_doc("Sales Invoice", name)
    except Exception:
        return None


def get_invoice_doctor(si):
    return si.get("ref_practitioner") or si.get("practitioner")


def passes_common_invoice_filters(si, filters):
    if filters.get("customer") and si.customer != filters.customer:
        return False

    if filters.get("customer_group") and si.customer_group != filters.customer_group:
        return False

    if filters.get("patient") and si.get("patient") != filters.patient:
        return False

    if filters.get("doctor") and get_invoice_doctor(si) != filters.doctor:
        return False

    return True


def make_invoice_context(si):
    return {
        "sales_invoice": si.name,
        "customer": si.customer,
        "customer_name": si.customer_name,
        "customer_group": si.customer_group,
        "patient": si.get("patient"),
        "patient_name": si.get("patient_name"),
        "doctor": get_invoice_doctor(si),
    }


def get_invoice_items(si):
    items = []

    for item in si.items:
        if not item.item_group:
            continue

        net_amount = flt(item.net_amount)
        if not net_amount:
            continue

        items.append({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_group": item.item_group,
            "qty": flt(item.qty),
            "net_amount": net_amount,
            "gross_amount": flt(item.amount),
            "discount_amount": flt(item.amount) - flt(item.net_amount),
        })

    return items


# ---------------------------------------------------------------------
# PAYMENT ENTRY
# ---------------------------------------------------------------------

def get_payment_entry_discounts(filters):
    data = []

    conditions = [
        "pe.docstatus = 1",
        "pe.posting_date between %(from_date)s and %(to_date)s"
    ]

    if filters.get("company"):
        conditions.append("pe.company = %(company)s")

    if filters.get("discount_account"):
        conditions.append("ded.account = %(discount_account)s")

    payment_entries = frappe.db.sql(f"""
        select
            pe.name,
            pe.posting_date,
            pe.company,
            ded.account,
            ded.amount,
            ded.cost_center
        from `tabPayment Entry` pe
        inner join `tabPayment Entry Deduction` ded
            on ded.parent = pe.name
        where {" and ".join(conditions)}
        order by pe.posting_date, pe.name
    """, filters, as_dict=True)

    for pe in payment_entries:
        references = frappe.db.sql("""
            select
                reference_doctype,
                reference_name,
                allocated_amount
            from `tabPayment Entry Reference`
            where parent = %s
              and reference_doctype = 'Sales Invoice'
              and allocated_amount > 0
        """, pe.name, as_dict=True)

        if not references:
            if filters.get("show_unallocated_payment_entries"):
                data.append({
                    "source": "Payment Entry",
                    "voucher_type": "Payment Entry",
                    "voucher_no": pe.name,
                    "posting_date": pe.posting_date,
                    "discount_account": pe.account,
                    "eligible_amount": 0,
                    "discount_amount": flt(pe.amount),
                    "status": "Unallocated",
                    "remarks": "Payment deduction exists but no Sales Invoice allocation found"
                })
            continue

        total_allocated = sum(flt(r.allocated_amount) for r in references)

        if not total_allocated:
            continue

        for ref in references:
            si = get_invoice_doc(ref.reference_name)
            if not si:
                continue

            if not passes_common_invoice_filters(si, filters):
                continue

            invoice_items = get_invoice_items(si)
            invoice_total = sum(flt(i["net_amount"]) for i in invoice_items)

            if not invoice_total:
                continue

            invoice_share_discount = flt(pe.amount) * flt(ref.allocated_amount) / total_allocated
            ctx = make_invoice_context(si)

            for item in invoice_items:
                discount_amount = invoice_share_discount * flt(item["net_amount"]) / invoice_total

                row = {
                    "source": "Payment Entry",
                    "voucher_type": "Payment Entry",
                    "voucher_no": pe.name,
                    "posting_date": pe.posting_date,
                    "item_code": item["item_code"],
                    "item_name": item["item_name"],
                    "item_group": item["item_group"],
                    "qty": item["qty"],
                    "discount_account": pe.account,
                    "invoice_net_amount": flt(si.net_total),
                    "eligible_amount": flt(item["net_amount"]),
                    "discount_amount": discount_amount,
                    "status": "Allocated",
                    "remarks": "Payment deduction allocated normally. Ignored item groups redistributed after full calculation."
                }

                row.update(ctx)
                data.append(row)

    return data


# ---------------------------------------------------------------------
# SALES INVOICE
# ---------------------------------------------------------------------

def get_sales_invoice_discounts(filters):
    data = []

    conditions = [
        "docstatus = 1",
        "posting_date between %(from_date)s and %(to_date)s"
    ]

    if filters.get("company"):
        conditions.append("company = %(company)s")

    if filters.get("customer"):
        conditions.append("customer = %(customer)s")

    if filters.get("customer_group"):
        conditions.append("customer_group = %(customer_group)s")

    if filters.get("patient"):
        conditions.append("patient = %(patient)s")

    if filters.get("doctor"):
        conditions.append("(ref_practitioner = %(doctor)s or practitioner = %(doctor)s)")

    invoices = frappe.db.sql(f"""
        select name
        from `tabSales Invoice`
        where {" and ".join(conditions)}
        order by posting_date, name
    """, filters, as_dict=True)

    for row in invoices:
        si = get_invoice_doc(row.name)
        if not si:
            continue

        invoice_items = get_invoice_items(si)
        invoice_total = sum(flt(i["net_amount"]) for i in invoice_items)

        if not invoice_total:
            continue

        ctx = make_invoice_context(si)
        additional_discount = flt(si.discount_amount)

        for item in invoice_items:
            item_level_discount = flt(item["discount_amount"])

            additional_share = 0
            if additional_discount:
                additional_share = additional_discount * flt(item["net_amount"]) / invoice_total

            total_discount = item_level_discount + additional_share

            if total_discount <= 0:
                continue

            report_row = {
                "source": "Sales Invoice",
                "voucher_type": "Sales Invoice",
                "voucher_no": si.name,
                "posting_date": si.posting_date,
                "sales_invoice": si.name,
                "item_code": item["item_code"],
                "item_name": item["item_name"],
                "item_group": item["item_group"],
                "qty": item["qty"],
                "invoice_net_amount": flt(si.net_total),
                "eligible_amount": flt(item["net_amount"]),
                "discount_amount": total_discount,
                "status": "Submitted",
                "remarks": "Sales Invoice discount allocated normally. Ignored item groups redistributed after full calculation."
            }

            report_row.update(ctx)
            data.append(report_row)

    return data


# ---------------------------------------------------------------------
# JOURNAL ENTRY
# ---------------------------------------------------------------------

def get_journal_entry_discounts(filters):
    data = []

    if (
        filters.get("item_group")
        or filters.get("item_code")
        or filters.get("patient")
        or filters.get("doctor")
        or filters.get("customer_group")
    ):
        return data

    conditions = [
        "je.docstatus = 1",
        "je.posting_date between %(from_date)s and %(to_date)s"
    ]

    if filters.get("company"):
        conditions.append("je.company = %(company)s")

    if filters.get("discount_account"):
        conditions.append("jea.account = %(discount_account)s")

    if filters.get("customer"):
        conditions.append("jea.party_type = 'Customer'")
        conditions.append("jea.party = %(customer)s")

    rows = frappe.db.sql(f"""
        select
            je.name,
            je.posting_date,
            je.company,
            je.user_remark,
            jea.account,
            jea.party_type,
            jea.party,
            jea.party_name,
            jea.debit,
            jea.credit,
            jea.user_remark as row_remark
        from `tabJournal Entry` je
        inner join `tabJournal Entry Account` jea
            on jea.parent = je.name
        where {" and ".join(conditions)}
        order by je.posting_date, je.name
    """, filters, as_dict=True)

    for r in rows:
        amount = flt(r.debit) or flt(r.credit)

        if not amount:
            continue

        data.append({
            "source": "Journal Entry",
            "voucher_type": "Journal Entry",
            "voucher_no": r.name,
            "posting_date": r.posting_date,
            "customer": r.party if r.party_type == "Customer" else None,
            "customer_name": r.party_name if r.party_type == "Customer" else None,
            "discount_account": r.account,
            "eligible_amount": 0,
            "discount_amount": amount,
            "status": "Submitted",
            "remarks": r.row_remark or r.user_remark or "Journal Entry discount row. No item-wise allocation available."
        })

    return data


# ---------------------------------------------------------------------
# REDISTRIBUTION
# ---------------------------------------------------------------------

def redistribute_ignored_item_group_discounts(raw_data, filters):
    ignored_item_groups = get_ignored_item_groups()

    if not ignored_item_groups:
        return apply_item_filters(raw_data, filters)

    kept_rows = []
    ignored_discount_by_key = {}
    kept_base_by_key = {}

    for row in raw_data:
        source = row.get("source") or "Not Set"
        account = row.get("discount_account") or "Not Set"
        key = (source, account)

        item_group = row.get("item_group")

        if item_group and item_group in ignored_item_groups:
            ignored_discount_by_key[key] = ignored_discount_by_key.get(key, 0) + flt(row.get("discount_amount"))
            continue

        kept_rows.append(row)

        # Journal/unallocated rows have no item group; keep them but do not use them as redistribution base
        if item_group:
            kept_base_by_key[key] = kept_base_by_key.get(key, 0) + flt(row.get("eligible_amount"))

    for row in kept_rows:
        item_group = row.get("item_group")
        if not item_group:
            continue

        source = row.get("source") or "Not Set"
        account = row.get("discount_account") or "Not Set"
        key = (source, account)

        ignored_discount = ignored_discount_by_key.get(key, 0)
        kept_base = kept_base_by_key.get(key, 0)

        if ignored_discount and kept_base:
            extra = ignored_discount * flt(row.get("eligible_amount")) / kept_base
            row["discount_amount"] = flt(row.get("discount_amount")) + extra
            row["remarks"] = (row.get("remarks") or "") + " | Ignored item group discount redistributed."

    return apply_item_filters(kept_rows, filters)


def apply_item_filters(rows, filters):
    final_rows = []

    for row in rows:
        if filters.get("item_group") and row.get("item_group") != filters.get("item_group"):
            continue

        if filters.get("item_code") and row.get("item_code") != filters.get("item_code"):
            continue

        final_rows.append(row)

    return final_rows


# ---------------------------------------------------------------------
# SUMMARY / CHART
# ---------------------------------------------------------------------

def build_summary(raw_data, group_fields):
    grouped = {}

    for row in raw_data:
        key = tuple(row.get(field) or "Not Set" for field in group_fields)

        if key not in grouped:
            grouped[key] = {}

            for idx, field in enumerate(group_fields):
                grouped[key][field] = key[idx]

            grouped[key]["voucher_count_set"] = set()
            grouped[key]["invoice_count_set"] = set()
            grouped[key]["customer_count_set"] = set()
            grouped[key]["qty"] = 0
            grouped[key]["eligible_amount"] = 0
            grouped[key]["discount_amount"] = 0

        if row.get("voucher_no"):
            grouped[key]["voucher_count_set"].add(row.get("voucher_no"))

        if row.get("sales_invoice"):
            grouped[key]["invoice_count_set"].add(row.get("sales_invoice"))

        if row.get("customer"):
            grouped[key]["customer_count_set"].add(row.get("customer"))

        grouped[key]["qty"] += flt(row.get("qty"))
        grouped[key]["eligible_amount"] += flt(row.get("eligible_amount"))
        grouped[key]["discount_amount"] += flt(row.get("discount_amount"))

    result = []

    for row in grouped.values():
        row["voucher_count"] = len(row.pop("voucher_count_set"))
        row["invoice_count"] = len(row.pop("invoice_count_set"))
        row["customer_count"] = len(row.pop("customer_count_set"))
        result.append(row)

    result.sort(key=lambda x: flt(x.get("discount_amount")), reverse=True)

    return result


def get_chart(raw_data, filters):
    chart_by = filters.get("chart_by") or "Item Group"

    field_map = {
        "Item Group": "item_group",
        "Item": "item_name",
        "Source": "source",
        "Customer Group": "customer_group",
        "Doctor": "doctor",
    }

    group_field = field_map.get(chart_by, "item_group")
    grouped = {}

    for row in raw_data:
        label = row.get(group_field) or "Not Set"
        grouped[label] = grouped.get(label, 0) + flt(row.get("discount_amount"))

    rows = sorted(grouped.items(), key=lambda x: x[1], reverse=True)[:10]

    if not rows:
        return None

    return {
        "data": {
            "labels": [r[0] for r in rows],
            "datasets": [
                {
                    "name": "Discount Amount",
                    "values": [flt(r[1], 2) for r in rows]
                }
            ]
        },
        "type": "bar",
        "height": 280,
        "colors": ["#5e64ff"]
    }


def get_report_summary(raw_data):
    total_discount = sum(flt(r.get("discount_amount")) for r in raw_data)
    total_eligible = sum(flt(r.get("eligible_amount")) for r in raw_data)

    vouchers = set()
    invoices = set()
    customers = set()
    unallocated = 0

    for row in raw_data:
        if row.get("voucher_no"):
            vouchers.add(row.get("voucher_no"))

        if row.get("sales_invoice"):
            invoices.add(row.get("sales_invoice"))

        if row.get("customer"):
            customers.add(row.get("customer"))

        if row.get("status") == "Unallocated":
            unallocated += flt(row.get("discount_amount"))

    return [
        {"value": total_discount, "label": "Total Discount", "datatype": "Currency", "indicator": "Red"},
        {"value": total_eligible, "label": "Eligible Amount", "datatype": "Currency", "indicator": "Blue"},
        {"value": len(vouchers), "label": "Vouchers", "datatype": "Int", "indicator": "Green"},
        {"value": len(invoices), "label": "Invoices", "datatype": "Int", "indicator": "Blue"},
        {"value": len(customers), "label": "Customers", "datatype": "Int", "indicator": "Purple"},
        {"value": unallocated, "label": "Unallocated", "datatype": "Currency", "indicator": "Orange"},
    ]


# # Copyright (c) 2026, Rasiin Tech and contributors
# # For license information, please see license.txt
# import frappe
# from frappe.utils import flt


# HIS_SETTINGS = "HIS Settings"

# # Change only these two names if your HIS Settings fieldnames are different
# IGNORE_CHILD_TABLE_FIELD = "discount_ignore_item_groups"
# IGNORE_ITEM_GROUP_FIELD = "item_group"


# def execute(filters=None):
#     filters = frappe._dict(filters or {})

#     raw_data = []

#     voucher_type = filters.get("voucher_type") or "All"

#     if voucher_type in ("All", "Payment Entry"):
#         raw_data.extend(get_payment_entry_discounts(filters))

#     # if voucher_type in ("All", "Sales Invoice"):
#     #     raw_data.extend(get_sales_invoice_discounts(filters))

#     if voucher_type in ("All", "Journal Entry"):
#         raw_data.extend(get_journal_entry_discounts(filters))

#     view_type = filters.get("view_type") or "Management Summary"

#     if view_type == "Detail":
#         columns = get_detail_columns()
#         data = raw_data

#     elif view_type == "Item Wise":
#         columns = get_item_wise_columns()
#         data = build_summary(
#             raw_data,
#             group_fields=["item_code", "item_name", "item_group", "source", "discount_account"]
#         )

#     elif view_type == "Item Group Summary":
#         columns = get_item_group_summary_columns()
#         data = build_summary(
#             raw_data,
#             group_fields=["item_group", "source", "discount_account"]
#         )

#     else:
#         columns = get_management_summary_columns()
#         data = build_summary(
#             raw_data,
#             group_fields=["source", "discount_account"]
#         )

#     chart = get_chart(raw_data, filters)
#     report_summary = get_report_summary(raw_data)

#     return columns, data, None, chart, report_summary


# # ---------------------------------------------------------------------
# # COLUMNS
# # ---------------------------------------------------------------------

# def get_management_summary_columns():
#     return [
#         {"label": "Source", "fieldname": "source", "fieldtype": "Data", "width": 150},
#         {"label": "Discount Account", "fieldname": "discount_account", "fieldtype": "Link", "options": "Account", "width": 220},
#         {"label": "Voucher Count", "fieldname": "voucher_count", "fieldtype": "Int", "width": 120},
#         {"label": "Invoice Count", "fieldname": "invoice_count", "fieldtype": "Int", "width": 120},
#         {"label": "Customer Count", "fieldname": "customer_count", "fieldtype": "Int", "width": 130},
#         {"label": "Eligible Amount", "fieldname": "eligible_amount", "fieldtype": "Currency", "width": 150},
#         {"label": "Discount Amount", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 160},
#     ]


# def get_item_group_summary_columns():
#     return [
#         {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 180},
#         {"label": "Source", "fieldname": "source", "fieldtype": "Data", "width": 140},
#         {"label": "Discount Account", "fieldname": "discount_account", "fieldtype": "Link", "options": "Account", "width": 200},
#         {"label": "Voucher Count", "fieldname": "voucher_count", "fieldtype": "Int", "width": 120},
#         {"label": "Invoice Count", "fieldname": "invoice_count", "fieldtype": "Int", "width": 120},
#         {"label": "Customer Count", "fieldname": "customer_count", "fieldtype": "Int", "width": 130},
#         {"label": "Eligible Amount", "fieldname": "eligible_amount", "fieldtype": "Currency", "width": 150},
#         {"label": "Discount Amount", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 160},
#     ]


# def get_item_wise_columns():
#     return [
#         {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 170},
#         {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 220},
#         {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 160},
#         {"label": "Source", "fieldname": "source", "fieldtype": "Data", "width": 140},
#         {"label": "Discount Account", "fieldname": "discount_account", "fieldtype": "Link", "options": "Account", "width": 200},
#         {"label": "Voucher Count", "fieldname": "voucher_count", "fieldtype": "Int", "width": 120},
#         {"label": "Invoice Count", "fieldname": "invoice_count", "fieldtype": "Int", "width": 120},
#         {"label": "Customer Count", "fieldname": "customer_count", "fieldtype": "Int", "width": 130},
#         {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 100},
#         {"label": "Eligible Amount", "fieldname": "eligible_amount", "fieldtype": "Currency", "width": 150},
#         {"label": "Discount Amount", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 160},
#     ]


# def get_detail_columns():
#     return [
#         {"label": "Source", "fieldname": "source", "fieldtype": "Data", "width": 130},
#         {"label": "Voucher Type", "fieldname": "voucher_type", "fieldtype": "Data", "width": 130},
#         {"label": "Voucher", "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 180},
#         {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 110},

#         {"label": "Sales Invoice", "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 180},
#         {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 160},
#         {"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 190},
#         {"label": "Customer Group", "fieldname": "customer_group", "fieldtype": "Link", "options": "Customer Group", "width": 150},

#         {"label": "Patient", "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 140},
#         {"label": "Patient Name", "fieldname": "patient_name", "fieldtype": "Data", "width": 180},
#         {"label": "Doctor", "fieldname": "doctor", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 180},

#         {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 160},
#         {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 220},
#         {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 150},

#         {"label": "Discount Account", "fieldname": "discount_account", "fieldtype": "Link", "options": "Account", "width": 190},

#         {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 90},
#         {"label": "Invoice Net Amount", "fieldname": "invoice_net_amount", "fieldtype": "Currency", "width": 150},
#         {"label": "Eligible Amount", "fieldname": "eligible_amount", "fieldtype": "Currency", "width": 150},
#         {"label": "Discount Amount", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 150},

#         {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120},
#         {"label": "Remarks", "fieldname": "remarks", "fieldtype": "Data", "width": 300},
#     ]


# # ---------------------------------------------------------------------
# # SETTINGS / HELPERS
# # ---------------------------------------------------------------------

# def get_ignored_item_groups():
#     ignored = set()

#     if not frappe.db.exists(HIS_SETTINGS, HIS_SETTINGS):
#         return ignored

#     settings = frappe.get_doc(HIS_SETTINGS, HIS_SETTINGS)

#     for row in settings.get(IGNORE_CHILD_TABLE_FIELD) or []:
#         item_group = row.get(IGNORE_ITEM_GROUP_FIELD)
#         if item_group:
#             ignored.add(item_group)

#     return ignored


# def get_invoice_doc(name):
#     try:
#         return frappe.get_doc("Sales Invoice", name)
#     except Exception:
#         return None


# def get_invoice_doctor(si):
#     return si.get("ref_practitioner") or si.get("practitioner")


# def passes_common_invoice_filters(si, filters):
#     if filters.get("customer") and si.customer != filters.customer:
#         return False

#     if filters.get("customer_group") and si.customer_group != filters.customer_group:
#         return False

#     if filters.get("patient") and si.get("patient") != filters.patient:
#         return False

#     if filters.get("doctor") and get_invoice_doctor(si) != filters.doctor:
#         return False

#     return True


# def make_invoice_context(si):
#     return {
#         "sales_invoice": si.name,
#         "customer": si.customer,
#         "customer_name": si.customer_name,
#         "customer_group": si.customer_group,
#         "patient": si.get("patient"),
#         "patient_name": si.get("patient_name"),
#         "doctor": get_invoice_doctor(si),
#     }


# def get_eligible_invoice_items(si, filters, ignored_item_groups):
#     items = []

#     for item in si.items:
#         if not item.item_group:
#             continue

#         if item.item_group in ignored_item_groups:
#             continue

#         if filters.get("item_group") and item.item_group != filters.item_group:
#             continue

#         if filters.get("item_code") and item.item_code != filters.item_code:
#             continue

#         net_amount = flt(item.net_amount)
#         if net_amount == 0:
#             continue

#         items.append({
#             "item_code": item.item_code,
#             "item_name": item.item_name,
#             "item_group": item.item_group,
#             "qty": flt(item.qty),
#             "net_amount": net_amount,
#             "gross_amount": flt(item.amount),
#             "discount_amount": flt(item.amount) - flt(item.net_amount),
#         })

#     return items


# # ---------------------------------------------------------------------
# # PAYMENT ENTRY
# # ---------------------------------------------------------------------

# def get_payment_entry_discounts(filters):
#     ignored_item_groups = get_ignored_item_groups()
#     data = []

#     conditions = [
#         "pe.docstatus = 1",
#         "pe.posting_date between %(from_date)s and %(to_date)s"
#     ]

#     if filters.get("company"):
#         conditions.append("pe.company = %(company)s")

#     if filters.get("discount_account"):
#         conditions.append("ded.account = %(discount_account)s")

#     payment_entries = frappe.db.sql(f"""
#         select
#             pe.name,
#             pe.posting_date,
#             pe.company,
#             ded.account,
#             ded.amount,
#             ded.cost_center
#         from `tabPayment Entry` pe
#         inner join `tabPayment Entry Deduction` ded
#             on ded.parent = pe.name
#         where {" and ".join(conditions)}
#         order by pe.posting_date, pe.name
#     """, filters, as_dict=True)

#     for pe in payment_entries:
#         references = frappe.db.sql("""
#             select
#                 reference_doctype,
#                 reference_name,
#                 allocated_amount
#             from `tabPayment Entry Reference`
#             where parent = %s
#               and reference_doctype = 'Sales Invoice'
#               and allocated_amount > 0
#         """, pe.name, as_dict=True)

#         if not references:
#             if filters.get("show_unallocated_payment_entries"):
#                 data.append({
#                     "source": "Payment Entry",
#                     "voucher_type": "Payment Entry",
#                     "voucher_no": pe.name,
#                     "posting_date": pe.posting_date,
#                     "discount_account": pe.account,
#                     "discount_amount": flt(pe.amount),
#                     "status": "Unallocated",
#                     "remarks": "Payment deduction exists but no Sales Invoice allocation found"
#                 })
#             continue

#         total_allocated = sum(flt(r.allocated_amount) for r in references)

#         if not total_allocated:
#             continue

#         for ref in references:
#             si = get_invoice_doc(ref.reference_name)
#             if not si:
#                 continue

#             if not passes_common_invoice_filters(si, filters):
#                 continue

#             invoice_items = get_eligible_invoice_items(si, filters, ignored_item_groups)
#             eligible_total = sum(flt(i["net_amount"]) for i in invoice_items)

#             if not eligible_total:
#                 continue

#             invoice_share_discount = flt(pe.amount) * flt(ref.allocated_amount) / total_allocated
#             ctx = make_invoice_context(si)

#             for item in invoice_items:
#                 discount_amount = invoice_share_discount * flt(item["net_amount"]) / eligible_total

#                 row = {
#                     "source": "Payment Entry",
#                     "voucher_type": "Payment Entry",
#                     "voucher_no": pe.name,
#                     "posting_date": pe.posting_date,
#                     "item_code": item["item_code"],
#                     "item_name": item["item_name"],
#                     "item_group": item["item_group"],
#                     "qty": item["qty"],
#                     "discount_account": pe.account,
#                     "invoice_net_amount": flt(si.net_total),
#                     "eligible_amount": flt(item["net_amount"]),
#                     "discount_amount": discount_amount,
#                     "status": "Allocated",
#                     "remarks": "Payment deduction distributed item-wise by eligible invoice net amount"
#                 }

#                 row.update(ctx)
#                 data.append(row)

#     return data


# # ---------------------------------------------------------------------
# # SALES INVOICE
# # ---------------------------------------------------------------------

# def get_sales_invoice_discounts(filters):
#     ignored_item_groups = get_ignored_item_groups()
#     data = []

#     conditions = [
#         "docstatus = 1",
#         "posting_date between %(from_date)s and %(to_date)s"
#     ]

#     if filters.get("company"):
#         conditions.append("company = %(company)s")

#     if filters.get("customer"):
#         conditions.append("customer = %(customer)s")

#     if filters.get("customer_group"):
#         conditions.append("customer_group = %(customer_group)s")

#     if filters.get("patient"):
#         conditions.append("patient = %(patient)s")

#     if filters.get("doctor"):
#         conditions.append("(ref_practitioner = %(doctor)s or practitioner = %(doctor)s)")

#     invoices = frappe.db.sql(f"""
#         select name
#         from `tabSales Invoice`
#         where {" and ".join(conditions)}
#         order by posting_date, name
#     """, filters, as_dict=True)

#     for row in invoices:
#         si = get_invoice_doc(row.name)
#         if not si:
#             continue

#         invoice_items = get_eligible_invoice_items(si, filters, ignored_item_groups)
#         eligible_total = sum(flt(i["net_amount"]) for i in invoice_items)

#         if not invoice_items:
#             continue

#         ctx = make_invoice_context(si)
#         additional_discount = flt(si.discount_amount)

#         for item in invoice_items:
#             item_level_discount = flt(item["discount_amount"])
#             additional_share = 0

#             if additional_discount and eligible_total:
#                 additional_share = additional_discount * flt(item["net_amount"]) / eligible_total

#             total_discount = item_level_discount + additional_share

#             if total_discount <= 0:
#                 continue

#             report_row = {
#                 "source": "Sales Invoice",
#                 "voucher_type": "Sales Invoice",
#                 "voucher_no": si.name,
#                 "posting_date": si.posting_date,
#                 "sales_invoice": si.name,
#                 "item_code": item["item_code"],
#                 "item_name": item["item_name"],
#                 "item_group": item["item_group"],
#                 "qty": item["qty"],
#                 "invoice_net_amount": flt(si.net_total),
#                 "eligible_amount": flt(item["net_amount"]),
#                 "discount_amount": total_discount,
#                 "status": "Submitted",
#                 "remarks": "Sales Invoice item discount plus document additional discount"
#             }

#             report_row.update(ctx)
#             data.append(report_row)

#     return data


# # ---------------------------------------------------------------------
# # JOURNAL ENTRY
# # ---------------------------------------------------------------------

# def get_journal_entry_discounts(filters):
#     data = []

#     # Journal Entry cannot safely support item/patient/doctor filters
#     if (
#         filters.get("item_group")
#         or filters.get("item_code")
#         or filters.get("patient")
#         or filters.get("doctor")
#         or filters.get("customer_group")
#     ):
#         return data

#     conditions = [
#         "je.docstatus = 1",
#         "je.posting_date between %(from_date)s and %(to_date)s"
#     ]

#     if filters.get("company"):
#         conditions.append("je.company = %(company)s")

#     if filters.get("discount_account"):
#         conditions.append("jea.account = %(discount_account)s")

#     if filters.get("customer"):
#         conditions.append("jea.party_type = 'Customer'")
#         conditions.append("jea.party = %(customer)s")

#     rows = frappe.db.sql(f"""
#         select
#             je.name,
#             je.posting_date,
#             je.company,
#             je.user_remark,
#             jea.account,
#             jea.party_type,
#             jea.party,
#             jea.party_name,
#             jea.debit,
#             jea.credit,
#             jea.user_remark as row_remark
#         from `tabJournal Entry` je
#         inner join `tabJournal Entry Account` jea
#             on jea.parent = je.name
#         where {" and ".join(conditions)}
#         order by je.posting_date, je.name
#     """, filters, as_dict=True)

#     for r in rows:
#         amount = flt(r.debit) or flt(r.credit)

#         if not amount:
#             continue

#         data.append({
#             "source": "Journal Entry",
#             "voucher_type": "Journal Entry",
#             "voucher_no": r.name,
#             "posting_date": r.posting_date,
#             "customer": r.party if r.party_type == "Customer" else None,
#             "customer_name": r.party_name if r.party_type == "Customer" else None,
#             "discount_account": r.account,
#             "discount_amount": amount,
#             "status": "Submitted",
#             "remarks": r.row_remark or r.user_remark or "Journal Entry discount row. No item-wise allocation available."
#         })

#     return data


# # ---------------------------------------------------------------------
# # SUMMARY / CHART
# # ---------------------------------------------------------------------

# def build_summary(raw_data, group_fields):
#     grouped = {}

#     for row in raw_data:
#         key = tuple(row.get(field) or "Not Set" for field in group_fields)

#         if key not in grouped:
#             grouped[key] = {}

#             for idx, field in enumerate(group_fields):
#                 grouped[key][field] = key[idx]

#             grouped[key]["voucher_count_set"] = set()
#             grouped[key]["invoice_count_set"] = set()
#             grouped[key]["customer_count_set"] = set()
#             grouped[key]["qty"] = 0
#             grouped[key]["eligible_amount"] = 0
#             grouped[key]["discount_amount"] = 0

#         if row.get("voucher_no"):
#             grouped[key]["voucher_count_set"].add(row.get("voucher_no"))

#         if row.get("sales_invoice"):
#             grouped[key]["invoice_count_set"].add(row.get("sales_invoice"))

#         if row.get("customer"):
#             grouped[key]["customer_count_set"].add(row.get("customer"))

#         grouped[key]["qty"] += flt(row.get("qty"))
#         grouped[key]["eligible_amount"] += flt(row.get("eligible_amount"))
#         grouped[key]["discount_amount"] += flt(row.get("discount_amount"))

#     result = []

#     for row in grouped.values():
#         row["voucher_count"] = len(row.pop("voucher_count_set"))
#         row["invoice_count"] = len(row.pop("invoice_count_set"))
#         row["customer_count"] = len(row.pop("customer_count_set"))
#         result.append(row)

#     result.sort(key=lambda x: flt(x.get("discount_amount")), reverse=True)

#     return result


# def get_chart(raw_data, filters):
#     chart_by = filters.get("chart_by") or "Item Group"

#     field_map = {
#         "Item Group": "item_group",
#         "Item": "item_name",
#         "Source": "source",
#         "Customer Group": "customer_group",
#         "Doctor": "doctor",
#     }

#     group_field = field_map.get(chart_by, "item_group")

#     grouped = {}

#     for row in raw_data:
#         label = row.get(group_field) or "Not Set"
#         grouped[label] = grouped.get(label, 0) + flt(row.get("discount_amount"))

#     rows = sorted(grouped.items(), key=lambda x: x[1], reverse=True)[:10]

#     if not rows:
#         return None

#     return {
#         "data": {
#             "labels": [r[0] for r in rows],
#             "datasets": [
#                 {
#                     "name": "Discount Amount",
#                     "values": [flt(r[1], 2) for r in rows]
#                 }
#             ]
#         },
#         "type": "bar",
#         "height": 280,
#         "colors": ["#5e64ff"]
#     }


# def get_report_summary(raw_data):
#     total_discount = sum(flt(r.get("discount_amount")) for r in raw_data)
#     total_eligible = sum(flt(r.get("eligible_amount")) for r in raw_data)

#     vouchers = set()
#     invoices = set()
#     customers = set()
#     unallocated = 0

#     for row in raw_data:
#         if row.get("voucher_no"):
#             vouchers.add(row.get("voucher_no"))

#         if row.get("sales_invoice"):
#             invoices.add(row.get("sales_invoice"))

#         if row.get("customer"):
#             customers.add(row.get("customer"))

#         if row.get("status") == "Unallocated":
#             unallocated += flt(row.get("discount_amount"))

#     return [
#         {
#             "value": total_discount,
#             "label": "Total Discount",
#             "datatype": "Currency",
#             "indicator": "Red"
#         },
#         {
#             "value": total_eligible,
#             "label": "Eligible Amount",
#             "datatype": "Currency",
#             "indicator": "Blue"
#         },
#         {
#             "value": len(vouchers),
#             "label": "Vouchers",
#             "datatype": "Int",
#             "indicator": "Green"
#         },
#         {
#             "value": len(invoices),
#             "label": "Invoices",
#             "datatype": "Int",
#             "indicator": "Blue"
#         },
#         {
#             "value": len(customers),
#             "label": "Customers",
#             "datatype": "Int",
#             "indicator": "Purple"
#         },
#         {
#             "value": unallocated,
#             "label": "Unallocated",
#             "datatype": "Currency",
#             "indicator": "Orange"
#         },
#     ]