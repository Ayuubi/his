# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from his.api.gyn import set_so_values_from_db
from his.api.gyn import enqueue_sales_orders
from frappe.model.document import Document

class GYN(Document):
	def before_validate(self):
		set_so_values_from_db(self)
	
	def on_update(self):
		enqueue_sales_orders(self)
	def on_update_after_submit(self):
		enqueue_sales_orders(self)
	def before_save(self):
		
		if self.que:
			if frappe.db.exists("Que" , self.que):
				old_que = frappe.get_doc("Que" , self.que)
				old_que.status = "Closed" 
				old_que.save()
@frappe.whitelist()
def transfer(**args):
	# frappe.db.set_value("Healthcare Service Unit", service_unit, "occupancy_status", "Vacant")
	# name.service_unit=service_unit
	inp = frappe.get_doc({
		'doctype': 'Inpatient Record',
		'patient': args.get('patient'),
		'diagnose': args.get('diagnose'),
		"admission_practitioner": args.get('practitioner'),
		"status":"Admission Scheduled"
		})
	inp.insert(ignore_permissions = True)
	frappe.db.set_value("GYN", args.get('name'), "status", "Transferred")


@frappe.whitelist()
def refer(**args):
    q = frappe.get_doc({
    "doctype" : "Que",
    "patient": args.get('patient'),
    "practitioner": args.get('practitioner'),
   
  
    # "emergency": args.get('name'),
    "date" : frappe.utils.getdate(),
    "que_type" : "Refer",
    "paid_amount" : 0
    
        
                    
    })           
    q.insert(ignore_permissions=1) 
