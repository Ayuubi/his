# import frappe
# @frappe.whitelist()
# def credit_limit(doc , method =None):
#     his_settings = frappe.get_doc("HIS Settings", "HIS Settings")
#     if his_settings.credit_limit:
#         doc.append("credit_limits" , {
#             "company" : frappe.defaults.get_user_default("company"),
#             "credit_limit" : 0.01
#         })

import frappe

def credit_limit(doc, method=None):
    settings = frappe.get_single("HIS Settings")
    if not settings.credit_limit:
        return

    # set Allow Credit now
    doc.allow_credit = 1

    company = frappe.defaults.get_user_default("Company")
    if not company:
        return

    doc.append("credit_limits", {
        "company": company,
        "credit_limit": 0.01,
        "bypass_credit_limit_check": 1
    })
