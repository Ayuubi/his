import frappe
from frappe import _
from frappe.utils import getdate
from frappe.model.mapper import map_doc


def set_so_values_from_db(doc, method=None):
    for so_type in ("medication_so", "services_so"):
        if not doc.get(so_type):
            doc.set(so_type, doc.db_get(so_type))


def enqueue_sales_orders(doc, method=None):
    
    create_sales_orders(doc=doc)
    event = "new_msg"
    # msg = {"content" : "This updated Encounter"}
    frappe.publish_realtime(event)
    


def create_sales_orders(doc):
    # if doc.fee_validity:
    #     if doc.fallow_up_days:
    #         start_date = frappe.db.get_value("Fee Validity" , doc.fee_validity , "start_date")
    #         start_date = frappe.utils.getdate(start_date)
    #         frappe.db.set_value("Fee Validity" , doc.fee_validity, "valid_till" ,frappe.utils.add_to_date(start_date , days = doc.fallow_up_days) )
    for so_type in ("medication_so", "services_so"):
        sales_order = None
        so_name = doc.get(so_type)
        if so_name:
            sales_order = frappe.get_doc("Sales Order", so_name)
            # frappe.msgprint(sales_order.per_billed)
            if sales_order.per_billed >= 100:
                # frappe.msgprint("did this")
                
                sales_order.per_billed = 20
                sales_order.status = "To Bill"
        else:
            sales_order = frappe.new_doc("Sales Order")
            sales_order.source_order="OPD"
            sales_order.ref_practitioner=doc.practitioner

        map_doc(
            doc,
            sales_order,
            {
                "GYN": {
                    "doctype": "Sales Order",
                    "field_no_map": ["source", "docstatus"],
                },
            },
        )

        sales_order.__updated_items = []
        sales_order.delivery_date = getdate()
        sales_order.customer = frappe.db.get_value("Patient", doc.patient, "customer")
        if not sales_order.customer:
            frappe.throw("Please set a Customer linked to the Patient")

        if so_type == "medication_so":
            # frappe.msgprint("ok")
            add_drug_items(sales_order, doc)
            sales_order.so_type = "Pharmacy"

        elif so_type == "services_so":
            # add_visit_charge(sales_order, doc)
            add_service_items(sales_order, doc)
            sales_order.so_type = "Cashiers"

        sales_order.items = [
            row
            for row in sales_order.get("items", default=[])
            if row.reference_dn in sales_order.__updated_items
        ]

        if not sales_order.items and not sales_order.name:
            continue

        sales_order.flags.ignore_links = 1
        sales_order.flags.ignore_validate_update_after_submit = 1
        sales_order.flags.ignore_permissions = 1
     

        if sales_order.name:
            if not sales_order.items:
                sales_order.reload()
                sales_order.cancel()
                doc.db_set(so_type, "", update_modified=False, notify=True)
                continue

            sales_order.db_set("docstatus", 0, update_modified=False)
        # if sales_order.status == "To Deliver":
        #     sales_order.per_billed = 50
        #     frappe.msgprint("To Deleiver")
        #     sales_order.status = "To Bill"
        sales_order.save()
        sales_order.submit()

        if so_name != sales_order.name:
            doc.db_set(so_type, sales_order.name, update_modified=False, notify=True)


def add_drug_items(so, doc):
    for child in ("drug_prescription"):
        for row in doc.get("drug_prescription"):
            so_item = find_or_create_item(row, so, doc)
            so_item.item_code = row.drug_code
            so_item.item_name = row.drug_name
            so_item.qty = row.qty
            if row.dosage:
                so_item.time = row.dosage

        # if frappe.db.get_value("Item", row.drug_code, "stock_uom") in (
        #     "Nos",
        #     "Each",
        #     "Pcs",
        # ):
        #     so_item.qty = row.get_quantity()

            so_item.description = row.drug_name
        # if row.dosage and row.period:
        #     so_item.description = _("{0} for {1}").format(row.dosage, row.period)





def add_service_items(so, doc):
    items=[]
    for child_table in ("lab_test_prescription", "procedure_prescription" , "radiology_prescription"):
        for row in doc.get(child_table):
            frappe.errprint(child_table)
            item, is_billable = get_item_and_is_billable(row)
            if not item or not is_billable:
                continue
            if child_table=="procedure_prescription":
                child= frappe.get_doc('Clinical Procedure Template', item)
                for i in child._aneasthesia_prescription:
                    so_item = find_or_create_item(i, so, doc , from_templae=True)
                    so_item.item_code = i.aneasthesia
                    so_item.rate=i.amount
                    so_item.qty = 1

                for i in child.lab_prescription:
                    so_item = find_or_create_item(i, so, doc , from_templae=True)
                    so_item.item_code = i.lab_test_code
                    so_item.qty = 1

            so_item = find_or_create_item(row, so, doc)
            so_item.item_code = item
            so_item.qty = 1


def get_item_and_is_billable(row):
    if row.doctype == "Lab Prescription":
        return frappe.get_cached_value(
            "Lab Test Template", row.lab_test_code, ("item", "is_billable")
        )
    elif row.doctype == "Procedure Prescription":
        return frappe.get_cached_value(
            "Clinical Procedure Template", row.procedure, ("item", "is_billable")
        )
    elif row.doctype == "Radiology Prescription":
        return frappe.get_cached_value(
            "Radiology Template", row.image, ("item", "is_billable")
        )
    elif row.doctype == "Hemodialysis Prescription":
        return frappe.get_cached_value(
            "Hemodialysis Templete", row.hemodialysis, ("item", "is_billable")
        )

def find_or_create_item(row, so, doc , from_templae = False):
    for item in so.get("items"):
        if item.reference_dn == row.name:
            break
    else:
        item = so.append("items")
        item.reference_dt = row.doctype
        item.reference_dn = row.name
    if from_templae:
        item.reference_dt = ""
        item.reference_dn = ""
    if doc.get("branch"):
        item.branch = doc.branch

    so.__updated_items.append(item.reference_dn)
    return item
@frappe.whitelist()
def close_que_after_save_pe(doc , method = None):
        if doc.que:
            if frappe.db.exists("Que" , doc.que):
                old_que = frappe.get_doc("Que" , doc.que)
                old_que.status = "Closed" 
                old_que.save()