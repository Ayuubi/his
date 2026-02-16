# from healthcare.healthcare.doctype.inpatient_record.inpatient_record import admit_patient
import frappe
import json 
from his.api.ipd_bed_guard import lock_and_validate_bed_is_vacant


def admit_patient(inpatient_record, service_unit, check_in, inpatient_type, expected_discharge=None):
	# validate_nursing_tasks(inpatient_record)

	inpatient_record.admitted_datetime = check_in
	inpatient_record.status = "Admitted"
	inpatient_record.expected_discharge = expected_discharge

	inpatient_record.set("inpatient_occupancies", [])
	transfer_patient(inpatient_record, service_unit, check_in, inpatient_type)

	frappe.db.set_value(
		"Patient",
		inpatient_record.patient,
		{"inpatient_status": "Admitted", "inpatient_record": inpatient_record.name},
	)


def transfer_patient(inpatient_record, service_unit, check_in, inpatient_type):
	item_line = inpatient_record.append("inpatient_occupancies", {})
	item_line.service_unit = service_unit
	item_line.check_in = check_in
	item_line.invoiced = 1
	item_line.inpatient_type = inpatient_type

	inpatient_record.save(ignore_permissions=True)

	frappe.db.set_value("Healthcare Service Unit", service_unit, "occupancy_status", "Occupied")

@frappe.whitelist()
def  admit_p(inp_doc, service_unit,patient, type, practitioner, is_insurance = "", expected_discharge=None):
	ip_doc = frappe.get_doc("Inpatient Record" , inp_doc)
	frappe.db.set_value('Healthcare Service Unit', service_unit, 'patient',patient)
	ip_doc.bed=service_unit
	ip_doc.room=frappe.db.get_value("Healthcare Service Unit", service_unit , "service_unit_type")
	ip_doc.inpatient_status = "Admitted"
	ip_doc.type=type
	ip_doc.floor=frappe.db.get_value("Healthcare Service Unit Type", ip_doc.room , "floor")
	if practitioner:
		ip_doc.primary_practitioner = practitioner
		ip_doc.secondary_practitioner = practitioner
	# frappe.errprint(practitioner)
	ip_doc.save()

	if is_insurance:
		ip_doc.insurance = is_insurance
		ip_doc.save()
	check_in = frappe.utils.now()
	
	admit_patient(ip_doc , service_unit , check_in , type, expected_discharge)

	ip = ip_doc
	patientinfo = frappe.get_doc("Patient" , ip.patient)
	service_unit_type = frappe.get_doc("Healthcare Service Unit Type", frappe.db.get_value("Healthcare Service Unit", service_unit, "service_unit_type"))
	patient = ip.patient
	patient_name = ip.patient_name
	customer = patientinfo.customer
	item_code = service_unit_type.item
	rate = float(service_unit_type.rate)
	desc = service_unit_type.description
	remark = service_unit
	practitioner = ip.primary_practitioner
	medical_department = ip.medical_department
	# salesdoc = frappe.get_doc({

	# 			"patient": patient,
	# 			"patient_name": patient_name,
	# 			"customer" : customer,
	# 			"is_pos" : 0,
	# 			"so_type": "Cashiers",
	# 			"source_order" : "IPD",
	# 			"posting_date" : frappe.utils.getdate(),
	
	# 			'due_date' : frappe.utils.getdate(),
			
	# 			"remarks" : remark,
			   
			  
	# 			"doctype": "Sales Invoice",
	# 			"cost_center": "Main - DASSH",
		  
	# 			"ref_practitioner" : practitioner,
				
	# 			"items": [
	# 				{
	# 				"item_code": item_code,
	# 					"item_name": item_code,
	# 					"description": desc,
					 
	
	# 					"qty": 1,
	
	# 					"rate": rate/2,
	# 					"amount": 1*rate,
	
	
	
					  
	
	
		
	
	# 					"doctype": "Sales Invoice Item",
	
	# 				}
	# 			],
	
	# 		})
	# try:
	# 	salesdoc.insert()
	# 	salesdoc.submit()
	# except:
	# 	pass

	doc_plan = frappe.get_doc({
	"doctype" : "Doctor Plan",
	"patient": ip_doc.patient,
	"ref_practitioner" :ip_doc.admission_practitioner,
	"date": frappe.utils.getdate(),
	"room": frappe.db.get_value("Healthcare Service Unit", service_unit , "service_unit_type"),
	"bed" : service_unit

	

	})
	doc_plan.insert(ignore_permissions=True)

	
	
	# if frappe.db.get_value("Healthcare Service Unit", service_unit , "service_unit_type")=="ICU":
	# 	frappe.get_doc({
	# 		"doctype" : "ICU",
	# 		"patient": ip_doc.patient,
	# 		"practitioner" :ip_doc.primary_practitioner,
			

			

	# 		}).insert(ignore_permissions=True)
	# customer=frappe.get_doc("Customer",frappe.db.get_value("Patient",ip_doc.patient,"customer"))
	# customer.allow_credit=1
	# for row in customer.credit_limits:
	# 	row.credit_limit = 25000
	# customer.save()

