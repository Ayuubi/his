import imp


import frappe
@frappe.whitelist()
def get_blood_store_balance(patient = None):
    blood_bank = frappe.db.sql(""" 
     

            select * from `tabBlood Bank Bin` where docstatus = 1
       
         """ , as_dict = 1)
    
    result_dict = {}

    for item in blood_bank:
        patient = item["patient"]
        debit = item["store"]
        credit = item["withdraw"]
        patient_name = item['patient_name']
        blood_group = item['blood_group']
        
        if patient not in result_dict:
            result_dict[patient] = {"debit_total": debit, "credit_total": credit , "patient_name" : patient_name , "blood_group" : blood_group}
        else:
            result_dict[patient]["debit_total"] += debit
            result_dict[patient]["credit_total"] += credit

    # Output the result
    grouped   = [] 
    for patient, totals in result_dict.items():
        group = {}
        group['patient'] = patient
        group['patient_name'] = totals['patient_name']
        group['blood_group'] = totals['blood_group']
    
        debit_total = totals["debit_total"]
        credit_total = totals["credit_total"]
        group["units"] = debit_total - credit_total
        grouped.append(group)

    return grouped
    



# data = [
#     {"patient": "Test 1", "debit": 10, "credit": 0},
#     {"patient": "Test 2", "debit": 20, "credit": 0},
#     {"patient": "Test 1", "debit": 5, "credit": 0},
#     {"patient": "Test 1", "debit": 0, "credit": 6},
#     {"patient": "Test 2", "debit": 0, "credit": 10}
# ]



# print(grouped)