import frappe
from frappe import _

def lock_and_validate_bed_is_vacant(service_unit: str, exclude_ip: str = None):
    if not service_unit:
        frappe.throw(_("Bed (Service Unit) is required."))

    # Lock bed row to avoid two users taking it at the same time
    su = frappe.db.sql("""
        SELECT name, occupancy_status
        FROM `tabHealthcare Service Unit`
        WHERE name=%s
        FOR UPDATE
    """, (service_unit,), as_dict=True)

    if not su:
        frappe.throw(_("Healthcare Service Unit {0} not found.").format(service_unit))

    if (su[0].get("occupancy_status") or "").strip().lower() == "occupied":
        frappe.throw(_("Bed {0} is already occupied.").format(service_unit))

    # Extra safety: block if active occupancy exists (even if occupancy_status is wrong)
    extra = "AND ip.name != %s" if exclude_ip else ""
    params = [service_unit] + ([exclude_ip] if exclude_ip else [])

    active = frappe.db.sql(f"""
        SELECT ip.name
        FROM `tabInpatient Occupancy` io
        INNER JOIN `tabInpatient Record` ip ON ip.name = io.parent
        WHERE io.service_unit = %s
          AND io.`left` = 0
          AND ip.status = 'Admitted'
          {extra}
        LIMIT 1
    """, tuple(params), as_dict=True)

    if active:
        frappe.throw(
            _("Bed {0} already has an active admitted patient (IP: {1}).")
            .format(service_unit, active[0]["name"])
        )
