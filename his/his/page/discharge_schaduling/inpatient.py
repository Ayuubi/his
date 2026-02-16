import frappe
@frappe.whitelist()
def transfer(**args):
	# frappe.db.set_value("Healthcare Service Unit", service_unit, "occupancy_status", "Vacant")
	# name.service_unit=service_unit
	inp = frappe.get_doc({
		'doctype': 'Inpatient Record',
		'patient': args.get('patient'),
		"admission_practitioner": args.get('practitioner'),
		"status":"Admission Scheduled"
		})
	inp.insert(ignore_permissions = True)