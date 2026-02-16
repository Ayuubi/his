# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Request(Document):
	def on_submit(self):
		if self.status != "Rejected":
			items = []
			for item in self.items:
				
				items.append({
					"item_code" : item.item_code,
					"schedule_date" : self.schedule_date,
					"qty" : item.qty,
					# "stock_uom" : "Nos",

				})
			mat_req = frappe.get_doc({
				"doctype" : "Material Request",
				"material_request_type" : "Material Issue",
				"transaction_date" : frappe.utils.getdate(),
				"schedule_date" : frappe.utils.getdate(),
				"items" : items,
				"user" : self.user,
				"department" : self.department,
				"medical_department" : self.medical_department,
				"full_name" : self.full_name
			})
			mat_req.insert(ignore_permissions = 1)
		

