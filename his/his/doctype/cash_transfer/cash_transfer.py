# Copyright (c) 2021, Rasiin and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from erpnext.accounts.utils import get_balance_on


class CashTransfer(Document):	

	def validate(self):
		self.validate_transfer_amount()
		self.validate_from_account_balance()

	def validate_transfer_amount(self):
		if not self.transferred_amount or self.transferred_amount <= 0:
			frappe.throw("Transferred Amount must be greater than zero.")

	def validate_from_account_balance(self):
		if not self.from_account:
			frappe.throw("From Account is required.")

		if not self.date:
			frappe.throw("Date is required.")

		balance = get_balance_on(
			account=self.from_account,
			date=self.date
		)

		if self.transferred_amount > balance:
			frappe.throw(
				f"Cannot transfer {frappe.format_value(self.transferred_amount, {'fieldtype': 'Currency'})}. "
				f"Available balance in account <b>{self.from_account}</b> is only "
				f"{frappe.format_value(balance, {'fieldtype': 'Currency'})}."
			)

	def on_submit(self):

		account = [
			
		{
			"account":self.to_account,
			"debit_in_account_currency":self.transferred_amount,
			
		},
		{
			"account":self.from_account,
			"credit_in_account_currency":self.transferred_amount,	
			
		},
   ]
		doc = frappe.get_doc({
		'doctype': 'Journal Entry',
		'voucher_type': 'Journal Entry',
		"posting_date" : self.date,
		"user_remark":self.remark,
		"accounts": account
		
		})
		doc.insert(ignore_permissions = True)
		doc.submit()
		self.journal_entry = doc.name
		self.save()
	def on_cancel(self):
		# frappe.throw(('This is an Error Message'))
		journal = frappe.get_doc("Journal Entry" , self.journal_entry)
		journal.cancel()
