import frappe
@frappe.whitelist()
def patient_clearance(patient , practitioner , inpatient_record):

	discharge = frappe.get_doc({
	"doctype" : "Discharge And Clearance",
	"patient": patient,
	"inpatient_record" : inpatient_record,
	"practitioner" :practitioner

	})
	discharge.insert()
	# discharge.submit()
	# frappe.msgprint("gooood")
