# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

from tokenize import group
import frappe
from frappe.model.document import Document

class BloodBankBin(Document):
	pass


@frappe.whitelist()
def get_blood_store_balance(patient = None):
	blood_bank = frappe.db.sql(""" 
	 

			select * from `tabBlood Bank Bin` where docstatus = 1
	   
	     """ , as_dict = 1)
	grouped_blood = []
	group = {}
	for blood in blood_bank:
		if blood.patient in group:
			if blood.withdraw:
				group[blood.patient] -= blood.withdraw
			if blood.store:
				group[blood.store] += blood.store
		else:
			if blood.withdraw:
				group[blood.patient] = blood.withdraw * -1
			if blood.store:
				group[blood.store] = blood.store 
	grouped_blood.push(group)
	frappe.errprint(grouped_blood)