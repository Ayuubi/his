# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from his.api.post_delivery import set_so_values_from_db
from his.api.post_delivery import enqueue_sales_orders
from frappe.model.document import Document

class PostDelivery(Document):
	def before_validate(self):
		set_so_values_from_db(self)
	
	def on_update(self):
		enqueue_sales_orders(self)
	
	def on_update_after_submit(self):
		enqueue_sales_orders(self)
