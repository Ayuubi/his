from erpnext.stock.get_item_details import get_pos_profile
import  frappe
from frappe.utils import getdate, nowdate
import datetime

@frappe.whitelist()
def make_fee_validity(doc, method=None):
	max_visit=frappe.db.get_single_value('Healthcare Settings', 'max_visits') or 1
	valid_days=frappe.db.get_single_value('Healthcare Settings', 'valid_days') or 1

	
	fee_validity = frappe.get_doc({
	"doctype" : "Fee Validity",
	"patient": doc.patient,
	"practitioner": doc.practitioner,
	"status" : "Pending",
	"max_visits" : max_visit,
	"visited": 0,
	"start_date" : doc.date,
	"valid_till" : getdate(doc.date) + datetime.timedelta(days=int(valid_days))
	
				
	})
				
	fee_validity.insert(ignore_permissions=1) 
	# fee_validity.submit()
	doc.fee_validity=fee_validity.name

# @frappe.whitelist()
# def make_que(patient ,practitioner ):
# 	# sql=frappe.db.sql(f""" select  patient, visited from `tabFee Validity` where patient='{patient}' and practitioner='{practitioner}';  """ ,  as_dict=True)
# 	# if sql:
# 	# 	frappe.db.sql(f""" update  `tabFee Validity` set visited=visited+1 where patient='{patient}' and practitioner='{practitioner}';  """ ,  as_dict=True)
# 	pre_fee  , no_of_pr_vis = frappe.db.get_value('Fee Validity', {'patient': patient , "practitioner" :practitioner}, ['name' , 'visited'])
# 	if pre_fee:
# 		frappe.db.set_value("Fee Validity" ,pre_fee ,'visited' , no_of_pr_vis + 1 )
# 	pat= frappe.get_doc("Patient",patient)
# 	doc= frappe.get_doc("Healthcare Practitioner",practitioner)

# 	que = frappe.get_doc({
# 	"doctype" : "Que",
# 	"patient": patient,
# 	"patient_name" : pat.patient_name,
# 	"gender" : pat.sex,
# 	"age": pat.dob,
# 	"practitioner": practitioner,
# 	"practitioner_name": doc.first_name,
# 	"department" : doc.department,
# 	"follow_up": 1,
# 	"paid_amount" : 0,

# 	"date" : frappe.utils.getdate(),
# 	"que_type" : "Follow Up"
	
		
		            
# 	})
            
# 	que.insert(ignore_permissions=1) 

@frappe.whitelist()
def make_que(patient, practitioner, que_date=None):
    que_date = getdate(que_date) if que_date else getdate(nowdate())

    fv = frappe.db.get_value(
        "Fee Validity",
        {"patient": patient, "practitioner": practitioner},
        ["name", "visited", "start_date", "valid_till"],
        as_dict=True
    )

    if not fv:
        frappe.throw("No Fee Validity found for this patient and practitioner.")

    start_date = getdate(fv.start_date)
    end_date = getdate(fv.valid_till)

    # must be inside FV window
    if que_date < start_date or que_date > end_date:
        frappe.throw(f"Selected date must be between {start_date} and {end_date}.")

    # no past date
    if que_date < getdate(nowdate()):
        frappe.throw("You cannot create a follow up Que in the past.")

    # ------------------------------------------------------------------
    # Prevent duplicates / wrong doctor on same day
    # ------------------------------------------------------------------
    # Prevent duplicate follow-up for SAME doctor on SAME day
    existing_name = frappe.db.get_value(
        "Que",
        {
            "patient": patient,
            "date": que_date,
            "follow_up": 1,
            "practitioner": practitioner,
            "docstatus": ["<", 2],  # Draft or Submitted
        },
        "name",
    )

    if existing_name:
        frappe.throw(
            f"Follow Up Que already created for this patient and doctor on {que_date}: {existing_name}"
        )


    # ------------------------------------------------------------------

    pat = frappe.get_doc("Patient", patient)
    doc = frappe.get_doc("Healthcare Practitioner", practitioner)

    que = frappe.get_doc({
        "doctype": "Que",
        "patient": patient,
        "patient_name": pat.patient_name,
        "gender": pat.sex,
        "age": pat.dob,
        "practitioner": practitioner,
        "practitioner_name": doc.first_name,
        "department": doc.department,
        "follow_up": 1,
        "paid_amount": 0,
        "date": que_date,
        "que_type": "Follow Up",
    })

    que.insert(ignore_permissions=1)

    # increment visited ONLY after success
    frappe.db.set_value("Fee Validity", fv.name, "visited", (fv.visited or 0) + 1)

    return que.name
