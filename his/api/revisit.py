import frappe;
from frappe.utils import (
    today,
    format_time,
    global_date_format,
    now,
    get_first_day,
)
@frappe.whitelist()
def que_revisit(que=None):
	# frappe.msgprint(str(que))
	
	pat= frappe.get_doc("Que",str(que))
	pe_name = frappe.db.get_value("Patient Encounter", 
	{'encounter_date':today(), 'patient': pat.patient}, "name")
	# doc= frappe.get_doc("Healthcare Practitioner",doctor)
	# frappe.msgprint(str(pat.patient_name))
	q = frappe.get_doc({
	"doctype" : "Revisit",
	"patient": pat.patient,
	"patient_name" : pat.patient_name,
	"gender" : pat.gender,
	"age": pat.age,
	"practitioner": pat.practitioner,
	"practitioner_name": pat.practitioner_name,
	"department" : pat.department,
	"follow_up": 1,
	"is_free" : 1,
	"is_package" : 0,
	"is_insurance" : 0,
	"date" : pat.date,
	"que_type" : "Revisit",
	"patient_encounter" : pe_name,

	
		
		            
	})
	# frappe.msgprint("haha")	            
	q.insert() 
	q.token_no = token_numebr(q)
	q.save()
	# q.submit()
	return q


def token_numebr(doc):
	# if not frappe.db.get_value('Revisit', doc.name, "name"):
		# if not frappe.get_doc("Patient Appointment", doc.name):
	prac = doc.practitioner
	# prac ="HLC-PRAC-2021-00002"
	appoinda = doc.date
	b = frappe.db.sql(f""" select Max(token_no) as max from `tabRevisit` where date = '{appoinda}' and practitioner = '{prac}'  ; """ , as_dict = True)
	num = b[0]['max'] 
	
	if num == None:
		num = 0
	
	token_no = int(num) + 1
	return token_no
		# doc.appointment_time = ""
	

@frappe.whitelist()
def Check_revisit(**args):
	patient=args.get("que")
	date =args.get("date")
	# frappe.msgprint(patient)
	doc=args.get("doctor")
	sql=frappe.db.sql(f""" select * from tabQue where name='{patient}' and date=current_date and status="Closed" """ ,  as_dict=True)
	# frappe.errprint(sql)
	return sql
