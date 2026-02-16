# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt


from asyncio import Condition
import frappe

def execute(filters=None):
	
	return get_columns(), get_data(filters)

def get_data(filters):
    cond=''
    _from, to = filters.get('from_date'), filters.get('to')
    if not filters.department:
        cond= ""
    else:
         cond= f"and department= '{filters.department}' "  
    data = frappe.db.sql(f"""
        SELECT 
        date,
        count(*) as number,
        practitioner
        FROM `tabQue`
        WHERE date BETWEEN "{_from}" AND "{to}" {cond} Group by practitioner
        ;""", as_dict=1)

    # Add row number to each dictionary in the data list

    return data
	
def get_columns():
	return [
		
		"Date: Date:120",
		"Practitioner:Link/Healthcare Practitioner:200", 
		"Number:Data:110",
       
		
	
		
	]

