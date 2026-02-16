import frappe
from erpnext.stock.get_item_details import get_pos_profile
from his.api.get_mode_of_payments import mode_of_payments
@frappe.whitelist()
def make_invoice(doc, method=None):
	is_employee = doc.is_employee
	employee = doc.employee


	pos_profile = get_pos_profile(frappe.defaults.get_user_default("company"))
	d= frappe.get_doc('Healthcare Practitioner', doc.practitioner)
	pat= frappe.get_doc('Patient', doc.patient)
	mode_of_payment = frappe.db.get_value('POS Payment Method', {"parent": pos_profile.name},  'mode_of_payment')
	abbr = frappe.db.get_value("Company", frappe.defaults.get_user_default("company"), "abbr")
	cost_center = frappe.db.get_value("POS Profile", pos_profile.name, "write_off_cost_center")
	if doc.que_type != 'Refer' and doc.status != "Closed":
		if not doc.is_free and  not doc.follow_up and   doc.que_type !="Renew" and doc.que_type !="Revisit":
			is_insurance = doc.is_insurance
			paid_amount = doc.paid_amount
			
			# frappe.errprint(type(paid_amount))
			if is_insurance:
				doc.is_free = 0
				paid_amount = 0
			
			is_pos = 0
			if paid_amount:
				is_pos = 1
			if doc.is_free:
				is_pos = 1
				paid_amount = doc.doctor_amount
				mode_of_payment = 'Free'
			sales_doc = frappe.get_doc({
				"doctype" : "Sales Invoice",
				"patient" : doc.patient,
				"patient_name" : doc.patient_name,
				"customer" : frappe.db.get_value("Patient" , doc.patient, "customer"),
				"ref_practitioner" : doc.practitioner,
				"is_pos" : is_pos,
				"bill_to_employee" : is_employee,
				"employee" : employee,
				"is_insurance" : is_insurance,
				"is_free" : doc.is_free,
				"source_order": "OPD",
				"cost_center": cost_center,
				"pos_profile" : pos_profile.name,
				"posting_date" : frappe.utils.getdate(),
				"items": [{
							"item_code": d.op_consulting_charge_item,
							"item_name": d.op_consulting_charge_item,
							
							"qty": 1,
							"rate": d.op_consulting_charge,
							"amount": 1*d.op_consulting_charge,
				
							"doctype": "Sales Invoice Item"
				}],
				"payments" : [{
					"mode_of_payment" : doc.mode_of_payment,
					"amount" :paid_amount
				}]
			
			})
			sales_doc.insert(ignore_permissions=1)
			sales_doc.submit()
			doc.sales_invoice=sales_doc.name
			doc.save()
	
		
		# frappe.msgprint('Sales Invoice Created successfully')
		
		# if doc.is_free == 1 and doc.follow_up == 0 and  doc.is_insurance==0 and  doc.is_package==0:
		# 		sales_doc = frappe.get_doc({
		# 			"doctype" : "Sales Invoice",
		# 			"patient" : doc.patient,
		# 			"patient_name" : doc.patient_name,
		# 			"customer" : frappe.db.get_value("Patient" , doc.patient, "customer"),
		# 			"practitioner" : doc.practitioner,
		# 			"source_order": "PACKAGE",
		# 			"bill_to_employee" : is_employee,
		# 			"employee" : employee,
		# 			"is_pos" : 1,
		# 			"cost_center": mode_cost[1],
		# 			"pos_profile" : pos_profile.name,
		# 			"posting_date" : frappe.utils.getdate(),
		# 			"items": [{
		# 						"item_code": d.op_consulting_charge_item,
		# 						"item_name": d.op_consulting_charge_item,
								
		# 						"qty": 1,
		# 						"rate": d.op_consulting_charge,
		# 						"amount": 1*d.op_consulting_charge,
					
		# 						"doctype": "Sales Invoice Item"
		# 			}],
		# 			"payments" : [{
		# 				"mode_of_payment" : "Free",
		# 				"amount" : doc.paid_amount
		# 			}]
				
		# 		})
		# 		sales_doc.insert()
		# 		sales_doc.status= "Unpaid"
		# 		sales_doc.save()
		# 		sales_doc.submit()
		# 		doc.sales_invoice=sales_doc.name
		# 		frappe.msgprint('Sales Invoice Created successfully')
			
		# if doc.is_free==0 and doc.follow_up == 0 and  doc.is_insurance==1 and  doc.is_package==0:
		# 	sales_doc = frappe.get_doc({
		# 		"doctype" : "Sales Invoice",
		# 		"patient" : doc.patient,
		# 		"patient_name" : doc.patient_name,
		# 		"customer" : frappe.db.get_value("Patient" , doc.patient, "customer"),
		# 		"practitioner" : doc.practitioner,
		# 		"is_insurance" : 1,
		# 		"source_order": "PACKAGE",
		# 		"bill_to_employee" : is_employee,
		# 		"employee" : employee,
		# 		"is_pos" : 1,
		# 		"cost_center": mode_cost[1],
		# 		"pos_profile" : pos_profile.name,
		# 		"posting_date" : frappe.utils.getdate(),
		# 		"items": [{
		# 					"item_code": d.op_consulting_charge_item,
		# 					"item_name": d.op_consulting_charge_item,
							
		# 					"qty": 1,
		# 					"rate": d.op_consulting_charge,
		# 					"amount": 1*d.op_consulting_charge,
				
		# 					"doctype": "Sales Invoice Item"
		# 		}],
		# 		"payments" : [{
		# 			"mode_of_payment" : mode_cost,
		# 			"amount" : 0
		# 		}]
			
		# 	})
		# 	sales_doc.insert()
		# 	sales_doc.submit()
		# 	doc.sales_invoice=sales_doc.name
		# 	frappe.msgprint('Sales Invoice Created successfully')
		

