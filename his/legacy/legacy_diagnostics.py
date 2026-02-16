import frappe
from .smartfinancial import fetch_patient_diagnostics, fetch_patient_meta

@frappe.whitelist()
def get_legacy_diagnostics(patient: str, limit: int = 300, refresh_cache: int = 0):
    p = frappe.get_doc("Patient", patient)
    legacy_no = (p.get("legacy_patient_number") or "").strip()

    if not legacy_no:
        return {"ok": False, "message": "Set Legacy Patient Number on this Patient.", "rows": []}

    cache_key = f"legacy_dx::{legacy_no}::{int(limit)}"

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

    rows = fetch_patient_diagnostics(legacy_no, limit=int(limit))
    meta = fetch_patient_meta(legacy_no)

    payload = {
        "ok": True,
        "legacy_patient_number": legacy_no,
        "patient_meta": meta or {},
        "rows": rows or [],
        "cached": 0,
    }

    frappe.cache().set_value(cache_key, payload, expires_in_sec=60 * 10)
    return payload
