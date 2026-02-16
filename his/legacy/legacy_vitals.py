from __future__ import annotations
import frappe
from frappe.utils import cint
from his.legacy.smartfinancial import fetch_patient_vitals, fetch_patient_meta

@frappe.whitelist()
def get_legacy_vitals(patient: str, limit: int = 500, refresh_cache: int = 0):
    p = frappe.get_doc("Patient", patient)
    legacy_no = (p.get("legacy_patient_number") or "").strip()

    if not legacy_no:
        return {"ok": False, "message": "Set Legacy Patient Number on this Patient.", "rows": []}

    limit = max(1, min(cint(limit), 2000))

    cache_key = f"legacy_vitals::{legacy_no}::{int(limit)}"

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

    rows = fetch_patient_vitals(legacy_no, limit=int(limit))
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
