# his/his/commission/work_commission.py

from __future__ import annotations

import frappe
from frappe.utils import getdate, nowdate
from typing import Dict, List, Set, Tuple, Optional

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _norm(v: str) -> str:
    return (v or "").strip().lower()

def _ensure_commission_accounts(his_settings):
    if not his_settings.doctor_exp_account or not his_settings.doctor_commission_account:
        frappe.throw(
            "Missing accounts in HIS Settings: "
            "Doctor Expense Account and/or Doctor Commission Account."
        )

def _get_commission_rows_by_group(hpr) -> Dict[str, List[dict]]:
    """
    Build a mapping:
      {norm_item_group: [row_dict, row_dict, ...]}
    where row_dict contains normalized source_order as well.
    """
    by_group: Dict[str, List[dict]] = {}
    for r in (hpr.commission or []):
        ig = _norm(getattr(r, "item_group", None))
        if not ig:
            continue
        by_group.setdefault(ig, []).append({
            "item_group": getattr(r, "item_group", None),
            "percent": float(getattr(r, "percent", 0) or 0),
            "source_order": getattr(r, "source_order", None),
            "_source_norm": _norm(getattr(r, "source_order", None)),
        })
    return by_group

def pick_commission_rows_for_item_group(
    commission_rows_by_group: Dict[str, List[dict]],
    item_group: str,
    invoice_source_order: str,
    stack_any_with_exact: bool = False,
) -> List[dict]:
    """
    Rules:
      - If exact rows exist for source_order -> use them
      - Else use Any/blank rows
      - Optionally stack exact + any
    """
    rows = commission_rows_by_group.get(_norm(item_group), [])
    if not rows:
        return []

    so_norm = _norm(invoice_source_order)

    any_rows = [r for r in rows if r["_source_norm"] in ("any", "")]
    exact_rows = [r for r in rows if so_norm and r["_source_norm"] == so_norm] if so_norm else []

    if stack_any_with_exact:
        return exact_rows + any_rows
    return exact_rows if exact_rows else any_rows

def _get_existing_commissioned_sii_names(invoice_item_names: List[str]) -> Set[str]:
    """
    Bulk check: which Sales Invoice Item names already have commission in submitted JEs.
    """
    invoice_item_names = [n for n in invoice_item_names if n]
    if not invoice_item_names:
        return set()

    placeholders = ", ".join(["%s"] * len(invoice_item_names))
    rows = frappe.db.sql(f"""
        SELECT DISTINCT cr.sales_invoice_item
        FROM `tabJournal Entry` je
        JOIN `tabCommisions Reference` cr ON cr.parent = je.name
        WHERE je.docstatus = 1
          AND cr.sales_invoice_item IN ({placeholders})
    """, tuple(invoice_item_names), as_list=True)

    return {r[0] for r in rows if r and r[0]}

def _bulk_get_invoice_items(invoice_item_names: List[str]) -> Dict[str, dict]:
    """
    Bulk fetch minimal fields needed from Sales Invoice Item.
    """
    invoice_item_names = [n for n in invoice_item_names if n]
    if not invoice_item_names:
        return {}

    rows = frappe.get_all(
        "Sales Invoice Item",
        filters={"name": ["in", list(set(invoice_item_names))]},
        fields=[
            "name",
            "item_code",
            "item_group",
            "net_amount",
            "amount",
            "net_rate",
        ],
    )
    return {r["name"]: r for r in rows}

# ------------------------------------------------------------
# Core posting
# ------------------------------------------------------------

