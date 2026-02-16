# his/his/commission/invoice_handlers.py

from __future__ import annotations

import frappe
from collections import defaultdict
from typing import Dict, Set


def _clear_commission_links_for_docs(work_map: Dict[str, Set[str]]):
    """
    Clears fields on work documents referenced by commission_reference:
      - journal_entry
      - commission_posted (optional)
      - commission_posting_date (optional)

    Field-safe: only clears if the field exists on that doctype.
    """
    for doctype, names in (work_map or {}).items():
        names = list({n for n in names if n})
        if not names:
            continue

        meta = frappe.get_meta(doctype)
        if not meta:
            continue

        sets = []
        if meta.has_field("journal_entry"):
            sets.append("`journal_entry` = NULL")
        if meta.has_field("commission_posted"):
            sets.append("`commission_posted` = 0")
        if meta.has_field("commission_posting_date"):
            sets.append("`commission_posting_date` = NULL")

        if not sets:
            continue

        table = f"`tab{doctype}`"
        placeholders = ", ".join(["%s"] * len(names))
        frappe.db.sql(
            f"UPDATE {table} SET {', '.join(sets)} WHERE name IN ({placeholders})",
            tuple(names),
        )


def cancel_commission_for_invoice(doc, method=None):
    """
    On cancel Sales Invoice:
      1) Find all submitted JEs that paid commission for this invoice (via Commisions Reference)
      2) Unlink referenced work docs (so later cancels/deletes don’t fail with link errors)
      3) Cancel those JEs
    """
    rows = frappe.db.sql("""
        SELECT DISTINCT
            je.name AS je_name,
            cr.work_doctype,
            cr.work_name
        FROM `tabJournal Entry` je
        JOIN `tabCommisions Reference` cr ON cr.parent = je.name
        WHERE je.docstatus = 1
          AND cr.sales_invoice = %s
    """, (doc.name,), as_dict=True)

    if not rows:
        # Still clear invoice's own JE link if you use it
        if frappe.get_meta(doc.doctype).has_field("journal_entry") and getattr(doc, "journal_entry", None):
            doc.db_set("journal_entry", None)
        return

    work_map = defaultdict(set)
    je_names = set()

    for r in rows:
        je_names.add(r.get("je_name"))
        wd = r.get("work_doctype")
        wn = r.get("work_name")
        if wd and wn:
            work_map[wd].add(wn)

    # Unlink invoice itself
    if frappe.get_meta(doc.doctype).has_field("journal_entry") and getattr(doc, "journal_entry", None):
        doc.db_set("journal_entry", None)

    # Unlink other doctypes involved
    _clear_commission_links_for_docs(work_map)

    # Cancel JEs
    for je_name in je_names:
        if not je_name:
            continue
        je = frappe.get_doc("Journal Entry", je_name)
        if je.docstatus == 1:
            je.cancel()



# import frappe

# def cancel_commission_for_invoice(doc, method=None):
#     jes = frappe.db.sql("""
#         SELECT DISTINCT je.name
#         FROM `tabJournal Entry` je
#         JOIN `tabCommisions Reference` cr ON cr.parent = je.name
#         WHERE je.docstatus = 1
#           AND cr.sales_invoice = %s
#     """, (doc.name,), as_list=True)

#     for (je_name,) in jes:
#         frappe.get_doc("Journal Entry", je_name).cancel()
