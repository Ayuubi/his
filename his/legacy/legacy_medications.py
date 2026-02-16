import frappe
from .smartfinancial import fetch_patient_medications

@frappe.whitelist()
def get_legacy_medications(patient: str, limit: int = 800, refresh_cache: int = 0):
    p = frappe.get_doc("Patient", patient)
    legacy_no = (p.get("legacy_patient_number") or "").strip()

    if not legacy_no:
        return {"ok": False, "message": "Set Legacy Patient Number on this Patient.", "rows": []}

    cache_key = f"legacy_meds::{legacy_no}::{int(limit)}"

    if not int(refresh_cache):
        cached = frappe.cache().get_value(cache_key)
        if cached:
            return {
                "ok": True,
                "legacy_patient_number": legacy_no,
                "rows": cached.get("rows", []),
                "cached": 1,
            }

    rows = fetch_patient_medications(legacy_no, limit=int(limit))

    payload = {
        "ok": True,
        "legacy_patient_number": legacy_no,
        "rows": rows or [],
        "cached": 0,
    }

    frappe.cache().set_value(cache_key, payload, expires_in_sec=60 * 10)
    return payload