def post_commission_for_invoice_items(
    *,
    sales_invoice: str,
    invoice_item_names: List[str],
    practitioner: str,
    work_doctype: str,
    work_name: str,
    posting_date=None,
):
    """
    Creates a Journal Entry with:
      - Debit doctor expense
      - Credit doctor commission (Employee party)
      - Child rows in `Commisions Reference` for audit + unlinking later

    Idempotency:
      - Skips invoice items already present in submitted JEs (by Sales Invoice Item).
    """
    his_settings = frappe.get_doc("HIS Settings", "HIS Settings")
    if not his_settings.allow_comm_doc:
        return None

    if not sales_invoice or not invoice_item_names or not practitioner:
        return None

    _ensure_commission_accounts(his_settings)

    inv = frappe.get_doc("Sales Invoice", sales_invoice)
    if inv.docstatus != 1:
        return None

    hpr = frappe.get_doc("Healthcare Practitioner", practitioner)
    if not hpr.commission:
        return None

    if not getattr(hpr, "employee", None):
        frappe.throw(f"Healthcare Practitioner {practitioner} has no Employee linked.")

    source_order = getattr(inv, "source_order", None)
    # STRICT: never post commission if source_order is missing
    if not source_order:
        return None
        
    posting_date = getdate(posting_date or inv.posting_date or nowdate())

    # Deduplicate input
    invoice_item_names = [n for n in invoice_item_names if n]
    invoice_item_names = list(dict.fromkeys(invoice_item_names))

    # Bulk “already commissioned” check
    commissioned = _get_existing_commissioned_sii_names(invoice_item_names)

    # Bulk fetch items
    items_by_name = _bulk_get_invoice_items(invoice_item_names)

    # Prebuild commission config by group
    by_group = _get_commission_rows_by_group(hpr)

    item_com: List[dict] = []
    total = 0.0

    for sii_name in invoice_item_names:
        if not sii_name or sii_name in commissioned:
            continue

        sii = items_by_name.get(sii_name)
        if not sii:
            continue

        base_amount = float(sii.get("net_amount") or 0) or float(sii.get("amount") or 0)
        if not base_amount:
            continue

        comm_rows = pick_commission_rows_for_item_group(
            by_group,
            sii.get("item_group"),
            source_order,
            stack_any_with_exact=False,
        )
        if not comm_rows:
            continue

        for comm in comm_rows:
            pct = float(comm.get("percent") or 0)
            if pct <= 0:
                continue

            comm_amount = (pct / 100.0) * base_amount
            if not comm_amount:
                continue

            total += comm_amount
            item_com.append({
                "item": sii.get("item_code"),
                "item_group": sii.get("item_group"),
                "net_rate": float(sii.get("net_rate") or 0),
                "commission": comm_amount,

                # Audit fields used for unlinking later
                "sales_invoice": inv.name,
                "sales_invoice_item": sii_name,
                "work_doctype": work_doctype,
                "work_name": work_name,
            })

    if not total:
        return None

    accounts = [
        {
            "account": his_settings.doctor_exp_account,
            "debit_in_account_currency": total,
            "source_order": source_order,
        },
        {
            "account": his_settings.doctor_commission_account,
            "party_type": "Employee",
            "party": hpr.employee,
            "credit_in_account_currency": total,
            "source_order": source_order,
        },
    ]

    je = frappe.get_doc({
        "doctype": "Journal Entry",
        "voucher_type": "Journal Entry",
        "posting_date": posting_date,
        "practitioner": practitioner,
        "user_remark": f"Doctor Commission | {work_doctype} {work_name} | Invoice {inv.name} | {source_order}",
        "accounts": accounts,
        "sales_invoice": inv.name,
        "commission_reference": item_com,
    })
    je.insert(ignore_permissions=True)
    je.submit()
    return je


# ------------------------------------------------------------
# Commission Spit Logic
# ------------------------------------------------------------

def _get_commission_rows_by_group_from_doc(parent_doc, child_field="commission") -> Dict[str, List[dict]]:
    by_group: Dict[str, List[dict]] = {}
    for r in (getattr(parent_doc, child_field, None) or []):
        ig = _norm(getattr(r, "item_group", None))
        if not ig:
            continue
        by_group.setdefault(ig, []).append({
            "item_group": getattr(r, "item_group", None),
            "percent": float(getattr(r, "percent", 0) or 0),
            "source_order": getattr(r, "source_order", None),
            "_source_norm": _norm(getattr(r, "source_order", None)),
        })
    return by_group

def _allow_commission_on_sample_collection() -> bool:
    """True => commission should happen on Sample Collection, not on Lab Result."""
    try:
        return bool(frappe.db.get_single_value("HIS Settings", "allow_commission_on_sc"))
    except Exception:
        return False


