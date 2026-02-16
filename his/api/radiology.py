from his.api.tests_sts_check import create_tests_sts
import frappe
from his.api.make_sample_collection import make_sample_collection

import frappe
from his.api.ref_utils import get_ref_invoice, get_is_return, resolve_sales_invoice_item

def create_radiolgy(doc, method=None):
	reff_invoice = get_ref_invoice(doc)
	is_return = get_is_return(doc)

	sample_collection = []

	for i in (doc.items or []):
		if frappe.db.exists("Radiology Template", {"item": i.item_code}, cache=True) and not is_return:

			rad_data = {
				"doctype": "Radiology",
				"patient": doc.patient,
				"eximination": frappe.db.get_value("Radiology Template", {"item": i.item_code}, "name"),
				"practitioner": getattr(doc, "ref_practitioner", None),
				"reff_invoice": reff_invoice,
				"source_order": getattr(doc, "source_order", None),
			}

			si_item = resolve_sales_invoice_item(doc, i, reff_invoice)
			if si_item:
				rad_data["sales_invoice_item"] = si_item

			rad_doc = frappe.get_doc(rad_data)
			rad_doc.insert(ignore_permissions=True)

			tok = token_numebr(rad_doc)
			rad_doc.db_set("token_no", tok)
			if hasattr(doc, "token_no") or frappe.db.has_column(doc.doctype, "token_no"):
				doc.db_set("token_no", tok)

		# your checkup logic stays (if you re-enable it), but use reff_invoice not doc.name

# def create_radiolgy(doc, method=None):
# 	is_return = 0
# 	reff_invoice = ""
# 	if doc.doctype == "Sales Invoice":
# 		reff_invoice = doc.name
# 		is_return = doc.is_return
	
# 	# frappe.msgprint()
# 	sample_collection = []
# 	radiology  = []
# 	for i in doc.items:
# 		# if i.item_group == "Imaging" or i.item_group == "ECG" or  i.item_group == "ECO" and not doc.is_return:
# 		if frappe.db.exists("Radiology Template", {"item": i.item_code}, cache=True)  and not is_return:
			
# 			# frappe.errprint(doc.patient)
# 			rad_doc = frappe.get_doc({
# 			'doctype': 'Radiology',
			
# 			'patient': doc.patient,
# 			# 'indication':i.comments,
# 			'eximination': frappe.db.get_value("Radiology Template" , {"item": i.item_code},"name"),
# 			'practitioner' : doc.ref_practitioner,
# 			'reff_invoice' : reff_invoice,
# 			'source_order' : doc.source_order,
			
# 			})
# 			if doc.doctype == "Sales Invoice":
# 				rad_data["sales_invoice_item"] = i.name
# 			# frappe.msgprint("OK")
# 			rad_doc.insert(ignore_permissions=True)
# 			tok = token_numebr(rad_doc)
# 			# frappe.msgprint("tok")
# 			rad_doc.token_no = tok
# 			rad_doc.save()
# 			doc.token_no = tok
# 			doc.save()
# 			# create_tests_sts(rad_doc.doctype , rad_doc.name)
# 		if i.item_group == "Checkup":
# 			checup_doc = frappe.get_doc("Package Template" , i.item_code)
# 			for check in  checup_doc.package_prescription:
# 				if check.item_group == "Imaging":
# 					rad_doc = frappe.get_doc({
# 					'doctype': 'Radiology',
					
# 					'patient': doc.patient,
# 					# 'indication':check.comments,
# 					'eximination': check.item,
# 					'practitioner' : doc.ref_practitioner,
# 					'reff_invoice' : doc.name,
# 					'source_order' : doc.source_order
# 					})
# 					# frappe.msgprint("OK")
# 					rad_doc.insert(ignore_permissions=True)
# 				if check.item_group == "Laboratory":
# 					sample_collection.append({"lab_test" : check.item })
# 	if len(sample_collection) > 0:
# 		make_sample_collection(doc ,method = None, items = sample_collection)



@frappe.whitelist()
def token_numebr(doc, method=None):
	# if not frappe.db.get_value('Radiology', doc.name, "name"):
		# if not frappe.get_doc("Patient Appointment", doc.name):
		# prac = doc.doctor
		# prac ="HLC-PRAC-2021-00002"
	date = doc.date
	b = frappe.db.sql(f""" select Max(token_no) as max from `tabRadiology` where date = '{date}'  ; """ , as_dict = True)
	num = b[0]['max'] 
	# frappe.msgprint(num)
	if num == None:
		num = 0
	
	# doc.token_no = int(num) + 1
	return int(num) + 1
		# doc.appointment_time = ""

@frappe.whitelist()
def make_cytology(doc, method=None):
	for i in doc.items:
		if i.item_group == "Cytology":
			obs = frappe.get_doc({
				'doctype': 'Cytology',
				'patient': doc.patient,
				'patient_name': doc.patient_name,
				"examination":   i.item_code
			})
			obs.insert(ignore_permissions = True)



@frappe.whitelist()
def create_checkup(doc , method =None):
	if i.item_group == "Checkup":
		pass