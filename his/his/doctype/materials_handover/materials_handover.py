# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MaterialsHandover(Document):
	def before_insert(self):
		self.from_nurse_user = frappe.session.user
@frappe.whitelist()
def materials_handover(docname):
	if docname:
		mh = frappe.get_doc("Materials Handover", docname)
		mh.to_nurse = frappe.session.user
		mh.save()
		mh.submit()
