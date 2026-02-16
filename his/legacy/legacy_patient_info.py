import frappe
from .smartfinancial import search_patients, search_patients_paged


@frappe.whitelist()
def search_legacy_patients(q: str, limit: int = 50):
    q = (q or "").strip()
    if not q:
        return {"ok": False, "message": "Type Patient Number, Phone, or Name.", "rows": []}

    rows = search_patients(q, limit=int(limit))
    return {"ok": True, "q": q, "rows": rows}

import frappe

@frappe.whitelist()
def search_legacy_patients_paged(
    q: str = "",
    date_field: str = "LastVisited",
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_length: int = 50,
    sort_by: str = "LastVisited",
    sort_order: str = "DESC",
):
    data = search_patients_paged(
        q=q,
        date_field=date_field,
        date_from=date_from,
        date_to=date_to,
        page=int(page),
        page_length=int(page_length),
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return {"ok": True, **data}
    
@frappe.whitelist()
def resolve_patient_from_legacy(legacy_patient_number: str):
    legacy_no = (legacy_patient_number or "").strip()
    if not legacy_no:
        return {"ok": False, "message": "Missing legacy patient number."}

    patient = frappe.db.get_value("Patient", {"legacy_patient_number": legacy_no}, "name")
    if not patient:
        return {
            "ok": False,
            "message": f"No Patient found with legacy_patient_number = {legacy_no}",
            "legacy_patient_number": legacy_no,
        }

    return {"ok": True, "patient": patient, "legacy_patient_number": legacy_no}
