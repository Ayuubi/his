# Copyright (c) 2022, Rasiin and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DoctorPlan(Document):
	def after_insert(self):
		docname = frappe.db.get_value("Inpatient Record", {'status':'Admitted', 'patient': self.patient}, "name")
		ipr_data = frappe.get_doc("Inpatient Record" , docname)
		ipr_data.doctor_plan = self.name
		ipr_data.save()
	

	# def before_validate(self):
	# 	set_so_values_from_db(self)
	
	# def on_update(self):
	# 	enqueue_sales_orders(self)
	
	# def on_update_after_submit(self):
	# 	enqueue_sales_orders(self)

	
	




