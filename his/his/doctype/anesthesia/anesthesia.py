# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Anesthesia(Document):
	def on_submit(self):
		if self.procedure_items:
			pro_items = []
			for item in self.procedure_items:
					pro_items.append({
						"item_code" : item.item_code,
						"qty" : item.qty
					})
			customer_to = frappe.db.get_value("Patient", self.patient, "customer")
			sales_doc = frappe.get_doc({
				"doctype" : "Sales Invoice",
				"posting_date" : frappe.utils.nowdate(),
				"customer": customer_to,
				"patient" : self.patient,
				"is_pos" : 0,
				"items" : pro_items,
				})
			sales_doc.insert(ignore_permissions = True)
			sales_doc.submit()
		
