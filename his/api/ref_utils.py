import frappe

def get_ref_invoice(source_doc):
	"""
	Return the Sales Invoice name related to this doc.
	- Sales Invoice: doc.name
	- Others (Hajj Screening): doc.ref_invoice / doc.reff_invoice
	"""
	if source_doc.doctype == "Sales Invoice":
		return source_doc.name

	return (
		getattr(source_doc, "ref_invoice", None)
		or getattr(source_doc, "reff_invoice", None)
		or ""
	)

def get_is_return(source_doc):
	"""
	Return is_return for both Sales Invoice and other doctypes.
	- Sales Invoice: doc.is_return
	- Others: read from ref invoice if exists
	"""
	if source_doc.doctype == "Sales Invoice":
		return int(getattr(source_doc, "is_return", 0) or 0)

	inv = get_ref_invoice(source_doc)
	if inv and frappe.db.exists("Sales Invoice", inv):
		return int(frappe.db.get_value("Sales Invoice", inv, "is_return") or 0)

	return 0

def resolve_sales_invoice_item(source_doc, item_row, invoice_name=None):
	"""
	Return Sales Invoice Item rowname or None.
	- If source_doc is Sales Invoice: item_row.name is already the SI Item rowname
	- Otherwise: map using invoice + item_code
	"""
	if source_doc.doctype == "Sales Invoice":
		return item_row.name

	inv = invoice_name or get_ref_invoice(source_doc)
	if not inv:
		return None

	item_code = getattr(item_row, "item_code", None) or getattr(item_row, "item", None)
	if not item_code:
		return None

	return frappe.db.get_value(
		"Sales Invoice Item",
		{"parent": inv, "item_code": item_code},
		"name"
	)
