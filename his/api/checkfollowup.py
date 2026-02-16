import  frappe
from frappe.utils import getdate, nowdate

@frappe.whitelist()
def Check_follow_up(patient):
    today = getdate(nowdate())

    rows = frappe.db.get_all(
        "Fee Validity",
        filters={
            "patient": patient,
            "is_cancel": 0,
            # if you only want pending/active rows, uncomment:
            # "status": "Pending",
        },
        fields=["name", "patient", "practitioner", "start_date", "valid_till", "status"],
        order_by="valid_till desc, modified desc",
    )

    # Keep only latest row per practitioner
    seen = set()
    out = []
    for r in rows:
        pr = r.get("practitioner")
        if not pr:
            continue
        if pr in seen:
            continue
        seen.add(pr)
        out.append(r)

    return out