def _compute_commission_percent_and_desc(by_group, item_group: str, source_order: str):
    """
    Returns (total_percent, desc_string)
    """
    comm_rows = pick_commission_rows_for_item_group(
        by_group,
        item_group,
        source_order,
        stack_any_with_exact=False,
    )
    if not comm_rows:
        return 0.0, "No commission rule"

    total_pct = 0.0
    parts = []
    for r in comm_rows:
        pct = float(r.get("percent") or 0)
        if pct <= 0:
            continue
        total_pct += pct
        parts.append(f'{pct:g}%({r.get("source_order") or "ANY"})')

    if total_pct <= 0:
        return 0.0, "Commission percent is 0"

    return total_pct, " + ".join(parts)


def post_commission_split_for_clinical_procedure(doc):
    """
    One JE:
      - 1 debit (expense) = total commissions
      - N credits (commission payable) = one per employee
    Role is written into each JEA.user_remark.
    """

    his_settings = frappe.get_doc("HIS Settings", "HIS Settings")
    if not his_settings.allow_comm_doc:
        return None
    _ensure_commission_accounts(his_settings)

    inv = frappe.get_doc("Sales Invoice", doc.sales_invoice)
    if inv.docstatus != 1:
        return None

    source_order = getattr(inv, "source_order", None)
    if not source_order:
        return None  # keep your STRICT rule

    posting_date = getdate(getattr(doc, "start_date", None) or inv.posting_date or nowdate())

    sii_name = doc.sales_invoice_item
    items_by_name = _bulk_get_invoice_items([sii_name])
    sii = items_by_name.get(sii_name)
    if not sii:
        return None

    item_group = sii.get("item_group")
    base_amount = float(sii.get("net_amount") or 0) or float(sii.get("amount") or 0)
    if not base_amount:
        return None

    requesting = getattr(doc, "practitioner", None)
    performing = getattr(doc, "performing_practitioner", None)
    anesth = getattr(doc, "anesthetist_practitioner", None)  # Link to Anesthesia Commission

    payees = []

    # ---- compute percents first ----
    req_pct = perf_pct = anes_pct = 0.0
    req_desc = perf_desc = anes_desc = ""

    if requesting:
        hpr = frappe.get_doc("Healthcare Practitioner", requesting)
        if not getattr(hpr, "employee", None):
            frappe.throw(f"Healthcare Practitioner {requesting} has no Employee linked.")
        req_emp = hpr.employee

        req_by_group = _get_commission_rows_by_group_from_doc(hpr, "commission")
        req_pct, req_desc = _compute_commission_percent_and_desc(req_by_group, item_group, source_order)
    else:
        return None

    if performing and performing != requesting:
        hpr2 = frappe.get_doc("Healthcare Practitioner", performing)
        if not getattr(hpr2, "employee", None):
            frappe.throw(f"Healthcare Practitioner {performing} has no Employee linked.")
        perf_emp = hpr2.employee

        perf_by_group = _get_commission_rows_by_group_from_doc(hpr2, "commission")
        perf_pct, perf_desc = _compute_commission_percent_and_desc(perf_by_group, item_group, source_order)

    if anesth:
        ac = frappe.get_doc("Anesthesia Commission", anesth)
        if not getattr(ac, "employee", None):
            frappe.throw(f"Anesthesia Commission {anesth} has no Employee linked.")
        anes_emp = ac.employee

        anes_by_group = _get_commission_rows_by_group_from_doc(ac, "commission")
        anes_pct, anes_desc = _compute_commission_percent_and_desc(anes_by_group, item_group, source_order)

    # ---- apply your rule: requesting reduced by performing (only if different) ----
    # ------------------------------------------------------------
    # Split logic switch:
    #   - If allow_split_on_requesting_percentage = 0:
    #       Performing % is based on FULL procedure base_amount
    #       Requesting % is reduced by Performing % (your current logic)
    #
    #   - If allow_split_on_requesting_percentage = 1:
    #       Performing % is based on REQUESTING AMOUNT (req_pct% of base_amount)
    #       Requesting keeps the remainder of their pool after Performing cut
    # ------------------------------------------------------------
    split_on_requesting_pool = bool(getattr(his_settings, "allow_split_on_requesting_percentage", 0))

    payees = []

    # Always compute anesthesia from full base_amount (unchanged)
    anes_amt = 0.0
    if anesth:
        anes_amt = (max(0.0, float(anes_pct)) / 100.0) * base_amount

    # ---------- Requesting / Performing ----------
    # Base requesting pool (Requesting doctor's configured percent of procedure)
    req_pool_amt = (max(0.0, float(req_pct)) / 100.0) * base_amount

    perf_amt = 0.0
    req_amt = 0.0

    if performing and performing != requesting and perf_pct:
        perf_pct_sane = max(0.0, float(perf_pct))

        if split_on_requesting_pool:
            # Performing cut comes from requesting pool (e.g. 10% of 600 = 60)
            perf_amt = (perf_pct_sane / 100.0) * req_pool_amt

            # Don’t allow performing to exceed requesting pool
            if perf_amt > req_pool_amt:
                perf_amt = req_pool_amt

            req_amt = req_pool_amt - perf_amt

            req_rule_desc = (
                f"{req_desc} | pool={req_pct:g}% of base ({req_pool_amt:g}) | "
                f"effective={req_amt:g} after perf cut ({perf_pct_sane:g}% of pool = {perf_amt:g})"
            )
            perf_rule_desc = (
                f"{perf_desc} | pct={perf_pct_sane:g}% of REQUESTING pool ({req_pool_amt:g})"
            )
        else:
            # Current behavior: performing cut is based on full procedure base_amount
            perf_amt = (perf_pct_sane / 100.0) * base_amount

            # Requesting reduced by performing percentage (pct math, your original rule)
            req_effective_pct = max(0.0, float(req_pct) - float(perf_pct_sane))
            req_amt = (req_effective_pct / 100.0) * base_amount

            req_rule_desc = (
                f"{req_desc} | effective={req_effective_pct:g}% (orig {req_pct:g}% - perf {perf_pct_sane:g}%)"
            )
            perf_rule_desc = f"{perf_desc} | pct={perf_pct_sane:g}%"
    else:
        # No performing doctor (or same as requesting) => requesting gets full requesting pool
        req_amt = req_pool_amt
        req_rule_desc = f"{req_desc} | pct={req_pct:g}% (no performing cut)"

    # ---- Add payees (same JE behavior as before) ----
    if req_amt:
        payees.append({
            "role": "Requesting",
            "employee": req_emp,
            "ref": requesting,
            "amount": float(req_amt),
            "rule_desc": req_rule_desc,
        })

    if performing and performing != requesting and perf_amt:
        payees.append({
            "role": "Performing",
            "employee": perf_emp,
            "ref": performing,
            "amount": float(perf_amt),
            "rule_desc": perf_rule_desc,
        })

    if anesth and anes_amt:
        payees.append({
            "role": "Anesthesia",
            "employee": anes_emp,
            "ref": anesth,
            "amount": float(anes_amt),
            "rule_desc": f"{anes_desc} | pct={anes_pct:g}% (of base)",
        })

    if not payees:
        return None


    total_all = sum(float(p["amount"]) for p in payees)
    if not total_all:
        return None

    commission_reference = [{
        "item": sii.get("item_code"),
        "item_group": item_group,
        "net_rate": float(sii.get("net_rate") or 0),
        "net_amount": float(base_amount or 0),

        # total commission for this Sales Invoice Item (sum of Requesting/Performing/Anesthesia)
        "commission": float(total_all),

        # IMPORTANT: link to ORIGINAL invoice + ORIGINAL invoice item
        "sales_invoice": inv.name,
        "sales_invoice_item": sii_name,

        # work doc that caused the commission
        "work_doctype": doc.doctype,   # Clinical Procedure
        "work_name": doc.name,
    }]

    accounts = [
        {
            "account": his_settings.doctor_exp_account,
            "debit_in_account_currency": total_all,
            "source_order": source_order,
            # "reference_type": "Sales Invoice",
            # "reference_name": doc.sales_invoice,
        }
    ]

    # One credit line per payee (employee)
    for p in payees:
        accounts.append({
            "account": his_settings.doctor_commission_account,
            "party_type": "Employee",
            "party": p["employee"],
            "credit_in_account_currency": float(p["amount"]),
            "source_order": source_order,

            # # makes it clear + searchable
            # "reference_type": doc.doctype,
            # "reference_name": doc.name,
            "user_remark": (
                f'{p["role"]} | Ref={p["ref"]} | '
                f'ItemGroup={item_group} | Base={base_amount:g} | Rules={p["rule_desc"]} | Amt={float(p["amount"]):g}'
            ),
        })

    je = frappe.get_doc({
        "doctype": "Journal Entry",
        "voucher_type": "Journal Entry",
        "posting_date": posting_date,
        "practitioner": requesting,  # keep main = requesting
        "user_remark": (
            f"Commission Split | {doc.doctype} {doc.name} | Invoice {inv.name} | {source_order} | "
            f"ItemGroup={item_group} | Base={base_amount:g}"
        ),
        "accounts": accounts,
        "sales_invoice": inv.name,
        # IMPORTANT: we can omit commission_reference here to avoid confusing “who got what”
        # "commission_reference": [],
        "commission_reference": commission_reference,
    })
    je.insert(ignore_permissions=True)
    je.submit()
    return je

