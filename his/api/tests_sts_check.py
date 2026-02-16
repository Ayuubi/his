import frappe
from frappe.utils import getdate
def create_tests_sts(dt , dn):
    doc = frappe.get_doc(dt , dn)
    if doc.patient:
        if frappe.db.exists("Tests Status Check" , {"patient" : doc.patient , "date" : getdate() , "practitioner" : doc.practitioner}):
            name = frappe.db.get_value("Tests Status Check" , {"patient" : doc.patient , "date" : getdate() , "practitioner" : doc.practitioner} , "name")
            pre_sts = frappe.get_doc("Tests Status Check" , name)
            pre_sts.append("refrence_test", {
                 "test_template" : dt,
                "test" : dn,
                "status" : "Not Ready"
                
            })
            pre_sts.save(ignore_permissions = 1)

        else:
            ts_doc = frappe.get_doc({
                "doctype" : "Tests Status Check",
                "patient" : doc.patient,
                "practitioner" : doc.practitioner,
                "date" : getdate(),
                "refrence_test" : [
                {
                "test_template" : dt,
                "test" : dn,
                "status" : "Not Ready"
                }
                ]
            })
            ts_doc.insert(ignore_permissions = 1)


    