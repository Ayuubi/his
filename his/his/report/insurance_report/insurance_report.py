# Copyright (c) 2022, Anfac Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate
from frappe.utils import add_to_date
from his.api.get_mode_of_payments import  mode_of_payments
def execute(filters=None):
  
  return get_columns(), get_data(filters)

def get_data(filters):
    company = frappe.defaults.get_global_default("company")
    _from, to, insurance_company = filters.get('from_date'), filters.get('to'), filters.get('customer')
    
    report_gl = frappe.get_doc("Report", "General Ledger")

    report_gl_filters = {
        "company": company,
        "party_type": "Customer",
        "party": [insurance_company], 
        "from_date": _from,
        "to_date": to,
        "group_by": "Group by Voucher (Consolidated)",
    }

    columns_gl, data_gl = report_gl.get_data(
        limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
    )
    
    patient_data = {}

    for i in data_gl:
        patient_name = i.get('against')  # Get patient name safely
        
        # Skip entries where patient is None or an empty string (likely a total row)
        if not patient_name:
            continue
        
        if patient_name not in patient_data:
            patient_data[patient_name] = {
                "debit": 0,
                "credit": 0,
                "against": insurance_company
            }
        
        patient_data[patient_name]["debit"] += i['debit']
        patient_data[patient_name]["credit"] += i['credit']
    
    # Convert patient data to a list for the report
    report_data = []
    total_debit = 0
    total_credit = 0

    for patient, data in patient_data.items():
        balance = data["debit"] - data["credit"]
        total_debit += data["debit"]
        total_credit += data["credit"]
        
        report_data.append({
            "insurance_company": data["against"],
            "patient": patient,
            "debit": data["debit"],
            "credit": data["credit"],
            "balance": balance,
        })

    
   

    return report_data


def get_columns():
    columns = [
        _("Insurance Company"),
        _("Patient"),
        _("Debit"),
        _("Credit"),
        _("Balance"),
    ]

    return columns




