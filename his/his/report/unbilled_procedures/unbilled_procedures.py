
import frappe
from frappe import _

# Function to define the report columns
def get_detailed_columns():
    return [
        {"label": _("Sales Order"), "fieldname": "sn", "fieldtype": "Link", "options": "Sales Order", "width": 150},
        {"label": _("Transaction Date"), "fieldname": "transaction_date", "fieldtype": "Date", "width": 100},
        {"label": _("Patient"), "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 150},
        {"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 200},
        # {"label": _("Customer Group"), "fieldname": "customer_group", "fieldtype": "Data", "width": 200},
        {"label": _("Mobile No"), "fieldname": "mobile_no", "fieldtype": "Data", "width": 120},
        {"label": _("Practitioner"), "fieldname": "ref_practitioner", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 150},
        {"label": _("Medical Department"), "fieldname": "medical_department", "fieldtype": "Link", "options": "Medical Department", "width": 200},
        {"label": _("Service Name"), "fieldname": "item_code", "fieldtype": "Link", "options": "Clinical Procedure Template", "width": 250},
        {"label": _("Service Type"), "fieldname": "item_group", "fieldtype": "Data", "width": 120},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
        {"label": _("Quantity"), "fieldname": "qty", "fieldtype": "Int", "width": 100},
        {"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 100},
        # {"label": _("Sales Rate"), "fieldname": "sales_net_rate", "fieldtype": "Currency", "width": 100},
        # {"label": _("Discount"), "fieldname": "discount", "fieldtype": "Currency", "width": 100},
    ]


def execute(filters=None):
    filters = filters or {}
    columns = get_detailed_columns()

    # Build query WHERE conditions
    conditions = []
    if filters.get("patient"):
        conditions.append(f"S.patient = '{filters.get('patient')}'")
    if filters.get("practitioner"):
        conditions.append(f"S.ref_practitioner = '{filters.get('practitioner')}'")
    if filters.get("medical_department"):
        conditions.append(f"S.medical_department = '{filters.get('medical_department')}'")
    if filters.get("customer_group"):
        conditions.append(f"S.customer_group = '{filters.get('customer_group')}'")
    if filters.get("item_group"):
        conditions.append(f"R.item_group = '{filters.get('item_group')}'")
    if filters.get("procedure_name"):
        # If your field is actually R.name, adjust accordingly
        conditions.append(f"R.template = '{filters.get('procedure_name')}'")
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append(
            f"S.transaction_date BETWEEN '{filters.get('from_date')}' AND '{filters.get('to_date')}'"
        )

    query = f"""
        SELECT
            R.name as "procedure",
            S.name AS "sn",
            S.transaction_date AS "transaction_date",
            S.patient AS "patient",
            S.patient_name AS "patient_name",
            S.customer_group AS "customer_group",
            P.mobile_no AS "mobile_no",
            S.ref_practitioner AS "ref_practitioner",
            S.medical_department AS "medical_department",
            I.item_code AS "item_code",
            R.item_group AS "item_group",
            I.name as "sales_order_item",
            S.name as sales_order,
            CASE
                WHEN I.delivered_qty = 1 THEN 'Completed'
                WHEN I.delivered_qty = 0 THEN 'To Deliver and Bill'
                ELSE S.status
            END AS "status",
            I.qty AS "qty",
            ROUND(R.rate, 2) AS "rate"
        FROM `tabSales Order` S
        JOIN `tabSales Order Item` I ON S.name = I.parent
        JOIN `tabClinical Procedure Template` R ON I.item_code = R.name
        LEFT JOIN `tabPatient` P ON S.patient = P.name
        WHERE S.docstatus = 1 AND I.delivered_qty <> 1
            {f"AND {' AND '.join(conditions)}" if conditions else ''}
        ORDER BY S.transaction_date DESC
    """

    data = frappe.db.sql(query, as_dict=True)

    result = []
    for i in data:
        # Load the procedure template for this row
        pro = frappe.get_doc("Clinical Procedure Template", {"name": i.procedure})

        # --- Gather anesthesia items from the template child table dynamically ---
        # NOTE: If your child table field is named differently, change "_aneasthesia_prescription"
        child_rows = getattr(pro, "_aneasthesia_prescription", []) or []

        sum_of_anes = 0
        anesth_items = []

        for j in child_rows:
            # NOTE: If your fields are spelled "anesthesia" and not "aneasthesia", update below:
            item_code_field = getattr(j, "aneasthesia", None)
            amount_val = getattr(j, "amount", 0) or 0

            sum_of_anes += amount_val
            if item_code_field:
                anesth_items.append(item_code_field)

        # Expected rate from template + anesthesia amounts on template
        updated_rate = (i.rate or 0) + (sum_of_anes or 0)

        # Base billed rate for the procedure SO line (linked via so_detail)
        rate_doc = None
        if frappe.get_all(
            "Sales Invoice Item",
            filters={"so_detail": i.sales_order_item, "docstatus": 1},
            limit=1,
        ):
            rate_doc = frappe.get_doc(
                "Sales Invoice Item",
                {"so_detail": i.sales_order_item, "docstatus": 1},
            )

        billed_base = rate_doc.net_rate if rate_doc else 0

        # --- Dynamically add **all** invoice items that match anesthesia items for this SO ---
        dynamic_addons_net = 0
        if anesth_items:
            # Fetch all matching SI Items for this sales order where item_code in anesth_items
            addon_rows = frappe.get_all(
                "Sales Invoice Item",
                filters=[
                    ["Sales Invoice Item", "sales_order", "=", i.sales_order],
                    ["Sales Invoice Item", "item_code", "in", anesth_items],
                    ["Sales Invoice Item", "docstatus", "=", 1],
                ],
                fields=["name", "net_rate"],
            )
            dynamic_addons_net = sum((row.get("net_rate") or 0) for row in addon_rows)

        # Final billed rate = base billed + any dynamic anesthesia invoice lines
        billed_rate = (billed_base or 0) + (dynamic_addons_net or 0)

        discount = 0
        if billed_rate:
            discount = updated_rate - billed_rate

        result.append({
            **i,
            "rate": round(updated_rate, 2),
            "sales_net_rate": round(billed_rate, 2),
            "discount": round(discount, 2),
        })

    return columns, result

