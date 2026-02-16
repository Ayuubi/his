# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from his.api.inpatient_order import set_so_values_from_db
from his.api.inpatient_order import enqueue_sales_orders


def update_doctor_plan(inpatient_order):
	# Get the Doctor Plan document
	doctor_plan = frappe.get_doc('Doctor Plan', inpatient_order.doctor_plan)

	if not doctor_plan:
		# frappe.msgprint(f'No Doctor Plan found with name {inpatient_order.doctor_plan}')
		return
	
	# Find the medication item in the Inpatient Order child table of the inpatient medication document
	drug_prescription = inpatient_order.get('drug_prescription')
	if not drug_prescription:
		# frappe.msgprint(f'No drug prescription found for Inpatient Order {inpatient_order.name}')
		return

	# Find the medication items in the Doctor Plan child table
	ipd_drug_prescription = doctor_plan.get('drug_prescription')
	if not ipd_drug_prescription:
		frappe.msgprint(f'No Drug Prescription found in Doctor Plan {doctor_plan.name}')
		

	for prescription in drug_prescription:
		if prescription.drug_code:
			# Look for a medication item in the Doctor Plan child table that matches both the name and drug_code fields
			medication_item = next((item for item in ipd_drug_prescription if item.drug_code == prescription.drug_code), None)

			if not medication_item:
				# frappe.msgprint(f'Medication {prescription.drug_code} ({prescription.drug_name}) not found in Drug Prescription of Doctor Plan {doctor_plan.name}')
				continue

			# Update the "Ordered Qty" field in the Doctor Plan
			medication_item.ordered_qty += float(prescription.qty)

	# Save the changes to the Doctor Plan
	doctor_plan.save()

	frappe.msgprint(f'Successfully updated Doctor Plan {doctor_plan.name}')   


class InpatientOrder(Document):
	def before_validate(self):
		set_so_values_from_db(self)
	
	def on_update(self):
		enqueue_sales_orders(self)
	
	def on_update_after_submit(self):
		enqueue_sales_orders(self)

	def on_submit(self):
		pass
		# Call function to update the Doctor Plan
		# update_doctor_plan(self)














