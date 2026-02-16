import frappe
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos
import frappe
from frappe import _
from frappe.utils import flt
from erpnext.controllers.sales_and_purchase_return import get_returned_qty_map_for_row

def update_served_status(sales_invoice_number, item_names, is_served_value):
    """
    This function updates the 'is_served' field for the given sales invoice items.
    :param sales_invoice_number: The sales invoice number.
    :param item_names: List of item names (lab tests or imaging).
    :param is_served_value: The value to set for the 'is_served' field (1 or 0).
    """
    if not item_names:
        return  # Skip if no items to update

    # Use parameterized queries to avoid SQL injection
    placeholders = ', '.join(['%s'] * len(item_names))  # Create placeholders for each item name
    
    # Update the served status
    frappe.db.sql("""
        UPDATE `tabSales Invoice Item`
        SET is_served = %s
        WHERE parent = %s AND item_name IN ({})
    """.format(placeholders), [is_served_value, sales_invoice_number] + item_names)


def update_lab_results_status(doc, method):
    sample_collection = frappe.get_doc("Sample Collection", doc.reff_collection)
    sales_invoice_number = sample_collection.reff_invoice
    
    # Collect lab test names
    lab_test_names = [doc.template] + [item.lab_test_name for item in doc.normal_test_items]
    
    # Update served status to 1 (served)
    update_served_status(sales_invoice_number, lab_test_names, 1)


def update_imaging_results_status(doc, method):
    sales_invoice_number = doc.reff_invoice
    item_name = doc.eximination
    
    # Update served status to 1 (served) for imaging result
    update_served_status(sales_invoice_number, [item_name], 1)


def handle_lab_result_cancellation(doc, method):
    sample_collection = frappe.get_doc("Sample Collection", doc.reff_collection)
    sales_invoice_number = sample_collection.reff_invoice
    
    # Collect lab test names
    lab_test_names = [doc.template] + [item.lab_test_name for item in doc.normal_test_items]
    
    # Update served status to 0 (not served) for cancelled lab results
    update_served_status(sales_invoice_number, lab_test_names, 0)


def handle_imaging_result_cancellation(doc, method):
    sales_invoice_number = doc.reff_invoice
    item_name = doc.eximination
    
    # Update served status to 0 (not served) for cancelled imaging results
    update_served_status(sales_invoice_number, [item_name], 0)



@frappe.whitelist()
def custom_make_sales_return(source_name, target_doc=None):
    return custom_make_return_doc("Sales Invoice", source_name, target_doc)
  

