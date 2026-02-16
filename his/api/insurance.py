import frappe
@frappe.whitelist()
def insurance(doc, method=None):
	if doc.is_insurance:
		Journal = frappe.get_doc({
		"doctype" : "Journal Entry",
		"posting_date": doc.posting_date,
		"source_order": "OPD",
		"accounts": [{
		"account": doc.debit_to,
		"party_type": "Customer",
		"party" : frappe.db.get_value("Patient", doc.patient,"ref_insturance"),
		"debit_in_account_currency": doc.net_total,
		"doctype": "Journal Entry Account"
	
	
			},
			{
		"account": doc.debit_to,
		"party_type": "Customer",
		"party" : doc.customer,
		"credit_in_account_currency": doc.net_total,
		"doctype": "Journal Entry Account"
	
	
			}]
	
		})
		Journal.insert()
		Journal.submit()
