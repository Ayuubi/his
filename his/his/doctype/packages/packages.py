# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt
from erpnext.stock.get_item_details import get_pos_profile
import frappe
from frappe.model.document import Document

class Packages(Document):
	def before_save(self):
		items= []
		pos_profile = get_pos_profile(frappe.defaults.get_user_default("company"))	
		pat= frappe.get_doc("Patient",self.patient)
		doc= frappe.get_doc("Healthcare Practitioner",self.practitioner)
		pac= frappe.get_doc('Package Template', self.package)
		# frappe.msgprint("dacad")
		
		if not self.without_practitioner:
				for i in pac.package_prescription:
					items.append(
					{
						"item_code": i.item,
						'item' : i.item,
						'rate' : i.rate,
						'qty' : 1,
						'amount' : 1*i.rate
					
					}
					)
				items.append(
				    {
						"item_code": doc.op_consulting_charge_item,
				        'item' : doc.op_consulting_charge_item,
						'qty' : 1,
				        'rate' : doc.op_consulting_charge,
						'amount' : 1*doc.op_consulting_charge,
						"doctype": "Sales Invoice Item"
						
					
				    }
				    )
				# frappe.msgprint(str(items))
				que = frappe.get_doc({
				"doctype" : "Que",
				"patient_id": self.patient,
				"patient_name" : pat.patient_name,
				"gender" : pat.sex,
				"age": pat.dob,
				"doctor": self.practitioner,
				"doctor_name": doc.first_name,
				"department" : doc.department,
				
				"follow_up": 0,
				"is_free" : 0,
				"is_package" : 1,
				"date" : self.date,
				"que_type" : "New Patient"
				
					
								
				})
					            
				que.insert() 
				que.submit()
			
				sales_doc = frappe.get_doc({
					"doctype" : "Sales Invoice",
					"patient" : self.patient,
					"patient_name" : pat.patient_name,
					"customer" : pat.patient_name,
					"ref_practitioner" : self.practitioner,
					"is_pos" : 1,
					"cost_center": "Main - D",
					"source_order": "PACKAGE",
					"posting_date" : frappe.utils.getdate(),
					"items": items,
					"payments" : [{
						"mode_of_payment" : pos_profile.name,
						"amount" : self.paid_amount
					}]
				
				})
				sales_doc.insert()
				sales_doc.submit()
				
				self.sales_invoice=sales_doc.name
				self.total=self.package_amount+doc.op_consulting_charge
				
				# frappe.msgprint('Sales Invoice Created successfully')
				# frappe.errprint(pac.package_prescription)

		
		