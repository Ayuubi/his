# his/his/commission/work_handlers.py

from __future__ import annotations

import frappe
from .work_commission import (
    post_commission_for_invoice_items, 
    cancel_commission_for_work_doc, 
    post_commission_split_for_clinical_procedure, 
    _allow_commission_on_sample_collection
)


# ------------------------------------------------------------
# Work doctypes
# ------------------------------------------------------------

def on_submit_radiology(doc, method=None):
    if getattr(doc, "journal_entry", None):
        return
    if not getattr(doc, "reff_invoice", None) or not getattr(doc, "sales_invoice_item", None):
        return
    if not getattr(doc, "practitioner", None):
        return

    je = post_commission_for_invoice_items(
        sales_invoice=doc.reff_invoice,
        invoice_item_names=[doc.sales_invoice_item],
        practitioner=doc.practitioner,
        work_doctype=doc.doctype,
        work_name=doc.name,
        posting_date=getattr(doc, "date", None),
    )
    if je:
        doc.db_set("journal_entry", je.name)

def on_cancel_radiology(doc, method=None):
    cancel_commission_for_work_doc(doc)


# def on_submit_clinical_procedure(doc, method=None):
#     if getattr(doc, "journal_entry", None):
#         return
#     if not getattr(doc, "sales_invoice", None) or not getattr(doc, "sales_invoice_item", None):
#         return
#     if not getattr(doc, "practitioner", None):
#         return

#     je = post_commission_for_invoice_items(
#         sales_invoice=doc.sales_invoice,
#         invoice_item_names=[doc.sales_invoice_item],
#         practitioner=doc.practitioner,
#         work_doctype=doc.doctype,
#         work_name=doc.name,
#         posting_date=getattr(doc, "start_date", None),
#     )
#     if je:
#         doc.db_set("journal_entry", je.name)

def on_submit_clinical_procedure(doc, method=None):
    if getattr(doc, "journal_entry", None):
        return
    if not getattr(doc, "sales_invoice", None) or not getattr(doc, "sales_invoice_item", None):
        return
    if not getattr(doc, "practitioner", None):
        return

    je = post_commission_split_for_clinical_procedure(doc)
    if je:
        doc.db_set("journal_entry", je.name)


def on_cancel_clinical_procedure(doc, method=None):
    cancel_commission_for_work_doc(doc)

# ------------------------------------------------------------
# Lab Result commission 
# ------------------------------------------------------------

def on_submit_lab_result(doc, method=None):
    # If commission is configured to run on Sample Collection, do nothing here
    if _allow_commission_on_sample_collection():
        return

    if getattr(doc, "journal_entry", None):
        return

    sales_invoice = getattr(doc, "sales_invoice", None)
    if not sales_invoice or not getattr(doc, "practitioner", None):
        return

    invoice_items = []

    if getattr(doc, "sales_invoice_item", None):
        invoice_items.append(doc.sales_invoice_item)

    for row in (getattr(doc, "normal_test_items", None) or []):
        sii = getattr(row, "sales_invoice_item", None)
        if sii:
            invoice_items.append(sii)

    invoice_items = list(dict.fromkeys([x for x in invoice_items if x]))
    if not invoice_items:
        return

    je = post_commission_for_invoice_items(
        sales_invoice=sales_invoice,
        invoice_item_names=invoice_items,
        practitioner=doc.practitioner,
        work_doctype=doc.doctype,
        work_name=doc.name,
        posting_date=getattr(doc, "posting_date", None),
    )
    if je:
        doc.db_set("journal_entry", je.name)

def on_cancel_lab_result(doc, method=None):
    cancel_commission_for_work_doc(doc)


# ------------------------------------------------------------
# Sample Collection commission 
# ------------------------------------------------------------
def on_submit_sample_collection(doc, method=None):
    if not _allow_commission_on_sample_collection():
        return

    if getattr(doc, "journal_entry", None):
        return

    sales_invoice = getattr(doc, "reff_invoice", None)
    if not sales_invoice or not getattr(doc, "practitioner", None):
        return

    invoice_items = []

    for row in (getattr(doc, "lab_test", None) or []):
        sii = getattr(row, "sales_invoice_item", None)
        if sii:
            invoice_items.append(sii)

    invoice_items = list(dict.fromkeys([x for x in invoice_items if x]))
    if not invoice_items:
        return


    je = post_commission_for_invoice_items(
        sales_invoice=sales_invoice,
        invoice_item_names=invoice_items,
        practitioner=doc.practitioner,
        work_doctype=doc.doctype,
        work_name=doc.name,
        posting_date=getattr(doc, "date", None),
    )
    if je:
        doc.db_set("journal_entry", je.name)


def on_cancel_sample_collection(doc, method=None):
    cancel_commission_for_work_doc(doc)

# ------------------------------------------------------------
# Sales Invoice commission (invoice-time groups e.g. Drugs/Rooms)
# ------------------------------------------------------------

def get_invoice_commission_item_groups():
    hs = frappe.get_doc("HIS Settings", "HIS Settings")
    rows = hs.get("invoice_commission_item_groups") or []  # child table fieldname
    return {(r.item_group or "").strip() for r in rows if (r.item_group or "").strip()}

