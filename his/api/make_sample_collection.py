# import frappe;
# def make_sample_collection(doc, method=None , items = None):
# 	hajj_screening = ""
# 	if doc.doctype == "Hajj Screening":
# 		hajj_screening = doc.name
# 	reff_invoice = ""
# 	if doc.doctype == "Sales Invoice":
# 		reff_invoice = doc.name
# 	itms= []
# 	if items:
# 		itms = items
# 	else:   
# 		count=0
# 		for i in doc.items:
# 			if frappe.db.exists("Lab Test Template", i.item_code, cache=True):
# 			# if i.item_group == "Laboratory":
# 				count=count+1
# 				itms.append(
# 							{
# 							"lab_test": frappe.db.get_value("Lab Test Template", {"item":i.item_code},"name"),
# 							"department": frappe.db.get_value("Lab Test Template", {"item":i.item_code},"department"),

							
# 				}
# 				)
# 				if doc.doctype == "Sales Invoice":
# 					itms["sales_invoice_item"] = i.name

# 	if itms:
# 		sm_doc = frappe.get_doc({
# 			'doctype': 'Sample Collection',
# 			'sample_qty': 1,
# 			'practitioner':doc.ref_practitioner,
# 			'patient': doc.patient,
# 			'lab_test': itms,
# 			'reff_invoice' : reff_invoice,
# 			'source_order' : doc.source_order,
# 			# 'doner' : doc.doner,
# 			# "for_patient" : doc.ref_patient,
# 			# "blood_donar" : 1
# 			"hajj_screening" : hajj_screening
# 		})
# 		sm_doc.insert(ignore_permissions = True)
# 		sm_doc.lab_ref=sm_doc.name.split("-")[1]
# 		sm_doc.save()
# 		# if doc.ref_patient:
# 		#     blood_strore = 


import frappe
from his.api.ref_utils import get_ref_invoice, get_is_return, resolve_sales_invoice_item

def make_sample_collection(doc, method=None, items=None):
	hajj_screening = doc.name if doc.doctype == "Hajj Screening" else ""
	reff_invoice = get_ref_invoice(doc)
	is_return = get_is_return(doc)

	itms = []
	if items:
		# If items are passed in, keep them, but (optional) you can also map SI item here if needed
		itms = items
	else:
		for i in (doc.items or []):
			if frappe.db.exists("Lab Test Template", {"item": i.item_code}, cache=True):
				row = {
					"lab_test": frappe.db.get_value("Lab Test Template", {"item": i.item_code}, "name"),
					"department": frappe.db.get_value("Lab Test Template", {"item": i.item_code}, "department"),
				}

				# ✅ Works for both sources
				si_item = resolve_sales_invoice_item(doc, i, reff_invoice)
				if si_item:
					row["sales_invoice_item"] = si_item

				itms.append(row)

	# If you want to block creation on returns (optional)
	if not itms or is_return:
		return

	sm_doc = frappe.get_doc({
		"doctype": "Sample Collection",
		"sample_qty": 1,
		"practitioner": getattr(doc, "ref_practitioner", None),
		"patient": doc.patient,
		"lab_test": itms,
		"reff_invoice": reff_invoice,
		"source_order": getattr(doc, "source_order", None),
		"hajj_screening": hajj_screening
	})
	sm_doc.insert(ignore_permissions=True)
	sm_doc.lab_ref = sm_doc.name.split("-")[-1]
	sm_doc.save()



	
@frappe.whitelist()
def token_numebr(doc, method=None):
	if not frappe.db.get_value('Sample Collection', doc.name, "name"):
		date = doc.date
		b = frappe.db.sql(f""" select Max(token_no) as max from `tabSample Collection` where date = '{date}'  ; """ , as_dict = True)
		num = b[0]['max'] 
		if num == None:
			num = 0
		doc.token_no = int(num) + 1
		# last_col = frappe.db.sql("""SELECT lab_ref FROM `tabSample Collection` ORDER BY creation DESC LIMIT 1 """, as_dict=True)
		# if last_col and last_col[0].get('lab_ref'):
		#     doc.lab_ref = int(last_col[0]['lab_ref']) + 1
		# # col = frappe.get_last_doc("Sample Collection")
		# # if col:
		# #     if col.lab_ref:
		# #         doc.lab_ref = int(col.lab_ref) + 1