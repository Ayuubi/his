# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
import fractions
from frappe.model.document import Document

class BloodRequestform(Document):
	def on_submit(self):
		# blood = frappe.new_doc("Blood Bank Withdraw")
		# frappe.msgprint("Tested")
		blood_with = frappe.get_doc(
			{
				"doctype" : "Blood Bank Withdraw",
				"patient" : self.patient,
				"patient_name" : self.patient_name,
				"date" : self.date,
				"ordering_doctor" : self.doctor_name,
				"requested_blood_product" : self.blood_group,
				"quantity" : self.units
			}
		)
		blood_with.insert(ignore_permissions = 1)
