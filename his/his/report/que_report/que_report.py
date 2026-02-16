# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt


import frappe

def execute(filters=None):
	
	return get_columns(), get_data(filters)

def get_data(filters):
	
	_from ,to  = filters.get('from_date'), filters.get('to') 
	
	data = frappe.db.sql(f"""
	select 
	
	date,
	patient,
	patient_name, 
	practitioner ,
	paid_amount,
	status
	

from `tabQue`
where date between "{_from}" and "{to}" 
and status = "Open" 
and que_type="New Patient" 
and is_free="0" and department !="Emergency"
 ;""", as_dict = 1)
	
	for i in data:
		i["action"] = f"""<button style='padding: 3px; margin:-5px' class= 'btn btn-primary' onClick='renew("{i.name}")'>Renew</button>"""
		# frappe.errprint(data)
	return data
def get_columns():
	return [
	
		"Date: Date:120",
		"Patient:Link/Patient:100",
		"Patient Name:Data:220",
		"Practitioner:Link/Healthcare Practitioner:200", 
		"Paid Amount:110",
		"Status:Data:110",
		"Action:Data:110"
	
		
	]

