import frappe
from his.api.ipd_bed_guard import lock_and_validate_bed_is_vacant

@frappe.whitelist()
def transfer_ip(self, service_unit, check_in, leave_from, inpatient_type):
    self = frappe.get_doc("Inpatient Record" , self)
    if leave_from:
        patient_leave_service_unit(self, check_in, leave_from)
    if service_unit:
        transfer_patient(self, service_unit, check_in, inpatient_type)

@frappe.whitelist()
def transfer_ip_bed(self, service_unit, check_in, leave_from, inpatient_type):
    ip_doc = frappe.get_doc("Inpatient Record", self)

    frappe.db.begin()
    try:
        # ✅ NEW: validate target bed before leaving old bed
        if service_unit:
            lock_and_validate_bed_is_vacant(service_unit, exclude_ip=ip_doc.name)

        if leave_from:
            patient_leave_service_unit(ip_doc, check_in, leave_from)

        if service_unit:
            transfer_patient(ip_doc, service_unit, check_in, inpatient_type)

        frappe.db.commit()
        return {"ok": 1}

    except Exception:
        frappe.db.rollback()
        raise


def transfer_patient(inpatient_record, service_unit, check_in, inpatient_type):
	item_line = inpatient_record.append("inpatient_occupancies", {})
	item_line.service_unit = service_unit
	item_line.check_in = check_in
	item_line.inpatient_type = inpatient_type
	inpatient_record.bed = service_unit
	inpatient_record.type = inpatient_type
	inpatient_record.room = frappe.db.get_value(
    "Healthcare Service Unit",
    service_unit,
    "service_unit_type"
)

	inpatient_record.save(ignore_permissions=True)

	frappe.db.set_value("Healthcare Service Unit", service_unit, "occupancy_status", "Occupied")


def patient_leave_service_unit(inpatient_record, check_out, leave_from):
	if inpatient_record.inpatient_occupancies:
		for inpatient_occupancy in inpatient_record.inpatient_occupancies:
			if inpatient_occupancy.left != 1 and inpatient_occupancy.service_unit == leave_from:
				inpatient_occupancy.left = True
				inpatient_occupancy.check_out = check_out
				frappe.db.set_value(
					"Healthcare Service Unit", inpatient_occupancy.service_unit, "occupancy_status", "Vacant"
				)
	inpatient_record.save(ignore_permissions=True)