# ------------------------------------------------------------
# Cancel helper for work docs
# ------------------------------------------------------------

def cancel_commission_for_work_doc(work_doc):
    """
    Cancels JE linked directly on a work document (journal_entry field),
    and clears links/flags on that doc first to avoid link validation issues.
    """
    je_name = getattr(work_doc, "journal_entry", None)
    if not je_name:
        return

    # Clear links first (idempotent, field-safe)
    if frappe.get_meta(work_doc.doctype).has_field("journal_entry"):
        frappe.db.set_value(work_doc.doctype, work_doc.name, "journal_entry", None, update_modified=False)
        work_doc.journal_entry = None

    if frappe.get_meta(work_doc.doctype).has_field("commission_posted"):
        frappe.db.set_value(work_doc.doctype, work_doc.name, "commission_posted", 0, update_modified=False)
        if hasattr(work_doc, "commission_posted"):
            work_doc.commission_posted = 0

    if frappe.get_meta(work_doc.doctype).has_field("commission_posting_date"):
        frappe.db.set_value(work_doc.doctype, work_doc.name, "commission_posting_date", None, update_modified=False)
        if hasattr(work_doc, "commission_posting_date"):
            work_doc.commission_posting_date = None

    je = frappe.get_doc("Journal Entry", je_name)
    if je.docstatus == 1:
        je.cancel()