# @frappe.whitelist()
# def make_invoice_patient_fee(doc, method=None):
# 	pos_profile = get_pos_profile(doc.company)
# 	patient_fee=frappe.db.get_single_value('Healthcare Settings', 'patient_ragistration_fee')
# 	currency=frappe.db.get_single_value('Healthcare Settings', 'currency')

	
# 	if patient_fee:
# 		invoice = frappe.get_doc({
# 			"doctype" : "Sales Invoice",
# 			"patient" : doc.first_name,
# 			"patient_name" : doc.first_name,
# 			"customer" : doc.first_name,
			
# 			"is_pos" : 1,
# 			"pos_profile" : pos_profile.name,
# 			"posting_date" : frappe.utils.getdate(),
# 			"items": [{
# 						"item_code": "Ragistration",
# 						"item_name": "Ragistration",
						
# 						"qty": 1,
# 						"rate": currency,
# 						"amount": 1*currency,
			
# 						"doctype": "Sales Invoice Item"
# 			}],
# 			"payments" : [{
# 				"mode_of_payment" : "Isfree",
# 				"amount" : currency
# 			}]
		   
# 		})
# 		invoice.insert()
# 		invoice.submit()
		
# 		frappe.msgprint('Sales Invoice Created successfully')


@frappe.whitelist()
def renew(name):
	old_que = frappe.get_doc("Que" , name)
	old_que.status = "Renewed"
	old_que.save()
	que = frappe.get_doc({
				"doctype" : "Que",
				"patient": old_que.patient,
				"patient_name" : old_que.patient_name,
				"gender" : old_que.gender,
				"age": old_que.age,
				"practitioner": old_que.practitioner,
				"practitioner_name": old_que.practitioner_name,
				"department" : old_que.department,
				
				"follow_up": 0,
				"is_free" : 0,
				"is_package" : 0,
				"date" : frappe.utils.getdate(),
				"que_type" : "Renew"			
				})
					            
	que.insert(ignore_permissions=1) 
	que.submit()