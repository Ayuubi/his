import frappe
from frappe import _
from frappe.utils import getdate
from frappe.model.mapper import map_doc
import datetime

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
    for so_type in ("medication_so", "services_so"):
        sales_order = None
        so_name = doc.get(so_type)
        if so_name:
            sales_order = frappe.get_doc("Sales Order", so_name)
            # frappe.msgprint(sales_order.per_billed)
            if sales_order.per_billed >= 100:
                # frappe.msgprint("did this")
                
                sales_order.sts = "New Item Added"
        else:
            sales_order = frappe.new_doc("Sales Order")
            sales_order.source_order="OPD"
            sales_order.ref_practitioner=doc.practitioner

        map_doc(
            doc,
            sales_order,
            {
                "Patient Encounter": {
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
    for child in ("drug_prescription", "billible_items"):
        if child== "drug_prescription":
            for row in doc.get("drug_prescription"):
                so_item = find_or_create_item(row, so, doc)
                so_item.item_code = row.drug_code
                so_item.item_name = row.drug_name
                so_item.qty = row.qty
        # elif child== "billible_items":
        #     for bill_row in doc.get("billible_items"):
        #         so_item = find_or_create_item(bill_row, so, doc)
        #         so_item.item_code = bill_row.item_code
        #         so_item.qty = bill_row.qty

        

        # if frappe.db.get_value("Item", row.drug_code, "stock_uom") in (
        #     "Nos",
        #     "Each",
        #     "Pcs",
        # ):
        #     so_item.qty = row.get_quantity()

   
        # if row.dosage and row.period:
        #     so_item.description = _("{0} for {1}").format(row.dosage, row.period)




def add_service_items(so, doc):
    items=[]
    for child_table in ("lab_test", "radiology_prescription"):
        for row in doc.get(child_table):
            item, is_billable = get_item_and_is_billable(row)
            if not item or not is_billable:
                continue
            if child_table=="procedure_prescription":
                child= frappe.get_doc('Clinical Procedure Template', item)
                for i in child._aneasthesia_prescription:
                    so_item = find_or_create_item(i, so, doc)
                    so_item.item_code = i.aneasthesia
                    so_item.rate=i.amount
                    so_item.qty = 1

                for i in child.lab_prescription:
                    so_item = find_or_create_item(i, so, doc)
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


def find_or_create_item(row, so, doc):
    for item in so.get("items"):
        if item.reference_dn == row.name:
            break
    else:
        item = so.append("items")
        item.reference_dt = row.doctype
        item.reference_dn = row.name

    if doc.get("branch"):
        item.branch = doc.branch

    so.__updated_items.append(item.reference_dn)
    return item






@frappe.whitelist() 
def make_ot_prepararion(doc, method=None):
    itms=[]
    imaging_items=[]
    procedure = ''
    papp=''
    for i in doc.items:
        if i.item_group == "OT":
            # papp = frappe.get_doc({
            #         'doctype': 'OT Schedule',
            #         'patient': doc.patient,
            #         "appointment_date" : doc.posting_date,
            #         "appointment_time": doc.posting_time,
            #         "company":frappe.defaults.get_user_default("company"),
            #         "practitioner": doc.ref_practitioner,
            #         "procedure_template": i.item_code,
            #         "duration": 15,
            #         })
            # papp.insert(ignore_permissions = True)
            if not frappe.db.exists("Inpatient Record", {"patient":doc.patient,"status":['!=', 'Discharged']}):

                admission_schedule = frappe.get_doc({
                        'doctype': 'Inpatient Record',
                        'patient': doc.patient,
                        "scheduled_date" : doc.posting_date,
                        "company":frappe.defaults.get_user_default("company"),
                        "admission_practitioner": doc.ref_practitioner,
                        "primary_practitioner": doc.ref_practitioner,
                        "status": "Admission Scheduled",
                        "procedure":i.item_code
                        })
                admission_schedule.insert(ignore_permissions = True)

            procedure = i.item_code
            for x in doc.items:
                if x.item_group == "Laboratory":
                      itms.append({
                        "test_name": x.item_code,
                        "test": x.item_code
                       })
            for z in doc.items:
                if z.item_group == "Imaging":
                      imaging_items.append({
                        "examination": z.item_code,
                        
                       })

    res_list = []

    for i in range(len(itms)):
        if itms[i] not in itms[i + 1:]:
            res_list.append(itms[i])

    if res_list and not imaging_items:
        ot_preparation=frappe.get_doc({
            "doctype": "OT Prepartion",
            "patient": doc.patient,
            "procedure_template" : procedure,
            "practitioner": doc.ref_practitioner,
            "lab_investigations": res_list,
            "reff_invoice": doc.name,
            # "ot_schedule": papp.name
            
        })
        ot_preparation.insert(ignore_permissions=True)

    if imaging_items and not res_list:
        ot_preparation=frappe.get_doc({
            "doctype": "OT Prepartion",
            "patient": doc.patient,
            "practitioner": doc.ref_practitioner,
            
               "procedure_template" : procedure,
            "imaging": imaging_items,
            "reff_invoice": doc.name,
            # "ot_schedule": papp.name
            
        })
        ot_preparation.insert(ignore_permissions=True)

    if res_list and imaging_items:
        ot_preparation=frappe.get_doc({
            "doctype": "OT Prepartion",
            "patient": doc.patient,
            "practitioner": doc.ref_practitioner,
               "procedure_template" : procedure,
            "lab_investigations": res_list,
            "imaging": imaging_items,
            "reff_invoice": doc.name,
            # "ot_schedule": papp.name
            
        })
        ot_preparation.insert(ignore_permissions=True)
    
    else:
        for i in doc.items:
            if i.item_group == "OT":
                ot_preparation=frappe.get_doc({
                "doctype": "OT Prepartion",
                "patient": doc.patient,
                "practitioner": doc.ref_practitioner,
                "procedure_template" : procedure,
                "lab_investigations": res_list,
                "imaging": imaging_items,
                "reff_invoice": doc.name,
                # "ot_schedule": papp.name
                
                })
                ot_preparation.insert(ignore_permissions=True)



@frappe.whitelist() 
def make_ot_schedule(docname, method=None):
    current_datetime = datetime.datetime.now()
    doc = frappe.get_doc("Inpatient Record", docname)
    ot_schedule = frappe.get_doc({
            'doctype': 'OT Schedule',
            'patient': doc.patient,
            "appointment_date" : current_datetime.date(),
            "appointment_time": current_datetime.time(),
            "company":frappe.defaults.get_user_default("company"),
            "practitioner": doc.primary_practitioner,
            "duration": 15,
            "procedure_template": doc.procedure,
            "status": "Scheduled"
            
            })
    ot_schedule.insert(ignore_permissions = True)