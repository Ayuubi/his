# his/his/legacy/legacy_labs.py

import frappe
from .smartfinancial import fetch_patient_labs, fetch_patient_meta

# @frappe.whitelist()
# def get_legacy_labs(patient: str, limit: int = 500):
#     p = frappe.get_doc("Patient", patient)
#     legacy_no = p.get("legacy_patient_number")

#     if not legacy_no:
#         return {"ok": False, "message": "This Patient has no legacy_patient_number mapped yet.", "rows": []}

#     rows = fetch_patient_labs(legacy_no, limit=limit)
#     return {"ok": True, "legacy_patient_number": legacy_no, "rows": rows}


# @frappe.whitelist()
# def get_legacy_labs(patient: str, limit: int = 500, refresh_cache: int = 0):
#     p = frappe.get_doc("Patient", patient)
#     legacy_no = p.get("legacy_patient_number")

#     if not legacy_no:
#         return {"ok": False, "message": "Set Legacy Patient Number on this Patient.", "rows": []}

#     cache_key = f"legacy_labs::{legacy_no}::{int(limit)}"
#     if not int(refresh_cache):
#         cached = frappe.cache().get_value(cache_key)
#         if cached:
#             return {"ok": True, "legacy_patient_number": legacy_no, "rows": cached, "cached": 1}

#     rows = fetch_patient_labs(legacy_no, limit=int(limit))
#     frappe.cache().set_value(cache_key, rows, expires_in_sec=600)  # 10 mins
#     return {"ok": True, "legacy_patient_number": legacy_no, "rows": rows, "cached": 0}



@frappe.whitelist()
def get_legacy_labs(patient: str, limit: int = 500, refresh_cache: int = 0):
    p = frappe.get_doc("Patient", patient)
    legacy_no = (p.get("legacy_patient_number") or "").strip()

    if not legacy_no:
        return {"ok": False, "message": "Set Legacy Patient Number on this Patient.", "rows": []}

    cache_key = f"legacy_labs::{legacy_no}::{int(limit)}"

    if not int(refresh_cache):
        cached = frappe.cache().get_value(cache_key)
        if cached:
            return {
                "ok": True,
                "legacy_patient_number": legacy_no,
                "patient_meta": cached.get("patient_meta", {}),
                "rows": cached.get("rows", []),
                "cached": 1,
            }

    rows = fetch_patient_labs(legacy_no, limit=int(limit))
    meta = fetch_patient_meta(legacy_no)

    payload = {"rows": rows, "patient_meta": meta}
    frappe.cache().set_value(cache_key, payload, expires_in_sec=600)  # 10 mins

    return {
        "ok": True,
        "legacy_patient_number": legacy_no,
        "patient_meta": meta,
        "rows": rows,
        "cached": 0,
    }