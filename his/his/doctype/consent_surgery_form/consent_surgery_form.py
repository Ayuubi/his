# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ConsentSurgeryForm(Document):
	def after_insert(self):
		if self.surgery_preparation:
			surg_doc = frappe.get_doc("Surgery Preparation" , self.surgery_preparation )
			surg_doc.consent_form = self.name
			surg_doc.save()
