# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import cint, flt, today


def execute(filters=None):
	filters = frappe._dict(filters or {})

	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns():
	return [
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 150,
		},
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Item Group"),
			"fieldname": "item_group",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 150,
		},
		{
			"label": _("Check in Group"),
			"fieldname": "check_in_group",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 160,
		},
		{
			"label": _("Request For / Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 180,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 150,
		},
		{
			"label": _("Actual Qty"),
			"fieldname": "actual_qty",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": _("Projected Qty"),
			"fieldname": "projected_qty",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Re-order Level"),
			"fieldname": "reorder_level",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Re-order Qty"),
			"fieldname": "reorder_qty",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Qty to Request"),
			"fieldname": "qty_to_request",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Stock UOM"),
			"fieldname": "stock_uom",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 100,
		},
		{
			"label": _("Material Request Type"),
			"fieldname": "material_request_type",
			"fieldtype": "Data",
			"width": 170,
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 140,
		},
	]


def get_data(filters):
	schema = get_item_reorder_schema()

	request_warehouse_expr = "ir.`{0}`".format(schema.request_warehouse_field)

	if schema.check_group_field:
		check_group_expr = "ir.`{0}`".format(schema.check_group_field)
	else:
		check_group_expr = "NULL"

	conditions = [
		"IFNULL(i.disabled, 0) = 0",
		"IFNULL(i.is_stock_item, 0) = 1",
		"ir.parenttype = 'Item'",
		"IFNULL({0}, '') != ''".format(request_warehouse_expr),
		"IFNULL(ir.warehouse_reorder_level, 0) > 0",
	]

	values = {}

	if filters.get("company"):
		conditions.append("w.company = %(company)s")
		values["company"] = filters.company

	if filters.get("warehouse"):
		conditions.append("{0} = %(warehouse)s".format(request_warehouse_expr))
		values["warehouse"] = filters.warehouse

	if filters.get("item_group"):
		conditions.append("i.item_group = %(item_group)s")
		values["item_group"] = filters.item_group

	if filters.get("material_request_type"):
		conditions.append(
			"IFNULL(ir.material_request_type, 'Purchase') = %(material_request_type)s"
		)
		values["material_request_type"] = filters.material_request_type

	if cint(filters.get("show_only_low_stock", 1)):
		conditions.append(
			"""(
				IFNULL(b.actual_qty, 0) <= IFNULL(ir.warehouse_reorder_level, 0)
				OR IFNULL(b.projected_qty, 0) <= IFNULL(ir.warehouse_reorder_level, 0)
			)"""
		)

	query = """
		SELECT
			i.name AS item_code,
			i.item_name AS item_name,
			i.item_group AS item_group,
			i.stock_uom AS stock_uom,
			{check_group_expr} AS check_in_group,
			{request_warehouse_expr} AS warehouse,
			w.company AS company,
			IFNULL(b.actual_qty, 0) AS actual_qty,
			IFNULL(b.projected_qty, 0) AS projected_qty,
			IFNULL(b.reserved_qty, 0) AS reserved_qty,
			IFNULL(b.ordered_qty, 0) AS ordered_qty,
			IFNULL(ir.warehouse_reorder_level, 0) AS reorder_level,
			IFNULL(ir.warehouse_reorder_qty, 0) AS reorder_qty,
			IFNULL(ir.material_request_type, 'Purchase') AS material_request_type
		FROM `tabItem Reorder` ir
		INNER JOIN `tabItem` i
			ON i.name = ir.parent
		LEFT JOIN `tabWarehouse` w
			ON w.name = {request_warehouse_expr}
		LEFT JOIN `tabBin` b
			ON b.item_code = i.name
			AND b.warehouse = {request_warehouse_expr}
		WHERE {conditions}
		ORDER BY
			{request_warehouse_expr} ASC,
			i.item_code ASC
	""".format(
		check_group_expr=check_group_expr,
		request_warehouse_expr=request_warehouse_expr,
		conditions=" AND ".join(conditions),
	)

	rows = frappe.db.sql(query, values, as_dict=True)

	data = []

	for row in rows:
		row = frappe._dict(row)

		row.actual_qty = flt(row.actual_qty)
		row.projected_qty = flt(row.projected_qty)
		row.reorder_level = flt(row.reorder_level)
		row.reorder_qty = flt(row.reorder_qty)

		row.status = get_status(
			actual_qty=row.actual_qty,
			projected_qty=row.projected_qty,
			reorder_level=row.reorder_level,
		)

		row.qty_to_request = get_qty_to_request(
			projected_qty=row.projected_qty,
			reorder_level=row.reorder_level,
			reorder_qty=row.reorder_qty,
		)

		data.append(row)

	return data