def custom_make_return_doc(doctype: str, source_name: str, target_doc=None):
    company = frappe.db.get_value("Delivery Note", source_name, "company")
    default_warehouse_for_sales_return = frappe.get_cached_value(
        "Company", company, "default_warehouse_for_sales_return"
    )

    def set_missing_values(source, target):
        doc = frappe.get_doc(target)
        doc.is_return = 1
        doc.return_against = source.name
        doc.set_warehouse = ""
        if doctype == "Sales Invoice" or doctype == "POS Invoice":
            doc.is_pos = source.is_pos

            # look for Print Heading "Credit Note"
            if not doc.select_print_heading:
                doc.select_print_heading = frappe.get_cached_value("Print Heading", _("Credit Note"))

        elif doctype == "Purchase Invoice":
            doc.select_print_heading = frappe.get_cached_value("Print Heading", _("Debit Note"))

        for tax in doc.get("taxes") or []:
            if tax.charge_type == "Actual":
                tax.tax_amount = -1 * tax.tax_amount

        if doc.get("is_return"):
            if doc.doctype == "Sales Invoice" or doc.doctype == "POS Invoice":
                doc.consolidated_invoice = ""
                doc.set("payments", [])
                for data in source.payments:
                    paid_amount = 0.00
                    base_paid_amount = 0.00
                    data.base_amount = flt(
                        data.amount * source.conversion_rate, source.precision("base_paid_amount")
                    )
                    paid_amount += data.amount
                    base_paid_amount += data.base_amount
                    doc.append(
                        "payments",
                        {
                            "mode_of_payment": data.mode_of_payment,
                            "type": data.type,
                            "amount": -1 * paid_amount,
                            "base_amount": -1 * base_paid_amount,
                            "account": data.account,
                            "default": data.default,
                        },
                    )
                if doc.is_pos:
                    doc.paid_amount = -1 * source.paid_amount
            elif doc.doctype == "Purchase Invoice":
                doc.paid_amount = -1 * source.paid_amount
                doc.base_paid_amount = -1 * source.base_paid_amount
                doc.payment_terms_template = ""
                doc.payment_schedule = []

        if doc.get("is_return") and hasattr(doc, "packed_items"):
            for d in doc.get("packed_items"):
                d.qty = d.qty * -1

        if doc.get("discount_amount"):
            doc.discount_amount = -1 * source.discount_amount

        if doctype != "Subcontracting Receipt":
            doc.run_method("calculate_taxes_and_totals")

    def update_item(source_doc, target_doc, source_parent):
        target_doc.qty = -1 * source_doc.qty

        if source_doc.serial_no:
            returned_serial_nos = get_returned_serial_nos(source_doc, source_parent)
            serial_nos = list(set(get_serial_nos(source_doc.serial_no)) - set(returned_serial_nos))
            if serial_nos:
                target_doc.serial_no = "\n".join(serial_nos)

        if source_doc.get("rejected_serial_no"):
            returned_serial_nos = get_returned_serial_nos(
                source_doc, source_parent, serial_no_field="rejected_serial_no"
            )
            rejected_serial_nos = list(
                set(get_serial_nos(source_doc.rejected_serial_no)) - set(returned_serial_nos)
            )
            if rejected_serial_nos:
                target_doc.rejected_serial_no = "\n".join(rejected_serial_nos)

        if doctype in ["Purchase Receipt", "Subcontracting Receipt"]:
            returned_qty_map = get_returned_qty_map_for_row(
                source_parent.name, source_parent.supplier, source_doc.name, doctype
            )

            if doctype == "Subcontracting Receipt":
                target_doc.received_qty = -1 * flt(source_doc.qty)
            else:
                target_doc.received_qty = -1 * flt(
                    source_doc.received_qty - (returned_qty_map.get("received_qty") or 0)
                )
                target_doc.rejected_qty = -1 * flt(
                    source_doc.rejected_qty - (returned_qty_map.get("rejected_qty") or 0)
                )

            target_doc.qty = -1 * flt(source_doc.qty - (returned_qty_map.get("qty") or 0))

            if hasattr(target_doc, "stock_qty"):
                target_doc.stock_qty = -1 * flt(
                    source_doc.stock_qty - (returned_qty_map.get("stock_qty") or 0)
                )
                target_doc.received_stock_qty = -1 * flt(
                    source_doc.received_stock_qty - (returned_qty_map.get("received_stock_qty") or 0)
                )

            if doctype == "Subcontracting Receipt":
                target_doc.subcontracting_order = source_doc.subcontracting_order
                target_doc.subcontracting_order_item = source_doc.subcontracting_order_item
                target_doc.rejected_warehouse = source_doc.rejected_warehouse
                target_doc.subcontracting_receipt_item = source_doc.name
            else:
                target_doc.purchase_order = source_doc.purchase_order
                target_doc.purchase_order_item = source_doc.purchase_order_item
                target_doc.rejected_warehouse = source_doc.rejected_warehouse
                target_doc.purchase_receipt_item = source_doc.name

        elif doctype == "Purchase Invoice":
            returned_qty_map = get_returned_qty_map_for_row(
                source_parent.name, source_parent.supplier, source_doc.name, doctype
            )
            target_doc.received_qty = -1 * flt(
                source_doc.received_qty - (returned_qty_map.get("received_qty") or 0)
            )
            target_doc.rejected_qty = -1 * flt(
                source_doc.rejected_qty - (returned_qty_map.get("rejected_qty") or 0)
            )
            target_doc.qty = -1 * flt(source_doc.qty - (returned_qty_map.get("qty") or 0))

            target_doc.stock_qty = -1 * flt(source_doc.stock_qty - (returned_qty_map.get("stock_qty") or 0))
            target_doc.purchase_order = source_doc.purchase_order
            target_doc.purchase_receipt = source_doc.purchase_receipt
            target_doc.rejected_warehouse = source_doc.rejected_warehouse
            target_doc.po_detail = source_doc.po_detail
            target_doc.pr_detail = source_doc.pr_detail
            target_doc.purchase_invoice_item = source_doc.name

        elif doctype == "Delivery Note":
            returned_qty_map = get_returned_qty_map_for_row(
                source_parent.name, source_parent.customer, source_doc.name, doctype
            )
            target_doc.qty = -1 * flt(source_doc.qty - (returned_qty_map.get("qty") or 0))
            target_doc.stock_qty = -1 * flt(source_doc.stock_qty - (returned_qty_map.get("stock_qty") or 0))

            target_doc.against_sales_order = source_doc.against_sales_order
            target_doc.against_sales_invoice = source_doc.against_sales_invoice
            target_doc.so_detail = source_doc.so_detail
            target_doc.si_detail = source_doc.si_detail
            target_doc.expense_account = source_doc.expense_account
            target_doc.dn_detail = source_doc.name
            if default_warehouse_for_sales_return:
                target_doc.warehouse = default_warehouse_for_sales_return
        elif doctype == "Sales Invoice" or doctype == "POS Invoice":
            returned_qty_map = get_returned_qty_map_for_row(
                source_parent.name, source_parent.customer, source_doc.name, doctype
            )
            target_doc.qty = -1 * flt(source_doc.qty - (returned_qty_map.get("qty") or 0))
            target_doc.stock_qty = -1 * flt(source_doc.stock_qty - (returned_qty_map.get("stock_qty") or 0))

            target_doc.sales_order = source_doc.sales_order
            target_doc.delivery_note = source_doc.delivery_note
            target_doc.so_detail = source_doc.so_detail
            target_doc.dn_detail = source_doc.dn_detail
            target_doc.expense_account = source_doc.expense_account

            if doctype == "Sales Invoice":
                target_doc.sales_invoice_item = source_doc.name
            else:
                target_doc.pos_invoice_item = source_doc.name

            if default_warehouse_for_sales_return:
                target_doc.warehouse = default_warehouse_for_sales_return

    def update_terms(source_doc, target_doc, source_parent):
        target_doc.payment_amount = -source_doc.payment_amount

    doclist = get_mapped_doc(
        doctype,
        source_name,
        {
            doctype: {
                "doctype": doctype,
                "validation": {
                    "docstatus": ["=", 1],
                },
            },
            doctype + " Item": {
                "doctype": doctype + " Item",
                "field_map": {"serial_no": "serial_no", "batch_no": "batch_no", "bom": "bom"},
                "postprocess": update_item,
                "condition": lambda doc: not doc.is_served
            },
            "Payment Schedule": {"doctype": "Payment Schedule", "postprocess": update_terms},
        },
        target_doc,
        set_missing_values,
    )

    doclist.set_onload("ignore_price_list", True)

    return doclist
  
