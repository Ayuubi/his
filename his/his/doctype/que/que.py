# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from his.api.Que_to_make_sales_invove import make_invoice
from his.api.Que_to_fee_validity import make_fee_validity
from his.api.que_token_number import token_numebr
from his.api.order_to_bill import create_que_order_bill
class Que(Document):
	def before_insert(self):
		# pass
		token_numebr(self)
	def on_update(self):
		event = "que_update"

		frappe.publish_realtime(event)

	def after_insert(self):
		if self.que_type != 'Refer' and not self.is_free and  not self.follow_up and   self.que_type !="Renew" and self.que_type !="Revisit"  and self.doctor_amount>0:
			create_que_order_bill(self)
		
		# pass
		# if self.que_type=="New Patient":
		make_fee_validity(self)
			
		# make_invoice(self)
			

	







