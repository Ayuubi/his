import frappe
import json 
@frappe.whitelist()
def ready(bed):
	if bed:
		frappe.db.set_value("Healthcare Service Unit", bed, "occupancy_status", "Vacant")	