import frappe
from frappe.utils import getdate

def enqueue_anaesthesia_sales_order(doc, method=None):
    create_anaesthesia_sales_order(doc)
    frappe.publish_realtime("new_msg")

def create_anaesthesia_sales_order(doc):
    # Load/create Sales Order
    so_name = doc.get("sales_order")
    if so_name:
        so = frappe.get_doc("Sales Order", so_name)
    else:
        so = frappe.new_doc("Sales Order")
        so.source_order = "Anaesthesia"

    # Header
    so.delivery_date = getdate()
    so.so_type = "Pharmacy"
    so.ref_practitioner = doc.practitioner
    so.anaesthetist = doc.anaesthetist  # your custom field

    # ✅ FIX: set patient fields on Sales Order
    so.patient = doc.patient
    # patient_name usually exists; set if field exists to avoid errors
    patient_name = frappe.db.get_value("Patient", doc.patient, "patient_name")
    if hasattr(so, "patient_name"):
        so.patient_name = patient_name

    customer = frappe.db.get_value("Patient", doc.patient, "customer")
    if not customer:
        frappe.throw("Please set a Customer linked to the Patient")
    so.customer = customer

    # Rebuild items from packages
    so.__updated_items = []

    add_anaesthesia_package_items_expanded(so, doc)

    # Keep only rebuilt rows (prevents duplicates on re-run)
    so.items = [r for r in so.get("items", []) if r.reference_dn in so.__updated_items]

    # Write summary/remarks
    # summary_text = "; ".join(package_summaries)
    # Use your custom field if you have it; otherwise use standard customer_remarks
    # if hasattr(so, "comment"):
    #     so.comment = summary_text
    # else:
    #     so.customer_remarks = summary_text

    if not so.items and not so.name:
        return

    so.flags.ignore_links = 1
    so.flags.ignore_validate_update_after_submit = 1
    so.flags.ignore_permissions = 1

    # If updating a submitted SO, temporarily draft it
    if so.name:
        so.db_set("docstatus", 0, update_modified=False)

    so.save()
    so.submit()

    if doc.get("sales_order") != so.name:
        doc.db_set("sales_order", so.name, update_modified=False)


def add_anaesthesia_package_items_expanded(so, doc):
    """
    Expands Package Template components into SO items.

    Anaesthesia:
      - packages_prescription (child table)
        expected: row.package, row.qty

    Package Template:
      - package_prescription (child rows): item, rate (optional), qty (optional)
    """
    for row in doc.get("packages_prescription") or []:
        if not row.package:
            continue

        pkg = frappe.get_doc("Package Template", row.package)
        pkg_qty = row.qty or 1

        item_bits = []

        for line in pkg.get("package_prescription") or []:
            # ✅ SKIP if disabled
            if getattr(line, "disabled", 0):
                continue

            if not line.item:
                continue

            # unique reference per anaesthesia-row + package-line
            ref = line.name

            so_item = find_or_create_so_item(so, ref)
            so_item.reference_dt = line.doctype
            so_item.reference_dn = ref

            so_item.item_code = line.item
            so_item.qty = pkg_qty * (getattr(line, "qty", None) or 1)

            # rate logic: take line.rate if exists else 0 (or pull from Item Price if you prefer)
            so_item.rate = (getattr(line, "rate", None) or 0)

            so.__updated_items.append(ref)
            item_bits.append(f"{line.item} x{so_item.qty}")


def find_or_create_so_item(so, reference_dn):
    for r in so.get("items", []):
        if r.reference_dn == reference_dn:
            return r
    return so.append("items", {})


def cancel_anaesthesia_sales_order(doc, method=None):
    if not doc.get("sales_order"):
        return
    so = frappe.get_doc("Sales Order", doc.sales_order)
    if so.docstatus == 1:
        so.cancel()
