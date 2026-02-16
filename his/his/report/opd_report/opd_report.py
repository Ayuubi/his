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
    # data = frappe.db.sql(f"""
    #     select  
    #     sum(q.paid_amount) as paid,      
    #     q.practitioner,
    #     q.department,         
    #     SUM(if(q.que_type = 'New Patient', 1, 0)) AS new,         
    #     SUM(if(q.que_type = 'Follow Up', 1, 0)) AS 'followup',
    #     SUM(if(q.que_type = 'Refer', 1, 0)) AS 'refer',         
    #     --  SUM(if(q.que_type = 'Revisit', 1, 0)) AS 'revisit',          
    #     SUM(if(que_type = 'New Patient', 1, 0)+if(q.que_type = 'Follow Up', 1, 0)+if(q.que_type = 'Refer', 1, 0)+if(q.que_type = 'Revisit', 1, 0)) as total,         
    #     SUM(if(q.status = 'Open', 1, 0)) AS 'open',         
    #     SUM(if(q.status = 'Closed', 1, 0)) AS 'closed' ,
    #      SUM(if(s.docstatus = 2, 1, 0)) AS 'cancelled'
    #      --   SUM(if(s.is_return  = 1, 1, 0)) AS 'return' 
    #     from `tabQue`  q
    #     left join `tabSales Invoice` s on q.sales_invoice = s.name

    #     WHERE date BETWEEN "{_from}" AND "{to}" 
    #     AND q.status != 'Canceled'
       
    #     and s.is_return = 0
    #     group by q.practitioner
    #     ;""", as_dict=1)
    data = frappe.db.sql(f"""
        SELECT
            SUM(q.paid_amount) AS paid,
            q.practitioner,
            q.department,
            SUM(IF(q.que_type = 'New Patient', 1, 0)) AS new,
            SUM(IF(q.que_type = 'Follow Up' OR COALESCE(q.follow_up, 0) = 1, 1, 0)) AS followup,
            SUM(IF(q.que_type = 'Refer', 1, 0)) AS refer,
            SUM(
                IF(q.que_type = 'New Patient', 1, 0)
                + IF(q.que_type = 'Refer', 1, 0)
                + IF(q.que_type = 'Revisit', 1, 0)
                + IF(q.que_type = 'Follow Up' OR COALESCE(q.follow_up, 0) = 1, 1, 0)
            ) AS total,
            SUM(IF(q.status = 'Open', 1, 0)) AS open,
            SUM(IF(q.status = 'Closed', 1, 0)) AS closed,
            SUM(IF(s.docstatus = 2, 1, 0)) AS cancelled
        FROM `tabQue` q
        LEFT JOIN `tabSales Invoice` s ON q.sales_invoice = s.name
        WHERE q.date BETWEEN %(from)s AND %(to)s
        AND q.status != 'Canceled'
        AND COALESCE(s.is_return, 0) = 0
        GROUP BY q.practitioner
    """, {"from": _from, "to": to}, as_dict=1)

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
        
        #   "return:Data:100",
        # "revisit:Data:100",
        "total:Data:100",
         "cancelled:Data:100",
        
        "closed:Data:110",
        "open:Data:100",
       
      
        
    ]

