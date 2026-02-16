# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
import math
from frappe import _


def execute(filters=None):

	if not filters:
		filters = {}
	columns = get_columns()
	stock = get_total_stock(filters)

	return columns, stock


def get_columns():
	columns = [
		{
			"label": _("Item"),
			"fieldname": "item_code",
			"fieldtype": "Data",
			# "options": "Item",
			"width": 300,
		},
		{
			"label": _("Qty Box"),
			"fieldname": "qty_box",
			"fieldtype": "Float",
			"width": 200,
		},
		{
			"label": _("Qty Strep"),
			"fieldname": "qty_strep",
			"fieldtype": "Float",
			"width": 200,
		},
		
	]

	return columns


def get_total_stock(filters):
	conditions = ""
	columns = ""

	if filters.get("group_by") == "Warehouse":
		if filters.get("company"):
			conditions += " AND warehouse.company = %s" % frappe.db.escape(
				filters.get("company"), percent=False
			)

		conditions += " GROUP BY ledger.warehouse, item.item_code"
		columns += "'' as company, ledger.warehouse"
	else:
		conditions += " GROUP BY warehouse.company, item.item_code"
		columns += " warehouse.company, '' as warehouse"

	result = frappe.db.sql(
		f"""
			SELECT
			
				item.item_code,
			
				sum(ledger.actual_qty) as actual_qty

			FROM
				`tabBin` AS ledger
			INNER JOIN `tabItem` AS item
				ON ledger.item_code = item.item_code
			INNER JOIN `tabWarehouse` warehouse
				ON warehouse.name = ledger.warehouse
			WHERE
				ledger.actual_qty != 0 {conditions}""", as_dict = 1
		)
	data = []
	
	for i in result:
		datad = {}
		datad["item_code"]= i.item_code
		item_doc = frappe.get_doc("Item" , i.item_code)
		datad["qty_box"]	= i.actual_qty
		strep, box = math.modf(i.actual_qty)
		if strep:
			streps = strep * int(item_doc.uoms[1].no_of_streps)
			datad["qty_box"]	= box 
			datad["qty_strep"]	= round(streps)

		
		
		
		data.append(datad)
	frappe.errprint(result)
	
		
	return data

