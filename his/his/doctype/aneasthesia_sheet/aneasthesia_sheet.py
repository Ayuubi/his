# Copyright (c) 2022, Rasiin and contributors
# For license information, please see license.txt
import time
import frappe
from frappe.model.document import Document

class AneasthesiaSheet(Document):
	def on_submit(self):
		frappe.db.set_value("Healthcare Service Unit", self.service_unit, "occupancy_status", "Vacant")
	# def after_insert(self):
		# time.sleep(5)
		# docdata = frappe.get_doc("OT Schedule" , self.ot_schedule)
		# docdata.status = 'Closed'
		# docdata.save()
		
		# clpro.save()
	@frappe.whitelist()
	def admit(self,service_unit=None, expected_discharge=None):
		if service_unit:
			frappe.db.set_value("Healthcare Service Unit", service_unit, "occupancy_status", "Occupied")
			self.service_unit=service_unit
			self.status = 'Admitted'
			self.save()
			clpro = frappe.get_doc({
			'doctype': 'Clinical Procedure',
			'patient': self.patient,
			"procedure_template": self.clinical_procedure,
			"ot_schedule": self.ot_schedule,
			"service_unit": self.service_unit,
			'practitioner': self.operative_doctor

			})
			clpro.insert(ignore_permissions = True)
@frappe.whitelist()
def transfer(service_unit,patient,clinical_procedure, practitioner):
		# docdata = frappe.get_doc("Aneasthesia Sheet" , docname)
		if service_unit:
			frappe.db.set_value("Healthcare Service Unit", service_unit, "occupancy_status", "Vacant")
			recovety = frappe.get_doc({
				'doctype': 'Recovery',
				'patient': patient,
				"procedure_template": clinical_procedure,
				"leave_from": service_unit,
				"practitioner": practitioner
				})
			recovety.insert(ignore_permissions = True)
		# docdata.status = 'Transferred'
		# docdata.save()




