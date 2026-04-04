# Copyright (c) 2021, Rasiin and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class Expenses(Document):
    def validate(self):
        return
        self._validate_header()
        self._validate_lines()
        self._recalc_total()

    def _validate_header(self):
        if not self.company:
            frappe.throw("Company is required")
        if not self.posting_date:
            frappe.throw("Posting Date is required")
        # if not self.paid_from:
        #     frappe.throw("Paid From is required")

        # Paid From must be leaf + Bank/Cash + same company
        pf = frappe.get_cached_value(
            "Account",
            self.paid_from,
            ["is_group", "account_type", "company"],
            as_dict=True,
        )

        if pf.is_group:
            frappe.throw("Paid From cannot be a group account")

        if pf.company != self.company:
            frappe.throw(f"Paid From must belong to company {self.company}")

        if (pf.account_type or "") not in ("Bank", "Cash"):
            frappe.throw("Paid From must be a Bank or Cash account")

    def _validate_lines(self):
        if not getattr(self, "expense_lines", None) or len(self.expense_lines) == 0:
            frappe.throw("Please add at least one Expense Line")

        allowed_party_types = {"Supplier", "Customer", "Employee"}

        for i, row in enumerate(self.expense_lines, start=1):
            if not row.expense_account:
                frappe.throw(f"Row #{i}: Expense Account is required")

            if flt(row.amount) <= 0:
                frappe.throw(f"Row #{i}: Amount must be greater than 0")

            # Expense account must be leaf + Expense root_type + same company
            acc = frappe.get_cached_value(
                "Account",
                row.expense_account,
                ["is_group", "root_type", "company"],
                as_dict=True,
            )

            if acc.is_group:
                frappe.throw(f"Row #{i}: Expense Account cannot be a group account")

            if acc.company != self.company:
                frappe.throw(f"Row #{i}: Expense Account must belong to company {self.company}")

            if (acc.root_type or "") != "Expense":
                frappe.throw(f"Row #{i}: Expense Account must be an Expense account (root_type=Expense)")

            # Party validation
            pt = (row.party_type or "").strip()
            party = (row.party or "").strip()

            if pt and pt not in allowed_party_types:
                frappe.throw(f"Row #{i}: Party Type must be Supplier, Customer, or Employee")

            if party and not pt:
                frappe.throw(f"Row #{i}: Party Type is required when Party is set")

            if pt and not party:
                frappe.throw(f"Row #{i}: Party is required when Party Type is set")

    def _recalc_total(self):
        total = 0.0
        for row in self.expense_lines:
            total += flt(row.amount)
        self.total_amount = total

    def on_submit(self):
        # Ensure total is up-to-date
        self._recalc_total()

        accounts = []

        # Debit lines (one per expense line)
        for row in self.expense_lines:
            accounts.append(
                {
                    "account": row.expense_account,
                    "debit_in_account_currency": flt(row.amount),
                    "party_type": row.party_type,
                    "party": row.party,
                    "user_remark": row.line_remark,
					"expense_type": row.expense_type,
                }
            )

        # Credit line (Paid From)
        accounts.append(
            {
                "account": self.paid_from,
                "credit_in_account_currency": flt(self.total_amount),
                "user_remark": "Paid From",
            }
        )

        je = frappe.get_doc(
            {
                "doctype": "Journal Entry",
                "voucher_type": "Journal Entry",
                "company": self.company,
                "posting_date": self.posting_date,
                "user_remark": self.remark,
                "accounts": accounts,
            }
        )

        je.insert(ignore_permissions=True)
        je.submit()

        # DO NOT self.save() in on_submit
        self.db_set("journal_entry", je.name)

    def on_cancel(self):
        if self.journal_entry:
            je = frappe.get_doc("Journal Entry", self.journal_entry)
            if je.docstatus == 1:
                je.cancel()



# # Copyright (c) 2021, Rasiin and contributors
# # For license information, please see license.txt
# from erpnext.stock.get_item_details import get_pos_profile

# import frappe
# from frappe.model.document import Document

# class Expenses(Document):
# 	@frappe.whitelist()
# 	def mode_of_payments(company):
# 		pos_profile = get_pos_profile(company)
# 		mode_of_payment = frappe.db.get_value('POS Payment Method', {"parent": pos_profile.name},  'mode_of_payment')
# 		default_account = frappe.db.get_value('Mode of Payment Account', {"parent": mode_of_payment},  'default_account')
# 		return default_account
	
# 	def on_submit(self):

# 		account = [
			
# 		{
# 			"account":self.account,
# 			"debit_in_account_currency":self.amount,
# 			"source_order" : self.source_order,
# 		},
# 		{
# 			"account":self.paid_from,
# 			"credit_in_account_currency":self.amount,	
# 			"source_order" : self.source_order,
# 		},
#    ]
# 		doc = frappe.get_doc({
# 		'doctype': 'Journal Entry',
# 		'voucher_type': 'Journal Entry',
# 		"posting_date" : self.date,
# 		"user_remark":self.remark,
# 		"accounts": account
		
# 		})
# 		doc.insert(ignore_permissions = True)
# 		doc.submit()
# 		self.journal_entry = doc.name
# 		self.save()
# 	def on_cancel(self):
# 		# frappe.throw(('This is an Error Message'))
# 		journal = frappe.get_doc("Journal Entry" , self.journal_entry)
# 		journal.cancel()