@frappe.whitelist()
def admit_p_bed(inp_doc, service_unit, patient, type, practitioner, is_insurance="", expected_discharge=None):
    ip_doc = frappe.get_doc("Inpatient Record", inp_doc)

    frappe.db.begin()
    try:
        # ✅ NEW: validate bed server-side (prevents manual typing / double booking)
        lock_and_validate_bed_is_vacant(service_unit, exclude_ip=ip_doc.name)

        frappe.db.set_value("Healthcare Service Unit", service_unit, "patient", patient)

        ip_doc.bed = service_unit
        ip_doc.room = frappe.db.get_value("Healthcare Service Unit", service_unit, "service_unit_type")
        ip_doc.inpatient_status = "Admitted"
        ip_doc.type = type
        ip_doc.floor = frappe.db.get_value("Healthcare Service Unit Type", ip_doc.room, "floor")
        if practitioner:
            ip_doc.primary_practitioner = practitioner
            ip_doc.secondary_practitioner = practitioner

        if is_insurance:
            ip_doc.insurance = is_insurance

        ip_doc.save(ignore_permissions=True)

        check_in = frappe.utils.now()
        admit_patient(ip_doc, service_unit, check_in, type, expected_discharge)

        doc_plan = frappe.get_doc({
            "doctype": "Doctor Plan",
            "patient": ip_doc.patient,
            "ref_practitioner": ip_doc.admission_practitioner,
            "date": frappe.utils.getdate(),
            "room": frappe.db.get_value("Healthcare Service Unit", service_unit, "service_unit_type"),
            "bed": service_unit
        })
        doc_plan.insert(ignore_permissions=True)

        frappe.db.commit()
        return {"ok": 1}

    except Exception:
        frappe.db.rollback()
        raise


@frappe.whitelist()
def invoice_addition_beds(doc , method = None):
	return
	# frappe.msgprint("Ok")
	if frappe.db.exists("Inpatient Record" , doc.name):
		for i in doc.inpatient_occupancies:
			if not i.invoiced:
				ip = doc
				patientinfo = frappe.get_doc("Patient" , ip.patient)
	
				service_unit_type = frappe.get_doc("Healthcare Service Unit Type", frappe.db.get_value("Healthcare Service Unit", i.service_unit, "service_unit_type"))
				
				patient = ip.patient
				patient_name = ip.patient_name
				customer = patientinfo.customer
				item_code = service_unit_type.item
				rate = float(service_unit_type.rate)
				desc = service_unit_type.description
				remark = i.service_unit
				practitioner = ip.primary_practitioner
				medical_department = ip.medical_department
				salesdoc = frappe.get_doc({
			
							"patient": patient,
							"patient_name": patient_name,
							"customer" : customer,
							"is_pos" : 0,
							"so_type": "Cashiers",
							"source_order" : "IPD",
							"posting_date" : frappe.utils.getdate(),
				
							'due_date' : frappe.utils.getdate(),
						
							"remarks" : remark,
						
						
							"doctype": "Sales Invoice",
							"cost_center":  "Main - DASSH",
					
							"ref_practitioner" : practitioner,
							
							"items": [
								{
								"item_code": item_code,
									"item_name": item_code,
									"description": desc,
								
				
									"qty": 1,
				
									"rate": rate/2,
									"amount": 1*rate,
				
				
				
								
				
				
					
				
									"doctype": "Sales Invoice Item",
				
								}
							],
				
						})
				try:
					salesdoc.insert()
					salesdoc.submit()
					frappe.db.set_value("Inpatient Occupancy" ,i.name ,  "invoiced" , 1)
				except:
					pass
					
			
			