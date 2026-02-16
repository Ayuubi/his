# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DailyCashierStatus(Document):
	def on_submit(self):
		company = frappe.defaults.get_global_default("company")
		abbr = frappe.get_value("Company", company, "abbr")
		dat=self.posting_date
		user=self.user
		debit=''
		credit=''
		acc=''
		for i in self.accounts:
			if i.account != 'Main Cashier - '+abbr:
				acc=i.account
				
			if i.credit_in_account_currency>0:
				# frappe.msgprint(str(i.credit_in_account_currency))
				Journal = frappe.get_doc({
				"doctype" : "Journal Entry",
				"posting_date": dat,
				"accounts": [{
				"account": "Main Cashier - "+abbr,
				
				"debit_in_account_currency": i.credit_in_account_currency,
				"doctype": "Journal Entry Account"
			
			
					},
					
					{
				"account": str(acc),
				"credit_in_account_currency": i.credit_in_account_currency,
				"source_order" : "Cashiers Closing",
				"doctype": "Journal Entry Account"
			
			
					}]
			
				})
				Journal.insert()
				Journal.submit()
				#frappe.db.sql(f""" update  `tabDaily casheir cash closing` set status='Approved' where owner='{user}' and posting_date='{dat}'; """ ,as_dict=True )
			   
				frappe.msgprint("Journal Entry Created Successfully!!");
				
