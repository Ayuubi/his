# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Recovery(Document):
	pass

	@frappe.whitelist()
	def accept(self,service_unit,leave_from,check_in,status, expected_discharge=None):
		frappe.db.set_value("Healthcare Service Unit", leave_from, "occupancy_status", "Vacant")
		frappe.db.set_value("Healthcare Service Unit", service_unit, "occupancy_status", "Occupied")
		self.service_unit=service_unit
		self.status="Accepted"
		self.save()
		# self.submit()
		# frappe.errprint(service_unit)

@frappe.whitelist()
def transfer(name,service_unit,patient,sex,status, practitioner,expected_discharge=None):
	frappe.db.set_value("Healthcare Service Unit", service_unit, "occupancy_status", "Vacant")
	# name.service_unit=service_unit
	inp = frappe.get_doc({
		'doctype': 'Inpatient Record',
		'patient': patient,
		"gender": sex,
		"admission_practitioner": practitioner,
		"primary_practitioner": practitioner,
		"medical_department" : frappe.db.get_value("Healthcare Practitioner", practitioner, "department"),
		"status":"Admission Scheduled"
		})
	inp.insert(ignore_permissions = True)
	
	# frappe.db.set_value("Recovery", name, "status", "Transferred")
	rec_doc = frappe.get_doc("Recovery" , name)
	rec_doc.status = "Transferred"
	rec_doc.submit()
	# frappe.errprint(name)
	
@frappe.whitelist()
def discharge(name,service_unit,patient,sex,status, practitioner,expected_discharge=None):
	frappe.db.set_value("Healthcare Service Unit", service_unit, "occupancy_status", "Vacant")
	# name.service_unit=service_unit
	inp = frappe.get_doc({
		'doctype': 'Inpatient Record',
		'patient': patient,
		"gender": sex,
		"admission_practitioner": practitioner,
		"primary_practitioner": practitioner,
		"status":"Discharge Scheduled",
		"medical_department" : frappe.db.get_value("Healthcare Practitioner", practitioner, "department")
		})
	inp.insert(ignore_permissions = True)
	# frappe.db.set_value("Recovery", name, "status", "Transferred")
	rec_doc = frappe.get_doc("Recovery" , name)
	rec_doc.status = "Transferred"
	rec_doc.submit()