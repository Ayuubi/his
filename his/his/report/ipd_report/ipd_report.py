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
            patient,
            patient_name ,
           
            admission_practitioner,
            SUBSTRING(admitted_datetime, 1, 19) as admitted_datetime,
            SUBSTRING(discharge_datetime, 1, 19) as discharge_datetime,
            status 
            from  `tabInpatient Record` 

        WHERE creation BETWEEN "{_from}" AND "{to}" 
    
        ;""", as_dict=1)

    for i, row in enumerate(data):
        if row.status=="Discharged":
            row["status_"] = frappe.db.get_value("Discharge Summery", {"patient":row.patient} , "discharged_type")
    # frappe.errprint(data)

    return data
    
def get_columns():
    columns = [
        {
            "label": ("Patient"),
            "fieldtype": "Data",
            "fieldname": "patient_name",
            
            "width": 250,
        },
        {
            "label": ("Doctor"),
            "fieldtype": "Data",
            "fieldname": "admission_practitioner",
            
            "width": 250,
        },
           {
            "label": ("Status"),
            "fieldtype": "Data",
            "fieldname": "status",
            
            "width": 250,
        },
        {
            "label": ("Admission Date"),
            "fieldtype": "Data",
            "fieldname": "admitted_datetime",
            
            "width": 200,
        },
            {
            "label": ("Discharched Date"),
            "fieldtype": "Data",
            "fieldname": "discharge_datetime",
            
            "width": 200,
        },
    
        {
            "label": ("Discharched Status"),
            "fieldtype": "Data",
            "fieldname": "status_",
            
            "width": 150,
        }
    
    
    ]
    return columns