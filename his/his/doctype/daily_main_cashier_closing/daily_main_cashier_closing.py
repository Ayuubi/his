# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DailyMaincashierClosing(Document):
	def on_submit(self):
		company = frappe.defaults.get_global_default("company")
		abbr = frappe.get_value("Company", company, "abbr")
		for i in self.accounts:
			# frappe.msgprint(str(i));
			Journal = frappe.get_doc({
			"doctype" : "Journal Entry",
			"posting_date": self.date,
			"accounts": [{
			"account": str(i.to),
			
			"debit_in_account_currency": i.amount,
			"doctype": "Journal Entry Account"
					
					
			},
			{
			"account": str(i.froms),
			"credit_in_account_currency": i.amount,
			"doctype": "Journal Entry Account"
					
					
			}]
					
			})
			Journal.insert()
			Journal.submit()
		# frappe.msgprint(str(abbr))
