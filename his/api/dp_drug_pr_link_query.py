import frappe
from frappe.model.db_query import DatabaseQuery

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def my_custom_query(doctype, txt, searchfield, start, page_len, filters):
        # Define your custom query logic here
    # frappe.msgprint(str(txt))
    condition = ""
    if txt:
        condition += f"and name LIKE '%{txt}%' or department LIKE  '%{txt}%'"
    query = frappe.db.sql(f"""
        SELECT name, department
        FROM `tabHealthcare Practitioner`
        WHERE status = "Active"  {condition}
      
    """)

    return query




    # frappe.msgprint(str(doctype))
    # if(doctype == "IPD Drug Prescription")
    # condition = ''
    
    # if filters:
    #     for key, value in filters.items():
    #         condition += f' {key} = "{value}" and'

    # if condition:
    #     condition = condition[:-3]
    # frappe.msgprint(str(filters))
    # # data =  frappe.db.sql(f"""
    # #     SELECT    name , department
    # #     FROM `tabHealthcare Practitioner`
    # #     where {condition}
       
   
                
    # #             """)
    # return {"data"}

    