# Copyright (c) 2021, Rasiin and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document

class CashTransfer(Document):	
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
