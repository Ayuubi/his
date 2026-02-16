# from __future__ import annotations
# import frappe
# from his.legacy.smartfinancial import fetch_patient_meta

# @frappe.whitelist()
# def get_legacy_meta(patient: str):
#     p = frappe.get_doc("Patient", patient)
#     legacy_no = (p.get("legacy_patient_number") or "").strip()

#     if not legacy_no:
#         return {"ok": False, "message": "Set Legacy Patient Number on this Patient."}

#     meta = fetch_patient_meta(legacy_no) or {}
#     return {
#         "ok": True,
#         "legacy_patient_number": legacy_no,
#         "patient_meta": meta,
#     }


from __future__ import annotations
import frappe
from his.legacy.smartfinancial import fetch_patient_meta

@frappe.whitelist()
def get_legacy_meta(patient: str | None = None, legacy_no: str | None = None):
    legacy_no = (legacy_no or "").strip()

    # If legacy_no not provided, derive it from Patient docname
    if not legacy_no:
        if not patient:
            return {"ok": False, "message": "Pass patient (Patient docname) or legacy_no."}

        # patient is Patient docname here
        p = frappe.get_doc("Patient", patient)
        legacy_no = (p.get("legacy_patient_number") or "").strip()

    if not legacy_no:
        return {"ok": False, "message": "Set Legacy Patient Number on this Patient."}

    meta = fetch_patient_meta(legacy_no) or {}
    return {
        "ok": True,
        "legacy_patient_number": legacy_no,
        "patient_meta": meta,
    }
