# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from his.api.create_inv import create_inv
from frappe.model.document import Document
from erpnext.stock.get_item_details import get_pos_profile
from his.api.make_invoice import make_sales_invoice_direct

class WalkingPatient(Document):
	def on_submit(self):
		pos_profile = get_pos_profile(self.company)
		mode_of_payment = frappe.db.get_value('POS Payment Method', {"parent": pos_profile.name},  'mode_of_payment')
		default_account = frappe.db.get_value('Mode of Payment Account', {"parent": mode_of_payment},  'default_account')
		# mode_of_payment = "Cash"
		
		customer = self.customer
		items = []
		empty_items = ""
		for item in self.items:

			items.append({
				"item_code" : item.item_code,
				"rate" : item.rate,
				"qty" : item.qty,
				"uom" : item.uom
			})

	
	
			
		
		
	
	
		sales_doc = frappe.get_doc({
			"doctype" : "Sales Order",
			"so_type": self.so_type,
			"transaction_date" : self.transaction_date,
			"customer": customer,
			"patient" : self.patient,
		
			"discount_amount" : self.discount_amount,
			
			"voucher_no" : self.name,
			"source_order" : "WP",
			"ref_practitioner" : self.ref_practitioner,
			"additional_discount_percentage": self.additional_discount_percentage,
			"items" : items,
		
		})
	
		sales_doc.insert()
		sales_doc.submit()
		sale_inv = make_sales_invoice_direct(sales_doc.name , self.paid_amount , mode_of_payment)
		frappe.msgprint('Billed successfully')
		self.sales_order  = sales_doc.name
		self.sales_invoice = sale_inv
		self.save()
		return sales_doc

	def on_cancel(self):
		if self.sales_invoice:
			

			sales_inv = frappe.get_doc("Sales Invoice" , self.sales_invoice)
			sales_inv.cancel()
		if self.sales_order:
			sales_order = frappe.get_doc("Sales Order" , self.sales_order)
			
			sales_order.cancel()
