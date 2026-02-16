# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from his.api.ot_prepation import set_so_values_from_db
from his.api.ot_prepation import enqueue_sales_orders

class OTPrepartion(Document):
	def before_validate(self):
		set_so_values_from_db(self)
	
	def on_update(self):
		enqueue_sales_orders(self)
	def on_update_after_submit(self):
		enqueue_sales_orders(self)
	def on_submit(self):
		company = frappe.defaults.get_global_default("company")
		abbr = frappe.get_value("Company", company, "abbr")
		if self.consumable_items:
			items = []
			for item in self.consumable_items:
				items.append({
							"item_code" : item.item_code,
							"qty" : item.qty,
							
						})
			stock_ent = frappe.get_doc({
				"doctype" : "Stock Entry",
				"posting_date" : frappe.utils.nowdate(),
				"stock_entry_type": "Material Issue",
				# "company" : self.company,
				"from_warehouse": "Stores - "+abbr,
				"items" : items,
				})
			stock_ent.insert()
			stock_ent.submit()
