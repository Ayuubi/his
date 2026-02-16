# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from erpnext.stock.get_item_details import get_pos_profile
from his.api.get_mode_of_payments import mode_of_payments
from frappe.model.document import Document

class BloodDoner(Document):
	def on_submit(self):
		doc=self
		if not doc.is_inpatient:
			pos_profile = get_pos_profile(frappe.defaults.get_user_default("company"))
			sales_doc = frappe.get_doc({
				"doctype" : "Sales Invoice",
				"patient" : doc.patient,
				"customer" : frappe.db.get_value("Patient" , doc.patient, "customer"),
				"pos_profile" : pos_profile.name,
				"posting_date" : frappe.utils.getdate(),
				"is_pos": 1,
				"items": [{
							"item_code": "Blood Doner",
							"qty": 1,
							"doctype": "Sales Invoice Item"
				}],
				"payments" : [{
					"mode_of_payment" : "cash",
					"amount" : doc.paid_amount
				}],
				
				"doner": "From Doner"
			
			})
			sales_doc.insert(ignore_permissions=1)
			sales_doc.submit()
		if  doc.is_inpatient:
			# pos_profile = get_pos_profile(frappe.defaults.get_user_default("company"))
			sales_doc = frappe.get_doc({
				"doctype" : "Sales Invoice",
				"patient" : doc.patient,
				"customer" : frappe.db.get_value("Patient" , doc.patient, "customer"),
				# "pos_profile" : pos_profile.name,
				"posting_date" : frappe.utils.getdate(),
				# "is_pos": 1,
				"items": [{
							"item_code": "Blood Doner",
							"qty": 1,
							"doctype": "Sales Invoice Item"
				}],
				"payments" : [{
					"mode_of_payment" : "cash",
					"amount" : doc.paid_amount
				}],
				
				"doner": "From Doner",
				"is_inpatient" : 1,
				"ref_patient" : doc.reff_patient
			
			})
			sales_doc.insert(ignore_permissions=1)
			sales_doc.submit()

