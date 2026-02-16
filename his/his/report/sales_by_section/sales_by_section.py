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
	report_gl = frappe.get_doc("Report", "Sales Register")

	report_gl_filters = {
	
	
	
	
			"from_date": frappe.utils.getdate(filters.from_date),
			"to_date": frappe.utils.getdate(filters.to_date),
	
		}
	
	columns_gl, data_gl = report_gl.get_data(
				limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
			) 
	
	by_doc_list = []
	income_accounts = frappe.db.sql_list(""" select name from tabAccount """)
	for   d in  data_gl[:-1]:
		
	# for i , d in enumerate(data_gl[:-1]):
		sales_doc = frappe.get_doc("Sales Invoice" , d.invoice)
		
		if sales_doc.source_order:
			doc_by = {}
			doc_by['date'] = d.posting_date


			doc_by['section'] = sales_doc.source_order
			for acc in income_accounts:
				if frappe.scrub(acc) in d:
					doc_by[frappe.scrub(acc)] = d[frappe.scrub(acc)] or 0
				
			doc_by['outstanding_amount'] = d['outstanding_amount'] or 0
			doc_by['net_total'] = d['net_total'] or 0
			if doc_by['outstanding_amount']:
				doc_by['cash'] = doc_by['net_total'] -doc_by["outstanding_amount"]
			else:
				doc_by['cash'] = doc_by['net_total']

			by_doc_list.append(doc_by)

	
	from collections import defaultdict

	# List of dictionaries
	data = [
		{'category': 'A', 'value': 10, 'field1': 5, 'field2': 2},
		{'category': 'B', 'value': 20, 'field1': 3, 'field2': 7},
		{'category': 'A', 'value': 30, 'field1': 8, 'field2': 4},
		{'category': 'B', 'value': 40, 'field1': 2, 'field2': 6},
		{'category': 'A', 'value': 50, 'field1': 6, 'field2': 3},
	]

	# Group the dictionaries based on the 'category' key and calculate the sum of selected fields for each group
	grouped_data = defaultdict(lambda: defaultdict(int))
	
	for item in by_doc_list:
			practioner = item['section']
			
			grouped_item = grouped_data[practioner]
			
			for key, value in item.items():
				if  key == 'date':
					grouped_item[key] = value

				if key != 'section' and  key != 'date':
					grouped_item[key] += value

	# Print the grouped data with the sums of selected fields for each category
	by_doc_sales_list = []
	for category, grouped_item in grouped_data.items():
		by_doc_sales = {}
		by_doc_sales['section'] = category
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
			# {
			# 			"label": "Date",
			# 			"fieldname": "date",
			# 			"fieldtype": "Date",
						
			# 			"width": 100,
			# 		},
					{
						"label": "Section",
						"fieldname": "section",
						"fieldtype": "Data",
						
						"width": 120,
					

					}
			
		
	]
	income_accounts = frappe.db.sql_list(""" select name from tabAccount """)

	report_cols = get_report_columns(filters)
	for col in report_cols:

		if col.label in  income_accounts:
			columns.append(
					{
						"label": col.label,
						"fieldname": frappe.scrub(col.fieldname),
						"fieldtype": col.fieldtype,
						"options": col.options,
						"width": 120,
					

					}
				)
			
			

	columns.append(
			{
			"label": _("Net Total"),
			"fieldname": "net_total",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		}
	)
	columns.append(	
		{
			"label": _("Cash"),
			"fieldname": "cash",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		})
	columns.append(	
		{
			"label": _("Credit"),
			"fieldname": "outstanding_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		})
	
	return columns


def daterange(start_date, end_date):
		for n in range(int ((end_date - start_date).days)+1):
			yield start_date + timedelta(n)
def get_report_columns(filters):
	report_gl = frappe.get_doc("Report", "Sales Register")

	report_gl_filters = {
	
	
	
	
			"from_date": frappe.utils.getdate(),
			"to_date": frappe.utils.getdate(),
	
		}
	
	columns_gl, data_gl = report_gl.get_data(
				limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
			) 
	return columns_gl 