def on_submit_sales_invoice(doc, method=None):
    # Skip credit notes/returns (handled by return reversal logic)
    if getattr(doc, "is_return", 0):
        return

    # no doctor, no commission
    if not getattr(doc, "ref_practitioner", None):
        return

    # optional JE link on invoice prevents duplicates
    if getattr(doc, "journal_entry", None):
        return

    invoice_groups = get_invoice_commission_item_groups()
    if not invoice_groups:
        return

    invoice_item_names = [
        i.name for i in (doc.items or [])
        if (i.item_group or "").strip() in invoice_groups
    ]
    if not invoice_item_names:
        return

    je = post_commission_for_invoice_items(
        sales_invoice=doc.name,
        invoice_item_names=invoice_item_names,
        practitioner=doc.ref_practitioner,
        work_doctype="Sales Invoice",
        work_name=doc.name,
        posting_date=doc.posting_date,
    )
    if je:
        doc.db_set("journal_entry", je.name)



# import frappe
# from .work_commission import post_commission_for_invoice_items, cancel_commission_for_work_doc

# def on_submit_radiology(doc, method=None):
#     if doc.journal_entry:
#         return
#     if not doc.reff_invoice or not doc.sales_invoice_item:
#         return
#     if not doc.practitioner:
#         return

#     je = post_commission_for_invoice_items(
#         sales_invoice=doc.reff_invoice,
#         invoice_item_names=[doc.sales_invoice_item],
#         practitioner=doc.practitioner,
#         work_doctype=doc.doctype,
#         work_name=doc.name,
#         posting_date=getattr(doc, "date", None),
#     )
#     if je:
#         doc.db_set("journal_entry", je.name)

# def on_cancel_radiology(doc, method=None):
#     cancel_commission_for_work_doc(doc)


# def on_submit_clinical_procedure(doc, method=None):
#     if doc.journal_entry:
#         return
#     if not doc.sales_invoice or not doc.sales_invoice_item:
#         return
#     if not doc.practitioner:
#         return

#     je = post_commission_for_invoice_items(
#         sales_invoice=doc.sales_invoice,
#         invoice_item_names=[doc.sales_invoice_item],
#         practitioner=doc.practitioner,
#         work_doctype=doc.doctype,
#         work_name=doc.name,
#         posting_date=getattr(doc, "start_date", None),
#     )
#     if je:
#         doc.db_set("journal_entry", je.name)

# def on_cancel_clinical_procedure(doc, method=None):
#     cancel_commission_for_work_doc(doc)


# def on_submit_lab_result(doc, method=None):
#     if doc.journal_entry:
#         return

#     sales_invoice = getattr(doc, "sales_invoice", None)
#     if not sales_invoice or not doc.practitioner:
#         return

#     invoice_items = []

#     # If you stored it on parent for Group:
#     if getattr(doc, "sales_invoice_item", None):
#         invoice_items.append(doc.sales_invoice_item)

#     # For Blood: child rows
#     for row in (doc.normal_test_items or []):
#         sii = getattr(row, "sales_invoice_item", None)
#         if sii:
#             invoice_items.append(sii)

#     if not invoice_items:
#         return

#     je = post_commission_for_invoice_items(
#         sales_invoice=sales_invoice,
#         invoice_item_names=invoice_items,
#         practitioner=doc.practitioner,
#         work_doctype=doc.doctype,
#         work_name=doc.name,
#         posting_date=getattr(doc, "posting_date", None),
#     )
    
#     if je:
#         doc.db_set("journal_entry", je.name)

# def on_cancel_lab_result(doc, method=None):
#     cancel_commission_for_work_doc(doc)

# def get_invoice_commission_item_groups():
#     hs = frappe.get_doc("HIS Settings", "HIS Settings")
#     rows = hs.get("invoice_commission_item_groups") or []   # <-- child table fieldname
#     return { (r.item_group or "").strip() for r in rows if r.item_group }


# import frappe

# def on_submit_sales_invoice(doc, method=None):
#     # Skip credit notes/returns (handled by return reversal logic)
#     if doc.is_return:
#         return

#     # no doctor, no commission
#     if not doc.ref_practitioner:
#         return

#     # prevent duplicates if you store a JE link on invoice
#     if getattr(doc, "journal_entry", None):
#         return

#     invoice_groups = get_invoice_commission_item_groups()
#     if not invoice_groups:
#         return

#     invoice_item_names = [
#         i.name for i in doc.items
#         if (i.item_group or "").strip() in invoice_groups
#     ]

#     if not invoice_item_names:
#         return

#     je = post_commission_for_invoice_items(
#         sales_invoice=doc.name,
#         invoice_item_names=invoice_item_names,
#         practitioner=doc.ref_practitioner,
#         work_doctype="Sales Invoice",
#         work_name=doc.name,
#         posting_date=doc.posting_date,
#     )

#     if je:
#         doc.db_set("journal_entry", je.name)

# # def on_cancel_sales_invoice(doc, method=None):
# #     cancel_commission_for_work_doc(doc)