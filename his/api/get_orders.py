import frappe
from frappe.utils import pretty_date, now, add_to_date , getdate

defalts={}
userdata = {}
if frappe.db.exists('User Defaults', frappe.session.user):
    userdata=frappe.get_doc('User Defaults', frappe.session.user)
if userdata:
    for i in userdata.user_defaults:
        defalts[f'{i.doctype_party}'] = i.value

def has_role(user, role):
    roles = frappe.get_roles(user)
    return role in roles


# condition = ''
# if has_role(frappe.session.user , "Pharmacy"):
#     condition += "and so_type = 'Pharmacy'"
# elif has_role(frappe.session.user , "Cashier"):
#     condition += "and so_type = 'Cashiers'"
# if frappe.session.user == "Administrator":
#     condition = ''
@frappe.whitelist()
def get_opd_orders(currdate):
    condition = ''
    if has_role(frappe.session.user , "Pharmacy"):
        condition += "and so_type = 'Pharmacy'"
    elif has_role(frappe.session.user , "Cashier"):
        condition += "and so_type = 'Cashiers'"
    if frappe.session.user == "Administrator":
        condition = ''
        
 
    # frappe.errprint(condition)
 
    return frappe.db.sql(f""" Select name,
        patient, patient_name ,
        transaction_date,status,
        modified as modified,
        per_billed,
        ref_practitioner,total , grand_total
        from `tabSales Order`
        where  transaction_date='{currdate}' {condition}
         ORDER BY modified DESC """, as_dict=True
       
        )

@frappe.whitelist()
def get_dialysis(flowdate=None, date=None):
    filters = []

    # Check which date to filter by
    if flowdate:
        filters.append(f"flowdate = '{flowdate}'")
    if date:
        filters.append(f"date = '{date}'")  # Replace with the actual column name for work date

    # Create the WHERE clause
    filter_query = " AND ".join(filters) if filters else "1=1"  # Fallback to get all if no filters

    return frappe.db.sql(f"""
        SELECT name,
            patient,
            patient_name,
            date AS lastDate,
            flowdate AS Today,
            age,
            entry_weight,
            target_weight,
            exit_weight,
            practitioner
        FROM `tabDIALYSIS REPORT`
        WHERE {filter_query}
        ORDER BY modified DESC
    """, as_dict=True)

    
@frappe.whitelist()
def get_canteen_orders(currdate):
    condition = ''
    if has_role(frappe.session.user , "Pharmacy"):
        condition += "and so_type = 'Pharmacy'"
    elif has_role(frappe.session.user , "Cashier"):
        condition += "and so_type = 'Cashiers'"
    if frappe.session.user == "Administrator":
        condition = ''
        
 
    # frappe.errprint(condition)
 
    return frappe.db.sql(f""" Select name,
        customer, customer_name ,
        transaction_date,status,
        modified as modified,
        per_billed,
        ref_practitioner,total 
        from `tabSales Order`
        where source_order= "Canteen" and transaction_date='{currdate}' {condition}
         ORDER BY modified DESC """, as_dict=True
       
        )

@frappe.whitelist()
def get_que_em(currdate):

    return frappe.db.sql(f""" Select name,
        patient, patient_name ,
        date,
        department,   
        district,
        mobile,
        age,

        modified as modified
      
        from `tabQue`
        where department= "Emergency" and date='{currdate}' 
         ORDER BY modified DESC """, as_dict=True
       
        )



@frappe.whitelist()
def get_ipd_orders(currdate):
    condition = ''
    if has_role(frappe.session.user , "Pharmacy"):
        condition += "and so_type = 'Pharmacy'"
    elif has_role(frappe.session.user , "Cashier"):
        condition += "and so_type = 'Cashiers'"
    if frappe.session.user == "Administrator":
        condition = ''


    return frappe.db.sql(f""" Select name,
        patient, patient_name ,
        transaction_date,status,
        modified as modified,
        per_billed,
        ref_practitioner,total 
        from `tabSales Order`
        where source_order= "IPD" and transaction_date='{currdate}' {condition} 
        ORDER BY modified DESC """, as_dict=True
       
        )


@frappe.whitelist()
def get_em_orders(currdate):
    condition = ''
    if has_role(frappe.session.user , "Pharmacy"):
        condition += "and so_type = 'Pharmacy'"
    elif has_role(frappe.session.user , "Cashier"):
        condition += "and so_type = 'Cashiers'"
    if frappe.session.user == "Administrator":
        condition = ''


    return frappe.db.sql(f""" Select name,
        patient, patient_name ,
        transaction_date,status,
        modified as modified,
        per_billed,
        ref_practitioner,total 
        from `tabSales Order`
        where source_order= "E.R"  and transaction_date='{currdate}' {condition} 
        ORDER BY modified DESC """, as_dict=True
       
        )
