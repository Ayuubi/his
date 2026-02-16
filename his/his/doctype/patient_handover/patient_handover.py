# Copyright (c) 2022, Rasiin and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PATIENTHANDOVER(Document):
	pass
	# def before_save(self):
	# 	pat= frappe.get_doc("Patient",self.patient)
	# 	frappe.db.get_value("Inpatient Record", {'status': 'Admitted', 'patient': self.patient}, 'name')
	# 	doc= frappe.get_doc("Inpatient Record",self.inpatient_record)
	# 	# frappe.errprint(doc.status)
	# 	if doc.status=="Admitted":
	# @frappe.whitelist()
	# def patietnt_handover():
	# 	data=frappe.db.get_value("Inpatient Record",  {'status': 'Admitted'})
	# 	frappe.errprint(data)