def get_status(actual_qty, projected_qty, reorder_level):
	actual_qty = flt(actual_qty)
	projected_qty = flt(projected_qty)
	reorder_level = flt(reorder_level)

	if actual_qty <= 0:
		return "Out of Stock"

	if actual_qty <= reorder_level and projected_qty > reorder_level:
		return "Low Stock / Ordered"

	if actual_qty <= reorder_level:
		return "Critical"

	if projected_qty <= reorder_level:
		return "Need Reorder"

	return "OK"


def get_qty_to_request(projected_qty, reorder_level, reorder_qty):
	projected_qty = flt(projected_qty)
	reorder_level = flt(reorder_level)
	reorder_qty = flt(reorder_qty)

	if projected_qty > reorder_level:
		return 0

	if reorder_qty > 0:
		return reorder_qty

	required_qty = reorder_level - projected_qty

	if required_qty <= 0:
		return 1

	return required_qty


@frappe.whitelist()
def create_material_request(filters=None):
	if isinstance(filters, str):
		filters = frappe.parse_json(filters)

	filters = frappe._dict(filters or {})
	filters.show_only_low_stock = 1

	if not frappe.has_permission("Material Request", "create"):
		frappe.throw(
			_("You do not have permission to create Material Request."),
			frappe.PermissionError,
		)

	rows = get_data(filters)

	if not rows:
		frappe.throw(_("No low stock items found for the selected filters."))

	grouped_rows = {}
	skipped = []

	for row in rows:
		row = frappe._dict(row)

		if row.get("status") == "OK":
			continue

		if not row.get("warehouse"):
			skipped.append(
				{
					"item_code": row.get("item_code"),
					"warehouse": "",
					"reason": _("Warehouse is missing"),
				}
			)
			continue

		if flt(row.get("qty_to_request")) <= 0:
			skipped.append(
				{
					"item_code": row.get("item_code"),
					"warehouse": row.get("warehouse"),
					"reason": _("Projected Qty is already above Re-order Level"),
				}
			)
			continue

		material_request_type = row.get("material_request_type") or "Purchase"
		company = row.get("company") or filters.get("company") or get_default_company()

		existing_request = get_existing_open_material_request(
			item_code=row.item_code,
			warehouse=row.warehouse,
			material_request_type=material_request_type,
			company=company,
		)

		if existing_request:
			skipped.append(
				{
					"item_code": row.item_code,
					"warehouse": row.warehouse,
					"reason": _("Open Material Request already exists"),
					"existing_request": existing_request,
				}
			)
			continue

		key = (company or "", material_request_type)
		grouped_rows.setdefault(key, []).append(row)

	created_material_requests = []

	for key, items in grouped_rows.items():
		company, material_request_type = key

		material_request = frappe.new_doc("Material Request")
		material_request.material_request_type = material_request_type
		material_request.transaction_date = today()

		if company and material_request.meta.has_field("company"):
			material_request.company = company

		for row in items:
			append_material_request_item(material_request, row)

		material_request.insert(ignore_permissions=False)
		created_material_requests.append(material_request.name)

	return {
		"material_requests": created_material_requests,
		"skipped": skipped,
	}


