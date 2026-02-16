import frappe
@frappe.whitelist()
def make_uppercase(doc , method = None):
    if doc.first_name:
            doc.first_name = doc.first_name.upper()
            doc.mobile = doc.mobile_no 	 	