# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns, data =  get_columns(), get_data(filters)
	return columns, data
def get_data(filters):
	from_date ,to_date = filters.get('from_date'), filters.get('to_date')
	data = frappe.db.sql(f"""
		select

		`tabDoctor Plan`.`name`,`tabDoctor Plan`.`patient_name`,`tabDoctor Plan`.`ref_practitioner`,
		`tabIPD Drug Prescription`.`drug_code`,`tabIPD Drug Prescription`.`quantity`,`tabIPD Drug Prescription`.`used_qty`,`tabIPD Drug Prescription`.`ordered_qty`
		from `tabDoctor Plan`
		INNER JOIN `tabIPD Drug Prescription` ON `tabDoctor Plan`.`name` = `tabIPD Drug Prescription`.`parent`

		""" , as_dict = 1)
	return data 
def get_columns():
	columns = [
		{
			"label": _("Name"),
			"fieldtype": "Data",
			"fieldname": "name",
			
			"width": 100,
		},
		{
			"label": _("Patient Name"),
			"fieldtype": "Data",
			"fieldname": "patient_name",
			
			"width": 200,
		},
		{
			"label": _("Practitioner"),
			"fieldtype": "Data",
			"fieldname": "ref_practitioner",
			
			"width": 200,
		},
			{
			"label": _("Drug"),
			"fieldtype": "Data",
			"fieldname": "drug_code",
			
			"width": 200,
		},
	
		{
			"label": _("Quantity"),
			"fieldtype": "int",
			"fieldname": "quantity",
			
			"width": 100,
		},
		{
			"label": _("Ordered Qty"),
			"fieldtype": "int",
			"fieldname": "ordered_qty",
			
			"width": 100,
		},
		{
			"label": _("Used Qty"),
			"fieldtype": "int",
			"fieldname": "used_qty",
			
			"width": 100,
		},
	
	]
	return columns