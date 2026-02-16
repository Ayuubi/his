# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Packageprescription(Document):
	def after_insert(self):
		frappe.msgprint("shdlkj")
