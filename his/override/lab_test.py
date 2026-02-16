import frappe
@frappe.whitelist()
def create_multiple(doctype, docname):
	frappe.msgprint("ahskhakuhsdkuaj")
	if not doctype or not docname:
		frappe.throw(
			_("Sales Invoice or Patient Encounter is required to create Lab Tests"),
			title=_("Insufficient Data"),
		)

	lab_test_created = False
	if doctype == "Sales Invoice":
		lab_test_created = create_lab_test_from_invoice(docname)
	elif doctype == "Patient Encounter":
		lab_test_created = create_lab_test_from_encounter(docname)

	if lab_test_created:
		frappe.msgprint(
			_("Lab Test(s) {0} created successfully").format(lab_test_created), indicator="green"
		)
	else:
		frappe.msgprint(_("No Lab Tests created"))
