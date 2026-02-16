# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.stock.get_item_details import get_pos_profile

class Advance(Document):
	
	def on_submit(self):
		pos_profile = get_pos_profile(frappe.defaults.get_user_default("company"))
		mode_of_payment = frappe.db.get_value('POS Payment Method', {"parent": pos_profile.name},  'mode_of_payment')
		default_account = frappe.db.get_value('Mode of Payment Account', {"parent": mode_of_payment},  'default_account')
		company_details = frappe.get_doc("Company" ,frappe.defaults.get_user_default("company"))
		payment_entry = frappe.get_doc({
        "doctype" : "Payment Entry",
        "payment_type" : "Receive",
        "posting_date" : self.date,
        "company" : frappe.defaults.get_user_default("company"),
        "party_type": "Customer",
        "party" : self.customer,
        "paid_from" : company_details.default_receivable_account,
        "paid_to": self.account,
        "received_amount": float(self.amount),
        "paid_amount": float(self.amount)
        
       
    	})
		payment_entry.insert(ignore_permissions=1)
		payment_entry.submit()
		self.payment_entry=payment_entry.name
		self.save()
	def on_cancel(self):
		if self.payment_entry:
			payments = frappe.get_doc("Payment Entry" , self.payment_entry)
			if payments.docstatus == 1 :
				payments.cancel()