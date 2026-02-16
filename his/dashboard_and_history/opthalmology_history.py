import frappe
from frappe.utils import getdate
from datetime import datetime # from python std library
from frappe.utils import add_to_date
years = add_to_date(getdate(), years=-1) 

@frappe.whitelist()
def get_history(patient , doc, from_date = "2019-01-01", to_date = getdate):
    data = frappe.db.get_list("Patient Encounter", filters =  {"patient": patient, "name": doc, "docstatus": ["!=", 2],  }, fields= ["name", "practitioner"])
   
    patient_history = []
  
    for patient_info in data:
        doc = frappe.get_doc('Patient Encounter', patient_info.name)
        patient_history.append(doc.as_dict())
        
    frappe.errprint(patient_history)
    report_html_data = frappe.render_template(
	"his/his/page/patient_information/patient_information.html",
        {

        "patient" : patient,
        "patient_name" : frappe.db.get_value("Patient", patient, "first_name"),
        "age": frappe.db.get_value("Patient", patient, "p_age"),
        "mobile": frappe.db.get_value("Patient", patient, "mobile"),
        "sex": frappe.db.get_value("Patient", patient, "sex"),
        "table": patient_history,
        }
	)

    
    return report_html_data

