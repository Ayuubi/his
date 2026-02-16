from __future__ import annotations

import frappe
from frappe.utils import flt


# ----------------------
# Mapping helpers
# ----------------------

def _get_original_sii_name(return_row):
    """
    Try common pointer fields that may exist in your Sales Invoice Item schema.
    Your system may have any of these.
    """
    for f in ("si_detail", "sales_invoice_item", "return_against_item", "dn_detail"):
        if hasattr(return_row, f):
            v = getattr(return_row, f, None)
            if v:
                return v
    return None


def _fallback_match_original_sii(return_doc, return_row):
    """
    Fallback mapping if pointer field is missing.
    Matches by item_code (+ optionally net_rate/uom).
    Can be ambiguous if original invoice has duplicate item_code lines.
    """
    if not return_doc.return_against:
        return None

    filters = {"parent": return_doc.return_against, "item_code": return_row.item_code}

    if flt(return_row.net_rate):
        filters["net_rate"] = abs(flt(return_row.net_rate))

    if getattr(return_row, "uom", None):
        filters["uom"] = return_row.uom

    name = frappe.db.get_value("Sales Invoice Item", filters, "name")
    if name:
        return name

    # relaxed fallback
    return frappe.db.get_value(
        "Sales Invoice Item",
        {"parent": return_doc.return_against, "item_code": return_row.item_code},
        "name",
    )


# ----------------------
# Commission queries
# ----------------------

def _commission_paid_for_original_sii_by_employee(original_sii_name: str, commission_account: str):
    """
    SAFE universal method for old + split JEs:

    For each JE that includes this original SII:
      item_commission_in_that_JE = SUM(cr.commission) for (JE, SII)
      employee_share = employee_credit / total_employee_credit_in_that_JE
      employee_item_commission = item_commission_in_that_JE * employee_share
    """
    return frappe.db.sql(
        """
        SELECT
            shares.employee,
            SUM(shares.item_commission * shares.emp_ratio) AS total_commission
        FROM (
            SELECT
                je.name AS je_name,
                jea.party AS employee,
                item_comm.item_commission AS item_commission,
                (jea.credit_in_account_currency / totals.total_credit) AS emp_ratio
            FROM `tabJournal Entry` je
            JOIN (
                SELECT
                    cr.parent AS je_name,
                    SUM(cr.commission) AS item_commission
                FROM `tabCommisions Reference` cr
                WHERE cr.sales_invoice_item = %s
                GROUP BY cr.parent
            ) item_comm
              ON item_comm.je_name = je.name
            JOIN (
                SELECT
                    jea2.parent AS je_name,
                    SUM(jea2.credit_in_account_currency) AS total_credit
                FROM `tabJournal Entry Account` jea2
                WHERE jea2.party_type = 'Employee'
                  AND jea2.party IS NOT NULL
                  AND jea2.account = %s
                  AND jea2.credit_in_account_currency > 0
                GROUP BY jea2.parent
            ) totals
              ON totals.je_name = je.name
             AND totals.total_credit > 0
            JOIN `tabJournal Entry Account` jea
              ON jea.parent = je.name
             AND jea.party_type = 'Employee'
             AND jea.party IS NOT NULL
             AND jea.account = %s
             AND jea.credit_in_account_currency > 0
            WHERE je.docstatus = 1
        ) shares
        GROUP BY shares.employee
        """,
        (original_sii_name, commission_account, commission_account),
        as_dict=True,
    )

def _reversal_already_created_for_return(return_invoice_name: str) -> bool:
    row = frappe.db.sql(
        """
        SELECT je.name
        FROM `tabJournal Entry` je
        JOIN `tabCommisions Reference` cr ON cr.parent = je.name
        WHERE je.docstatus = 1
          AND cr.work_doctype = 'Sales Invoice'
          AND cr.work_name = %s
          AND cr.sales_invoice = %s
          AND cr.commission < 0
        LIMIT 1
        """,
        (return_invoice_name, return_invoice_name),
        as_list=True,
    )
    return bool(row)


# ----------------------
# Create reversal JE(s)
# ----------------------

