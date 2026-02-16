import frappe
from frappe.model.document import Document
from frappe.utils import nowdate

class VAExamination(Document):
    pass

@frappe.whitelist()
def create_eyeglass_prescription(va_exam_name: str):
    va = frappe.get_doc("VA Examination", va_exam_name)

    # 1) Fast existence check
    existing = frappe.db.get_value(
        "EyeGlass Prescription",
        {"source_va_examination": va.name},
        "name"
    )
    if existing:
        return {"doctype": "EyeGlass Prescription", "name": existing, "status": "exists"}

    # 2) Create new
    presc = frappe.new_doc("EyeGlass Prescription")
    presc.patient = getattr(va, "patient", None)
    if hasattr(presc, "date"):
        presc.date = nowdate()
    elif hasattr(presc, "posting_date"):
        presc.posting_date = nowdate()

    # backlink (must exist & be Unique per above)
    presc.source_va_examination = va.name

    # child rows
    r = presc.append("right_eye", {})
    if hasattr(r, "ucva"):
        r.ucva = getattr(va, "va", None)

    l = presc.append("left_eye", {})
    if hasattr(l, "ucva"):
        l.ucva = getattr(va, "va1", None)

    # 3) Insert with race-condition safety (catch unique violation)
    try:
        presc.insert()
    except (frappe.UniqueValidationError, frappe.DuplicateEntryError):
        # Another user clicked in the same moment — fetch the one that won
        name = frappe.db.get_value(
            "EyeGlass Prescription",
            {"source_va_examination": va.name},
            "name"
        )
        return {"doctype": "EyeGlass Prescription", "name": name, "status": "exists"}

    frappe.db.commit()
    return {"doctype": presc.doctype, "name": presc.name, "status": "created"}
