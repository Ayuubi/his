# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt


from asyncio import Condition
import frappe

def execute(filters=None):
	
	return get_columns(), get_data(filters)

def get_data(filters):
    cond=''
    _from, to = filters.get('from_date'), filters.get('to')
    # if not filters.doctor:
    #     cond= ""
    # else:
    #      cond= f"and practitioner= '{filters.doctor}' "  
    data = frappe.db.sql(f"""
        select  
        sum(paid_amount) as paid,      
        practitioner,
        department,         
        SUM(if(que_type = 'New Patient', 1, 0)) AS new,         
        SUM(if(que_type = 'Follow Up', 1, 0)) AS 'followup',
        SUM(if(que_type = 'Refer', 1, 0)) AS 'refer',         
        --  SUM(if(que_type = 'Revisit', 1, 0)) AS 'revisit',          
        SUM(if(que_type = 'New Patient', 1, 0)+if(que_type = 'Follow Up', 1, 0)+if(que_type = 'Refer', 1, 0)+if(que_type = 'Revisit', 1, 0)) as total,         
        SUM(if(status = 'Open', 1, 0)) AS 'open',         
        SUM(if(status = 'Closed', 1, 0)) AS 'closed' 
                  
        from `tabQue`  

        WHERE date BETWEEN "{_from}" AND "{to}" 
        AND status != 'Canceled'
        group by practitioner
        ;""", as_dict=1)

    # Add row number to each dictionary in the data list
    for i, row in enumerate(data):
        row["no"] = i + 1
    frappe.errprint(data)
    return data
	
def get_columns():
   return [
        
        
        "Practitioner:Link/Healthcare Practitioner:350",
        "department:Data:100",
        "new:Data:100",
        "followup:Data:100",
        "refer:Data:100",
        # "revisit:Data:100",
        "total:Data:100",
        
        "closed:Data:110",
        "open:Data:100",
      
        
    ]