def append_material_request_item(material_request, row):
	child_meta = frappe.get_meta("Material Request Item")

	item_row = {
		"item_code": row.item_code,
		"qty": flt(row.qty_to_request),
		"schedule_date": today(),
	}

	if child_meta.has_field("warehouse"):
		item_row["warehouse"] = row.warehouse

	if child_meta.has_field("uom") and row.get("stock_uom"):
		item_row["uom"] = row.stock_uom

	if child_meta.has_field("stock_uom") and row.get("stock_uom"):
		item_row["stock_uom"] = row.stock_uom

	if child_meta.has_field("conversion_factor"):
		item_row["conversion_factor"] = 1

	if child_meta.has_field("description"):
		item_row["description"] = row.item_name or row.item_code

	material_request.append("items", item_row)


def get_existing_open_material_request(
	item_code, warehouse, material_request_type, company=None
):
	values = {
		"item_code": item_code,
		"warehouse": warehouse,
		"material_request_type": material_request_type,
	}

	company_condition = ""

	if company and frappe.get_meta("Material Request").has_field("company"):
		company_condition = " AND mr.company = %(company)s"
		values["company"] = company

	result = frappe.db.sql(
		"""
		SELECT
			mr.name
		FROM `tabMaterial Request Item` mri
		INNER JOIN `tabMaterial Request` mr
			ON mr.name = mri.parent
		WHERE
			mr.docstatus < 2
			AND mr.material_request_type = %(material_request_type)s
			AND mri.item_code = %(item_code)s
			AND IFNULL(mri.warehouse, '') = %(warehouse)s
			AND IFNULL(mr.status, '') NOT IN (
				'Stopped',
				'Transferred',
				'Received',
				'Ordered',
				'Issued',
				'Cancelled',
				'Completed'
			)
			{company_condition}
		ORDER BY mr.creation DESC
		LIMIT 1
		""".format(
			company_condition=company_condition
		),
		values,
		as_dict=True,
	)

	return result[0].name if result else None


def get_default_company():
	company = frappe.defaults.get_user_default("Company")

	if company:
		return company

	try:
		from erpnext import get_default_company as erpnext_get_default_company

		return erpnext_get_default_company()
	except Exception:
		return None


def get_item_reorder_schema():
	meta = frappe.get_meta("Item Reorder")

	request_warehouse_field = get_request_warehouse_field(meta)
	check_group_field = get_check_group_field(meta, request_warehouse_field)

	return frappe._dict(
		{
			"request_warehouse_field": request_warehouse_field,
			"check_group_field": check_group_field,
		}
	)


def get_request_warehouse_field(meta):
	warehouse_fields = get_warehouse_link_fields(meta)

	for df in warehouse_fields:
		if normalize(df.label) == "request for":
			return df.fieldname

	for df in warehouse_fields:
		if normalize(df.label) in ("request warehouse", "warehouse"):
			if "check" not in normalize(df.label):
				return df.fieldname

	for fieldname in ("request_for", "request_warehouse", "warehouse"):
		df = meta.get_field(fieldname)
		if df and df.fieldtype == "Link" and df.options == "Warehouse":
			label = normalize(df.label)
			if "check" not in label and "group" not in fieldname:
				return fieldname

	frappe.throw(
		_(
			"Cannot find Request For warehouse field in Item Reorder. Please check Item Reorder fieldnames."
		)
	)


def get_check_group_field(meta, request_warehouse_field):
	warehouse_fields = get_warehouse_link_fields(meta)

	for df in warehouse_fields:
		if df.fieldname == request_warehouse_field:
			continue

		label = normalize(df.label)
		fieldname = normalize(df.fieldname)

		if "check" in label or "group" in label or "group" in fieldname:
			return df.fieldname

	for fieldname in ("warehouse_group", "check_in_group", "check_in"):
		df = meta.get_field(fieldname)
		if df and df.fieldtype == "Link" and df.options == "Warehouse":
			if fieldname != request_warehouse_field:
				return fieldname

	return None


def get_warehouse_link_fields(meta):
	fields = []

	for df in meta.fields:
		if df.fieldtype == "Link" and df.options == "Warehouse":
			fields.append(df)

	return fields


def normalize(value):
	return (value or "").strip().lower()