# import frappe
# from frappe.utils import getdate, nowdate

# def _norm(v: str) -> str:
#     return (v or "").strip().lower()

# def pick_commission_rows_for_item_group(hpr, item_group, invoice_source_order, stack_any_with_exact=False):
#     rows = [r for r in (hpr.commission or []) if _norm(r.item_group) == _norm(item_group)]
#     if not rows:
#         return []

#     so = (invoice_source_order or "").strip()
#     any_rows = [r for r in rows if _norm(r.source_order) in ("any", "")]
#     exact_rows = [r for r in rows if (r.source_order or "").strip() == so] if so else []

#     if stack_any_with_exact:
#         return exact_rows + any_rows
#     return exact_rows if exact_rows else any_rows

# def je_exists_for_invoice_item(sii_name: str) -> bool:
#     # IMPORTANT: table name uses your child doctype: `tabCommisions Reference`
#     res = frappe.db.sql("""
#         SELECT je.name
#         FROM `tabJournal Entry` je
#         JOIN `tabCommisions Reference` cr ON cr.parent = je.name
#         WHERE je.docstatus = 1
#           AND cr.sales_invoice_item = %s
#         LIMIT 1
#     """, (sii_name,))
#     return bool(res)

# def post_commission_for_invoice_items(
#     *,
#     sales_invoice: str,
#     invoice_item_names: list[str],
#     practitioner: str,
#     work_doctype: str,
#     work_name: str,
#     posting_date=None,
# ):
#     his_settings = frappe.get_doc("HIS Settings", "HIS Settings")
#     if not his_settings.allow_comm_doc:
#         return None

