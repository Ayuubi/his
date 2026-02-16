# Copyright (c) 2022, Anfac Tech and contributors
# For license information, please see license.txt

import frappe
from his.api.create_p_e import payment
from frappe.model.document import Document

class Pay(Document):
	def on_submit(self):
		# frappe.msgprint("ok")
		payments = payment(self.name,  dt = 'Pay')
		self.payment_entry = payments.name
		self.save()
	def on_cancel(self):
		if self.payment_entry:
			

			payments = frappe.get_doc("Payment Entry" , self.payment_entry)
			payments.cancel()
