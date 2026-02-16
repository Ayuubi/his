# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from his.api.make_sample_collection import make_sample_collection
from his.api.radiology import create_radiolgy

class HajjScreening(Document):
	def on_submit(self):
		if self.items:
			self.source_order = "OPD"
			create_radiolgy(self)
			make_sample_collection(self)