#     if not sales_invoice or not invoice_item_names or not practitioner:
#         return None

#     inv = frappe.get_doc("Sales Invoice", sales_invoice)

#     # If invoice got cancelled, don't pay
#     if inv.docstatus != 1:
#         return None

#     # Find doctor commission profile
#     hpr = frappe.get_doc("Healthcare Practitioner", practitioner)
#     if not hpr.commission:
#         return None

#     source_order = inv.source_order
#     posting_date = getdate(posting_date or inv.posting_date or nowdate())

#     item_com = []
#     total = 0.0

#     # Deduplicate invoice items list
#     seen = set()
#     for sii_name in invoice_item_names:
#         if not sii_name or sii_name in seen:
#             continue
#         seen.add(sii_name)

#         # Skip if already commissioned anywhere
#         if je_exists_for_invoice_item(sii_name):
#             continue

#         sii = frappe.get_doc("Sales Invoice Item", sii_name)

#         # Amount base: use net_amount (qty-safe)
#         base_amount = float(sii.net_amount or 0) or float(sii.amount or 0)

#         if not base_amount:
#             continue

#         comm_rows = pick_commission_rows_for_item_group(hpr, sii.item_group, source_order, stack_any_with_exact=False)
#         if not comm_rows:
#             continue

#         for comm in comm_rows:
#             comm_amount = (float(comm.percent) / 100.0) * base_amount
#             total += comm_amount

#             item_com.append({
#                 "item": sii.item_code,
#                 "item_group": sii.item_group,
#                 "net_rate": float(sii.net_rate or 0),
#                 "commission": comm_amount,

#                 # NEW audit fields
#                 "sales_invoice": inv.name,
#                 "sales_invoice_item": sii.name,
#                 "work_doctype": work_doctype,
#                 "work_name": work_name,
#             })

#     if not total:
#         return None

#     accounts = [
#         {
#             "account": his_settings.doctor_exp_account,
#             "debit_in_account_currency": total,
#             "source_order": source_order,
#         },
#         {
#             "account": his_settings.doctor_commission_account,
#             "party_type": "Employee",
#             "party": hpr.employee,
#             "credit_in_account_currency": total,
#             "source_order": source_order,
#         },
#     ]

#     je = frappe.get_doc({
#         "doctype": "Journal Entry",
#         "voucher_type": "Journal Entry",
#         "posting_date": posting_date,
#         "practitioner": practitioner,
#         "user_remark": f"Doctor Commission | {work_doctype} {work_name} | Invoice {inv.name} | {source_order}",
#         "accounts": accounts,
#         "sales_invoice": inv.name,
#         "commission_reference": item_com,
#     })
#     je.insert(ignore_permissions=True)
#     je.submit()
#     return je

# def cancel_commission_for_work_doc(work_doc):
#     je_name = getattr(work_doc, "journal_entry", None)
#     if not je_name:
#         return

#     # 1) Clear the link FIRST (so Frappe won't complain after JE is cancelled)
#     # update_modified=False so it doesn't touch timestamps unnecessarily
#     frappe.db.set_value(work_doc.doctype, work_doc.name, "journal_entry", None, update_modified=False)

#     # also clear flags if you use them
#     if hasattr(work_doc, "commission_posted"):
#         frappe.db.set_value(work_doc.doctype, work_doc.name, "commission_posted", 0, update_modified=False)
#     if hasattr(work_doc, "commission_posting_date"):
#         frappe.db.set_value(work_doc.doctype, work_doc.name, "commission_posting_date", None, update_modified=False)

#     # keep runtime object consistent too
#     work_doc.journal_entry = None
#     if hasattr(work_doc, "commission_posted"):
#         work_doc.commission_posted = 0
#     if hasattr(work_doc, "commission_posting_date"):
#         work_doc.commission_posting_date = None

#     # 2) Now cancel the JE
#     je = frappe.get_doc("Journal Entry", je_name)
#     if je.docstatus == 1:
#         je.cancel()

