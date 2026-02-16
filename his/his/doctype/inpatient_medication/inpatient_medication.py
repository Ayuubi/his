# Copyright (c) 2021, Rasiin and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


def update_doctor_plan(inpatient_medication):
    # Get the Doctor Plan document
    doctor_plan = frappe.get_doc('Doctor Plan', inpatient_medication.doctor_plan)

    if not doctor_plan:
        frappe.msgprint(f'No Doctor Plan found with name {inpatient_medication.doctor_plan}')
        return
    
    # Find the medication item in the Treatment Sheet child table of the inpatient medication document
    treatment_sheet = inpatient_medication.get('treatment_sheet')
    if not treatment_sheet:
        frappe.msgprint(f'No treatment sheet found for Inpatient Medication {inpatient_medication.name}')
        return

    for prescription in treatment_sheet:
        if prescription.drug:
            # Find the medication item in the Doctor Plan child table
            ipd_drug_prescription = doctor_plan.get('drug_prescription')
            if not ipd_drug_prescription:
                frappe.msgprint(f'No Drug Prescription found in Doctor Plan {doctor_plan.name}')
                continue

            medication_item = next((item for item in ipd_drug_prescription if item.drug_code == prescription.drug), None)

            if not medication_item:
                # frappe.msgprint(f'Medication {prescription.drug} not found in IPD Drug Prescription of Doctor Plan {doctor_plan.name}')
                continue

            # Update the "Used Qty" field in the Doctor Plan
            medication_item.used_qty += float( prescription.quantity)

    # Save the changes to the Doctor Plan
    doctor_plan.save()

    frappe.msgprint(f'Successfully updated Doctor Plan {doctor_plan.name}')



class InpatientMedication(Document):
	

	def on_submit(self):
		# Call function to update the Doctor Plan
		update_doctor_plan(self)


@frappe.whitelist()
def get_billed_items(patient):
    list_of_bills = frappe.db.get_list("Sales Invoice" , filters = {"patient" : patient, "so_type": "Pharmacy" , "docstatus" : 1 , "is_return" :0},pluck = "name")
    items_of_bills = frappe.db.get_all("Sales Invoice Item" , filters = {"parent" : ['in', list_of_bills] } , fields = ['item_code'])
    items = []
    # frappe.errprint(items_of_bills)
    for item in items_of_bills:
        items.append(item.item_code)
    return items