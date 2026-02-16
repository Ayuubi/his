import frappe
def real(doc, method=None):
    event = "new_msg"
    # msg = {"content" : "This updated Encounter"}
    frappe.publish_realtime(event)

