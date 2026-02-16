# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.share import add, remove
from frappe.model.document import Document

class PatientHistory(Document):
	pass


@frappe.whitelist()
def refer(inpatient_record, practitioner):
	inpatient_rec = frappe.get_doc('Inpatient Record', inpatient_record)
	inpatient_rec.primary_practitioner = practitioner
	inpatient_rec.admission_practitioner = practitioner
	inpatient_rec.secondary_practitioner = practitioner
	inpatient_rec.discharge_practitioner = practitioner
	inpatient_rec.save(ignore_permissions=1 )
	
	return "Refered Successfully"

@frappe.whitelist()
def share(patient, practitioner, doctype, access):
    user = frappe.db.get_value("Healthcare Practitioner", practitioner, 'user_id')
    inpatient_record = frappe.db.get_value("Inpatient Record", {'patient': patient, 'status': 'Admitted'}, 'name')
    if access == "Give Access":
        add(doctype, inpatient_record, user, read=1, write=1)
        frappe.msgprint(f"You have Successfully Shared with {practitioner}")
    if access == "Remove Access":
        remove(doctype, inpatient_record, user)
        frappe.msgprint(f"You have removed Access for {practitioner}")
        
    
	
