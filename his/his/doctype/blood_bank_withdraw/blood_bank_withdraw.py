# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class BloodBankWithdraw(Document):
	def on_submit(self):
		blood_bin = frappe.get_doc(
			{
				"doctype" : "Blood Bank Bin",
				"patient" : self.patient,
				# "donor" : self.donor,
				"blood_group" : self.blood_group,
				"units" :self.units,
				"date" : self.with_date,
				"document" : self.doctype,
				"document_name" : self.name,
				"withdraw" : self.units,
				"bag_nr" : self.bag_nr
			}
		)
		blood_bin.insert(ignore_permissions = 1)
		blood_bin.submit()