# def get_returned_qty_map_for_row(return_against, party, row_name, doctype):
# 	child_doctype = doctype + " Item"
# 	reference_field = "dn_detail" if doctype == "Delivery Note" else frappe.scrub(child_doctype)

# 	if doctype in ("Purchase Receipt", "Purchase Invoice", "Subcontracting Receipt"):
# 		party_type = "supplier"
# 	else:
# 		party_type = "customer"

# 	fields = [
# 		"sum(abs(`tab{0}`.qty)) as qty".format(child_doctype),
# 	]

# 	if doctype != "Subcontracting Receipt":
# 		fields += [
# 			"sum(abs(`tab{0}`.stock_qty)) as stock_qty".format(child_doctype),
# 		]

# 	if doctype in ("Purchase Receipt", "Purchase Invoice", "Subcontracting Receipt"):
# 		fields += [
# 			"sum(abs(`tab{0}`.rejected_qty)) as rejected_qty".format(child_doctype),
# 			"sum(abs(`tab{0}`.received_qty)) as received_qty".format(child_doctype),
# 		]

# 		if doctype == "Purchase Receipt":
# 			fields += ["sum(abs(`tab{0}`.received_stock_qty)) as received_stock_qty".format(child_doctype)]

# 	# Used retrun against and supplier and is_retrun because there is an index added for it
# 	data = frappe.get_all(
# 		doctype,
# 		fields=fields,
# 		filters=[
# 			[doctype, "return_against", "=", return_against],
# 			[doctype, party_type, "=", party],
# 			[doctype, "docstatus", "=", 1],
# 			[doctype, "is_return", "=", 1],
# 			[child_doctype, reference_field, "=", row_name],
# 		],
# 	)

# 	return data[0]
