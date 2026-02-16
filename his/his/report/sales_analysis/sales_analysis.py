# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _, msgprint
from frappe.utils import getdate
from datetime import timedelta, date
def execute(filters=None):
	columns, data =get_columns(filters) , get_data(filters)
	return columns, data

def get_data(filters):
	sales_sumery = []
	report_gl = frappe.get_doc("Report", "Sales Order Analysis")

	report_gl_filters = {
	
	
	
			"company":frappe.defaults.get_user_default("company"),
			"from_date": frappe.utils.getdate(filters.from_date),
			"to_date": frappe.utils.getdate(filters.to_date),
	
		}
	
	columns_gl, data_gl = report_gl.get_data(
				limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
			) 
	# billed_qty  qty_to_bill ,amount, billed_amount, pending_amount
	by_doc_list = []
	for   d in  data_gl[:-1]:
		doc_by = {}
		doc_by['date'] = d.posting_date

		doc_by['item_group'] = frappe.db.get_value("Item",d.item_code,"item_group")
		if filters.by_item:
			doc_by['item_code'] = d.item_code
			doc_by['item_group'] = frappe.db.get_value("Item",d.item_code,"item_group")
		else:
			doc_by['item_group'] = frappe.db.get_value("Item",d.item_code,"item_group")
		doc_by['qty'] = d['qty'] or 0
		doc_by['billed_qty'] = d['billed_qty'] or 0
		doc_by['qty_to_bill'] = d['qty_to_bill'] or 0
		doc_by['amount'] = d['amount'] or 0
		doc_by['billed_amount'] = d['billed_amount'] or 0
		doc_by['pending_amount'] = d['pending_amount'] or 0

		by_doc_list.append(doc_by)

	
	from collections import defaultdict


	# Group the dictionaries based on the 'category' key and calculate the sum of selected fields for each group
	grouped_data = defaultdict(lambda: defaultdict(int))
	
	for item in by_doc_list:
			item_code = item['item_group']
			if filters.by_item:
				item_code = item['item_code']
			
			grouped_item = grouped_data[item_code]
			
			for key, value in item.items():
				# if filters.by_item:
				if  key == 'item_group':
					grouped_item[key] = value

				if key != 'item_code' and  key != 'item_group':
					if value:
				
						grouped_item[key] += value

	# Print the grouped data with the sums of selected fields for each category
	by_doc_sales_list = []
	for category, grouped_item in grouped_data.items():
		by_doc_sales = {}
		by_doc_sales['item_code'] = category
		for key, total_value in grouped_item.items():
			by_doc_sales[key] = total_value
		by_doc_sales_list.append(by_doc_sales)
			

	
	for date in daterange(getdate(filters.from_date) , getdate(filters.to_date)):
		
		report_gl_filters = {
	
	
	
	
			"from_date": frappe.utils.getdate(date),
			"to_date": frappe.utils.getdate(date),
	
		}
		columns_gl, data_gl = report_gl.get_data(
				limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
			) 
		
		if len(data_gl):
		
			sales_su = data_gl[-1]
			if sales_su.outstanding_amount: 
				sales_su['cash'] = sales_su.net_total - sales_su.outstanding_amount
			else:
				sales_su['cash'] = sales_su.net_total 

			sales_su.date = date
			sales_sumery.append(sales_su)
	return by_doc_sales_list 

	# for d in data_gl[0]:
	# 	sales_sumery.append


def daterange(start_date, end_date):
		for n in range(int ((end_date - start_date).days)+1):
			yield start_date + timedelta(n)






def get_columns(filters):
	columns = [
			
			{
				"label": _("Qty"),
				"fieldname": "qty",
				"fieldtype": "Float",
				"width": 120,
				"convertible": "qty",
			},
			{
				"label": _("Billed Qty"),
				"fieldname": "billed_qty",
				"fieldtype": "Float",
				"width": 120,
				"convertible": "qty",
			},
			{
				"label": _("Qty to Bill"),
				"fieldname": "qty_to_bill",
				"fieldtype": "Float",
				"width": 120,
				"convertible": "qty",
			},
			{
				"label": _("Amount"),
				"fieldname": "amount",
				"fieldtype": "Currency",
				"width": 110,
				"options": "Company:company:default_currency",
				"convertible": "rate",
			},
			{
				"label": _("Billed Amount"),
				"fieldname": "billed_amount",
				"fieldtype": "Currency",
				"width": 110,
				"options": "Company:company:default_currency",
				"convertible": "rate",
			},
			{
				"label": _("Pending Amount"),
				"fieldname": "pending_amount",
				"fieldtype": "Currency",
				"width": 130,
				"options": "Company:company:default_currency",
				"convertible": "rate",
			},
			
	]
	if filters.by_item:
		columns.insert(
			0,
			{
				"label": _("Item Code"),
				"fieldname": "item_code",
				"fieldtype": "Link",
				"options": "Item",
				"width": 200,
			}
		)
	
		columns.insert(
			1,
			{
				"label": _("Item Group"),
				"fieldname": "item_group",
				"fieldtype": "Link",
				"options": "Item",
				"width": 200,
			}
		)
	else:
		columns.insert(
			0,
			{
				"label": _("Item Group"),
				"fieldname": "item_group",
				"fieldtype": "Link",
				"options": "Item",
				"width": 200,
			},
		)
	return columns


def daterange(start_date, end_date):
		for n in range(int ((end_date - start_date).days)+1):
			yield start_date + timedelta(n)