def create_commission_reversal_for_return(doc, method=None):
    """
    Trigger: Sales Invoice on_submit (Return / Credit Note)

    Rule:
      - Reverse commission ONLY if commission was actually PAID for the original invoice item.
      - No dependency on HIS Settings invoice_groups (prevents wrong skipping).
      - Supports partial returns (proportional by amount; qty fallback).
      - Prevent duplicates per return invoice.
    """
    if not doc.is_return or not doc.return_against:
        return

    # prevent duplicates if hook runs twice
    if _reversal_already_created_for_return(doc.name):
        return

    hs = frappe.get_doc("HIS Settings", "HIS Settings")
    if not hs.allow_comm_doc:
        return

    commission_account = hs.doctor_commission_account
    exp_account = hs.doctor_exp_account
    if not commission_account or not exp_account:
        frappe.throw("Set Doctor Commission Account and Doctor Expense Account in HIS Settings.")

    original_invoice = frappe.get_doc("Sales Invoice", doc.return_against)

    employee_totals: dict[str, float] = {}
    ref_rows_by_employee: dict[str, list[dict]] = {}

    for r in (doc.items or []):
        # Map return row -> original invoice item
        original_sii = _get_original_sii_name(r) or _fallback_match_original_sii(doc, r)
        if not original_sii:
            frappe.log_error(
                f"Could not map return row={r.name} item_code={r.item_code} "
                f"pointer_fields={{si_detail:{getattr(r,'si_detail',None)}, sales_invoice_item:{getattr(r,'sales_invoice_item',None)}, "
                f"return_against_item:{getattr(r,'return_against_item',None)}}}",
                "Commission Return Mapping Failed",
            )
            continue

        orig_row = frappe.get_doc("Sales Invoice Item", original_sii)

        # Compute proportional ratio (amount-based; qty fallback)
        returned_base = abs(flt(getattr(r, "net_amount", 0) or 0))
        original_base = abs(flt(getattr(orig_row, "net_amount", 0) or 0))

        if returned_base and original_base:
            ratio = min(1.0, returned_base / original_base)
        else:
            # fallback only if net_amount missing
            returned_qty = abs(flt(getattr(r, "qty", 0) or 0))
            original_qty = abs(flt(getattr(orig_row, "qty", 0) or 0))
            if not returned_qty or not original_qty:
                continue
            ratio = min(1.0, returned_qty / original_qty)


        # Reverse only if there WAS paid commission for this original item
        paid_rows = _commission_paid_for_original_sii_by_employee(original_sii, commission_account)
        if not paid_rows:
            continue

        orig_group = (orig_row.item_group or "").strip()

        for prow in paid_rows:
            employee = prow.get("employee")
            paid_total = flt(prow.get("total_commission"))
            if not employee or paid_total <= 0:
                continue

            reverse_amt = paid_total * ratio
            if reverse_amt <= 0:
                continue

            employee_totals[employee] = employee_totals.get(employee, 0.0) + reverse_amt

            ref_rows_by_employee.setdefault(employee, []).append({
                "item": r.item_code,
                "item_group": orig_group,
                "net_rate": flt(r.net_rate),
                "commission": -reverse_amt,      # negative in reference
                "sales_invoice": doc.name,       # RETURN invoice
                "sales_invoice_item": r.name,    # RETURN row name
                "work_doctype": "Sales Invoice",
                "work_name": doc.name,
            })

    if not employee_totals:
        return
    
    total_rev = sum(flt(v) for v in employee_totals.values())
    if total_rev <= 0:
        return

    accounts = [
        {
            # Reverse the commission expense
            "account": exp_account,
            "debit_in_account_currency": total_rev,
            "source_order": getattr(original_invoice, "source_order", None),
        }
    ]

    # Reduce payable for each employee (credit payable)
    for employee, amt in employee_totals.items():
        amt = flt(amt)
        if amt <= 0:
            continue

        accounts.append({
            "account": commission_account,
            "party_type": "Employee",
            "party": employee,
            "credit_in_account_currency": amt,
            "source_order": getattr(original_invoice, "source_order", None),
            "user_remark": f"Commission Reversal Share | {employee} | {amt:g}",
        })


    # IMPORTANT:
    # If your commission_account is the same account used for employee payables,
    # you may prefer this accounting structure instead:
    #   Debit commission_account (no party) total_rev
    #   Credit commission_account with party per employee amounts
    #   Credit exp_account total_rev
    # If it errors due to account/party validations, tell me and I'll match your chart of accounts.

    je = frappe.get_doc({
        "doctype": "Journal Entry",
        "voucher_type": "Journal Entry",
        "posting_date": doc.posting_date,
        "practitioner": getattr(doc, "ref_practitioner", None),
        "user_remark": f"Commission Reversal | Return {doc.name} against {doc.return_against}",
        "accounts": accounts,
        "sales_invoice": doc.name,
    })

    # append ALL reference rows (flatten)
    for employee, rows in ref_rows_by_employee.items():
        for rr in rows:
            je.append("commission_reference", rr)

    je.insert(ignore_permissions=True)
    je.submit()


    # Create one reversal JE per employee
    # for employee, amt in employee_totals.items():
    #     accounts = [
    #         {
    #             "account": commission_account,
    #             "party_type": "Employee",
    #             "party": employee,
    #             "debit_in_account_currency": amt,
    #             "source_order": getattr(original_invoice, "source_order", None),
    #         },
    #         {
    #             "account": exp_account,
    #             "credit_in_account_currency": amt,
    #             "source_order": getattr(original_invoice, "source_order", None),
    #         },
    #     ]

    #     je = frappe.get_doc({
    #         "doctype": "Journal Entry",
    #         "voucher_type": "Journal Entry",
    #         "posting_date": doc.posting_date,
    #         "practitioner": getattr(doc, "ref_practitioner", None),
    #         "user_remark": f"Commission Reversal | Return {doc.name} against {doc.return_against} | Employee {employee}",
    #         "accounts": accounts,
    #         "sales_invoice": doc.name,
    #         "commission_reference": ref_rows_by_employee.get(employee, []),
    #     })
    #     je.insert(ignore_permissions=True)
    #     je.submit()


# ----------------------
# Cancel reversal JE(s)
# ----------------------

def cancel_commission_reversal_for_return(doc, method=None):
    """
    Trigger: Sales Invoice on_cancel (Return invoice)
    Cancels ALL reversal JEs created for THIS return invoice.
    """
    if not doc.is_return:
        return

    je_rows = frappe.db.sql(
        """
        SELECT DISTINCT je.name
        FROM `tabJournal Entry` je
        JOIN `tabCommisions Reference` cr ON cr.parent = je.name
        WHERE je.docstatus = 1
        AND cr.work_doctype = 'Sales Invoice'
        AND cr.work_name = %s
        AND cr.sales_invoice = %s
        AND cr.commission < 0
        """,
        (doc.name, doc.name),
        as_list=True,
    )

    for (je_name,) in je_rows:
        je = frappe.get_doc("Journal Entry", je_name)
        if je.docstatus == 1:
            je.cancel()
