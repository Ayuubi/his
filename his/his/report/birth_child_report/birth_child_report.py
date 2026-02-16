# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt


from asyncio import Condition
import frappe

def execute(filters=None):
    columns, data =  get_columns(), get_data(filters)
    return columns, data

def get_data(filters):
    cond=''
    _from, to = filters.get('from_date'), filters.get('to')
    
    #     cond= ""
    # else:
    #      cond= f"and practitioner= '{filters.doctor}' "  
    data = frappe.db.sql(f"""
            select 
			date,
			child_name,
			sex,
			type_of_birth,
			midwifery,
			mother
            from  `tabBirth Certificate` 

        WHERE date BETWEEN "{_from}" AND "{to}" 
    
        ;""", as_dict=1)



    return data
    
def get_columns():
    columns = [
        {
            "label": ("Birth Date"),
            "fieldtype": "Date",
            "fieldname": "date",
            
            "width": 200,
        },
        {
            "label": ("Child Name"),
            "fieldtype": "Data",
            "fieldname": "child_name",
            
            "width": 250,
        },
		{
            "label": ("Sex"),
            "fieldtype": "Data",
            "fieldname": "sex",
            
            "width": 100,
        },
		{
         "label": ("Type"),
            "fieldtype": "Data",
            "fieldname": "type_of_birth",
            
            "width": 100,
        }
		,
		{
            "label": ("Mother"),
            "fieldtype": "Data",
            "fieldname": "mother",
            
            "width": 250,
        },
		{
            "label": ("Midwifery"),
            "fieldtype": "Data",
            "fieldname": "midwifery",
            
            "width": 250,
        }
 
    
    
    ]
    return columns