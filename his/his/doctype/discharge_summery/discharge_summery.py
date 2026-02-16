# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from his.api.discharge import patient_clearance
from his.api.doctor_plan import set_so_values_from_db
from his.api.doctor_plan import enqueue_sales_orders
from frappe.utils import get_datetime, get_link_to_form, getdate, now_datetime, today

class DischargeSummery(Document):
    def on_submit(self):

        patient_clearance(self.patient , self.ref_practitioner , self.inpatient_record)
        if frappe.db.exists("Inpatient Record" , self.inpatient_record):
            inpatient_record = frappe.get_doc("Inpatient Record" , self.inpatient_record)
            if inpatient_record.status == "Admitted":
                inpatient_record.status = "Discharge Scheduled"
                check_out_inpatient(inpatient_record)
                inpatient_record.save()

    def before_validate(self):
        # frappe.msgprint("discharge order")
        set_so_values_from_db(self)
    def on_update(self):
        enqueue_sales_orders(self)
        event = "new_msg"
        frappe.publish_realtime(event)
    def on_update_after_submit(self):
        enqueue_sales_orders(self)
        

def check_out_inpatient(inpatient_record):
    if inpatient_record.inpatient_occupancies:
        for inpatient_occupancy in inpatient_record.inpatient_occupancies:
            if inpatient_occupancy.left != 1:
            
                frappe.db.set_value(
                    "Healthcare Service Unit", inpatient_occupancy.service_unit, "occupancy_status", "Discharge Ordered"
                )
