# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Insurance(Document):
	def before_save(self):

		doc = frappe.get_doc({
		    
		    "doctype" : "Customer",
		    "customer_name" : self.company_name,
		    "customer_type" : "Company",
		    "customer_group": self.company_group,
		    "territory": self.territory
		    
		})

		doc.insert()
		doc.submit()
