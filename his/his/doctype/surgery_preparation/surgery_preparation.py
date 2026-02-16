# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt
import datetime
import frappe
from frappe.model.document import Document

class SurgeryPreparation(Document):
    def after_insert(self):
        if self.inpatient_record == "Admitted":
            ip_d = frappe.db.get_value("Patient",self.patient,"inpatient_record")
            if ip_d:
                frappe.db.set_value("Inpatient Record",ip_d,"inpatient_status","Ready to Surgery")

@frappe.whitelist() 
def make_ot_schedule(docname, method=None):
    current_datetime = datetime.datetime.now()
    doc = frappe.get_doc("Surgery Preparation", docname)
    ot_schedule = frappe.get_doc({
            'doctype': 'OT Schedule',
            'patient': doc.patient,
            "appointment_date" : current_datetime.date(),
            "appointment_time": current_datetime.time(),
            "company":frappe.defaults.get_user_default("company"),
            "practitioner": doc.consultant,
            "duration": 15,
            "procedure_template": doc.procedure,
            "status": "Scheduled"
            
            })
    ot_schedule.insert(ignore_permissions = True)


    
    if doc.inpatient_record == "Admitted":
            ip_d = frappe.db.get_value("Patient",doc.patient,"inpatient_record")

            if ip_d:
                frappe.db.set_value("Inpatient Record",ip_d,"inpatient_status","Transferred to OT")
    anasaethia = frappe.get_doc({
            'doctype': 'Anesthesia',
            'patient': doc.patient,
            
            
            })
    anasaethia.insert(ignore_permissions = True)
    
@frappe.whitelist()
def get_billed_items(patient):
    list_of_bills = frappe.db.get_list("Sales Invoice" , filters = {"patient" : patient , "docstatus" : 1 , "is_return" :0},pluck = "name")
    items_of_bills = frappe.db.get_all("Sales Invoice Item" , filters = {"parent" : ['in', list_of_bills] } , fields = ['item_code'])
    items = []
    # frappe.errprint(items_of_bills)
    for item in items_of_bills:
        items.append(item.item_code)
    return items