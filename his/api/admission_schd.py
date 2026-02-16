
import json

import frappe
from frappe import _
from frappe.desk.reportview import get_match_cond
from frappe.model.document import Document
from frappe.utils import get_datetime, get_link_to_form, getdate, now_datetime, today

from healthcare.healthcare.doctype.nursing_task.nursing_task import NursingTask
from healthcare.healthcare.utils import validate_nursing_tasks

@frappe.whitelist()
def schedule_inpatient(args):
    admission_order = json.loads(args)  # admission order via Encounter
    # frappe.errprint(admission_order)
    if (
        not admission_order
        or not admission_order["patient"]
        # or not admission_order["admission_encounter"]
    ):
        frappe.throw(_("Missing required details, did not create Inpatient Record"))


    existing_inpatient_record = frappe.get_all(
        "Inpatient Record",
        filters={
            "patient": admission_order["patient"],
            "status": ["in", ["Discharge Scheduled", "Admission Scheduled", "Admitted"]]
        },
        fields=["name", "status"]
    )
    
    # If an inpatient record with the specified status exists, show a message
    if existing_inpatient_record:
        # You can use the status of the first record, or just show one message
        current_status = existing_inpatient_record[0].status
        frappe.throw(
            _("This patient already has a record with the status: {0}.").format(current_status)
        )

    inpatient_record = frappe.new_doc("Inpatient Record")

    # Admission order details
    # set_details_from_ip_order(inpatient_record, admission_order)

    # Patient details
    patient = frappe.get_doc("Patient", admission_order["patient"])
    inpatient_record.patient = patient.name
    inpatient_record.patient_name = patient.patient_name
    inpatient_record.gender = patient.sex
    inpatient_record.blood_group = patient.blood_group
    inpatient_record.dob = patient.dob
    inpatient_record.mobile = patient.mobile
    inpatient_record.email = patient.email
    inpatient_record.phone = patient.phone
    inpatient_record.scheduled_date = today()
    inpatient_record.status = "Admission Scheduled"
    inpatient_record.admission_practitioner= admission_order["primary_practitioner"]
    inpatient_record.diagnose= admission_order["diagnosis"]
    inpatient_record.save(ignore_permissions=True)


@frappe.whitelist()
def cancel_admision(inp_doc):
    in_d = frappe.get_doc("Inpatient Record" , inp_doc)
    in_d.status = "Cancelled"
    in_d.save()


@frappe.whitelist()
def schedule_inpatient_enc(args):
	admission_order = json.loads(args)  # admission order via Encounter
	if (
		not admission_order
		or not admission_order["patient"]
		or not admission_order["admission_encounter"]
	):
		frappe.throw(_("Missing required details, did not create Inpatient Record"))

	inpatient_record = frappe.new_doc("Inpatient Record")
	patient = frappe.get_doc("Patient", admission_order["patient"])
	inpatient_record.patient = patient.name
	inpatient_record.patient_name = patient.patient_name
	inpatient_record.gender = patient.sex
	inpatient_record.blood_group = patient.blood_group
	inpatient_record.dob = patient.dob
	inpatient_record.mobile = patient.mobile
	inpatient_record.email = patient.email
	inpatient_record.phone = patient.phone
	inpatient_record.scheduled_date = today()
	inpatient_record.diagnose= admission_order["diagnosis"]
	inpatient_record.admission_encounter = admission_order["admission_encounter"]
	inpatient_record.admission_practitioner= admission_order["primary_practitioner"]
	inpatient_record.status = "Admission Scheduled"
	inpatient_record.insert(ignore_permissions=1)




